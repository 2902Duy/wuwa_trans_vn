import json
import re
import sqlite3
from pathlib import Path


DB_ROOT = Path("work_db_vi_mistral")
JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
REPORT = Path("mistral_translate_work/reports/fix_third_pass_surface_errors.json")


REPLACEMENTS = [
    # Repair translated input-token values while keeping the game control tag shape intact.
    (r"\{Cus:Ipt,Touch=tap PC=Press Gamepad=Press\}", "{Cus:Ipt,Touch=tap PC=press Gamepad=press}"),
    (r"\{Cus:Ipt,Touch=Nhấn PC=Press Gamepad=Press\}", "{Cus:Ipt,Touch=tap PC=press Gamepad=press}"),
    (r"\{Cus:Ipt,Touch=Nhấn PC=Press Gamepad=Press\}", "{Cus:Ipt,Touch=tap PC=press Gamepad=press}"),
    (r"\{Cus:Ipt,Touch=Nhấn PC=press Gamepad=press\}", "{Cus:Ipt,Touch=tap PC=press Gamepad=press}"),
    (r"\{Cus:Ipt,Touch=tap PC=nhấn Gamepad=nhấn\}", "{Cus:Ipt,Touch=tap PC=press Gamepad=press}"),
    (r"\{Cus:Ipt,Touch=tap PC=Nhấn Gamepad=Nhấn\}", "{Cus:Ipt,Touch=tap PC=press Gamepad=press}"),
    (r"\{Cus:Ipt,Touch=nhấn PC=nhấn Gamepad=nhấn\}", "{Cus:Ipt,Touch=tap PC=press Gamepad=press}"),
    # Visible action verbs. Keep combat terms such as Normal Attack in English.
    (r"\bHold <color=Highlight>Hold Normal Attack</color>", "Giữ <color=Highlight>Normal Attack</color>"),
    (r"\bHold <color=Highlight>Giữ Basic Attack</color>", "Giữ <color=Highlight>Basic Attack</color>"),
    (r"\bHold <color=Highlight>Normal Attack</color>", "Giữ <color=Highlight>Normal Attack</color>"),
    (r"\bHold <color=Highlight>Basic Attack</color>", "Giữ <color=Highlight>Basic Attack</color>"),
    (r"\bHold <color=Highlight>Resonance Skill</color>", "Giữ <color=Highlight>Resonance Skill</color>"),
    (r"\bHold <color=([^>]+)>", r"Giữ <color=\1>"),
    (r"-Hold <color=([^>]+)>", r"-Giữ <color=\1>"),
    (r"<color=([^>]+)>Hold </color>", r"<color=\1>Giữ </color>"),
    (r"\bHold <color=#ffd12f>Hold</color>", "Giữ <color=#ffd12f>Giữ</color>"),
    (r"\bHold <color=#ffd12f>\{0\}</color>", "Giữ <color=#ffd12f>{0}</color>"),
    (r"\bHold Normal Attack\b", "Giữ Normal Attack"),
    (r"\bHold Resonance Skill\b", "Giữ Resonance Skill"),
    (r"\bHold \[Normal Attack\]", "Giữ [Normal Attack]"),
    (r"\bHold \{", "Giữ {"),
    (r"\bHold \(", "Giữ ("),
    (r"\bHold để", "Giữ để"),
    (r"\bHold ([A-ZÀ-ỸĐ])", r"Giữ \1"),
    (r"\bHold ([a-zà-ỹđ])", r"Giữ \1"),
    (r"\bhold Normal Attack\b", "giữ Normal Attack"),
    (r"\buse Normal Attack\b", "sử dụng Normal Attack"),
    (r"\buse Thường Attack\b", "sử dụng Normal Attack"),
    (r"\benhanced Mid-air Attack\b", "Mid-air Attack cường hóa"),
    (r"\bAttack mục tiêu\b", "Tấn công mục tiêu"),
    (r"\bAttack các mục tiêu\b", "Tấn công các mục tiêu"),
    (r"\bBasic Atttack\b", "Basic Attack"),
    (r"\bSummon You'tan\b", "Triệu hồi You'tan"),
    # UI/menu/title leftovers.
    (r"\bSwitch sang Member Đội\b", "Chuyển sang thành viên Đội"),
    (r"\bSwitch sang\b", "Chuyển sang"),
    (r"\bSwitch đi\b", "Chuyển đi"),
    (r"\bFavorite Food\b", "Món ăn yêu thích"),
    (r"\bDetails Item\b", "Chi tiết vật phẩm"),
    (r"\bMedic of Public Security Bureau\b", "Bác sĩ của Cục An Ninh Công Cộng"),
    (r"\bPublic Security Bureau\b", "Cục An Ninh Công Cộng"),
    (r"\bFriends:\b", "Bạn bè:"),
    (r"\bMalee:", "Tên:"),
    (r"\(Male,", "(Nam,"),
    (r"\(Female,", "(Nữ,"),
    # Lore/document wording that was left as English headings or literal machine output.
    (r"\bSupply Application Form Template\b", "Mẫu đơn xin cấp vật tư"),
    (r"\bSupplies xin cấp & Amount:", "Vật tư xin cấp & Số lượng:"),
    (r"\bSupplies được cấp\b", "Vật tư được cấp"),
    (r"\bAmount:", "Số lượng:"),
    (r"\bNotice về\b", "Thông báo về"),
    (r"\bNotice New Yi\b", "Thông báo mới"),
    (r"\bNotice Đã Cũ\b", "Thông báo cũ"),
    (r"\bNotice:\b", "Thông báo:"),
    (r"\bNotice\b", "Thông báo"),
    (r"\bTime:", "Thời gian:"),
    (r"\bNote:", "Ghi chú:"),
    (r"\bNote và", "Ghi chú và"),
    (r"\bPrevious khi\b", "Trước khi"),
    (r"\bNone quy luật\b", "Không có quy luật"),
    (r"\bNone ghi chép\b", "Không có ghi chép"),
    (r"\bNone trí tuệ\b", "Không có trí tuệ"),
    (r"\bNone tranh cãi\b", "Không có tranh cãi"),
    (r"\bVillager vui mừng\b", "Dân làng vui mừng"),
    (r"\bNight đầy sao\b", "Đêm đầy sao"),
    (r"\bNight đêm\b", "Đêm"),
    (r"\bNight Đầy Sao\b", "Đêm Đầy Sao"),
    (r"\bNight khuya\b", "Đêm khuya"),
    (r"\bBóng Night\b", "Bóng Đêm"),
    (r"\bHolda khúc sông\b", "Ở khúc sông"),
    (r"\bBộ Play Triển\b", "Bộ Phát Triển"),
    (r"\bPlay hiện\b", "Phát hiện"),
    (r"\bSave ý\b", "Lưu ý"),
    (r"\bSave Đày\b", "Lưu Đày"),
    (r"\bConfere Truyện tranh\b", "Hội Truyện tranh"),
    (r"\bInstructions khán giả\b", "Hướng dẫn dành cho khán giả"),
    (r"\bHome hát\b", "Nhà hát"),
    (r"\bRating tính khả thi\b", "Đánh giá tính khả thi"),
    (r"\bResearch tác động\b", "Nghiên cứu tác động"),
    (r"\bUnlimited;", "Không giới hạn;"),
    (r"\bRight có bằng lái\b", "Có bằng lái"),
    (r"\bDo thêm:", "Làm thêm:"),
    (r"\bGet bánh\b", "Lấy bánh"),
    (r"\bAdjust thời gian\b", "Điều chỉnh thời gian"),
    (r"\bGather ba\b", "Thu thập ba"),
    (r"\bPhoto đã lưu\b", "Ảnh đã lưu"),
    (r"\bRừng Mờ Photo\b", "Ảnh Rừng Mờ"),
    (r"\bPhoto hưởng\b", "Ảnh hưởng"),
    (r"\bNhiếp Photo\b", "Nhiếp ảnh"),
    (r"\bNhiệm Vụ Photo Lollo Joy Album\b", "Nhiệm vụ Album ảnh Lollo Joy"),
    (r"\bPhoto ([A-ZÀ-ỸĐ][^\n]*)", r"Chụp ảnh \1"),
    (r"\bPhoto ([A-Za-zÀ-ỹ' -]+?) thực hiện\b", r"Chụp ảnh \1 thực hiện"),
    (r"\bPhoto ([A-Za-zÀ-ỹ' -]+?) đang\b", r"Chụp ảnh \1 đang"),
    (r"\bPhoto ([A-Za-zÀ-ỹ' -]+?) uống\b", r"Chụp ảnh \1 uống"),
    (r"\bPhoto ([A-Za-zÀ-ỹ' -]+?) triệu hồi\b", r"Chụp ảnh \1 triệu hồi"),
    (r"\bJump lên\b", "Nhảy lên"),
    (r"\b3 times\b", "3 lần"),
    (r"\bRelease ra\b", "Thả ra"),
    (r"\bRelease để\b", "Thả để"),
    (r"\bRelease trong\b", "Thả trong"),
    (r"\bRelease vật phẩm\b", "Thả vật phẩm"),
    (r"\bRelease nút\b", "Thả nút"),
    (r"\bRelease Normal Attack\b", "Thả Normal Attack"),
    (r"\bRelease Heavy Attack\b", "Thả Heavy Attack"),
    (r"\bRelease \{", "Thả {"),
    (r"\bRelease một\b", "Thả một"),
    (r"\bRelease <color=", "Thả <color="),
    (r"\band thả\b", "và thả"),
    (r"\brelease Resonance Liberation\b", "thả Resonance Liberation"),
    (r"\bhold Resonance Liberation\b", "giữ Resonance Liberation"),
    (r"\bDeal <color=", "Gây <color="),
    (r"\bCan be cast mid-air\b", "Có thể thi triển trên không"),
    (r"để进入 trạng thái", "để vào trạng thái"),
    (r"\b进入 trạng thái", "vào trạng thái"),
    (r"\bmid-air\b", "trên không"),
    (r"\bResonator switching is disabled\b", "chuyển đổi Resonator bị vô hiệu hóa"),
    (r"\bAttack Holda Không\b", "Mid-air Attack"),
    (r"\bAttack Lao Xuống\b", "Đòn Lao Xuống"),
    (r"\bResearch của\b", "Nghiên cứu của"),
    (r"\bResearch Institute\b", "Viện Nghiên Cứu"),
    (r"\bNghiên cứu Institute\b", "Viện Nghiên Cứu"),
    (r"\bUtility\b", "Công cụ"),
    # Additional refined leftovers found after the main audit.
    (r"\bDrag Novelty to Deployment Zone\b", "Kéo Novelty vào Khu Vực Triển Khai"),
    (r"\bDeployment Zone\b", "Khu Vực Triển Khai"),
    (r"\bDeployment Stage\b", "Giai đoạn Triển khai"),
    (r"\bDeploying\b", "Đang triển khai"),
    (r"\bDeployed\b", "Đã triển khai"),
    (r"\bDeployment\b", "Triển khai"),
    (r"\bDeploy\b", "Triển khai"),
    (r"\bDeployment Stage\b", "Giai đoạn Triển khai"),
    (r"\bPlease end Giai đoạn Triển khai\b", "Vui lòng kết thúc Giai đoạn Triển khai"),
    (r"\bJump đến\b", "Nhảy đến"),
    (r"\bJump vào\b", "Nhảy vào"),
    (r"\bJump xuống\b", "Nhảy xuống"),
    (r"\bJump để\b", "Nhảy để"),
    (r"\bJump thêm\b", "Nhảy thêm"),
    (r"\bGather các\b", "Thu thập các"),
    (r"\bGather vật\b", "Thu thập vật"),
    (r"\bGather thông\b", "Thu thập thông"),
    (r"\bGather những\b", "Thu thập những"),
    (r"\bGather toàn\b", "Thu thập toàn"),
    (r"\bGather Da\b", "Thu thập Da"),
    (r"\bGather Soliskin\b", "Thu thập Soliskin"),
    (r"\bGather Ký\b", "Thu thập Ký"),
    (r"\bGather và\b", "Thu thập và"),
    (r"\bGather âm\b", "Thu thập âm"),
    (r"\bGather Sắt\b", "Thu thập Sắt"),
    (r"\bGather Windchimers\b", "Thu thập Windchimers"),
    (r"\bGather ([0-9]+)", r"Thu thập \1"),
    (r"\bResearch viên\b", "Nghiên cứu viên"),
    (r"\bResearch cho thấy\b", "Nghiên cứu cho thấy"),
    (r"\bResearch xác nhận\b", "Nghiên cứu xác nhận"),
    (r"\bResearch Khoa học\b", "Nghiên cứu Khoa học"),
    (r"\bResearch TD\b", "Nghiên cứu TD"),
    (r"\bResearch Sample\b", "Mẫu Nghiên Cứu"),
    (r"\bResearch Memo\b", "Ghi Chú Nghiên Cứu"),
    (r"\bResearch Note\b", "Ghi Chú Nghiên Cứu"),
    (r"\bResearch Records\b", "Hồ Sơ Nghiên Cứu"),
    (r"\bResearch Log\b", "Nhật Ký Nghiên Cứu"),
    (r"\bResearch Log Fragment\b", "Mảnh Nhật Ký Nghiên Cứu"),
    (r"\bResearch Outpost\b", "Trạm Nghiên Cứu"),
    (r"\bResearch Zero Point\b", "Nghiên Cứu Zero Point"),
    (r"\bTrạm Research\b", "Trạm Nghiên Cứu"),
    (r"\bSáng kiến Research\b", "Sáng kiến Nghiên cứu"),
    (r"\bInstructions vận hành\b", "Hướng dẫn vận hành"),
    (r"\bInstructions for playing\b", "Hướng dẫn chơi"),
    (r"\bInstructions sử dụng\b", "Hướng dẫn sử dụng"),
    (r"\bInstructions bổ sung\b", "Hướng dẫn bổ sung"),
    (r"\bInstructions\b", "Hướng dẫn"),
    (r"\bPerhaps\b", "Có lẽ"),
    (r"\bcharge up\b", "tích lực"),
    (r"\bvarious enhanced moves\b", "các chiêu cường hóa khác nhau"),
    (r"\bflip backward\b", "lộn ngược ra sau"),
    (r"\bAttack Lao\b", "Đòn Lao"),
    (r"\bExchange những\b", "Trao đổi những"),
    (r"\bTrao Exchange Học Thuật\b", "Trao Đổi Học Thuật"),
    (r"\bTrao Exchange\b", "Trao đổi"),
    (r"\bGiảng Sugar\b", "Giảng Đường"),
    (r"\bPlays Giả\b", "Diễn Giả"),
    (r"\bResearch\b", "Nghiên cứu"),
    (r"\bJump Pad\b", "Bệ Nhảy"),
    (r"\bJump Plant\b", "Cây Nhảy"),
    (r"\bJump Bật\b", "Bật Nhảy"),
    (r"\bClimbing Jump Stamina Consumption \(Once\)\b", "Tiêu hao thể lực khi nhảy leo trèo (một lần)"),
    (r"\bJump\b", "Nhảy"),
    (r"\bMonthly Development Supplies Pack\b", "Gói Vật Tư Phát Triển Hàng Tháng"),
    (r"\bWeekly Development Supplies Pack\b", "Gói Vật Tư Phát Triển Hàng Tuần"),
    (r"\bBeginner Development Supplies Pack\b", "Gói Vật Tư Phát Triển Tân Thủ"),
    (r"\bSupplies\b", "Vật tư"),
    (r"\bTemplates Supply Request Form\b", "Mẫu đơn yêu cầu vật tư"),
    (r"\bTemplate Supply Request Form\b", "Mẫu đơn yêu cầu vật tư"),
    (r"\bReleasem Họa\b", "Thảm Họa"),
]


