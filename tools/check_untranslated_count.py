import json
from pathlib import Path

JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
domains = ["ui", "item", "system_text", "quest", "lore", "story_dialogue", "skill_description", "name_title", "weapon", "rc_description", "monster_description", "echo_set", "phantom_skill"]

total_untranslated = 0
untranslated_by_domain = {}

for domain in domains:
    target_dir = JSON_ROOT / domain
    if not target_dir.exists():
        continue
    count = 0
    for p in target_dir.rglob("*.json"):
        try:
            rows = json.loads(p.read_text(encoding="utf-8"))
            for r in rows:
                src = r.get("source_en", "")
                vi = r.get("new_translation_vi", "")
                if not src: continue
                # check if it needs translation
                # (matching the logic in translate_gemini_gemma_parallel.py)
                is_num = src.strip().isdigit() or not any(c.isalpha() for c in src)
                if (not vi or vi == src) and not is_num and src not in ["Echo", "Resonator", "Rover"]:
                    count += 1
        except Exception:
            pass
    untranslated_by_domain[domain] = count
    total_untranslated += count

print(f"Total untranslated rows remaining: {total_untranslated}")
for d, c in untranslated_by_domain.items():
    if c > 0:
        print(f"  {d:<20}: {c}")
