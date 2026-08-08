# LexOCR — backend

## Qué hace

API FastAPI: subir imágenes o PDF/TIFF, ejecutar PP-OCRv6 medium (engine escena + rescate angular en imágenes) y devolver / exportar resultados listos para revisión y consumo LLM.

## Entrada / salida

- **Entrada:** archivo ≤ 20 MB.
  - Imágenes: PNG, JPEG, WEBP, GIF, BMP, ICO, PPM, AVIF → PNG normalizado + infer bajo demanda.
  - Documentos: **PDF** (`pypdfium2`) / **TIFF** (Pillow) → rasteriza a PNG por página (tope 50); OCR vía `/infer` (progreso por página en UI).
- **Salida:** `OCRResult` JSON (regiones, confianza, `orientation`, `page_index`/`page_count` si aplica, `ocr_tier: medium`) o PNG anotado.

## Ejecución

Desde `backend/`:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8100
```

- API: `http://127.0.0.1:8100`
- OpenAPI: `/docs`

## Endpoints

- `GET /health` — device y engines cacheados (escena)
- `POST /upload` — imagen → 1 `image_id` pending; PDF/TIFF → rasteriza páginas y `pages[]` pending
- `POST /infer/{image_id}` — OCR escena; rescue ON solo si no es página PDF/TIFF
- `POST /infer/batch` — lista de ids
- `GET /image/{image_id}` — PNG de preview
- `GET /status/{image_id}`
- `GET /export/{image_id}/annotated` — PNG con boxes desde el OCRResult guardado (sin re-OCR)

## Engine

| | Escena (único) |
|--|----------------|
| Modelo | PP-OCRv6 medium |
| `use_textline_orientation` | True |
| `use_doc_orientation_classify` | False |
| `use_doc_unwarping` | False (UVDoc OFF; demasiado lento en CPU) |

PDF/TIFF no usan un segundo engine: se rasterizan y se OCR-ean como PNG.

## Entorno

- `PADDLE_PDX_CACHE_HOME=backend/.paddlex` (por defecto en app)
- `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` (seteado en código al arrancar)
- `PADDLEOCR_API_TOKEN` — opcional, solo SDK cloud futuro (no leído por este API)
- Uploads en `backend/uploads/` (store in-memory; se pierde al reiniciar)

## Tests

Suite pytest en [`tests/`](tests/) (app FastAPI de prueba **sin** lifespan / warmup Paddle).

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt   # pytest, httpx (+ deps de requirements.txt)
pytest                                # excluye @pytest.mark.slow (addopts)
```

CI (GitHub Actions) usa [`requirements-ci.txt`](requirements-ci.txt) sin Paddle y corre el mismo `pytest` rápido + `npm test` / build. Ver [`.github/workflows/tests.yml`](../.github/workflows/tests.yml).

Golden OCR real (Paddle; tarda; `archivos_pruebas/doc_01.webp`):

```powershell
pytest -m slow -o addopts=
```

**Cubre (rápido):**
- API/storage: `/health`; `/upload` PNG, TIFF multipágina y PDF; rechazos (>20 MB, >50 págs. vía mock de conteo, formato basura); `/infer` con `_run_paddle` mockeado (rescue ON en imagen, OFF en PDF/TIFF); `/status`; `/export/.../annotated`; `_detect_format` y `_page_filename`.
- Unitarios: `parsing`, helpers de `orientation`, `annotate`.

**Cubre (slow):** soft golden sobre todo el corpus imagen de `archivos_pruebas/` + primera página de `doc_07.pdf` (regiones ≥ 1, confAvg ≥ 0.3, texto no vacío).

**No cubre:** e2e de UI (ver frontend Playwright). Fixtures checklist en [../tests/fixtures/images/](../tests/fixtures/images/README.md); corpus manual en [../archivos_pruebas/](../archivos_pruebas/README.md).

## Qué no hace

StructureV3/VL/HPD, HPI, multi-motor, auth, DB, colas, Docker, Poppler/pdf2image.

## Archivos relacionados

- [app/README.md](app/README.md) — módulos internos
- [../docs/PRODUCT.md](../docs/PRODUCT.md)
- [../README.md](../README.md#tests-automatizados) — cómo correr backend + frontend
