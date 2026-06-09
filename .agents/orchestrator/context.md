# Context - UI Translation File Auditing and Correction

## original request
Original request text is documented in `C:\Users\tduy2\Documents\antigravity\silly-darwin\ORIGINAL_REQUEST.md`.

## Key Requirements
- Check for proper noun violations in `shared_glossary.md` (e.g. `Jinzhou`, `Mt. Firmament`, `Sentinel`).
- Tag mismatches (`{0}`, `{1}`, `{Cus:Ipt}`, etc.).
- Action verbs untranslated (`Increase`, `Decrease`, `Claim`, `Exchange`, `Return`).
- Isolated instances of `Weapon` / `Weapons` -> `Vũ khí` / `vũ khí`.
- Apply JSON corrections in `mistral_translate_work/split_by_prompt/json/ui/`.
- Regenerate Excel at `mistral_translate_work/split_by_prompt/ui_translation_pack/ui_all.xlsx`.
