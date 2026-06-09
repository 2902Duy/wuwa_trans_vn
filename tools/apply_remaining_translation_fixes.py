import csv
import json
from pathlib import Path


JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
REPORT_DIR = Path("mistral_translate_work/reports/forbidden_english_audit")
ACTIONABLE_CSV = REPORT_DIR / "actionable_high_medium.csv"
OUT = REPORT_DIR / "remaining_translation_fixes.json"


SOURCE_TRANSLATIONS = {
    "Adventures in the Water City-Aria Mummer": "Những cuộc phiêu lưu ở Thành phố Nước - Aria Mummer",
    "Trial of Wisdom": "Thử thách Trí tuệ",
    "After the performance": "Sau buổi biểu diễn",
    "Explore the Meishin Passageway": "Khám phá Lối đi Meishin",
    "Return to Shashou Cafe": "Quay lại Shashou Cafe",
    "Tacet Discord Nest": "Tổ Tacet Discord",
    "Tacet Discord Nest Cleared": "Đã dọn sạch Tổ Tacet Discord",
    "Difficult: Tacet Discord Nest": "Khó: Tổ Tacet Discord",
    "Confident Child": "Đứa trẻ tự tin",
    "Unknown Tacet Discord": "Tacet Discord bí ẩn",
    "Incomplete Tacet Discord": "Tacet Discord chưa hoàn chỉnh",
    "\"Young Girl\"": "\"Cô bé\"",
    "Recycling Staff Member": "Nhân viên tái chế",
    "Female Pioneer Association Member": "Thành viên nữ Hiệp hội Tiên phong",
    "Person Admiring the View": "Người ngắm cảnh",
    "Strange Tacet Discord": "Tacet Discord kỳ lạ",
    "Phantom of a Woman": "Bóng ma người phụ nữ",
    "Phantom of a Young Man": "Bóng ma chàng trai trẻ",
    "Tacet Discord in the Forbidden Archive": "Tacet Discord trong Kho lưu trữ Cấm",
    "Upset Soldier": "Người lính bực bội",
    "Secret Tacet Discord": "Tacet Discord bí mật",
    "Tacet Discord Info": "Thông tin Tacet Discord",
    "Travel in Jinzhou: Gulpuffs prerequisite": "Du lịch Jinzhou: điều kiện tiên quyết của Gulpuffs",
    "Sept": "Thg 9",
    "Tune Strain - Interfered": "Điều chỉnh Biến dạng - Bị nhiễu",
    "Rinascita-Thessaleo Fells-Twin Peaks": "Rinascita - Thessaleo Fells - Song Phong",
    "(Pick up the Soliskin）": "(Nhặt Soliskin)",
    "Resonator Menu": "Menu Resonator",
    "Namipon Stickers": "Nhãn dán Namipon",
    "Owlwatch Hacking": "Hack Owlwatch",
    "Microphone": "Micro",
    "Fast Swimming Stamina Consumption Speed": "Tốc độ tiêu hao thể lực khi bơi nhanh",
    "Fast Climbing Stamina Consumption Speed": "Tốc độ tiêu hao thể lực khi leo nhanh",
    "Fast Climbing Stamina Consumption": "Tiêu hao thể lực khi leo nhanh",
    "When Wonders Gather in the Box": "Khi kỳ quan tụ về trong hộp",
    "Close Your Eyes and Listen in": "Nhắm mắt và lắng nghe",
    "Stimulus Feedback": "Phản hồi kích thích",
    "Navigation Support": "Hỗ trợ dẫn đường",
    "Use Fast Decorate once in Party Decor": "Dùng Trang trí nhanh một lần trong Trang trí tiệc",
    "Namipon Stickers": "Nhãn dán Namipon",
    "Rare Sticker": "Nhãn dán hiếm",
    "Common Sticker": "Nhãn dán thường",
    "Trial Name": "Tên thử nghiệm",
    "Lock rotation": "Khóa xoay",
    "Total Exploration Progress": "Tổng tiến độ khám phá",
    "Mail Name": "Tên thư",
    "Equipment Name": "Tên trang bị",
    "Max Level Preview": "Xem trước cấp tối đa",
    "Sort by": "Sắp xếp theo",
    "* Data from recently active players": "* Dữ liệu từ người chơi hoạt động gần đây",
    "Crest Obtained": "Đã nhận Huy hiệu",
    "Survey Rewards": "Phần thưởng khảo sát",
    "Memetic Tuning": "Điều chỉnh Memetic",
    "Nightmare Memes": "Meme Ác mộng",
    "Area Quests": "Nhiệm vụ khu vực",
    "Companions Stats": "Chỉ số Đồng hành",
    "First Clear Complete": "Hoàn tất lần vượt đầu",
    "Dream Shards": "Mảnh Giấc mơ",
    "Total Tactic Points": "Tổng điểm chiến thuật",
    "Limited Time Early Access": "Truy cập sớm giới hạn thời gian",
    "Complete Travel Records for all areas to claim": "Hoàn thành Nhật ký du lịch của mọi khu vực để nhận thưởng",
    "Concerto Companions": "Đồng hành Concerto",
    "Basic Stats": "Chỉ số cơ bản",
    "Rewards Countdown": "Đếm ngược phần thưởng",
    "Result Preview": "Xem trước kết quả",
    "Available Tactics": "Chiến thuật khả dụng",
    "Quick Build": "Tạo nhanh",
    "Go Search": "Đi tìm kiếm",
    "Event Rewards: {0}/{1}": "Phần thưởng sự kiện: {0}/{1}",
    "Available Now": "Hiện có",
    "Clear to unlock the Persona Pinball": "Vượt qua để mở khóa Persona Pinball",
    "Survey Progress": "Tiến độ khảo sát",
    "The Primus": "Primus",
    "Inspect the Terminal": "Kiểm tra Terminal",
    "Immobilize the Vitreum Dancer": "Khống chế Vitreum Dancer",
    "Begin the Trial of Swiftness": "Bắt đầu Thử thách Tốc độ",
    "Enter the Void Storm Zone": "Vào Vùng Bão Hư Không",
    "Return to Startorch Academy": "Quay lại Học viện Startorch",
    "Inspect the Symphodai": "Kiểm tra Symphodai",
    "Return to the Ministry of Development": "Quay lại Bộ Phát triển",
    "Restart the radar": "Khởi động lại radar",
    "A Brief Respite": "Khoảng nghỉ ngắn",
    "Enter Whimpering Wastes": "Vào Whimpering Wastes",
    "Woman in Mask": "Người phụ nữ đeo mặt nạ",
    "Inspect the Tubpup": "Kiểm tra Tubpup",
    "Constructor Cores: {count_1}/540": "Lõi Constructor: {count_1}/540",
    "Chase the Kronablight": "Truy đuổi Kronablight",
    "Board the train Echo": "Lên Echo tàu",
    "Return to the Leonidas Hotel": "Quay lại Khách sạn Leonidas",
    "Deliver Sonance Caskets to Teensy Weensy": "Giao Sonance Caskets cho Teensy Weensy",
    "Deliver the Pavo Plums": "Giao Pavo Plums",
    "Spring Adventures": "Phiêu lưu mùa xuân",
    "Print out the Cruise Conduit": "In Cruise Conduit",
    "Return to the Montelli Quarter": "Quay lại Khu Montelli",
    "Mephis Tacet Field": "Tacet Field Mephis",
    "Deliver Flour x5, Milk x5": "Giao 5 Bột mì, 5 Sữa",
    "Inspect the Geospider": "Kiểm tra Geospider",
    "Glory to the Montellis!": "Vinh quang cho nhà Montelli!",
    "Yum! Fruit Crackle, yum!": "Ngon! Fruit Crackle, ngon!",
    "Albums <color=#ffd12f>{0}</color>/{1}": "Album <color=#ffd12f>{0}</color>/{1}",
    "Duelists: <color=#8ece7f>{0}</color>/<color=#ffffff>{1}</color>": "Đấu sĩ: <color=#8ece7f>{0}</color>/<color=#ffffff>{1}</color>",
    "Duelists:  <color=#497c49>{0}</color>/<color=#1c1c1c>{1}</color>": "Đấu sĩ: <color=#497c49>{0}</color>/<color=#1c1c1c>{1}</color>",
    "Master Jianxin.": "Sư phụ Jianxin.",
    "Duelists: <color=#8ece7f>{0}</color>/<color=#ffffff>{1}</color>": "Đấu sĩ: <color=#8ece7f>{0}</color>/<color=#ffffff>{1}</color>",
}

