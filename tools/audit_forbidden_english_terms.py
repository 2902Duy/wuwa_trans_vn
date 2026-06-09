import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


JSON_ROOT = Path("mistral_translate_work/split_by_prompt/json")
PROMPT_ROOT = Path("mistral_translate_work/prompts")
REPORT_DIR = Path("mistral_translate_work/reports/forbidden_english_audit")

EXCLUDED_DOMAINS = {
    "skill_description",
    "weapon",
    "echo_set",
    "phantom_skill",
    "monster_description",
}

TAG_RE = re.compile(r"<[^>]+>")
PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")
ASSET_RE = re.compile(r"<texture=[^>]+>|/Game/[^\s>]+")
ASCII_WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9'./&+-]*\b")
VI_RE = re.compile(
    r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡ"
    r"ùúụủũưừứựửữỳýỵỷỹđ"
    r"ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ"
    r"ÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
)

BASE_ALLOWED = {
    # Core Wuthering Waves terms that prompts intentionally keep in English.
    "Rover", "Echo", "Echoes", "Resonator", "Resonators", "Tacet", "Discord", "Discords",
    "Sonata", "Terminal", "Data", "Bank", "Resonance", "Liberation", "Forte", "Circuit",
    "Concerto", "Intro", "Outro", "DMG", "HP", "ATK", "DEF", "Crit", "CRIT", "EXP", "Lv",
    "Aero", "Glacio", "Fusion", "Electro", "Spectro", "Havoc", "Jinzhou", "Huanglong",
    "Rinascita", "Black", "Shores", "Fractsidus", "Lament",
    # Controls / technical labels often intentionally kept.
    "UID", "NPC", "PC", "UI", "FPS", "HUD", "KURO", "WavesLine",
}

FORBIDDEN_WORDS = {
    # UI/action words should normally be Vietnamese outside excluded domains.
    "Cancel": "Hủy",
    "Confirm": "Xác nhận",
    "Select": "Chọn",
    "Tap": "Chạm",
    "Claim": "Nhận",
    "Remove": "Gỡ/Xóa",
    "Place": "Đặt",
    "Previous": "Trước",
    "Next": "Tiếp",
    "Back": "Quay lại",
    "Close": "Đóng",
    "Start": "Bắt đầu",
    "Continue": "Tiếp tục",
    "Skip": "Bỏ qua",
    "Retry": "Thử lại",
    "View": "Xem",
    "Unlock": "Mở khóa",
    "Unlocked": "Đã mở khóa",
    "Locked": "Đã khóa",
    "Unavailable": "Không khả dụng",
    "Requirement": "Yêu cầu",
    "Requirements": "Yêu cầu",
    "Description": "Mô tả",
    "Details": "Chi tiết",
    "Overview": "Tổng quan",
    "Settings": "Cài đặt",
    "Tutorials": "Hướng dẫn",
    "Guidebook": "Sổ tay hướng dẫn",
    "Gallery": "Bộ sưu tập",
    "Friends": "Bạn bè",
    "Store": "Cửa hàng",
    "Team": "Đội",
    "Missions": "Nhiệm vụ",
    "Achievements": "Thành tựu",
    "Database": "Cơ sở dữ liệu",
    "Map": "Bản đồ",
    "Backpack": "Túi đồ",
    "Utilities": "Tiện ích",
    "Feedback": "Phản hồi",
    "Controls": "Điều khiển",
    "Module": "Mô-đun",
    "Alert": "Cảnh báo",
    "Notice": "Thông báo",
    "Items": "Vật phẩm",
    "Item": "Vật phẩm",
    "Use": "Dùng/Sử dụng",
    "Hold": "Giữ",
    "Release": "Thả",
    "Jump": "Nhảy",
    "Gather": "Thu thập",
    "Deploy": "Triển khai",
    "Research": "Nghiên cứu",
    "Instructions": "Hướng dẫn",
    "Amount": "Số lượng",
    "Support": "Hỗ trợ",
    "Transform": "Biến đổi",
    "Fast": "Dịch chuyển nhanh (trong Fast Travel)",
    "Travel": "Dịch chuyển nhanh (trong Fast Travel)",
    "Merchandiser": "Thương nhân/Nhân viên bán hàng",
    "Demodulator": "Bộ giải điều chế",
}

