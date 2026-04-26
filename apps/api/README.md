# py-iku Studio API

FastAPI service wrapping `py2dataiku` for py-iku Studio.

## Install

```bash
# From repo root — installs py2dataiku first, then the API with dev extras
pip install -e .
pip install -e "apps/api[dev]"
```

## Run

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

Interactive docs: <http://localhost:8000/docs>

## Test

```bash
cd apps/api
pytest tests/ -v --tb=short
```

## Environment Variables

All variables use the `PY_IKU_STUDIO_` prefix.

| Variable | Default | Description |
|---|---|---|
| `PY_IKU_STUDIO_ENV` | `dev` | Runtime environment (`dev` / `prod`) |
| `PY_IKU_STUDIO_CORS_ORIGINS` | `["http://localhost:5173"]` | JSON list of allowed CORS origins |
| `PY_IKU_STUDIO_SECRET_KEY` | `change-me-in-production` | HMAC secret for share links |
| `PY_IKU_STUDIO_MAX_PAYLOAD_BYTES` | `262144` | Max request body (bytes) |
| `PY_IKU_STUDIO_DEFAULT_LLM_PROVIDER` | `anthropic` | Default LLM provider |
| `PY_IKU_STUDIO_DEFAULT_LLM_MODEL` | _(provider default)_ | Override LLM model |

## Error responses

All `Py2DataikuError` subclasses are mapped to RFC 7807 `application/problem+json`:

| Exception | HTTP status |
|---|---|
| `InvalidPythonCodeError` | 400 |
| `ConversionError` | 422 |
| `ValidationError` | 422 |
| `ProviderError` / `LLMResponseParseError` | 502 |
| `ExportError` / `ConfigurationError` | 500 |
