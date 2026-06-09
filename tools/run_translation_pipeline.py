import argparse
import subprocess
import sys
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parents[1]

def run_script(script_rel_path: str, args: list[str] = None):
    script_path = WORKSPACE_DIR / script_rel_path
    if not script_path.exists():
        print(f"Error: Script {script_path} not found.")
        sys.exit(1)
        
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
        
    print(f"\n>>> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(WORKSPACE_DIR))
    if result.returncode != 0:
        print(f"Error: Command failed with return code {result.returncode}")
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(description="Wuthering Waves Translation Pipeline Orchestrator")
    parser.add_argument(
        "--step",
        choices=["prepare", "translate", "correct", "sync", "all"],
        required=True,
        help="Pipeline step to run: prepare (extract/classify/merge), translate, correct (reverts/audits/fixes), sync (sync to DB/verify), or all"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=80,
        help="Batch size for translation (default: 80)"
    )
    args = parser.parse_args()

    steps_to_run = []
    if args.step == "all":
        steps_to_run = ["prepare", "translate", "correct", "sync"]
    else:
        steps_to_run = [args.step]

    for step in steps_to_run:
        print(f"\n============================================================")
        print(f"  STARTING PIPELINE STEP: {step.upper()}")
        print(f"============================================================")
        
        if step == "prepare":
            # Phase 1: prepare
            run_script("tools/extract_new_strings.py")
            run_script("tools/classify_new_strings.py")
            run_script("tools/merge_new_strings_to_split.py")
            
        elif step == "translate":
            # Phase 2: translate
            domains = [
                "name_title", "weapon", "rc_description", "monster_description", 
                "echo_set", "phantom_skill", "ui", "item", "system_text", 
                "quest", "lore", "story_dialogue", "skill_description"
            ]
            translate_args = [
                "--batch-size", str(args.batch_size),
                "--only-empty",
                "--domains"
            ] + domains
            run_script("tools/translate_gemini_gemma_parallel.py", translate_args)
            
        elif step == "correct":
            # Phase 3: correct
            run_script("tools/apply_keep_english_reverts.py")
            run_script("tools/audit_forbidden_english_terms.py")
            run_script("tools/apply_forbidden_english_fixes.py")
            run_script("tools/apply_remaining_translation_fixes.py")
            run_script("tools/apply_manual_corrections.py")
            
        elif step == "sync":
            # Phase 4: sync
            run_script("tools/sync_split_json_to_db.py")

    print(f"\n============================================================")
    print(f"  [SUCCESS] PIPELINE STEP(S) COMPLETED SUCCESSFULLY!")
    print(f"============================================================")

if __name__ == "__main__":
    main()