FORBIDDEN_PHRASES = {
    "Fast Travel": "Dịch chuyển nhanh",
    "Hồi chiêu Skill": "Hồi chiêu Kỹ năng",
    "Cooldown Skill": "Hồi chiêu Kỹ năng",
    "Research Institute": "Viện Nghiên Cứu",
    "Normal Attack": "Tấn công thường",
    "Heavy Attack": "Trọng kích",
    "Basic Attack": "Tấn công cơ bản",
}

VIETNAMESE_ASCII_WORDS = {
    "ai", "anh", "ba", "ban", "bang", "bao", "bay", "be", "ben", "bi", "biet", "bo", "boi",
    "bon", "buoc", "buoi", "ca", "cac", "cach", "cai", "cam", "can", "canh", "cao", "cap",
    "cau", "chat", "chi", "cho", "chung", "chua", "chuyen", "co", "con", "cong", "cua", "cung",
    "cuoc", "cuoi", "cuu", "da", "dang", "danh", "day", "de", "den", "di", "dia", "dich", "do",
    "doi", "dong", "du", "dua", "duoc", "duoi", "dung", "duong", "em", "ga", "gap", "ghi", "gia",
    "giai", "gian", "giao", "giu", "giua", "giup", "hai", "han", "hay", "hien", "hoa", "hoi",
    "hom", "hon", "hoac", "kha", "khac", "khi", "kho", "khong", "khu", "kia", "kiem", "lai",
    "lam", "lan", "lay", "len", "luc", "luon", "ma", "mang", "mat", "may", "minh", "mo", "moi",
    "mong", "mot", "mua", "muon", "muc", "nam", "nay", "neu", "ngay", "nghe", "nghi", "ngoai",
    "nguoi", "nguy", "nha", "nhan", "nhanh", "nhau", "nho", "nhom", "nhung", "noi", "nuoc",
    "qua", "quan", "ra", "rang", "rat", "roi", "sao", "sau", "se", "sinh", "su", "suy", "ta",
    "tai", "tao", "ten", "tham", "thanh", "thay", "the", "theo", "thi", "thoi", "thu", "tien",
    "tim", "tin", "tinh", "to", "toi", "tong", "tra", "trang", "tren", "trong", "trung", "tu",
    "tuc", "tung", "vao", "ve", "vi", "viec", "voi", "vui", "vua", "vung", "xin", "xem", "xong",
    "xuong", "yeu",
    # User-reviewed false positives / Vietnamese without diacritics / names / interjections.
    "lu", "meo", "sai", "mua", "hoa", "sao", "chu", "cao", "xem", "quang", "ta", "vinh",
    "khu", "nam", "ui", "trao", "ba", "anh", "phong", "chung", "thay", "nghe", "ai",
    "xoay", "quen", "kho", "tt", "minh", "sakura", "lulala", "thanh", "giao", "chim",
    "haha", "em", "giun", "namipon", "mai", "sau", "khi", "shashou", "lululala", "hang",
    "stalaglow", "lan", "hai", "murmurin", "joy", "lollo", "conduit", "cruisea", "hmm",
    "huy", "khoan", "i", "trai", "cho", "tao", "okay", "aaaaaaa", "nhanh",
    # Additional user-reviewed false positives from mixed_english_terms review.
    "h", "d", "ch", "bida", "honami", "spd", "phim", "x2", "ca...sette", "y", "z",
    "uuu", "tem", "hmhmhm", "uaaa", "ong", "yeah", "ngoan", "cucu", "ngh", "meo-ow",
    "alwa", "tidebreaker", "ishmael", "ngon", "chulululu", "chuuu", "chu-luu-luu",
    "aleph-1", "aaaaaahhhh", "chu-luu-luu-luu-luu", "chuu-chuu", "daaaaaa",
    "chuluu", "chu-chu-chu", "chuu-luu-luu", "chuuluu", "waveworn", "aaaahhh",
    "iaen", "ho", "aaaaaahhhhh", "a", "aaaagh", "il", "matto", "doki", "aaaaa",
    "haaah", "ta-da", "ta-daaa", "lalala...lala", "woo", "uuuuuuu",
    "hihihahahahaha", "khs", "reng", "w-wuli", "maqi", "mithril", "la", "rurara",
    "rururara", "b", "c", "kh", "m", "ng", "ri", "s", "choi", "hyeon", "ji",
    "nham", "ngai", "tay", "son", "xe", "v", "mi", "hy", "kinh", "rondo", "limbo",
    "lenie", "mia", "mannequin", "doanh", "mya", "tadaa", "gideon", "kuangda",
    "xu", "ohm", "hsin", "kumi", "jamie", "ting", "aaa", "aaaa", "jinji", "harbor",
    "sepp", "ku-hihi", "shee", "neam", "tia", "iris", "tre", "dosumu", "yo-ren",
    "ivank", "hihi", "hu", "xess2", "phanh/l", "sephira", "arbor", "bogu's",
    "joshua", "davide", "cube", "linh", "chuy", "n", "area", "cha", "haa", "cay",
    "ha", "tch", "chu-lu-lu", "hi", "threnodian", "chu-lu", "chu-luu-luu-luu",
    "chu-lu-lu-lu", "chu-luuuu", "x", "montelli", "kim", "juebi", "aurora", "ride",
    "lana", "long", "chu-luu-chu-luu", "chu-lu", "huhu", "chu-luu", "khe", "liliana",
    "adrenalin", "adrenalinee", "primus", "thg", "everflow", "phagosite", "hysteriarch",
    "miseriarch", "lahai-roi", "fells", "thessaleo", "lucio", "colleen", "rapper",
    "isth", "pin", "jinhu", "ninja", "hieron", "siran", "zahira", "gulan", "hehe",
    "are", "gai", "nevermore", "blaze", "upphopia", "id", "xbox", "soliskin", "orbit",
    "pass", "radio", "cruise", "field", "blake", "bloom", "khss", "origami", "yuanyuan",
    "hya", "exostrider", "gyokuro", "exploration",
    "in", "chia", "lenore", "oki", "doki", "hmmm", "connector",
}

