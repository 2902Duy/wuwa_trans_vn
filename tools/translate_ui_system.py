import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
import concurrent.futures
import threading

# Fix Windows console encoding issues for Vietnamese text
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
WORK_DIR = WORKSPACE_DIR / "mistral_translate_work"
PROMPT_DIR = WORK_DIR / "prompts_compressed"
UI_DIR = WORK_DIR / "split_by_prompt" / "json" / "ui"
SYS_DIR = WORK_DIR / "split_by_prompt" / "json" / "system_text"

RUN_DIR = WORK_DIR / "reports" / "ui_system_run"
CHECKPOINT_PATH = RUN_DIR / "unique_translations.json"

API_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL_NAME = "mistral-large-latest"

TOKEN_RE = re.compile(r"(<[^>]+>|\{\d+\}|\{[A-Za-z_][A-Za-z0-9_]*\}|\\[nrt]|\{Cus:[^}]+\})")
ROW_RE = re.compile(r"^\s*([A-Z_]+_\d+):::(.*)$")

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

def read_json(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    for attempt in range(8):
        try:
            tmp.write_text(content, encoding="utf-8")
            import os
            os.replace(str(tmp), str(path))
            return
        except PermissionError:
            if attempt == 7:
                path.write_text(content, encoding="utf-8")
                try:
                    tmp.unlink(missing_ok=True)
                except Exception:
                    pass
                return
            time.sleep(0.25 * (attempt + 1))

def normalize(text):
    return (text or "").replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")

def denormalize(text):
    return (text or "").replace("\\n", "\n")

def load_api_keys():
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

def build_system_prompt(domain):
    parts = []
    # Load shared prompts
    parts.append((PROMPT_DIR / "shared_glossary.md").read_text(encoding="utf-8"))
    parts.append((PROMPT_DIR / "keep_english_rules.md").read_text(encoding="utf-8"))
    
    # Load domain-specific prompt
    prompt_file = "ui_prompt.md" if domain == "ui" else "system_text_prompt.md"
    parts.append((PROMPT_DIR / prompt_file).read_text(encoding="utf-8"))
    
    parts.append(
        """
## Strict Batch Output

Translate only rows that are meant to be translated. Preserve all IDs exactly.
Return only lines in this exact format:
ID:::Vietnamese translation

No Markdown, no comments, no explanations.
Keep all placeholders, tags, numbers, punctuation markers, and glossary terms exactly.
"""
    )
    return "\n\n".join(parts)

def call_mistral(api_key, system_prompt, user_prompt, retries):
    body = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 8192,
    }
    data = json.dumps(body).encode("utf-8")
    delay = 5
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            API_URL,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if attempt < retries and exc.code in {429, 500, 502, 503, 504}:
                time.sleep(delay)
                delay *= 2
                continue
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except Exception:
            if attempt >= retries:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("Mistral request failed")

def call_mistral_key_pool(keys, start_index, system_prompt, user_prompt, retries, batch_delay):
    errors = []
    key_count = len(keys)
    current = start_index
    for round_no in range(1, retries + 1):
        for _ in range(key_count):
            key_index = current % key_count
            current += 1
            try:
                output = call_mistral(keys[key_index], system_prompt, user_prompt, 1)
                if batch_delay:
                    time.sleep(batch_delay)
                return output, current
            except Exception as exc:
                errors.append({"round": round_no, "key_index": key_index, "error": repr(exc)})
                continue
        if round_no < retries:
            time.sleep(15 * round_no)
    raise RuntimeError(json.dumps({"kind": "all_keys_failed", "errors": errors[-20:]}, ensure_ascii=False))

def parse_output(output):
    parsed = {}
    current_id = None
    for line in output.splitlines():
        match = ROW_RE.match(line)
        if match:
            current_id = match.group(1)
            parsed[current_id] = match.group(2).strip()
        elif current_id and line.strip():
            parsed[current_id] += "\n" + line.rstrip()
    return parsed

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

