import re
import os
import json
from pathlib import Path

WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
PROMPT_DIR = WORKSPACE_DIR / "mistral_translate_work" / "prompts"
SPLIT_JSON_DIR = WORKSPACE_DIR / "mistral_translate_work" / "split_by_prompt" / "json"

def extract_proper_nouns():
    weapons = set()
    monsters = set()
    resonators = set()
    
    name_title_dir = SPLIT_JSON_DIR / "name_title"
    if name_title_dir.exists():
        for path in name_title_dir.rglob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    rows = json.load(f)
                    for row in rows:
                        source = row.get("source_en", "").strip()
                        note = row.get("translator_note", "")
                        table = row.get("table", "")
                        pk = row.get("primary_key", "")
                        
                        if not source or source.isdigit():
                            continue
                            
                        # Basic length filters
                        if len(source) > 60 or source.count(" ") > 5:
                            continue
                            
                        # Weapons
                        is_weapon = False
                        if table == "WeaponConf" or "lang_weapon" in path.name:
                            is_weapon = True
                        elif table == "MultiText" and pk.startswith("WeaponConf_") and pk.endswith("_WeaponName"):
                            is_weapon = True
                            
                        if is_weapon:
                            if note in ("keep_proper_name", "keep_item_weapon_echo_name"):
                                weapons.add(source)
                            continue
                            
                        # Resonators
                        is_resonator = False
                        if table in ("RoleInfo", "RoleConf") or "lang_role" in path.name:
                            is_resonator = True
                        elif table == "MultiText" and pk.startswith("RoleInfo_") and pk.endswith("_Name"):
                            is_resonator = True
                            
                        if is_resonator:
                            if note == "keep_proper_name":
                                resonators.add(source)
                            continue
                            
                        # Monsters
                        is_monster = False
                        if table == "MonsterInfo" or "lang_monster_Info" in path.name:
                            is_monster = True
                        elif table == "MultiText" and pk.startswith("MonsterInfo_") and pk.endswith("_Name"):
                            is_monster = True
                            
                        if is_monster:
                            if note in ("keep_proper_name", "keep_item_weapon_echo_name"):
                                monsters.add(source)
                            continue
            except Exception:
                pass

    # Exclusions
    exclude_resonators = {
        "All", "R", "Black Shores", "Crimson Blades", "Huanglong", 
        "Sadness Enshroud", "Snow Dance Flora", "The Ever Burning Flame", 
        "Yin Yang Sheep", "Rover", "PlayerName", "Crownless", "Cruisewing", 
        "Currie", "Excarat", "Gulpuff", "Jué", "Stonewall Bracer", "Zapstring"
    }
    clean_resonators = resonators - exclude_resonators
    
    exclude_monsters = {
        "Black Shores", "Central Plains", "Calamity Class", "Elite Class", 
        "Overlord Class", "Standard Class", "Desorock Highland", "Dim Forest", 
        "Huanglong", "Norfall Barrens", "Tiancheng Urban Area", "Wasted Metropolis", 
        "Whining Aix's Mire", "Exile"
    }
    
    # Remove any resonator names and names with colons from monsters
    clean_monsters = set()
    for m in monsters:
        if m in clean_resonators or ":" in m or m in exclude_monsters:
            continue
        clean_monsters.add(m)
        
    exclude_weapons = {"Weapon", "R"}
    clean_weapons = weapons - exclude_weapons

    return sorted(list(clean_weapons)), sorted(list(clean_monsters)), sorted(list(clean_resonators))

def parse_backticks(text):
    return re.findall(r'`([^`]+)`', text)

def update_keep_rules_md(path, new_weapons, new_monsters, new_resonators):
    if not path.exists():
        return False
    
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    sec1_start, sec1_end = -1, -1
    sec2_start, sec2_end = -1, -1
    sec3_start, sec3_end = -1, -1
    
    for idx, line in enumerate(lines):
        if "## 1. Tên Vũ Khí" in line or "## 1. Tên Vũ khí" in line:
            sec1_start = idx
        elif "## 2. Tên Thú Cưng" in line or "## 2. Tên quái vật" in line or "## 2. Tên Thú cưng" in line:
            sec1_end = idx
            sec2_start = idx
        elif "## 3. Tên Nhân vật" in line or "## 3. Tên nhân vật" in line:
            sec2_end = idx
            sec3_start = idx
        elif "## 4. Tên Bộ Echo" in line or "## 4. Tên bộ Echo" in line:
            sec3_end = idx
            
    modified = False
    
    # 1. Update Section 1 Weapons
    if sec1_start != -1 and sec1_end != -1:
        bullet_indices = []
        for i in range(sec1_start, sec1_end):
            if re.match(r'^\s*>\s*-\s*`([^`]+)`', lines[i]):
                bullet_indices.append(i)
        if bullet_indices:
            existing_weapons = []
            for i in bullet_indices:
                existing_weapons.extend(parse_backticks(lines[i]))
            merged_weapons = sorted(list(set(existing_weapons) | set(new_weapons)))
            start_idx = bullet_indices[0]
            end_idx = bullet_indices[-1]
            new_bullets = [f"> - `{w}`" for w in merged_weapons]
            lines[start_idx:end_idx + 1] = new_bullets
            diff_len = len(new_bullets) - (end_idx - start_idx + 1)
            sec1_end += diff_len
            sec2_start += diff_len
            sec2_end += diff_len
            sec3_start += diff_len
            sec3_end += diff_len
            modified = True

    # 2. Update Section 2 Monsters
    if sec2_start != -1 and sec2_end != -1:
        bullet_indices = []
        for i in range(sec2_start, sec2_end):
            if re.match(r'^\s*>\s*-\s*`([^`]+)`', lines[i]):
                bullet_indices.append(i)
        if bullet_indices:
            existing_monsters = []
            for i in bullet_indices:
                existing_monsters.extend(parse_backticks(lines[i]))
            merged_monsters = sorted(list(set(existing_monsters) | set(new_monsters)))
            start_idx = bullet_indices[0]
            end_idx = bullet_indices[-1]
            new_bullets = [f"> - `{m}`" for m in merged_monsters]
            lines[start_idx:end_idx + 1] = new_bullets
            diff_len = len(new_bullets) - (end_idx - start_idx + 1)
            sec2_end += diff_len
            sec3_start += diff_len
            sec3_end += diff_len
            modified = True

    # 3. Update Section 3 Resonators line:
    if sec3_start != -1 and sec3_end != -1:
        resonators_line_idx = -1
        for i in range(sec3_start, sec3_end):
            if "Nhân vật:" in lines[i] and "`" in lines[i]:
                resonators_line_idx = i
                break
        if resonators_line_idx != -1:
            line_val = lines[resonators_line_idx]
            existing_res = parse_backticks(line_val)
            existing_res = [r for r in existing_res if r != "..."]
            merged_res = sorted(list(set(existing_res) | set(new_resonators)))
            res_str = ", ".join(f"`{r}`" for r in merged_res)
            match = re.match(r'^([^`]*`)(.*)$', line_val)
            if match:
                prefix = match.group(1).split("`")[0]
                lines[resonators_line_idx] = f"{prefix}{res_str}..."
                modified = True

    if modified:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True
    return False

