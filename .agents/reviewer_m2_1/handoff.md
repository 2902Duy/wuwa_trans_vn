# Review & Challenge Report — UI Translation Corrections

## 1. Observation

During our inspection of the UI translation correction files and the script `correct_ui.py`, we observed several key data entries and code sections:

### 1.1 Replacement Ordering Defect in `correct_ui.py`
In `correct_ui.py` (lines 174–220), the `proper_nouns_replacements` list contains the following items:
```python
198:                     ("Sẹo", "Scar"), ("Vết Sẹo", "Scar"),
```
Because the shorter target string `"Sẹo"` is placed before the longer target string `"Vết Sẹo"`, the script executes the `"Sẹo"` replacement first, which leaves no match for `"Vết Sẹo"`.
In `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_multi_text\lang_multi_text__ui__part_0013.json` line 4649, we observed:
```json
"split_id": "UI_0007276",
"source_en": "Scar II",
"new_translation_vi": "Vết Scar II"
```
The original Vietnamese translation was `"Vết Sẹo II"`. Due to the ordering bug, it became `"Vết Scar II"`.

### 1.2 Untranslated standard verbs and adjectives
We observed several standard English words that are completely untranslated or translated into hybrid Vietnamese-English phrasing:
- **Verb `"Place"`**: In `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_multi_text\lang_multi_text__ui__part_0021.json` (lines 497–499, Split IDs `UI_0011110`, `UI_0011111`, `UI_0011112`):
  ```json
  "source_en": "Place the Electro Predator here. The Echoes on the right-hand side appear in the Backline.",
  "new_translation_vi": "Place Electro Predator vào đây. Các Echoes ở bên phải sẽ xuất hiện ở Hàng Sau."
  ```
  The verb `"Place"` is left untranslated.
- **Adjective `"Special"`**: In `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_multi_text\lang_multi_text__ui__part_0010.json` (lines 372–374, Split ID `UI_0005605`):
  ```json
  "source_en": "Special Supplies",
  "new_translation_vi": "Hàng Cung Ứng Special"
  ```
- **Adjective/Noun hybrid `"Details Exam"`**: In `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_multi_text\lang_multi_text__ui__part_0010.json` (lines 572–574, Split ID `UI_0005613`):
  ```json
  "source_en": "Exam Details",
  "new_translation_vi": "Details Exam"
  ```
- **Noun `"Attack"`**: In `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_multi_text\lang_multi_text__ui__part_0013.json` (lines 372–374, Split ID `UI_0007105`):
  ```json
  "source_en": "Coordinated Attack",
  "new_translation_vi": "... Attack Phối Hợp ..."
  ```
- **Noun `"Night"`**: In `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_multi_text\lang_multi_text__ui__part_0013.json` (line 12349, Split ID `UI_0007584`):
  ```json
  "source_en": "...Queen of the Night...",
  "new_translation_vi": "...Nữ hoàng Night tối..."
  ```

### 1.3 NPC Proper Name Mistranslation
In `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_map_mark\lang_map_mark__ui__part_0001.json` (lines 497–499, Split ID `UI_0000672`):
```json
"source_en": "Ma He's Grocers",
"new_translation_vi": "Ma Anh ấy's Grocers"
```
The proper name `"Ma He"` was translated to `"Ma Anh ấy"`, mistaking `"He"` for the male gender pronoun.

---

## 2. Logic Chain

1. **Ordering logic**: Sequential `str.replace` execution replaces substrings as they are found. If a short string (`"Sẹo"`) is a substring of a longer string (`"Vết Sẹo"`), and the short string is replaced first, it converts the longer string into a hybrid term (`"Vết Scar"`), causing the second replacement rule to fail.
2. **Translation quality**: Standard verbs and adjectives like `"Place"`, `"Special"`, and `"Details"` do not fall under the "Keep English" mandatory glossary (such as Resonator/Boss names). Translating them in hybrid formats (e.g. `"Place... vào đây"`, `"Hàng Cung Ứng Special"`) violates standard UI Vietnamese translation guidelines.
3. **NPC parsing errors**: Simple tokenizers/LLMs translate sentences word-by-word. When encountering an NPC name like `"Ma He"`, the name `"He"` was parsed as the English pronoun `"he"`, leading to the ridiculous literal translation `"Ma Anh ấy"`.
4. **Audit limitations**: The audit script `audit.py` only performs presence checks (`if noun in translation_vi`). Since `"Scar"` is present in `"Vết Scar II"`, it did not trigger any violation, leading to false-positives of "0 violations remaining".

---

## 3. Caveats

- We assumed that `audit.py` is the only automated validator being run. If there are other validators in the main build pipeline, they might check for spelling or language detection, but `audit.py` is the primary one mentioned.
- We did not manually read all 54 split JSON files line-by-line, but targeted specific files based on the reported fix patterns in the code.

---

## 4. Conclusion & Verdict

**Verdict**: **REQUEST_CHANGES**

We cannot approve the current translation corrections because they contain significant logic bugs in the correction script, as well as multiple major translation quality and correctness violations.

### 4.1 Findings

#### [Major] Finding 1: Shorter-Before-Longer Replacement Bug
- **Location**: `correct_ui.py` (lines 198) and `lang_multi_text__ui__part_0013.json` (Split ID: `UI_0007276`).
- **Why**: Replaces `"Sẹo"` first, leaving `"Vết Scar"` which fails to match `"Vết Sẹo"`.
- **Suggestion**: In `correct_ui.py`, sort the `proper_nouns_replacements` list by length of the target string in descending order before executing replacements:
  ```python
  proper_nouns_replacements.sort(key=lambda x: len(x[0]), reverse=True)
  ```

#### [Major] Finding 2: Hybrid and Untranslated Standard Vocabulary
- **Location**: Various JSON files (`UI_0011110`, `UI_0005605`, `UI_0005613`, `UI_0007105`, `UI_0007584`).
- **Why**: Words like `"Place"`, `"Special"`, `"Details"`, and `"Attack"` are left untranslated or translated in hybrid phrasing, breaking standard translation conventions.
- **Suggestion**: Standardize these terms into proper Vietnamese:
  - `"Place... here"` -> `"Đặt... vào đây"`
  - `"Special Supplies"` -> `"Vật Tư Đặc Biệt"`
  - `"Exam Details"` -> `"Chi Tiết Kỳ Thi"`
  - `"Coordinated Attack"` -> `"Tấn Công Phối Hợp"`
  - `"Queen of the Night"` -> `"Nữ hoàng Bóng Đêm"`

#### [Major] Finding 3: NPC Proper Name Mistranslation
- **Location**: `lang_map_mark__ui__part_0001.json` (Split ID: `UI_0000672`).
- **Why**: NPC name `"Ma He"` was translated to `"Ma Anh ấy"`.
- **Suggestion**: Restore to `"Cửa Hàng Ma He"` or `"Ma He's Grocers"`.

---

## 5. Verification Method

To independently verify:
1. Open `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_multi_text\lang_multi_text__ui__part_0013.json` and inspect line 4649 to see if the translation is `"Vết Scar II"`.
2. Open `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_map_mark\lang_map_mark__ui__part_0001.json` and inspect line 499 to check if `"Ma Anh ấy's Grocers"` exists.
3. Open `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_multi_text\lang_multi_text__ui__part_0021.json` and inspect lines 497-501 to check if `"Place Electro Predator vào đây"` exists.
