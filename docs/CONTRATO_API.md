# Contrato de la API · Sistema de selección Immpetus

Versión 0.4 · Sprint 3: reserva, correos sin asignar, reporte y anonimización (secciones 3 y 5.8, códigos 502).
v0.3 · Agrega la autenticación con Google (sección 1.5) y cambia la sesión del centro de mando a cookie httpOnly.
v0.2 · Agrega la sección 5 (reglas de negocio) con las decisiones de la revisión de backend.
Cualquier cambio a este archivo se hace por Pull Request y lo aprueban frontend y backend.

## Convenciones

- Base: `/api` (pública), `/api/auth` (inicio y cierre de sesión) y `/api/admin` (requiere sesión).
- JSON en `snake_case`. Fechas en ISO 8601 UTC (`2026-10-24T15:30:00Z`).
- IDs: UUID.
- Autenticación admin: cookie httpOnly `immpetus_sesion` (Secure, SameSite=Lax, 8 h), creada por `POST /api/auth/google` (sección 1.5). Todo `/api/admin/*` responde `401 UNAUTHENTICATED` sin cookie válida y `403 FORBIDDEN` si el usuario está inactivo o no tiene rol. No hay login con contraseña.
- El frontend llama a `/api/*` a través de un rewrite de Next (mismo dominio que la web) y con `credentials: "include"`.
- Paginación: `?page=1&page_size=20` → respuesta `{ "items": [...], "total": 42, "page": 1, "page_size": 20 }`.
- Errores, siempre con esta forma:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "El archivo debe ser PDF de máximo 5 MB.", "field": "archivo" } }
```

| HTTP | `code` | Cuándo |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Datos inválidos |
| 401 | `UNAUTHENTICATED` | Sin sesión, sesión vencida o token de Google inválido |
| 403 | `FORBIDDEN` | Cuenta fuera del dominio, no registrada, inactiva o sin rol |
| 404 | `NOT_FOUND` | Recurso no existe |
| 409 | `CONFLICT` | Transición de estado no permitida |
| 413 | `FILE_TOO_LARGE` | PDF supera el límite |
| 502 | `STORAGE_ERROR` | Falló Drive (guardar, mover o borrar el PDF) |
| 502 | `EMAIL_ERROR` | Falló el envío del reporte por Gmail |

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

**La API es la única puerta a la base de datos.** El frontend nunca se conecta directo a Supabase.

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
| `archivo` | PDF | Solo `application/pdf`, máximo `MAX_PDF_MB` (variable de entorno, por defecto 5) |
| `autorizacion_datos` | boolean | Debe ser `true`, si no → 400 |
| `autorizacion_version` | texto | Ej. `"1.0"` |

Respuesta `201`:
```json
{ "id": "uuid", "estado": "nuevo", "mensaje": "Postulación enviada." }
```
El backend guarda el PDF en Drive y deja el candidato en `nuevo`. La calificación con IA corre después, en segundo plano (ver sección 3).

---

## 1.5 Autenticación (`/api/auth`)

Solo Google. No existe registro ni login con contraseña. Los usuarios del centro de mando los crea el rol `lider` en la tabla `usuarios`.

### `POST /api/auth/google`
```json
{ "id_token": "token que entrega Google Identity Services en el navegador" }
```

El backend:
1. Verifica el `id_token` con la librería `google-auth` (firma de Google y `aud` = `GOOGLE_OAUTH_CLIENT_ID`).
2. Exige `email_verified = true` y `hd` = `ALLOWED_EMAIL_DOMAIN` (`immpetus.co`).
3. Busca el correo en `usuarios` con `activo = true`.
4. Crea la cookie `immpetus_sesion` firmada con `SESSION_SECRET` (httpOnly, Secure, SameSite=Lax, 8 h).

Respuesta `200`: igual a `GET /api/admin/me`.

| HTTP | `code` | Cuándo | `message` |
|---|---|---|---|
| 401 | `UNAUTHENTICATED` | Token inválido o vencido | "No pudimos verificar tu cuenta de Google. Intenta de nuevo." |
| 403 | `FORBIDDEN` | Dominio distinto a `@immpetus.co` | "Solo pueden entrar cuentas @immpetus.co." |
| 403 | `FORBIDDEN` | Correo no registrado o inactivo | "Tu cuenta no está registrada en el centro de mando. Pide acceso al líder de selección." |

### `POST /api/auth/logout`
Borra la cookie. Respuesta `204`, aunque no haya sesión.

**Notas**
- El `proxy.ts` del frontend solo revisa que la cookie exista para redirigir a `/admin/login`; la validación real la hace el backend en cada petición a `/api/admin/*` (dependencia `usuario_actual`).
- Si cualquier llamada del admin responde `401`, el frontend redirige a `/admin/login?next=<ruta>`.
- En desarrollo local (frontend `localhost:3000`, backend `localhost:8000`) el rewrite de Next mantiene el mismo origen; no se necesita CORS con credenciales.

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
Devuelve el candidato actualizado. Transiciones no permitidas → `409 CONFLICT`. Cada cambio crea una fila en `estados` con el usuario de la sesión y la fecha (inmodificable).

`POST /api/admin/candidatos/{id}/calificacion` (corregir nota)
```json
{ "nota": 3, "motivo": "Experiencia equivalente en ventas consultivas" }
```
Corregir la nota **no cambia el estado** (ver regla 5.4). Devuelve el candidato con `nota_validada: true`.

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
| `POST` | `/api/admin/correos-sin-asignar/{id}/asignar` | `{ "vacante_id": "uuid" }` → crea el candidato y lo devuelve (ver regla 5.6) |

---

## 3. Contrato interno: Backend ↔ Integraciones e IA

Las integraciones no son endpoints públicos: son funciones de Python en el módulo `integraciones/` que el backend llama, más un job programado.

```python
# integraciones/drive.py
def guardar_hv(pdf_bytes: bytes, vacante: Vacante, nombre: str) -> DriveFile:
    """Sube a Drive/<vacante.codigo>/ y devuelve id y url."""

def renombrar_hv(drive_file_id: str, nota: int, nombre: str, cargo: str) -> None:
    """Renombra a '[NOTA] - [NOMBRE] - [CARGO].pdf'."""

def mover_hv(drive_file_id: str, vacante: Vacante) -> DriveFile:   # v0.4 (asignar correo)
    """Mueve el PDF a Drive/<vacante.codigo>/ y devuelve id y url (pueden cambiar)."""

def borrar_hv(drive_file_id: str) -> None:                          # v0.4 (anonimizar)
    """Borra el PDF. Si ya no existe se considera éxito (el borrado debe ser reintentable)."""

# integraciones/ia.py
def calificar_hv(pdf_bytes: bytes, vacante: Vacante, catalogo_habilidades: list[str]) -> Calificacion:
    """Devuelve nota 1-5, resumen, matriz y habilidades detectadas.
    No decide estados: eso lo hace el backend con la regla de oro."""

# integraciones/gmail.py
def leer_postulaciones_nuevas() -> list[CorreoHV]:
    """Lee seleccion@ desde la última ejecución; devuelve adjuntos PDF + asunto + remitente."""

def enviar_reporte(destinatarios: list[str], html: str) -> None: ...
# El asunto del correo sale del <title> del html (el contrato no tiene parámetro `asunto`).
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

**Job de correo** (Cloud Scheduler cada [POR CONFIRMAR] min): `POST /internal/jobs/ingesta-correo` con header `X-Job-Token: <INTERNAL_JOB_TOKEN>` (no usa la cookie de sesión).
Flujo: leer correos → identificar la vacante por código en el asunto → si no hay código, a `correos-sin-asignar` → guardar en Drive → crear candidato (`canal = "correo"`) → calificar.

**Mapeo nota → estado (lo aplica el backend):**

| Nota | Estado inicial |
|---|---|
| 4–5 | `nuevo` (resaltado como apto) |
| 3 | `reserva` |
| 1–2 | `por_validar` (nunca `no_apto` automático) |

---

## 4. Datos de prueba (mientras no hay backend)

El frontend usa `mocks/` con este mismo formato (`NEXT_PUBLIC_USE_MOCKS=true`), incluido un login simulado. Backend e integraciones deben devolver exactamente estas formas. Se conecta endpoint por endpoint.

---

## 5. Reglas de negocio (decisiones)

### 5.1 Transiciones de estado

Las únicas transiciones válidas. Cualquier otra → `409 CONFLICT`. Todas las que se hacen desde `/api/admin` quedan registradas con `validado_por` (usuario de la sesión).

| Desde \ Hacia | `entrevista` | `reserva` | `por_validar` | `no_apto` | `contratado` |
|---|---|---|---|---|---|
| `nuevo` | ✅ | ✅ | — | ✅ | — |
| `por_validar` | ✅ | ✅ | — | ✅ | — |
| `reserva` | ✅ | — | — | ✅ | — |
| `entrevista` | — | ✅ | — | ✅ | ✅ |
| `no_apto` | — | — | — | — | — |
| `contratado` | — | — | — | — | — |

- `no_apto` y `contratado` son **finales**. Si hubo un error, el líder de RR. HH. lo resuelve fuera del sistema y queda como observación; no se reabre.
- **Solo el sistema** asigna el estado inicial (`nuevo`, `reserva` o `por_validar`) con la primera calificación de la IA (regla 5.3). El sistema **nunca** asigna `no_apto`, `entrevista` ni `contratado`.
- La tabla vive en `services/estados.py` como un diccionario; es la única función que inserta en `estados`.

### 5.2 Campos `nota`, `nota_validada` y `validada_por`

No son columnas: se derivan (vista `v_candidatos`, migración `0002`).

| Campo | Significado |
|---|---|
| `nota` | La nota de la calificación **más reciente** (IA o analista). |
| `nota_validada` | `true` si una persona ya revisó la nota: la última calificación la hizo un analista, **o** existe un cambio de estado hecho por un usuario después de la última calificación. |
| `validada_por` | Nombre del usuario que hizo esa validación; `null` si `nota_validada = false`. |

En la UI: `nota_validada = false` → "Sugerida por IA"; `true` → "Validada por {validada_por}".

### 5.3 Mapeo nota → estado (solo la primera vez)

Se aplica **una sola vez**, cuando la IA califica por primera vez a un candidato en estado `nuevo`:

| Nota IA | Estado inicial |
|---|---|
| 4–5 | `nuevo` |
| 3 | `reserva` |
| 1–2 | `por_validar` |

Si la IA vuelve a calificar (por ejemplo, tras ajustar la matriz), se guarda la nueva calificación pero **no se cambia el estado**.

### 5.4 Corrección de nota por el analista

`POST /calificacion` guarda la nueva nota con `origen = analista` y `motivo`, y **nunca cambia el estado**. Si el analista quiere mover al candidato, lo hace explícitamente con `POST /estado`. Así una corrección a 1–2 nunca saca a alguien de `reserva` sin una decisión humana explícita.

### 5.5 No se borran candidatos; se anonimizan

- La API **no ofrece `DELETE`** de candidatos, calificaciones ni estados. Los triggers de la base lo bloquean (también por `cascade`).
- **Derecho de supresión (Ley 1581, art. 8):** si un titular pide eliminar sus datos, se usa `POST /api/admin/candidatos/{id}/anonimizar` (solo rol `lider`). Reemplaza nombre, correo y celular por valores anónimos, borra el PDF de Drive y registra el evento. El historial queda, pero sin datos personales. Implementado como función SQL `anonimizar_candidato` (migración `0002`).

### 5.6 Postulaciones por correo

- `asignar` crea un candidato nuevo con `canal = correo`, mueve el PDF a la carpeta de la vacante, enlaza `correos_sin_asignar.asignado_a` con el candidato creado y dispara la calificación (regla 5.3).
- **Autorización de datos:** el candidato que envía su HV por correo no marcó una casilla. Se registra `autorizacion_version = "correo-1.0"`, entendida como autorización por conducta inequívoca, **siempre que la publicación de la vacante incluya el aviso de privacidad** [VERIFICAR con asesoría legal]. Además, el sistema le responde con un correo que enlaza la política de datos.

### 5.7 Modelos Pydantic separados

Mismo concepto, formas distintas según la audiencia:

| Modelo | Uso | Campos |
|---|---|---|
| `CriterioPublico` | `GET /api/vacantes/{slug}` | `habilidad` (nombre), `obligatoria` |
| `CriterioAdmin` | `POST/PATCH /api/admin/vacantes` | `habilidad_id`, `obligatoria`, `peso` |

Regla general: los modelos públicos nunca exponen IDs internos de habilidades, pesos ni datos de candidatos.

### 5.8 Sprint 3 (decisiones)

- **Listas paginadas.** `GET /api/admin/reserva` y `GET /api/admin/correos-sin-asignar` responden `{ items, total, page, page_size }`. `correos-sin-asignar` solo trae los pendientes e incluye `archivo_nombre` (columna nueva, migración `0003`; la llena el job de ingesta).
- **Reserva · filtros.** `habilidad_id` repetido exige tener **todas** las habilidades; `cargo` busca dentro del cargo de la vacante de origen. Solo candidatos en `reserva` y no anonimizados.
- **`POST /reserva/{candidato_id}/asociar`** → `201` con el candidato **nuevo**: se crea otra postulación del mismo titular en la vacante destino (debe estar activa, distinta de la original y sin postulación previa). Nace en `nuevo`, sin nota (la IA califica contra los criterios nuevos); el original sigue en `reserva`. Conserva la autorización original [VERIFICAR con asesoría legal que cubra otras vacantes].
- **`POST /correos-sin-asignar/{id}/asignar`** → `201`. Nombre y correo salen del remitente (`Nombre <correo>`); si no hay nombre se usa la parte local del correo; `celular` queda vacío. `404` si ya fue asignado. La calificación con IA se dispara al integrarse `integraciones/ia.py`.
- **`POST /candidatos/{id}/anonimizar`** (solo `lider`, `403` para otros roles). Anonimiza **todas** las postulaciones del mismo correo y sus correos sin asignar, borra el PDF en Drive **antes** (si falla: `502` y no se toca la base) y deja un evento en el historial sin datos personales. `409` si ya estaba anonimizado.
- **`POST /vacantes/{id}/reporte`** → `202`. Solo acepta destinatarios del dominio `ALLOWED_EMAIL_DOMAIN`; el ranking excluye `no_apto` y anonimizados. Los roles `gerencia` consultan pero no envían.

## Pendientes [POR CONFIRMAR]

- Tamaño máximo del PDF (mientras tanto, `MAX_PDF_MB=5` en `.env`).
- Frecuencia del job de correo.
- Formato del código de vacante en el asunto del correo (ej. `[GSC-0425]`).
- Correos de gerencia para el reporte.
- Si algún usuario del centro de mando (p. ej. gerencia) no tiene cuenta `@immpetus.co`: se agrega como excepción en `usuarios`, sin crear login con contraseña.
