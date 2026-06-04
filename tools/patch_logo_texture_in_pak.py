import argparse
import json
from pathlib import Path

from PIL import Image


WIDTH = 857
HEIGHT = 515
RAW_SIZE = WIDTH * HEIGHT * 4
UEXP_RAW_OFFSET = 212
REPORT = Path("mistral_translate_work/reports/direct_pak_patch/logo_patch_result.json")


def find_uexp_offset(pak: bytes, reference_uexp: bytes) -> int:
    for start in (0, 128, 192, 200, 212):
        marker = reference_uexp[start : start + 64]
        pos = pak.find(marker)
        if pos >= 0:
            return pos - start
    raise RuntimeError("Could not locate T_LogoEn.uexp bytes inside pak")


def make_raw_bgra(image_path: Path) -> bytes:
    image = Image.open(image_path).convert("RGBA")
    image.thumbnail((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    x = (WIDTH - image.width) // 2
    y = (HEIGHT - image.height) // 2
    canvas.alpha_composite(image, (x, y))

    raw = canvas.tobytes("raw", "BGRA")
    if len(raw) != RAW_SIZE:
        raise RuntimeError(f"Unexpected raw size: {len(raw)} != {RAW_SIZE}")
    return raw


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pak", required=True, type=Path)
    parser.add_argument("--reference-uexp", required=True, type=Path)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    pak = bytearray(args.pak.read_bytes())
    reference_uexp = args.reference_uexp.read_bytes()
    uexp_offset = find_uexp_offset(bytes(pak), reference_uexp)
    raw_offset = uexp_offset + UEXP_RAW_OFFSET
    end = raw_offset + RAW_SIZE
    if end > len(pak):
        raise RuntimeError("Computed texture range is outside pak")

    raw = make_raw_bgra(args.image)
    pak[raw_offset:end] = raw
    args.output.write_bytes(pak)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "pak": str(args.pak),
        "output": str(args.output),
        "image": str(args.image),
        "reference_uexp": str(args.reference_uexp),
        "texture": "T_LogoEn",
        "format": "PF_B8G8R8A8",
        "size": [WIDTH, HEIGHT],
        "uexp_offset": uexp_offset,
        "raw_offset": raw_offset,
        "raw_size": RAW_SIZE,
    }
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
