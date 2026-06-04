import argparse
import json
import shutil
import sqlite3
from pathlib import Path


SQLITE_HEADER = b"SQLite format 3\x00"
REPORT_DIR = Path("mistral_translate_work/reports/direct_pak_patch")


def read_page_info(blob: bytes, offset: int) -> tuple[int, int] | None:
    if offset + 100 > len(blob):
        return None
    page_size = int.from_bytes(blob[offset + 16 : offset + 18], "big")
    if page_size == 1:
        page_size = 65536
    if page_size < 512 or page_size > 65536 or page_size & (page_size - 1):
        return None
    page_count = int.from_bytes(blob[offset + 28 : offset + 32], "big")
    if page_count <= 0:
        return None
    size = page_size * page_count
    if offset + size > len(blob):
        return None
    return page_size, page_count


def quick_check_db(path: Path) -> str:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        row = con.execute("PRAGMA quick_check").fetchone()
        return row[0] if row else ""
    finally:
        con.close()


def compact_db_if_needed(db_path: Path, max_size: int, temp_dir: Path) -> Path | None:
    if db_path.stat().st_size <= max_size:
        return db_path
    compact_path = temp_dir / f"{db_path.name}.compact.db"
    compact_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.execute(f"VACUUM INTO '{compact_path.as_posix()}'")
    finally:
        con.close()
    return compact_path if compact_path.stat().st_size <= max_size else None


def identify_db(segment: bytes, temp_dir: Path, index: int) -> dict:
    temp_path = temp_dir / f"segment_{index:04d}.db"
    temp_path.write_bytes(segment)
    info = {"quick_check": "", "tables": [], "database_list": []}
    con = sqlite3.connect(temp_path)
    try:
        info["quick_check"] = con.execute("PRAGMA quick_check").fetchone()[0]
        info["tables"] = [
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        info["database_list"] = [list(row) for row in con.execute("PRAGMA database_list").fetchall()]
    finally:
        con.close()
    temp_path.unlink(missing_ok=True)
    return info


def scan_pak(pak_path: Path, db_dir: Path) -> list[dict]:
    blob = pak_path.read_bytes()
    temp_dir = REPORT_DIR / "_segments"
    temp_dir.mkdir(parents=True, exist_ok=True)
    known_sizes = {path.name: path.stat().st_size for path in db_dir.glob("*.db")}
    db_names_by_size = {}
    for name, size in known_sizes.items():
        db_names_by_size.setdefault(size, []).append(name)
    db_table_sets = {}
    for path in db_dir.glob("*.db"):
        con = sqlite3.connect(path)
        try:
            tables = tuple(
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
            )
        finally:
            con.close()
        db_table_sets[path.name] = tables

    offsets = []
    start = 0
    while True:
        offset = blob.find(SQLITE_HEADER, start)
        if offset < 0:
            break
        page_info = read_page_info(blob, offset)
        if page_info:
            offsets.append((offset, *page_info))
        start = offset + 1

    segments = []
    for index, (offset, page_size, page_count) in enumerate(offsets):
        size = page_size * page_count
        segment = blob[offset : offset + size]
        info = identify_db(segment, temp_dir, index)
        candidates = db_names_by_size.get(size, [])
        table_candidates = [
            name for name, tables in db_table_sets.items() if tables == tuple(info["tables"])
        ]
        matched = ""
        if len(candidates) == 1:
            matched = candidates[0]
        elif len(table_candidates) == 1:
            matched = table_candidates[0]
        elif table_candidates:
            # Same-schema DBs, such as MultiText, are resolved by closest size.
            matched = min(table_candidates, key=lambda name: abs(known_sizes[name] - size))
        segments.append(
            {
                "index": index,
                "offset": offset,
                "page_size": page_size,
                "page_count": page_count,
                "size": size,
                "quick_check": info["quick_check"],
                "tables": info["tables"],
                "size_name_candidates": candidates,
                "table_name_candidates": table_candidates,
                "matched_db": matched,
            }
        )
    return segments


def patch_pak(base_pak: Path, output_pak: Path, db_dir: Path, segments: list[dict]) -> dict:
    shutil.copyfile(base_pak, output_pak)
    db_by_name = {path.name: path for path in db_dir.glob("*.db")}
    patched = []
    skipped = []
    compact_dir = REPORT_DIR / "compact_dbs"
    compact_dir.mkdir(parents=True, exist_ok=True)

    with output_pak.open("r+b") as handle:
        for seg in segments:
            name = seg.get("matched_db")
            if not name or name not in db_by_name:
                skipped.append({**seg, "reason": "no_unique_db_match"})
                continue
            db_path = db_by_name[name]
            patch_db_path = compact_db_if_needed(db_path, seg["size"], compact_dir)
            if patch_db_path is None:
                skipped.append(
                    {**seg, "reason": f"db_too_large_after_compact:{db_path.stat().st_size}>{seg['size']}"}
                )
                continue
            db_size = patch_db_path.stat().st_size
            qc = quick_check_db(patch_db_path)
            if qc != "ok":
                skipped.append({**seg, "reason": f"source_quick_check:{qc}"})
                continue
            handle.seek(seg["offset"])
            handle.write(patch_db_path.read_bytes())
            if db_size < seg["size"]:
                handle.write(b"\x00" * (seg["size"] - db_size))
            patched.append(
                {
                    "db": name,
                    "offset": seg["offset"],
                    "old_region_size": seg["size"],
                    "new_db_size": db_size,
                    "padding": seg["size"] - db_size,
                    "quick_check": qc,
                    "used_compact_db": str(patch_db_path) if patch_db_path != db_path else "",
                }
            )
    return {"patched": patched, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-pak", required=True)
    parser.add_argument("--db-dir", default="work_db_vi_mistral")
    parser.add_argument("--output-pak", default="TiengViet_99_P_direct_patch.pak")
    parser.add_argument("--scan-only", action="store_true")
    args = parser.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    base_pak = Path(args.base_pak)
    db_dir = Path(args.db_dir)
    output_pak = Path(args.output_pak)

    segments = scan_pak(base_pak, db_dir)
    (REPORT_DIR / "sqlite_segments.json").write_text(
        json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if args.scan_only:
        print(json.dumps({"segments": len(segments)}, ensure_ascii=False, indent=2))
        return

    result = patch_pak(base_pak, output_pak, db_dir, segments)
    (REPORT_DIR / "patch_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "segments": len(segments),
                "patched": len(result["patched"]),
                "skipped": len(result["skipped"]),
                "output_pak": str(output_pak),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
