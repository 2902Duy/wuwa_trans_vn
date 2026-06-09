import os
import re
from pathlib import Path

WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
PROMPT_DIR = WORKSPACE_DIR / "mistral_translate_work" / "prompts"
OUT_DIR = WORKSPACE_DIR / "mistral_translate_work" / "prompts_compressed"

OUT_DIR.mkdir(parents=True, exist_ok=True)

def compress_shared_glossary(content):
    # Condense shared glossary by replacing huge name lists with concise summaries
    sections = []
    current_section = []
    lines = content.splitlines()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for boss/echo names list
        if "### 5. Tên Quái vật" in line:
            sections.append(line)
            sections.append("Bắt buộc giữ nguyên tiếng Anh tên của tất cả các Tacet Discords, Boss tuần, Quái vật, Sentinel và tên của Echo (ví dụ: Crownless, Impermanence Heron, Mourning Aix, Tempest Mephis, Jué, Aero Prism, Gulpuff). Không dịch, không viết lại.")
            # Skip until next section
            i += 1
            while i < len(lines) and not lines[i].startswith("### 6."):
                i += 1
            continue
            
        # Check for resonator names list
        if "### 6. Tên Nhân vật" in line:
            sections.append(line)
            sections.append("Bắt buộc giữ nguyên tiếng Anh tên của tất cả các nhân vật cộng hưởng (Resonator) (ví dụ: Rover, Yangyang, Chixia, Jinhsi, Jiyan, Changli, Yinlin, Taoqi, Encore, Verina, Shorekeeper). Không dịch.")
            i += 1
            while i < len(lines) and not lines[i].startswith("### 7."):
                i += 1
            continue
            
        # Check for location names list
        if "### 7. Tên Địa danh" in line:
            sections.append(line)
            sections.append("Bắt buộc giữ nguyên tiếng Anh tên của tất cả các khu vực, địa danh, vùng đất (ví dụ: Huanglong, Jinzhou, Mt. Firmament, Central Plains, Desorock Highland, Dim Forest, Gorges of Spirits, Black Shores). Không dịch.")
            i += 1
            while i < len(lines) and not lines[i].startswith("### 8."):
                i += 1
            continue
            
        # Check for weapon names list
        if "### 8. Tên Vũ khí" in line:
            sections.append(line)
            sections.append("Bắt buộc giữ nguyên tiếng Anh tên của tất cả các loại vũ khí 3-sao, 4-sao và 5-sao trong game (ví dụ: Emerald of Genesis, Stringmaster, Abyss Surges, Ages of Harvest, Autumntrace, Jinzhou Keeper). Không dịch.")
            i += 1
            while i < len(lines) and not lines[i].startswith("### 9."):
                i += 1
            continue
            
        sections.append(line)
        i += 1
        
    return "\n".join(sections)

def compress_keep_english_rules(content):
    # Condense keep english rules by replacing large lists with summaries
    lines = content.splitlines()
    sections = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if any(line.startswith(f"## {num}.") for num in range(1, 6)):
            sections.append(line)
            sections.append("- Giữ nguyên 100% tiếng Anh cho tất cả tên vũ khí, quái vật, nhân vật, địa danh, tài nguyên và tiền tệ.")
            sections.append("- Tuyệt đối không dịch nghĩa hoặc Việt hóa các cụm tên này.")
            # Skip down to next heading or section
            i += 1
            while i < len(lines) and not (lines[i].startswith("## ") or lines[i].startswith("---")):
                i += 1
            continue
            
        sections.append(line)
        i += 1
        
    return "\n".join(sections)

