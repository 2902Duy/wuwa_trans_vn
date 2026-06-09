"""
translate_gemini_gemma_parallel.py
===================================
Dịch song song UI + item + system_text bằng Gemma 26B A4B + 31B.

- system_text = toàn bộ tên quái vật/boss → auto keep-english, KHÔNG gửi LLM
- Prompt gọn, không nhúng domain rules nặng
- Parser linh hoạt xử lý bullet/arrow output của Gemma
- Round-robin key + model pool
- Flush mỗi 3 batch để không mất dữ liệu
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import threading
import concurrent.futures
from pathlib import Path

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
WORK_DIR = WORKSPACE_DIR / "mistral_translate_work"

TARGET_DIRS = {
    "ui":                  WORK_DIR / "split_by_prompt" / "json" / "ui",
    "item":                WORK_DIR / "split_by_prompt" / "json" / "item",
    "system_text":         WORK_DIR / "split_by_prompt" / "json" / "system_text",
    "quest":               WORK_DIR / "split_by_prompt" / "json" / "quest",
    "lore":                WORK_DIR / "split_by_prompt" / "json" / "lore",
    "story_dialogue":      WORK_DIR / "split_by_prompt" / "json" / "story_dialogue",
    "skill_description":   WORK_DIR / "split_by_prompt" / "json" / "skill_description",
    "name_title":          WORK_DIR / "split_by_prompt" / "json" / "name_title",
    "weapon":              WORK_DIR / "split_by_prompt" / "json" / "weapon",
    "rc_description":      WORK_DIR / "split_by_prompt" / "json" / "rc_description",
    "monster_description": WORK_DIR / "split_by_prompt" / "json" / "monster_description",
    "echo_set":            WORK_DIR / "split_by_prompt" / "json" / "echo_set",
    "phantom_skill":       WORK_DIR / "split_by_prompt" / "json" / "phantom_skill",
}

# ── Compact system prompt (no heavy doc attachment) ───────────────────
SYSTEM_INSTR = """Bạn là dịch thuật viên game Wuthering Waves Việt hóa.

QUY TẮC:
- Dịch từng dòng sang tiếng Việt.
- Format output bắt buộc mỗi dòng: ID:::Bản dịch tiếng Việt
- KHÔNG thêm dấu gạch đầu dòng, markdown, giải thích, hay dòng thừa.
- Giữ nguyên tiếng Anh: Echo, Resonator, Rover, DMG, ATK, DEF, HP, STA, Waveplate, Astrite, Resonance Skill, Resonance Liberation, Forte Circuit, Concerto Energy.
- Giữ nguyên tên Boss/Quái vật: Crownless, Dreamless, Impermanence Heron, Vanguard Junrock, Inferno Rider, v.v.
- Giữ nguyên tags: {0}, {PlayerName}, <color=#...>, \\n, {Cus:Ipt,...}
- Số nguyên và ký hiệu đặc biệt → sao chép nguyên xi.
- TUYỆT ĐỐI không dùng "mày", "tao". Kẻ thù: "ta"/"ngươi". Đồng minh: "cậu"/"tôi".

Thuật ngữ UI hay dùng:
Confirm→Xác nhận | Cancel→Hủy | Back→Quay lại | Claim→Nhận | Claimed→Đã nhận
Equip→Trang bị | Unlock→Mở khóa | Settings→Cài đặt | Exit→Thoát | Skip→Bỏ qua
Completed→Đã hoàn thành | Obtained→Nhận được | Apply→Áp dụng | Refresh→Làm mới
Shop→Cửa hàng | Inventory→Kho đồ | Level Up→Nâng cấp | Upgrade→Nâng cấp
High→Cao | Medium→Trung bình | Low→Thấp | On→Bật | Off→Tắt"""

FEW_SHOT_PREFIX = """Dưới đây là các dòng cần dịch. Chỉ xuất kết quả dạng ID:::Bản dịch, mỗi dòng một bản dịch:

"""

# ── Keep-English detection ────────────────────────────────────────────
KEEP_EN_TERMS = {
    "Resonance Chain", "Resonance Skill", "Resonance Liberation", "Forte Circuit",
    "Concerto Energy", "Resonance Energy", "Echo", "Resonator", "Rover",
    "Basic Attack", "Normal Attack", "Heavy Attack", "Mid-air Attack",
    "Dodge Counter", "Intro Skill", "Outro Skill", "Inherent Skill",
    "DMG", "DMG Bonus", "Crit. Rate", "Crit. DMG", "ATK", "DEF", "HP",
    "STA", "Waveplate", "Astrite", "Lunite", "Shell Credit",
    "Lustrous Tide", "Radiant Tide", "Forging Tide",
    "Aero Erosion", "Glacio Chafe", "Spectro Frazzle", "Havoc Bane",
    "Fusion Burst", "Electro Flare", "Tidal Blight", "Negative Status",
    "Crownless", "Dreamless", "Impermanence Heron", "Mourning Aix",
    "Tempest Mephis", "Thundering Mephis", "Inferno Rider",
    "Feilian Beringal", "Bell-Borne Geochelone", "Fallacy of No Return",
    "Sentinel", "Jué", "Vanguard Junrock", "Fission Junrock",
    "Exile Commoner", "Exile Craftsman", "Exile Technician",
    "Aero Prism", "Glacio Prism", "Fusion Prism", "Havoc Prism",
    "Spectro Prism", "Electro Prism",
    "Sierra Gale", "Void Thunder", "Molten Rift", "Freezing Frost",
    "Lingering Tunes", "Sun-sinking Eclipse", "Celestial Light",
    "Rejuvenating Glow", "Moonlit Clouds", "Eternal Radiance",
    "Midnight Veil", "Frosty Resolve",
    "Tacet Field", "Tacet Discord", "Modulation",
}

NUMERIC_RE = re.compile(r"^\d+$")

_COMMON_EN = {
    'the','a','an','is','are','was','to','for','and','or','but',
    'in','on','at','by','with','from','of','that','this','your',
    'you','all','not','be','can','will','has','have','do','does',
    'its','it','if','as','up','out','so','no','into','about',
    'get','use','set','yes','now','here','please','tap','press','click',
    
    # Common UI & system actions/nouns
    'notice', 'exit', 'cancel', 'back', 'confirm', 'retry', 'continue', 'submit', 'ok', 
    'agree', 'accept', 'decline', 'close', 'open', 'save', 'load', 'settings', 'options', 
    'help', 'info', 'about', 'play', 'pause', 'stop', 'quit', 'download', 'install', 
    'update', 'check', 'search', 'find', 'select', 'delete', 'remove', 'clear', 'reset', 
    'default', 'mail', 'friend', 'blocklist', 'apply', 'refresh', 'shop', 'inventory', 
    'equip', 'unequip', 'lock', 'unlock', 'view', 'hide', 'show', 'share', 'claim', 
    'claimed', 'completed', 'obtained', 'success', 'failed', 'warning', 'error',
    'loading', 'connecting', 'patching', 'verifying', 'repair', 'repairing', 'status',
    'progress', 'speed', 'size', 'storage', 'space', 'network', 'internet', 'driver',
    'version', 'resource', 'resources', 'downloading', 'installing', 'next', 'prev',
    'previous', 'title', 'mode', 'resolution', 'volume', 'sound', 'music', 'graphics',
    'screen', 'display', 'language', 'account', 'password', 'login', 'logout', 'register',
    'connect', 'disconnect', 'online', 'offline', 'server', 'client', 'patch', 'file',
    'files', 'folder', 'directory', 'path', 'verify', 'integrity', 'checking',
}

def _is_proper_noun_sysfile(s: str) -> bool:
    """True if string is a proper noun (boss/monster name), not a system message."""
    s = s.strip()
    if not re.search(r'[a-zA-Z]', s): return True   # number/symbol only
    if re.search(r'[\{\[\(]', s): return False        # has placeholder = system message
    if len(s) > 50: return False                      # too long = sentence
    if '.' in s or ',' in s: return False             # punctuation = sentence
    words = s.split()
    if len(words) > 5: return False
    alpha = [w for w in words if re.match(r'^[A-Za-z]+$', w)]
    if not alpha: return True
    if not all(w[0].isupper() for w in alpha): return False
    if any(w.lower() in _COMMON_EN for w in alpha): return False
    return True

def _load_system_text_terms():
    """Load ONLY proper nouns (boss/monster names) from system_text into KEEP_EN_TERMS."""
    sysdir = (Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
              / "mistral_translate_work" / "split_by_prompt" / "json" / "system_text")
    if not sysdir.exists():
        return
    for f in sysdir.rglob("*.json"):
        try:
            rows = json.loads(f.read_text(encoding="utf-8"))
            for row in rows:
                src = row.get("source_en", "").strip()
                if src and _is_proper_noun_sysfile(src):
                    KEEP_EN_TERMS.add(src)
        except Exception:
            pass

def _load_glossary_terms():
    """Load terms from shared_glossary.md into KEEP_EN_TERMS."""
    glossary_path = WORKSPACE_DIR / "mistral_translate_work" / "split_by_prompt" / "ui_translation_pack" / "shared_glossary.md"
    if not glossary_path.exists():
        return
    with open(glossary_path, "r", encoding="utf-8") as f:
        in_section = False
        for line in f:
            if "## THUẬT NGỮ BẮT BUỘC GIỮ NGUYÊN TIẾNG ANH" in line:
                in_section = True
                continue
            if "## Ví dụ về các dịch sai cần tránh" in line:
                in_section = False
                break
            if in_section:
                if "->" in line:
                    continue
                found = re.findall(r"`([^`]+)`", line)
                for term in found:
                    if "," in term:
                        subterms = [t.strip() for t in term.split(",")]
                        for st in subterms:
                            if st:
                                KEEP_EN_TERMS.add(st)
                    else:
                        if term.strip():
                            KEEP_EN_TERMS.add(term.strip())

def _load_extracted_quest_terms():
    """Load extracted NPC names / proper nouns from extracted_names.json."""
    names_path = WORKSPACE_DIR / "mistral_translate_work" / "extracted_names.json"
    if names_path.exists():
        try:
            names = json.loads(names_path.read_text(encoding="utf-8"))
            for name in names:
                name_strip = name.strip()
                if name_strip:
                    KEEP_EN_TERMS.add(name_strip)
            print(f"  [Init] Loaded {len(names)} NPC/proper names from {names_path.name}")
        except Exception as e:
            print(f"  [ERROR] Failed to load extracted quest terms: {e}")

SORTED_KEEP_EN_TERMS = []

def initialize_keep_english_rules():
    global SORTED_KEEP_EN_TERMS
    _load_glossary_terms()
    _load_system_text_terms()
    _load_extracted_quest_terms()
    
    clean_terms = set()
    for t in KEEP_EN_TERMS:
        val = t.strip()
        if not val:
            continue
        if val.lower() in _COMMON_EN:
            continue
        clean_terms.add(val)
        
    KEEP_EN_TERMS.clear()
    KEEP_EN_TERMS.update(clean_terms)
    
    SORTED_KEEP_EN_TERMS = sorted(list(KEEP_EN_TERMS), key=len, reverse=True)
    print(f"  [Init] Loaded {len(SORTED_KEEP_EN_TERMS)} sorted Keep-English terms for replacement.")

def tag_sentence(text: str) -> tuple[str, dict]:
    placeholder_map = {}
    tagged_text = text
    counter = 0
    
    for term in SORTED_KEEP_EN_TERMS:
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        
        def replace_fn(match):
            nonlocal counter
            placeholder = f"{{KeepEN_{counter}}}"
            original_value = match.group(0)
            placeholder_map[placeholder] = original_value
            counter += 1
            return placeholder
            
        tagged_text = pattern.sub(replace_fn, tagged_text)
        
    return tagged_text, placeholder_map

def untag_sentence(tagged_text: str, placeholder_map: dict) -> str:
    text = tagged_text
    for placeholder, original_value in placeholder_map.items():
        text = text.replace(placeholder, original_value)
    return text

def is_keep_english(source: str) -> bool:
    s = source.strip()
    if NUMERIC_RE.match(s): return True
    if not re.search(r"[a-zA-Z]", s): return True
    if s in KEEP_EN_TERMS: return True
    if len(s) <= 6 and s.isupper() and s.isalpha(): return True
    return False

# ── Flexible output parser ────────────────────────────────────────────
_ID_PAT = r"([A-Z0-9_]+_\d+)"
# Standard or bullet:  [spaces/*/`]  ID:::text
ROW_RE   = re.compile(r"^[\s*`]*" + _ID_PAT + r":::(.*?)(?:`.*)?$")
# Arrow format (26B):  [spaces/*/`]  ID:::English`? -> Vietnamese
ARROW_RE = re.compile(r"^[\s*`]*" + _ID_PAT + r":::[^>]*?`?\s*->\s*(.+)$")

def parse_output(text: str) -> dict:
    result = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Arrow format first (26B): ID:::EN -> VI
        m = ARROW_RE.match(line)
        if m:
            sid, vi = m.group(1), m.group(2).strip().rstrip('`').strip()
            if sid and vi:
                result[sid] = vi
            continue
        # Standard / bullet format: ID:::VI
        m = ROW_RE.match(line)
        if m:
            sid, vi = m.group(1), m.group(2).strip().rstrip('`').strip()
            if sid and vi:
                result[sid] = vi
    return result

def get_system_instruction(domain: str) -> str:
    prompt_file_map = {
        "ui": "ui_prompt.md",
        "item": "item_prompt.md",
        "system_text": "system_text_prompt.md",
        "quest": "quest_prompt.md",
        "lore": "lore_prompt.md",
        "story_dialogue": "story_dialogue_prompt.md",
        "name_title": "name_title_prompt.md",
        "weapon": "weapon_prompt.md",
        "skill_description": "skill_description_prompt.md",
        "phantom_skill": "phantom_skill_prompt.md",
        "rc_description": "rc_description_prompt.md",
        "echo_set": "echo_set_prompt.md",
        "monster_description": "monster_description_prompt.md",
    }
    prompt_name = prompt_file_map.get(domain, "ui_prompt.md")
    prompt_path = WORKSPACE_DIR / "mistral_translate_work" / "prompts" / prompt_name
    specific_rules = ""
    if prompt_path.exists():
        try:
            specific_rules = prompt_path.read_text(encoding="utf-8")
        except Exception:
            pass
    combined_instr = f"""Bạn là dịch thuật viên game Wuthering Waves Việt hóa chuyên nghiệp.

