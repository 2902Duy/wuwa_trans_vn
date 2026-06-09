import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
import concurrent.futures
import threading

# Thread-safe tracking of exhausted keys and exit signals
exhausted_gemini_keys = set()
exhausted_gemini_lock = threading.Lock()

exhausted_mistral_keys = set()
exhausted_mistral_lock = threading.Lock()

stop_event = threading.Event()

# Fix Windows console encoding issues for Vietnamese text
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
WORK_DIR = WORKSPACE_DIR / "mistral_translate_work"
PROMPT_DIR = WORK_DIR / "prompts_compressed"
STORY_DIR = WORK_DIR / "split_by_prompt" / "json" / "story_dialogue"

RUN_DIR = WORK_DIR / "reports" / "story_dialogue_run"
CHECKPOINT_PATH = RUN_DIR / "unique_translations.json"
ERRORS_PATH = RUN_DIR / "placeholder_errors.json"

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

def build_system_prompt():
    parts = []
    parts.append((PROMPT_DIR / "shared_glossary.md").read_text(encoding="utf-8"))
    parts.append((PROMPT_DIR / "keep_english_rules.md").read_text(encoding="utf-8"))
    if (PROMPT_DIR / "character_voice_map.md").exists():
        parts.append((PROMPT_DIR / "character_voice_map.md").read_text(encoding="utf-8"))
    parts.append((PROMPT_DIR / "story_dialogue_prompt.md").read_text(encoding="utf-8"))
    
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

def build_gemini_audit_prompt():
    parts = []
    parts.append((PROMPT_DIR / "shared_glossary.md").read_text(encoding="utf-8"))
    parts.append((PROMPT_DIR / "keep_english_rules.md").read_text(encoding="utf-8"))
    if (PROMPT_DIR / "character_voice_map.md").exists():
        parts.append((PROMPT_DIR / "character_voice_map.md").read_text(encoding="utf-8"))
    parts.append((PROMPT_DIR / "story_dialogue_prompt.md").read_text(encoding="utf-8"))
    
    parts.append(
        """
## Role: Quality Auditor (Lớp kiểm định chất lượng bản dịch)

You will receive a batch of English source lines and their corresponding Vietnamese translations generated by a machine translator.
Your task is to audit and correct the translations.

### Checklist:
1. **Untranslated Words:** Check if there are any words/phrases left in English that SHOULD be translated to Vietnamese. Correct them.
2. **Personal Pronoun mappings:** adult females like Changli, Taoqi, Yinlin xưng "Tôi" - gọi Rover là "cậu/em", avoiding "chị". Gender-neutral tone for Rover.
3. **Glossary/Keep English:** Ensure game terms (e.g. Echo, Resonator, Rover) are NOT translated, and matching tags/placeholders are preserved exactly.

Return the finalized translations in the exact same format:
ID:::Vietnamese translation

Do not explain. Do not include markdown. Only return the lines.
"""
    )
    return "\n\n".join(parts)

def call_gemini(api_key, system_prompt, user_prompt, retries, model="gemini-3.1-flash-lite"):
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
    delay = 3
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
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
                candidates = payload.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                raise RuntimeError(f"Unexpected response format: {payload}")
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
    raise RuntimeError("Gemini request failed")

def call_gemini_key_pool(keys, start_index, system_prompt, user_prompt, retries, batch_delay, model="gemini-3.1-flash-lite"):
    global exhausted_gemini_keys
    errors = []
    key_count = len(keys)
    
    for round_no in range(1, retries + 1):
        if stop_event.is_set():
            raise RuntimeError("stop_event_is_set")
            
        with exhausted_gemini_lock:
            available_indices = [i for i in range(key_count) if keys[i] not in exhausted_gemini_keys]
            
        if not available_indices:
            raise RuntimeError("all_keys_exhausted_daily_limit")
            
        num_avail = len(available_indices)
        for i in range(num_avail):
            key_index = available_indices[(start_index + i) % num_avail]
            try:
                output = call_gemini(keys[key_index], system_prompt, user_prompt, 1, model=model)
                if batch_delay:
                    time.sleep(batch_delay)
                return output, start_index + i + 1
            except Exception as exc:
                err_str = str(exc)
                errors.append({"round": round_no, "key_index": key_index, "error": err_str})
                
                # Check for daily limit quota exhaustion or permission issues
                if "limit: 500" in err_str or "limit: 1500" in err_str or "PERMISSION_DENIED" in err_str or "denied" in err_str.lower():
                    with exhausted_gemini_lock:
                        if keys[key_index] not in exhausted_gemini_keys:
                            exhausted_gemini_keys.add(keys[key_index])
                            print(f"\n[Gemini] Key index {key_index} marked as EXHAUSTED/DENIED. Active keys left: {key_count - len(exhausted_gemini_keys)}")
                continue
        if round_no < retries:
            time.sleep(5 * round_no)
    raise RuntimeError(json.dumps({"kind": "all_gemini_keys_failed", "errors": errors[-20:]}, ensure_ascii=False))

