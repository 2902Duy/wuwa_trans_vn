import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const reportPath = "mistral_translate_work/reports/remaining_split_format_issues_after_fix/hits.json";
const outputDir = "mistral_translate_work/reports/remaining_split_format_issues_after_fix";
const outputPath = `${outputDir}/remaining_review_items.xlsx`;

function colName(index) {
  let n = index + 1;
  let name = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    name = String.fromCharCode(65 + rem) + name;
    n = Math.floor((n - 1) / 26);
  }
  return name;
}

function rangeFor(sheet, rowCount, colCount) {
  return `${sheet}!A1:${colName(colCount - 1)}${rowCount}`;
}

function countBy(items, key) {
  const counts = new Map();
  for (const item of items) {
    const value = item[key] || "";
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

const raw = await fs.readFile(reportPath, "utf8");
const hits = JSON.parse(raw);
const workbook = Workbook.create();

const review = workbook.worksheets.add("Review_Items");
const summaryDomain = workbook.worksheets.add("Summary_By_Domain");
const summaryKind = workbook.worksheets.add("Summary_By_Kind");

const headers = [
  "review_status",
  "kind",
  "domain",
  "file",
  "index",
  "split_id",
  "source_en",
  "current_new_translation_vi",
  "new_translation_vi_fixed",
  "note",
];

const rows = hits.map((h) => [
  "needs_review",
  h.kind || "",
  h.domain || "",
  h.file || "",
  h.index ?? "",
  h.split_id || "",
  h.source_en || "",
  h.new_translation_vi || "",
  "",
  "",
]);

review.getRange(rangeFor("Review_Items", rows.length + 1, headers.length)).values = [headers, ...rows];

const domainRows = [["domain", "count"], ...countBy(hits, "domain")];
summaryDomain.getRange(rangeFor("Summary_By_Domain", domainRows.length, 2)).values = domainRows;

const kindRows = [["kind", "count"], ...countBy(hits, "kind")];
summaryKind.getRange(rangeFor("Summary_By_Kind", kindRows.length, 2)).values = kindRows;

await workbook.inspect({
  kind: "table",
  range: "Review_Items!A1:J10",
  include: "values",
});

await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, rows: rows.length }, null, 2));
