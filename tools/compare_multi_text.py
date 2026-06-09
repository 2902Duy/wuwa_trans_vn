"""
So sanh lang_multi_text.db giua Fmodel export (cu) va project db_en (moi).
Hien thi cac string moi va string da thay doi.
"""
import sqlite3
import sys
import io

# Redirect output to UTF-8 file
OUT_FILE = "multi_text_diff.txt"
out = io.open(OUT_FILE, "w", encoding="utf-8")

def p(*args, **kwargs):
    print(*args, **kwargs, file=out)

OLD_DB = r"D:\Program\Fmodel\Output\Exports\Client\Content\Aki\ConfigDB\en\lang_multi_text.db"
NEW_DB = r"db_en\lang_multi_text.db"

def get_tables(path):
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    con.close()
    return tables

def get_all_rows(path, table):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(f"SELECT * FROM [{table}]")
    rows = {r[0]: dict(r) for r in cur.fetchall()}
    con.close()
    return rows

def get_columns(path, table):
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info([{table}])")
    cols = [r[1] for r in cur.fetchall()]
    con.close()
    return cols

p("=== Kiem tra cau truc DB ===")
old_tables = get_tables(OLD_DB)
new_tables = get_tables(NEW_DB)
p(f"OLD tables: {old_tables}")
p(f"NEW tables: {new_tables}")
p()

# Lay table chinh
common = set(old_tables) & set(new_tables)
if not common:
    p("Khong co table chung!")
    sys.exit(1)

for table in sorted(common):
    p(f"=== Table: {table} ===")
    old_cols = get_columns(OLD_DB, table)
    new_cols = get_columns(NEW_DB, table)
    p(f"  Columns OLD: {old_cols}")
    p(f"  Columns NEW: {new_cols}")

    old_rows = get_all_rows(OLD_DB, table)
    new_rows = get_all_rows(NEW_DB, table)

    p(f"  So dong OLD: {len(old_rows)}")
    p(f"  So dong NEW: {len(new_rows)}")

    # Tim key column (cot dau tien)
    key_col = old_cols[0]

    # String moi (chi co trong NEW)
    new_keys = set(new_rows.keys()) - set(old_rows.keys())
    # String bi xoa (chi co trong OLD)
    del_keys = set(old_rows.keys()) - set(new_rows.keys())
    # String thay doi
    changed_keys = []
    for k in set(old_rows.keys()) & set(new_rows.keys()):
        if old_rows[k] != new_rows[k]:
            changed_keys.append(k)

    p(f"\n  [NEW] Them moi: {len(new_keys)} strings")
    for k in sorted(new_keys)[:30]:
        row = new_rows[k]
        vals = [f"{c}={repr(row[c])}" for c in new_cols[1:4] if row.get(c)]
        p(f"    + {k}: {' | '.join(vals)}")
    if len(new_keys) > 30:
        p(f"    ... va {len(new_keys)-30} strings khac")

    p(f"\n  [DEL] Bi xoa: {len(del_keys)} strings")
    for k in sorted(del_keys)[:10]:
        row = old_rows[k]
        vals = [f"{c}={repr(row[c])}" for c in old_cols[1:4] if row.get(c)]
        p(f"    - {k}: {' | '.join(vals)}")

    p(f"\n  [MOD] Thay doi: {len(changed_keys)} strings")
    for k in sorted(changed_keys):
        old_r = old_rows[k]
        new_r = new_rows[k]
        for col in old_cols[1:]:
            if old_r.get(col) != new_r.get(col):
                p(f"  ~ {k} [{col}]:")
                p(f"    OLD: {old_r.get(col, '')}")
                p(f"    NEW: {new_r.get(col, '')}")
                p()

    p()

out.close()
print(f"Done! Ket qua da luu vao: multi_text_diff.txt")
