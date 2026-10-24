## Sprint 0 · Fundaciones

Objetivo: que los 4 puedan trabajar en paralelo sin bloquearse.

| Rol           | Tareas                                                                                                                                                                                                                           | Listo cuando                                                                           |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Front         | ✅ Repo y organización en GitHub · ✅ `CLAUDE.md`, contrato y este plan · ✅ proyecto Next.js con Tailwind · ✅ base de datos en Supabase con el esquema aplicado · mocks con el formato del contrato · deploy inicial en Vercel | Cualquiera clona, corre `npm run dev` y ve la landing publicada                        |
| Backend       | Conexión a la base con SQLAlchemy usando `DATABASE_URL` (local y nube) · modelos Pydantic del contrato · CORS para `localhost:3000` · script de datos semilla con las 4 vacantes de prueba                                       | `/health` responde, el backend lee la tabla `vacantes` y las 4 vacantes están cargadas |
| Integraciones | Proyecto en Google Cloud · habilitar Gmail, Drive y Gemini · cuenta de servicio (sin contraseñas del correo) · prompt v1 de calificación probado con 5 HV inventadas                                                             | Script que recibe un PDF de prueba y devuelve el JSON del contrato                     |
| QA            | Plantilla de casos de prueba desde RQ1–RQ15 · 10 HV de prueba inventadas (variadas)                                                                                                                                              | Excel de casos y carpeta de HV de prueba                                               |

## Sprint 1 · Web pública y postulación

| Rol           | Tareas                                                                                                                                                                                  |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Front         | ✅ Landing completa · ✅ lista de vacantes · ✅ página `/vacantes/[slug]` con SEO (JobPosting, sitemap) · ✅ formulario de postulación (con mocks) · conectar con el backend real       |
| Backend       | `GET /api/vacantes`, `GET /api/vacantes/{slug}`, `POST /api/postulaciones` (solo PDF, tamaño máximo, autorización obligatoria, vacante activa) · tests con pytest de los casos de error |
| Integraciones | `drive.guardar_hv` y `drive.renombrar_hv` · conectar con `POST /api/postulaciones`                                                                                                      |
| QA            | Probar RQ13, RQ14, RQ15 · revisar accesibilidad básica                                                                                                                                  |

**Demo:** un candidato se postula desde la web y su PDF aparece en Drive.

## Sprint 2 · Agente de IA y centro de mando

| Rol           | Tareas                                                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Front         | Login con Google · centro de mando: vacantes con interruptor, contadores, tabla de candidatos, bandeja "Por validar"                       |
| Backend       | Endpoints `/api/admin/*` de vacantes, candidatos, estado y corrección de nota · reglas de estado y RLS · conectar frontend real            |
| Integraciones | `ia.calificar_hv` en producción · mapeo nota → estado · habilidades contra el catálogo · job de correo (`gmail.leer_postulaciones_nuevas`) |
| QA            | Probar RQ4, RQ6, RQ7, RQ8, RQ9, RQ11 · comparar notas de la IA vs. criterio humano en las HV de prueba                                     |

**Demo:** llega una HV (web o correo), se califica sola, aparece en el ranking y el analista la valida.

## Sprint 3 · Trazabilidad, reserva y reporte

| Rol           | Tareas                                                                                                   |
| ------------- | -------------------------------------------------------------------------------------------------------- |
| Front         | Detalle del candidato con historial · Reserva Estratégica con búsqueda · panel gerencial · pulido visual |
| Backend       | Historial, búsqueda en reserva, `correos-sin-asignar`                                                    |
| Integraciones | `gmail.enviar_reporte` con ranking · plantilla del correo                                                |
| QA            | Regresión completa RQ1–RQ15 · checklist OWASP básico · 0 enlaces públicos en Drive                       |

**Demo:** sistema completo de punta a punta.

## Piloto

Una convocatoria real de Immpetus [POR CONFIRMAR]. Todos: soporte, corrección de errores y medición de KPI B1–B4 y concordancia IA vs. analista.

## Cierre

Versión final · manual de usuario (QA) · manual técnico (backend + integraciones) · capacitación a RR. HH. · entrega de accesos a Immpetus · acta de cierre.

## Definición de terminado

Una tarea está terminada cuando: cumple el contrato, está en `main` por PR revisado, QA la probó contra su RQ, y no expone datos personales ni secretos.
