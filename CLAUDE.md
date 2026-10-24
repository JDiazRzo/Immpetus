# CLAUDE.md · Sistema de selección de talento Immpetus

Este archivo le da contexto a Claude (y a cualquier persona nueva) sobre el proyecto. Léelo completo antes de escribir código. Si algo de aquí choca con lo que te pidan, pregunta antes de cambiarlo.

## Qué es el proyecto

Immpetus Soluciones es una consultora de talento humano en Bogotá. Hoy recibe ~30 hojas de vida (HV) diarias por correo para 4–5 vacantes simultáneas, y el analista de RR. HH. las descarga, revisa y transcribe a mano.

Construimos:

1. **Web pública** con landing de la empresa y una página por vacante (indexable en Google) con formulario de postulación.
2. **Centro de mando** interno para crear/activar vacantes, ver candidatos calificados, validar y reportar a gerencia.
3. **Agente de IA** que lee cada HV en PDF, la califica de 1 a 5 (escala Likert) contra los criterios del cargo, la guarda en Drive con nombre estándar y la registra en la base de datos.
4. **Captura desde Gmail** de las HV que todavía llegan al correo `seleccion@`.

Proyecto académico (Gestión de Proyectos, Universidad EAN) con cliente real. Enfoque híbrido: diseño predictivo + construcción en sprints.

## Reglas que NO se negocian

1. **La IA sugiere, la persona decide.** Nunca se asigna el estado `no_apto` de forma automática. Notas 1–2 quedan en `por_validar` hasta que un usuario lo confirme.
2. **El historial de estados es inmodificable.** Solo se insertan filas en `estados`; nunca UPDATE ni DELETE.
3. **Datos personales (Ley 1581 de 2012).** Toda postulación exige `autorizacion_datos = true` y guarda versión y fecha. Nunca subir HV reales a herramientas de IA públicas, ni al repositorio, ni a logs. Usar HV de prueba inventadas.
4. **Nada de secretos en el código.** Claves en `.env` (nunca se suben). Ver `.env.example`.
5. **La matriz de calificación no usa atributos sensibles** (edad, sexo, estado civil, religión, etnia, discapacidad, orientación). Si la IA los detecta, se ignoran.
6. **El contrato de la API manda.** `docs/CONTRATO_API.md` es la fuente de verdad entre frontend y backend. Cambiarlo requiere PR aprobado por ambos.
7. **La base de datos es PostgreSQL estándar.** Acceso solo por `DATABASE_URL` con SQLAlchemy; no usar el cliente, Auth ni Storage de Supabase. Cambios al esquema solo con `npx supabase migration new`, nunca editando migraciones existentes ni desde el panel.
8. **El login es solo con Google.** No hay registro ni contraseñas propias. El backend valida el `id_token` de Google, exige el dominio `@immpetus.co` y que el correo exista en `usuarios` con `activo = true`, y crea una cookie httpOnly `immpetus_sesion`. El `proxy.ts` del frontend solo redirige; quien protege de verdad es el backend (`401` si no hay sesión válida).

## Stack

| Capa                     | Tecnología                                                                 | Carpeta                      |
| ------------------------ | -------------------------------------------------------------------------- | ---------------------------- |
| Frontend                 | Next.js 16 (App Router) + TypeScript + Tailwind v4                         | `frontend/`                  |
| Backend                  | FastAPI (Python 3.12) + Pydantic + SQLAlchemy                              | `backend/`                   |
| Integraciones e IA       | Python: Gmail API, Drive API, Gemini API (cuenta de servicio)              | `backend/app/integraciones/` |
| Base de datos            | PostgreSQL en Supabase (región São Paulo), con RLS                         | `supabase/migrations/`       |
| Archivos                 | Google Drive (carpeta por vacante)                                         | —                            |
| Auth del centro de mando | Solo Google (dominio `@immpetus.co`) + cookie httpOnly creada por backend  | —                            |
| Despliegue               | Frontend en Vercel · Backend en Google Cloud Run                           | —                            |

## Estructura del repositorio

