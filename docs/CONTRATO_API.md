# Contrato de la API · Sistema de selección Immpetus

Versión 0.1 · Acordar en la primera reunión técnica antes de escribir código.
Cualquier cambio a este archivo se hace por Pull Request y lo aprueban frontend y backend.

## Convenciones

- Base: `/api` (pública) y `/api/admin` (requiere sesión).
- JSON en `snake_case`. Fechas en ISO 8601 UTC (`2026-10-24T15:30:00Z`).
- IDs: UUID.
- Autenticación admin: header `Authorization: Bearer <token de Google>`. El backend valida que el correo sea del dominio de Immpetus y que exista en `usuarios`.
- Paginación: `?page=1&page_size=20` → respuesta `{ "items": [...], "total": 42, "page": 1, "page_size": 20 }`.
- Errores, siempre con esta forma:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "El archivo debe ser PDF de máximo 5 MB.", "field": "archivo" } }
```

| HTTP | `code` | Cuándo |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Datos inválidos |
| 401 | `UNAUTHENTICATED` | Sin sesión o token vencido |
| 403 | `FORBIDDEN` | Cuenta fuera del dominio o sin rol |
| 404 | `NOT_FOUND` | Recurso no existe |
| 409 | `CONFLICT` | Transición de estado no permitida |
| 413 | `FILE_TOO_LARGE` | PDF supera el límite |

## Valores fijos (enums)

| Campo | Valores |
|---|---|
| `estado` | `nuevo`, `entrevista`, `reserva`, `por_validar`, `no_apto`, `contratado` |
| `rol` | `analista`, `lider`, `gerencia` |
| `canal` | `web`, `correo` |
| `modalidad` | `presencial`, `hibrido`, `remoto` |
| `origen` (habilidad) | `ia`, `analista` |
| `nivel` | `basico`, `intermedio`, `avanzado` |

**Regla de oro (dilema ético):** el sistema nunca asigna `no_apto` por sí solo. La IA deja las notas 1–2 en `por_validar`; solo un usuario autenticado puede pasar a `no_apto`.

---

## 1. Endpoints públicos (web)

### `GET /api/vacantes`
Lista las vacantes **activas**. Query opcional: `q` (texto), `modalidad`.

```json
{
  "items": [
    {
      "id": "uuid",
      "slug": "gestor-soporte-servicio-cliente",
      "cargo": "Gestor de Soporte y Servicio al Cliente",
      "ciudad": "Bogotá",
      "modalidad": "remoto",
      "modalidad_detalle": "80 % remoto",
      "jornada": "Tiempo completo",
      "salario_texto": "$2.700.000",
      "urgente": false,
      "publicada_en": "2026-10-20T13:00:00Z"
    }
  ],
  "total": 4, "page": 1, "page_size": 20
}
```

### `GET /api/vacantes/{slug}`
Detalle de una vacante activa (404 si está inactiva).

```json
{
  "id": "uuid",
  "slug": "gestor-soporte-servicio-cliente",
  "cargo": "Gestor de Soporte y Servicio al Cliente",
  "ciudad": "Bogotá",
  "modalidad": "remoto",
  "modalidad_detalle": "80 % remoto",
  "jornada": "Tiempo completo",
  "salario_texto": "$2.700.000",
  "descripcion": "texto",
  "responsabilidades": ["...", "..."],
  "criterios": [
    { "habilidad": "Servicio al cliente", "obligatoria": true }
  ]
}
```

### `POST /api/postulaciones`
`multipart/form-data`

| Campo | Tipo | Regla |
|---|---|---|
| `vacante_id` | uuid | Vacante activa |
| `nombre` | texto | Obligatorio |
| `correo` | email | Obligatorio |
| `celular` | texto | Obligatorio |
| `archivo` | PDF | Solo `application/pdf`, máximo [POR CONFIRMAR] MB |
| `autorizacion_datos` | boolean | Debe ser `true`, si no → 400 |
| `autorizacion_version` | texto | Ej. `"1.0"` |

Respuesta `201`:
```json
{ "id": "uuid", "estado": "nuevo", "mensaje": "Postulación enviada." }
```
El backend guarda el PDF en Drive y deja el candidato en `nuevo`. La calificación con IA corre después, en segundo plano (ver sección 3).

---

## 2. Endpoints del centro de mando (`/api/admin`)

### `GET /api/admin/me`
```json
{ "id": "uuid", "correo": "analista@immpetus.co", "nombre": "…", "rol": "analista" }
```

### Vacantes

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/api/admin/vacantes` | Todas (activas e inactivas) |
| `POST` | `/api/admin/vacantes` | Crear vacante |
| `PATCH` | `/api/admin/vacantes/{id}` | Editar; incluye `{ "activa": true/false }` para el interruptor |
| `GET` | `/api/admin/vacantes/{id}/resumen` | Contadores del panel |

Cuerpo de `POST` / `PATCH`:
```json
{
  "cargo": "…", "cliente": "…", "ciudad": "…", "modalidad": "hibrido",
  "modalidad_detalle": "…", "jornada": "…", "salario_texto": "…",
  "descripcion": "…", "responsabilidades": ["…"], "urgente": false, "activa": true,
  "criterios": [ { "habilidad_id": "uuid", "obligatoria": true, "peso": 3 } ]
}
```

