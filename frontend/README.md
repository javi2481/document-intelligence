# LexOCR — frontend

## Qué hace

Studio web: galería (incluye páginas de PDF/TIFF), visor con boxes, ResultText espacial, edición de palabras y export a formatos LLM-ready.

## Entrada / salida

- **Entrada:** imágenes y **PDF** / TIFF (upload API). Un documento se expande a N ítems en la galería; la UI auto-dispara `/infer` por página.
- **Salida:** UI + descargas JSON / MD / CSV / TXT / PNG anotado (`page_index` en export de páginas; export documento consolidado).

## Desarrollo

```bash
npm install
npm run dev
```

Backend por defecto: `http://localhost:8100`. Override:

```powershell
$env:VITE_API_URL="http://localhost:8100"
npm run dev
```

## Build

```bash
npm run build
```

## Tests

### Vitest (rápido)

```bash
npm test
npm run test:watch
```

Libs puras: `readingOrder`, `consolidate`, `documentGroups`, `buildExportResult` / `buildExportDocument`.

### Playwright e2e (opt-in)

Requiere API en `http://127.0.0.1:8100` (OCR real). El frontend lo arranca Playwright.

```bash
npm install
npx playwright install chromium
# en otra terminal: backend uvicorn :8100
npm run test:e2e
```

Smoke: subset de `archivos_pruebas/` (`doc_01`, `doc_05`, `doc_08`, `doc_12` → Run; `doc_07.pdf` → auto-OCR) → espera regiones en «Palabras detectadas».

**No cubre (Vitest):** DOM/`downloadBlob`. **E2e** no corre en `npm test`.

## Qué no hace

No ejecuta OCR en el browser; no selecciona tier/mode (motor fixed medium en API).

## Archivos relacionados

- [src/README.md](src/README.md)
- [src/lib/README.md](src/lib/README.md)
- [../docs/PRODUCT.md](../docs/PRODUCT.md)
- [../README.md](../README.md#tests-automatizados)
