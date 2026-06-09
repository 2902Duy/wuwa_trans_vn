import marshal
import dis
import sys

pyc_path = r"__pycache__/mistral_game_translate.cpython-314.pyc"

try:
    with open(pyc_path, "rb") as f:
        f.read(16) # Header in python 3.14 has 16 bytes
        code_obj = marshal.load(f)
        
    print("Code object loaded successfully.")
    with open("disassembly.txt", "w", encoding="utf-8") as out:
        dis.dis(code_obj, file=out)
    print("Wrote disassembly to disassembly.txt")
except Exception as e:
    print("Error:", e)
