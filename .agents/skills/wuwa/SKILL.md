---
name: wuwa
description: >
  Coordinating translation and localization pipeline for Wuthering Waves Vietnamese translation.
  Automatically applies keeping rules, pronoun maps, character matrices, audits, and builds.
  Includes a workflow step to automatically scan and update untranslated keywords (monsters, weapons, resonators) on new version releases.
---

# Wuthering Waves Vietnamese Translator Skill

When this skill is active, the agent automates the localization workflow for translating game files and compiling databases according to the custom Vietnamese prompt rules.

---

## 1. Master Rules & References (Always Read Before Operations)
Always refer to the following core prompt files under `mistral_translate_work/prompts/`:
- **`character_voice_map.md`**: Playable Resonator personalities, tones, xưng hô, and mature female character dynamics (strictly use `tôi` - `{Male=cậu;Female=em}`, avoid "Chị + Name").
- **`story_dialogue_prompt.md`**: Core dialogue formatting, gender-neutral guidelines for Rover, and generic NPC styles.
- **`keep_english_rules.md`**: Master lists of monsters, weapons, zones, and terms that must remain in English (except for the 4 condition exceptions).
- **`shared_glossary.md`**: Master terminology list and exact Vietnamese translations for UI/system components.

---

## 2. Category-Specific Prompts (Read Based on File Type Being Translated)
Depending on the type of game content being translated/processed, the agent must load the corresponding prompt from `mistral_translate_work/prompts/`:

| Prompt File | Target Content Category | Key Instructions / Nuances |
| :--- | :--- | :--- |
| **`name_title_prompt.md`** | Character Names, Weapon Names, & short titles | Keep weapon/character names in English. Translate short titles naturally. |
| **`ui_prompt.md`** | UI buttons, menus, screens, layouts | Keep translations compact, avoid wordiness, preserve variables. |
| **`system_text_prompt.md`** | Error codes, system notices, prompts | Match system status tone, keep technical terms intact. |
| **`quest_prompt.md`** | Quest names, objectives, descriptions | Keep objectives action-oriented and clear. |
| **`lore_prompt.md`** | Book records, historical archives | Use a narrative, slightly formal, fantasy style. |
| **`item_prompt.md`** | Consumables, materials, descriptions | Use accurate names, match effects to game stats. |
| **`weapon_prompt.md`** | Weapon passive effects, stats | Strictly format values, keep stat terms matching glossary. |
| **`skill_description_prompt.md`** | Resonator skill descriptions | Match skill types (Basic Attack, Forte Circuit, etc.) to the glossary. |
| **`phantom_skill_prompt.md`** | Echo/Phantom skill descriptions | Keep Echo actions clear, match stat formats. |
| **`rc_description_prompt.md`** | Resonance Chain (constellations) | Maintain precise activation conditions and stat gains. |
| **`echo_set_prompt.md`** | Sonata set effects and names | Keep Sonata names in English, translate description effects. |
| **`monster_description_prompt.md`** | Monster profiles and archive info | Match database tone, keep monster names in English. |
| **`file_classification.md`** | File organization and mapping rules | Defines how files are categorized and routed in the pipeline. |

---

## 3. Action Workflows
The agent should execute these tasks step-by-step using `run_command` in the project root:

### A. Auto-Update Keywords (Run First on New Version Releases)
Scan split JSON files, identify newly added weapons, monsters, and resonators, and automatically update `keep_english_rules.md` and `shared_glossary.md` lists:
```powershell
python tools/update_keep_rules.py
```
*(After this completes, the agent must read the modified rule files to refresh its system context before starting translation)*

### B. Web-Search Keyword Updates (Scan the Web for New Versions)
When the user asks to update keywords from the web (e.g., "cập nhật thông tin vũ khí mới từ mạng" or "/browser cập nhật vũ khí mới"), the agent MUST:
1. Use the `search_web` tool to search for new resonators, weapons, or bosses introduced in the target version of Wuthering Waves (e.g. search "Wuthering Waves new weapons 1.4", "Wuthering Waves new resonators 1.4", etc.).
2. Extract the clean English names.
3. Execute the python helper script `tools/add_web_keywords.py` using `run_command` to safely merge and sort these names in `keep_english_rules.md` and `shared_glossary.md`.
   Example command:
   ```powershell
   python tools/add_web_keywords.py --weapons "WeaponName A, WeaponName B" --resonators "Resonator A" --monsters "Monster A"
   ```

### C. Translate New Content
To run a translation batch with parallel Mistral API keys:
```powershell
python mistral_game_translate.py translate --max-keys 5 --batch-size 12 --max-chars 3600
```
*(Optionally append `--limit <number>` for smaller test batches)*

### D. Audit and Review Quality
To run the automated rule-based audit and verify tags/glossary consistency:
```powershell
python mistral_game_translate.py audit
```
To run AI-assisted review for complex dialogue/lore strings:
```powershell
python mistral_game_translate.py review-ai --limit 500
```

### E. Sync Split JSON Files (For split prompts workflow)
If edits are made directly to split JSON files in `split_by_prompt/json/`, sync them back to the temporary work databases:
```powershell
python tools/sync_split_json_to_db.py
```

### F. Compile and Import into Target Database
Compile the translated cache files and write them to the SQLite databases under `work_db_vi_mistral/`:
```powershell
python mistral_game_translate.py import --out-db-dir work_db_vi_mistral --force
```

### G. Verify & Check Output Status
Run verification scripts to ensure database integrity and alignment:
```powershell
python verify_changes.py
```
