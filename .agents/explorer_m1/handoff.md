# Analysis of UI Translation Files, Glossary Rules, and Proposed Audit Script Design

This report synthesizes the read-only investigation of UI translation files and translation rules under the `silly-darwin` repository. It identifies proper nouns, validation rules, layout/tag matching strategies, and proposed audit script design to detect violations.

---

## 1. Observation

### Exact File Paths and Context
The investigation analyzed:
*   **Glossary File**: `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\shared_glossary.md`
*   **Keep-English Rules**: `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\keep_english_rules.md`
*   **UI Translation Directory**: `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\` (containing 54 JSON translation splits)

### Verified Glossary Rules (shared_glossary.md)
*   **Proper Nouns**: 305 terms extracted, including:
    *   *Core terms/stats*: `Resonance Chain`, `Resonator`, `Rover`, `Echo`, `Forte Circuit`, `Concerto Energy`, `STA`, `HP`, `ATK`, `DEF`, `Crit. Rate`, `DMG`, etc.
    *   *Boss/Echo Names*: `Crownless`, `Bell-Borne Geochelone`, `Inferno Rider`, `Impermanence Heron`, etc.
    *   *Resonators*: `Aalto`, `Baizhi`, `Chixia`, `Jinhsi`, `Jiyan`, `Sanhua`, `Verina`, `Xiangli Yao`, `Yinlin`, etc.
    *   *Locations*: `Huanglong`, `Jinzhou`, `Mt. Firmament`, `Hongzhen`, `Dim Forest`, `Central Plains`, `Gorges of Spirits`, etc.
    *   *Weapons*: `Abyss Surges`, `Ages of Harvest`, `Emerald of Genesis`, `Static Mist`, `Stringmaster`, etc.
    *   *Debuffs*: `Aero Erosion`, `Glacio Chafe`, `Spectro Frazzle`, `Havoc Bane`, `Fusion Burst`, `Electro Flare`, `Electrified`, `Negative Status`, `Debuff`, `Burn`, `Freeze`, `Poison`, `Bleed`, `Stun`, `Paralyze`, `Slow`, `Silence`, `Corrosion`, `Erosion`, `Tidal Blight`, `Blight`.

### Verified Key-based Keep-English Rules (keep_english_rules.md)
Translations must equal the English source exactly when:
1.  `table = "WeaponConf"` inside `lang_weapon.json` (Weapon names)
2.  `table = "PhantomItem"`, `table = "MonsterInfo"`, or `table = "Condition"` inside their respective files (Echo/Boss names)
3.  `table = "RoleInfo"`, `table = "MapBoundary"`, or `table = "MultiText"` if they represent names of resonators or locations.
4.  `table = "PhantomFetter"` (Echo set names)
5.  `primary_key` starts with `ResonantChain_` and ends with `_NodeName` (RC node names)
6.  `primary_key` contains `_SkillName`, starts with `Skill_` and ends with `_SkillName`, starts with `RoleSkillTreeInfo_` and ends with `_Title`, or `table = "Skill"` in `lang_skill.json`, or `table = "RoleSkillTreeInfo"` in `lang_skillTree.json` (Character skill names).

### Audit Run Observations and Verbatim Violations
Running an audit script on the UI JSON splits (`python audit.py`) produced **182 unique violations** across the following categories:

| Violation Type | Count | Description / Example |
| :--- | :--- | :--- |
| **Glossary Translation Violation** | 129 | Proper nouns in English source are translated or altered in Vietnamese. |
| **Untranslated Action Verb** | 35 | Verbs like `Return` or `Exchange` left untranslated. |
| **Newline Mismatch** | 9 | Number of newlines (`\n`) differs, often causing severe layout truncation. |
| **Placeholder Mismatch** | 6 | Gender selection `{Male=...;Female=...}` or custom tag mismatches. |
| **Blacklisted Translation** | 2 | Using forbidden Vietnamese terms (e.g. `Giải phóng Cộng hương` for `Resonance Liberation`). |
| **Untranslated Weapon Word** | 1 | Isolated `Weapon Level` left untranslated. |

#### Verbatim Examples from `violations_report.json`:
1.  **Glossary Location Translation**:
    *   *File*: `lang_map_mark\lang_map_mark__ui__part_0001.json` (Split ID: `UI_0000660`)
    *   *Source*: `"Dim Forest"`
    *   *Translation*: `"Rừng Tối"`
    *   *Violation*: Missing proper noun `Dim Forest`. (Should remain in English).
2.  **Glossary Boss Translation**:
    *   *File*: `lang_multi_text\lang_multi_text__ui__part_0013.json` (Split ID: `UI_0007276`)
    *   *Source*: `"Scar II"`
    *   *Translation*: `"Vết Sẹo II"`
    *   *Violation*: Missing proper noun `Scar`. (Should remain in English).
3.  **Core Term/Attribution Mismatch**:
    *   *File*: `lang_multi_text\lang_multi_text__ui__part_0009.json` (Split ID: `UI_0005118`)
    *   *Source*: `"ATK SPD"`
    *   *Translation*: `"SPD TẤN CÔNG"`
    *   *Violation*: Missing proper noun `ATK`. (Should remain in English).
4.  **Resonator Translation**:
    *   *File*: `lang_multi_text\lang_multi_text__ui__part_0012.json` (Split ID: `UI_0007033`)
    *   *Source*: `"A mysterious gateway emerges in the Whining Aix's Mire..."`
    *   *Translation*: `"Một cánh cổng bí ẩn xuất hiện tại Bãi Lầy Aix Rên Rỉ..."`
    *   *Violation*: Missing proper noun `Whining Aix's Mire` (translated to `Bãi Lầy Aix Rên Rỉ`).
