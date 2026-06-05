import os
import shutil
from pathlib import Path

# Paths
WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
SRC_SKILL_DIR = WORKSPACE_DIR / "mistral_translate_work" / "skills" / "wuwa"

def get_install_paths():
    home = os.path.expanduser("~")
    paths = [
        # 1. Global Antigravity skills directory
        Path(home) / ".gemini" / "antigravity" / "skills" / "wuwa",
        # 2. Local project .claude skills directory
        WORKSPACE_DIR / ".claude" / "skills" / "wuwa",
        # 3. Local project .agent skills directory
        WORKSPACE_DIR / ".agent" / "skills" / "wuwa",
        # 4. Local project .agents skills directory
        WORKSPACE_DIR / ".agents" / "skills" / "wuwa"
    ]
    return paths

def install():
    if not SRC_SKILL_DIR.exists():
        print(f"Error: Source skill folder {SRC_SKILL_DIR} does not exist in workspace.")
        return
        
    print(f"Installing wuwa skill...")
    print(f"Source: {SRC_SKILL_DIR}")
    
    paths = get_install_paths()
    for dest in paths:
        try:
            # Create directory if it doesn't exist
            dest.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            for filename in os.listdir(SRC_SKILL_DIR):
                src_file = SRC_SKILL_DIR / filename
                dest_file = dest / filename
                if src_file.is_file():
                    shutil.copy2(src_file, dest_file)
            print(f"Installed to: {dest}")
        except Exception as e:
            print(f"Could not install to {dest}: {e}")
            
    print("\nSkill installed successfully!")
    print("You can now call it using: '/wuwa' directly in your chat terminal!")

if __name__ == "__main__":
    install()
