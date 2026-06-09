"""
So sanh lang_multi_text.db moi (Fmodel 09/06) voi ban project hien tai (05/06).
Xuat ra JSON cac string moi can dich.
"""
import sqlite3
import json

NEW_DB = r"D:\Program\Fmodel\Output\Exports\Client\Content\Aki\ConfigDB\en\lang_multi_text.db"
OLD_DB = r"db_en\lang_multi_text.db"
OUT_FILE = r"new_strings_to_translate.json"

def get_rows(path):
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("SELECT Id, Content FROM [MultiText]")
    rows = {r[0]: r[1] for r in cur.fetchall() if r[1] and r[1].strip()}
    con.close()
    return rows

print("Dang doc DB...")
new_rows = get_rows(NEW_DB)
old_rows = get_rows(OLD_DB)

print(f"  Moi (09/06): {len(new_rows)} strings co noi dung")
print(f"  Cu  (05/06): {len(old_rows)} strings co noi dung")

# Tim string moi hoan toan (ID chua ton tai trong ban cu)
brand_new = {k: v for k, v in new_rows.items() if k not in old_rows}

# Tim string da thay doi noi dung
changed = {
    k: {"old": old_rows[k], "new": v}
    for k, v in new_rows.items()
    if k in old_rows and v != old_rows[k]
}

print(f"\n  [NEW]     String moi hoan toan : {len(brand_new)}")
print(f"  [CHANGED] String thay doi noi dung: {len(changed)}")

# Build output JSON
output = {
    "summary": {
        "export_date": "2026-06-09",
        "new_strings": len(brand_new),
        "changed_strings": len(changed),
        "total_to_review": len(brand_new) + len(changed)
    },
    "new_strings": {
        k: {
            "id": k,
            "english": v,
            "vietnamese": ""
        }
        for k, v in sorted(brand_new.items())
    },
    "changed_strings": {
        k: {
            "id": k,
            "old_english": d["old"],
            "new_english": d["new"],
            "vietnamese": ""
        }
        for k, d in sorted(changed.items())
    }
}

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nDa xuat ra: {OUT_FILE}")
print(f"Tong can dich/review: {len(brand_new) + len(changed)} strings")
