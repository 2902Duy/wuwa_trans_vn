import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "mistral_translate_work"
    / "reports"
    / "name_title_english_audit"
    / "english_not_translated_exact.json"
)
OUTPUT_DIR = ROOT / "outputs" / "name_title_audit" / "you_pilot"
OUTPUT_JSON = OUTPUT_DIR / "pilot_translations.json"
API_URL = "https://api.you.com/v1/agents/runs"
PILOT_SIZE = 10


def load_env_key() -> str:
    key = os.environ.get("YDC_API_KEY", "").strip()
    if key:
        return key

    env_path = ROOT / ".env"
    if not env_path.exists():
        raise RuntimeError("Missing .env")

    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "YDC_API_KEY":
            return value.strip().strip("'\"")
    raise RuntimeError("YDC_API_KEY is missing or empty")


def select_rows() -> list[dict]:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    selected = []
    for row in report["rows"]:
        source = row["source_en"].strip()
        if (
            3 <= len(source) <= 90
            and "\n" not in source
            and row.get("source_translatable")
            and not row.get("keep_allowed")
        ):
            selected.append(row)
        if len(selected) == PILOT_SIZE:
            break
    if len(selected) != PILOT_SIZE:
        raise RuntimeError(f"Could only select {len(selected)} pilot rows")
    return selected


def protected_tokens(text: str) -> list[str]:
    patterns = [
        r"\{[^{}]+\}",
        r"<[^<>]+>",
        r"\\n",
    ]
    tokens = []
    for pattern in patterns:
        tokens.extend(re.findall(pattern, text))
    return tokens


def build_prompt(rows: list[dict]) -> str:
    payload = [
        {"split_id": row["split_id"], "source_en": row["source_en"]}
        for row in rows
    ]
    return f"""Translate Wuthering Waves name/title strings from English to Vietnamese.

Mandatory rules:
- Return ONLY one valid JSON object mapping every split_id to its translated string.
- Do not omit, add, reorder, or alter split_id values.
- Keep character, NPC, place, organization, Echo, weapon, set, skill, event, and named game terms in English.
- Translate ordinary roles, common descriptions, and generic short titles naturally into Vietnamese.
- Keep exact English names embedded inside a translated phrase.
- Preserve all placeholders, tags, punctuation, line breaks, prefixes, and suffixes.
- Do not add explanations or Markdown fences.
- For a pure proper noun, output the source unchanged.
- Use concise, natural Vietnamese suitable for in-game display.

Examples:
{{"A":"City Guard","B":"Yangyang","C":"Hukou, the Tiger's Maw"}}
must become:
{{"A":"Lính gác thành phố","B":"Yangyang","C":"Hukou, Hang Hổ"}}

Input:
{json.dumps(payload, ensure_ascii=False)}
"""


def extract_answer(response: dict) -> str:
    for item in reversed(response.get("output", [])):
        if item.get("type") == "message.answer" and isinstance(item.get("text"), str):
            return item["text"].strip()
    raise RuntimeError("You.com response has no message.answer text")


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
        raise RuntimeError("Translation answer is not a JSON object")
    return value


def call_you(api_key: str, prompt: str) -> dict:
    body = json.dumps(
        {"agent": "express", "input": prompt, "stream": False},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "wuwa-name-title-pilot/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"You.com HTTP {error.code}: {detail[:500]}") from error


def validate(rows: list[dict], translations: dict) -> list[dict]:
    expected_ids = [row["split_id"] for row in rows]
    if set(translations) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(translations))
        extra = sorted(set(translations) - set(expected_ids))
        raise RuntimeError(f"ID mismatch; missing={missing}, extra={extra}")

    results = []
    for row in rows:
        split_id = row["split_id"]
        translation = translations[split_id]
        if not isinstance(translation, str) or not translation.strip():
            raise RuntimeError(f"Empty/non-string translation for {split_id}")
        source_tokens = protected_tokens(row["source_en"])
        translated_tokens = protected_tokens(translation)
        results.append(
            {
                **row,
                "retranslate_vi": translation.strip(),
                "validation": {
                    "protected_tokens_match": source_tokens == translated_tokens,
                    "changed_from_source": translation.strip() != row["source_en"].strip(),
                },
            }
        )
    return results


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

    api_key = load_env_key()
    rows = select_rows()
    response = call_you(api_key, build_prompt(rows))
    answer_text = extract_answer(response)
    translations = parse_json_answer(answer_text)
    results = validate(rows, translations)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "provider": "you.com",
        "agent": "express",
        "pilot_size": len(results),
        "rows": results,
    }
    OUTPUT_JSON.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(results)} pilot translations to {OUTPUT_JSON}")
    for row in results:
        print(
            f"{row['split_id']}: {row['source_en']} -> {row['retranslate_vi']}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