SPLIT_ID_TRANSLATIONS = {
    "STORY_DIALOGUE_0004318": "Di chuyển riêng biệt và tiến thêm số ô bằng số Cube khác trên cùng ô đó.",
    "STORY_DIALOGUE_0014453": "Khu dân cư Huanglong",
    "STORY_DIALOGUE_0102215": "Ngoại ô Jinzhou",
    "STORY_DIALOGUE_0102847": "Gameplay_Mt. Firmament_barrier connector",
    "NAME_TITLE_0007362": "\"Juniper\"",
    "NAME_TITLE_0007402": "Primus",
    "NAME_TITLE_0009632": "Chủ Arbor của Bogu",
    "NAME_TITLE_0026439": "Làng Juebi",
    "NAME_TITLE_0026987": "Sa mạc Juebi",
    "NAME_TITLE_0029933": "Ngoại ô Sa mạc Lanxiang",
    "NAME_TITLE_0030359": "Sa mạc Lanxiang",
    "NAME_TITLE_0031432": "Vinh Quang Mặt Trời - Đứa Con Mặt Trời 2",
    "NAME_TITLE_0031433": "Vinh Quang Mặt Trời - Đứa Con Mặt Trời 3",
    "NAME_TITLE_0031434": "Vinh Quang Mặt Trời - Đứa Con Mặt Trời 4",
    "NAME_TITLE_0031435": "Vinh Quang Mặt Trời - Đứa Con Mặt Trời 5",
    "NAME_TITLE_0031436": "Vinh Quang Mặt Trời - Đứa Con Mặt Trời 6",
    "NAME_TITLE_0031437": "Vinh Quang Mặt Trời - Đứa Con Mặt Trời 7",
    "NAME_TITLE_0031438": "Vinh Quang Mặt Trời - Đứa Con Mặt Trời 8",
    "NAME_TITLE_0031439": "Vinh Quang Mặt Trời - Đứa Con Mặt Trời 9",
    "NAME_TITLE_0042876": "\"Meo Are #2\"",
    "NAME_TITLE_0043876": "Đại tiệc Mộng ngày",
    "NAME_TITLE_0047085": "Sim Credits",
    "NAME_TITLE_0047226": "Blaze - Dung Nham",
    "NAME_TITLE_0047493": "Ngai Gai",
    "NAME_TITLE_0048662": "Chia Tay",
    "NAME_TITLE_0049061": "Resonator Demo",
    "NAME_TITLE_0056269": "Mua Kênh Connoisseur",
    "NAME_TITLE_0056523": "Kho lưu trữ: Tacet Discord",
    "NAME_TITLE_0056991": "Neo-Tide | Album Remix",
    "NAME_TITLE_0057275": "Trỗi dậy sau tám lần chôn cất",
    "NAME_TITLE_0057469": "Hecate - Truy cập sớm",
    "NAME_TITLE_0058250": "Album Lollo Joy",
    "UI_0001923": "Kênh Insider của Pioneer Podcast",
    "UI_0004409": "Dreamland Coupons hiện có",
    "UI_0004938": "Điểm Stability Accords",
    "UI_0004939": "Điểm Singularity Expansion",
    "UI_0004998": "Tên bản nhạc",
    "UI_0005227": "Album Lollo Joy",
    "UI_0005303": "Album Lollo Joy",
    "UI_0005304": "Album Lollo Joy",
    "UI_0005764": "Chỉ số ROM",
    "QUEST_0010521": "Orbit Valley Pass - Nam",
    "QUEST_0013986": "Làng Plushie",
    "QUEST_0014146": "Phiêu lưu mùa xuân",
    "QUEST_0016733": "Giao 5 Bột mì, 5 Sữa",
}

