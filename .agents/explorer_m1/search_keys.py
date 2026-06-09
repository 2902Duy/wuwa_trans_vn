import os
import json

ui_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"

rc_nodes = 0
skill_names = 0
total_items = 0

for root, dirs, files in os.walk(ui_dir):
    for f in files:
        if f.endswith(".json"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
                for item in data:
                    total_items += 1
                    pk = str(item.get("primary_key", ""))
                    table = item.get("table", "")
                    
                    # Check Resonance Chain Node Rule
                    # starts with ResonantChain_ and ends with _NodeName
                    if pk.startswith("ResonantChain_") and pk.endswith("_NodeName"):
                        rc_nodes += 1
                    
                    # Check Character Skill Name Rule
                    is_skill_name = False
                    if "_SkillName" in pk:
                        is_skill_name = True
                    elif pk.startswith("RoleSkillTreeInfo_") and pk.endswith("_Title"):
                        is_skill_name = True
                    elif table == "Skill" and item.get("source_file") == "lang_skill.json":
                        is_skill_name = True
                    elif table == "RoleSkillTreeInfo" and item.get("source_file") == "lang_skillTree.json":
                        is_skill_name = True
                    
                    if is_skill_name:
                        skill_names += 1

print(f"Total items scanned: {total_items}")
print(f"Resonance Chain Nodes found: {rc_nodes}")
print(f"Character Skill Names found: {skill_names}")
