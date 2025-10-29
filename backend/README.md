# ChatKit Python Backend

> For the steps to run both fronend and backend apps in this repo, please refer to the README.md at the top directory insteaad.

This FastAPI service wires up a minimal ChatKit server implementation with tools for weather and theme switching.

## Features

- **ChatKit endpoint** at `POST /chatkit` that streams responses using the ChatKit protocol when the optional ChatKit Python package is installed.
- **Guardrail-ready system prompt** extracted into `app/constants.py` so it is easy to modify.
- **REST helpers**
  - `GET  /health` – surface a basic health indicator

## Getting started

To enable the realtime assistant you need to install both the ChatKit Python package and the OpenAI SDK, then provide an `OPENAI_API_KEY` environment variable.

```bash
uv sync
export OPENAI_API_KEY=sk-proj-...
uv run uvicorn app.main:app --reload
```

## Raw Markdown Transcripts

Place `.md` files in `app/raw_transcripts/` and restart the backend. They will be exposed as `@doc_{slug}` tags derived from filenames (lowercased; non-alphanumeric → `_`; repeated `_` collapsed).

Examples from this repo:

- `Oxy <> Weekly Planning.md` → `@doc_oxy_weekly_planning`
- `Craig - Oxy.md` → `@doc_craig_oxy`
- ` Andrew Fitasy Check In.md` → `@doc_andrew_fitasy_check_in`
- `Oxy Internal Sales Planning.md` → `@doc_oxy_internal_sales_planning`
- `Soraban <> Oxy - Weekly Sync.md` → `@doc_soraban_oxy_weekly_sync`

Notes:
- The transcript "summary" is optional and omitted from context if missing.
- The full Markdown file content is passed to the model as the transcript body.
