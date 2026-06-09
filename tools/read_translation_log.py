import os
import sys

log_path = "translation_run.log"
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

if os.path.exists(log_path):
    try:
        content = open(log_path, "r", encoding="utf-16").read()
    except UnicodeError:
        content = open(log_path, "r", encoding="utf-8", errors="replace").read()
    
    lines = content.splitlines()
    print(f"Total lines: {len(lines)}")
    print("Last 100 lines:")
    for line in lines[-100:]:
        print(line)
else:
    print("translation_run.log does not exist yet.")