def call_mistral(api_key, system_prompt, user_prompt, retries, model="mistral-small-latest"):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 8192,
    }
    data = json.dumps(body).encode("utf-8")
    delay = 3
    for attempt in range(1, retries + 1):
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
            with urllib.request.urlopen(request, timeout=120) as response:
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

def call_mistral_key_pool(keys, start_index, system_prompt, user_prompt, retries, batch_delay, model="mistral-small-latest"):
    global exhausted_mistral_keys
    errors = []
    key_count = len(keys)
    
    for round_no in range(1, retries + 1):
        if stop_event.is_set():
            raise RuntimeError("stop_event_is_set")
            
        with exhausted_mistral_lock:
            available_indices = [i for i in range(key_count) if keys[i] not in exhausted_mistral_keys]
            
        if not available_indices:
            raise RuntimeError("all_mistral_keys_exhausted")
            
        num_avail = len(available_indices)
        for i in range(num_avail):
            key_index = available_indices[(start_index + i) % num_avail]
            try:
                output = call_mistral(keys[key_index], system_prompt, user_prompt, 1, model=model)
                if batch_delay:
                    time.sleep(batch_delay)
                return output, start_index + i + 1
            except Exception as exc:
                err_str = str(exc)
                errors.append({"round": round_no, "key_index": key_index, "error": err_str})
                
                # Check for quota limits / credit expiration
                if "401" in err_str or "403" in err_str or "limit" in err_str.lower():
                    if "rate" not in err_str.lower():
                        with exhausted_mistral_lock:
                            if keys[key_index] not in exhausted_mistral_keys:
                                exhausted_mistral_keys.add(keys[key_index])
                                print(f"\n[Mistral] Key index {key_index} marked as EXHAUSTED/DENIED. Active keys left: {key_count - len(exhausted_mistral_keys)}")
                continue
        if round_no < retries:
            time.sleep(5 * round_no)
    raise RuntimeError(json.dumps({"kind": "all_mistral_keys_failed", "errors": errors[-20:]}, ensure_ascii=False))

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

def clean_translation_formatting(source, translation):
    source = source.strip()
    translation = translation.strip()
    
    # Strip leading colons if source doesn't start with colon
    if translation.startswith(":") and not source.startswith(":"):
        translation = translation.lstrip(":").strip()
        
    # Strip leading exclamation mark if it leaked from sequence bias
    if translation.startswith("!") and not source.startswith("!"):
        if translation.startswith("!\"") and not source.startswith("\""):
            translation = translation[1:].strip()
        elif translation.startswith("!*") and not source.startswith("*"):
            translation = translation[1:].strip()
            
    # Auto-restore translated glossary terms and locations
    replacements = [
        ("Hẻm Núi Linh Hồn", "Gorges of Spirits"), ("Hẻm núi Linh Hồn", "Gorges of Spirits"), ("Hẻm núi Spirit", "Gorges of Spirits"),
        ("Thủy Triều Hắc Ám", "Dark Tide"), ("Thủy triều Hắc Ám", "Dark Tide"), ("Hắc Triều", "Dark Tide"),
        ("Thủy Triều High", "High Tide"), ("Triều High", "High Tide"),
        ("Rừng Mờ", "Dim Forest"), ("Rừng Tối", "Dim Forest"), ("Khu Rừng Mù Sương", "Dim Forest"), ("Rừng Mù Sương", "Dim Forest"),
        ("Cao nguyên Desorock", "Desorock Highland"), ("Cao Nguyên Desorock", "Desorock Highland"),
        ("Núi Vòm Trời", "Mt. Firmament"), ("Trầm Minh Khánh", "Mt. Firmament"), ("Núi Firmament", "Mt. Firmament"),
        ("Hồng Trấn", "Hongzhen"),
        ("Ngõ Tối", "Black Alley"), ("Hẻm Đen", "Black Alley"),
        ("Vịt Bất Diệt", "Impermanence Heron"), ("Vịt bất diệt", "Impermanence Heron"),
        ("Chim Than Vãn Aix", "Mourning Aix"), ("Than Vãn Aix", "Mourning Aix"),
        ("Quả Cầu Sonoro", "Sonoro Sphere"), ("Quả cầu Sonoro", "Sonoro Sphere"),
        ("Nghệ sĩ Sáo", "Flautist"), ("Nghệ Sĩ Sáo", "Flautist"),
        ("Kim Châu", "Jinzhou"),
        ("Mạch Forte", "Forte Circuit"), ("Chuỗi Forte", "Forte Circuit"),
        ("Giải Phóng Cộng Hưởng", "Resonance Liberation"), ("Giải phóng Cộng hưởng", "Resonance Liberation"),
        ("Kỹ Năng Cộng Hưởng", "Resonance Skill"), ("Kỹ năng Cộng hưởng", "Resonance Skill"),
        ("Người Cộng Hưởng", "Resonator"), ("Cộng Hưởng Giả", "Resonator"),
        ("Linh Thú", "Echo"), ("Tiếng Vang", "Echo"),
        ("Nhà Lữ Hành", "Rover"), ("Vãng Minh Giả", "Rover"), ("Viễn Khách", "Rover"),
    ]
    
    for vi_term, en_term in replacements:
        if en_term.lower() in source.lower():
            if vi_term in translation:
                translation = translation.replace(vi_term, en_term)
                
    return translation

