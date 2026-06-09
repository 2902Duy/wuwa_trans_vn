## 2026-06-04T04:02:12Z
You are teamwork_preview_worker.
Your working directory is: C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\worker_m2_corrected
Your task is to modify the existing Python script `C:\Users\tduy2\Documents\antigravity\silly-darwin\correct_ui.py` to fix several issues identified during review, execute it to correct the UI JSON translation files, regenerate the consolidated Excel file `ui_all.xlsx`, and verify that 0 violations remain.

**Required Modifications in `correct_ui.py`**:
1. **Shorter-Before-Longer Replacement Bug**:
   In the list `proper_nouns_replacements` under the block `elif v_type in ["Glossary Translation Violation", "Blacklisted Translation", "Casing Violation"]:`:
   Make sure you sort the list by the length of the Vietnamese target string (first element of each tuple, index 0) in descending order before executing the loop. This ensures that longer phrases (like `"Vết Sẹo"`) are replaced before their substrings (like `"Sẹo"`), which prevents issues like converting `"Vết Sẹo II"` to `"Vết Scar II"` instead of `"Scar II"`.
   Example code to add before the loop:
   ```python
   proper_nouns_replacements.sort(key=lambda x: len(x[0]), reverse=True)
   ```

2. **Targeted Quality Fixes**:
   Under the `# --- FIX LOGIC ---` block (around line 91), add specific `elif` branches or statements for the following split IDs to apply correct Vietnamese translations directly:
   - For split IDs `UI_0011110`, `UI_0011111`, `UI_0011112`:
     Replace `"Place Electro Predator"` with `"Đặt Electro Predator"` (so the translation becomes `"Đặt Electro Predator vào đây. ..."`).
     Example:
     ```python
     elif split_id in ["UI_0011110", "UI_0011111", "UI_0011112"]:
         fixed_translation = fixed_translation.replace("Place Electro Predator", "Đặt Electro Predator")
     ```
   - For split ID `UI_0005605`:
     Set `fixed_translation = "Vật Tư Đặc Biệt"` (source: "Special Supplies").
   - For split ID `UI_0005613`:
     Set `fixed_translation = "Chi Tiết Kỳ Thi"` (source: "Exam Details").
   - For split ID `UI_0007105`:
     Replace `"Attack Phối Hợp"` with `"Tấn Công Phối Hợp"` (source: "Coordinated Attack").
     Example:
     ```python
     elif split_id == "UI_0007105":
         fixed_translation = fixed_translation.replace("Attack Phối Hợp", "Tấn Công Phối Hợp")
     ```
   - For split ID `UI_0007584`:
     Replace `"Nữ hoàng Night tối"` with `"Nữ hoàng Bóng Đêm"` (source: "...Queen of the Night...").
     Example:
     ```python
     elif split_id == "UI_0007584":
         fixed_translation = fixed_translation.replace("Nữ hoàng Night tối", "Nữ hoàng Bóng Đêm")
     ```
   - For split ID `UI_0000672`:
     Set `fixed_translation = "Cửa Hàng Ma He"` (source: "Ma He's Grocers").

**Steps to Execute**:
1. Modify `correct_ui.py` with the changes above (you can use `replace_file_content` or similar tools).
2. Execute the updated `correct_ui.py` script by running `python correct_ui.py` at the project root `C:\Users\tduy2\Documents\antigravity\silly-darwin`.
3. Check the command output to ensure it prints:
   `SUCCESS: All violations fixed, 0 remaining violations!`
4. Verify that:
   - The JSON files are updated.
   - The Excel file `mistral_translate_work\split_by_prompt\ui_translation_pack\ui_all.xlsx` is regenerated and is consistent.
   - The violations report `.agents\explorer_m1\violations_report.json` contains `[]`.

**MANDATORY INTEGRITY WARNING**:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

**Handoff Report**:
Document the modifications, the execution logs, and verify that the 6 split IDs listed above are correctly updated in their respective JSON files. Save your handoff report to `C:\Users\tduy2\Documents\antigravity\silly-darwin\.agents\worker_m2_corrected\handoff.md` and send a message back when completed.
