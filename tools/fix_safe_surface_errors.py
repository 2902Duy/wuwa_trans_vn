import json
import re
import sqlite3
from pathlib import Path


DB_ROOT = Path("work_db_vi_mistral")
JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
REPORT = Path("mistral_translate_work/reports/fix_safe_surface_errors.json")


EXACT_MAP = {
    "Missions": "Nhiệm vụ",
    "Achievements": "Thành tựu",
    "Database": "Ngân Hàng Dữ Liệu",
    "Forces": "Phe phái",
    "Settings": "Cài đặt",
    "Overview": "Tổng quan",
    "Friends": "Bạn bè",
    "Gallery": "Thư viện",
    "Map": "Bản đồ",
    "Backpack": "Túi đồ",
    "Utilities": "Công cụ",
    "Feedback": "Phản hồi",
    "Tutorials": "Hướng dẫn",
    "Guidebook": "Sổ tay",
    "Events": "Sự kiện",
    "Store": "Cửa hàng",
    "Trophies": "Thành tựu",
    "Team": "Đội",
    "Convene": "Triệu Tập",
    "Cancel": "Hủy",
    "Confirm": "Xác nhận",
    "Select": "Chọn",
    "Tap": "Nhấn",
    "Claim": "Nhận",
    "Remove": "Gỡ bỏ",
    "Place": "Đặt",
    "Previous": "Trước",
    "Ongoing": "Đang diễn ra",
    "Requirement": "Yêu cầu",
    "Equipped": "Đã trang bị",
    "Unlocked": "Đã mở khóa",
    "Revive": "Hồi sinh",
    "Controls": "Điều khiển",
    "Skills": "Kỹ năng",
    "Wave": "Đợt",
    "Leave": "Rời khỏi",
    "Rating": "Đánh giá",
    "Tactics": "Chiến thuật",
    "Details": "Chi tiết",
    "Locked": "Đã khóa",
    "Unavailable": "Không khả dụng",
    "Defeated": "Đã thất bại",
    "Track": "Theo dõi",
    "Back": "Quay lại",
    "Close": "Đóng",
    "Start": "Bắt đầu",
    "Continue": "Tiếp tục",
    "Skip": "Bỏ qua",
    "Retry": "Thử lại",
    "Next": "Tiếp",
    "View": "Xem",
    "Obtained": "Đã nhận",
    "Unlock": "Mở khóa",
}


PHRASE_MAP = [
    (r"\bYou Tan\b", "__KEEP_YOU_TAN__"),
    (r"\bYou'tan\b", "__KEEP_YOUTAN__"),
    (r"\bResonatorssss\b", "Resonators"),
    (r"\bResonatorsss\b", "Resonators"),
    (r"\bResonatorss\b", "Resonators"),
    (r"\bEchoeses\b", "Echoes"),
    (r"\bEchoess\b", "Echoes"),
    (r"\bBiến Đổi thành\b", "Biến thành"),
    (r"\bTranform\b", "Biến Đổi"),
    (r"\bTransfrom\b", "Biến Đổi"),
    (r"\bYou\b", "Bạn"),
    (r"\bBut\b", "Nhưng"),
    (r"\bShe\b", "Cô ấy"),
    (r"\bHe\b", "Anh ấy"),
    (r"\bThey\b", "Họ"),
    (r"\bTap\b", "Nhấn"),
    (r"\bSelect\b", "Chọn"),
    (r"\bConfirm\b", "Xác nhận"),
    (r"\bCancel\b", "Hủy"),
    (r"\bContinue\b", "Tiếp tục"),
    (r"\bClaim\b", "Nhận"),
    (r"\bReset button\b", "nút Đặt lại"),
    (r"\bReset Cooldown\b", "Đặt lại hồi chiêu"),
    (r"\bReset\b", "Đặt lại"),
    (r"\bSupport Module\b", "Mô-đun Hỗ Trợ"),
    (r"\bSupport Modules\b", "Mô-đun Hỗ Trợ"),
    (r"\bSupport Echo\b", "Echo Hỗ Trợ"),
    (r"\bEcho Support\b", "Echo Hỗ Trợ"),
    (r"\bSupport Cube\b", "Cube Hỗ Trợ"),
    (r"\bSupport Resonators\b", "Resonator Hỗ Trợ"),
    (r"\bSupport\b", "Hỗ Trợ"),
    (r"\bStore\b", "Cửa hàng"),
    (r"\bConvene\b", "Triệu Tập"),
    (r"\bPurchase\b", "Mua"),
    (r"\bAll\b", "Tất cả"),
    (r"\bNo\b", "Không"),
    (r"\bNormal\b", "Thường"),
    (r"\bHard\b", "Khó"),
    (r"\bReal\b", "Thật sự"),
    (r"\bAfter\b", "Sau khi"),
    (r"\bToday\b", "Hôm nay"),
    (r"\bDay\b", "Ngày"),
    (r"\bWait\b", "Khoan"),
    (r"\bThen\b", "Vậy thì"),
    (r"\bReporter\b", "Phóng viên"),
    (r"\bItems\b", "Vật phẩm"),
    (r"\bDescription\b", "Mô tả"),
    (r"\bVoice\b", "Giọng nói"),
    (r"\bAlert\b", "Cảnh báo"),
    (r"\bModule\b", "Mô-đun"),
    (r"\bRequirement\b", "Yêu cầu"),
    (r"__KEEP_YOU_TAN__", "You Tan"),
    (r"__KEEP_YOUTAN__", "You'tan"),
]


def fix_text(text: str) -> str:
    if text in EXACT_MAP:
        return EXACT_MAP[text]
    fixed = text
    for pattern, repl in PHRASE_MAP:
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
