import csv
import json
import re
from pathlib import Path


JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
REPORT_DIR = Path("mistral_translate_work/reports/forbidden_english_audit")
ACTIONABLE_CSV = REPORT_DIR / "actionable_high_medium.csv"
OUTPUT_JSON = REPORT_DIR / "applied_fixes.json"
OUTPUT_CSV = REPORT_DIR / "applied_fixes.csv"

EXCLUDED_DOMAINS = {
    "skill_description",
    "weapon",
    "echo_set",
    "phantom_skill",
    "monster_description",
}

# Deterministic fixes only. Proper nouns and uncertain terms stay in the review report.
PHRASE_FIXES = {
    "Platform Fast Travel Unlocked": "Đã mở khóa Dịch chuyển nhanh tại nền tảng",
    "Fast Travel": "Dịch chuyển nhanh",
    "Hồi chiêu Skill": "Hồi chiêu Kỹ năng",
    "Cooldown Skill": "Hồi chiêu Kỹ năng",
    "Close Friend": "Bạn thân",
    "Locked Box": "Hộp bị khóa",
    "Quest Item": "Vật phẩm nhiệm vụ",
    "Hoochief's Map": "Bản đồ của Hoochief",
    "Treasure Map": "Bản đồ kho báu",
    "Map Kho Báu": "Bản đồ kho báu",
    "Challenge Completed": "Hoàn thành thử thách",
    "Challenge Complete": "Hoàn thành thử thách",
    "Echo Details": "Chi tiết Echo",
    "Resonator Details": "Chi tiết Resonator",
    "Hand Glider": "Dù lượn",
    "Illusive Store": "Cửa hàng Illusive",
    "Support Missile: Enhanced": "Tên lửa hỗ trợ: Cường hóa",
    "Support Missile": "Tên lửa hỗ trợ",
    "Bounce Jump": "Nhảy bật",
    "Make yourself known": "Khai danh tính",
    "Hide the blade": "Giấu danh tính",
    "Big known": "Người có tiếng",
    "Gather Spring": "Hiểu tiếng lóng",
    "Gold pole": "Cái chân",
    "The green": "Vũ khí",
    "The stick": "Súng",
    "Research Institute": "Viện Nghiên Cứu",
}

WORD_FIXES = {
    "Cancel": "Hủy",
    "Confirm": "Xác nhận",
    "Select": "Chọn",
    "Tap": "Chạm",
    "Claim": "Nhận",
    "Remove": "Gỡ",
    "Place": "Đặt",
    "Previous": "Trước",
    "Next": "Tiếp",
    "Back": "Quay lại",
    "Close": "Đóng",
    "Start": "Bắt đầu",
    "Continue": "Tiếp tục",
    "Skip": "Bỏ qua",
    "Retry": "Thử lại",
    "View": "Xem",
    "Unlock": "Mở khóa",
    "Unlocked": "Đã mở khóa",
    "Locked": "Đã khóa",
    "Unavailable": "Không khả dụng",
    "Requirement": "Yêu cầu",
    "Requirements": "Yêu cầu",
    "Description": "Mô tả",
    "Details": "Chi tiết",
    "Overview": "Tổng quan",
    "Settings": "Cài đặt",
    "Tutorials": "Hướng dẫn",
    "Guidebook": "Sổ tay hướng dẫn",
    "Gallery": "Bộ sưu tập",
    "Friends": "Bạn bè",
    "Store": "Cửa hàng",
    "Team": "Đội",
    "Missions": "Nhiệm vụ",
    "Achievements": "Thành tựu",
    "Database": "Cơ sở dữ liệu",
    "Map": "Bản đồ",
    "Backpack": "Túi đồ",
    "Utilities": "Tiện ích",
    "Feedback": "Phản hồi",
    "Controls": "Điều khiển",
    "Module": "Mô-đun",
    "Alert": "Cảnh báo",
    "Notice": "Thông báo",
    "Items": "Vật phẩm",
    "Item": "Vật phẩm",
    "Use": "Dùng",
    "Hold": "Giữ",
    "Release": "Thả",
    "Jump": "Nhảy",
    "Gather": "Thu thập",
    "Deploy": "Triển khai",
    "Research": "Nghiên cứu",
    "Instructions": "Hướng dẫn",
    "Amount": "Số lượng",
    "Support": "Hỗ trợ",
    "Transform": "Biến đổi",
    "Merchandiser": "Thương nhân",
    "Demodulator": "Bộ giải điều chế",
    "Glider": "Dù lượn",
    "Challenge": "Thử thách",
    "Complete": "Hoàn thành",
    "Guide": "Hướng dẫn",
    "Buff": "Hiệu ứng tăng cường",
    "New": "Mới",
}