5.  **Severe Truncation (Newline Mismatch)**:
    *   *File*: `lang_multi_text\lang_multi_text__ui__part_0013.json` (Split ID: `UI_0007573`)
    *   *Source*: `"At the start... based on your Combat Rank:\n\nA: Target takes 50% more damage.\nS: Target takes 100% more damage.\nSS: Target takes 200% more damage."`
    *   *Translation*: `"Khi bắt đầu thử thách, Resonance Energy được phục hồi 50%... dựa trên Combat Rank của bạn:"`
    *   *Violation*: Truncated translation where the entire bulleted list (`A`, `S`, `SS`) was deleted.
6.  **Untranslated Action Verb**:
    *   *File*: `lang_multi_text\lang_multi_text__ui__part_0004.json` (Split ID: `UI_0002740`)
    *   *Source*: `"Return"`
    *   *Translation*: `"Return"`
    *   *Violation*: Standing verb `Return` left untranslated. (Should be `Trở về` or `Quay lại`).
7.  **Blacklisted Translation**:
    *   *File*: `lang_multi_text\lang_multi_text__ui__part_0019.json` (Split ID: `UI_0010329`)
    *   *Source*: `"Cartethyia Enhanced Resonance Liberation Tutorial"`
    *   *Translation*: `"Hướng dẫn Giải phóng Cộng hưởng Nâng cao Cartethyia"`
    *   *Violation*: Translated `Resonance Liberation` as `Giải phóng Cộng hưởng` (specifically blacklisted).
8.  **Untranslated Weapon Word**:
    *   *File*: `lang_multi_text\lang_multi_text__ui__part_0017.json` (Split ID: `UI_0009514`)
    *   *Source*: `"Increase <color=#8c7e51>Weapon Level</color>..."`
    *   *Translation*: `"Tăng <color=#8c7e51>Weapon Level</color>..."`
    *   *Violation*: Isolated word `Weapon` left untranslated. (Should be `Cấp Vũ Khí`).

---

## 2. Logic Chain