def scan_and_collect_unique_stories():
    import random
    story_sources = set()
    for path in STORY_DIR.rglob("*.json"):
        for row in read_json(path):
            source = row.get("source_en", "")
            if source:
                story_sources.add(source)
    sources_list = sorted(story_sources)
    # Deterministic shuffle using a fixed seed to break list-based LLM sequence bias
    rng = random.Random(42)
    rng.shuffle(sources_list)
    return sources_list

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

def build_gemini_user_prompt(batch, mistral_translations):
    lines = []
    for item in batch:
        temp_id = item['temp_id']
        source = item['source_en']
        translation = mistral_translations.get(temp_id, "")
        lines.append(f"SOURCE_{temp_id}:::{normalize(source)}")
        lines.append(f"TRANSLATION_{temp_id}:::{normalize(translation)}")
    return "\n".join(lines)

def parse_gemini_audit_output(output):
    parsed = {}
    current_id = None
    for line in output.splitlines():
        match = ROW_RE.match(line)
        if match:
            current_id = match.group(1)
            # Remove TRANSLATION_ prefix if returned by Gemini
            if current_id.startswith("TRANSLATION_"):
                current_id = current_id[len("TRANSLATION_"):]
            elif current_id.startswith("SOURCE_"):
                # Avoid appending subsequent non-matching lines to the SOURCE_ ID
                current_id = None
                continue
            parsed[current_id] = match.group(2).strip()
        elif current_id and line.strip():
            parsed[current_id] += "\n" + line.rstrip()
    return parsed

