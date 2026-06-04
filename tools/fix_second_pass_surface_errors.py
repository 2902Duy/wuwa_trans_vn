import json
import re
import sqlite3
from pathlib import Path


DB_ROOT = Path("work_db_vi_mistral")
JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
REPORT = Path("mistral_translate_work/reports/fix_second_pass_surface_errors.json")


EXACT_STRIP_MAP = {
    "Ongoing": "Đang diễn ra",
    "Ongoing ": "Đang diễn ra",
}

REPLACEMENTS = [
    (r"\bTeam trưởng\b", "Trưởng nhóm"),
    (r"\bTeam Exploration\b", "Đội Thám Hiểm"),
    (r"\bTeam Morn Guards\b", "Đội Morn Guards"),
    (r"\bĐồng Team\b", "Co-op"),
    (r"\bTeam\b", "Đội"),
    (r"\bGallery Character\b", "Nhân Vật Trưng Bày"),
    (r"\bAshened Gallery\b", "Thư Viện Tro Tàn"),
    (r"\bCollection Gallery\b", "Thư Viện Sưu Tập"),
    (r"\bOpen Air Gallery\b", "Phòng Trưng Bày Ngoài Trời"),
    (r"\bGallery\b", "Thư viện"),
    (r"\bGuidebook\b", "Sổ tay"),
    (r"\bFeedback\b", "Phản hồi"),
    (r"\bBackpack\b", "Túi đồ"),
    (r"\bFriends\b", "Bạn bè"),
    (r"\bUtilities\b", "Công cụ"),
    (r"\bTutorials\b", "Hướng dẫn"),
    (r"\bUse\b", "Dùng"),
    (r"\bStart\b", "Bắt đầu"),
    (r"\bRecent\b", "Gần đây"),
    (r"\bPhase\b", "Giai đoạn"),
    (r"\bCulture\b", "Văn hóa"),
    (r"\bSystem\b", "Hệ thống"),
    (r"\bRecommended\b", "Được đề xuất"),
    (r"\bResearch Area\b", "Khu vực Nghiên cứu"),
    (r"\bComments\b", "Bình luận"),
    (r"\bOutfit\b", "Trang phục"),
    (r"\bEveryone\b", "Mọi người"),
    # Repair over-literal replacements from earlier safe passes.
    (r"\bThường Attack\b", "Normal Attack"),
    (r"\bThường Attacks\b", "Normal Attacks"),
    (r"\bKhông longer\b", "không còn"),
    (r"\bKhông ở\b", "Không ở"),
    (r"\bKhông suy nghĩ\b", "Không suy nghĩ"),
    (r"\bKhông ưa\b", "Không ưa"),
    (r"\bKhông quan tâm\b", "Không quan tâm"),
    (r"\bKhông làm theo\b", "Không làm theo"),
    (r"\bBạn'tan\b", "You'tan"),
    (r"\bBạn Tan\b", "You Tan"),
]


def fix_text(text: str) -> str:
    stripped = text.strip()
    if stripped in EXACT_STRIP_MAP and ("\n" not in text):
        return EXACT_STRIP_MAP[stripped]
    fixed = text
    for pattern, repl in REPLACEMENTS:
        fixed = re.sub(pattern, repl, fixed)
    return fixed


def patch_json() -> list[dict]:
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
            if not isinstance(before, str):
                continue
            after = fix_text(before)
            if after != before:
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


def patch_db() -> list[dict]:
    changes = []
    for db_path in DB_ROOT.glob("*.db"):
        con = sqlite3.connect(db_path)
        try:
            for table, in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                cols = [row[1] for row in con.execute(f"PRAGMA table_info({table})")]
                if "Content" not in cols:
                    continue
                id_col = "Id" if "Id" in cols else cols[0]
                for row_id, before in con.execute(f"SELECT {id_col}, Content FROM {table}"):
                    if not isinstance(before, str):
                        continue
                    after = fix_text(before)
                    if after == before:
                        continue
                    con.execute(f"UPDATE {table} SET Content = ? WHERE {id_col} = ?", (after, row_id))
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


def main() -> None:
    changes = patch_json() + patch_db()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"changes": changes}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"changes": len(changes), "report": str(REPORT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
