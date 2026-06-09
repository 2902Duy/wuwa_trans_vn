import pandas as pd

excel_path = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\ui_translation_pack\ui_all.xlsx"

try:
    xl = pd.ExcelFile(excel_path)
    print("Sheets:", xl.sheet_names)
    df = xl.parse(xl.sheet_names[0], keep_default_na=False)
    print("Columns:", list(df.columns))
    print("Shape:", df.shape)
    print("First row:\n", df.iloc[0].to_dict())
except Exception as e:
    print("Error:", e)
