import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const reportDir = path.join(root, "mistral_translate_work", "reports", "name_title_english_audit");
const outputDir = path.join(root, "outputs", "name_title_audit");
const outputPath = path.join(outputDir, "name_title_english_audit.xlsx");

async function readJson(name) {
  return JSON.parse(await fs.readFile(path.join(reportDir, name), "utf8"));
}

function colName(index) {
  let n = index + 1;
  let s = "";
  while (n > 0) {
    const r = (n - 1) % 26;
    s = String.fromCharCode(65 + r) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

function sheetRange(rowCount, colCount) {
  return `A1:${colName(colCount - 1)}${rowCount}`;
}

function safeText(value) {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

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

async function addSheet(workbook, name, headers, rows) {
  const sheet = workbook.worksheets.add(name);
  const matrix = [headers, ...rows];
  const fullRange = sheet.getRange(sheetRange(matrix.length, headers.length));
  fullRange.values = matrix;
  const headerRange = sheet.getRange(sheetRange(1, headers.length));
  headerRange.format.fill = "accent1";
  headerRange.format.font = { color: "lt1", bold: true };
  headerRange.format.wrapText = true;
  sheet.getRange("A:A").format.columnWidthPx = 120;
  sheet.getRange("B:B").format.columnWidthPx = 260;
  sheet.getRange("G:G").format.columnWidthPx = 260;
  sheet.getRange("L:L").format.columnWidthPx = 220;
  sheet.getRange("M:N").format.columnWidthPx = 520;
  return sheet;
}

const summary = await readJson("summary.json");
const untranslatedExact = await readJson("english_not_translated_exact.json");
const untranslatedNoVi = await readJson("english_not_translated_no_vietnamese.json");
const mixed = await readJson("mixed_english_vietnamese_unauthorized.json");
const workbook = Workbook.create();

const summaryRows = [
  ["Metric", "Value"],
  ["Total rows audited", summary.total_rows],
  ["English not translated total", summary.english_not_translated_total_unique_rows],
  ["Mixed English/Vietnamese unauthorized", summary.mixed_english_vietnamese_unauthorized_unique_rows],
  ["Clean or not actionable", summary.counts.clean_or_not_actionable ?? 0],
  ["Kept English allowed by rule", summary.counts.kept_english_allowed ?? 0],
  ["Exact source == translation, not allowed", summary.counts.english_not_translated_exact ?? 0],
  ["Partially/insufficiently translated", summary.counts.english_not_translated_no_vietnamese ?? 0],
  ["Report source folder", summary.report_dir],
];
await addSheet(workbook, "Summary", summaryRows[0], summaryRows.slice(1));

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

const untranslatedRows = [
  ...untranslatedExact.rows.map(rowToRecord),
  ...untranslatedNoVi.rows.map(rowToRecord),
];
await addSheet(workbook, "Not Translated", headers, untranslatedRows);
await addSheet(workbook, "Mixed Unauthorized", headers, mixed.rows.map(rowToRecord));

await fs.mkdir(outputDir, { recursive: true });
const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);
console.log(JSON.stringify({ outputPath, rows: summary.total_rows }, null, 2));