def update_shared_glossary_md(path, new_weapons, new_monsters, new_resonators):
    if not path.exists():
        return False
    
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    modified = False
    
    for idx, line in enumerate(lines):
        # 1. Resonators list in shared_glossary.md:
        if idx > 0 and "### 6. Tên Nhân vật" in lines[idx-1] or (idx > 1 and "### 6. Tên Nhân vật" in lines[idx-2]):
            for j in range(idx, idx + 5):
                if lines[j].strip().startswith("- `"):
                    existing_res = parse_backticks(lines[j])
                    merged_res = sorted(list(set(existing_res) | set(new_resonators)))
                    res_str = ", ".join(f"`{r}`" for r in merged_res)
                    lines[j] = f"- {res_str}"
                    modified = True
                    break
                    
        # 2. Monsters list in shared_glossary.md:
        elif idx > 0 and "### 5. Tên Quái vật" in lines[idx-1] or (idx > 1 and "### 5. Tên Quái vật" in lines[idx-2]):
            for j in range(idx, idx + 5):
                if lines[j].strip().startswith("- `"):
                    existing_monsters = parse_backticks(lines[j])
                    merged_monsters = sorted(list(set(existing_monsters) | set(new_monsters)))
                    monsters_str = ", ".join(f"`{m}`" for m in merged_monsters)
                    lines[j] = f"- {monsters_str}"
                    modified = True
                    break
                    
        # 3. Weapons lists in shared_glossary.md:
        elif "Danh sách Vũ khí 5-Sao:" in line:
            for j in range(idx + 1, idx + 5):
                if lines[j].strip().startswith("- `"):
                    existing = parse_backticks(lines[j])
                    lines[j] = f"- {', '.join(f'`{w}`' for w in sorted(existing))}"
                    modified = True
                    break
        elif "Danh sách Vũ khí 4-Sao:" in line:
            for j in range(idx + 1, idx + 5):
                if lines[j].strip().startswith("- `"):
                    existing = parse_backticks(lines[j])
                    lines[j] = f"- {', '.join(f'`{w}`' for w in sorted(existing))}"
                    modified = True
                    break
        elif "Danh sách Vũ khí 3-Sao, 2-Sao, 1-Sao" in line:
            for j in range(idx + 1, idx + 5):
                if lines[j].strip().startswith("- `"):
                    existing = parse_backticks(lines[j])
                    all_existing_weapons = set()
                    for k in range(len(lines)):
                        if "Danh sách Vũ khí" in lines[k] or "Vũ khí thường" in lines[k]:
                            for m in range(k+1, k+4):
                                if m < len(lines) and lines[m].strip().startswith("- `"):
                                    all_existing_weapons.update(parse_backticks(lines[m]))
                    brand_new_weapons = [w for w in new_weapons if w not in all_existing_weapons]
                    merged = sorted(list(set(existing) | set(brand_new_weapons)))
                    lines[j] = f"- {', '.join(f'`{w}`' for w in merged)}"
                    modified = True
                    break

    if modified:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return True
    return False

def main():
    print("Extracting keywords from split JSON files...")
    weapons, monsters, resonators = extract_proper_nouns()
    print(f"Found {len(weapons)} weapons, {len(monsters)} monsters, {len(resonators)} resonators.")
    
    # Update keep_english_rules.md
    keep_rules_path = PROMPT_DIR / "keep_english_rules.md"
    if update_keep_rules_md(keep_rules_path, weapons, monsters, resonators):
        print(f"Updated {keep_rules_path.name} successfully.")
    else:
        print(f"No changes or failed to update {keep_rules_path.name}.")
        
    # Update shared_glossary.md
    glossary_path = PROMPT_DIR / "shared_glossary.md"
    if update_shared_glossary_md(glossary_path, weapons, monsters, resonators):
        print(f"Updated {glossary_path.name} successfully.")
    else:
        print(f"No changes or failed to update {glossary_path.name}.")

if __name__ == "__main__":
    main()
