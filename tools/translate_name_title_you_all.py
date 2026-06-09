import argparse
import concurrent.futures
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "mistral_translate_work" / "reports" / "name_title_english_audit"
OUTPUT_DIR = ROOT / "outputs" / "name_title_audit" / "you_all"
CHECKPOINT_PATH = OUTPUT_DIR / "translations_checkpoint.json"
RESULT_PATH = OUTPUT_DIR / "translations_all.json"
API_URL = "https://api.you.com/v1/agents/runs"

REPORT_FILES = (
    ("Not Translated", "english_not_translated_exact.json"),
    ("Not Translated", "english_not_translated_no_vietnamese.json"),
    ("Mixed Unauthorized", "mixed_english_vietnamese_unauthorized.json"),
)
TOKEN_PATTERNS = (
    r"\{[^{}]+\}",
    r"<[^<>]+>",
    r"\\[nrt]",
    r"\[[^\[\]]+\]",
)


def load_env_key() -> str:
    key = os.environ.get("YDC_API_KEY", "").strip()
    if key:
        return key
    env_path = ROOT / ".env"
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "YDC_API_KEY":
            key = value.strip().strip("'\"")
            if key:
                return key
    raise RuntimeError("YDC_API_KEY is missing or empty")


def load_rows() -> list[dict]:
    rows = []
    seen = set()
    for group, file_name in REPORT_FILES:
        report = json.loads((REPORT_DIR / file_name).read_text(encoding="utf-8"))
        for row in report["rows"]:
            split_id = row["split_id"]
            if split_id in seen:
                continue
            seen.add(split_id)
            rows.append({**row, "audit_group": group})
    return rows


def load_checkpoint() -> dict:
    if not CHECKPOINT_PATH.exists():
        return {}
    data = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    return data.get("translations", {})


def write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    for attempt in range(8):
        temp.write_text(content, encoding="utf-8")
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            if attempt == 7:
                # Some Windows indexers briefly lock the destination. A direct
                # rewrite is preferable to losing an otherwise valid checkpoint.
                path.write_text(content, encoding="utf-8")
                temp.unlink(missing_ok=True)
                return
            time.sleep(0.25 * (attempt + 1))


def protected_tokens(text: str) -> list[str]:
    tokens = []
    for pattern in TOKEN_PATTERNS:
        tokens.extend(re.findall(pattern, text or ""))
    return tokens


def make_batches(rows: list[dict], batch_size: int, max_chars: int) -> list[list[dict]]:
    batches = []
    batch = []
    char_count = 0
    for row in rows:
        row_chars = len(row["source_en"]) + len(row.get("new_translation_vi", "")) + 100
        if batch and (len(batch) >= batch_size or char_count + row_chars > max_chars):
            batches.append(batch)
            batch = []
            char_count = 0
        batch.append(row)
        char_count += row_chars
    if batch:
        batches.append(batch)
    return batches


def build_prompt(rows: list[dict]) -> str:
    payload = [
        {
            "split_id": row["split_id"],
            "source_en": row["source_en"],
            "current_vi": row.get("new_translation_vi", ""),
        }
        for row in rows
    ]
    return f"""Translate these Wuthering Waves strings from English to Vietnamese.

Return ONLY one valid JSON object mapping each split_id to one final Vietnamese string.

Mandatory localization rules:
- Include every input split_id exactly once. Never alter IDs.
- Translate all ordinary English words and sentences naturally and completely.
- Keep proper names in English: characters, NPCs, locations, organizations, Echoes, monsters, weapons, sets, skills, events, and named game terms.
- Keep these system terms in English when present: Rover, Resonator, Echo, Resonance Chain, Forte Circuit, Resonance Skill, Resonance Liberation, Basic Attack, Normal Attack, Heavy Attack, Mid-air Attack, Dodge Counter, Intro Skill, Outro Skill, Inherent Skill, HP, ATK, DEF, DMG, Crit. Rate, Crit. DMG, Waveplate, Astrite, Lunite, Shell Credit, Concerto Energy, Resonance Energy.
- Preserve proper names inside translated phrases.
- Preserve placeholders, rich-text tags, bracketed named effects, escaped line breaks, numbers, punctuation, and meaningful prefixes/suffixes.
- Remove obvious developer-only test markers such as "test/" when they are not meaningful player-facing content.
- For pure proper nouns, output the source unchanged.
- Do not use Markdown fences, notes, citations, or explanations.
- Use concise game-quality Vietnamese. Fix any mixed English/Vietnamese in current_vi instead of copying it.

Examples:
{{"A":"City Guard","B":"Yangyang","C":"Gain full [Chilling Vein]","D":"test/No description needed"}}
becomes:
{{"A":"Lính gác thành phố","B":"Yangyang","C":"Nhận đầy [Chilling Vein]","D":"Không cần mô tả"}}

Input:
{json.dumps(payload, ensure_ascii=False)}
"""


def extract_answer(response: dict) -> str:
    for item in reversed(response.get("output", [])):
        if item.get("type") == "message.answer" and isinstance(item.get("text"), str):
            return item["text"].strip()
    raise RuntimeError("Response has no message.answer")


