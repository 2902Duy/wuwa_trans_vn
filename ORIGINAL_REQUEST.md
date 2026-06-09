# Original User Request

## Initial Request — 2026-06-04T03:20:10Z

Audit the UI translation files in the workspace using the newly updated glossaries and rules to detect any mismatches, incorrect translations, or formatting violations, and apply necessary corrections.

Working directory: C:/Users/tduy2/Documents/antigravity/silly-darwin
Integrity mode: development

## Requirements

### R1. Translation Audit and Detection
Scan all translation files under `mistral_translate_work/split_by_prompt/json/ui/` and check for:
- Violations of proper noun preservation (e.g. `Jinzhou` translated as `Kim Châu`, `Mt. Firmament` as `Núi Vòm Trời`, `Sentinel` as `lính canh`, etc. as defined in `shared_glossary.md`).
- Placeholder tag mismatches (`{0}`, `{1}`, `{Cus:Ipt}`) or corrupted tags.
- Action verbs left untranslated (`Increase`, `Decrease`, `Claim`, `Exchange`, `Return`).
- Isolated instances of `Weapon` or `Weapons` that should be localized to `Vũ khí` / `vũ khí`.

### R2. Automatic Correction and Excel Regeneration
For all detected errors:
- Correct the split JSON files directly with proper Vietnamese translations.
- Regenerate the consolidated Excel file `mistral_translate_work/split_by_prompt/ui_translation_pack/ui_all.xlsx`.

## Acceptance Criteria

### Verification of Corrections
- [ ] No proper noun violations remain in the modified UI translation files.
- [ ] Tag integrity is 100% restored for all modified records.
- [ ] The consolidated `ui_all.xlsx` is successfully regenerated and matches the corrected JSON records.

## Follow-up — 2026-06-04T03:21:02Z

Hi team, the user explicitly requests that you inspect the newly updated prompts and glossary files before starting the audit/corrections on 'mistral_translate_work/split_by_prompt/json/ui/'.
Please make sure to read and check:
1. 'mistral_translate_work/prompts/shared_glossary.md' and 'mistral_translate_work/prompts/keep_english_rules.md'
2. 'mistral_translate_work/split_by_prompt/ui_translation_pack/shared_glossary.md' and 'mistral_translate_work/split_by_prompt/ui_translation_pack/keep_english_rules.md'
Ensure these rules are fully respected and analyzed.

## Follow-up — 2026-06-04T03:33:48Z

Audit the UI translation files in the workspace using the newly updated glossaries and rules to detect any mismatches, incorrect translations, or formatting violations, and apply necessary corrections.

Working directory: C:/Users/tduy2/Documents/antigravity/silly-darwin
Integrity mode: development

## Requirements

### R0. Pre-requisite Prompt Analysis
Before auditing, inspect and analyze the newly updated prompts and glossary files in the workspace:
- `mistral_translate_work/prompts/shared_glossary.md` and `mistral_translate_work/prompts/keep_english_rules.md`
- `mistral_translate_work/split_by_prompt/ui_translation_pack/shared_glossary.md` and `mistral_translate_work/split_by_prompt/ui_translation_pack/keep_english_rules.md`
Use the exact proper nouns list (Resonators, Locations, Echoes, Weapons) and rules defined in these files as the absolute reference.

### R1. Translation Audit and Detection
Scan all translation files under `mistral_translate_work/split_by_prompt/json/ui/` and check for:
- Violations of proper noun preservation (e.g. `Jinzhou` translated as `Kim Châu`, `Mt. Firmament` as `Núi Vòm Trời`, `Sentinel` as `lính canh`, etc. as defined in `shared_glossary.md`).
- Placeholder tag mismatches (`{0}`, `{1}`, `{Cus:Ipt}`) or corrupted tags.
- Action verbs left untranslated (`Increase`, `Decrease`, `Claim`, `Exchange`, `Return`).
- Isolated instances of `Weapon` or `Weapons` that should be localized to `Vũ khí` / `vũ khí`.

### R2. Automatic Correction and Excel Regeneration
For all detected errors:
- Correct the split JSON files directly with proper Vietnamese translations.
- Regenerate the consolidated Excel file `mistral_translate_work/split_by_prompt/ui_translation_pack/ui_all.xlsx`.

## Acceptance Criteria

### Verification of Corrections
- [ ] No proper noun violations remain in the modified UI translation files.
- [ ] Tag integrity is 100% restored for all modified records.
- [ ] The consolidated `ui_all.xlsx` is successfully regenerated and matches the corrected JSON records.