```
/
├── CLAUDE.md                ← este archivo
├── docs/
│   ├── CONTRATO_API.md      ← endpoints y JSON (fuente de verdad)
│   └── SPRINTS.md           ← plan de trabajo por sprint y rol
├── supabase/migrations/     ← esquema de la base de datos (SQL)
├── frontend/                ← Next.js
│   └── src/
│       ├── app/admin/(panel)/  ← páginas del centro de mando
│       ├── app/admin/login/    ← login con Google
│       ├── proxy.ts            ← redirige a /admin/login si no hay cookie
│       └── mocks/              ← datos de prueba (se borran al conectar el backend)
└── backend/
    └── app/
        ├── api/             ← routers FastAPI (auth, públicos y admin)
        ├── models/          ← esquemas Pydantic (iguales al contrato)
        ├── services/        ← lógica de negocio (estados, reglas, sesión)
        └── integraciones/   ← gmail.py, drive.py, ia.py
```

## Roles y dueños

| Rol                                         | Responsable | Carpeta principal                       |
| ------------------------------------------- | ----------- | --------------------------------------- |
| Frontend, despliegue y coordinación técnica | Jerónimo    | `frontend/`                             |
| Backend                                     | Justin      | `backend/app/api`, `services`, `models` |
| Integraciones e IA                          | Fabian      | `backend/app/integraciones`             |
| QA y documentación                          | Santiago    | `docs/`, casos de prueba                |

Si tu tarea toca la carpeta de otro rol, avísale en el PR.

## Flujo de trabajo con Git

- Rama principal: `main` (protegida, solo entra por PR).
- Ramas: `feat/<rol>-<tarea>` (ej. `feat/front-landing`, `feat/back-postulaciones`, `feat/ia-calificar`).
- Commits en español, en presente: `agrega formulario de postulación`.
- Todo PR: descripción corta, qué requerimiento (RQ#) cubre y cómo se probó.
- No se hace merge de un PR propio sin una revisión de otro integrante.

## Convenciones de código

**Frontend**

- TypeScript estricto, sin `any`.
- Componentes en `src/components`, páginas en `src/app`.
- Tipos de la API en `src/types/api.ts`, copiados del contrato.
- Mientras el backend no esté listo, leer de `src/mocks/` (`NEXT_PUBLIC_USE_MOCKS=true`). Se conecta endpoint por endpoint, conservando las firmas de `lib/api.ts` y `lib/admin-api.ts`.
- Las llamadas a `/api/*` pasan por un rewrite de Next hacia el backend (mismo dominio, para que la cookie funcione), siempre con `credentials: "include"`. La URL del backend va en `NEXT_PUBLIC_API_URL`.
- Si una llamada del admin responde `401`, redirigir a `/admin/login`.
- Accesibilidad: `<button>`, `<label>`, foco visible, contraste AA.
- Estilo visual: usar el skill `immpetus-frontend` si está disponible.
- La versión de Next.js es 16: leer `frontend/AGENTS.md` y la documentación en `node_modules/next/dist/docs/` antes de usar APIs que no conozcas (por ejemplo, `middleware` ahora se llama `proxy`).

**Backend / integraciones**

- Pydantic para toda entrada y salida; los modelos replican el contrato.
- Errores con el formato `{ "error": { "code", "message", "field" } }`.
- La lógica de estados vive en `services/estados.py` y es la única que puede cambiar un estado.
- Las integraciones no deciden estados: devuelven datos y el backend aplica las reglas.
- Funciones de integración puras y probables con datos falsos (sin llamar a Google en los tests).
- Sesión: verificar el `id_token` con la librería `google-auth` (no a mano), firmar la cookie con `SESSION_SECRET`, y una dependencia de FastAPI (`usuario_actual`) que protege todo `/api/admin/*`.
- `ruff` para formato y lint (`uv run ruff check .`).
- Dependencias con `uv add`; se instalan con `uv sync`.

## Glosario

| Término             | Significado                                                                 |
| ------------------- | --------------------------------------------------------------------------- |
| HV                  | Hoja de vida (CV)                                                           |
| Terna               | Los 3 finalistas que se presentan a la empresa cliente                      |
| Reserva Estratégica | Candidatos con nota 3: no aptos para esta vacante, útiles para futuras      |
| Convocatoria        | Proceso de selección de una vacante                                         |
| Centro de mando     | Panel interno de RR. HH.                                                    |
| KPI B1–B4           | Tiempo de clasificación, time-to-hire, % HV trazables, % vacantes indexadas |

## Antes de entregar cualquier tarea

1. ¿Cumple el contrato de la API (nombres y formas exactas)?
2. ¿Respeta las 8 reglas de arriba?
3. ¿Hay algún secreto, HV real o dato personal en el código o en los logs?
4. ¿Se probó? (al menos manualmente, y con test si es backend)