def parse_json_answer(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise RuntimeError("Answer is not a JSON object")
    return value


def call_you(api_key: str, prompt: str, retries: int) -> dict:
    body = json.dumps(
        {"agent": "express", "input": prompt, "stream": False},
        ensure_ascii=False,
    ).encode("utf-8")
    delay = 3
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            API_URL,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "wuwa-name-title-full/1.0",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if attempt == retries or error.code not in {408, 429, 500, 502, 503, 504}:
                raise RuntimeError(f"You.com HTTP {error.code}: {detail[:500]}") from error
        except Exception:
            if attempt == retries:
                raise
        time.sleep(delay)
        delay = min(delay * 2, 30)
    raise RuntimeError("You.com request failed")


def translate_batch(api_key: str, rows: list[dict], retries: int) -> dict:
    response = call_you(api_key, build_prompt(rows), retries)
    translations = parse_json_answer(extract_answer(response))
    expected = {row["split_id"] for row in rows}
    actual = set(translations)
    if actual != expected:
        raise RuntimeError(
            f"ID mismatch missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
        )
    for split_id, translation in translations.items():
        source = next(row["source_en"] for row in rows if row["split_id"] == split_id)
        if isinstance(translation, str) and not translation.strip() and source.strip().lower() == "test/":
            translations[split_id] = source
            continue
        if not isinstance(translation, str) or not translation.strip():
            raise RuntimeError(f"Empty/non-string translation for {split_id}")
        translations[split_id] = translation.strip()
    return translations


def translate_with_split(api_key: str, rows: list[dict], retries: int) -> dict:
    try:
        return translate_batch(api_key, rows, retries)
    except Exception:
        if len(rows) == 1:
            raise
        middle = len(rows) // 2
        left = translate_with_split(api_key, rows[:middle], retries)
        right = translate_with_split(api_key, rows[middle:], retries)
        return {**left, **right}


def build_result(rows: list[dict], translations: dict) -> dict:
    result_rows = []
    stats = {
        "total": len(rows),
        "translated_changed": 0,
        "kept_unchanged": 0,
        "protected_token_mismatch": 0,
    }
    for row in rows:
        translation = translations[row["split_id"]]
        changed = translation.strip() != row["source_en"].strip()
        tokens_match = protected_tokens(row["source_en"]) == protected_tokens(translation)
        stats["translated_changed" if changed else "kept_unchanged"] += 1
        if not tokens_match:
            stats["protected_token_mismatch"] += 1
        qc_status = "PASS"
        qc_note = ""
        if not tokens_match:
            qc_status = "FAIL_TOKEN"
            qc_note = "Placeholder/tag/bracket token mismatch"
        elif row["source_en"].strip().lower() == "test/":
            qc_status = "REVIEW_TEST_ONLY"
            qc_note = "Developer-only test marker with no translatable content"
        elif not changed:
            qc_status = "REVIEW_KEEP"
            qc_note = "Kept unchanged as a possible proper name"
        result_rows.append(
            {
                **row,
                "retranslate_vi": translation,
                "qc_status": qc_status,
                "qc_note": qc_note,
            }
        )
    return {
        "provider": "you.com",
        "agent": "express",
        "stats": stats,
        "rows": result_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument("--max-chars", type=int, default=9000)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--retries", type=int, default=4)
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    api_key = load_env_key()
    rows = load_rows()
    checkpoint = load_checkpoint()
    pending = [row for row in rows if row["split_id"] not in checkpoint]
    batches = make_batches(pending, args.batch_size, args.max_chars)
    lock = threading.Lock()
    completed = len(checkpoint)
    print(
        f"Total={len(rows)} completed={completed} pending={len(pending)} batches={len(batches)}"
    )

    def process(batch: list[dict]) -> dict:
        return translate_with_split(api_key, batch, args.retries)

    if batches:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process, batch): batch for batch in batches}
            for future in concurrent.futures.as_completed(futures):
                batch = futures[future]
                try:
                    translated = future.result()
                except Exception as error:
                    print(
                        f"FAILED batch {batch[0]['split_id']}..{batch[-1]['split_id']}: {error}",
                        file=sys.stderr,
                    )
                    continue
                with lock:
                    checkpoint.update(translated)
                    completed = len(checkpoint)
                    write_json_atomic(
                        CHECKPOINT_PATH,
                        {
                            "provider": "you.com",
                            "agent": "express",
                            "total_expected": len(rows),
                            "translations": checkpoint,
                        },
                    )
                print(f"Progress {completed}/{len(rows)}")

    missing = [row["split_id"] for row in rows if row["split_id"] not in checkpoint]
    if missing:
        print(f"INCOMPLETE: {len(missing)} rows remain", file=sys.stderr)
        return 2

    result = build_result(rows, checkpoint)
    write_json_atomic(RESULT_PATH, result)
    print(json.dumps(result["stats"], ensure_ascii=False))
    print(f"Wrote {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