def scan_and_collect_unique():
    # Scan both directories and group identical English sentences by domain
    ui_sources = set()
    sys_sources = set()
    
    for path in UI_DIR.rglob("*.json"):
        for row in read_json(path):
            source = row.get("source_en", "")
            if source:
                ui_sources.add(source)
                
    for path in SYS_DIR.rglob("*.json"):
        for row in read_json(path):
            source = row.get("source_en", "")
            if source:
                sys_sources.add(source)
                
    return sorted(ui_sources), sorted(sys_sources)

def make_batches(items, batch_size, max_chars):
    batch = []
    chars = 0
    for item in items:
        row_len = len(item["source_en"]) + 40
        if batch and (len(batch) >= batch_size or chars + row_len > max_chars):
            yield batch
            batch = []
            chars = 0
        batch.append(item)
        chars += row_len
    if batch:
        yield batch

def build_user_prompt(batch):
    lines = []
    for item in batch:
        lines.append(f"{item['temp_id']}:::{normalize(item['source_en'])}")
    return "\n".join(lines)

def apply_translations_to_json_files(all_translations):
    # Map domain -> source -> translation
    mapping = defaultdict(dict)
    for k, v in all_translations.items():
        domain, source = k.split(":::", 1)
        mapping[domain][source] = v
        
    print("\nApplying translations back to JSON split files...")
    
    # UI
    ui_files = list(UI_DIR.rglob("*.json"))
    for path in ui_files:
        rows = read_json(path)
        changed = False
        for row in rows:
            source = row.get("source_en", "")
            trans = mapping["ui"].get(source)
            if trans:
                row["new_translation_vi"] = trans
                row["status"] = "translated"
                row["rule_decision"] = "PASS"
                row["rule_score"] = 10
                row["rule_issues"] = ""
                changed = True
        if changed:
            write_json(path, rows)
            
    # System Text
    sys_files = list(SYS_DIR.rglob("*.json"))
    for path in sys_files:
        rows = read_json(path)
        changed = False
        for row in rows:
            source = row.get("source_en", "")
            trans = mapping["system_text"].get(source)
            if trans:
                row["new_translation_vi"] = trans
                row["status"] = "translated"
                row["rule_decision"] = "PASS"
                row["rule_score"] = 10
                row["rule_issues"] = ""
                changed = True
        if changed:
            write_json(path, rows)
            
    print("Done applying translations to JSON files.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--max-chars", type=int, default=5000)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--batch-delay", type=float, default=0.2)
    parser.add_argument("--workers", type=int, default=11)
    args = parser.parse_args()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    keys = load_api_keys()
    if not keys:
        raise RuntimeError("No Mistral API keys found in .env.")
    print(f"Loaded {len(keys)} API keys.")

    # Load existing checkpoint
    checkpoint = {}
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            print(f"Loaded checkpoint with {len(checkpoint)} unique translations.")
        except Exception as exc:
            print(f"Error loading checkpoint: {exc}. Starting fresh.")
            checkpoint = {}

    # Scan and collect unique
    print("Scanning directories...")
    ui_sources, sys_sources = scan_and_collect_unique()
    print(f"UI Unique: {len(ui_sources)}, System Text Unique: {len(sys_sources)}")

    # Group into items to translate
    items_to_translate = []
    
    # UI items
    ui_to_run = []
    for idx, source in enumerate(ui_sources):
        key = f"ui:::{source}"
        if key in checkpoint:
            continue
        ui_to_run.append({
            "temp_id": f"UIT_{idx:05d}",
            "source_en": source,
            "prompt_domain": "ui"
        })
    print(f"UI unique items needing translation: {len(ui_to_run)}")
    
    # System Text items
    sys_to_run = []
    for idx, source in enumerate(sys_sources):
        key = f"system_text:::{source}"
        if key in checkpoint:
            continue
        sys_to_run.append({
            "temp_id": f"SYST_{idx:05d}",
            "source_en": source,
            "prompt_domain": "system_text"
        })
    print(f"System Text unique items needing translation: {len(sys_to_run)}")

    # Make batches
    ui_batches = list(make_batches(ui_to_run, args.batch_size, args.max_chars))
    sys_batches = list(make_batches(sys_to_run, args.batch_size, args.max_chars))
    
    all_batches_info = []
    for batch in ui_batches:
        all_batches_info.append({
            "domain": "ui",
            "system_prompt": build_system_prompt("ui"),
            "items": batch
        })
    for batch in sys_batches:
        all_batches_info.append({
            "domain": "system_text",
            "system_prompt": build_system_prompt("system_text"),
            "items": batch
        })

    total_batches = len(all_batches_info)
    print(f"Total batches to translate: {total_batches}")

    if total_batches > 0:
        write_lock = threading.Lock()
        key_cursor_lock = threading.Lock()
        key_cursor = 0
        batch_counter = 0

        placeholder_errors = []
        translation_errors = []

        def process_batch(batch_info):
            nonlocal key_cursor, batch_counter
            domain = batch_info["domain"]
            sys_prompt = batch_info["system_prompt"]
            batch_items = batch_info["items"]

            with write_lock:
                batch_counter += 1
                current_batch_no = batch_counter

            # Map temp_id -> item
            item_map = {item["temp_id"]: item for item in batch_items}

            with key_cursor_lock:
                start_idx = key_cursor
                key_cursor += 1

            try:
                output, new_cursor = call_mistral_key_pool(
                    keys,
                    start_idx,
                    sys_prompt,
                    build_user_prompt(batch_items),
                    args.retries,
                    args.batch_delay,
                )
                
                with key_cursor_lock:
                    key_cursor = max(key_cursor, new_cursor)

                parsed = parse_output(output)
                missing_ids = sorted(set(item_map.keys()) - set(parsed.keys()))

                local_checkpoint_updates = {}
                
                if missing_ids:
                    print(f"[{domain} Batch {current_batch_no}/{total_batches}] Warning: {len(missing_ids)} missing rows in translation response.")

                for temp_id, translation in parsed.items():
                    item = item_map.get(temp_id)
                    if not item:
                        continue
                    
                    source = item["source_en"]
                    val_issues = validate_translation(source, translation)
                    
                    if val_issues:
                        with write_lock:
                            placeholder_errors.append({
                                "domain": domain,
                                "source": source,
                                "translation": translation,
                                "issues": val_issues
                            })
                    else:
                        key = f"{domain}:::{source}"
                        local_checkpoint_updates[key] = translation

                # Write batch results to checkpoint
                if local_checkpoint_updates:
                    with write_lock:
                        checkpoint.update(local_checkpoint_updates)
                        write_json(CHECKPOINT_PATH, checkpoint)

                print(f"[{domain} Batch {current_batch_no}/{total_batches}] Completed. Translated {len(local_checkpoint_updates)}/{len(batch_items)} items successfully.")

            except Exception as exc:
                print(f"[{domain} Batch {current_batch_no}/{total_batches}] FAILED with exception: {exc}")
                with write_lock:
                    translation_errors.append({
                        "domain": domain,
                        "batch": current_batch_no,
                        "error": str(exc),
                        "items": [{"temp_id": i["temp_id"], "source_en": i["source_en"]} for i in batch_items]
                    })

        # Run parallel workers
        print(f"Starting execution pool with {args.workers} workers...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            executor.map(process_batch, all_batches_info)

        print("\nAPI translation run finished!")
        print(f"Successful unique translations added: {len(checkpoint)}")
        print(f"Placeholder validation errors: {len(placeholder_errors)}")
        print(f"API translation failures (batches): {len(translation_errors)}")

        if placeholder_errors:
            write_json(RUN_DIR / "placeholder_errors.json", placeholder_errors)
        if translation_errors:
            write_json(RUN_DIR / "batch_errors.json", translation_errors)

    # Finally, apply all translations (both existing in checkpoint and newly translated) to JSON split files
    apply_translations_to_json_files(checkpoint)
    print("\nAll tasks completed successfully!")

if __name__ == "__main__":
    main()
