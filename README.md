# Wuthering Waves Vietnamese Mod Translation Project (`wuwa_trans_vn`)

Chào mừng bạn đến với kho lưu trữ chính của dự án dịch thuật mod tiếng Việt cho Wuthering Waves. Kho lưu trữ này quản lý bộ quy tắc dịch thuật (prompt rules), từ điển thuật ngữ chuyên ngành (glossary), và các công cụ/script tự động hóa toàn bộ luồng xử lý bản dịch, kiểm định (audit) và đóng gói mod `.pak`.

Dự án này tích hợp một **Custom Skill** chạy trực tiếp trong chat terminal của Antigravity (hoặc Claude Code) để điều phối nhanh toàn bộ pipeline dịch thuật.

---

## 1. Hướng dẫn cài đặt Custom Skill `/wuwa`
Custom Skill `/wuwa` cho phép bạn gọi nhanh các luồng công việc tự động ngay từ khung chat.

Để đăng ký phím tắt này trên máy của bạn (hoặc máy khác), chỉ cần mở terminal tại thư mục gốc của dự án và chạy:
```powershell
python tools/install_skill.py
```
*Script sẽ tự động đăng ký skill `wuwa` vào cấu hình Antigravity toàn cục và dự án cục bộ. Từ đó, bạn có thể gõ trực tiếp `/wuwa` trong khung chat để xem hướng dẫn.*

---

## 2. Hướng dẫn sử dụng các Script Workflow `/wuwa`

Dưới đây là các câu lệnh chính của pipeline dịch thuật:

### Bước A: Tự động cập nhật từ khóa (Keywords) khi có phiên bản mới
Khi game ra phiên bản mới, ta cần quét các từ khóa mới (Vũ khí, Quái vật, Nhân vật chơi được) từ dữ liệu phân tách để cập nhật vào bộ quy tắc dịch:
```powershell
python tools/update_keep_rules.py
```
*Lưu ý: Script này tự động gộp (merge) và sắp xếp bảng từ khóa sạch sẽ trong `keep_english_rules.md` và `shared_glossary.md` mà không ghi đè làm mất phân loại 5-sao/4-sao có sẵn.*

### Bước B: Dịch thuật nội dung mới bằng LLM (Mistral/Gemini)
Để bắt đầu một tiến trình dịch tự động song song đa luồng qua API:
```powershell
python mistral_game_translate.py translate --max-keys 5 --batch-size 12 --max-chars 3600
```

### Bước C: Kiểm định chất lượng dịch thuật (Audit & Review)
Chạy script audit dựa trên tập hợp quy tắc để phát hiện lỗi định dạng, tag game hoặc sai thuật ngữ:
```powershell
python mistral_game_translate.py audit
```
Hoặc dùng AI hỗ trợ review các câu thoại/lore phức tạp:
```powershell
python mistral_game_translate.py review-ai --limit 500
```

### Bước D: Đồng bộ hóa tệp JSON (Nếu sửa đổi thủ công)
Nếu bạn chỉnh sửa bản dịch trực tiếp trên các file JSON phân tách tại `split_by_prompt/json/`, chạy script sau để đồng bộ ngược lại cơ sở dữ liệu làm việc SQLite:
```powershell
python tools/sync_split_json_to_db.py
```

### Bước E: Biên dịch & Nhập vào Cơ sở dữ liệu mod
Biên dịch bộ nhớ cache dịch thuật và ghi đè vào các cơ sở dữ liệu SQLite dưới thư mục `work_db_vi_mistral/`:
```powershell
python mistral_game_translate.py import --out-db-dir work_db_vi_mistral --force
```

### Bước F: Kiểm tra độ nhất quán & Đóng gói Pak
Chạy script xác minh tính toàn vẹn của dữ liệu:
```powershell
python verify_changes.py
```
Sau đó, đóng gói thư mục dữ liệu thành tệp mod `.pak` sử dụng công cụ `repak`:
```powershell
repak pack -v <directory_path>
```

---

## 3. Hệ thống Quy tắc dịch thuật & Quy định xưng hô (Prompts)

Toàn bộ prompt của dự án nằm trong thư mục `mistral_translate_work/prompts/`:
*   **[character_voice_map.md](file:///C:/Users/tduy2/Documents/antigravity/silly-darwin/mistral_translate_work/prompts/character_voice_map.md)**: Bản đồ giọng nói và xưng hô của các playable Resonators.
    *   *Quy tắc đặc biệt*: Các nhân vật nữ trưởng thành (Changli, Taoqi, Yinlin, Mornye) khi xưng hô với Rover phải sử dụng sắc thái lịch sự, chừng mực: **Tự xưng `Tôi` - gọi Rover là `{Male=cậu;Female=em}`**. Tuyệt đối không dùng xưng hô "Chị - Em" hay "Chị + Tên" để giữ khoảng cách chuyên nghiệp và tôn trọng vai vế.
*   **[story_dialogue_prompt.md](file:///C:/Users/tduy2/Documents/antigravity/silly-darwin/mistral_translate_work/prompts/story_dialogue_prompt.md)**: Quy định dịch cốt truyện, hội thoại, sắc thái xưng hô của NPC và Rover.
*   **[keep_english_rules.md](file:///C:/Users/tduy2/Documents/antigravity/silly-darwin/mistral_translate_work/prompts/keep_english_rules.md)**: Danh sách các tên riêng, kỹ năng, debuff phải giữ nguyên tiếng Anh để tránh loãng dịch thuật.
*   **[shared_glossary.md](file:///C:/Users/tduy2/Documents/antigravity/silly-darwin/mistral_translate_work/prompts/shared_glossary.md)**: Từ điển thuật ngữ giao diện (UI), hệ thống và tài nguyên chính thức.

---

## 4. repak (Unreal Engine .pak tool)

Dự án này tích hợp công cụ `repak` để đóng gói/giải nén tệp mod `.pak`.

Library and CLI tool for working with Unreal Engine .pak files.

 - Supports reading and writing a wide range of versions
 - Easy to use API while providing low level control:
   - Only parses index initially and reads file data upon request
   - Can rewrite index in place to perform append or delete operations without rewriting entire pak

### CLI usage
```console
$ repak --help
Usage: repak [OPTIONS] <COMMAND>

Commands:
  info       Print .pak info
  list       List .pak files
  hash-list  List .pak files and the SHA256 of their contents. Useful for finding differences between paks
  unpack     Unpack .pak file
  pack       Pack directory into .pak file
  get        Reads a single file to stdout
  help       Print this message or the help of the given subcommand(s)

Options:
  -a, --aes-key <AES_KEY>  256 bit AES encryption key as base64 or hex string if the pak is encrypted
  -h, --help               Print help
  -V, --version            Print version
```

#### Packing
```console
$ find mod
mod
mod/assets
mod/assets/AssetA.uasset
mod/assets/AssetA.uexp

$ repak pack -v mod
packing assets/AssetA.uasset
packing assets/AssetA.uexp
Packed 4 files to mod.pak

$ repak list mod.pak
assets/AssetA.uasset
assets/AssetA.uexp
```

#### Unpacking
```console
$ repak --aes-key 0x12345678 unpack MyEncryptedGame.pak
Unpacked 12345 files to MyEncryptedGame from MyEncryptedGame.pak
```

---

## 5. Bản quyền & Đóng góp
- Cải tiến mod dịch thuật thuộc về cộng đồng dịch giả Wuthering Waves Việt Nam.
- Công cụ `repak` được phát hành theo giấy phép MIT.
