## 2026-06-04T10:41:25Z
You are teamwork_preview_worker.
Your working directory is: C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\worker_m2
Your task is to implement and execute the correction script for the UI translation files under `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\` to resolve all 182 violations listed in `C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\explorer_m1\violations_report.json`.

**Inputs**:
1. Glossary file: `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\shared_glossary.md`
2. Keep-English rules: `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\keep_english_rules.md`
3. Violations report: `C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\explorer_m1\violations_report.json`
4. Split JSON files directory: `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\`

**Objective**:
1. Analyze the 182 violations in `violations_report.json`.
2. Write a Python correction script (e.g. `correct_ui.py` at the project root or in your working directory) that loads the split JSON files, applies corrections based on the glossary/rules, and saves the modified JSON files.
For each violation in the report:
   - For **Glossary Translation Violation** and **Blacklisted Translation**: Ensure proper nouns (e.g. `Dim Forest`, `Tacet Discord`, `Scar`, `ATK`, `Whining Aix's Mire`, `Sentinel`, `Sonoro Sphere`, `Black Alley`, `Emerald of Genesis`, `Impermanence Heron`, `Rover`, `Resonator`, `Resonance Skill`, `Resonance Liberation`, `Forte Circuit`, `Basic Attack`, `Heavy Attack`, `Cooldown`) are preserved in English in the translation. The script can perform precise string replacement to revert Vietnamese translations of these proper nouns back to their English forms.
   - For **Keep English Key Rule Violation**: Ensure the translation matches the English source exactly (`translation_vi = source_en`).
   - For **Newline Mismatch**: Fix the translations so they have the correct newlines (`\n`) and no content is truncated.
   - For **Placeholder Mismatch**: Fix the placeholder tags (like `{0}`, `{1}`, `{Cus:Ipt}`) in the translation to match the source.
   - For **Untranslated Action Verb**: Translate verbs like `Return` -> `Trở về`, `Exchange` -> `Trao đổi` / `Đổi`, `Increase` -> `Tăng`, `Decrease` -> `Giảm`, `Claim` -> `Nhận` in the translation.
   - For **Untranslated Weapon Word**: Translate isolated `Weapon` -> `Vũ khí` or `Weapon Level` -> `Cấp Vũ Khí`.
3. Apply these corrections. After running the script, run the explorer's audit script `C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\explorer_m1\audit.py` to verify that all 182 violations have been successfully fixed and the new violations report contains 0 violations.
4. Regenerate the consolidated Excel file `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\ui_all.xlsx` containing the updated translations. Follow the same aggregation and column sorting logic as in `apply_manual_corrections.py` to ensure it is structured and formatted correctly.
5. Verify that `ui_all.xlsx` is successfully regenerated and matches the updated JSON files exactly.

**MANDATORY INTEGRITY WARNING**:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

**Output Requirements**:
Document the corrections applied, the script design, execution logs, and the validation results (running `audit.py` showing 0 violations) in `C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\worker_m2\handoff.md`. Communicate your completion back via message.