def domain_from_rel(rel: str) -> str:
    return rel.split("/", 1)[0].split("\\", 1)[0]


def phrase_replace(text: str, old: str, new: str) -> str:
    return re.sub(rf"(?<![A-Za-z0-9]){re.escape(old)}(?![A-Za-z0-9])", new, text)


def word_replace(text: str, old: str, new: str) -> str:
    return re.sub(rf"\b{re.escape(old)}\b", new, text)


def apply_fixes(text: str) -> str:
    fixed = text
    for old, new in sorted(PHRASE_FIXES.items(), key=lambda item: len(item[0]), reverse=True):
        fixed = phrase_replace(fixed, old, new)
    for old, new in sorted(WORD_FIXES.items(), key=lambda item: len(item[0]), reverse=True):
        fixed = word_replace(fixed, old, new)
    fixed = fixed.replace("Nhiệm Vụ Mở khóa", "Nhiệm vụ mở khóa")
    fixed = fixed.replace("Nhiệm Vụ Unlock", "Nhiệm vụ mở khóa")
    fixed = fixed.replace("Dùng Nhảy", "Nhấn Nhảy")
    fixed = fixed.replace("Issue Mô tả", "Mô tả vấn đề")
    fixed = fixed.replace("Test Vật phẩm", "Hạng mục kiểm tra")
    fixed = fixed.replace("Data Mô-đun", "Mô-đun dữ liệu")
    fixed = fixed.replace("Main Motor Mô-đun", "Mô-đun động cơ chính")
    fixed = fixed.replace("Laser Beam Mô-đun", "Mô-đun tia laser")
    fixed = fixed.replace("Tấm Bản đồ kho báu", "Tấm bản đồ kho báu")
    fixed = fixed.replace("Dịch chuyển nhanh đến", "Dịch chuyển nhanh đến")
    return fixed


def main() -> None:
    if not ACTIONABLE_CSV.exists():
        raise SystemExit(f"Missing audit file: {ACTIONABLE_CSV}")

    rows = list(csv.DictReader(ACTIONABLE_CSV.open(encoding="utf-8-sig")))
    by_file: dict[str, set[int]] = {}
    for row in rows:
        rel = row["json_file"]
        if domain_from_rel(rel) in EXCLUDED_DOMAINS:
            continue
        if "forbidden_" not in row["issues"] and "english_without_vietnamese" not in row["issues"]:
            continue
        by_file.setdefault(rel, set()).add(int(row["json_index"]))

    applied = []
    for rel, indexes in sorted(by_file.items()):
        path = JSON_ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for index in sorted(indexes):
            row = data[index]
            before = str(row.get("new_translation_vi") or "")
            after = apply_fixes(before)
            if after == before:
                continue
            row["new_translation_vi"] = after
            changed = True
            applied.append({
                "json_file": rel,
                "json_index": index,
                "split_id": row.get("split_id", ""),
                "source_en": row.get("source_en", ""),
                "before": before,
                "after": after,
            })
        if changed:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(applied, ensure_ascii=False, indent=2), encoding="utf-8")
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["json_file", "json_index", "split_id", "source_en", "before", "after"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(applied)
    print(json.dumps({"files_seen": len(by_file), "rows_changed": len(applied)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