INPUT_TAG_RE = re.compile(r"\{Cus:Ipt,Touch=([^ }]+) PC=([^ }]+) Gamepad=([^}]+)\}")


def fix_input_tag(match: re.Match) -> str:
    touch, pc, gamepad = match.groups()
    has_bad = any(
        value in {"Nhấn", "nhấn", "Chạm", "chạm", "Nhấp", "nhấp", "Press"}
        for value in (touch, pc, gamepad)
    )
    if not has_bad:
        return match.group(0)

    touch_map = {"Nhấn": "tap", "nhấn": "tap", "Chạm": "tap", "chạm": "tap", "Nhấp": "tap", "nhấp": "tap"}
    pc_map = {"Nhấn": "press", "nhấn": "press", "Chạm": "click", "chạm": "click", "Nhấp": "click", "nhấp": "click", "Press": "press"}
    gamepad_map = {"Nhấn": "press", "nhấn": "press", "Chạm": "press", "chạm": "press", "Nhấp": "press", "nhấp": "press", "Press": "press"}
    return (
        "{Cus:Ipt,"
        f"Touch={touch_map.get(touch, touch)} "
        f"PC={pc_map.get(pc, pc)} "
        f"Gamepad={gamepad_map.get(gamepad, gamepad)}"
        "}"
    )


def fix_text(text: str) -> str:
    fixed = INPUT_TAG_RE.sub(fix_input_tag, text)
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
            if after == before:
                continue
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
            for (table,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
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
