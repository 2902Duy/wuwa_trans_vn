import sqlite3

def inspect_db(path, label):
    print(f"\n=== {label}: {path} ===")
    con = sqlite3.connect(path)
    cur = con.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Tables: {tables}")

    for tname in tables:
        cur.execute(f"PRAGMA table_info([{tname}])")
        cols = [(c[1], c[2]) for c in cur.fetchall()]
        cur.execute(f"SELECT COUNT(*) FROM [{tname}]")
        count = cur.fetchone()[0]
        print(f"  [{tname}] {count} rows | columns: {cols}")
        cur.execute(f"SELECT * FROM [{tname}] LIMIT 3")
        for row in cur.fetchall():
            print(f"    {row}")
    con.close()

# Kiem tra db trong project
inspect_db(r"db_en\lang_skill.db", "Project db_en (hien tai)")

# Kiem tra db tu Fmodel export
inspect_db(r"D:\Program\Fmodel\Output\Exports\Client\Content\Aki\ConfigDB\en\lang_skill.db", "Fmodel export")
