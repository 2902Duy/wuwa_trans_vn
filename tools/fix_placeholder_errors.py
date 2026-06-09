import json
import os
import sys
import time
import urllib.request
import urllib.error
import threading
import re
from pathlib import Path
import concurrent.futures

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
WORK_DIR = WORKSPACE_DIR / "mistral_translate_work"
RUN_DIR = WORK_DIR / "reports" / "story_dialogue_run"
CHECKPOINT_PATH = RUN_DIR / "unique_translations.json"
ERRORS_PATH = RUN_DIR / "placeholder_errors.json"

TOKEN_RE = re.compile(r"(<[^>]+>|\{\d+\}|\{[A-Za-z_][A-Za-z0-9_]*\}|\\[nrt]|\{Cus:[^}]+\})")
GLOSSARY_TERMS = (
    "Rover",
    "Echo",
    "Resonator",
    "Resonance Chain",
    "Resonance Skill",
    "Resonance Liberation",
    "Forte Circuit",
    "Basic Attack",
    "Normal Attack",
    "Heavy Attack",
    "Mid-air Attack",
    "Dodge Counter",
    "Intro Skill",
    "Outro Skill",
    "Inherent Skill",
    "Aero Erosion",
    "Glacio Chafe",
    "Spectro Frazzle",
    "Havoc Bane",
    "Fusion Burst",
    "Electro Flare",
    "Negative Status",
    "Tidal Blight",
    "DMG",
    "DMG Bonus",
    "Crit. Rate",
    "Crit. DMG",
)

def normalize(text):
    return (text or "").replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")

def validate_translation(source, translation):
    issues = []
    source_norm = normalize(source)
    translation_norm = normalize(translation)
    for token in TOKEN_RE.findall(source_norm):
        if token not in translation_norm:
            issues.append(f"missing_token:{token}")
    for term in GLOSSARY_TERMS:
        if term in source_norm and term not in translation_norm:
            issues.append(f"missing_glossary_term:{term}")
    return issues

def load_mistral_keys():
    keys = []
    env_path = WORKSPACE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() in {"MISTRAL_API_KEYS", "MISTRAL_API_KEY"}:
                keys.extend(part.strip() for part in value.strip().strip('"').strip("'").split(","))
    env_keys = os.environ.get("MISTRAL_API_KEYS") or os.environ.get("MISTRAL_API_KEY", "")
    if env_keys:
        keys.extend(part.strip() for part in env_keys.replace("\n", ",").split(","))
    clean = []
    for key in keys:
        if key and key not in clean:
            clean.append(key)
    return clean

def call_mistral(api_key, system_prompt, user_prompt, model="mistral-small-latest"):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
    }
    data = json.dumps(body).encode("utf-8")
    delay = 2
    for attempt in range(1, 4):
        request = urllib.request.Request(
            "https://api.mistral.ai/v1/chat/completions",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            if attempt == 3:
                raise exc
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("Mistral request failed")

def main():
    if not ERRORS_PATH.exists():
        print("No placeholder errors file found.")
        return

    with open(ERRORS_PATH, "r", encoding="utf-8") as f:
        errors = json.load(f)
    print(f"Loaded {len(errors)} placeholder errors to fix.")

    mistral_keys = load_mistral_keys()
    if not mistral_keys:
        print("No Mistral API keys found.")
        return
    print(f"Loaded {len(mistral_keys)} Mistral API keys.")

    checkpoint = {}
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)

    system_prompt = """You are an expert game localizer translating Wuthering Waves dialogue from English to Vietnamese.
Your task is to fix a translation that failed validation because of missing tags, placeholders, or glossary terms.

Here are the strict keeping rules:
1. Never translate `{PlayerName}`. Keep `{PlayerName}` exactly as `{PlayerName}`.
2. Keep `Echo` (or plural `Echoes`) as `Echo` or `Echoes`. Do not translate to "Tiếng Vang".
3. Keep `Rover` as `Rover`. Do not translate to "Nhà Lữ Hành".
4. Keep `Resonator` as `Resonator`.
5. Keep all HTML tags like `<i>`, `</i>`, `<color=...>`, `</color>`, `<ano=...>`, `</ano>`, `<te ...>`, `</te>` exactly as in the source.
6. Keep control characters like `\\n` exactly.
7. Keep gameplay mechanics terms like `Mid-air Attack`, `Basic Attack`, `Heavy Attack`, `Dodge Counter`, `DMG` exactly in English.

Format your output to return ONLY the corrected Vietnamese translation. No explanations, no markdown block wrappers.
"""

    write_lock = threading.Lock()
    key_cursor_lock = threading.Lock()
    key_cursor = 0
    fixed_count = 0
    remaining_errors = []

    def fix_item(item):
        nonlocal key_cursor, fixed_count
        source = item["source"]
        prev_trans = item["translation"]
        
        # Check if already in checkpoint
        with write_lock:
            if source in checkpoint:
                return

        with key_cursor_lock:
            api_key = mistral_keys[key_cursor % len(mistral_keys)]
            key_cursor += 1

        user_prompt = f"Source: {normalize(source)}\nPrevious Translation: {normalize(prev_trans)}\nCorrected Translation:"
        
        try:
            corrected = call_mistral(api_key, system_prompt, user_prompt)
            # Check for starting {0} issues and auto-fix
            val_issues = validate_translation(source, corrected)
            if val_issues and "missing_token:{0}" in val_issues and source.startswith("{0}") and "{0}" not in corrected:
                corrected = "{0} " + corrected
                val_issues = validate_translation(source, corrected)
                
            if not val_issues:
                with write_lock:
                    checkpoint[source] = corrected
                    fixed_count += 1
                    if fixed_count % 50 == 0:
                        print(f"Fixed {fixed_count} errors...")
            else:
                with write_lock:
                    remaining_errors.append({
                        "source": source,
                        "translation": corrected,
                        "issues": val_issues
                    })
        except Exception as e:
            with write_lock:
                remaining_errors.append({
                    "source": source,
                    "translation": prev_trans,
                    "issues": item["issues"] + [f"api_error: {str(e)[:50]}"]
                })

    print("Running error correction in parallel...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        executor.map(fix_item, errors)

    print(f"\nCorrection run finished!")
    print(f"Successfully fixed: {fixed_count} / {len(errors)} errors.")
    print(f"Remaining errors: {len(remaining_errors)}")

    # Write back checkpoint
    if fixed_count > 0:
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
        print("Updated unique_translations.json checkpoint.")

    # Write remaining errors
    with open(ERRORS_PATH, "w", encoding="utf-8") as f:
        json.dump(remaining_errors, f, ensure_ascii=False, indent=2)
    print("Updated placeholder_errors.json.")

if __name__ == "__main__":
    main()
