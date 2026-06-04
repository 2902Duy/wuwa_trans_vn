import json
import mimetypes
import re
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


WORKSPACE_DIR = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
WORK_DIR = WORKSPACE_DIR / "mistral_translate_work"
SPLIT_DIR = WORK_DIR / "split_by_prompt" / "json"
REVIEW_DIR = WORK_DIR / "review_translated_only"
PROMPT_DIR = WORK_DIR / "prompts"
STATIC_DIR = Path(__file__).resolve().parent / "static"

QUEST_RE = re.compile(r"^(Quest_\d+)")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def row_text(row):
    return "\n".join(
        str(row.get(key, ""))
        for key in ("split_id", "source_file", "primary_key", "source_en", "new_translation_vi")
    ).lower()


class WikiData:
    def __init__(self):
        self.rows = []
        self.by_split_id = {}
        self.by_domain = defaultdict(list)
        self.by_source_file = defaultdict(list)
        self.file_cache = {}
        self.characters = []
        self.load()

    def load(self):
        self.rows.clear()
        self.by_split_id.clear()
        self.by_domain.clear()
        self.by_source_file.clear()
        self.file_cache.clear()

        for path in sorted(SPLIT_DIR.rglob("*.json")):
            rows = read_json(path)
            self.file_cache[str(path)] = rows
            for index, row in enumerate(rows):
                item = dict(row)
                item["_json_path"] = str(path)
                item["_json_index"] = index
                item["_search"] = row_text(item)
                self.rows.append(item)
                self.by_split_id[item["split_id"]] = item
                self.by_domain[item.get("prompt_domain", "unknown")].append(item)
                self.by_source_file[item.get("source_file", "unknown")].append(item)

        self.characters = self.load_characters()

    def load_characters(self):
        roster = self.load_character_roster()
        path = REVIEW_DIR / "lang_role.json"
        profile_by_name = {}
        if path.exists():
            rows = read_json(path)
            for index, row in enumerate(rows):
                name = row.get("source_en", "").strip()
                if not self.looks_like_character_name(name):
                    continue
                title_row = rows[index + 1] if index + 1 < len(rows) else {}
                desc_row = rows[index + 2] if index + 2 < len(rows) else {}
                title = title_row.get("source_en", "").strip()
                description = desc_row.get("source_en", "").strip()
                if title.lower() == "stay tuned":
                    title = ""
                if description.lower() == "stay tuned":
                    description = ""
                profile_by_name.setdefault(
                    name,
                    {
                        "name": name,
                        "title": title,
                        "description": description,
                        "vi_name": row.get("translation_vi", "").strip(),
                        "vi_title": title_row.get("translation_vi", "").strip() if title else "",
                        "vi_description": desc_row.get("translation_vi", "").strip() if description else "",
                    },
                )

        names = []
        for name in roster + list(profile_by_name):
            if name and name not in names:
                names.append(name)

        characters = []
        for name in names:
            profile = profile_by_name.get(name, {"name": name, "title": "", "description": "", "vi_name": "", "vi_title": "", "vi_description": ""})
            profile["id"] = f"char_{len(characters) + 1}"
            characters.append(profile)
        return characters

    @staticmethod
    def looks_like_character_name(name):
        if not name or name.lower() == "stay tuned":
            return False
        if len(name) > 40:
            return False
        if any(mark in name for mark in ".!?{}<>:"):
            return False
        words = re.findall(r"[A-Za-z][A-Za-z' -]*", name)
        return bool(words) and len(name.split()) <= 3

    @staticmethod
    def load_character_roster():
        path = PROMPT_DIR / "character_voice_map.md"
        if not path.exists():
            return []
        names = []
        in_playable_table = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if "Bản đồ toàn bộ playable Resonators" in line:
                in_playable_table = True
                continue
            if in_playable_table and line.startswith("## "):
                break
            if not in_playable_table:
                continue
            if not line.startswith("|") or line.startswith("| Nhân vật") or line.startswith("| :"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not cells:
                continue
            raw_name = cells[0].strip("` ")
            if not raw_name or set(raw_name) <= {"-", ":", " "}:
                continue
            name = re.sub(r"\s*\([^)]*\)", "", raw_name).strip()
            if name and name not in names and name.lower() not in {"environment assessment module"}:
                names.append(name)
        return names

    def summarize(self):
        domains = []
        for domain, rows in sorted(self.by_domain.items()):
            domains.append(
                {
                    "domain": domain,
                    "rows": len(rows),
                    "translated": sum(1 for row in rows if row.get("new_translation_vi")),
                    "source_files": len({row.get("source_file") for row in rows}),
                }
            )
        return {
            "total_rows": len(self.rows),
            "domains": domains,
            "source_files": len(self.by_source_file),
            "characters": len(self.characters),
        }

    def list_rows(self, params):
        domain = params.get("domain", [""])[0]
        source_file = params.get("source_file", [""])[0]
        query = params.get("q", [""])[0].lower().strip()
        page = max(int(params.get("page", ["1"])[0]), 1)
        page_size = min(max(int(params.get("page_size", ["50"])[0]), 1), 200)

        rows = self.by_domain.get(domain, self.rows) if domain else self.rows
        if source_file:
            rows = [row for row in rows if row.get("source_file") == source_file]
        if query:
            rows = [row for row in rows if query in row.get("_search", "")]

        total = len(rows)
        start = (page - 1) * page_size
        page_rows = rows[start : start + page_size]
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "rows": [self.public_row(row) for row in page_rows],
        }

    def quest_groups(self, params):
        query = params.get("q", [""])[0].lower().strip()
        groups = defaultdict(list)
        for row in self.by_source_file.get("lang_multi_text.json", []):
            key = str(row.get("primary_key", ""))
            match = QUEST_RE.match(key)
            if match:
                groups[match.group(1)].append(row)

        out = []
        for quest_id, rows in groups.items():
            title_row = next((r for r in rows if "QuestName" in str(r.get("primary_key", ""))), rows[0])
            title = title_row.get("source_en", quest_id)
            vi_title = title_row.get("new_translation_vi", "")
            haystack = f"{quest_id} {title} {vi_title}".lower()
            if query and query not in haystack:
                continue
            out.append(
                {
                    "quest_id": quest_id,
                    "title": title,
                    "vi_title": vi_title,
                    "rows": len(rows),
                    "translated": sum(1 for row in rows if row.get("new_translation_vi")),
                }
            )
        out.sort(key=lambda item: item["quest_id"])
        return {"total": len(out), "quests": out[:1000]}

    def quest_detail(self, quest_id):
        rows = []
        for row in self.by_source_file.get("lang_multi_text.json", []):
            if str(row.get("primary_key", "")).startswith(quest_id):
                rows.append(row)
        rows.sort(key=lambda row: row.get("primary_key", ""))
        return {"quest_id": quest_id, "rows": [self.public_row(row) for row in rows]}

    def character_detail(self, name):
        char = next((item for item in self.characters if item["name"] == name), None)
        if not char:
            return {"error": "character_not_found"}
        name_lower = name.lower()
        sections = {
            "profile": [],
            "skill_names": [],
            "skill_descriptions": [],
            "rc_names": [],
            "rc_descriptions": [],
            "lore": [],
            "other": [],
        }
        for row in self.rows:
            domain = row.get("prompt_domain", "")
            key = str(row.get("primary_key", ""))
            source_file = row.get("source_file", "")
            text = f"{key} {row.get('source_en','')} {row.get('new_translation_vi','')}".lower()
            if name_lower not in text:
                continue
            section = self.character_section(domain, key, source_file)
            sections[section].append(row)

        # Always expose role profile rows when present, even if the source text is only the character name.
        for row in self.by_source_file.get("lang_role.json", []):
            if row.get("source_en", "").strip().lower() == name_lower:
                sections["profile"].append(row)

        for section_rows in sections.values():
            section_rows.sort(key=lambda row: (row.get("source_file", ""), row.get("primary_key", "")))
        section_payload = {
            section: [self.public_row(row) for row in rows[:1000]]
            for section, rows in sections.items()
        }
        return {
            "character": char,
            "sections": section_payload,
            "section_counts": {section: len(rows) for section, rows in sections.items()},
            "related_total": sum(len(rows) for rows in sections.values()),
        }

    @staticmethod
    def character_section(domain, key, source_file):
        if source_file == "lang_role.json":
            return "profile"
        if key.startswith("ResonantChain_"):
            return "rc_descriptions" if key.endswith("_AttributesDescription") else "rc_names"
        if domain == "rc_description":
            return "rc_descriptions"
        if "SkillName" in key or key.startswith("PhantomBattleNPCSkill_") or (domain == "name_title" and "Skill" in key):
            return "skill_names"
        if domain in {"skill_description", "phantom_skill"} or "SkillDesc" in key or "SkillDescribe" in key or "SkillDescription" in key:
            return "skill_descriptions"
        if domain in {"lore", "story_dialogue"}:
            return "lore"
        return "other"

    def save_row(self, payload):
        split_id = payload.get("split_id", "")
        translation = payload.get("new_translation_vi", "")
        note = payload.get("translator_note", "")
        item = self.by_split_id.get(split_id)
        if not item:
            return {"ok": False, "error": "split_id_not_found"}

        path = Path(item["_json_path"])
        rows = self.file_cache[str(path)]
        row = rows[item["_json_index"]]
        row["new_translation_vi"] = translation
        row["translator_note"] = note
        write_json(path, rows)

        item["new_translation_vi"] = translation
        item["translator_note"] = note
        item["_search"] = row_text(item)
        return {"ok": True, "row": self.public_row(item)}

    @staticmethod
    def public_row(row):
        return {
            "split_id": row.get("split_id", ""),
            "prompt_domain": row.get("prompt_domain", ""),
            "prompt_file": row.get("prompt_file", ""),
            "source_file": row.get("source_file", ""),
            "original_index": row.get("original_index", ""),
            "database": row.get("database", ""),
            "table": row.get("table", ""),
            "primary_key": row.get("primary_key", ""),
            "column": row.get("column", ""),
            "category": row.get("category", ""),
            "source_en": row.get("source_en", ""),
            "new_translation_vi": row.get("new_translation_vi", ""),
            "translator_note": row.get("translator_note", ""),
        }


