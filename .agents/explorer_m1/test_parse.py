import re

glossary_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\shared_glossary.md"

with open(glossary_path, "r", encoding="utf-8") as f:
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
        # Extract backticked terms
        found = re.findall(r"`([^`]+)`", line)
        for term in found:
            # Split by comma if it's a list (like in sections 4, 5, 6, 7)
            if "," in term:
                subterms = [t.strip() for t in term.split(",")]
                terms.extend(subterms)
            else:
                terms.append(term.strip())

# Clean terms and remove duplicates, preserving order
unique_terms = []
for t in terms:
    if t and t not in unique_terms:
        # Skip description-like backticks (e.g. if it has spaces and slashes, like "inflicts/gains...")
        if "/" in t or "[" in t:
            continue
        unique_terms.append(t)

import sys
sys.stdout.reconfigure(encoding='utf-8')

print(f"Total terms found: {len(unique_terms)}")
print("First 10 terms:", unique_terms[:10])
print("Last 10 terms:", unique_terms[-10:])