def compress_character_voice_map(content):
    # Condense the giant resonator table into groups
    condensed = """# Character Voice Map (Nén tối ưu)

## Quy tắc xưng hô và sắc thái mặc định với Rover (Giữ trung tính giới tính):

1. **Rover (Spectro/Havoc/Aero)**: Trung tính, bình tĩnh, chính trực. Tự xưng `tôi/tớ/ta` theo ngữ cảnh; không khóa giới tính của Rover.
2. **Nhóm Bạn bè / Ngang hàng** (Yangyang, Chixia, Lingyang, Zhezhi, Lumi, Youhu, Iuno, Lucy): 
   - Tự xưng: `tớ/mình` hoặc `tôi`.
   - Gọi Rover: `cậu/bạn/Rover`.
3. **Nhóm Đàn chị / Hơn tuổi** (Changli, Taoqi, Mornye, Yinlin):
   - Tự xưng: `tôi` (viết trực tiếp, không dùng nhãn động).
   - Gọi Rover: `{Male=cậu;Female=em}`. Sắc thái lịch sự, chừng mực, chuyên nghiệp, tránh gọi "chị".
4. **Nhóm Nghiêm túc / Lính / Học giả** (Jiyan, Mortefi, Baizhi, Calcharo, Xiangli Yao, Danjin, Sanhua, Brant, Hiyuki, Luuk Herssen, Zani):
   - Tự xưng: `tôi`.
   - Gọi Rover: `cậu/Rover/bạn`.
5. **Nhóm Uy quyền / Trang trọng** (Jinhsi, Shorekeeper, Jianxin, Jué, Cartethyia, Cantarella):
   - Tự xưng: `tôi/ta`.
   - Gọi Rover: `Rover/người/cậu`.
6. **Nhóm Trẻ nhỏ** (Encore/An'ke, Verina, Youhu):
   - Tự xưng: `em`.
   - Gọi Rover: Bắt buộc gọi `Rover` hoặc ẩn chủ ngữ (Tuyệt đối không dùng `anh/chị` để gọi Rover).
7. **Nhóm Phản diện / Đối đầu** (Scar, Phrolova, Camellya, Roccia, Exile Leaders):
   - Tự xưng: `ta`.
   - Gọi Rover: `ngươi/Rover`.
8. **Nhóm Quần chúng / NPCs chung**:
   - Người lớn tuổi: Tự xưng `ta/lão/bà` - gọi Rover là `cậu/cháu/người trẻ tuổi`.
   - Người ngang hàng/Lính: Tự xưng `tôi` - gọi Rover là `cậu/bạn/Rover`.
   - Trẻ em NPC: Tự xưng `em/cháu` - gọi Rover là `Rover` (không gọi anh/chị).
   - Thương nhân: Tự xưng `tôi` - gọi Rover là `quý khách/cậu`.
"""
    return condensed

def compress_general_prompt(content):
    # General prompt compression: remove verbose explanations, keeps key bullets
    lines = content.splitlines()
    clean_lines = []
    for line in lines:
        # Skip verbose comments or links to local files since LLM doesn't read them
        if "character_voice_map.md" in line or "shared_glossary.md" in line or "keep_english_rules.md" in line:
            # Keep the reference but clean it up
            line = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line)
        
        # Strip long warning descriptions but keep tables
        clean_lines.append(line)
        
    return "\n".join(clean_lines)

def main():
    print("Starting prompt compression...")
    for file_path in PROMPT_DIR.glob("*.md"):
        name = file_path.name
        if name == "README.md":
            continue
            
        content = file_path.read_text(encoding="utf-8")
        
        if name == "shared_glossary.md":
            compressed = compress_shared_glossary(content)
        elif name == "keep_english_rules.md":
            compressed = compress_keep_english_rules(content)
        elif name == "character_voice_map.md":
            compressed = compress_character_voice_map(content)
        else:
            compressed = compress_general_prompt(content)
            
        # Add strict pronoun rule reinforcement to dialogue prompts
        if name == "story_dialogue_prompt.md":
            # Append strict tao-may bans and ta-nguoi rules
            compressed += """
            
## QUY TẮC CẤM TUYỆT ĐỐI VỀ ĐẠI TỪ PHẢN DIỆN VÀ THÙ ĐỊCH (CRITICAL BANS)

* **TUYỆT ĐỐI NGHIÊM CẤM** sử dụng các đại từ suồng sã, thiếu lịch sự đời thường như **"mày"**, **"tao"** trong bất kỳ hoàn cảnh nào (kể cả khi nhân vật giận dữ, khinh bỉ hay đối đầu).
* **Bắt buộc sử dụng cặp "ta" - "ngươi"** (hoặc "ta" - "các ngươi" cho số nhiều) đối với kẻ địch, phản diện, hoặc các đối thoại thù địch để giữ sắc thái kiếm hiệp/giả tưởng phương Đông trang trọng.
"""
            
        out_path = OUT_DIR / name
        out_path.write_text(compressed, encoding="utf-8")
        print(f"Compressed {name}: {len(content)} -> {len(compressed)} bytes ({len(compressed)/len(content)*100:.1f}%)")

if __name__ == "__main__":
    main()
