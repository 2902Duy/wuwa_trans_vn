import json
import sqlite3
from pathlib import Path


JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
DB_ROOT = Path("work_db_vi_mistral")
REPORT = Path("mistral_translate_work/reports/fix_cancel_confirm.json")

MAP = {
    "Cancel": "Hủy",
    "Confirm": "Xác nhận",
}


def patch_json():
    changes = []
    for path in JSON_ROOT.rglob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        changed = False
        rel = path.relative_to(JSON_ROOT).as_posix()
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            before = item.get("new_translation_vi")
            if before not in MAP:
                continue
            after = MAP[before]
            item["new_translation_vi"] = after
            changed = True
            changes.append(
                {
                    "kind": "json",
                    "file": rel,
                    "index": index,
                    "split_id": item.get("split_id"),
                    "primary_key": item.get("primary_key"),
                    "before": before,
                    "after": after,
                }
            )
        if changed:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return changes


def patch_db():
    changes = []
    for db_path in DB_ROOT.glob("*.db"):
        con = sqlite3.connect(db_path)
        try:
            for table, in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                cols = [row[1] for row in con.execute(f"PRAGMA table_info({table})")]
                if "Content" not in cols:
                    continue
                id_col = "Id" if "Id" in cols else cols[0]
                rows = con.execute(
                    f"SELECT {id_col}, Content FROM {table} WHERE Content IN ('Cancel', 'Confirm')"
                ).fetchall()
                for row_id, before in rows:
                    after = MAP[before]
                    con.execute(
                        f"UPDATE {table} SET Content = ? WHERE {id_col} = ?",
                        (after, row_id),
                    )
                    changes.append(
                        {
                            "kind": "db",
                            "db": db_path.name,
                            "table": table,
                            "id": row_id,
                            "before": before,
                            "after": after,
                        }
                    )
            con.commit()
        finally:
            con.close()
    return changes


def main():
    changes = patch_json() + patch_db()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"changes": changes}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"changes": len(changes), "report": str(REPORT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
