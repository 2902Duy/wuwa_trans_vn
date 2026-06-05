import os
import json
import re
from pathlib import Path

WORKSPACE = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
JSON_DIR = WORKSPACE / "mistral_translate_work" / "split_by_prompt" / "json"
RULES_PATH = WORKSPACE / "mistral_translate_work" / "prompts" / "keep_english_rules.md"
REPORT_PATH = WORKSPACE / "mistral_translate_work" / "reports" / "keep_english_violations_report.json"

def parse_keep_rules():
    if not RULES_PATH.exists():
        print(f"Error: {RULES_PATH} does not exist!")
        return {}, set()

    content = RULES_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    weapons = set()
    monsters = set()
    resonators = set()
    echo_sets = set()
    resources = set()

    current_section = 0
    for line in lines:
        line_strip = line.strip()
        # Detect sections
        if "## 1. Tên Vũ Khí" in line or "## 1. Tên Vũ khí" in line:
            current_section = 1
            continue
        elif "## 2. Tên Thú Cưng" in line or "## 2. Tên quái vật" in line or "## 2. Tên Thú cưng" in line:
            current_section = 2
            continue
        elif "## 3. Tên Nhân vật" in line or "## 3. Tên nhân vật" in line:
            current_section = 3
            continue
        elif "## 4. Tên Bộ Echo" in line or "## 4. Tên bộ Echo" in line:
            current_section = 4
            continue
        elif "## 5. Waveplate" in line:
            current_section = 5
            continue
        elif line.startswith("## "):
            current_section = 0
            continue
            
        # Parse only bullet points or list items
        if line_strip.startswith("> - `") or line_strip.startswith("- `") or "Nhân vật:" in line_strip or "Địa danh:" in line_strip:
            terms = re.findall(r'`([^`]+)`', line_strip)
            for t in terms:
                t_clean = t.strip()
                if not t_clean or t_clean == "...":
                    continue
                if current_section == 1:
                    weapons.add(t_clean)
                elif current_section == 2:
                    monsters.add(t_clean)
                elif current_section == 3:
                    resonators.add(t_clean)
                elif current_section == 4:
                    echo_sets.add(t_clean)
                elif current_section == 5:
                    resources.add(t_clean)

    # Exclude categories we know are generic warning terms
    ignore = {"Weapon", "Echo", "Quest_"}
    weapons = {w for w in weapons if w not in ignore}
    monsters = {m for m in monsters if m not in ignore}
    resonators = {r for r in resonators if r not in ignore}
    echo_sets = {e for e in echo_sets if e not in ignore}
    resources = {r for r in resources if r not in ignore}

    print(f"Parsed {len(weapons)} weapons, {len(monsters)} monsters, {len(resonators)} resonators, {len(echo_sets)} echo sets, {len(resources)} resources.")
    return {
        "weapons": weapons,
        "monsters": monsters,
        "resonators": resonators,
        "echo_sets": echo_sets,
        "resources": resources
    }, (weapons | monsters | resonators | echo_sets | resources)


def scan_violations():
    categories, all_terms = parse_keep_rules()
    violations = []

    for path in sorted(JSON_DIR.rglob("*.json")):
        rel_path = path.relative_to(JSON_DIR).as_posix()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {rel_path}: {e}")
            continue

        if not isinstance(data, list):
            continue

        for idx, row in enumerate(data):
            source = str(row.get("source_en") or "").strip()
            target = str(row.get("new_translation_vi") or "").strip()
            pk = str(row.get("primary_key") or "")
            table = str(row.get("table") or "")

            if not source or not target:
                continue

            # If the translation is identical to source, it is NOT a violation
            if target == source:
                continue

            violation_reason = None

            # Check exact term matching
            if source in categories["weapons"]:
                violation_reason = "Weapon Name (exact match)"
            elif source in categories["monsters"]:
                violation_reason = "Monster/Echo Name (exact match)"
            elif source in categories["resonators"]:
                violation_reason = "Resonator/Location Name (exact match)"
            elif source in categories["echo_sets"]:
                violation_reason = "Echo Set Name (exact match)"
            elif source in categories["resources"]:
                violation_reason = "Resource/Currency (exact match)"
            
            # Check Resonance Chain Node Rule
            elif pk.startswith("ResonantChain_") and pk.endswith("_NodeName"):
                violation_reason = "Resonance Chain Node Name (Rule 6)"
                
            # Check Character Skill Name Rule
            elif (
                (
                    "_SkillName" in pk or 
                    (pk.startswith("Skill_") and pk.endswith("_SkillName")) or
                    (pk.startswith("RoleSkillTreeInfo_") and pk.endswith("_Title")) or
                    table in ("Skill", "RoleSkillTreeInfo")
                ) and not any(x in pk for x in ("_SkillDescribe", "_Description", "_DescList"))
            ):
                violation_reason = "Character Skill Name (Rule 7)"

            # If a violation is found
            if violation_reason:
                violations.append({
                    "file": rel_path,
                    "primary_key": pk,
                    "table": table,
                    "source_en": source,
                    "new_translation_vi": target,
                    "reason": violation_reason
                })

    print(f"Total violations found: {len(violations)}")
    
    # Save report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(violations, f, ensure_ascii=False, indent=2)
    print(f"Saved report to {REPORT_PATH}")

if __name__ == "__main__":
    scan_violations()
