# Immpetus · Sistema de selección de talento

Web pública con vacantes + centro de mando + agente de IA que califica hojas de vida.
Antes de escribir código lee **`CLAUDE.md`** (reglas y convenciones) y **`docs/CONTRATO_API.md`**.

## Requisitos (instalar una sola vez)

| Herramienta    | Versión                    | Quién la necesita                                  | Cómo instalar (Windows)                                  |
| -------------- | -------------------------- | -------------------------------------------------- | -------------------------------------------------------- |
| Git            | reciente                   | Todos                                              | git-scm.com                                              |
| Node.js        | 22 (ver `frontend/.nvmrc`) | Todos (también para `npx supabase`)                | nodejs.org (versión LTS 22)                              |
| uv             | última                     | Backend e integraciones (instala Python 3.12 solo) | `winget install --id=astral-sh.uv -e` y reabrir VS Code  |
| Docker Desktop | última (activar WSL2)      | Backend e integraciones (base local)               | docker.com                                               |
| VS Code        | —                          | Todos                                              | Aceptar las extensiones recomendadas al abrir la carpeta |

La CLI de Supabase **no se instala**: se usa con `npx supabase`.

## Primer arranque

```bash
git clone <url-del-repo> immpetus
cd immpetus
cp .env.example .env          # PowerShell: copy .env.example .env
```

Pedir los valores del `.env` al equipo. **Nunca subir `.env`.**

**Frontend**

```bash
cd frontend
npm ci                        # instala EXACTAMENTE lo de package-lock.json
npm run dev                   # http://localhost:3000
```

**Backend / integraciones**

```bash
cd backend
uv sync                       # instala EXACTAMENTE lo de uv.lock
uv run uvicorn app.main:app --reload   # http://localhost:8000/health
```

O con Docker desde la raíz: `docker compose up api`

## Base de datos (Supabase / PostgreSQL)

La base ya está creada en la nube. **Nadie debe correr `supabase init` ni crear otro proyecto.**

### Opción A · Base compartida en la nube

Para probar junto con el resto del equipo.

1. Pedir a Jerónimo la invitación a la organización "Immpetus" en Supabase.
2. En el panel: Project Settings → Database → Connection string → copiar en `.env` como `DATABASE_URL`.

### Opción B · Copia local con Docker

Para experimentar sin afectar a nadie. Requiere Docker Desktop abierto.

```bash
npx supabase start      # levanta Postgres local
npx supabase db reset   # aplica el esquema de supabase/migrations/
npx supabase stop       # al terminar
```

En `.env`: `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54322/postgres`
Panel local: http://localhost:54323

### Cambiar el esquema (tablas o columnas)

1. `npx supabase migration new nombre_del_cambio`
2. Escribir el SQL en el archivo creado y probar en local con `npx supabase db reset`.
3. Subirlo por PR.
4. Después del merge, **solo backend o Jerónimo** aplica en la nube: `npx supabase db push`.

Nunca modificar tablas a mano desde el panel de Supabase.

## Reglas de dependencias

- Nunca subir `node_modules/` ni `.venv/`.
- Agregar dependencia: `npm install <pkg>` o `uv add <pkg>`, y subir el lock en el mismo PR.
- Instalar siempre con `npm ci` / `uv sync`, no con `npm install` a secas.

## Estructura

```
├── CLAUDE.md                 contexto y reglas para el equipo y para Claude
├── docs/                     contrato de la API y plan de sprints
├── supabase/                 config.toml y migrations/ (esquema de la base)
├── frontend/                 Next.js + TypeScript + Tailwind
└── backend/                  FastAPI + integraciones (Gmail, Drive, IA)
```