def apply_story_translations_to_json_files(all_translations):
    print("\nApplying story dialogue translations back to JSON split files...")
    story_files = list(STORY_DIR.rglob("*.json"))
    for path in story_files:
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
    print("Done applying translations.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=80)
    parser.add_argument("--max-chars", type=int, default=15000)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--batch-delay", type=float, default=0.5)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--mistral-model", type=str, default="mistral-small-latest")
    parser.add_argument("--gemini-model", type=str, default="gemini-3.1-flash-lite")
    parser.add_argument("--force-retranslate", action="store_true")
    parser.add_argument("--limit-batches", type=int, default=None, help="Limit number of batches to run (for testing)")
    args = parser.parse_args()

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    
    mistral_keys = load_mistral_keys()
    gemini_keys = load_gemini_keys()
    
    if not mistral_keys:
        raise RuntimeError("No Mistral API keys found in .env.")
    if not gemini_keys:
        raise RuntimeError("No Gemini API keys found in .env.")
        
    print(f"Loaded {len(mistral_keys)} Mistral API keys.")
    print(f"Loaded {len(gemini_keys)} Gemini API keys.")

    # Checkpoint handling
    checkpoint = {}
    if CHECKPOINT_PATH.exists() and not args.force_retranslate:
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            print(f"Loaded story dialogue checkpoint with {len(checkpoint)} unique translations.")
        except Exception as exc:
            print(f"Error loading checkpoint: {exc}. Starting fresh.")
            checkpoint = {}
    elif args.force_retranslate:
        if CHECKPOINT_PATH.exists():
            backup_path = CHECKPOINT_PATH.with_suffix(".backup")
            CHECKPOINT_PATH.replace(backup_path)
            print(f"Backed up existing checkpoint to {backup_path}")
        checkpoint = {}

    # Scan unique story lines
    print("Scanning story dialogue directories...")
    story_sources = scan_and_collect_unique_stories()
    print(f"Total Unique Story Lines: {len(story_sources)}")

    # Filter untranslated
    to_run = []
    for idx, source in enumerate(story_sources):
        if source in checkpoint:
            continue
        to_run.append({
            "temp_id": f"SD_{idx:06d}",
            "source_en": source
        })
    print(f"Unique story lines needing translation: {len(to_run)}")

    if not to_run:
        print("All story dialogue lines are already translated in checkpoint!")
        apply_story_translations_to_json_files(checkpoint)
        return

    # Make batches
    batches = list(make_batches(to_run, args.batch_size, args.max_chars))
    if args.limit_batches is not None:
        batches = batches[:args.limit_batches]
    total_batches = len(batches)
    print(f"Total batches to translate: {total_batches}")

    placeholder_errors = []
    translation_errors = []

    write_lock = threading.Lock()
    key_cursor_lock = threading.Lock()
    key_cursor = 0
    batch_counter = 0

    mistral_system_prompt = build_system_prompt()
    gemini_audit_prompt = build_gemini_audit_prompt()

    def process_batch(batch_items):
        nonlocal key_cursor, batch_counter
        
        if stop_event.is_set():
            return
            
        with write_lock:
            batch_counter += 1
            current_batch_no = batch_counter

        item_map = {item["temp_id"]: item for item in batch_items}

        with key_cursor_lock:
            start_idx = key_cursor
            key_cursor += 1

        try:
            # 1. Translate with Mistral
            mistral_output, new_cursor = call_mistral_key_pool(
                mistral_keys,
                start_idx,
                mistral_system_prompt,
                build_user_prompt(batch_items),
                args.retries,
                args.batch_delay,
                model=args.mistral_model,
            )
            
            with key_cursor_lock:
                key_cursor = max(key_cursor, new_cursor)

            mistral_parsed = parse_output(mistral_output)
            
            # 2. Audit and correct with Gemini 3.1
            gemini_user_prompt = build_gemini_user_prompt(batch_items, mistral_parsed)
            gemini_output, gemini_new_cursor = call_gemini_key_pool(
                gemini_keys,
                start_idx,
                gemini_audit_prompt,
                gemini_user_prompt,
                args.retries,
                args.batch_delay,
                model=args.gemini_model,
            )
            
            final_parsed = parse_gemini_audit_output(gemini_output)
            
            # Fallback to Mistral's translation if Gemini missed any keys
            for temp_id in item_map.keys():
                if temp_id not in final_parsed and temp_id in mistral_parsed:
                    final_parsed[temp_id] = mistral_parsed[temp_id]

            missing_ids = sorted(set(item_map.keys()) - set(final_parsed.keys()))
            local_checkpoint_updates = {}
            
            if missing_ids:
                print(f"[Batch {current_batch_no}/{total_batches}] Warning: {len(missing_ids)} missing rows in finalized response.")

            for temp_id, translation in final_parsed.items():
                item = item_map.get(temp_id)
                if not item:
                    continue
                
                source = item["source_en"]
                translation = clean_translation_formatting(source, translation)
                val_issues = validate_translation(source, translation)
                
                # Check for standard starting {0} issues and auto-fix
                if val_issues and "missing_token:{0}" in val_issues and source.startswith("{0}") and "{0}" not in translation:
                    translation = "{0} " + translation
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

            if current_batch_no % 10 == 0 or current_batch_no == total_batches:
                print(f"[Batch {current_batch_no}/{total_batches}] Completed. Progress: {len(checkpoint)}/{len(story_sources)} unique items translated.")

        except Exception as exc:
            err_msg = str(exc)
            if "all_keys_exhausted_daily_limit" in err_msg or "all_mistral_keys_exhausted" in err_msg or "stop_event_is_set" in err_msg:
                print(f"\n[Batch {current_batch_no}/{total_batches}] CRITICAL: API keys exhausted or stop requested. Stopping worker thread. Error: {exc}")
                stop_event.set()
                return
                
            print(f"[Batch {current_batch_no}/{total_batches}] FAILED with exception: {exc}")
            with write_lock:
                translation_errors.append({
                    "batch": current_batch_no,
                    "error": str(exc),
                    "items": [{"temp_id": i["temp_id"], "source_en": i["source_en"]} for i in batch_items]
                })

    # Run parallel workers
    print(f"Starting execution pool with {args.workers} workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        executor.map(process_batch, batches)

    print("\nHybrid Mistral-Gemini translation and audit run finished!")
    print(f"Successful unique translations: {len(checkpoint)}")
    print(f"Placeholder validation errors: {len(placeholder_errors)}")
    print(f"API translation failures (batches): {len(translation_errors)}")

    # Log remaining errors
    if placeholder_errors or translation_errors:
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
            write_json(ERRORS_PATH, remaining_errors)
            print(f"Logged {len(remaining_errors)} errors to placeholder_errors.json")

    # Apply translations to JSON files
    apply_story_translations_to_json_files(checkpoint)
    print("\nAll tasks completed successfully!")

if __name__ == "__main__":
    main()
