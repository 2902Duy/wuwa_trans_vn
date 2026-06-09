import os
import json
import re
import sys
from pathlib import Path
import pandas as pd

# Paths
violations_report_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\explorer_m1\violations_report.json"
ui_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"
glossary_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\shared_glossary.md"
out_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack"

def load_proper_nouns():
    with open(glossary_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    terms = []
    in_section = False
    for line in lines:
        if "## THUẬT NGỮ BẮT BUỘC GIỮ NGUYÊN TIẾNG ANH" in line:
            in_section = True
            continue
        if "## Ví dụ về các dịch sai cần tránh" in line:
            in_section = False
            break
        if in_section:
            if "->" in line:
                continue
            found = re.findall(r"`([^`]+)`", line)
            for term in found:
                if "," in term:
                    subterms = [t.strip() for t in term.split(",")]
                    terms.extend(subterms)
                else:
                    terms.append(term.strip())

    proper_nouns = []
    for t in terms:
        if t and t not in proper_nouns:
            if "/" in t or "[" in t or "{" in t or "<" in t:
                continue
            proper_nouns.append(t)

    proper_nouns.sort(key=len, reverse=True)
    return proper_nouns

def run_corrections(proper_nouns):
    # Load violations report
    with open(violations_report_path, "r", encoding="utf-8") as f:
        violations = json.load(f)

    # Ensure targeted split IDs are also included for correction if they are not in the violations report
    targeted_manual_violations = [
        {"split_id": "UI_0011110", "file": r"lang_multi_text\lang_multi_text__ui__part_0021.json", "type": "Manual Fix", "source": "Place the Electro Predator here. The Echoes on the right-hand side appear in the Backline.", "translation": ""},
        {"split_id": "UI_0011111", "file": r"lang_multi_text\lang_multi_text__ui__part_0021.json", "type": "Manual Fix", "source": "Place the Electro Predator here. The Echoes on the right-hand side appear in the Backline.", "translation": ""},
        {"split_id": "UI_0011112", "file": r"lang_multi_text\lang_multi_text__ui__part_0021.json", "type": "Manual Fix", "source": "Place the Electro Predator here. The Echoes on the right-hand side appear in the Backline.", "translation": ""},
        {"split_id": "UI_0005605", "file": r"lang_multi_text\lang_multi_text__ui__part_0010.json", "type": "Manual Fix", "source": "Special Supplies", "translation": ""},
        {"split_id": "UI_0005613", "file": r"lang_multi_text\lang_multi_text__ui__part_0010.json", "type": "Manual Fix", "source": "Exam Details", "translation": ""},
        {"split_id": "UI_0007105", "file": r"lang_multi_text\lang_multi_text__ui__part_0013.json", "type": "Manual Fix", "source": "Coordinated Attack", "translation": ""},
        {"split_id": "UI_0007584", "file": r"lang_multi_text\lang_multi_text__ui__part_0013.json", "type": "Manual Fix", "source": "...Queen of the Night...", "translation": ""},
        {"split_id": "UI_0000672", "file": r"lang_map_mark\lang_map_mark__ui__part_0001.json", "type": "Manual Fix", "source": "Ma He's Grocers", "translation": ""},
        {"split_id": "UI_0001154", "file": r"lang_multi_text\lang_multi_text__ui__part_0001.json", "type": "Manual Fix", "source": "Collect 1,200 Lollo Vouchers to unlock the Phantom reward", "translation": ""},
        {"split_id": "UI_0002809", "file": r"lang_multi_text\lang_multi_text__ui__part_0004.json", "type": "Manual Fix", "source": "Lunite Subscription", "translation": ""},
        {"split_id": "UI_0002814", "file": r"lang_multi_text\lang_multi_text__ui__part_0004.json", "type": "Manual Fix", "source": "Lunite Subscription", "translation": ""},
        {"split_id": "UI_0002815", "file": r"lang_multi_text\lang_multi_text__ui__part_0004.json", "type": "Manual Fix", "source": "Tap to claim today's Lunite Subscription reward", "translation": ""},
        {"split_id": "UI_0003317", "file": r"lang_multi_text\lang_multi_text__ui__part_0005.json", "type": "Manual Fix", "source": "Supply Chest", "translation": ""},
        {"split_id": "UI_0007388", "file": r"lang_multi_text\lang_multi_text__ui__part_0013.json", "type": "Manual Fix", "source": "Tide of Perils I", "translation": ""},
        {"split_id": "UI_0007389", "file": r"lang_multi_text\lang_multi_text__ui__part_0013.json", "type": "Manual Fix", "source": "Tide of Perils II", "translation": ""},
        {"split_id": "UI_0007390", "file": r"lang_multi_text\lang_multi_text__ui__part_0013.json", "type": "Manual Fix", "source": "Tide of Perils III", "translation": ""},
        {"split_id": "UI_0007404", "file": r"lang_multi_text\lang_multi_text__ui__part_0013.json", "type": "Manual Fix", "source": "Tide of Perils", "translation": ""},
        {"split_id": "UI_0007649", "file": r"lang_multi_text\lang_multi_text__ui__part_0014.json", "type": "Manual Fix", "source": "Plane of Dark Tide", "translation": ""},
        {"split_id": "UI_0007650", "file": r"lang_multi_text\lang_multi_text__ui__part_0014.json", "type": "Manual Fix", "source": "Another world concealed within the Dark Tide. From its depths resound the whispers of the ancient \"Divinity,\" the origin of all malice and fear.", "translation": ""},
        {"split_id": "UI_0007651", "file": r"lang_multi_text\lang_multi_text__ui__part_0014.json", "type": "Manual Fix", "source": "A mysterious entrance opened amidst the Dark Tide, where the surging currents converge.", "translation": ""},
        {"split_id": "UI_0007932", "file": r"lang_multi_text\lang_multi_text__ui__part_0014.json", "type": "Manual Fix", "source": "The High Tide's drawn in so many TDs, and even after it receded, plenty of those bastards still refuse to leave.", "translation": ""},
        {"split_id": "UI_0007954", "file": r"lang_multi_text\lang_multi_text__ui__part_0014.json", "type": "Manual Fix", "source": "I intend to step outside for a bit. See the world. Come back when the next High Tide arrives, and have a good brawl with those TDs myself.", "translation": ""},
        {"split_id": "UI_0011721", "file": r"lang_multi_text\lang_multi_text__ui__part_0022.json", "type": "Manual Fix", "source": "Activating a Namipon Lightbox reveals enemies and Supply Chests in its vicinity.", "translation": ""},
        {"split_id": "UI_0011722", "file": r"lang_multi_text\lang_multi_text__ui__part_0022.json", "type": "Manual Fix", "source": "Activating a Namipon Lightbox reveals enemies and Supply Chests in its vicinity.", "translation": ""},
        {"split_id": "UI_0011723", "file": r"lang_multi_text\lang_multi_text__ui__part_0022.json", "type": "Manual Fix", "source": "Activating a Namipon Lightbox reveals enemies and Supply Chests in its vicinity.", "translation": ""},
        {"split_id": "UI_0013159", "file": r"lang_payshop\lang_payshop__ui__part_0001.json", "type": "Manual Fix", "source": "Tacetreite Voucher", "translation": ""}
    ]
    
    existing_ids = {v["split_id"] for v in violations}
    for tmv in targeted_manual_violations:
        if tmv["split_id"] not in existing_ids:
            violations.append(tmv)

    print(f"Loaded {len(violations)} violations (including targeted manual fixes) for processing.")
    
    file_cache = {}
    
    for v in violations:
        rel_path = v["file"]
        split_id = v["split_id"]
        v_type = v["type"]
        source = v["source"]
        translation = v["translation"]
        
        full_path = os.path.join(ui_dir, rel_path)
        if rel_path not in file_cache:
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    file_cache[rel_path] = json.load(f)
            else:
                print(f"Warning: File {full_path} not found.")
                continue
                
        data = file_cache[rel_path]
        record = None
        for r in data:
            if r.get("split_id") == split_id:
                record = r
                break
                
        if not record:
            print(f"Warning: Record {split_id} not found in {rel_path}.")
            continue
            
        current_translation = record.get("new_translation_vi", "")
        if not current_translation:
            current_translation = translation
            
        fixed_translation = current_translation
        
        # --- FIX LOGIC ---
        if split_id in ["UI_0007504", "UI_0007550"]:
            fixed_translation = fixed_translation.replace("Sự im lặng", "Silence").replace("im lặng", "Silence")
        elif split_id == "UI_0001154":
            fixed_translation = "Thu thập 1.200 Lollo Vouchers để mở khóa phần thưởng Phantom"
        elif split_id in ["UI_0002809", "UI_0002814"]:
            fixed_translation = "Lunite Subscription"
        elif split_id == "UI_0002815":
            fixed_translation = "Chạm để nhận thưởng Lunite Subscription hôm nay"
        elif split_id == "UI_0003317":
            fixed_translation = "Supply Chest"
        elif split_id == "UI_0007388":
            fixed_translation = "Tide of Perils I"
        elif split_id == "UI_0007389":
            fixed_translation = "Tide of Perils II"
        elif split_id == "UI_0007390":
            fixed_translation = "Tide of Perils III"
        elif split_id == "UI_0007404":
            fixed_translation = "Tide of Perils"
        elif split_id == "UI_0007649":
            fixed_translation = "Plane of Dark Tide"
        elif split_id == "UI_0007650":
            fixed_translation = fixed_translation.replace("Thủy Triều Hắc Ám", "Dark Tide").replace("Thủy triều Hắc Ám", "Dark Tide")
        elif split_id == "UI_0007651":
            fixed_translation = fixed_translation.replace("Hắc Triều", "Dark Tide")
        elif split_id == "UI_0007932":
            fixed_translation = fixed_translation.replace("Thủy Triều High", "High Tide")
        elif split_id == "UI_0007954":
            fixed_translation = fixed_translation.replace("Triều High", "High Tide").replace("Thủy Triều High", "High Tide")
        elif split_id in ["UI_0011721", "UI_0011722", "UI_0011723"]:
            fixed_translation = fixed_translation.replace("Rương Vật Phẩm", "Supply Chests").replace("Rương Cung Cấp", "Supply Chests")
        elif split_id == "UI_0013159":
            fixed_translation = "Tacetreite Voucher"
        elif split_id == "UI_0007585":
            fixed_translation = fixed_translation.replace("Chim Than Vãn Aix", "Mourning Aix").replace("Than Vãn Aix", "Mourning Aix")
        elif split_id == "UI_0009084":
            fixed_translation = fixed_translation.replace("cần Quyết", "cần Jué").replace("Quyết", "Jué")
        elif split_id in ["UI_0009350", "UI_0009351"]:
            fixed_translation = "Khi <color=Highlight>Overflow</color> đầy, giữ **Normal Attack** để thi triển <color=Highlight>Basic Attack - Spark Collision</color> và vào trạng thái <color=Highlight>Kaleidoscopic Parade</color>."
        elif split_id == "UI_0009696":
            fixed_translation = fixed_translation.replace("Dodge phản công", "Dodge Counter")
        elif split_id in ["UI_0010329", "UI_0010330"]:
            fixed_translation = fixed_translation.replace("Giải phóng Cộng hưởng", "Resonance Liberation").replace("Giải Phóng Cộng Hưởng", "Resonance Liberation")
        elif split_id in ["UI_0010948", "UI_0010949", "UI_0010950"]:
            fixed_translation = "Đổi Resonator chính và đặt Chixia làm Protagonist."
        elif split_id in ["UI_0011649", "UI_0011650", "UI_0011651"]:
            fixed_translation = "Ở Chế độ Khó, bạn có thể dùng vật phẩm Slow Motion bất cứ lúc nào để làm chậm thời gian"
        elif split_id in ["UI_0011110", "UI_0011111", "UI_0011112"]:
            fixed_translation = fixed_translation.replace("Place Electro Predator", "Đặt Electro Predator")
        elif split_id == "UI_0005605":
            fixed_translation = "Vật Tư Đặc Biệt"
        elif split_id == "UI_0005613":
            fixed_translation = "Chi Tiết Kỳ Thi"
        elif split_id == "UI_0007105":
            fixed_translation = fixed_translation.replace("Attack Phối Hợp", "Tấn Công Phối Hợp")
        elif split_id == "UI_0007584":
            fixed_translation = fixed_translation.replace("Nữ hoàng Night tối", "Nữ hoàng Bóng Đêm")
        elif split_id == "UI_0000672":
            fixed_translation = "Cửa Hàng Ma He"
        else:
            if v_type == "Keep English Key Rule Violation":
                fixed_translation = source
                
            elif v_type == "Placeholder Mismatch":
                # Revert placeholder modifications
                src_phs = re.findall(r"\{[^\}]+\}", source)
                trans_phs = re.findall(r"\{[^\}]+\}", fixed_translation)
                if len(src_phs) == len(trans_phs):
                    for s_ph, t_ph in zip(src_phs, trans_phs):
                        fixed_translation = fixed_translation.replace(t_ph, s_ph)
                else:
                    # Custom regex replacements for gender placeholders
                    if "Male=him;Female=her" in source and "Male=" in fixed_translation:
                        fixed_translation = re.sub(r"\{Male=[^;]+;Female=[^\}]+\}", "{Male=him;Female=her}", fixed_translation)
                    elif "Male=gentleman;Female=lady" in source and "Male=" in fixed_translation:
                        fixed_translation = re.sub(r"\{Male=[^;]+;Female=[^\}]+\}", "{Male=gentleman;Female=lady}", fixed_translation)
                    elif "Male=lad;Female=lass" in source and "Male=" in fixed_translation:
                        fixed_translation = re.sub(r"\{Male=[^;]+;Female=[^\}]+\}", "{Male=lad;Female=lass}", fixed_translation)

            elif v_type == "Newline Mismatch":
                if split_id in ["UI_0007296", "UI_0007298"]:
                    fixed_translation = fixed_translation.replace("sự hướng dẫn. Nếu", "sự hướng dẫn. \nNếu")
                elif split_id in ["UI_0007571", "UI_0007572", "UI_0007573", "UI_0007574", "UI_0007575", "UI_0007576"]:
                    suffix = "\n\nA: Mục tiêu chịu thêm 50% sát thương.\nS: Mục tiêu chịu thêm 100% sát thương.\nSS: Mục tiêu chịu thêm 200% sát thương."
                    if not fixed_translation.endswith(suffix):
                        fixed_translation = fixed_translation.rstrip() + suffix
                elif split_id == "UI_0009261":
                    fixed_translation = fixed_translation.replace("x450 để chọn", "x450\nđể chọn")
                    
            elif v_type == "Untranslated Weapon Word":
                if "Weapon Level" in source:
                    fixed_translation = fixed_translation.replace("Weapon Level", "Cấp Vũ Khí")
                    fixed_translation = fixed_translation.replace("weapon level", "Cấp Vũ Khí")
                if "Weapon" in source:
                    fixed_translation = fixed_translation.replace("Weapon", "Vũ khí")
                    
            elif v_type == "Untranslated Action Verb":
                # Translate action verbs: Return -> Trở về, Exchange -> Trao đổi/Đổi, Increase -> Tăng, Decrease -> Giảm, Claim -> Nhận
                if "Interference Exchange" in fixed_translation:
                    fixed_translation = fixed_translation.replace("Interference Exchange", "Trao Đổi Interference")
                if "Service Credit Exchange" in fixed_translation:
                    fixed_translation = fixed_translation.replace("Service Credit Exchange", "Trao Đổi Credit Dịch Vụ")
                if "GPA Level Increase" in fixed_translation:
                    fixed_translation = fixed_translation.replace("GPA Level Increase", "Tăng Cấp Độ GPA")
                if "Increase GPA Level" in fixed_translation:
                    fixed_translation = fixed_translation.replace("Increase GPA Level", "Tăng Cấp Độ GPA")
                if "Exchange Service Credit" in fixed_translation:
                    fixed_translation = fixed_translation.replace("Exchange Service Credit", "Trao Đổi Credit Dịch Vụ")
                
                # Simple direct translations
                if fixed_translation == "Return":
                    fixed_translation = "Trở về"
                elif fixed_translation == "Exchange":
                    fixed_translation = "Trao đổi"
                else:
                    fixed_translation = re.sub(r"\bReturn\b", "Trở về", fixed_translation)
                    fixed_translation = re.sub(r"\bExchange\b", "Trao đổi", fixed_translation)
                    fixed_translation = re.sub(r"\bexchange\b", "trao đổi", fixed_translation)
                    fixed_translation = re.sub(r"\bIncrease\b", "Tăng", fixed_translation)
                    fixed_translation = re.sub(r"\bincrease\b", "tăng", fixed_translation)
                    fixed_translation = re.sub(r"\bDecrease\b", "Giảm", fixed_translation)
                    fixed_translation = re.sub(r"\bdecrease\b", "giảm", fixed_translation)
                    fixed_translation = re.sub(r"\bClaim\b", "Nhận", fixed_translation)
                    fixed_translation = re.sub(r"\bclaim\b", "nhận", fixed_translation)

            elif v_type in ["Glossary Translation Violation", "Blacklisted Translation", "Casing Violation"]:
                proper_nouns_replacements = [
                    # Regions
                    ("Rừng Mờ", "Dim Forest"), ("Rừng Tối", "Dim Forest"),
                    ("Khu Rừng Mù Sương", "Dim Forest"), ("Rừng Mù Sương", "Dim Forest"),
                    ("Bãi Lầy Whining Aix", "Whining Aix's Mire"), ("Bãi Lầy Aix Rên Rỉ", "Whining Aix's Mire"),
                    ("Bãi Than Vãn Aix", "Whining Aix's Mire"), ("Whining Aix's Mire", "Whining Aix's Mire"),
                    ("Hẻm Núi Linh Hồn", "Gorges of Spirits"), ("Hẻm núi Spirit", "Gorges of Spirits"),
                    ("Đồng bằng Trung tâm", "Central Plains"), ("Cao nguyên Desorock", "Desorock Highland"),
                    ("Cao Nguyên Desorock", "Desorock Highland"),
                    ("Núi Vòm Trời", "Mt. Firmament"), ("Trầm Minh Khánh", "Mt. Firmament"),
                    ("Núi Firmament", "Mt. Firmament"), ("Núi Hiên Viên", "Mt. Firmament"),
                    ("Hồng Trấn", "Hongzhen"), ("Thiên Phàm Cốc", "Whisperwind Haven"),
                    ("Ngõ Tối", "Black Alley"), ("Hẻm Đen", "Black Alley"),
                    
                    # Characters
                    ("Xích Hà", "Chixia"), ("Tương Ly Yao", "Xiangli Yao"),
                    
                    # Bosses / Monsters / Echo
                    ("Kẻ Canh Gác Quyết", "Sentinel Jué"), ("Bức tượng Người Bảo Hộ", "Sentinel"),
                    ("Người Bảo Hộ", "Sentinel"), ("Kẻ Bảo Hộ", "Sentinel"), ("Kẻ Canh Gác", "Sentinel"),
                    ("Người Canh Gác", "Sentinel"),
                    ("Quả Cầu Sonoro", "Sonoro Sphere"), ("Quả cầu Sonoro", "Sonoro Sphere"),
                    ("Nghệ sĩ Sáo", "Flautist"), ("Nghệ Sĩ Sáo", "Flautist"),
                    ("Vịt Bất Diệt", "Impermanence Heron"), ("Vịt bất diệt", "Impermanence Heron"),
                    ("Sẹo", "Scar"), ("Vết Sẹo", "Scar"),
                    
                    # General Game Terms / Stats
                    ("Nhà Lữ Hành", "Rover"), ("Vãng Minh Giả", "Rover"), ("Viễn Khách", "Rover"),
                    ("Người Cộng Hưởng", "Resonator"), ("Cộng Hưởng Giả", "Resonator"),
                    ("Cấp Độ Resonator", "Resonator Level"),
                    ("Kỹ Năng Cộng Hưởng", "Resonance Skill"), ("Chiêu Thức Cộng Hưởng", "Resonance Skill"),
                    ("Giải Phóng Cộng Hưởng", "Resonance Liberation"), ("Nộ", "Resonance Liberation"),
                    ("Mạch Forte", "Forte Circuit"), ("Chuỗi Forte", "Forte Circuit"),
                    ("Tấn Công Thường", "Basic Attack"), ("Tấn Công Cơ Bản", "Basic Attack"),
                    ("Trọng Kích", "Heavy Attack"), ("Tấn Công Nặng", "Heavy Attack"),
                    ("Hồi Chiêu", "Cooldown"), ("Thời gian hồi", "Cooldown"),
                    ("TẤN CÔNG", "ATK"),
                    ("Linh Thú", "Echo"), ("Tiếng Vang", "Echo"),
                    ("Kim Châu", "Jinzhou"),
                    
                    # Debuffs & effects
                    ("Nhiễu Loạn Quang Phổ", "Spectro Frazzle"), ("Xói Mòn Gió", "Aero Erosion"),
                    ("Trầy Băng Giá", "Glacio Chafe"), ("Nổ Nhiệt Hạch", "Fusion Burst"),
                    ("Tai Họa Hỗn Loạn", "Havoc Bane"), ("Điện Tích", "Electro Flare"),
                    ("Bùng Điện", "Electro Flare"),
                    ("Im lặng", "Silence"),
                ]
                
                proper_nouns_replacements.sort(key=lambda x: len(x[0]), reverse=True)
                for vi_noun, en_noun in proper_nouns_replacements:
                    if en_noun.lower() in source.lower():
                        if vi_noun in fixed_translation:
                            fixed_translation = fixed_translation.replace(vi_noun, en_noun)
                
                # Handle "Tacet Discord" specifically
                if "tacet discord" in source.lower():
                    if "Discord Tacet" in fixed_translation:
                        fixed_translation = fixed_translation.replace("Discord Tacet", "Tacet Discord")
                    elif "Discord" in fixed_translation:
                        fixed_translation = re.sub(r"\bDiscord\b", "Tacet Discord", fixed_translation)
                    elif "discord" in fixed_translation:
                        fixed_translation = re.sub(r"\bdiscord\b", "Tacet Discord", fixed_translation)
                
                # Handle "Normal Attack" / "Normal Attacks"
                if "normal attack" in source.lower() or "normal attacks" in source.lower():
                    if "Basic Attack" in fixed_translation:
                        fixed_translation = fixed_translation.replace("Basic Attack", "Normal Attack" if "normal attack" in source.lower() and not "normal attacks" in source.lower() else "Normal Attacks")
                    elif "Tấn Công Thường" in fixed_translation:
                        fixed_translation = fixed_translation.replace("Tấn Công Thường", "Normal Attack" if "normal attack" in source.lower() and not "normal attacks" in source.lower() else "Normal Attacks")
                        
                # Handle "Echo Skill"
                if "echo skill" in source.lower():
                    if "Resonance Skill" in fixed_translation:
                        fixed_translation = fixed_translation.replace("Resonance Skill", "Echo Skill")
                        
                # Handle "Special Chain Attack"
                if "special chain attack" in source.lower():
                    if "Đòn Liên Kết Special" in fixed_translation:
                        fixed_translation = fixed_translation.replace("Đòn Liên Kết Special", "Special Chain Attack")

                # Handle "Resonator Skill"
                if "resonator" in source.lower() and "resonator skill" in source.lower():
                    if "Resonance Skill" in fixed_translation:
                        fixed_translation = fixed_translation.replace("Resonance Skill", "Resonator Skill")

                # Enforce Case-Sensitivity for all glossary proper nouns
                for noun in proper_nouns:
                    if len(noun) <= 4:
                        noun_pattern = re.compile(rf"\b{re.escape(noun)}\b")
                    else:
                        noun_pattern = re.compile(re.escape(noun))
                    
                    if noun_pattern.search(source):
                        if noun.lower() in fixed_translation.lower() and noun not in fixed_translation:
                            fixed_translation = re.sub(re.escape(noun), noun, fixed_translation, flags=re.IGNORECASE)

        # Update record in the cache
        if fixed_translation != current_translation:
            print(f"[{split_id}] '{current_translation}' -> '{fixed_translation}'")
            record["new_translation_vi"] = fixed_translation
            record["status"] = "translated"

    # Write back all modified files
    print("\nSaving updated files...")
    for rel_path, data in file_cache.items():
        full_path = os.path.join(ui_dir, rel_path)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    print("Corrections applied to JSON files.")

def run_audit(proper_nouns):
    print("\n--- RUNNING AUDIT CHECKS ---")
    blacklist_translations = [
        ("Echo", "Tiếng Vang"), ("Echo", "Linh Thú"),
        ("Rover", "Nhà Lữ Hành"), ("Rover", "Vãng Minh Giả"), ("Rover", "Viễn Khách"),
        ("Resonator", "Người Cộng Hưởng"), ("Resonator", "Cộng Hưởng Giả"),
        ("Resonance Skill", "Kỹ Năng Cộng Hưởng"), ("Resonance Skill", "Chiêu Thức Cộng Hưởng"),
        ("Resonance Liberation", "Giải Phóng Cộng Hưởng"), ("Resonance Liberation", "Nộ"),
        ("Forte Circuit", "Mạch Forte"), ("Forte Circuit", "Chuỗi Forte"),
        ("Basic Attack", "Tấn Công Thường"), ("Basic Attack", "Tấn Công Cơ Bản"),
        ("Heavy Attack", "Trọng Kích"), ("Heavy Attack", "Tấn Công Nặng"),
        ("Cooldown", "Hồi Chiêu"), ("Cooldown", "Thời gian hồi"),
        ("Spectro Frazzle", "Nhiễu Loạn Quang Phổ"),
        ("Aero Erosion", "Xói Mòn Gió"),
        ("Glacio Chafe", "Trầy Băng Giá"),
        ("Fusion Burst", "Nổ Nhiệt Hạch"),
        ("Havoc Bane", "Tai Họa Hỗn Loạn"),
        ("Electro Flare", "Điện Tích"), ("Electro Flare", "Bùng Điện"),
        ("Jinzhou", "Kim Châu"),
        ("Mt. Firmament", "Núi Vòm Trời"), ("Mt. Firmament", "Trầm Minh Khánh"),
        ("Emerald of Genesis", "Ngọc Lục Bảo Khởi Nguyên"),
        ("Impermanence Heron", "Vịt Bất Diệt")
    ]
    
    action_verbs_pattern = re.compile(r"\b(Increase|Decrease|Claim|Exchange|Return)\b", re.IGNORECASE)
    weapon_pattern = re.compile(r"\bweapons?\b", re.IGNORECASE)
    
    audit_violations = []
    
    for root, dirs, files in os.walk(ui_dir):
        for f in files:
            if f.endswith(".json"):
                path = os.path.join(root, f)
                rel_path = os.path.relpath(path, ui_dir)
                with open(path, "r", encoding="utf-8") as file:
                    try:
                        data = json.load(file)
                    except Exception as e:
                        print(f"Error reading {rel_path}: {e}")
                        continue
                    
                    for item in data:
                        split_id = item.get("split_id")
                        source_en = item.get("source_en", "")
                        translation_vi = item.get("new_translation_vi", "")
                        table = item.get("table", "")
                        pk = str(item.get("primary_key", ""))
                        source_file = item.get("source_file", "")
                        
                        if not translation_vi:
                            continue
                        
                        # --- CHECK 1: Proper Noun Casing & Preservation ---
                        for noun in proper_nouns:
                            if len(noun) <= 4:
                                noun_pattern = re.compile(rf"\b{re.escape(noun)}\b")
                            else:
                                noun_pattern = re.compile(re.escape(noun))
                            
                            if noun_pattern.search(source_en):
                                if noun not in translation_vi:
                                    if noun.lower() in translation_vi.lower():
                                        audit_violations.append({
                                            "file": rel_path,
                                            "split_id": split_id,
                                            "source": source_en,
                                            "translation": translation_vi,
                                            "type": "Casing Violation",
                                            "detail": f"Proper noun '{noun}' casing is not preserved in translation."
                                        })
                                    else:
                                        audit_violations.append({
                                            "file": rel_path,
                                            "split_id": split_id,
                                            "source": source_en,
                                            "translation": translation_vi,
                                            "type": "Glossary Translation Violation",
                                            "detail": f"Proper noun '{noun}' is missing (translated or modified) in translation."
                                        })
                        
                        # --- CHECK 2: Blacklisted Vietnamese Terms ---
                        for eng, wrong_vi in blacklist_translations:
                            if wrong_vi.lower() in translation_vi.lower():
                                if eng.lower() in source_en.lower():
                                    audit_violations.append({
                                        "file": rel_path,
                                        "split_id": split_id,
                                        "source": source_en,
                                        "translation": translation_vi,
                                        "type": "Blacklisted Translation",
                                        "detail": f"Incorrect translation '{wrong_vi}' used for '{eng}'."
                                    })
                        
                        # --- CHECK 3: Keep English Rules ---
                        is_keep_english_key = False
                        if pk.startswith("ResonantChain_") and pk.endswith("_NodeName"):
                            is_keep_english_key = True
                        elif "_SkillName" in pk:
                            is_keep_english_key = True
                        elif pk.startswith("RoleSkillTreeInfo_") and pk.endswith("_Title"):
                            is_keep_english_key = True
                        elif table == "Skill" and source_file == "lang_skill.json":
                            is_keep_english_key = True
                        elif table == "RoleSkillTreeInfo" and source_file == "lang_skillTree.json":
                            is_keep_english_key = True
                        
                        if is_keep_english_key:
                            if translation_vi != source_en:
                                audit_violations.append({
                                    "file": rel_path,
                                    "split_id": split_id,
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "type": "Keep English Key Rule Violation",
                                    "detail": f"Key rule requires translation to match source exactly, but they differ."
                                })
                        
                        # --- CHECK 4: Placeholders and Rich Text Tags ---
                        source_placeholders = re.findall(r"\{[^\}]+\}", source_en)
                        trans_placeholders = re.findall(r"\{[^\}]+\}", translation_vi)
                        
                        source_ph_counts = {}
                        for ph in source_placeholders:
                            source_ph_counts[ph] = source_ph_counts.get(ph, 0) + 1
                            
                        trans_ph_counts = {}
                        for ph in trans_placeholders:
                            trans_ph_counts[ph] = trans_ph_counts.get(ph, 0) + 1
                            
                        if source_ph_counts != trans_ph_counts:
                            audit_violations.append({
                                "file": rel_path,
                                "split_id": split_id,
                                "source": source_en,
                                "translation": translation_vi,
                                "type": "Placeholder Mismatch",
                                "detail": f"Source placeholders {list(source_ph_counts.keys())} vs Translation {list(trans_ph_counts.keys())}."
                            })
                        
                        source_tags = re.findall(r"<[^>]+>", source_en)
                        trans_tags = re.findall(r"<[^>]+>", translation_vi)
                        
                        for tag in source_tags:
                            if tag not in trans_tags:
                                audit_violations.append({
                                    "file": rel_path,
                                    "split_id": split_id,
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "type": "Tag Mismatch",
                                    "detail": f"Rich text tag '{tag}' from source is missing or modified in translation."
                                })
                        
                        opening_tags = [t for t in trans_tags if not t.startswith("</") and not t.endswith("/>")]
                        closing_tags = [t for t in trans_tags if t.startswith("</")]
                        def get_tag_name(t):
                            match = re.match(r"<([a-zA-Z]+)", t)
                            return match.group(1) if match else t
                        
                        opening_names = [get_tag_name(t) for t in opening_tags]
                        closing_names = [t[2:-1] for t in closing_tags]
                        
                        for name in set(opening_names):
                            if name in ["color", "size", "te", "SapTag"]:
                                op_count = opening_names.count(name)
                                cl_count = closing_names.count(name)
                                if op_count != cl_count:
                                    audit_violations.append({
                                        "file": rel_path,
                                        "split_id": split_id,
                                        "source": source_en,
                                        "translation": translation_vi,
                                        "type": "Tag Unbalanced",
                                        "detail": f"Tag '{name}' is unbalanced: {op_count} opening vs {cl_count} closing."
                                    })
                                    
                        source_newlines = source_en.count("\\n") + source_en.count("\n")
                        trans_newlines = translation_vi.count("\\n") + translation_vi.count("\n")
                        if source_newlines != trans_newlines:
                            audit_violations.append({
                                "file": rel_path,
                                "split_id": split_id,
                                "source": source_en,
                                "translation": translation_vi,
                                "type": "Newline Mismatch",
                                "detail": f"Source has {source_newlines} newlines, translation has {trans_newlines}."
                            })
                        
                        # --- CHECK 5: Untranslated Action Verbs ---
                        trans_clean = re.sub(r"\{[^\}]+\}", "", translation_vi)
                        trans_clean = re.sub(r"<[^>]+>", "", trans_clean)
                        
                        verb_matches = action_verbs_pattern.findall(trans_clean)
                        if verb_matches:
                            source_clean = re.sub(r"\{[^\}]+\}", "", source_en)
                            source_clean = re.sub(r"<[^>]+>", "", source_clean)
                            source_verbs = action_verbs_pattern.findall(source_clean)
                            
                            violating_verbs = [v for v in verb_matches if any(sv.lower() == v.lower() for sv in source_verbs)]
                            if violating_verbs:
                                audit_violations.append({
                                    "file": rel_path,
                                    "split_id": split_id,
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "type": "Untranslated Action Verb",
                                    "detail": f"Action verbs {list(set(violating_verbs))} were left untranslated."
                                })
                        
                        # --- CHECK 6: Standalone / Isolated Weapon Word ---
                        weapon_matches = weapon_pattern.findall(trans_clean)
                        if weapon_matches:
                            if weapon_pattern.search(source_en):
                                audit_violations.append({
                                    "file": rel_path,
                                    "split_id": split_id,
                                    "source": source_en,
                                    "translation": translation_vi,
                                    "type": "Untranslated Weapon Word",
                                    "detail": f"Isolated or general word 'Weapon(s)' was left untranslated."
                                })
    
    unique_audit = {}
    for v in audit_violations:
        key = (v["split_id"], v["type"])
        if key not in unique_audit:
            unique_audit[key] = v
            
    print(f"Total audit violations found: {len(audit_violations)}")
    print(f"Unique audit violations found: {len(unique_audit)}")
    
    # Overwrite the explorer violations report to reflect actual remaining violations!
    with open(violations_report_path, "w", encoding="utf-8") as out_f:
        json.dump(list(unique_audit.values()), out_f, ensure_ascii=False, indent=2)
        
    print(f"Updated violations report at {violations_report_path}.")
    return len(unique_audit)

def main_flow():
    proper_nouns = load_proper_nouns()
    print(f"Loaded {len(proper_nouns)} proper nouns from glossary.")
    
    # Run corrections
    run_corrections(proper_nouns)
    
    # Regenerate Excel
    print("\nRegenerating consolidated Excel: ui_all.xlsx...")
    ui_files = list(Path(ui_dir).rglob("*.json"))
    records = []
    for f_path in ui_files:
        with open(f_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f, strict=False)
                if isinstance(data, list):
                    records.extend(data)
                else:
                    records.append(data)
            except Exception as e:
                print(f"Error loading {f_path} for Excel export: {e}")
                
    columns = [
        'split_id', 'prompt_domain', 'prompt_file', 'source_file',
        'original_index', 'database', 'table', 'primary_key_column',
        'primary_key', 'column', 'category', 'source_en',
        'new_translation_vi', 'translator_note'
    ]
    df = pd.DataFrame(records)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df = df[columns]
    df = df.sort_values(by=['source_file', 'original_index'])
    
    excel_path = Path(out_dir) / "ui_all.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"Excel regenerated successfully at {excel_path}!")
    
    # Run audit and print final status
    violations_count = run_audit(proper_nouns)
    if violations_count == 0:
        print("\nSUCCESS: All violations fixed, 0 remaining violations!")
    else:
        print(f"\nWARNING: {violations_count} remaining violations. Please check violations_report.json.")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    main_flow()
