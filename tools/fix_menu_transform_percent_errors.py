import json
import sqlite3
from pathlib import Path


JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
DB_ROOT = Path("work_db_vi_mistral")
REPORT = Path("mistral_translate_work/reports/fix_menu_transform_percent_errors.json")


EXACT_BY_PRIMARY_KEY = {
    "FunctionMenu_10001_FunctionName": "Resonators",
    "FunctionMenu_10002_FunctionName": "Túi đồ",
    "FunctionMenu_10004_FunctionName": "Nhiệm vụ",
    "FunctionMenu_10007_FunctionName": "Đội",
    "FunctionMenu_10009_FunctionName": "Triệu Tập",
    "FunctionMenu_10010_FunctionName": "Cửa hàng",
    "FunctionMenu_10011_FunctionName": "Bạn bè",
    "FunctionMenu_10013_FunctionName": "Thành tựu",
    "FunctionMenu_10015_FunctionName": "Bản đồ",
    "FunctionMenu_10022_FunctionName": "Hướng dẫn",
    "FunctionMenu_10023_FunctionName": "Sổ tay",
    "FunctionMenu_10026_FunctionName": "Công cụ",
    "FunctionMenu_10028_FunctionName": "Phản hồi",
    "FunctionMenu_10035_FunctionName": "Tổng hợp",
    "FunctionMenu_10040_FunctionName": "Podcast Tiên Phong",
    "FunctionMenu_10041_FunctionName": "Ngân Hàng Dữ Liệu",
    "FunctionMenu_10051_FunctionName": "Thư viện",
    "FunctionMenu_10053_FunctionName": "Sự kiện",
    "FunctionMenu_10059_FunctionName": "Chế độ Hợp tác",
    "FunctionMenu_10086_FunctionName": "Kho Hướng Dẫn",
    "FunctionMenu_10095_FunctionName": "Kinh nghiệm Tiên Phong",
    "FunctionMenu_10098_FunctionName": "Xe máy Thám Hiểm",
    "FunctionMenu_10130_FunctionName": "WavesLine",
    "FunctionMenu_20002_FunctionName": "Tổng quan",
    "FunctionMenu_20003_FunctionName": "Cài đặt",
    "FunctionMenu_20008_FunctionName": "Thanh Cảm Xúc",
    "FunctionMenu_20010_FunctionName": "Máy ảnh",
}

FUNCTION_MENU_BY_ID = {
    1: "Resonators",
    2: "Túi đồ",
    3: "Terminal Cộng Hưởng",
    4: "Nhiệm vụ",
    7: "Đội",
    9: "Điều Chỉnh",
    10: "Trao đổi chung",
    11: "Bạn bè",
    13: "Thành tựu",
    14: "Thư viện",
    15: "Bản đồ",
    17: "Bản Ghi Cộng Hưởng",
    18: "Công cụ",
    19: "Phản hồi",
    20: "Phe phái",
    21: "Căn Chỉnh Sao",
    22: "Ngân Hàng Dữ Liệu",
    23: "Thư viện",
}

TEXT_EXACT = {
    "Friends": "Bạn bè",
    "Gallery": "Thư viện",
}


def normalize_text(value: str) -> str:
    if value == "%%":
        return "%"
    replacements = [
        ("Resonatorssss", "Resonators"),
        ("Resonatorsss", "Resonators"),
        ("Resonatorss", "Resonators"),
        ("Echoeses", "Echoes"),
        ("Tranform", "Biến Đổi"),
        ("Transformed", "Đã Biến Đổi"),
        ("Transformation", "Biến Đổi"),
        ("Transform", "Biến Đổi"),
    ]
    for old, new in replacements:
        value = value.replace(old, new)
    return value


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
            after = EXACT_BY_PRIMARY_KEY.get(item.get("primary_key"), before)
            if item.get("source_en") in TEXT_EXACT and before == item.get("source_en"):
                after = TEXT_EXACT[item["source_en"]]
            after = normalize_text(after)
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


def patch_sqlite() -> list[dict]:
    changes = []
    for db_path in DB_ROOT.glob("*.db"):
        con = sqlite3.connect(db_path)
        try:
            for table, in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                cols = [row[1] for row in con.execute(f"PRAGMA table_info({table})")]
                if "Content" not in cols:
                    continue
                id_col = "Id" if "Id" in cols else cols[0]
                rows = con.execute(f"SELECT {id_col}, Content FROM {table}").fetchall()
                for row_id, before in rows:
                    if not isinstance(before, str):
                        continue
                    after = before
                    if db_path.name == "lang_function.db" and table == "FunctionMenu":
                        after = FUNCTION_MENU_BY_ID.get(row_id, after)
                    if db_path.name == "lang_multi_text.db" and table == "MultiText":
                        after = EXACT_BY_PRIMARY_KEY.get(row_id, after)
                    if db_path.name == "lang_text.db" and table == "Text" and before in TEXT_EXACT:
                        after = TEXT_EXACT[before]
                    after = normalize_text(after)
                    if after != before:
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


def main() -> None:
    changes = patch_json() + patch_sqlite()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"changes": changes}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"changes": len(changes), "report": str(REPORT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