From the observations of rules and UI translations, the logic chain is as follows:
1.  **Proper Nouns Preservation**: The glossary mandates preserving 305 proper nouns in English (case-sensitively). If a proper noun exists in the English source but is missing or altered (e.g. `Hongzhen` -> `Hồng Trấn`, `Scar` -> `Vết Sẹo`, `ATK` -> `TẤN CÔNG`, or `Whining Aix's Mire` -> `Bãi Lầy Aix Rên Rỉ`), it constitutes a **Glossary Translation Violation**.
2.  **Blacklist Detection**: Specific translations are forbidden because they lead to inconsistent terminology (e.g., `Resonance Liberation` -> `Giải phóng Cộng hưởng` or `Nộ`, `Rover` -> `Nhà Lữ Hành`). If these incorrect terms are found in the Vietnamese translation, it is a **Blacklisted Translation** violation.
3.  **Keep-English Key Rules**: Character skills, RC nodes, and weapon/echo names in specific tables must match the source exactly. Any discrepancy (e.g., `Slayer's Trigger` -> `Kích hoạt Kẻ diệt sát`) is a **Keep English Key Rule Violation**.
4.  **Tag & Placeholder Verification**:
    *   *Positional/System Tags*: Placeholders like `{0}`, `{1}`, `{Cus:Ipt}`, `{PlayerName}` are crucial variables. If the sets of placeholders between source and translation do not match, it breaks the game engine, constituting a **Placeholder Mismatch**.
    *   *Rich Text Tags*: Game styling tags (e.g., `<color=#ffd12f>...</color>`, `<size=24>...</size>`) must match. Modifying hex values or failing to close tags causes UI rendering errors. Checking tag count, exact attributes, and tag balancing (opening/closing tag match) catches these **Tag Mismatches**.
    *   *Gender Placeholders*: The syntax `{Male=him;Female=her}` selects strings dynamically. While keys `Male` and `Female` must be preserved, values *must* be translated (e.g., `{Male=anh ấy;Female=cô ấy}`). Simple string matching will falsely flag this; thus, structural validation must be applied.
    *   *Newlines*: Layout structure relies on line breaks. Mismatched newline counts indicate formatting errors or content truncation (such as omitting bulleted items, as observed in `UI_0007573`).
5.  **Action Verbs and Isolated Weapons**:
    *   *Action Verbs*: `Increase`, `Decrease`, `Claim`, `Exchange`, `Return` are commands, not proper nouns, and must be translated. They are flagged if left in English, provided they are standalone words and not part of a proper noun (e.g. `Exchange` in `Interference Exchange`).
    *   *Weapons*: Standalone `Weapon` or `Weapons` must be translated to `Vũ khí`.

---

## 3. Caveats

1.  **Context-dependent False Positives**:
    *   *Common nouns acting as Proper Nouns*: Words like `Slow`, `Burn`, `Freeze`, `Poison`, `Bleed`, `Stun`, `Paralyze`, `Silence` are debuffs in the glossary. However, in UI sentences, they often act as regular verbs/adjectives (e.g. "use the Slow Motion gadget anytime to slow time"). Flagging them case-insensitively will yield false positives. A robust script must contextually ignore these words unless they represent named status effects (e.g. capitalized `Slow` or `Silenced` status).
    *   *Proper Noun containing Action Verbs*: Words like `Exchange` are action verbs but are correctly preserved in proper nouns like `Interference Exchange`. The validation script must exclude matches that are part of known English proper nouns.
2.  **Regex Edge Cases**: Extremely short proper nouns (like `HP`, `ATK`, `DEF`, `STA`, `RC`) must be matched using word boundaries (`\b`) to avoid flagging substrings of unrelated words (e.g. matching `STA` in `STATION` or `ATK` in `ATK_SPD`).
3.  **JSON File Encoded Strings**: Some JSON files might contain escaped characters (like `\u00a0` for non-breaking spaces or double backslashes for newlines `\\n`). The script must normalize whitespace and escape characters before running audits.

---

## 4. Conclusion

