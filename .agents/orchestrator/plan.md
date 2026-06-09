# Project Plan: UI Translation File Auditing and Correction

## Architecture & Data Flow
- **Source UI Translation Files**: Under `mistral_translate_work/split_by_prompt/json/ui/**/*.json`
- **Glossary & Rules**: Defined in `mistral_translate_work/prompts/shared_glossary.md` and `ORIGINAL_REQUEST.md`
- **Excel Output**: `mistral_translate_work/split_by_prompt/ui_translation_pack/ui_all.xlsx`
- **Data Flow**:
  1. Audit: Scan JSON files -> Detect mismatches/violations.
  2. Correct: Modify JSON files with proper Vietnamese translations.
  3. Consolidate: Regenerate `ui_all.xlsx` based on updated JSON files.
  4. Verify: Re-audit corrected JSON and Excel to ensure 100% compliance.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | Audit & Detection | Scan split JSON files for proper nouns, tag mismatches, untranslated verbs, isolated "Weapon(s)". | None | DONE |
| 2 | Correction | Apply corrections to the split JSON files. | Milestone 1 | DONE |
| 3 | Excel Regeneration | Regenerate the consolidated Excel file `ui_all.xlsx`. | Milestone 2 | DONE |
| 4 | Verification | Run validation to ensure no violations remain and Excel matches JSON. | Milestone 3 | DONE |

## Interface & Tool Contracts
- Audit results should be logged to a structured report (e.g. `audit_report.json` or `.agents/orchestrator/audit_issues.json`).
- Python scripts (e.g. `apply_corrections.py` or similar helper scripts) should be leveraged.
- Excel generation must use reliable pandas/openpyxl routines.
