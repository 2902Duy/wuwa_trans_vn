import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
SOURCE_DB_ROOT = Path("db_en")
REPORT = Path("mistral_translate_work/reports/restore_split_source_en_from_db.json")


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), strict=False)


def row_key(item: dict) -> tuple[str, str, str, str, str] | None:
    db = item.get("database") or item.get("source_file", "").replace(".json", ".db")
    table = item.get("table")
    pk_col = item.get("primary_key_column") or "Id"
    pk = str(item.get("primary_key", ""))
    col = item.get("column") or "Content"
    if not all([db, table, pk_col, pk, col]):
        return None
    return db, table, pk_col, pk, col


def fetch_sources(keys_by_db: dict[str, set[tuple[str, str, str, str, str]]], stats: Counter):
    sources: dict[tuple[str, str, str, str, str], str] = {}
    missing: list[dict] = []

    for db_name, keys in sorted(keys_by_db.items()):
        db_path = SOURCE_DB_ROOT / db_name
        if not db_path.exists():
            for key in keys:
                missing.append({"reason": "missing_source_db", "key": list(key)})
            stats["missing_source_db_rows"] += len(keys)
            continue

        con = sqlite3.connect(db_path)
        try:
            schema_cache: dict[str, set[str]] = {}
            for key in sorted(keys):
                db, table, pk_col, pk, col = key
                if table not in schema_cache:
                    try:
                        schema_cache[table] = {
                            row[1] for row in con.execute(f"PRAGMA table_info({quote_ident(table)})")
                        }
                    except sqlite3.OperationalError:
                        schema_cache[table] = set()

                cols = schema_cache[table]
                if not cols:
                    missing.append({"reason": "missing_source_table", "key": list(key)})
                    stats["missing_source_table_rows"] += 1
                    continue
                if pk_col not in cols or col not in cols:
                    missing.append({"reason": "missing_source_column", "key": list(key)})
                    stats["missing_source_column_rows"] += 1
                    continue

                query = (
                    f"SELECT {quote_ident(col)} FROM {quote_ident(table)} "
                    f"WHERE {quote_ident(pk_col)} = ?"
                )
                current = con.execute(query, (pk,)).fetchone()
                if current is None:
                    missing.append({"reason": "missing_source_primary_key", "key": list(key)})
                    stats["missing_source_primary_key_rows"] += 1
                    continue
                sources[key] = "" if current[0] is None else str(current[0])
                stats["source_rows_loaded"] += 1
        finally:
            con.close()

    return sources, missing


def main() -> None:
    stats = Counter()
    file_rows: dict[Path, list] = {}
    keys_by_db: dict[str, set[tuple[str, str, str, str, str]]] = defaultdict(set)
    incomplete: list[dict] = []

    for path in sorted(JSON_ROOT.rglob("*.json")):
        data = load_json(path)
        if not isinstance(data, list):
            stats["skipped_non_list_files"] += 1
            continue
        file_rows[path] = data
        rel = path.relative_to(JSON_ROOT).as_posix()
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                stats["skipped_non_object_rows"] += 1
                continue
            key = row_key(item)
            if key is None:
                incomplete.append({"json_file": rel, "json_index": index})
                stats["skipped_incomplete_rows"] += 1
                continue
            keys_by_db[key[0]].add(key)
            stats["json_rows_seen"] += 1

    sources, missing = fetch_sources(keys_by_db, stats)

    changed_files: list[str] = []
    changed_rows: list[dict] = []
    for path, data in file_rows.items():
        rel = path.relative_to(JSON_ROOT).as_posix()
        file_changed = False
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            key = row_key(item)
            if key is None or key not in sources:
                continue
            before = item.get("source_en", "")
            after = sources[key]
            if before == after:
                stats["unchanged_source_en_rows"] += 1
                continue
            item["source_en"] = after
            file_changed = True
            stats["updated_source_en_rows"] += 1
            changed_rows.append(
                {
                    "json_file": rel,
                    "json_index": index,
                    "split_id": item.get("split_id", ""),
                    "key": list(key),
                    "before": before,
                    "after": after,
                }
            )
        if file_changed:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed_files.append(rel)
            stats["updated_json_files"] += 1

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "summary": dict(stats),
        "updated_files": changed_files,
        "updated_rows": changed_rows,
        "missing": missing,
        "incomplete": incomplete,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": dict(stats),
                "updated_files": len(changed_files),
                "updated_rows": len(changed_rows),
                "missing": len(missing),
                "incomplete": len(incomplete),
                "report": str(REPORT),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
