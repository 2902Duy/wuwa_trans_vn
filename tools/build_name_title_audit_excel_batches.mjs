import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const reportDir = path.join(root, "mistral_translate_work", "reports", "name_title_english_audit");
const outputDir = path.join(root, "outputs", "name_title_audit", "batches_500");
const batchSize = 500;

async function readJson(name) {
  return JSON.parse(await fs.readFile(path.join(reportDir, name), "utf8"));
}

function safeText(value) {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function colName(index) {
  let n = index + 1;
  let result = "";
  while (n > 0) {
    const remainder = (n - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    n = Math.floor((n - 1) / 26);
  }
  return result;
}

function rangeAddress(rowCount, colCount) {
  return `A1:${colName(colCount - 1)}${rowCount}`;
}

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
];

function rowToRecord(row) {
  return [
    safeText(row.split_id),
    safeText(row.json_file),
    row.json_index ?? "",
    safeText(row.source_file),
    safeText(row.database),
    safeText(row.table),
    safeText(row.primary_key),
    safeText(row.findings),
    safeText(row.keep_reason),
    row.keep_allowed ? "YES" : "NO",
    row.source_translatable ? "YES" : "NO",
    safeText(row.unauthorized_english_tokens),
    safeText(row.source_en),
    safeText(row.new_translation_vi),
    "",
  ];
}

function chunks(rows, size) {
  const result = [];
  for (let i = 0; i < rows.length; i += size) {
    result.push(rows.slice(i, i + size));
  }
  return result;
}

async function writeBatch(groupName, groupSlug, batchRows, batchIndex, batchCount) {
  const workbook = Workbook.create();
  const summary = workbook.worksheets.add("Summary");
  summary.getRange("A1:B6").values = [
    ["Metric", "Value"],
    ["Group", groupName],
    ["Batch", `${batchIndex + 1}/${batchCount}`],
    ["Rows in batch", batchRows.length],
    ["Batch size limit", batchSize],
    ["Fill translations in", "retranslate_vi"],
  ];
  summary.getRange("A1:B1").format.fill = "accent1";
  summary.getRange("A1:B1").format.font = { color: "lt1", bold: true };
  summary.getRange("A:A").format.columnWidthPx = 180;
  summary.getRange("B:B").format.columnWidthPx = 260;

  const sheet = workbook.worksheets.add("Translation Batch");
  const matrix = [headers, ...batchRows.map(rowToRecord)];
  sheet.getRange(rangeAddress(matrix.length, headers.length)).values = matrix;
  sheet.getRange(rangeAddress(1, headers.length)).format.fill = "accent1";
  sheet.getRange(rangeAddress(1, headers.length)).format.font = { color: "lt1", bold: true };
  sheet.getRange(rangeAddress(1, headers.length)).format.wrapText = true;
  sheet.getRange("A:A").format.columnWidthPx = 120;
  sheet.getRange("B:B").format.columnWidthPx = 260;
  sheet.getRange("G:G").format.columnWidthPx = 260;
  sheet.getRange("L:L").format.columnWidthPx = 220;
  sheet.getRange("M:O").format.columnWidthPx = 520;

  const fileName = `${groupSlug}_part_${String(batchIndex + 1).padStart(3, "0")}.xlsx`;
  const outputPath = path.join(outputDir, fileName);
  const exported = await SpreadsheetFile.exportXlsx(workbook);
  await exported.save(outputPath);
  return { file: fileName, group: groupName, rows: batchRows.length };
}

const exact = await readJson("english_not_translated_exact.json");
const partial = await readJson("english_not_translated_no_vietnamese.json");
const mixed = await readJson("mixed_english_vietnamese_unauthorized.json");

const groups = [
  {
    name: "Not Translated",
    slug: "not_translated",
    rows: [...exact.rows, ...partial.rows],
  },
  {
    name: "Mixed Unauthorized",
    slug: "mixed_unauthorized",
    rows: mixed.rows,
  },
];

await fs.mkdir(outputDir, { recursive: true });
const manifest = [];
for (const group of groups) {
  const parts = chunks(group.rows, batchSize);
  for (let index = 0; index < parts.length; index += 1) {
    manifest.push(await writeBatch(group.name, group.slug, parts[index], index, parts.length));
  }
}

const manifestData = {
  batch_size: batchSize,
  total_files: manifest.length,
  total_rows: manifest.reduce((sum, item) => sum + item.rows, 0),
  files: manifest,
};
await fs.writeFile(
  path.join(outputDir, "manifest.json"),
  JSON.stringify(manifestData, null, 2) + "\n",
  "utf8",
);
console.log(JSON.stringify({ outputDir, ...manifestData }, null, 2));
