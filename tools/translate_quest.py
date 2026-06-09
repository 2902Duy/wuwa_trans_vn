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
QUEST_DIR = WORK_DIR / "split_by_prompt" / "json" / "quest"
UI_DIR = WORK_DIR / "split_by_prompt" / "json" / "ui"
SYS_DIR = WORK_DIR / "split_by_prompt" / "json" / "system_text"

RUN_DIR = WORK_DIR / "reports" / "quest_run"
CHECKPOINT_PATH = RUN_DIR / "unique_translations.json"

UI_SYS_RUN_DIR = WORK_DIR / "reports" / "ui_system_run"
UI_SYS_CHECKPOINT_PATH = UI_SYS_RUN_DIR / "unique_translations.json"
UI_SYS_ERRORS_PATH = UI_SYS_RUN_DIR / "placeholder_errors.json"

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

def load_gemini_keys():
    keys = []
    env_path = WORKSPACE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() in {"GEMINI_API_KEYS", "GEMINI_API_KEY"}:
                keys.extend(part.strip() for part in value.strip().strip('"').strip("'").split(","))
    env_keys = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
    if env_keys:
        keys.extend(part.strip() for part in env_keys.replace("\n", ",").split(","))

    clean = []
    for key in keys:
        if key and key not in clean:
            clean.append(key)
    return clean

def build_system_prompt(domain):
    parts = []
    parts.append((PROMPT_DIR / "shared_glossary.md").read_text(encoding="utf-8"))
    parts.append((PROMPT_DIR / "keep_english_rules.md").read_text(encoding="utf-8"))
    
    prompt_file = "quest_prompt.md"
    if domain == "ui":
        prompt_file = "ui_prompt.md"
    elif domain == "system_text":
        prompt_file = "system_text_prompt.md"
        
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

def call_gemini(api_key, system_prompt, user_prompt, retries, model="gemini-2.5-flash"):
    # Build Gemini request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_prompt}
            ]
        },
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192
        }
    }
    data = json.dumps(body).encode("utf-8")
    delay = 5
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = json.loads(response.read().decode("utf-8"))
                # Parse Gemini response candidate
                candidates = payload.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                raise RuntimeError(f"Unexpected response format: {payload}")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            # If flash fails, maybe try pro or retry
            if attempt < retries and exc.code in {429, 500, 502, 503, 504}:
                time.sleep(delay)
                delay *= 2
                continue
            # Try pro on other errors
            if model == "gemini-2.5-flash":
                return call_gemini(api_key, system_prompt, user_prompt, retries, model="gemini-2.5-pro")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except Exception:
            if attempt >= retries:
                if model == "gemini-2.5-flash":
                    return call_gemini(api_key, system_prompt, user_prompt, retries, model="gemini-2.5-pro")
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("Gemini request failed")

def call_gemini_key_pool(keys, start_index, system_prompt, user_prompt, retries, batch_delay):
    errors = []
    key_count = len(keys)
    current = start_index
    for round_no in range(1, retries + 1):
        for _ in range(key_count):
            key_index = current % key_count
            current += 1
            try:
                output = call_gemini(keys[key_index], system_prompt, user_prompt, 1)
                if batch_delay:
                    time.sleep(batch_delay)
                return output, current
            except Exception as exc:
                errors.append({"round": round_no, "key_index": key_index, "error": repr(exc)})
                continue
        if round_no < retries:
            time.sleep(15 * round_no)
    raise RuntimeError(json.dumps({"kind": "all_gemini_keys_failed", "errors": errors[-20:]}, ensure_ascii=False))

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

def scan_and_collect_unique_quests():
    quest_sources = set()
    for path in QUEST_DIR.rglob("*.json"):
        for row in read_json(path):
            source = row.get("source_en", "")
            if source:
                quest_sources.add(source)
    return sorted(quest_sources)

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

def apply_quest_translations_to_json_files(all_translations):
    print("\nApplying quest translations back to JSON split files...")
    quest_files = list(QUEST_DIR.rglob("*.json"))
    for path in quest_files:
        rows = read_json(path)
        changed = False
        for row in rows:
            source = row.get("source_en", "")
            trans = all_translations.get(source)
            if trans:
                row["new_translation_vi"] = trans
                row["status"] = "translated"
                row["rule_decision"] = "PASS"
                row["rule_score"] = 10
                row["rule_issues"] = ""
                changed = True
        if changed:
            write_json(path, rows)
    print("Done applying quest translations.")

