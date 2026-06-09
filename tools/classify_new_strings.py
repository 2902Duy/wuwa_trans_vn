"""
Phan loai cac string moi/thay doi trong new_strings_to_translate.json
theo prompt tuong ung dua vao key pattern tu file_classification.md
"""
import json, re

IN_FILE  = "new_strings_to_translate.json"
OUT_FILE = "new_strings_classified.json"

# -------------------------------------------------------
# BANG PHAN LOAI: (pattern_regex, prompt_file, group_name)
# Thu tu quan trong: match dau tien thang
# -------------------------------------------------------
RULES = [
    # --- Skill / RC ---
    (r"ResonantChain_\d+_AttributesDescription",    "rc_description_prompt",      "Resonance Chain - Effect"),
    (r"ResonantChain_\d+_NodeName",                 "keep_english",               "Resonance Chain - Name (KEEP EN)"),
    (r"SkillInput_\d+_",                            "skill_description_prompt",   "Skill Description"),
    (r"Skill_\d+_SkillDescribe",                    "skill_description_prompt",   "Skill Description"),
    (r"Skill_\d+_SkillDescription",                 "skill_description_prompt",   "Skill Description"),
    (r"Skill_\d+_SkillName",                        "keep_english",               "Skill Name (KEEP EN)"),
    (r"RoleSkillTree",                              "keep_english",               "Skill Tree Node (KEEP EN)"),
    (r"Pinball_Character_skill",                    "skill_description_prompt",   "Skill Description"),

    # --- Phantom / Echo ---
    (r"PhantomBattle_",                             "phantom_skill_prompt",       "Echo Skill"),
    (r"PhantomFetter_",                             "echo_set_prompt",            "Echo Set Effect"),

    # --- Weapon ---
    (r"WeaponConf_",                                "weapon_prompt",              "Weapon"),
    (r"WeaponReson_",                               "weapon_prompt",              "Weapon Resonance"),

    # --- Quest / Objective ---
    (r"Quest_\d+_QuestScheduleSubTitle",            "quest_prompt",               "Quest Objective"),
    (r"Quest_\d+_QuestDesc",                        "quest_prompt",               "Quest Description"),
    (r"Quest_\d+_ChildQuestTip",                    "quest_prompt",               "Quest Step Tip"),
    (r"Quest_\d+_",                                 "quest_prompt",               "Quest"),
    (r"LevelPlay_\d+_",                             "quest_prompt",               "Challenge/Level Quest"),

    # --- Story / Dialogue (Main) ---
    (r"^(MAIN|Main)_",                              "story_dialogue_prompt",      "Main Story Dialogue"),
    (r"^Heihaian_main_",                            "story_dialogue_prompt",      "Main Story Dialogue"),
    (r"^Huanglong_main_",                           "story_dialogue_prompt",      "Main Story Dialogue"),
    (r"^Shixifeidu_main_",                          "story_dialogue_prompt",      "Main Story Dialogue"),
    (r"^Main_Honami_",                              "story_dialogue_prompt",      "Main Story Dialogue"),
    (r"^Main_LahaiRoi_",                            "story_dialogue_prompt",      "Main Story Dialogue"),
    (r"^Main_Linaxita_",                            "story_dialogue_prompt",      "Main Story Dialogue"),
    (r"^HuanglongM\d+_",                            "story_dialogue_prompt",      "Main Story Dialogue"),
    (r"^Flow_\d+_",                                 "story_dialogue_prompt",      "Story Flow Dialogue"),

    # --- Story / Dialogue (Side / Event / NPC) ---
    (r"^Side_",                                     "story_dialogue_prompt",      "Side Quest Dialogue"),
    (r"^Event(TQDX|_[A-Z])",                        "story_dialogue_prompt",      "Event Dialogue"),
    (r"^Daily_",                                    "story_dialogue_prompt",      "Daily Quest Dialogue"),
    (r"^NPC_",                                      "story_dialogue_prompt",      "NPC Dialogue"),
    (r"^POI_",                                      "story_dialogue_prompt",      "POI Dialogue"),
    (r"^GNNPC_",                                    "story_dialogue_prompt",      "NPC Dialogue"),
    (r"^HD_",                                       "story_dialogue_prompt",      "Story Dialogue"),
    (r"^HHYSTBC_",                                  "story_dialogue_prompt",      "Story Dialogue"),
    (r"^TWTPOIZX_",                                 "story_dialogue_prompt",      "Story Dialogue"),
    (r"^ZLXYBLZ_",                                  "story_dialogue_prompt",      "Story Dialogue"),
    (r"^BVBHD_",                                    "story_dialogue_prompt",      "Story Dialogue"),
    (r"^BGYDGDSJ_",                                 "story_dialogue_prompt",      "Story Dialogue"),
    (r"^STNPC_",                                    "story_dialogue_prompt",      "Story Dialogue"),
    (r"^RGZYYYGJZ_",                                "story_dialogue_prompt",      "Story Dialogue"),
    (r"^MAIN_RGLC_",                                "story_dialogue_prompt",      "Story Dialogue"),
    (r"^MAIN_YHX_",                                 "story_dialogue_prompt",      "Story Dialogue"),

    # --- Character Dialogue ---
    (r"^Character_",                                "story_dialogue_prompt",      "Character Dialogue"),
    (r"^Guide_[A-Z]",                               "story_dialogue_prompt",      "Guide/Companion Dialogue"),
    (r"^FavorStory_",                               "lore_prompt",                "Companion Story (Lore)"),
    (r"^FavorWord_",                                "story_dialogue_prompt",      "Companion Word/Dialogue"),
    (r"^HonamiStoryTalent_",                        "story_dialogue_prompt",      "Story Talent Dialogue"),

    # --- Achievement ---
    (r"^Achievement_",                              "quest_prompt",               "Achievement"),

    # --- Lore / Term / Handbook ---
    (r"^Term\d+_Desc",                              "lore_prompt",                "Glossary/Term Lore"),
    (r"^InfoDisplay_",                              "lore_prompt",                "Info Display Lore"),
    (r"^MusicDes_",                                 "lore_prompt",                "Music Description"),
    (r"^GeographyRound_",                           "lore_prompt",                "Geography/Lore"),
    (r"^Handbook_",                                 "lore_prompt",                "Handbook Lore"),

    # --- Monster ---
    (r"^MonsterInfo_",                              "monster_description_prompt", "Monster Info"),

    # --- Item ---
    (r"^ItemInfo_",                                 "item_prompt",                "Item Description"),
    (r"^Item_\d+_",                                 "item_prompt",                "Item"),

    # --- UI / System ---
    (r"^PrefabTextItem_",                           "ui_prompt",                  "UI Text"),
    (r"^AdvertisingStory_",                         "ui_prompt",                  "UI Story Ad"),
    (r"^CrossLine_",                                "ui_prompt",                  "UI CrossLine"),
    (r"^LianjiPaoku_",                              "ui_prompt",                  "UI Leaderboard"),
    (r"^Tutorial_",                                 "ui_prompt",                  "Tutorial UI"),
    (r"^RoadBookTaskName_",                         "quest_prompt",               "Road Book Task"),
    (r"^Speaker_",                                  "name_title_prompt",          "Speaker Name"),
    (r"^InstanceDungeon_",                          "ui_prompt",                  "Dungeon Name/UI"),
    (r"^MapMark_",                                  "ui_prompt",                  "Map Mark"),
    (r"^PhantomBattle_",                            "ui_prompt",                  "Phantom Battle UI"),

    # --- Rogue / Event Mini-game ---
    (r"^RogueBuffPool_",                            "skill_description_prompt",   "Rogue Buff"),
    (r"^RogueRes_",                                 "ui_prompt",                  "Rogue Event"),
    (r"^TowerDefense_",                             "ui_prompt",                  "Tower Defense UI"),
    (r"^RhythmTask_",                               "ui_prompt",                  "Rhythm Task UI"),
    (r"^bossrush\d+_",                              "skill_description_prompt",   "Boss Rush Buff"),
    (r"^ReignsCard_",                               "ui_prompt",                  "Reigns Card Event"),

    # --- Entity / Entity misc ---
    (r"^Entity_",                                   "ui_prompt",                  "Entity/World UI"),
]

