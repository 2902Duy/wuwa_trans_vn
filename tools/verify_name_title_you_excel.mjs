import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = process.cwd();
const outputDir = path.join(
  root,
  "outputs",
  "name_title_audit",
  "you_all",
  "excel_batches_500",
);
const files = [
  "not_translated_you_part_001.xlsx",
  "not_translated_you_part_009.xlsx",
  "mixed_unauthorized_you_part_001.xlsx",
];

for (const file of files) {
  const workbook = await SpreadsheetFile.importXlsx(
    await FileBlob.load(path.join(outputDir, file)),
  );
  const inspection = await workbook.inspect({
    kind: "table",
    range: "Translation Batch!M1:Q6",
    include: "values,formulas",
    tableMaxRows: 6,
    tableMaxCols: 5,
  });
  console.log(file);
  console.log(inspection.ndjson);

  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: `${file} formula error scan`,
  });
  console.log(errors.ndjson);
}

const first = await SpreadsheetFile.importXlsx(
  await FileBlob.load(path.join(outputDir, files[0])),
);
const preview = await first.render({
  sheetName: "Translation Batch",
  range: "A1:Q12",
  format: "png",
  scale: 1,
});
await fs.writeFile(
  path.join(outputDir, "verification_preview.png"),
  Buffer.from(await preview.arrayBuffer()),
);
