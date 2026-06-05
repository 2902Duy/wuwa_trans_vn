import argparse
import sys
from pathlib import Path

# Add parent directory to sys.path so we can import update_keep_rules
sys.path.append(str(Path(__file__).parent))
from update_keep_rules import PROMPT_DIR, update_keep_rules_md, update_shared_glossary_md

def main():
    parser = argparse.ArgumentParser(description="Add new keywords extracted from the web to keep_english_rules.md and shared_glossary.md")
    parser.add_argument("--weapons", type=str, help="Comma-separated list of new weapons")
    parser.add_argument("--resonators", type=str, help="Comma-separated list of new resonators")
    parser.add_argument("--monsters", type=str, help="Comma-separated list of new monsters")
    
    args = parser.parse_args()
    
    weapons = [w.strip() for w in args.weapons.split(",")] if args.weapons else []
    resonators = [r.strip() for r in args.resonators.split(",")] if args.resonators else []
    monsters = [m.strip() for m in args.monsters.split(",")] if args.monsters else []
    
    # Filter out empty strings
    weapons = [w for w in weapons if w]
    resonators = [r for r in resonators if r]
    monsters = [m for m in monsters if m]
    
    if not weapons and not resonators and not monsters:
        print("No new keywords provided. Use --weapons, --resonators, or --monsters to pass keywords.")
        return
        
    print(f"Adding new keywords: {len(weapons)} weapons, {len(monsters)} monsters, {len(resonators)} resonators.")
    
    # Update files
    keep_rules_path = PROMPT_DIR / "keep_english_rules.md"
    if update_keep_rules_md(keep_rules_path, weapons, monsters, resonators):
        print(f"Updated {keep_rules_path.name} successfully.")
    else:
        print(f"No changes or failed to update {keep_rules_path.name}.")
        
    glossary_path = PROMPT_DIR / "shared_glossary.md"
    if update_shared_glossary_md(glossary_path, weapons, monsters, resonators):
        print(f"Updated {glossary_path.name} successfully.")
    else:
        print(f"No changes or failed to update {glossary_path.name}.")

if __name__ == "__main__":
    main()