KNOWN_BAD_PATTERNS = {
    "english_verb_to_vietnamese": re.compile(r"\b(Fast Travel|Teleport|Transform|Support|Use|Claim|Select|Tap|Confirm|Cancel)\b\s+(?:đến|vào|ra|với|cho|tại|ở)\b", re.I),
    "vietnamese_noun_plus_english_system_word": re.compile(r"\b(?:Hồi chiêu|Kỹ năng|Nhiệm vụ|Vật phẩm|Cửa hàng|Bản đồ|Túi đồ|Dữ liệu|Hướng dẫn)\s+(Skill|Item|Quest|Mission|Map|Store|Shop|Guide|Module|Cooldown)\b", re.I),
}


def strip_scan_noise(text: str) -> str:
    text = ASSET_RE.sub(" ", text or "")
    text = TAG_RE.sub(" ", text)
    text = PLACEHOLDER_RE.sub(" ", text)
    return text


def load_allowed_terms() -> set[str]:
    allowed = set(BASE_ALLOWED)
    for path in [PROMPT_ROOT / "shared_glossary.md", PROMPT_ROOT / "keep_english_rules.md"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for term in re.findall(r"`([^`\n]{2,80})`", text):
            if re.search(r"[A-Za-z]", term):
                # Keep whole phrase and component words for proper nouns/game terms.
                allowed.add(term)
                for word in ASCII_WORD_RE.findall(term):
                    if len(word) > 1:
                        allowed.add(word)
        for quoted in re.findall(r"^- `?([^`\n]{2,80})`?\s*$", text, re.M):
            if re.search(r"[A-Za-z]", quoted):
                allowed.add(quoted.strip())
                for word in ASCII_WORD_RE.findall(quoted):
                    if len(word) > 1:
                        allowed.add(word)
    return allowed


def domain_from_path(path: Path) -> str:
    rel = path.relative_to(JSON_ROOT)
    return rel.parts[0] if rel.parts else ""


def classify(source: str, target: str, allowed: set[str]) -> list[tuple[str, str]]:
    clean = strip_scan_noise(target).strip()
    source_clean = strip_scan_noise(source).strip()
    issues: list[tuple[str, str]] = []
    if not clean:
        return issues

    has_vi = bool(VI_RE.search(clean))

    for phrase, suggestion in FORBIDDEN_PHRASES.items():
        if phrase in allowed:
            continue
        if re.search(rf"\b{re.escape(phrase)}\b", clean, re.I):
            issues.append(("high", f"forbidden_phrase:{phrase}->{suggestion}"))

    for name, pattern in KNOWN_BAD_PATTERNS.items():
        if pattern.search(clean):
            issues.append(("high", name))

    words = ASCII_WORD_RE.findall(clean)
    forbidden_hits = []
    other_hits = []
    for word in words:
        if word in allowed or word.upper() in allowed:
            continue
        if re.fullmatch(r"[A-Z]{2,}", word) and word not in FORBIDDEN_WORDS:
            continue
        if word in FORBIDDEN_WORDS:
            forbidden_hits.append(word)
        elif has_vi and len(word) >= 3:
            if word.lower() in VIETNAMESE_ASCII_WORDS:
                continue
            # Do not flag proper nouns that are copied from source and likely names unless they are surrounded by VI.
            if word in ASCII_WORD_RE.findall(source_clean) and word[:1].isupper() and word not in FORBIDDEN_WORDS:
                continue
            other_hits.append(word)

    if forbidden_hits:
        unique = sorted(set(forbidden_hits))
        issues.append(("medium", "forbidden_words:" + ",".join(f"{w}->{FORBIDDEN_WORDS[w]}" for w in unique[:8])))

    if has_vi and other_hits:
        unique = sorted(set(other_hits))
        issues.append(("low", "unknown_english_words:" + ",".join(unique[:10])))

    if not has_vi and words and clean != source_clean and len(clean) <= 120:
        unknown = [w for w in words if w not in allowed and w.lower() not in VIETNAMESE_ASCII_WORDS]
        if unknown:
            issues.append(("medium", "english_without_vietnamese:" + ",".join(sorted(set(unknown))[:10])))

    return issues


def severity_rank(sev: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(sev, 9)


def main() -> None:
    allowed = load_allowed_terms()
    suspects = []
    stats = Counter()
    domain_rows = Counter()
    issue_counts = Counter()

    for path in sorted(JSON_ROOT.rglob("*.json")):
        domain = domain_from_path(path)
        if domain in EXCLUDED_DOMAINS:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        rel = path.relative_to(JSON_ROOT).as_posix()
        for index, row in enumerate(data):
            if not isinstance(row, dict):
                continue
            stats["rows_scanned"] += 1
            domain_rows[domain] += 1
            source = str(row.get("source_en") or "")
            target = str(row.get("new_translation_vi") or "")
            issues = classify(source, target, allowed)
            if not issues:
                continue
            highest = sorted({sev for sev, _ in issues}, key=severity_rank)[0]
            labels = [label for _, label in issues]
            for _, label in issues:
                issue_counts[label] += 1
            suspects.append({
                "severity": highest,
                "domain": domain,
                "json_file": rel,
                "json_index": index,
                "split_id": row.get("split_id", ""),
                "source_file": row.get("source_file", ""),
                "primary_key": row.get("primary_key", ""),
                "key_type": row.get("primary_key", "").split("_")[2] if str(row.get("primary_key", "")).startswith("Quest_") and len(str(row.get("primary_key", "")).split("_")) > 2 else "",
                "issues": labels,
                "source_en": source,
                "new_translation_vi": target,
            })

    suspects.sort(key=lambda r: (severity_rank(r["severity"]), r["domain"], r["json_file"], r["json_index"]))
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        "scope": "split_by_prompt/json excluding skill_description, weapon, echo_set, phantom_skill, monster_description",
        "excluded_domains": sorted(EXCLUDED_DOMAINS),
        "rows_scanned": stats["rows_scanned"],
        "suspect_rows": len(suspects),
        "domain_rows": dict(domain_rows),
        "domain_suspects": dict(Counter(row["domain"] for row in suspects)),
        "top_issues": dict(issue_counts.most_common(80)),
    }
    (REPORT_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DIR / "suspects.json").write_text(json.dumps(suspects, ensure_ascii=False, indent=2), encoding="utf-8")

    fields = [
        "severity", "domain", "json_file", "json_index", "split_id", "source_file",
        "primary_key", "key_type", "issues", "source_en", "new_translation_vi",
    ]
    with (REPORT_DIR / "suspects.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in suspects:
            out = dict(row)
            out["issues"] = " | ".join(row["issues"])
            writer.writerow(out)

    by_domain = defaultdict(list)
    for row in suspects:
        by_domain[row["domain"]].append(row)
    domain_dir = REPORT_DIR / "by_domain"
    domain_dir.mkdir(exist_ok=True)
    for domain, rows in by_domain.items():
        (domain_dir / f"{domain}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