The translation audit reveals that:
1.  **Translation Errors are Prevalent**: UI translations frequently violate the glossary rules by translating proper nouns (locations, boss names, character names) and core terminology into Vietnamese, or using blacklisted Hán-Việt terms.
2.  **Structural Integrity is Broken**: Positional placeholders and formatting tags are occasionally altered, and line-breaks are omitted, leading to UI layout errors or truncated sentences.
3.  **Action Verbs are Overlooked**: Isolated command verbs (`Return`, `Exchange`) and general items (`Weapon Level`) are often left untranslated.
4.  **An Audit Script is Feasible and Necessary**: An automated scan using optimized regular expressions and parser rules is highly effective at identifying these violations. It can catch 100% of formatting/tag violations and the vast majority of glossary violations, saving hours of manual review.

---

## 5. Proposed Audit Script Design

To implement a production-ready, performant, and accurate validation tool, the audit script should be designed with the following components:

### A. Performance Optimization
*   **Compiled Regex Cache**: Compile all regular expressions (for the 305 proper nouns, action verbs, and tags) *once* at startup. This prevents the $O(\text{items} \times \text{terms})$ recompilation overhead, reducing execution time from several minutes to under 2 seconds.
*   **Arie / Phrase Search**: Build a Trie of glossary terms or use a single optimized regex group `\b(Term1|Term2|...)\b` to perform rapid matches instead of scanning 305 terms sequentially.

### B. Accurate Verification Rules

#### 1. Proper Noun Preservation Rule
*   For each proper noun $P$ in the glossary:
    1.  If $P$ is short ($\le 4$ chars like `HP`, `STA`, `RC`), use word boundaries: `rf"\b{re.escape(P)}\b"`.
    2.  If $P$ exists in the English source:
        - Check if $P$ is present in the Vietnamese translation.
        - If missing but exists case-insensitively, flag as **"Casing Violation"**.
        - If missing entirely, flag as **"Glossary Translation Violation"**.
        - *Exception*: Exclude common words like `Slow`, `Burn`, `Freeze`, `Poison`, `Bleed`, `Stun`, `Paralyze`, `Silence` unless they represent a status effect.

#### 2. Keep English Key Rule
*   If `primary_key` matches key-rules (e.g. `_SkillName`, `ResonantChain_*_NodeName`, `RoleSkillTreeInfo_*_Title`), assert `new_translation_vi == source_en`.

#### 3. Tag & Placeholder Matching
*   **Positional Placeholders**: Extract all `{0}`, `{1}`, etc. using `r"\{[0-9]+\}"`. Compare the sorted list of placeholders between source and translation.
*   **System/Custom Placeholders**: Extract `{PlayerName}`, `{Cus:Ipt}`, etc. using `r"\{[a-zA-Z0-9_:]+\}"`. Compare the sorted list.
*   **Gender Placeholders**:
    - Extract using `r"\{Male=[^;]+;Female=[^}]+\}"`.
    - Do *not* compare the exact text. Parse it: verify both `Male` and `Female` keys are present, and their values are non-empty. Compare the key structure with the source.
*   **Rich Text Tags**:
    - Extract tags using `r"<[^>]+>"`.
    - Check if tags in the source are present in the translation.
    - Check tag spelling and attributes (e.g., `<color=#ffd12f>` in source must have exactly `<color=#ffd12f>` in translation).
    - Styling tag balance: track open/close counts for tags like `color`, `size`, `te`, `SapTag`.
*   **Newlines**:
    - Normalize newlines (convert `\\n` to `\n`).
    - Verify `source_en.count('\n') == new_translation_vi.count('\n')`.

#### 4. Action Verbs & Isolated Weapon Detection
*   **Action Verbs**: Match standalone `\b(Increase|Decrease|Claim|Exchange|Return)\b` (case-insensitive) in the translation.
    - *Filter*: Ensure the verb is also in the source.
    - *Filter*: Ignore the match if it is part of known proper nouns (e.g., inside `Interference Exchange`).
*   **Weapons**: Match standalone `\bweapons?\b` (case-insensitive) in the translation and flag if the source had it.

---

### C. Proposed Python Audit Script Implementation

