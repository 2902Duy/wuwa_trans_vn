import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


WORKBOOK = Path(r"C:\Users\tduy2\Downloads\ui_system_next_error_groups_fixed.xlsx")
JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
REPORT_DIR = Path("mistral_translate_work/reports/ui_system_full_audit")
REPORT = REPORT_DIR / "import_ui_system_next_error_groups_fixed.json"

NS = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def col_to_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref).group(0)
    value = 0
    for ch in letters:
        value = value * 26 + ord(ch) - ord("A") + 1
    return value - 1


def cell_text(cell: ET.Element) -> str:
    if cell.get("t") == "inlineStr":
        parts = [node.text or "" for node in cell.findall(".//x:t", NS)]
        return "".join(parts)
    value = cell.find("x:v", NS)
    return value.text if value is not None and value.text is not None else ""


def parse_workbook(path: Path) -> dict[str, list[dict[str, str]]]:
    with zipfile.ZipFile(path) as zf:
        workbook_xml = ET.fromstring(zf.read("xl/workbook.xml"))
        rels_xml = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rels = {
            rel.get("Id"): rel.get("Target")
            for rel in rels_xml
            if rel.get("Id") and rel.get("Target")
        }
        sheets = {}
        for sheet in workbook_xml.findall(".//x:sheet", NS):
            name = sheet.get("name")
            rid = sheet.get(f"{{{NS['r']}}}id")
            target = rels.get(rid, "")
            if not target:
                continue
            target = target.lstrip("/")
            sheet_path = target if target.startswith("xl/") else "xl/" + target
            xml = ET.fromstring(zf.read(sheet_path))
            raw_rows = []
            for row in xml.findall(".//x:sheetData/x:row", NS):
                values = []
                for cell in row.findall("x:c", NS):
                    idx = col_to_index(cell.get("r", "A1"))
                    while len(values) <= idx:
                        values.append("")
                    values[idx] = cell_text(cell)
                raw_rows.append(values)
            if not raw_rows:
                sheets[name] = []
                continue
            headers = raw_rows[0]
            rows = []
            for values in raw_rows[1:]:
                if not any(v != "" for v in values):
                    continue
                row = {headers[i]: values[i] if i < len(values) else "" for i in range(len(headers))}
                rows.append(row)
            sheets[name] = rows
        return sheets


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    sheets = parse_workbook(WORKBOOK)
    importable_sheets = [
        "placeholder_mismatch",
        "tag_mismatch",
        "untranslated_source",
        "question_marks",
    ]
    changes = []
    skipped = []
    touched: dict[Path, list] = {}

    for sheet_name in importable_sheets:
        for row_num, row in enumerate(sheets.get(sheet_name, []), start=2):
            rel = row.get("json_file", "").strip()
            idx_raw = row.get("json_index", "").strip()
            new_vi = row.get("new_translation_vi", "")
            if not rel or not idx_raw:
                skipped.append({"sheet": sheet_name, "row": row_num, "reason": "missing_json_file_or_index"})
                continue
            try:
                idx = int(float(idx_raw))
            except ValueError:
                skipped.append({"sheet": sheet_name, "row": row_num, "reason": "bad_json_index", "json_index": idx_raw})
                continue
            path = JSON_ROOT / rel
            if not path.exists():
                skipped.append({"sheet": sheet_name, "row": row_num, "reason": "json_file_not_found", "json_file": rel})
                continue
            if path not in touched:
                touched[path] = load_json(path)
            data = touched[path]
            if idx < 0 or idx >= len(data) or not isinstance(data[idx], dict):
                skipped.append({"sheet": sheet_name, "row": row_num, "reason": "json_index_out_of_range", "json_file": rel, "json_index": idx})
                continue
            current = data[idx].get("new_translation_vi", "")
            primary_key = str(row.get("primary_key", ""))
            current_key = str(data[idx].get("primary_key", ""))
            if primary_key and current_key and primary_key != current_key:
                skipped.append({
                    "sheet": sheet_name,
                    "row": row_num,
                    "reason": "primary_key_mismatch",
                    "json_file": rel,
                    "json_index": idx,
                    "excel_primary_key": primary_key,
                    "json_primary_key": current_key,
                })
                continue
            if new_vi != current:
                data[idx]["new_translation_vi"] = new_vi
                changes.append({
                    "sheet": sheet_name,
                    "row": row_num,
                    "json_file": rel,
                    "json_index": idx,
                    "primary_key": current_key or primary_key,
                    "old": current,
                    "new": new_vi,
                })

    for path, data in touched.items():
        save_json(path, data)

    summary = {
        "workbook": str(WORKBOOK),
        "sheet_rows": {name: len(rows) for name, rows in sheets.items()},
        "changes_applied": len(changes),
        "files_touched": [str(path) for path in sorted(touched)],
        "skipped": skipped,
        "changes": changes,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("sheet_rows", "changes_applied", "files_touched")}, ensure_ascii=False, indent=2))
    if skipped:
        print(json.dumps({"skipped": skipped[:20], "skipped_count": len(skipped)}, ensure_ascii=False, indent=2))
    print(str(REPORT))


if __name__ == "__main__":
    main()
