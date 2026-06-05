import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
DB_ROOT = Path("db_en")
OUT_ROOT = JSON_ROOT / "coverage_only"
REPORT = Path("mistral_translate_work/reports/export_raw_missing_db_rows_to_coverage_json.json")
PART_SIZE = 2000


def load_existing_keys() -> tuple[set[tuple[str, str, str, str, str]], dict[str, set[tuple[str, str, str]]]]:
    keys: set[tuple[str, str, str, str, str]] = set()
    target_columns: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for path in sorted(JSON_ROOT.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            db = item.get("database") or item.get("source_file", "").replace(".json", ".db")
            table = item.get("table")
            pk_col = item.get("primary_key_column") or "Id"
            pk = str(item.get("primary_key", ""))
            col = item.get("column") or "Content"
            if not all([db, table, pk_col, pk, col]):
                continue
            keys.add((db, table, pk_col, pk, col))
            target_columns[db].add((table, pk_col, col))
    return keys, target_columns


def row_payload(db: str, table: str, pk_col: str, pk: str, col: str, source) -> dict:
    is_null = source is None
    source_text = "" if source is None else str(source)
    return {
        "database": db,
        "source_file": db.replace(".db", ".json"),
        "table": table,
        "primary_key_column": pk_col,
        "primary_key": pk,
        "column": col,
        "source_en": source_text,
        "new_translation_vi": None,
        "prompt_domain": "coverage_only",
        "split_id": f"{db.replace('.db', '')}__coverage_only",
        "coverage_only": True,
        "coverage_note": "Raw DB row missing from split JSON. Source is null/empty, kept only for full DB coverage and skipped by translation sync.",
        "source_was_null": is_null,
    }


def write_parts(rows_by_db: dict[str, list[dict]]) -> list[dict]:
    written = []
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for db, rows in sorted(rows_by_db.items()):
        db_dir = OUT_ROOT / db.replace(".db", "")
        db_dir.mkdir(parents=True, exist_ok=True)
        for old in db_dir.glob("*.json"):
            old.unlink()
        for part_no, start in enumerate(range(0, len(rows), PART_SIZE), start=1):
            part = rows[start : start + PART_SIZE]
            path = db_dir / f"{db.replace('.db', '')}__coverage_only__part_{part_no:04d}.json"
            path.write_text(json.dumps(part, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            written.append({"file": str(path), "rows": len(part)})
    return written


def main() -> None:
    existing_keys, target_columns = load_existing_keys()
    missing_by_db: dict[str, list[dict]] = defaultdict(list)
    stats = Counter()

    for db, specs in sorted(target_columns.items()):
        db_path = DB_ROOT / db
        if not db_path.exists():
            stats["missing_db"] += 1
            continue
        con = sqlite3.connect(db_path)
        try:
            schema_cache: dict[str, set[str]] = {}
            for table, pk_col, col in sorted(specs):
                if table not in schema_cache:
                    schema_cache[table] = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
                cols = schema_cache[table]
                if pk_col not in cols or col not in cols:
                    stats["missing_column_or_pk"] += 1
                    continue
                for pk, source in con.execute(f"SELECT {pk_col}, {col} FROM {table}"):
                    key = (db, table, pk_col, str(pk), col)
                    if key in existing_keys:
                        continue
                    missing_by_db[db].append(row_payload(db, table, pk_col, str(pk), col, source))
                    stats["raw_missing_rows_exported"] += 1
                    if source is None:
                        stats["null_source_rows"] += 1
                    elif str(source).strip() == "":
                        stats["empty_source_rows"] += 1
                    else:
                        stats["nonempty_source_rows"] += 1
        finally:
            con.close()

    written = write_parts(missing_by_db)
    report = {
        "summary": dict(stats),
        "out_root": str(OUT_ROOT),
        "rows_by_db": {db: len(rows) for db, rows in sorted(missing_by_db.items())},
        "files_written": written,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"summary": dict(stats), "out_root": str(OUT_ROOT), "files_written": len(written), "report": str(REPORT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
