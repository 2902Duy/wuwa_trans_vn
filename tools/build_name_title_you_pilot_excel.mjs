import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const inputPath = path.join(
  root,
  "outputs",
  "name_title_audit",
  "you_pilot",
  "pilot_translations.json",
);
const outputPath = path.join(
  root,
  "outputs",
  "name_title_audit",
  "you_pilot",
  "name_title_you_pilot_10.xlsx",
);

const data = JSON.parse(await fs.readFile(inputPath, "utf8"));
const rows = data.rows;
const changedCount = rows.filter((row) => row.validation.changed_from_source).length;
const tokenPassCount = rows.filter(
  (row) => row.validation.protected_tokens_match,
).length;

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
summary.getRange("A1:B7").values = [
  ["Metric", "Value"],
  ["Provider", "You.com"],
  ["Agent", data.agent],
  ["Pilot rows", rows.length],
  ["Translated/changed", changedCount],
  ["Kept unchanged - review", rows.length - changedCount],
  ["Protected token checks passed", tokenPassCount],
];
summary.getRange("A1:B1").format.fill = "accent1";
summary.getRange("A1:B1").format.font = { color: "lt1", bold: true };
summary.getRange("A:A").format.columnWidthPx = 230;
summary.getRange("B:B").format.columnWidthPx = 260;

const sheet = workbook.worksheets.add("Pilot Translation");
const headers = [
  "split_id",
  "json_file",
  "json_index",
  "source_file",
  "table",
  "primary_key",
  "source_en",
  "old_translation_vi",
  "retranslate_vi",
  "qc_status",
  "qc_note",
];
const matrix = [
  headers,
  ...rows.map((row) => {
    const changed = row.validation.changed_from_source;
    const tokensOk = row.validation.protected_tokens_match;
    let status = "PASS";
    let note = "";
    if (!tokensOk) {
      status = "FAIL_TOKEN";
      note = "Placeholder/tag mismatch";
    } else if (!changed) {
      status = "REVIEW_KEEP";
      note = "API treated this as a proper name; verify manually";
    }
    return [
      row.split_id,
      row.json_file,
      row.json_index,
      row.source_file,
      row.table,
      row.primary_key,
      row.source_en,
      row.new_translation_vi,
      row.retranslate_vi,
      status,
      note,
    ];
  }),
];

sheet.getRange(`A1:K${matrix.length}`).values = matrix;
sheet.getRange("A1:K1").format.fill = "accent1";
sheet.getRange("A1:K1").format.font = { color: "lt1", bold: true };
sheet.getRange("A1:K1").format.wrapText = true;
sheet.getRange("A:A").format.columnWidthPx = 145;
sheet.getRange("B:B").format.columnWidthPx = 300;
sheet.getRange("C:C").format.columnWidthPx = 90;
sheet.getRange("D:F").format.columnWidthPx = 150;
sheet.getRange("G:I").format.columnWidthPx = 360;
sheet.getRange("G:K").format.wrapText = true;
sheet.getRange("J:J").format.columnWidthPx = 130;
sheet.getRange("K:K").format.columnWidthPx = 290;

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);

const inspect = await workbook.inspect({
  kind: "table",
  range: "Pilot Translation!A1:K11",
  include: "values,formulas",
  tableMaxRows: 12,
  tableMaxCols: 12,
});
console.log(inspect.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "pilot formula error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({
  sheetName: "Pilot Translation",
  range: "A1:K11",
  scale: 1,
  format: "png",
});
await fs.writeFile(
  path.join(
    root,
    "outputs",
    "name_title_audit",
    "you_pilot",
    "name_title_you_pilot_10_preview.png",
  ),
  Buffer.from(await preview.arrayBuffer()),
);
console.log(outputPath);
