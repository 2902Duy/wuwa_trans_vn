import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


WORKBOOK = Path(r"C:\Users\tduy2\Downloads\json_vs_original_db_coverage_processed.xlsx")
OUT = Path("mistral_translate_work/reports/json_vs_original_db_coverage_processed_from_xlsx.json")

NS = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def col_to_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref or "A1").group(0)
    value = 0
    for ch in letters:
        value = value * 26 + ord(ch) - ord("A") + 1
    return value - 1


def cell_text(cell: ET.Element) -> str:
    if cell.get("t") == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:t", NS))
    value = cell.find("x:v", NS)
    return value.text if value is not None and value.text is not None else ""


def parse_workbook(path: Path) -> dict[str, list[dict[str, str]]]:
    sheets: dict[str, list[dict[str, str]]] = {}
    with zipfile.ZipFile(path) as zf:
        workbook_xml = ET.fromstring(zf.read("xl/workbook.xml"))
        rels_xml = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rels = {rel.get("Id"): rel.get("Target") for rel in rels_xml}
        for sheet in workbook_xml.findall(".//x:sheet", NS):
            name = sheet.get("name")
            rid = sheet.get(f"{{{NS['r']}}}id")
            target = (rels.get(rid) or "").lstrip("/")
            if not target:
                sheets[name] = []
                continue
            sheet_path = target if target.startswith("xl/") else "xl/" + target
            xml = ET.fromstring(zf.read(sheet_path))
            rows = []
            for row in xml.findall(".//x:sheetData/x:row", NS):
                values = []
                for cell in row.findall("x:c", NS):
                    idx = col_to_index(cell.get("r", "A1"))
                    while len(values) <= idx:
                        values.append("")
                    values[idx] = cell_text(cell)
                if any(values):
                    rows.append(values)
            if not rows:
                sheets[name] = []
                continue
            headers = rows[0]
            sheet_rows = []
            for values in rows[1:]:
                record = {headers[i]: values[i] if i < len(values) else "" for i in range(len(headers))}
                sheet_rows.append(record)
            sheets[name] = sheet_rows
    return sheets


def main() -> None:
    sheets = parse_workbook(WORKBOOK)
    payload = {
        "source_workbook": str(WORKBOOK),
        "sheet_rows": {name: len(rows) for name, rows in sheets.items()},
        "sheets": sheets,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "sheet_rows": payload["sheet_rows"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
