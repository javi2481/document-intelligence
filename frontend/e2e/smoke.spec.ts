import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE = path.resolve(__dirname, "../../archivos_pruebas/doc_01.webp");
const BACKEND_URL = process.env.VITE_API_URL ?? "http://127.0.0.1:8100";

test.describe("smoke OCR manual fixture", () => {
  test.beforeAll(async ({ request }) => {
    const health = await request.get(`${BACKEND_URL}/health`);
    test.skip(
      !health.ok(),
      `Backend no disponible en ${BACKEND_URL}. Arrancá el API (uvicorn :8100) antes de e2e.`,
    );
  });

  test("upload doc_01 → Run → regiones detectadas", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("LexOCR")).toBeVisible();

    await page.getByTestId("file-input").setInputFiles(FIXTURE);
    await expect(page.getByText("doc_01.webp")).toBeVisible({ timeout: 30_000 });

    await page.getByTestId("run-selected").click();

    // Espera OCR real (primera corrida puede incluir carga de modelos).
    await expect(page.getByLabel("Palabras detectadas")).toContainText(/[1-9]\d*/, {
      timeout: 240_000,
    });
    await expect(page.getByLabel("Métricas")).not.toContainText("—", { timeout: 10_000 });
  });
});
