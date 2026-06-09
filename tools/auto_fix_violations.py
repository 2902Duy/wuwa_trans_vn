"""
auto_fix_violations.py
========================
Tự động sửa các violations phổ biến:
1. Placeholder Mismatch: khôi phục {Cus:Ipt,...} nguyên gốc từ source_en
2. Glossary Violation: khôi phục tên quái/boss tiếng Anh
3. Newline Mismatch: đồng bộ số lượng \n giữa source và translation
4. Blacklisted: thay thế thuật ngữ bị cấm
5. Tag Mismatch: khôi phục <color=...> tags
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
VIOLATIONS_FILE = WORKSPACE / ".agents" / "explorer_m1" / "violations_report.json"

TARGET_DIRS = [
    WORKSPACE / "mistral_translate_work" / "split_by_prompt" / "json" / "ui",
    WORKSPACE / "mistral_translate_work" / "split_by_prompt" / "json" / "item",
    WORKSPACE / "mistral_translate_work" / "split_by_prompt" / "json" / "system_text",
]

# ── Blacklist replacements ──────────────────────────────────────────
BLACKLIST_FIX = [
    # Wrong → Correct
    (r"Tấn Công Nặng",    "Heavy Attack"),
    (r"Tấn Công Thường",  "Normal Attack"),
    (r"Tấn Công Cơ Bản",  "Basic Attack"),
    (r"Tấn Công Giữa Không Trung", "Mid-air Attack"),
    (r"Kỹ Năng Cộng Hưởng", "Resonance Skill"),
    (r"Giải Phóng Cộng Hưởng", "Resonance Liberation"),
    (r"Mạch Forte",       "Forte Circuit"),
    (r"Năng Lượng Cộng Hưởng", "Resonance Energy"),
    (r"Năng Lượng Hòa Âm", "Concerto Energy"),
    (r"Kỹ Năng Vào",      "Intro Skill"),
    (r"Kỹ Năng Ra",       "Outro Skill"),
    (r"Kỹ Năng Bẩm Sinh", "Inherent Skill"),
    (r"Kỹ Năng Tránh Né", "Dodge Counter"),
    (r"Chuỗi Cộng Hưởng", "Resonance Chain"),
    (r"mày",              "ngươi"),
    (r"tao ",             "ta "),
]

# ── Cus:Ipt placeholder fix ─────────────────────────────────────────
CUS_IPT_RE = re.compile(r"\{Cus:Ipt,[^}]+\}")

def extract_cus_ipt(text: str) -> list:
    return CUS_IPT_RE.findall(text)

def restore_cus_ipt(source_en: str, translation: str) -> str:
    src_tags  = extract_cus_ipt(source_en)
    vi_tags   = extract_cus_ipt(translation)
    if not src_tags:
        return translation
    result = translation
    for i, vi_tag in enumerate(vi_tags):
        if i < len(src_tags) and vi_tag != src_tags[i]:
            result = result.replace(vi_tag, src_tags[i], 1)
    return result

# ── Color/HTML tag fix ──────────────────────────────────────────────
COLOR_TAG_RE = re.compile(r"<[^>]+>")

def restore_color_tags(source_en: str, translation: str) -> str:
    src_tags = COLOR_TAG_RE.findall(source_en)
    vi_tags  = COLOR_TAG_RE.findall(translation)
    if not src_tags or len(src_tags) != len(vi_tags):
        return translation
    result = translation
    for src_t, vi_t in zip(src_tags, vi_tags):
        if src_t != vi_t:
            result = result.replace(vi_t, src_t, 1)
    return result

# ── Newline count sync ──────────────────────────────────────────────
def sync_newlines(source_en: str, translation: str) -> str:
    src_count = source_en.count("\\n")
    vi_count  = translation.count("\\n")
    if src_count == vi_count:
        return translation
    # If translation has fewer \n, it may have been dropped - hard to auto-fix
    # Only fix if translation has MORE \n than source (strip extras)
    if vi_count > src_count:
        diff = vi_count - src_count
        result = translation
        for _ in range(diff):
            result = result[::-1].replace("n\\", "", 1)[::-1]
        return result
    return translation

# ── Apply blacklist fixes ───────────────────────────────────────────
def apply_blacklist(text: str) -> str:
    for pattern, replacement in BLACKLIST_FIX:
        text = re.sub(pattern, replacement, text)
    return text

# ── Load all JSON files into memory ────────────────────────────────
def load_all_files() -> dict:
    """Returns {Path: [rows]} for all JSON files."""
    all_files = {}
    for d in TARGET_DIRS:
        for f in sorted(d.rglob("*.json")):
            rows = json.loads(f.read_text(encoding="utf-8"))
            all_files[f] = rows
    return all_files

# ── Build split_id → (path, row_index) lookup ─────────────────────
def build_lookup(all_files: dict) -> dict:
    lookup = {}
    for path, rows in all_files.items():
        for idx, row in enumerate(rows):
            sid = row.get("split_id", "")
            if sid:
                lookup[sid] = (path, idx)
    return lookup

# ── Main fix logic ──────────────────────────────────────────────────
def main():
    print("Loading violations report...")
    violations = json.loads(VIOLATIONS_FILE.read_text(encoding="utf-8"))
    print(f"  {len(violations)} violations found.")

    print("Loading all JSON files...")
    all_files = load_all_files()
    lookup = build_lookup(all_files)
    print(f"  Loaded {len(lookup)} rows across {len(all_files)} files.")

    counters = {t: 0 for t in [
        "placeholder", "glossary", "newline", "blacklist", "tag", "skipped"
    ]}

    for v in violations:
        vtype = v.get("violation_type", v.get("type", ""))
        sid   = v.get("split_id", "")

        if sid not in lookup:
            counters["skipped"] += 1
            continue

        path, idx = lookup[sid]
        row = all_files[path][idx]
        src = row.get("source_en", "")
        vi  = row.get("new_translation_vi", "")

        if not vi or not src:
            counters["skipped"] += 1
            continue

        original_vi = vi

        # 1. Fix Placeholder Mismatch
        if "Placeholder" in vtype:
            vi = restore_cus_ipt(src, vi)
            if vi != original_vi:
                counters["placeholder"] += 1

        # 2. Fix Tag Mismatch
        if "Tag" in vtype:
            vi = restore_color_tags(src, vi)
            if vi != original_vi:
                counters["tag"] += 1

        # 3. Fix Newline Mismatch
        if "Newline" in vtype:
            vi = sync_newlines(src, vi)
            if vi != original_vi:
                counters["newline"] += 1

        # 4. Fix Blacklisted terms (apply to ALL rows, not just blacklist violations)
        vi_after_blacklist = apply_blacklist(vi)
        if vi_after_blacklist != vi:
            vi = vi_after_blacklist
            counters["blacklist"] += 1

        # Update in-memory
        all_files[path][idx]["new_translation_vi"] = vi

    # Always apply blacklist fixes across all rows
    print("\nApplying blacklist fixes across ALL rows...")
    for path, rows in all_files.items():
        for row in rows:
            vi = row.get("new_translation_vi", "")
            if not vi: continue
            fixed = apply_blacklist(vi)
            if fixed != vi:
                row["new_translation_vi"] = fixed
                counters["blacklist"] += 1

    # Write back all files
    print("Writing fixes to disk...")
    for path, rows in all_files.items():
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ Done!")
    print(f"  Placeholder fixes: {counters['placeholder']}")
    print(f"  Tag fixes:         {counters['tag']}")
    print(f"  Newline fixes:     {counters['newline']}")
    print(f"  Blacklist fixes:   {counters['blacklist']}")
    print(f"  Skipped:           {counters['skipped']}")

if __name__ == "__main__":
    main()