DATA = WikiData()


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path

        if path == "/":
            return self.serve_static("index.html")
        if path.startswith("/static/"):
            return self.serve_static(path.removeprefix("/static/"))

        if path == "/api/summary":
            return self.send_json(DATA.summarize())
        if path == "/api/rows":
            return self.send_json(DATA.list_rows(params))
        if path == "/api/quests":
            return self.send_json(DATA.quest_groups(params))
        if path.startswith("/api/quest/"):
            return self.send_json(DATA.quest_detail(unquote(path.removeprefix("/api/quest/"))))
        if path == "/api/characters":
            return self.send_json({"characters": DATA.characters})
        if path.startswith("/api/character/"):
            return self.send_json(DATA.character_detail(unquote(path.removeprefix("/api/character/"))))
        if path == "/api/reload":
            DATA.load()
            return self.send_json({"ok": True, **DATA.summarize()})

        return self.send_json({"error": "not_found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/row":
            return self.send_json({"error": "not_found"}, 404)
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        return self.send_json(DATA.save_row(payload))

    def serve_static(self, name):
        path = (STATIC_DIR / name).resolve()
        if STATIC_DIR.resolve() not in path.parents and path != STATIC_DIR.resolve():
            return self.send_json({"error": "bad_path"}, 400)
        if not path.exists() or path.is_dir():
            return self.send_json({"error": "not_found"}, 404)
        body = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    log_path = WORKSPACE_DIR / ".runlogs" / "wiki_editor_startup.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        log_path.write_text("starting\n", encoding="utf-8")
        server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
        log_path.write_text("running http://127.0.0.1:8765\n", encoding="utf-8")
        print("Wiki editor running at http://127.0.0.1:8765", flush=True)
        server.serve_forever()
    except Exception as exc:
        log_path.write_text(f"error: {exc!r}\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