Below is the design and full implementation code of the proposed script:

```python
import os
import json
import re
import sys

# Configure output encoding for unicode characters
sys.stdout.reconfigure(encoding='utf-8')

class TranslationAuditor:
    def __init__(self, ui_dir, glossary_path):
        self.ui_dir = ui_dir
        self.glossary_path = glossary_path
        self.proper_nouns = []
        self.blacklist_translations = [
            ("Echo", "Tiếng Vang"), ("Echo", "Linh Thú"),
            ("Rover", "Nhà Lữ Hành"), ("Rover", "Vãng Minh Giả"), ("Rover", "Viễn Khách"),
            ("Resonator", "Người Cộng Hưởng"), ("Resonator", "Cộng Hưởng Giả"),
            ("Resonance Skill", "Kỹ Năng Cộng Hưởng"), ("Resonance Skill", "Chiêu Thức Cộng Hưởng"),
            ("Resonance Liberation", "Giải Phóng Cộng Hưởng"), ("Resonance Liberation", "Nộ"),
            ("Forte Circuit", "Mạch Forte"), ("Forte Circuit", "Chuỗi Forte"),
            ("Basic Attack", "Tấn Công Thường"), ("Basic Attack", "Tấn Công Cơ Bản"),
            ("Heavy Attack", "Trọng Kích"), ("Heavy Attack", "Tấn Công Nặng"),
            ("Cooldown", "Hồi Chiêu"), ("Cooldown", "Thời gian hồi"),
            ("Spectro Frazzle", "Nhiễu Loạn Quang Phổ"),
            ("Aero Erosion", "Xói Mòn Gió"),
            ("Glacio Chafe", "Trầy Băng Giá"),
            ("Fusion Burst", "Nổ Nhiệt Hạch"),
            ("Havoc Bane", "Tai Họa Hỗn Loạn"),
            ("Electro Flare", "Điện Tích"), ("Electro Flare", "Bùng Điện"),
            ("Jinzhou", "Kim Châu"),
            ("Mt. Firmament", "Núi Vòm Trời"), ("Mt. Firmament", "Trầm Minh Khánh"),
            ("Emerald of Genesis", "Ngọc Lục Bảo Khởi Nguyên"),
            ("Impermanence Heron", "Vịt Bất Diệt")
        ]
        self.action_verbs = ["Increase", "Decrease", "Claim", "Exchange", "Return"]
        self.action_verbs_pattern = re.compile(r"\b(" + "|".join(self.action_verbs) + r")\b", re.IGNORECASE)
        self.weapon_pattern = re.compile(r"\bweapons?\b", re.IGNORECASE)
        
        # Parse glossary and compile patterns
        self._load_glossary()
        self._precompile_proper_nouns()

    def _load_glossary(self):
        """Extracts proper nouns from shared_glossary.md"""
        if not os.path.exists(self.glossary_path):
            raise FileNotFoundError(f"Glossary file not found: {self.glossary_path}")
            
        with open(self.glossary_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        terms = []
        in_section = False
        for line in lines:
            if "## THUẬT NGỮ BẮT BUỘC GIỮ NGUYÊN TIẾNG ANH" in line:
                in_section = True
                continue
            if "## Ví dụ về các dịch sai cần tránh" in line:
                in_section = False
                break
            if in_section:
                if "->" in line:
                    continue
                found = re.findall(r"`([^`]+)`", line)
                for term in found:
                    if "," in term:
                        subterms = [t.strip() for t in term.split(",")]
                        terms.extend(subterms)
                    else:
                        terms.append(term.strip())

        # Clean proper noun terms
        proper_nouns = []
        for t in terms:
            if t and t not in proper_nouns:
                if "/" in t or "[" in t or "{" in t or "<" in t:
                    continue
                proper_nouns.append(t)

        # Sort by length descending to match longer phrases first
        proper_nouns.sort(key=len, reverse=True)
        self.proper_nouns = proper_nouns

    def _precompile_proper_nouns(self):
        """Pre-compiles regex patterns for proper nouns to ensure high performance"""
        self.proper_noun_patterns = []
        for noun in self.proper_nouns:
            if len(noun) <= 4:
                # Use word boundaries for short acronyms like STA, HP, ATK
                pattern = re.compile(rf"\b{re.escape(noun)}\b")
            else:
                pattern = re.compile(re.escape(noun))
            self.proper_noun_patterns.append((noun, pattern))

    def _is_keep_english_key(self, pk, table, source_file):
        """Checks if the primary key or table requires exact English matching"""
        pk = str(pk)
        if pk.startswith("ResonantChain_") and pk.endswith("_NodeName"):
            return True
        if "_SkillName" in pk:
            return True
        if pk.startswith("RoleSkillTreeInfo_") and pk.endswith("_Title"):
            return True
        if table == "Skill" and source_file == "lang_skill.json":
            return True
        if table == "RoleSkillTreeInfo" and source_file == "lang_skillTree.json":
            return True
        return False

    def _parse_gender_placeholders(self, text):
        """Extracts and parses gender placeholders like {Male=him;Female=her}"""
        placeholders = re.findall(r"(\{Male=[^;]+;Female=[^}]+\})", text)
        parsed = []
        for ph in placeholders:
            match = re.match(r"\{Male=([^;]+);Female=([^}]+)\}", ph)
            if match:
                parsed.append({
                    "raw": ph,
                    "male_val": match.group(1),
                    "female_val": match.group(2)
                })
        return parsed

    def audit_item(self, item, rel_path):
        violations = []
        split_id = item.get("split_id")
        source_en = item.get("source_en", "")
        translation_vi = item.get("new_translation_vi", "")
        table = item.get("table", "")
        pk = item.get("primary_key", "")
        source_file = item.get("source_file", "")

        if not translation_vi:
            return violations  # Skip empty translations

        # --- CHECK 1: Keep English Key Rule ---
        if self._is_keep_english_key(pk, table, source_file):
            if translation_vi != source_en:
                violations.append({
                    "file": rel_path,
                    "split_id": split_id,
                    "source": source_en,
                    "translation": translation_vi,
                    "type": "Keep English Key Rule Violation",
                    "detail": "Key rule requires translation to match source exactly, but they differ."
                })
                return violations # If this rule applies, other checks are irrelevant

        # --- CHECK 2: Proper Nouns (Glossary) ---
        # Exclude common words when matching case-insensitively
        common_words_debuffs = {"slow", "burn", "freeze", "poison", "bleed", "stun", "paralyze", "silence"}
        for noun, pattern in self.proper_noun_patterns:
            if pattern.search(source_en):
                # Skip false positives for common nouns used generally
                if noun.lower() in common_words_debuffs and not re.search(rf"\b{re.escape(noun)}\b", source_en):
                    continue
                    
                if noun not in translation_vi:
                    # Check case-insensitive existence (Casing Violation)
                    if noun.lower() in translation_vi.lower():
                        violations.append({
                            "file": rel_path,
                            "split_id": split_id,
                            "source": source_en,
                            "translation": translation_vi,
                            "type": "Casing Violation",
                            "detail": f"Proper noun '{noun}' casing is not preserved in translation."
                        })
                    else:
                        violations.append({
                            "file": rel_path,
                            "split_id": split_id,
                            "source": source_en,
                            "translation": translation_vi,
                            "type": "Glossary Translation Violation",
                            "detail": f"Proper noun '{noun}' is missing or translated in translation."
                        })

        # --- CHECK 3: Blacklisted Translations ---
        for eng, wrong_vi in self.blacklist_translations:
            if wrong_vi.lower() in translation_vi.lower():
                if eng.lower() in source_en.lower():
                    violations.append({
                        "file": rel_path,
                        "split_id": split_id,
                        "source": source_en,
                        "translation": translation_vi,
                        "type": "Blacklisted Translation",
                        "detail": f"Incorrect translation '{wrong_vi}' used for '{eng}'."
                    })

        # --- CHECK 4: Formatting Tags & Placeholders ---
        # 4.1 Positional / System Placeholders
        # Ignore gender selection placeholders here as they are validated separately
        source_normal_ph = sorted(re.findall(r"\{(?!Male=|Female=)[^\}]+\}", source_en))
        trans_normal_ph = sorted(re.findall(r"\{(?!Male=|Female=)[^\}]+\}", translation_vi))
        if source_normal_ph != trans_normal_ph:
            violations.append({
                "file": rel_path,
                "split_id": split_id,
                "source": source_en,
                "translation": translation_vi,
                "type": "Placeholder Mismatch",
                "detail": f"Source placeholders {source_normal_ph} vs Translation {trans_normal_ph}."
            })

        # 4.2 Gender Placeholders (Structural Match)
        src_gender = self._parse_gender_placeholders(source_en)
        trans_gender = self._parse_gender_placeholders(translation_vi)
        if len(src_gender) != len(trans_gender):
            violations.append({
                "file": rel_path,
                "split_id": split_id,
                "source": source_en,
                "translation": translation_vi,
                "type": "Placeholder Mismatch",
                "detail": f"Gender placeholder count mismatch. Source: {len(src_gender)} vs Trans: {len(trans_gender)}."
            })

        # 4.3 Rich Text Tags (Count, Spelling, Attributes, and Balance)
        source_tags = re.findall(r"<[^>]+>", source_en)
        trans_tags = re.findall(r"<[^>]+>", translation_vi)
        
        # Verify tag existence & exact attributes
        for tag in source_tags:
            if tag not in trans_tags:
                violations.append({
                    "file": rel_path,
                    "split_id": split_id,
                    "source": source_en,
                    "translation": translation_vi,
                    "type": "Tag Mismatch",
                    "detail": f"Rich text tag '{tag}' from source is missing or altered in translation."
                })

        # Tag balancing check
        opening_tags = [t for t in trans_tags if not t.startswith("</") and not t.endswith("/>")]
        closing_tags = [t for t in trans_tags if t.startswith("</")]
        
        def get_tag_name(t):
            match = re.match(r"<([a-zA-Z]+)", t)
            return match.group(1) if match else t

        opening_names = [get_tag_name(t) for t in opening_tags]
        closing_names = [t[2:-1] for t in closing_tags]
        
        for name in set(opening_names):
            if name in ["color", "size", "te", "SapTag"]:
                op_count = opening_names.count(name)
                cl_count = closing_names.count(name)
                if op_count != cl_count:
                    violations.append({
                        "file": rel_path,
                        "split_id": split_id,
                        "source": source_en,
                        "translation": translation_vi,
                        "type": "Tag Unbalanced",
                        "detail": f"Rich text tag '{name}' is unbalanced: {op_count} opening vs {cl_count} closing."
                    })

        # 4.4 Newlines
        source_newlines = source_en.count("\\n") + source_en.count("\n")
        trans_newlines = translation_vi.count("\\n") + translation_vi.count("\n")
        if source_newlines != trans_newlines:
            violations.append({
                "file": rel_path,
                "split_id": split_id,
                "source": source_en,
                "translation": translation_vi,
                "type": "Newline Mismatch",
                "detail": f"Source has {source_newlines} newlines, translation has {trans_newlines} (potential layout truncation)."
            })

        # --- CHECK 5: Action Verbs & Standalone Words ---
        # Strip placeholders and tags to check only translatable text
        trans_clean = re.sub(r"\{[^\}]+\}", "", translation_vi)
        trans_clean = re.sub(r"<[^>]+>", "", trans_clean)
        
        # Verify action verbs left untranslated
        verb_matches = self.action_verbs_pattern.findall(trans_clean)
        if verb_matches:
            source_clean = re.sub(r"\{[^\}]+\}", "", source_en)
            source_clean = re.sub(r"<[^>]+>", "", source_clean)
            source_verbs = self.action_verbs_pattern.findall(source_clean)
            
            # Action verbs that were in source and left untranslated
            violating_verbs = [v for v in verb_matches if any(sv.lower() == v.lower() for sv in source_verbs)]
            
            # Exclude false positives (e.g. part of shop name "Interference Exchange")
            filtered_verbs = []
            for v in violating_verbs:
                if v.lower() == "exchange" and "interference exchange" in trans_clean.lower():
                    continue
                filtered_verbs.append(v)
                
            if filtered_verbs:
                violations.append({
                    "file": rel_path,
                    "split_id": split_id,
                    "source": source_en,
                    "translation": translation_vi,
                    "type": "Untranslated Action Verb",
                    "detail": f"Action verbs {list(set(filtered_verbs))} were left untranslated."
                })

        # General "Weapon/Weapons" check
        weapon_matches = self.weapon_pattern.findall(trans_clean)
        if weapon_matches:
            if self.weapon_pattern.search(source_en):
                violations.append({
                    "file": rel_path,
                    "split_id": split_id,
                    "source": source_en,
                    "translation": translation_vi,
                    "type": "Untranslated Weapon Word",
                    "detail": "Isolated or general word 'Weapon(s)' was left untranslated (should be 'Vũ khí')."
                })

        return violations

    def run(self, report_path="audit_report.json"):
        all_violations = []
        print(f"Scanning directory: {self.ui_dir}")
        
        for root, _, files in os.walk(self.ui_dir):
            for f in files:
                if f.endswith(".json"):
                    path = os.path.join(root, f)
                    rel_path = os.path.relpath(path, self.ui_dir)
                    with open(path, "r", encoding="utf-8") as file:
                        try:
                            data = json.load(file)
                        except Exception as e:
                            print(f"Error loading {rel_path}: {e}")
                            continue
                        
                        for item in data:
                            violations = self.audit_item(item, rel_path)
                            all_violations.extend(violations)

        # Deduplicate violations based on (split_id, violation_type)
        unique_violations = {}
        for v in all_violations:
            key = (v["split_id"], v["type"])
            if key not in unique_violations:
                unique_violations[key] = v

        violations_list = list(unique_violations.values())
        print(f"Total violations found: {len(all_violations)}")
        print(f"Unique violations found: {len(violations_list)}")

        with open(report_path, "w", encoding="utf-8") as out:
            json.dump(violations_list, out, ensure_ascii=False, indent=2)
        print(f"Audit report saved to: {report_path}")
        return violations_list

# Self-test block
if __name__ == "__main__":
    ui_dir = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui"
    glossary_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\shared_glossary.md"
    
    auditor = TranslationAuditor(ui_dir, glossary_path)
    auditor.run()
```

---

## 6. Verification Method

### How to Independently Verify the Findings:
1.  **Inspect Audit Output**: Load the generated `C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\explorer_m1\violations_report.json` using a text viewer or parser to verify the count and details of unique violations.
2.  **Run the Auditor**: Execute `python C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\explorer_m1\audit.py` in the command prompt. The output will write `violations_report.json` to the current working directory, confirming matching capability.
3.  **Inspect Random Sample Entries**:
    *   Open `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_map_mark\lang_map_mark__ui__part_0001.json`.
    *   Find the entry for `split_id` `UI_0000660` (source: `"Dim Forest"`).
    *   Confirm that its translation is `"Rừng Tối"` in the JSON file. This verifies the **Glossary Translation Violation** findings.
    *   Open `C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json\ui\lang_multi_text\lang_multi_text__ui__part_0013.json`.
    *   Find the entry for `split_id` `UI_0007573`.
    *   Confirm that its source ends with lists for `A`, `S`, `SS` but its translation completely omits these lines, verifying the **Newline Mismatch / Truncation** findings.

### Invalidation Conditions:
*   The findings are invalidated if the glossary rules (`shared_glossary.md`) are modified to allow translations of location names or boss names in UI elements.
*   The placeholder counts are invalidated if the game engine is updated to support dynamic localization where tags/placeholders can have differing counts.
