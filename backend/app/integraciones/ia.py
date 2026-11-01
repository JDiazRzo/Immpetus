import io
import pdfplumber
import re
from pydantic import BaseModel, Field, model_validator, model_validator
from typing import List
from app.models.vacantes import VacanteDetalle
from app.models.common import Pagina, Modalidad, EstadoCandidato
from google import genai  # pyright: ignore[reportMissingImports]
from google.genai import types  # pyright: ignore[reportMissingImports]

class MatrizEvaluacion(BaseModel):
    formacion: str
    experiencia_anios: int
    sectores: List[str]
    justificacion: str

class Habilidad(BaseModel):
    nombre: str
    nivel: str  # Opcional: puedes usar un Literal["básico", "intermedio", "avanzado"] si quieres restringir los valores
    en_catalogo: bool

class Calificacion(BaseModel):
    nota: int = Field(..., description="Puntaje o calificación otorgada")
    resumen: str = Field(..., max_length=600, description="Resumen con un máximo de 600 caracteres")
    matriz: MatrizEvaluacion
    habilidades: List[Habilidad]
    
    @model_validator(mode='after')
    def calcular_nota_automatica(self) -> 'Calificacion':
        """Calcula la nota de manera determinista usando reglas de negocio en Python."""
        puntaje = 1  # Base mínima
        
        # Regla por años de experiencia
        if self.matriz.experiencia_anios >= 5:
            puntaje += 2
        elif self.matriz.experiencia_anios >= 2:
            puntaje += 1
            
        # Regla por habilidades en catálogo
        habilidades_validas = sum(1 for h in self.habilidades if h.en_catalogo)
        if habilidades_validas >= 3:
            puntaje += 2
        elif habilidades_validas >= 1:
            puntaje += 1
            
        self.nota = min(puntaje, 5) # Máximo 5
        return self

def extraer_texto_pdf(ruta_pdf: str) -> str:
    texto_completo = []
    
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina_num, pagina in enumerate(pdf.pages, start=1):
            # Extraer texto de la página
            texto_pagina = pagina.extract_text(layout=False) # Puedes probar layout=True si hay columnas muy marcadas
            
            if texto_pagina:
                # Limpieza superficial de espacios extra
                texto_limpio = re.sub(r'[ \t]+', ' ', texto_pagina)
                texto_completo.append(f"--- Página {pagina_num} ---\n{texto_limpio}")
                
    return "\n".join(texto_completo)

def extraer_texto_desde_bytes(pdf_bytes: bytes) -> str:
    texto_completo = []
    
    # pdfplumber acepta un objeto en memoria tipo archivo con io.BytesIO
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pagina_num, pagina in enumerate(pdf.pages, start=1):
            texto_pagina = pagina.extract_text(layout=False)
            if texto_pagina:
                texto_completo.append(f"--- Página {pagina_num} ---\n{texto_pagina}")
                
    return "\n".join(texto_completo)

def analizar_cv_con_ia(texto_cv: str, vacante: VacanteDetalle, catalogo_habilidades: list[str]) -> Calificacion:
    """
    Envía el texto del CV, la vacante y el catálogo de habilidades a Gemini 
    para obtener una evaluación estructurada y tipada.
    """
    client = genai.Client() # Lee automáticamente GEMINI_API_KEY del entorno
    
    # Convertimos el catálogo de habilidades en un formato de texto limpio para el prompt
    catalogo_str = ", ".join(catalogo_habilidades)
    
    # Construimos un prompt contextualizado y riguroso
    prompt = f"""
    Eres un analista experto de recursos humanos y selección de talento TI.
    Tu tarea es evaluar la siguiente hoja de vida basándote estrictamente en los requerimientos de la vacante provista y contrastar las habilidades del candidato con el catálogo oficial.

    === INFORMACIÓN DE LA VACANTE ===
    Título: {vacante.cargo}
    Descripción: {vacante.descripcion}
    Criterios: {vacante.criterios}

    === CATÁLOGO OFICIAL DE HABILIDADES ===
    [{catalogo_str}]
    *(Nota: Para cada habilidad que detectes en el CV, debes marcar 'en_catalogo' como true SOLAMENTE si está presente o mapea directamente a este catálogo).*

    === TEXTO DE LA HOJA DE VIDA A ANALIZAR ===
    {texto_cv}
    """
    
    # Llamada a la API de Gemini pidiendo Structured Outputs
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Calificacion,
            temperature=0.1, # Temperatura baja para máxima precisión y cero inventos
        ),
    )
    
    # response.parsed ya devuelve el objeto 'Calificacion' validado por Pydantic
    return response.parsed

def calificar_hv(pdf_bytes: bytes, vacante: VacanteDetalle, catalogo_habilidades: list[str]) -> Calificacion:
    """
    Devuelve nota 1-5, resumen, matriz y habilidades detectadas.
    No decide estados: eso lo hace el backend con la regla de oro.
    """
    # 1. Extraer texto usando bytes en memoria
    texto_cv = extraer_texto_desde_bytes(pdf_bytes)
    
    # 2. Llamar a la IA pasándole también el contexto de la vacante y el catálogo
    # (Aquí integras el prompt con la vacante y el catálogo de habilidades)
    resultado_ia = analizar_cv_con_ia(texto_cv, vacante, catalogo_habilidades)
    
    # 3. Retornar el objeto Calificacion final
    return resultado_ia
