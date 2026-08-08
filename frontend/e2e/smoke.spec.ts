import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CORPUS = path.resolve(__dirname, "../../archivos_pruebas");
const BACKEND_URL = process.env.VITE_API_URL ?? "http://127.0.0.1:8100";

/** Subconjunto representativo del corpus (formatos + PDF). */
const IMAGE_CASES = ["doc_01.webp", "doc_05.png", "doc_08.jpg", "doc_12.jpeg"] as const;
const PDF_CASE = "doc_07.pdf";

test.describe("smoke OCR corpus archivos_pruebas", () => {
  test.beforeAll(async ({ request }) => {
    const health = await request.get(`${BACKEND_URL}/health`);
    test.skip(
      !health.ok(),
      `Backend no disponible en ${BACKEND_URL}. Arrancá el API (uvicorn :8100) antes de e2e.`,
    );
  });

  for (const filename of IMAGE_CASES) {
    test(`imagen ${filename}: upload → Run → regiones`, async ({ page }) => {
      await page.goto("/");
      await expect(page.getByText("LexOCR")).toBeVisible();

      await page.getByTestId("file-input").setInputFiles(path.join(CORPUS, filename));
      await expect(page.getByText(filename)).toBeVisible({ timeout: 30_000 });

      await page.getByTestId("run-selected").click();
      await expect(page.getByLabel("Palabras detectadas")).toContainText(/[1-9]\d*/, {
        timeout: 240_000,
      });
    });
  }

  test(`PDF ${PDF_CASE}: upload → auto-OCR → regiones`, async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("LexOCR")).toBeVisible();

    await page.getByTestId("file-input").setInputFiles(path.join(CORPUS, PDF_CASE));
    // Multipágina: aparece al menos p.1 en galería; la UI auto-dispara /infer.
    await expect(page.getByText(/p\.1/i).first()).toBeVisible({ timeout: 60_000 });

    await expect(page.getByLabel("Palabras detectadas")).toContainText(/[1-9]\d*/, {
      timeout: 300_000,
    });
  });
});
