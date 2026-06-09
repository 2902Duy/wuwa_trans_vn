import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const inputPath = path.join(
  root,
  "outputs",
  "name_title_audit",
  "you_all",
  "translations_all.json",
);
const outputDir = path.join(
  root,
  "outputs",
  "name_title_audit",
  "you_all",
  "excel_batches_500",
);
const batchSize = 500;

const data = JSON.parse(await fs.readFile(inputPath, "utf8"));
const headers = [
  "split_id",
  "json_file",
  "json_index",
  "source_file",
  "database",
  "table",
  "primary_key",
  "findings",
  "keep_reason",
  "keep_allowed",
  "source_translatable",
  "unauthorized_english_tokens",
  "source_en",
  "new_translation_vi",
  "retranslate_vi",
  "qc_status",
  "qc_note",
];

function text(value) {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function chunks(rows, size) {
  const result = [];
  for (let index = 0; index < rows.length; index += size) {
    result.push(rows.slice(index, index + size));
  }
  return result;
}

function columnName(index) {
  let current = index + 1;
  let result = "";
  while (current > 0) {
    const remainder = (current - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    current = Math.floor((current - 1) / 26);
  }
  return result;
}

function rowValues(row) {
  return [
    text(row.split_id),
    text(row.json_file),
    row.json_index ?? "",
    text(row.source_file),
    text(row.database),
    text(row.table),
    text(row.primary_key),
    text(row.findings),
    text(row.keep_reason),
    row.keep_allowed ? "YES" : "NO",
    row.source_translatable ? "YES" : "NO",
    text(row.unauthorized_english_tokens),
    text(row.source_en),
    text(row.new_translation_vi),
    text(row.retranslate_vi),
    text(row.qc_status),
    text(row.qc_note),
  ];
}

async function writeWorkbook(group, slug, rows, partIndex, partCount) {
  const workbook = Workbook.create();
  const passCount = rows.filter((row) => row.qc_status === "PASS").length;
  const reviewCount = rows.length - passCount;

  const summary = workbook.worksheets.add("Summary");
  summary.getRange("A1:B9").values = [
    ["Metric", "Value"],
    ["Provider", "You.com"],
    ["Agent", data.agent],
    ["Group", group],
    ["Batch", `${partIndex + 1}/${partCount}`],
    ["Rows", rows.length],
    ["QC PASS", passCount],
    ["QC review required", reviewCount],
    ["Translation column", "retranslate_vi"],
  ];
  summary.getRange("A1:B1").format.fill = "accent1";
  summary.getRange("A1:B1").format.font = { color: "lt1", bold: true };
  summary.getRange("A:A").format.columnWidthPx = 220;
  summary.getRange("B:B").format.columnWidthPx = 280;

  const sheet = workbook.worksheets.add("Translation Batch");
  const matrix = [headers, ...rows.map(rowValues)];
  const endColumn = columnName(headers.length - 1);
  sheet.getRange(`A1:${endColumn}${matrix.length}`).values = matrix;
  sheet.getRange(`A1:${endColumn}1`).format.fill = "accent1";
  sheet.getRange(`A1:${endColumn}1`).format.font = { color: "lt1", bold: true };
  sheet.getRange(`A1:${endColumn}1`).format.wrapText = true;
  sheet.getRange("A:A").format.columnWidthPx = 145;
  sheet.getRange("B:B").format.columnWidthPx = 300;
  sheet.getRange("C:C").format.columnWidthPx = 90;
  sheet.getRange("D:L").format.columnWidthPx = 145;
  sheet.getRange("M:O").format.columnWidthPx = 430;
  sheet.getRange("P:P").format.columnWidthPx = 150;
  sheet.getRange("Q:Q").format.columnWidthPx = 310;
  sheet.getRange(`M2:Q${matrix.length}`).format.wrapText = true;

  const fileName = `${slug}_you_part_${String(partIndex + 1).padStart(3, "0")}.xlsx`;
  const filePath = path.join(outputDir, fileName);
  const exported = await SpreadsheetFile.exportXlsx(workbook);
  await exported.save(filePath);
  return {
    file: fileName,
    group,
    rows: rows.length,
    qc_pass: passCount,
    qc_review: reviewCount,
  };
}

await fs.mkdir(outputDir, { recursive: true });
const groups = [
  {
    name: "Not Translated",
    slug: "not_translated",
    rows: data.rows.filter((row) => row.audit_group === "Not Translated"),
  },
  {
    name: "Mixed Unauthorized",
    slug: "mixed_unauthorized",
    rows: data.rows.filter((row) => row.audit_group === "Mixed Unauthorized"),
  },
];

const manifest = [];
for (const group of groups) {
  const parts = chunks(group.rows, batchSize);
  for (let index = 0; index < parts.length; index += 1) {
    manifest.push(
      await writeWorkbook(group.name, group.slug, parts[index], index, parts.length),
    );
  }
}

const manifestData = {
  provider: "you.com",
  agent: data.agent,
  batch_size: batchSize,
  total_files: manifest.length,
  total_rows: manifest.reduce((sum, item) => sum + item.rows, 0),
  source_stats: data.stats,
  files: manifest,
};
await fs.writeFile(
  path.join(outputDir, "manifest.json"),
  JSON.stringify(manifestData, null, 2) + "\n",
  "utf8",
);
console.log(JSON.stringify({ outputDir, ...manifestData }, null, 2));
