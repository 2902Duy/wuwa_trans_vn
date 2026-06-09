import csv
import json
from collections import Counter
from pathlib import Path


REPORT_DIR = Path("mistral_translate_work/reports/forbidden_english_audit")
SUSPECTS = REPORT_DIR / "suspects.json"
OUT = REPORT_DIR / "mixed_english_terms.csv"


def extract_terms(issue: str) -> list[str]:
    if issue.startswith("forbidden_phrase:"):
        return [issue.split(":", 1)[1].split("->", 1)[0]]
    if issue.startswith("forbidden_words:"):
        body = issue.split(":", 1)[1]
        return [part.split("->", 1)[0] for part in body.split(",") if part]
    if issue.startswith("english_without_vietnamese:"):
        return [part for part in issue.split(":", 1)[1].split(",") if part]
    return []


def main() -> None:
    rows = json.loads(SUSPECTS.read_text(encoding="utf-8"))
    actionable = [row for row in rows if row.get("severity") in {"high", "medium"}]
    counts = Counter()
    examples = {}
    domains = {}

    for row in actionable:
        for issue in row.get("issues", []):
            for term in extract_terms(issue):
                counts[term] += 1
                examples.setdefault(term, row)
                domains.setdefault(term, Counter())
                domains[term][row.get("domain", "")] += 1

    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "term",
                "count",
                "domains",
                "example_domain",
                "example_split_id",
                "example_source_en",
                "example_new_translation_vi",
            ],
        )
        writer.writeheader()
        for term, count in counts.most_common():
            example = examples[term]
            writer.writerow(
                {
                    "term": term,
                    "count": count,
                    "domains": "; ".join(f"{k}:{v}" for k, v in domains[term].most_common()),
                    "example_domain": example.get("domain", ""),
                    "example_split_id": example.get("split_id", ""),
                    "example_source_en": example.get("source_en", ""),
                    "example_new_translation_vi": example.get("new_translation_vi", ""),
                }
            )

    print({"terms": len(counts), "rows": len(actionable), "out": str(OUT)})


if __name__ == "__main__":
    main()