SOURCE_TRANSLATIONS.update({
    "Resonator Menu": "Trình đơn Resonator",
    "Owlwatch Hacking": "Xâm nhập Owlwatch",
    "Microphone": "Micrô",
    "Deliver Sonance Caskets to Teensy Weensy": "Giao Tráp Sonance cho Teensy Weensy",
    "Deliver the Pavo Plums": "Giao Mận Pavo",
    "Albums <color=#ffd12f>{0}</color>/{1}": "Tuyển tập <color=#ffd12f>{0}</color>/{1}",
    "Yum! Fruit Crackle, yum!": "Ngon! Bánh giòn trái cây, ngon!",
})

SPLIT_ID_TRANSLATIONS.update({
    "NAME_TITLE_0031590": "Trình đơn Resonator",
    "NAME_TITLE_0032971": "Xâm nhập Owlwatch",
    "NAME_TITLE_0033293": "Micrô",
    "NAME_TITLE_0035322": "Royan cận chiến",
    "NAME_TITLE_0037094": "Xe phong cầm Sonata",
    "NAME_TITLE_0049061": "Dùng thử Resonator",
    "NAME_TITLE_0056991": "Neo-Tide | Tuyển tập Remix",
    "NAME_TITLE_0058250": "Tuyển tập Lollo Joy",
    "QUEST_0013891": "Kiểm tra Frostbiter",
    "QUEST_0013893": "Kiểm tra Edelschnee",
    "QUEST_0013989": "Giao Tráp Sonance cho Teensy Weensy",
    "QUEST_0014144": "Giao Mận Pavo",
    "UI_0005227": "Tuyển tập Lollo Joy",
    "UI_0005303": "Tuyển tập Lollo Joy",
    "UI_0005304": "Tuyển tập Lollo Joy",
})


def main() -> None:
    rows = list(csv.DictReader(ACTIONABLE_CSV.open(encoding="utf-8-sig")))
    by_file: dict[str, list[dict]] = {}
    for row in rows:
        by_file.setdefault(row["json_file"], []).append(row)

    changes = []
    for rel, report_rows in sorted(by_file.items()):
        path = JSON_ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for report_row in report_rows:
            index = int(report_row["json_index"])
            item = data[index]
            split_id = str(item.get("split_id") or "")
            source = str(item.get("source_en") or "")
            after = SPLIT_ID_TRANSLATIONS.get(split_id) or SOURCE_TRANSLATIONS.get(source)
            if after is None:
                continue
            before = str(item.get("new_translation_vi") or "")
            if before == after:
                continue
            item["new_translation_vi"] = after
            changed = True
            changes.append({
                "json_file": rel,
                "json_index": index,
                "split_id": split_id,
                "source_en": source,
                "before": before,
                "after": after,
            })
        if changed:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    OUT.write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"rows_changed": len(changes), "report": str(OUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
