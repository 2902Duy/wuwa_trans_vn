# Bộ Prompt Hỗ Trợ Dịch Thuật (Translation Prompt Pack)

Thư mục này chứa các tệp prompt và quy tắc chi tiết dùng để dịch từng nhóm dữ liệu của game Wuthering Waves sang tiếng Việt một cách chuẩn xác và nhất quán.

## Mục Tiêu Chung
- **Dịch có chọn lọc**: Chỉ dịch những phần mô tả thực sự cần thiết.
- **Giữ nguyên tên riêng**: Tất cả các tên riêng được quy định giữ tiếng Anh sẽ tuyệt đối không dịch.
- **Bảo toàn định dạng game**: Giữ nguyên toàn bộ placeholder, thẻ định dạng (tag HTML/game), và các token đặc biệt.
- **Tự động phát hiện cập nhật**: Khi có phiên bản game mới, sử dụng script phát hiện thay đổi để lọc các dòng mới hoặc nguồn (source) bị thay đổi, từ đó xuất file dữ liệu đầu vào (batch input) tương ứng cho từng prompt.

---

## Danh Sách Các Prompt & Quy Tắc

Dưới đây là sơ đồ liên kết giữa các tài liệu hướng dẫn và prompt trong gói này:

- **Thuật ngữ & Quy tắc chung:**
  - [shared_glossary.md](shared_glossary.md): Lưu trữ toàn bộ thuật ngữ hệ thống bắt buộc giữ nguyên tiếng Anh.
  - [keep_english_rules.md](keep_english_rules.md): Các quy tắc loại trừ (các nhóm văn bản/dòng game tự động giữ nguyên tiếng Anh, không gửi dịch).
  - [file_classification.md](file_classification.md): Bảng phân loại chi tiết các file JSON, bảng (table), khóa chính (primary key) và cách điều phối sang prompt phù hợp.

- **Các Prompt Dịch Thuật Chi Tiết:**
  - [rc_description_prompt.md](rc_description_prompt.md): Prompt dịch chi tiết chuỗi cộng hưởng (Resonance Chain) trong file `lang_multi_text.json`.
  - [phantom_skill_prompt.md](phantom_skill_prompt.md): Prompt dịch mô tả kỹ năng Echo (Echo Skill) trong file `lang_phantom.json`.
  - [echo_set_prompt.md](echo_set_prompt.md): Prompt dịch hiệu ứng kích hoạt set và cốt truyện (lore) của set Echo trong file `lang_phantom.json`.
  - [weapon_prompt.md](weapon_prompt.md): Prompt dịch mô tả, lore và hiệu ứng kích hoạt của Vũ khí trong file `lang_weapon.json`.
  - [monster_description_prompt.md](monster_description_prompt.md): Prompt dịch mô tả sinh thái và cốt truyện quái vật trong file `lang_monster_Info.json`.
  - [skill_description_prompt.md](skill_description_prompt.md): Prompt dịch mô tả kỹ năng chủ động/bị động của Nhân vật trong file `lang_multi_text.json`.
  - [story_dialogue_prompt.md](story_dialogue_prompt.md): Prompt dịch hội thoại, cốt truyện nhiệm vụ và phụ đề cắt cảnh trong `lang_quest_chapter.json`, `lang_subtitle_text.json`, và `lang_multi_text.json`.
  - [quest_prompt.md](quest_prompt.md): Prompt dịch tên nhiệm vụ, mục tiêu nhiệm vụ và chỉ dẫn quest.
  - [item_prompt.md](item_prompt.md): Prompt dịch mô tả, lore ngắn và công dụng vật phẩm/nguyên liệu.
  - [ui_prompt.md](ui_prompt.md): Prompt dịch menu, nút bấm, nhãn UI và hướng dẫn thao tác ngắn.
  - [system_text_prompt.md](system_text_prompt.md): Prompt dịch lỗi hệ thống, thông báo kỹ thuật, điều kiện mở khóa và mail hệ thống.
  - [lore_prompt.md](lore_prompt.md): Prompt dịch sổ tay, archive, loading tips dài, tài liệu thế giới và lore dài.
  - [name_title_prompt.md](name_title_prompt.md): Prompt xử lý tên riêng, speaker name, title ngắn và các dòng cần giữ nguyên.

---

## Quy Trình Xử Lý Khi Có Phiên Bản Mới

### Bước 1: Chỉ chạy kiểm tra (Check & Export Batches)

Nếu bạn có thư mục chứa dữ liệu bản cũ tại:
`mistral_translate_work/review_translated_only`

Và dữ liệu của phiên bản mới đã được xuất ra tại:
`mistral_translate_work/new_review`

Hãy chạy lệnh sau để phân tích thay đổi:
```powershell
python tools/check_translation_updates.py --old-dir mistral_translate_work/review_translated_only --new-dir mistral_translate_work/new_review --out-dir mistral_translate_work/update_check
```

**Kết quả đầu ra bao gồm:**
* `update_report.json`: Thống kê các dòng mới, dòng bị thay đổi source tiếng Anh, hoặc dòng cần giữ nguyên tiếng Anh.
* `batches/*.txt`: Danh sách dữ liệu thô đầu vào phân chia theo từng loại prompt để sẵn sàng gửi dịch.
* `keep_english_patch.json`: File chứa các dòng được định sẵn quy tắc `translation_vi = source_en` (được vá trực tiếp, không cần tốn phí dịch).

> [NOTE]
> Sau khi có bản dịch cho các file batch, hệ thống sẽ thực hiện ánh xạ (map) ngược lại dữ liệu game dựa trên tổ hợp khóa: `file_name` + `table` + `primary_key` + `column` + `source_en`.

---

### Bước 2: Chạy quy trình tự động (Check + Gửi Dịch + Áp Dụng)

#### Chạy thử nghiệm (Dry-run) để xem trước các dòng sẽ dịch:
```powershell
python tools/run_translation_update_pipeline.py --old-dir mistral_translate_work/review_translated_only --new-dir mistral_translate_work/new_review --work-dir mistral_translate_work/update_run --dry-run
```

#### Chạy thực tế (Gửi dịch qua Mistral API và áp dụng vào thư mục đích):
```powershell
python tools/run_translation_update_pipeline.py --old-dir mistral_translate_work/review_translated_only --new-dir mistral_translate_work/new_review --work-dir mistral_translate_work/update_run --apply
```

**Các bước xử lý tự động của Runner:**
1. Gọi script `check_translation_updates.py` để phân loại và gắn tag cho từng dòng dữ liệu.
2. Tự động áp dụng bản vá tiếng Anh (patch) cho các dòng được định nghĩa trong [keep_english_rules.md](keep_english_rules.md).
3. Gửi các batch cần dịch tới mô hình ngôn ngữ lớn (LLM) kèm theo Prompt tương ứng của nhóm đó.
4. Kiểm tra và xác thực (Validate) tính toàn vẹn của các placeholder/tag/token trước khi nhận bản dịch.
5. Sao lưu (Backup) các tệp tin trước khi áp dụng đè bản dịch vào `mistral_translate_work/backups/update_pipeline_apply_*`.
6. Xuất báo cáo tổng quan quy trình tại `update_run/pipeline_report.json`.

> [WARNING]
> Nếu có bất kỳ dòng dịch nào không vượt qua bước kiểm tra định dạng (validate failed), runner sẽ bỏ qua dòng đó và không ghi đè vào dữ liệu game để tránh lỗi crash game. Bạn có thể kiểm tra danh sách các dòng bị lỗi tại:
> `mistral_translate_work/update_run/translations_failed.json`
