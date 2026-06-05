import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
DB_ROOT = Path("work_db_vi_mistral")
REPORT = Path("mistral_translate_work/reports/sync_split_json_to_db.json")


def load_rows() -> tuple[dict[tuple[str, str, str, str, str], dict], list[dict], Counter]:
    by_key: dict[tuple[str, str, str, str, str], dict] = {}
    conflicts: list[dict] = []
    stats = Counter()

    for path in sorted(JSON_ROOT.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        rel = path.relative_to(JSON_ROOT).as_posix()
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            db = item.get("database") or item.get("source_file", "").replace(".json", ".db")
            table = item.get("table")
            pk_col = item.get("primary_key_column") or "Id"
            pk = str(item.get("primary_key", ""))
            col = item.get("column") or "Content"
            text = item.get("new_translation_vi")
            if not all([db, table, pk_col, pk, col]) or not isinstance(text, str):
                stats["skipped_incomplete_json_row"] += 1
                continue
            key = (db, table, pk_col, pk, col)
            row = {
                "key": key,
                "text": text,
                "json_file": rel,
                "json_index": index,
                "split_id": item.get("split_id", ""),
            }
            old = by_key.get(key)
            if old and old["text"] != text:
                conflicts.append(
                    {
                        "database": db,
                        "table": table,
                        "primary_key_column": pk_col,
                        "primary_key": pk,
                        "column": col,
                        "old_text": old["text"],
                        "old_json_file": old["json_file"],
                        "old_split_id": old["split_id"],
                        "new_text": text,
                        "new_json_file": rel,
                        "new_split_id": item.get("split_id", ""),
                        "chosen": "newer_sorted_json_row",
                    }
                )
            by_key[key] = row
            stats["json_rows_loaded"] += 1
    return by_key, conflicts, stats


def sync_to_db(rows: dict[tuple[str, str, str, str, str], dict], stats: Counter) -> list[dict]:
    changes: list[dict] = []
    missing: list[dict] = []
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows.values():
        grouped[row["key"][0]].append(row)

    for db_name, db_rows in sorted(grouped.items()):
        db_path = DB_ROOT / db_name
        if not db_path.exists():
            for row in db_rows:
                missing.append({"reason": "missing_db", "database": db_name, "key": row["key"]})
            stats["missing_db_rows"] += len(db_rows)
            continue

        con = sqlite3.connect(db_path)
        try:
            schema_cache: dict[str, set[str]] = {}
            for row in db_rows:
                db, table, pk_col, pk, col = row["key"]
                if table not in schema_cache:
                    try:
                        schema_cache[table] = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
                    except sqlite3.OperationalError:
                        schema_cache[table] = set()
                cols = schema_cache[table]
                if not cols:
                    missing.append({"reason": "missing_table", "database": db, "table": table, "key": row["key"]})
                    stats["missing_table_rows"] += 1
                    continue
                if pk_col not in cols or col not in cols:
                    missing.append(
                        {
                            "reason": "missing_column",
                            "database": db,
                            "table": table,
                            "primary_key_column": pk_col,
                            "column": col,
                            "key": row["key"],
                        }
                    )
                    stats["missing_column_rows"] += 1
                    continue

                current = con.execute(f"SELECT {col} FROM {table} WHERE {pk_col} = ?", (pk,)).fetchone()
                if current is None:
                    missing.append({"reason": "missing_primary_key", "database": db, "table": table, "key": row["key"]})
                    stats["missing_primary_key_rows"] += 1
                    continue
                before = current[0]
                after = row["text"]
                if before == after:
                    stats["unchanged_rows"] += 1
                    continue
                con.execute(f"UPDATE {table} SET {col} = ? WHERE {pk_col} = ?", (after, pk))
                changes.append(
                    {
                        "database": db,
                        "table": table,
                        "primary_key_column": pk_col,
                        "primary_key": pk,
                        "column": col,
                        "before": before,
                        "after": after,
                        "json_file": row["json_file"],
                        "split_id": row["split_id"],
                    }
                )
                stats["updated_rows"] += 1
            con.commit()
        finally:
            con.close()

    return changes, missing


def main() -> None:
    rows, conflicts, stats = load_rows()
    changes, missing = sync_to_db(rows, stats)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "summary": dict(stats),
        "unique_db_targets": len(rows),
        "conflicts": conflicts,
        "missing": missing,
        "changes": changes,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": dict(stats),
                "unique_db_targets": len(rows),
                "conflicts": len(conflicts),
                "missing": len(missing),
                "changes": len(changes),
                "report": str(REPORT),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
