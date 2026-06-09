import json
import sys
from pathlib import Path

# Fix console encoding
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

JSON_ROOT = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json")

stats = {}

for domain_dir in sorted(JSON_ROOT.iterdir()):
    if not domain_dir.is_dir():
        continue
    domain = domain_dir.name
    stats[domain] = {
        "total": 0,
        "empty": [],
        "identical": []
    }
    
    for f in domain_dir.rglob("*.json"):
        try:
            rows = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue
            
        for idx, row in enumerate(rows):
            stats[domain]["total"] += 1
            src = row.get("source_en", "")
            vi = row.get("new_translation_vi", "")
            split_id = row.get("split_id", f"{domain.upper()}_{idx:07d}")
            
            if not vi:
                stats[domain]["empty"].append({
                    "split_id": split_id,
                    "file": f.name,
                    "source": src
                })
            elif vi == src:
                stats[domain]["identical"].append({
                    "split_id": split_id,
                    "file": f.name,
                    "source": src
                })

print("=== TRANSLATION COVERAGE REPORT (ALL DOMAINS) ===")
print(f"{'Domain':<22} | {'Total Rows':<10} | {'Empty Rows':<10} | {'Identical (EN==VI)':<18}")
print("-" * 70)

total_all = 0
total_empty = 0
total_identical = 0

for domain, d_stats in stats.items():
    t = d_stats["total"]
    e = len(d_stats["empty"])
    i = len(d_stats["identical"])
    print(f"{domain:<22} | {t:<10} | {e:<10} | {i:<18}")
    total_all += t
    total_empty += e
    total_identical += i

print("-" * 70)
print(f"{'TOTAL':<22} | {total_all:<10} | {total_empty:<10} | {total_identical:<18}")

# Print samples of identicals for each domain to let us inspect
print("\n=== IDENTICAL TRANSLATIONS SAMPLES (First 5 per domain) ===")
for domain, d_stats in stats.items():
    identicals = d_stats["identical"]
    if identicals:
        print(f"\n[{domain}] (Total identical: {len(identicals)})")
        for item in identicals[:10]:
            print(f"  - {item['split_id']} [{item['file']}]: {repr(item['source'])}")
            
# Print empty ones if any exist
if total_empty > 0:
    print("\n=== EMPTY TRANSLATIONS SAMPLES ===")
    for domain, d_stats in stats.items():
        empties = d_stats["empty"]
        if empties:
            print(f"\n[{domain}] (Total empty: {len(empties)})")
            for item in empties[:10]:
                print(f"  - {item['split_id']} [{item['file']}]: {repr(item['source'])}")
