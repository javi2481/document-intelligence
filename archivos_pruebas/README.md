# Corpus manual — `archivos_pruebas/`

Imágenes y un PDF locales para **pruebas manuales** y suites opt-in (golden / e2e).

## Archivos

| Archivo | Tipo |
|---------|------|
| `doc_01.webp` … `doc_06.jpg` | Imágenes |
| `doc_07.pdf` | PDF multipágina |
| `doc_08.jpg` … `doc_12.jpeg` | Imágenes |

## Uso

| Modo | Cómo |
|------|------|
| Manual (UI) | Arrancá `scripts/dev.ps1`, subí un `doc_NN` → Run (PDF auto-OCR) → export |
| Golden OCR | `cd backend` → `pytest -m slow -o addopts=` (todas las imágenes + 1ª pág. del PDF) |
| Playwright e2e | Backend `:8100` + `cd frontend && npm run test:e2e` (**todos** los `doc_*` de esta carpeta) |

Soft asserts: ≥1 región, confAvg ≥ 0.3, texto no vacío (sin strings exactos).

No reemplaza a [`tests/fixtures/images/`](../tests/fixtures/images/README.md) del checklist README (`poster.avif`, nubes, etc.).

## Qué no hace

No entra en `pytest` / `npm test` / CI por defecto. No hay asserts de texto exacto: los documentos pueden variar.
