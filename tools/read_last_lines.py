import os
import glob

log_dir = r"C:\Users\tduy2\.gemini\antigravity\brain\bb8a7efd-8a70-4c28-b8cb-6ba5d47d22f0\.system_generated\tasks"
pattern = os.path.join(log_dir, "*.log")
log_files = glob.glob(pattern)

if log_files:
    # Get the latest modified log file
    latest_log = max(log_files, key=os.path.getmtime)
    print(f"Reading latest log: {os.path.basename(latest_log)} (modified {os.path.getmtime(latest_log)})")
    with open(latest_log, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        print(f"Total lines: {len(lines)}")
        print("Last 30 lines:")
        for line in lines[-30:]:
            print(line, end="")
else:
    print(f"No log files found in: {log_dir}")