def classify(key):
    for pattern, prompt, group in RULES:
        if re.search(pattern, key, re.IGNORECASE):
            return prompt, group
    return "story_dialogue_prompt", "Uncategorized (fallback: dialogue)"

# -------------------------------------------------------
# LOAD + PHAN LOAI
# -------------------------------------------------------
with open(IN_FILE, encoding="utf-8") as f:
    data = json.load(f)

result = {}   # prompt -> list of entries
stats  = {}   # prompt -> count

def add(prompt, group, entry):
    key = f"{prompt}|{group}"
    if key not in result:
        result[key] = {"prompt": prompt, "group": group, "strings": []}
    result[key]["strings"].append(entry)
    stats[prompt] = stats.get(prompt, 0) + 1

# New strings
for kid, val in data["new_strings"].items():
    prompt, group = classify(kid)
    add(prompt, group, {
        "id": kid,
        "type": "NEW",
        "english": val["english"],
        "vietnamese": ""
    })

# Changed strings
for kid, val in data["changed_strings"].items():
    prompt, group = classify(kid)
    add(prompt, group, {
        "id": kid,
        "type": "CHANGED",
        "old_english": val["old_english"],
        "new_english": val["new_english"],
        "vietnamese": ""
    })

# Sort by prompt, then group
output_list = sorted(result.values(), key=lambda x: (x["prompt"], x["group"]))

output = {
    "summary": {
        "total_strings": sum(stats.values()),
        "by_prompt": dict(sorted(stats.items(), key=lambda x: -x[1]))
    },
    "classified": output_list
}

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nDa phan loai xong! -> {OUT_FILE}")
print(f"\n=== THONG KE THEO PROMPT ===")
for prompt, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"  {prompt:<35} : {count:>5} strings")
print(f"\n  TONG: {sum(stats.values())} strings")