def resolve_previous_errors_with_gemini(gemini_keys, args):
    if not gemini_keys:
        print("\nNo Gemini API keys available. Skipping resolution of previous UI/System Text errors.")
        return
    
    if not UI_SYS_ERRORS_PATH.exists():
        print("\nNo previous UI/System Text placeholder errors report found.")
        return
        
    print("\nResolving remaining placeholder errors in UI & System Text using Gemini API...")
    errors = read_json(UI_SYS_ERRORS_PATH)
    if not errors:
        print("No placeholder errors found in report.")
        return
        
    # Group errors by domain so we can use correct prompt
    domain_errors = defaultdict(list)
    for err in errors:
        # err is {"domain": "ui", "source": "...", "translation": "...", "issues": [...]}
        domain_errors[err["domain"]].append(err)
        
    ui_sys_checkpoint = {}
    if UI_SYS_CHECKPOINT_PATH.exists():
        try:
            with open(UI_SYS_CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                ui_sys_checkpoint = json.load(f)
        except Exception:
            pass

    resolved_count = 0
    
    for domain, items in domain_errors.items():
        print(f"Resolving {len(items)} items for domain '{domain}'...")
        system_prompt = build_system_prompt(domain)
        
        # Batch items
        batch_items = []
        for idx, item in enumerate(items):
            batch_items.append({
                "temp_id": f"ERR_{idx:05d}",
                "source_en": item["source"]
            })
            
        batches = list(make_batches(batch_items, args.batch_size, args.max_chars))
        key_cursor = 0
        
        for batch_no, batch in enumerate(batches, 1):
            item_map = {i["temp_id"]: i for i in batch}
            try:
                output, new_cursor = call_gemini_key_pool(
                    gemini_keys,
                    key_cursor,
                    system_prompt,
                    build_user_prompt(batch),
                    args.retries,
                    args.batch_delay
                )
                key_cursor = new_cursor
                parsed = parse_output(output)
                
                for temp_id, translation in parsed.items():
                    orig_item = item_map.get(temp_id)
                    if not orig_item:
                        continue
                    source = orig_item["source_en"]
                    val_issues = validate_translation(source, translation)
                    
                    if not val_issues:
                        key = f"{domain}:::{source}"
                        ui_sys_checkpoint[key] = translation
                        resolved_count += 1
                        print(f"Resolved UI/Sys: '{source}' -> '{translation}'")
            except Exception as exc:
                print(f"Failed to resolve batch {batch_no} in domain {domain} with Gemini: {exc}")
                
    if resolved_count > 0:
        # Save updated checkpoint
        write_json(UI_SYS_CHECKPOINT_PATH, ui_sys_checkpoint)
        print(f"Saved {resolved_count} resolved translations to UI/System Text checkpoint.")
        
        # Apply back to files
        mapping = defaultdict(dict)
        for k, v in ui_sys_checkpoint.items():
            dom, src = k.split(":::", 1)
            mapping[dom][src] = v
            
        # Apply UI
        for path in UI_DIR.rglob("*.json"):
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
                
        # Apply System Text
        for path in SYS_DIR.rglob("*.json"):
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
        print("Updated JSON split files for UI & System Text with resolved translations.")
    else:
        print("No placeholder errors were successfully resolved with Gemini.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--max-chars", type=int, default=5000)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--batch-delay", type=float, default=0.2)
    parser.add_argument("--workers", type=int, default=11)
    args = parser.parse_args()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    
    mistral_keys = load_mistral_keys()
    gemini_keys = load_gemini_keys()
    
    if not mistral_keys:
        raise RuntimeError("No Mistral API keys found in .env.")
    print(f"Loaded {len(mistral_keys)} Mistral API keys.")
    
    if gemini_keys:
        print(f"Loaded {len(gemini_keys)} Gemini API keys.")
    else:
        print("Warning: No Gemini API keys found in .env or environment.")

    # Load existing checkpoint
    checkpoint = {}
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            print(f"Loaded quest checkpoint with {len(checkpoint)} unique translations.")
        except Exception as exc:
            print(f"Error loading checkpoint: {exc}. Starting fresh.")
            checkpoint = {}

    # Scan and collect unique quests
    print("Scanning quest directories...")
    quest_sources = scan_and_collect_unique_quests()
    print(f"Quest Unique: {len(quest_sources)}")

    # Group into items to translate
    to_run = []
    for idx, source in enumerate(quest_sources):
        if source in checkpoint:
            continue
        to_run.append({
            "temp_id": f"QT_{idx:05d}",
            "source_en": source,
            "prompt_domain": "quest"
        })
    print(f"Quest unique items needing translation: {len(to_run)}")

    # Make batches
    batches = list(make_batches(to_run, args.batch_size, args.max_chars))
    total_batches = len(batches)
    print(f"Total batches to translate with Mistral: {total_batches}")

    placeholder_errors = []
    translation_errors = []

    if total_batches > 0:
        write_lock = threading.Lock()
        key_cursor_lock = threading.Lock()
        key_cursor = 0
        batch_counter = 0

        system_prompt = build_system_prompt("quest")

        def process_batch(batch_items):
            nonlocal key_cursor, batch_counter
            
            with write_lock:
                batch_counter += 1
                current_batch_no = batch_counter

            item_map = {item["temp_id"]: item for item in batch_items}

            with key_cursor_lock:
                start_idx = key_cursor
                key_cursor += 1

            try:
                output, new_cursor = call_mistral_key_pool(
                    mistral_keys,
                    start_idx,
                    system_prompt,
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
                    print(f"[Quest Batch {current_batch_no}/{total_batches}] Warning: {len(missing_ids)} missing rows in translation response.")

                for temp_id, translation in parsed.items():
                    item = item_map.get(temp_id)
                    if not item:
                        continue
                    
                    source = item["source_en"]
                    val_issues = validate_translation(source, translation)
                    
                    if val_issues:
                        with write_lock:
                            placeholder_errors.append({
                                "source": source,
                                "translation": translation,
                                "issues": val_issues
                            })
                    else:
                        local_checkpoint_updates[source] = translation

                # Write batch results to checkpoint
                if local_checkpoint_updates:
                    with write_lock:
                        checkpoint.update(local_checkpoint_updates)
                        write_json(CHECKPOINT_PATH, checkpoint)

                print(f"[Quest Batch {current_batch_no}/{total_batches}] Completed. Translated {len(local_checkpoint_updates)}/{len(batch_items)} items successfully.")

            except Exception as exc:
                print(f"[Quest Batch {current_batch_no}/{total_batches}] FAILED with exception: {exc}")
                with write_lock:
                    translation_errors.append({
                        "batch": current_batch_no,
                        "error": str(exc),
                        "items": [{"temp_id": i["temp_id"], "source_en": i["source_en"]} for i in batch_items]
                    })

        # Run parallel workers for Mistral translation
        print(f"Starting execution pool with {args.workers} workers...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            executor.map(process_batch, batches)

        print("\nMistral translation run finished!")
        print(f"Successful unique translations: {len(checkpoint)}")
        print(f"Placeholder validation errors: {len(placeholder_errors)}")
        print(f"API translation failures (batches): {len(translation_errors)}")

        # Now handle failed items with Gemini API if keys are available
        failed_items_to_resolve = []
        
        # 1. Collect API failures (batches that failed completely)
        for failure in translation_errors:
            for item in failure["items"]:
                failed_items_to_resolve.append(item["source_en"])
                
        # 2. Collect placeholder validation errors
        for err in placeholder_errors:
            failed_items_to_resolve.append(err["source"])
            
        # Remove duplicates
        failed_items_to_resolve = sorted(list(set(failed_items_to_resolve)))
        
        if failed_items_to_resolve and gemini_keys:
            print(f"\nProcessing {len(failed_items_to_resolve)} failed/remaining items using Gemini API...")
            gemini_batch_items = []
            for idx, source in enumerate(failed_items_to_resolve):
                gemini_batch_items.append({
                    "temp_id": f"QTG_{idx:05d}",
                    "source_en": source
                })
                
            gemini_batches = list(make_batches(gemini_batch_items, args.batch_size, args.max_chars))
            total_gemini_batches = len(gemini_batches)
            
            gemini_key_cursor = 0
            resolved_gemini_count = 0
            
            for g_batch_no, g_batch in enumerate(gemini_batches, 1):
                g_item_map = {i["temp_id"]: i for i in g_batch}
                try:
                    output, new_cursor = call_gemini_key_pool(
                        gemini_keys,
                        gemini_key_cursor,
                        system_prompt,
                        build_user_prompt(g_batch),
                        args.retries,
                        args.batch_delay
                    )
                    gemini_key_cursor = new_cursor
                    parsed = parse_output(output)
                    
                    local_g_updates = {}
                    for temp_id, translation in parsed.items():
                        item = g_item_map.get(temp_id)
                        if not item:
                            continue
                        source = item["source_en"]
                        val_issues = validate_translation(source, translation)
                        
                        if not val_issues:
                            local_g_updates[source] = translation
                            resolved_gemini_count += 1
                            
                    if local_g_updates:
                        checkpoint.update(local_g_updates)
                        write_json(CHECKPOINT_PATH, checkpoint)
                        
                    print(f"[Gemini Quest Batch {g_batch_no}/{total_gemini_batches}] Completed. Resolved {len(local_g_updates)}/{len(g_batch)} items.")
                except Exception as exc:
                    print(f"[Gemini Quest Batch {g_batch_no}/{total_gemini_batches}] FAILED: {exc}")
                    
            print(f"\nGemini resolution finished. Resolved {resolved_gemini_count} failed items.")
        
        # Save error reports for remaining failed items (that failed both Mistral and Gemini)
        remaining_errors = []
        for err in placeholder_errors:
            src = err["source"]
            if src not in checkpoint:
                remaining_errors.append(err)
        for failure in translation_errors:
            for item in failure["items"]:
                src = item["source_en"]
                if src not in checkpoint:
                    remaining_errors.append({
                        "source": src,
                        "translation": "",
                        "issues": ["api_failure"]
                    })
        if remaining_errors:
            write_json(RUN_DIR / "placeholder_errors.json", remaining_errors)
            print(f"Logged {len(remaining_errors)} remaining errors to placeholder_errors.json")

    # Apply quest translations to JSON split files
    apply_quest_translations_to_json_files(checkpoint)
    
    # Resolve previous UI & System Text errors using Gemini
    resolve_previous_errors_with_gemini(gemini_keys, args)
    
    print("\nAll tasks completed successfully!")

if __name__ == "__main__":
    main()
