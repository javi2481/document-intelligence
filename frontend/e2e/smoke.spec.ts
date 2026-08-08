import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CORPUS = path.resolve(__dirname, "../../archivos_pruebas");
const BACKEND_URL = process.env.VITE_API_URL ?? "http://127.0.0.1:8100";

const PDF_EXT = new Set([".pdf"]);
const IMAGE_EXT = new Set([
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
  ".gif",
  ".bmp",
  ".tif",
  ".tiff",
  ".avif",
]);

function listCorpusFiles(): string[] {
  if (!fs.existsSync(CORPUS)) return [];
  return fs
    .readdirSync(CORPUS)
    .filter((name) => {
      const ext = path.extname(name).toLowerCase();
      return IMAGE_EXT.has(ext) || PDF_EXT.has(ext);
    })
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}

const CORPUS_FILES = listCorpusFiles();

test.describe("e2e corpus archivos_pruebas (completo)", () => {
  test.beforeAll(async ({ request }) => {
    test.skip(
      CORPUS_FILES.length === 0,
      `No hay archivos en ${CORPUS}`,
    );
    const health = await request.get(`${BACKEND_URL}/health`);
    test.skip(
      !health.ok(),
      `Backend no disponible en ${BACKEND_URL}. Arrancá el API (uvicorn :8100) antes de e2e.`,
    );
  });

  for (const filename of CORPUS_FILES) {
    const ext = path.extname(filename).toLowerCase();
    const isPdf = PDF_EXT.has(ext);

    test(`${filename}: upload → OCR → regiones`, async ({ page }) => {
      await page.goto("/");
      await expect(page.getByText("LexOCR")).toBeVisible();

      await page.getByTestId("file-input").setInputFiles(path.join(CORPUS, filename));

      if (isPdf) {
        // Raster + auto-/infer por página.
        await expect(page.getByText(/p\.1/i).first()).toBeVisible({ timeout: 90_000 });
      } else {
        await expect(page.getByText(filename)).toBeVisible({ timeout: 30_000 });
        await page.getByTestId("run-selected").click();
      }

      await expect(page.getByLabel("Palabras detectadas")).toContainText(/[1-9]\d*/, {
        timeout: 300_000,
      });
    });
  }
});
