import { describe, expect, it } from "vitest";
import { buildExportResult } from "./exportResult";
import type { OCRResult, Region } from "../types/ocr";

function region(id: number, text: string, confidence = 0.95): Region {
  return {
    id,
    text,
    confidence,
    bbox: { x: id * 10, y: 0, width: 20, height: 8 },
    poly: [
      [id * 10, 0],
      [id * 10 + 20, 0],
      [id * 10 + 20, 8],
      [id * 10, 8],
    ],
    orientation: id === 1 ? -90 : 0,
  };
}

function sampleResult(partial: Partial<OCRResult> = {}): OCRResult {
  const regions = [region(0, "alpha"), region(1, "beta")];
  return {
    image_id: "img-1",
    filename: "page.png",
    status: "completed",
    inference_time_ms: 12,
    confidence_avg: 0.95,
    regions_count: regions.length,
    low_confidence_count: 0,
    regions,
    width: 100,
    height: 80,
    ocr_tier: "medium",
    ...partial,
  };
}

describe("buildExportResult", () => {
  const ordered = [region(0, "alpha"), region(1, "beta")];
  const cleanText = "alpha\nbeta";

  it("json includes reading_order, ocr_tier and page fields", () => {
    const result = sampleResult({
      page_index: 1,
      page_count: 3,
      source_format: "pdf",
    });
    const built = buildExportResult("json", {
      result,
      filename: "doc.pdf",
      orderedRegions: ordered,
      cleanText,
    });
    expect(built.filename).toBe("doc.json");
    expect(built.mime).toBe("application/json");
    const payload = JSON.parse(built.content);
    expect(payload.ocr_tier).toBe("medium");
    expect(payload.page_index).toBe(1);
    expect(payload.page_count).toBe(3);
    expect(payload.regions.map((r: { reading_order: number }) => r.reading_order)).toEqual([
      0, 1,
    ]);
  });

  it("md includes page_index frontmatter and region table", () => {
    const result = sampleResult({
      page_index: 0,
      page_count: 2,
      source_format: "tiff",
    });
    const built = buildExportResult("md", {
      result,
      filename: "scan.tiff",
      orderedRegions: ordered,
      cleanText,
    });
    expect(built.filename).toBe("scan.md");
    expect(built.content).toContain("page_index: 0");
    expect(built.content).toContain("page_count: 2");
    expect(built.content).toContain("# Regiones");
    expect(built.content).toContain("| 0 | 0 | alpha |");
  });

  it("csv and txt follow orderedRegions", () => {
    const result = sampleResult();
    const csv = buildExportResult("csv", {
      result,
      filename: "a.png",
      orderedRegions: ordered,
      cleanText,
    });
    expect(csv.content.split("\n")[0]).toContain("reading_order");
    expect(csv.content).toContain('"alpha"');
    expect(csv.content).toContain('"beta"');

    const txt = buildExportResult("txt", {
      result,
      filename: "a.png",
      orderedRegions: ordered,
      cleanText,
    });
    expect(txt.content).toBe("alpha\nbeta");
  });
});
