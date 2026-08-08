# Corpus manual — `archivos_pruebas/`

Imágenes y un PDF locales para **pruebas manuales** y suites opt-in (golden / e2e).

## Archivos

`doc_01.webp` … `doc_12.jpeg` (extensión original de cada archivo).

## Uso

| Modo | Cómo |
|------|------|
| Manual (UI) | Arrancá `scripts/dev.ps1`, subí un `doc_NN` → Run → export |
| Golden OCR | `cd backend` → `pytest -m slow -o addopts=` (usa `doc_01.webp`) |
| Playwright e2e | Backend en `:8100` + `cd frontend && npm run test:e2e` (usa `doc_01.webp`) |

No reemplaza a [`tests/fixtures/images/`](../tests/fixtures/images/README.md) del checklist README (`poster.avif`, nubes, etc.).

## Qué no hace

No entra en `pytest` / `npm test` por defecto. No hay asserts de texto exacto: los documentos pueden variar.