QUY TẮC PHÂN VÙNG:
{specific_rules}

QUY TẮC ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (QUAN TRỌNG):
- Dịch từng dòng sang tiếng Việt.
- Format output bắt buộc mỗi dòng: ID:::Bản dịch tiếng Việt
- KHÔNG thêm dấu gạch đầu dòng, markdown, giải thích, hay dòng thừa.
- Giữ nguyên tiếng Anh cho các từ có dạng {{KeepEN_X}} (ví dụ: {{KeepEN_0}}, {{KeepEN_1}}).
- Giữ nguyên tags: {{0}}, {{PlayerName}}, <color=#...>, \\n, v.v.
- Số nguyên và ký hiệu đặc biệt → sao chép nguyên xi.
- TUYỆT ĐỐI không dùng xưng hô "mày", "tao" thô lỗ.
"""
    return combined_instr

# ── API call ──────────────────────────────────────────────────────────
def call_api(api_key: str, batch_text: str, model: str, system_instr: str,
             timeout: int = 90) -> str:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={api_key}")
    user_prompt = FEW_SHOT_PREFIX + batch_text
    body = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instr}]},
        "generationConfig": {"temperature": 0.05, "maxOutputTokens": 8192},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    delay = 5
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                candidates = payload.get("candidates", [])
                if candidates:
                    parts_out = candidates[0].get("content", {}).get("parts", [])
                    if parts_out:
                        return parts_out[0].get("text", "")
                raise RuntimeError(f"Empty response: {payload}")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code == 403:
                raise RuntimeError(f"PERMISSION_DENIED: {detail}") from exc
            if exc.code == 429:
                wait = delay * (2 ** attempt)
                print(f"  [429] Rate limit, waiting {wait}s...")
                time.sleep(wait); continue
            if exc.code in {500, 502, 503, 504} and attempt < 3:
                time.sleep(delay); continue
            raise RuntimeError(f"HTTP {exc.code}: {detail[:200]}") from exc
        except Exception as exc:
            if attempt >= 3: raise
            time.sleep(delay)
    raise RuntimeError("Max retries exceeded")

# ── Key-model pool ────────────────────────────────────────────────────
def load_keys() -> list:
    keys = []
    env_path = WORKSPACE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            name, value = line.split("=", 1)
            if name.strip() in {"GEMINI_API_KEYS", "GEMINI_API_KEY"}:
                keys.extend(p.strip() for p in value.strip().strip('"\'').split(","))
    seen, out = set(), []
    for k in keys:
        if k and k not in seen:
            seen.add(k); out.append(k)
    return out

class SlotPool:
    MODELS = ["gemini-3.1-flash-lite"]

    def __init__(self, keys: list):
        self.slots = [(k, m) for k in keys for m in self.MODELS]
        self._lock = threading.Lock()
        self._cursor = 0
        self._exhausted: set = set()

    def next_slot(self):
        with self._lock:
            avail = [(k, m) for k, m in self.slots if k not in self._exhausted]
            if not avail: return None, None
            k, m = avail[self._cursor % len(avail)]
            self._cursor += 1
            return k, m

    def mark_exhausted(self, key: str):
        with self._lock:
            self._exhausted.add(key)
            remaining = len({k for k, _ in self.slots} - self._exhausted)
            print(f"  [Pool] Key exhausted. Active keys: {remaining}")

# ── Batch translation ─────────────────────────────────────────────────
def translate_batch(pool: SlotPool, batch: list, system_instr: str) -> dict:
    # Pre-tag each row's source text
    tagged_batch = []
    maps = {}
    for r in batch:
        tagged_text, p_map = tag_sentence(r["source_en"])
        tagged_batch.append({
            "split_id": r["split_id"],
            "source_en": tagged_text
        })
        maps[r["split_id"]] = p_map

    batch_text = "\n".join(f"{r['split_id']}:::{r['source_en']}" for r in tagged_batch)

    last_err = None
    for _ in range(min(len(pool.slots), 6)):
        key, model = pool.next_slot()
        if key is None:
            raise RuntimeError("All API keys exhausted.")
        try:
            raw = call_api(key, batch_text, model, system_instr)
            parsed = parse_output(raw)
            # Untag translations and handle fallback
            result = {}
            for r in batch:
                sid = r["split_id"]
                p_map = maps[sid]
                if sid in parsed:
                    translated_tagged = parsed[sid]
                    result[sid] = untag_sentence(translated_tagged, p_map)
                else:
                    result[sid] = r["source_en"]
            return result
        except RuntimeError as exc:
            err = str(exc)
            if "PERMISSION_DENIED" in err:
                pool.mark_exhausted(key); continue
            last_err = exc
            print(f"  [WARN] {model}: {str(exc)[:80]}")
            time.sleep(3)
    raise RuntimeError(f"All slots failed: {last_err}")

# ── Domain runners ────────────────────────────────────────────────────
def collect_untranslated(domain: str, only_empty: bool = False) -> list:
    items = []
    for path in sorted(TARGET_DIRS[domain].rglob("*.json")):
        rows = json.loads(path.read_text(encoding="utf-8"))
        for idx, row in enumerate(rows):
            src = row.get("source_en", "")
            vi = row.get("new_translation_vi", "")
            if not src: continue
            if only_empty:
                if vi: continue
            else:
                if vi and vi != src: continue
            if is_keep_english(src): continue
            items.append({
                "file": path, "row_index": idx,
                "split_id": row.get("split_id", f"{domain.upper()}_{idx:07d}"),
                "source_en": src,
            })
    return items

def apply_keep_english(domain: str) -> int:
    changed = 0
    for path in sorted(TARGET_DIRS[domain].rglob("*.json")):
        rows = json.loads(path.read_text(encoding="utf-8"))
        modified = False
        for row in rows:
            src = row.get("source_en", "")
            vi = row.get("new_translation_vi", "")
            if src and (not vi or vi == src) and is_keep_english(src):
                row["new_translation_vi"] = src
                row["status"] = "keep_english"
                modified = True
        if modified:
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
            changed += 1
    return changed

def flush_writes(pending: dict):
    for path, idx_map in pending.items():
        rows = json.loads(path.read_text(encoding="utf-8"))
        for idx, vi in idx_map.items():
            rows[idx]["new_translation_vi"] = vi
            rows[idx]["status"] = "translated"
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

def run_domain(domain: str, pool: SlotPool, batch_size: int,
               workers: int, batch_delay: float, only_empty: bool = False):
    print(f"\n{'='*60}\n  Domain: {domain.upper()}\n{'='*60}")
    ke = apply_keep_english(domain)
    print(f"  Auto keep-English: {ke} files.")
    items = collect_untranslated(domain, only_empty)
    print(f"  Rows for LLM: {len(items)}")
    if not items:
        print("  ✓ Nothing to translate.")
        return

    system_instr = get_system_instruction(domain)
    batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
    print(f"  Batches: {len(batches)} × {batch_size}")

    lock = threading.Lock()
    pending: dict = {}
    counters = {"done": 0, "errors": 0}

    def process(args):
        batch, bno = args
        try:
            translations = translate_batch(pool, batch, system_instr)
            if batch_delay: time.sleep(batch_delay)
            with lock:
                for r in batch:
                    vi = translations.get(r["split_id"], "")
                    if vi:
                        pending.setdefault(r["file"], {})[r["row_index"]] = vi
                counters["done"] += len(batch)
                total = len(items)
                if bno % 5 == 0 or bno == len(batches):
                    print(f"  [{domain}] {bno}/{len(batches)} done — {counters['done']}/{total} rows")
        except Exception as exc:
            with lock:
                counters["errors"] += 1
            print(f"  [{domain}] Batch {bno} FAILED: {exc}")

    # Write every N batches to avoid losing progress
    FLUSH_EVERY = 3
    batch_args = [(b, i+1) for i, b in enumerate(batches)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(process, arg): arg for arg in batch_args}
        done_count = 0
        for f in concurrent.futures.as_completed(futures):
            done_count += 1
            if done_count % FLUSH_EVERY == 0:
                with lock:
                    flush_writes(dict(pending))
                    pending.clear()

    flush_writes(pending)
    print(f"  [{domain}] Done ✓  translated={counters['done']}  errors={counters['errors']}")

# ── Entry point ───────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size",  type=int,   default=25)
    parser.add_argument("--workers",     type=int,   default=10)
    parser.add_argument("--batch-delay", type=float, default=0.3)
    parser.add_argument("--domains", nargs="+",
                        default=["ui", "item", "system_text", "quest", "lore"],
                        choices=["ui", "item", "system_text", "quest", "lore", "story_dialogue",
                                 "skill_description", "name_title", "weapon", "rc_description",
                                 "monster_description", "echo_set", "phantom_skill"])
    parser.add_argument("--only-empty",  action="store_true", help="Only translate rows with empty new_translation_vi")
    args = parser.parse_args()

    keys = load_keys()
    if not keys:
        raise RuntimeError("No API keys found in .env")

    pool = SlotPool(keys)
    print(f"Keys: {len(keys)} × {len(SlotPool.MODELS)} models = {len(pool.slots)} slots")
    print(f"Models: {', '.join(SlotPool.MODELS)}")
    print(f"Domains: {args.domains}  batch={args.batch_size}  workers={args.workers}  only-empty={args.only_empty}")

    initialize_keep_english_rules()

    for domain in args.domains:
        if not TARGET_DIRS[domain].exists():
            print(f"\nSkipping {domain} — not found.")
            continue
        run_domain(domain, pool, args.batch_size, args.workers, args.batch_delay, args.only_empty)

    print("\n✅ All done!")

if __name__ == "__main__":
    main()
