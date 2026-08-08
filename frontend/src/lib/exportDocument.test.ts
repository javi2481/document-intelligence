import { describe, expect, it } from "vitest";
import { buildExportDocument } from "./exportDocument";
import type { ConsolidatedDocument } from "./consolidate";
import type { OCRResult, Region } from "../types/ocr";

function region(id: number, text: string): Region {
  return {
    id,
    text,
    confidence: 0.9,
    bbox: { x: 0, y: id * 10, width: 30, height: 8 },
  };
}

function pageResult(page_index: number, texts: string[]): OCRResult {
  const regions = texts.map((t, i) => region(i, t));
  return {
    image_id: `p${page_index}`,
    filename: `doc · p.${page_index + 1}/2`,
    status: "completed",
    inference_time_ms: 10,
    confidence_avg: 0.9,
    regions_count: regions.length,
    low_confidence_count: 0,
    regions,
    width: 100,
    height: 100,
    page_index,
    page_count: 2,
    ocr_tier: "medium",
  };
}

function sampleDoc(): ConsolidatedDocument {
  const p0 = pageResult(0, ["uno"]);
  const p1 = pageResult(1, ["dos", "tres"]);
  return {
    cleanText: "--- página 1 ---\n\nuno\n\n--- página 2 ---\n\ndos\ntres",
    pages: [
      {
        localId: "a",
        pageIndex: 0,
        pageLabel: "página 1",
        result: p0,
        orderedRegions: p0.regions,
        cleanText: "uno",
      },
      {
        localId: "b",
        pageIndex: 1,
        pageLabel: "página 2",
        result: p1,
        orderedRegions: p1.regions,
        cleanText: "dos\ntres",
      },
    ],
    metrics: {
      confidence_avg: 0.9,
      regions_count: 3,
      regions_to_review: 0,
      pages_with_low: 0,
    },
    processedCount: 2,
    totalCount: 2,
    isComplete: true,
  };
}

describe("buildExportDocument", () => {
  it("json includes page_index, reading_order, metrics and isComplete", () => {
    const built = buildExportDocument("json", {
      filename: "informe.pdf",
      consolidated: sampleDoc(),
    });
    expect(built.filename).toBe("informe.json");
    const payload = JSON.parse(built.content);
    expect(payload.isComplete).toBe(true);
    expect(payload.metrics.regions_count).toBe(3);
    expect(payload.pages).toHaveLength(2);
    expect(payload.pages[0].page_index).toBe(0);
    expect(payload.pages[1].regions.map((r: { reading_order: number }) => r.reading_order)).toEqual([
      0, 1,
    ]);
  });

  it("md frontmatter has pages and processed", () => {
    const built = buildExportDocument("md", {
      filename: "informe.pdf",
      consolidated: sampleDoc(),
    });
    expect(built.content).toContain("pages: 2");
    expect(built.content).toContain("processed: 2");
    expect(built.content).toContain("# Texto limpio");
  });

  it("csv has page_index column", () => {
    const built = buildExportDocument("csv", {
      filename: "informe.pdf",
      consolidated: sampleDoc(),
    });
    const lines = built.content.split("\n");
    expect(lines[0].startsWith("page_index")).toBe(true);
    expect(lines.some((l) => l.startsWith("0,"))).toBe(true);
    expect(lines.some((l) => l.startsWith("1,"))).toBe(true);
  });
});
