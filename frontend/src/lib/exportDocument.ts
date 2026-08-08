import type { ExportFormat, BuiltExport } from "./exportResult";
import { downloadBlob } from "./exportResult";
import type { ConsolidatedDocument } from "./consolidate";

export type ExportDocumentOptions = {
  filename: string;
  consolidated: ConsolidatedDocument;
};

/** Serializa un documento consolidado a JSON/MD/CSV/TXT (sin DOM). */
export function buildExportDocument(
  format: ExportFormat,
  { filename, consolidated }: ExportDocumentOptions,
): BuiltExport {
  const base = filename.replace(/\.[^.]+$/, "") || "document";
  const { cleanText, pages, metrics } = consolidated;

  if (format === "json") {
    const payload = {
      document: filename,
      metrics,
      processedCount: consolidated.processedCount,
      totalCount: consolidated.totalCount,
      isComplete: consolidated.isComplete,
      pages: pages.map((page) => ({
        page_index: page.pageIndex,
        filename: page.result.filename,
        confidence_avg: page.result.confidence_avg,
        regions_count: page.result.regions_count,
        low_confidence_count: page.result.low_confidence_count,
        ocr_tier: page.result.ocr_tier ?? "medium",
        regions: page.orderedRegions.map((r, i) => ({
          ...r,
          orientation: r.orientation ?? 0,
          reading_order: i,
        })),
      })),
      cleanText,
    };
    return {
      filename: `${base}.json`,
      content: JSON.stringify(payload, null, 2),
      mime: "application/json",
    };
  }

  if (format === "md") {
    const lines = [
      "---",
      `filename: ${filename}`,
      `pages: ${consolidated.totalCount}`,
      `processed: ${consolidated.processedCount}`,
      `regions_count: ${metrics.regions_count}`,
      `confidence_avg: ${metrics.confidence_avg}`,
      `low_confidence_count: ${metrics.regions_to_review}`,
      `pages_with_low: ${metrics.pages_with_low}`,
      "---",
      "",
      "# Texto limpio",
      "",
      cleanText || "_(sin texto)_",
      "",
    ];
    return {
      filename: `${base}.md`,
      content: lines.join("\n"),
      mime: "text/markdown",
    };
  }

  if (format === "csv") {
    const rows = [
      [
        "page_index",
        "id",
        "reading_order",
        "text",
        "confidence",
        "orientation",
        "x",
        "y",
        "width",
        "height",
      ],
      ...pages.flatMap((page) =>
        page.orderedRegions.map((r, i) => [
          page.pageIndex,
          r.id,
          i,
          `"${r.text.replace(/"/g, '""')}"`,
          r.confidence,
          r.orientation ?? 0,
          r.bbox.x,
          r.bbox.y,
          r.bbox.width,
          r.bbox.height,
        ]),
      ),
    ];
    return {
      filename: `${base}.csv`,
      content: rows.map((row) => row.join(",")).join("\n"),
      mime: "text/csv",
    };
  }

  return {
    filename: `${base}.txt`,
    content: cleanText,
    mime: "text/plain",
  };
}

export function exportDocument(format: ExportFormat, opts: ExportDocumentOptions) {
  const built = buildExportDocument(format, opts);
  downloadBlob(built.filename, built.content, built.mime);
}