Respuesta de `/resumen`:
```json
{ "recibidas": 42, "nota_4_5": 9, "reserva": 14, "por_validar": 6, "entrevista": 5 }
```

### Candidatos

`GET /api/admin/vacantes/{id}/candidatos?estado=por_validar&orden=nota_desc`
```json
{
  "items": [
    {
      "id": "uuid",
      "nombre": "…", "correo": "…", "celular": "…",
      "drive_url": "https://drive.google.com/…",
      "archivo_nombre": "4 - Nombre Apellido - Gestor Soporte.pdf",
      "nota": 4,
      "nota_validada": false,
      "validada_por": null,
      "estado": "nuevo",
      "habilidades": [ { "nombre": "Zendesk", "coincide": true } ],
      "creado_en": "…"
    }
  ],
  "total": 42, "page": 1, "page_size": 20
}
```

`GET /api/admin/candidatos/{id}` → lo anterior más:
```json
{
  "resumen_ia": "texto",
  "matriz": { "formacion": "…", "experiencia_anios": 5, "sectores": ["…"], "justificacion": "…" },
  "historial": [
    { "fecha": "…", "evento": "postulacion_recibida", "detalle": "Canal web. Autorización v1.0", "usuario": null },
    { "fecha": "…", "evento": "calificacion_ia", "detalle": "Nota 2", "usuario": null }
  ]
}
```

`POST /api/admin/candidatos/{id}/estado`
```json
{ "estado": "no_apto", "observacion": "No cumple experiencia mínima" }
```
Devuelve el candidato actualizado. Transiciones no permitidas → `409 CONFLICT`. Cada cambio crea una fila en `estados` con el usuario y la fecha (inmodificable).

`POST /api/admin/candidatos/{id}/calificacion` (corregir nota)
```json
{ "nota": 3, "motivo": "Experiencia equivalente en ventas consultivas" }
```

### Reserva Estratégica

`GET /api/admin/reserva?habilidad_id=uuid&habilidad_id=uuid&cargo=soporte`
Devuelve candidatos en estado `reserva` con esas habilidades (mismo formato de lista).

`POST /api/admin/reserva/{candidato_id}/asociar` → `{ "vacante_id": "uuid" }`

### Habilidades
`GET /api/admin/habilidades?q=excel` → `[{ "id": "uuid", "nombre": "Excel", "categoria": "herramienta" }]`

### Reporte a gerencia
`POST /api/admin/vacantes/{id}/reporte` → `{ "destinatarios": ["gerencia@immpetus.co"] }`
Respuesta `202 { "enviado": true }`.

### Correos sin asignar
| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/api/admin/correos-sin-asignar` | HV de correo que no se pudieron asociar a una vacante |
| `POST` | `/api/admin/correos-sin-asignar/{id}/asignar` | `{ "vacante_id": "uuid" }` |

---

## 3. Contrato interno: Backend ↔ Integraciones e IA

Las integraciones no son endpoints públicos: son funciones de Python en el módulo `integraciones/` que el backend llama, más un job programado.

```python
# integraciones/drive.py
def guardar_hv(pdf_bytes: bytes, vacante: Vacante, nombre: str) -> DriveFile:
    """Sube a Drive/<vacante.codigo>/ y devuelve id y url."""

def renombrar_hv(drive_file_id: str, nota: int, nombre: str, cargo: str) -> None:
    """Renombra a '[NOTA] - [NOMBRE] - [CARGO].pdf'."""

# integraciones/ia.py
def calificar_hv(pdf_bytes: bytes, vacante: Vacante, catalogo_habilidades: list[str]) -> Calificacion:
    """Devuelve nota 1-5, resumen, matriz y habilidades detectadas.
    No decide estados: eso lo hace el backend con la regla de oro."""

# integraciones/gmail.py
def leer_postulaciones_nuevas() -> list[CorreoHV]:
    """Lee seleccion@ desde la última ejecución; devuelve adjuntos PDF + asunto + remitente."""

def enviar_reporte(destinatarios: list[str], html: str) -> None: ...
```

Salida esperada de `calificar_hv` (validar con Pydantic):
```json
{
  "nota": 4,
  "resumen": "texto ≤ 600 caracteres",
  "matriz": { "formacion": "…", "experiencia_anios": 5, "sectores": ["…"], "justificacion": "…" },
  "habilidades": [ { "nombre": "Zendesk", "nivel": "intermedio", "en_catalogo": true } ]
}
```

**Job de correo** (Cloud Scheduler cada [POR CONFIRMAR] min): `POST /internal/jobs/ingesta-correo` con token interno.
Flujo: leer correos → identificar la vacante por código en el asunto → si no hay código, a `correos-sin-asignar` → guardar en Drive → crear candidato (`canal = "correo"`) → calificar.

**Mapeo nota → estado (lo aplica el backend):**

| Nota | Estado inicial |
|---|---|
| 4–5 | `nuevo` (resaltado como apto) |
| 3 | `reserva` |
| 1–2 | `por_validar` (nunca `no_apto` automático) |

---

## 4. Datos de prueba (mientras no hay backend)

El frontend usa `mocks/` con este mismo formato. Backend e integraciones deben devolver exactamente estas formas.

## Pendientes [POR CONFIRMAR]

- Tamaño máximo del PDF.
- Frecuencia del job de correo.
- Formato del código de vacante en el asunto del correo (ej. `[GSC-0425]`).
- Correos de gerencia para el reporte.
