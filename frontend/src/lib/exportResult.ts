import type { OCRResult, Region } from "../types/ocr";

export type ExportFormat = "json" | "md" | "csv" | "txt";

export type ExportResultOptions = {
  result: OCRResult;
  filename: string;
  orderedRegions: Region[];
  cleanText: string;
};

export type BuiltExport = {
  filename: string;
  content: string;
  mime: string;
};

export function downloadBlob(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/** Serializa un OCRResult a JSON/MD/CSV/TXT (sin DOM). */
export function buildExportResult(
  format: ExportFormat,
  { result, filename, orderedRegions, cleanText }: ExportResultOptions,
): BuiltExport {
  const base = filename.replace(/\.[^.]+$/, "") || "ocr";
  const orderIndex = new Map(orderedRegions.map((r, i) => [r.id, i]));
  const polyStr = (r: Region) => (r.poly ?? []).map((p) => `${p[0]},${p[1]}`).join(";");

  if (format === "json") {
    const payload = {
      ...result,
      ocr_tier: result.ocr_tier ?? "medium",
      regions: orderedRegions.map((r) => ({
        ...r,
        orientation: r.orientation ?? 0,
        reading_order: orderIndex.get(r.id) ?? r.id,
      })),
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
      `ocr_tier: ${result.ocr_tier ?? "medium"}`,
      ...(result.page_index != null
        ? [
            `page_index: ${result.page_index}`,
            `page_count: ${result.page_count ?? ""}`,
            `source_format: ${result.source_format ?? ""}`,
          ]
        : []),
      `regions_count: ${result.regions_count}`,
      `confidence_avg: ${result.confidence_avg}`,
      `low_confidence_count: ${result.low_confidence_count}`,
      `inference_time_ms: ${result.inference_time_ms}`,
      `width: ${result.width}`,
      `height: ${result.height}`,
      "---",
      "",
      "# Texto limpio",
      "",
      cleanText || "_(sin texto)_",
      "",
      "# Regiones",
      "",
      "| id | reading_order | text | confidence | orientation | x | y | w | h |",
      "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
      ...orderedRegions.map((r) => {
        const text = r.text.replace(/\|/g, "\\|").replace(/\n/g, " ");
        return `| ${r.id} | ${orderIndex.get(r.id) ?? r.id} | ${text} | ${r.confidence} | ${r.orientation ?? 0} | ${r.bbox.x} | ${r.bbox.y} | ${r.bbox.width} | ${r.bbox.height} |`;
      }),
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
        "id",
        "reading_order",
        "text",
        "confidence",
        "orientation",
        "x",
        "y",
        "width",
        "height",
        "poly",
      ],
      ...orderedRegions.map((r) => [
        r.id,
        orderIndex.get(r.id) ?? r.id,
        `"${r.text.replace(/"/g, '""')}"`,
        r.confidence,
        r.orientation ?? 0,
        r.bbox.x,
        r.bbox.y,
        r.bbox.width,
        r.bbox.height,
        `"${polyStr(r)}"`,
      ]),
    ];
    return {
      filename: `${base}.csv`,
      content: rows.map((row) => row.join(",")).join("\n"),
      mime: "text/csv",
    };
  }

  return {
    filename: `${base}.txt`,
    content: orderedRegions.map((r) => r.text).join("\n"),
    mime: "text/plain",
  };
}

export function exportResult(format: ExportFormat, opts: ExportResultOptions) {
  const built = buildExportResult(format, opts);
  downloadBlob(built.filename, built.content, built.mime);
}
