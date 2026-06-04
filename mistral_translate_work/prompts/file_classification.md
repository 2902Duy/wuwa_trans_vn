# Hướng Dẫn Phân Loại File Dữ Liệu (File Classification Guide)

Tài liệu này hướng dẫn cách nhận biết tệp tin JSON nào chứa loại nội dung gì trong game, dựa trên cấu trúc hiện tại trong thư mục dữ liệu `mistral_translate_work/review_translated_only`. Từ đó, hệ thống sẽ ánh xạ và áp dụng đúng prompt hoặc quy tắc dịch.

---

## Quy Tắc Định Danh Chung

Mỗi dòng dữ liệu trong các file JSON thường bao gồm các trường thông tin sau:
* `database`: Tên cơ sở dữ liệu gốc của game.
* `table`: Bảng gốc lưu trữ dòng dữ liệu đó (đây là thông tin quan trọng nhất để phân loại).
* `primary_key`: ID/Khóa chính của dòng, dùng để nhận diện kiểu dữ liệu con (subtype).
* `source_en`: Văn bản tiếng Anh gốc cần dịch.
* `translation_vi`: Bản dịch tiếng Việt tương ứng.

Khi ánh xạ (map) hoặc đối chiếu bản dịch mới, không được chỉ sử dụng `primary_key` độc lập vì nhiều file JSON khác nhau có thể chứa các table có khóa trùng nhau. Bắt buộc phải sử dụng tổ hợp khóa duy nhất:
`file_name` + `table` + `primary_key` + `column`

Đối với riêng file `lang_multi_text.json` (và các file chia nửa của nó là `lang_multi_text_1sthalf.json`, `lang_multi_text_2ndhalf.json`), trường `primary_key` đóng vai trò tối quan trọng vì toàn bộ bản ghi đều nằm chung trong một table duy nhất có tên là `MultiText`.

---

## Bảng Tra Cứu Quy Tắc Dịch Cho Toàn Bộ File Dữ Liệu Hiện Có

Dưới đây là danh sách phân loại chi tiết cho tất cả 65 tệp tin JSON được tìm thấy trong thư mục dữ liệu nguồn:

| Tệp tin JSON | Tên Bảng (Table) hoặc Khóa (Key) | Nội dung | Cách xử lý | Quy tắc / Prompt áp dụng |
| :--- | :--- | :--- | :--- | :--- |
| **Nhóm Chiến Đấu & Nhân Vật** | | | | |
| `lang_weapon.json` | `WeaponConf` | Tên vũ khí, cốt truyện (lore), hiệu ứng vũ khí | Giữ nguyên tên vũ khí; dịch lore & hiệu ứng | [weapon_prompt.md](weapon_prompt.md), [keep_english_rules.md](keep_english_rules.md) |
| `lang_weapon.json` | `WeaponReson` | Tên nội tại/hiệu ứng cộng hưởng của vũ khí | Mặc định skip (không dịch tự động) | Dịch thủ công nếu cần |
| `lang_phantom.json` | `PhantomItem` | Tên Echo, văn bản UI của Echo | Giữ nguyên tên Echo; dịch các văn bản UI | [keep_english_rules.md](keep_english_rules.md) |
| `lang_phantom.json` | `PhantomFetter` | Tên bộ Echo, hiệu ứng bộ, lore bộ Echo | Giữ nguyên tên bộ; dịch hiệu ứng & lore | [echo_set_prompt.md](echo_set_prompt.md), [keep_english_rules.md](keep_english_rules.md) |
| `lang_phantom.json` | `PhantomSkill` | Mô tả kỹ năng Echo (Echo Skill) | Dịch mô tả; giữ nguyên tên tiếng Anh của Echo | [phantom_skill_prompt.md](phantom_skill_prompt.md) |
| `lang_monster_Info.json` | `MonsterInfo` | Tên quái vật, mô tả sinh thái, lore quái | Giữ nguyên tên riêng quái; dịch mô tả & lore | [monster_description_prompt.md](monster_description_prompt.md) |
| `lang_monster_Info.json` | `MonsterPerch` | Khu vực xuất hiện/nơi sống của quái vật | Tên địa danh/UI | Không dịch tự động bằng pipeline |
| `lang_monster_Info.json` | `MonsterRarity` | Cấp độ hiếm/mạnh của quái vật | Văn bản UI ngắn | Không dịch tự động bằng pipeline |
| `lang_skill.json` | `Skill` | Tên kỹ năng ngắn (hệ thống) | Giữ nguyên tiếng Anh | [keep_english_rules.md](keep_english_rules.md) |
| `lang_skill.json` | `SkillType` | Loại kỹ năng (ví dụ: `Resonance Liberation`) | Giữ nguyên tiếng Anh theo bảng thuật ngữ | [shared_glossary.md](shared_glossary.md) |
| `lang_skillTree.json` | `RoleSkillTreeInfo` | Tên các node/nhánh trên cây kỹ năng nhân vật | Giữ nguyên tiếng Anh | [keep_english_rules.md](keep_english_rules.md) |
| `lang_skillTree.json` | `SkillInput` | Hướng dẫn thao tác/nhập kỹ năng | Dịch mô tả thao tác; giữ nguyên tên kỹ năng riêng | Dùng chung [skill_description_prompt.md](skill_description_prompt.md) |
| `lang_skillTree.json` | `SkillCondition` | Điều kiện mở khóa kỹ năng nhân vật | Văn bản UI ngắn | Dịch thủ công nếu cần |
| `lang_role.json` | `RoleInfo` | Tên nhân vật, danh hiệu, mô tả nhân vật | Giữ nguyên tên nhân vật; dịch mô tả tùy style | Chưa tự động hóa trong pipeline |
| `lang_roleDescription.json` | `RoleDescription` | Giới thiệu, tiểu sử ngắn của nhân vật | Dịch mô tả tiểu sử, giữ nguyên tên riêng | Dịch lore nhân vật |
| `lang_roleInfluence.json` | `RoleInfluence` | Chỉ số hảo cảm, ảnh hưởng của nhân vật | Dịch UI chỉ số hảo cảm | Dịch UI chung |
| `lang_role_reson.json` | `RoleResonance` | Văn bản đột phá/cộng hưởng nhân vật | Dịch hệ thống (thường chứa chỉ số đột phá) | Dịch UI chung / Bán tự động |
| `lang_resonate_chain.json` | `ResonateChain` | Tên chung/UI liên quan đến Resonance Chain | Giữ nguyên thuật ngữ Resonance Chain | [shared_glossary.md](shared_glossary.md) |
| **Nhóm Nhiệm Vụ & Cốt Truyện** | | | | |
| `lang_quest_chapter.json` | `QuestChapter` | Tên chương, tên nhiệm vụ chính/phụ | Dịch tên nhiệm vụ văn phong tự nhiên | [quest_prompt.md](quest_prompt.md) |
| `lang_subtitle_text.json` | `SubtitleText` | Phụ đề video cắt cảnh, hội thoại cốt truyện | Dịch hội thoại văn phong tự nhiên, giữ tag | [story_dialogue_prompt.md](story_dialogue_prompt.md) |
| `lang_multi_text.json` | `Quest_*` | Tên, mô tả và lời thoại nhiệm vụ | Mục tiêu/mô tả dùng quest prompt; thoại dùng story prompt | [quest_prompt.md](quest_prompt.md), [story_dialogue_prompt.md](story_dialogue_prompt.md) |
| `lang_multi_text.json` | `ResonantChain_*_NodeName` | Tên các nút chuỗi cộng hưởng (RC) | Giữ nguyên tiếng Anh | [keep_english_rules.md](keep_english_rules.md) |
| `lang_multi_text.json` | `ResonantChain_*_AttributesDescription` | Mô tả chi tiết hiệu ứng RC | Dịch mô tả; giữ nguyên tên gốc trong các tag | [rc_description_prompt.md](rc_description_prompt.md) |
| `lang_multi_text.json` | `*_SkillName` | Tên kỹ năng nhân vật / kỹ năng hệ thống | Giữ nguyên tiếng Anh | [keep_english_rules.md](keep_english_rules.md) |
| `lang_multi_text.json` | `*_SkillDescribe`, `*SkillDescription*` | Mô tả chi tiết kỹ năng nhân vật | Dịch mô tả; giữ tên skill và thuật ngữ | [skill_description_prompt.md](skill_description_prompt.md) |
| `lang_multi_text_1sthalf.json` | `MultiText` | (Nửa đầu của multi_text) Dữ liệu tổng hợp | Phân loại theo Key tương tự multi_text gốc | Áp dụng theo key con tương ứng |
| `lang_multi_text_2ndhalf.json` | `MultiText` | (Nửa sau của multi_text) Dữ liệu tổng hợp | Phân loại theo Key tương tự multi_text gốc | Áp dụng theo key con tương ứng |
| **Nhóm Vật Phẩm & Sinh Hoạt** | | | | |
| `lang_item.json` | `Item` | Tên vật phẩm, mô tả vật phẩm và lore vật phẩm | Tên vật phẩm giữ tiếng Anh; dịch mô tả & lore | [item_prompt.md](item_prompt.md) |
| `lang_cook.json` | `Cook` | Công thức nấu ăn, tên món ăn, mô tả món ăn | Tên món giữ tiếng Anh; dịch mô tả hiệu ứng ăn | [item_prompt.md](item_prompt.md) |
| `lang_compose.json` | `Compose` | Ghép vật phẩm, chế tạo nguyên liệu | Dịch giao diện ghép, tên nguyên liệu dịch/giữ | [item_prompt.md](item_prompt.md), [ui_prompt.md](ui_prompt.md) |
| `lang_forge.json` | `Forge` | Giao diện rèn vũ khí, chế tạo trang bị | Dịch giao diện rèn, giữ tên vũ khí | [item_prompt.md](item_prompt.md), [ui_prompt.md](ui_prompt.md) |
| `lang_calabash.json` | `Calabash` | Cấp độ bình Calabash, UI hấp thụ Echo | Dịch thuộc tính bình Calabash, giữ nguyên Echo | Dịch UI/Hệ thống |
| `lang_explore_skill.json` | `ExploreSkill` | Kỹ năng khám phá bản đồ (Dây móc, Nam châm...) | Dịch mô tả kỹ năng khám phá | Dịch UI/Hệ thống |
| `lang_explore_progress.json` | `ExploreProgress` | Tiến độ khám phá các khu vực | Dịch UI hiển thị tiến trình | Dịch UI chung |
| `lang_handbook.json` | `Handbook` | Sổ tay thế giới, danh sách quái, cốt truyện lưu trữ | Dịch mô tả sổ tay và văn bản cốt truyện dài | [lore_prompt.md](lore_prompt.md) |
| `lang_handbook_entrance.json` | `HandbookEntrance` | Các nút bấm lối vào của Sổ tay | Dịch tên các lối vào UI | Dịch UI chung |
| **Nhóm Địa Lý & Bản Đồ** | | | | |
| `lang_area.json` | `Area` | Tên khu vực, địa danh trên bản đồ | Giữ nguyên tiếng Anh (ví dụ: Jinzhou, Taoyuan Vale) | Quy tắc địa lý |
| `lang_country.json` | `Country` | Tên quốc gia, lãnh thổ thế giới game | Giữ nguyên tiếng Anh (ví dụ: Huanglong) | Quy tắc địa lý |
| `lang_map_mark.json` | `MapMark` | Tên điểm đánh dấu, ghi chú trên bản đồ | Dịch mô tả điểm đánh dấu, giữ nguyên địa danh tiếng Anh | Dịch UI/Bản đồ |
| **Nhóm NPC & Người Nói** | | | | |
| `lang_npc_headinfo.json` | `NpcHeadInfo` | Tên NPC hiện trên đầu, chức danh NPC | Giữ nguyên tên riêng NPC; dịch chức danh | [name_title_prompt.md](name_title_prompt.md) |
| `lang_speaker.json` | `Speaker` | Tên của người phát ngôn hiển thị trong đối thoại | Giữ nguyên tiếng Anh (tên nhân vật/NPC) | [name_title_prompt.md](name_title_prompt.md) |
| **Nhóm Giao Diện & Hệ Thống** | | | | |
| `lang_text.json` | `Text` | Bản dịch giao diện (UI) chung của game | Dịch ngắn gọn, rõ ràng theo ngữ cảnh UI | [ui_prompt.md](ui_prompt.md) |
| `lang_ui.json` | `Ui` | Giao diện UI màn hình, thông báo hệ thống | Dịch ngắn gọn, rõ ràng | [ui_prompt.md](ui_prompt.md) |
| `lang_menu.json` | `Menu` | Các nút bấm và mục lục trong Menu UI | Dịch ngắn gọn, chuẩn hóa theo game gốc | [ui_prompt.md](ui_prompt.md) |
| `lang_UiHotKot.json` | `UiHotKey` | Hướng dẫn phím tắt giao diện | Dịch phím tắt UI, giữ nguyên tên phím (F, G...) | [ui_prompt.md](ui_prompt.md) |
| `lang_accesspath.json` | `AccessPath` | Hướng dẫn cách nhận/sở hữu vật phẩm | Dịch mô tả nguồn nhận vật phẩm | [ui_prompt.md](ui_prompt.md), [item_prompt.md](item_prompt.md) |
| `lang_advice.json` | `Advice` | Lời khuyên, gợi ý hệ thống | Dịch mô tả gợi ý | [ui_prompt.md](ui_prompt.md) |
| `lang_bag.json` | `Bag` | Giao diện túi đồ, phân loại ngăn túi | Dịch tên các ngăn túi đồ | [ui_prompt.md](ui_prompt.md) |
| `lang_cgVideo.json` | `CgVideo` | Tên video CG, mô tả cảnh phim cắt cảnh | Dịch mô tả video | [story_dialogue_prompt.md](story_dialogue_prompt.md) |
| `lang_condition.json` | `Condition` | Điều kiện mở khóa tính năng/phó bản | Dịch câu mô tả điều kiện | [system_text_prompt.md](system_text_prompt.md) |
| `lang_confirmbox.json` | `ConfirmBox` | Nút xác nhận, hủy, thông báo trong hộp thoại | Dịch ngắn gọn (Xác nhận, Hủy, Đồng ý...) | [ui_prompt.md](ui_prompt.md) |
| `lang_cycle_tower.json` | `CycleTower` | Giao diện Tháp Nghịch Cảnh (Tower of Adversity) | Dịch thuộc tính buff/debuff phó bản | Dịch UI/Hệ thống |
| `lang_detection.json` | `Detection` | Giao diện radar dò tìm tài nguyên | Dịch mô tả hoạt động dò tìm | Dịch UI/Hệ thống |
| `lang_element_info.json` | `ElementInfo` | Thông tin thuộc tính nguyên tố | Giữ nguyên tên nguyên tố theo glossary | Dịch UI/Hệ thống |
| `lang_error_code.json` | `ErrorCode` | Thông báo lỗi hệ thống, mất kết nối | Dịch câu thông báo lỗi chuẩn kỹ thuật | [system_text_prompt.md](system_text_prompt.md) |
| `lang_favor.json` | `Favor` | Lời thoại hảo cảm, cấp độ hảo cảm nhân vật | Dịch lời thoại hảo cảm tự nhiên | [story_dialogue_prompt.md](story_dialogue_prompt.md) |
| `lang_function.json` | `Function` | Khóa/Mở khóa tính năng hệ thống | Dịch tên tính năng hệ thống | Dịch UI/Hệ thống |
| `lang_generic_tips.json` | `GenericTips` | Gợi ý chung, hướng dẫn nhanh lúc tải cảnh | Dịch hướng dẫn ngắn gọn | [ui_prompt.md](ui_prompt.md) |
| `lang_help.json` | `Help` | Tài liệu trợ giúp, giải thích tính năng | Dịch mô tả chi tiết trợ giúp | [system_text_prompt.md](system_text_prompt.md) |
| `lang_hot_patch.json` | `HotPatch` | Thông báo cập nhật bản vá nóng | Dịch thông báo cập nhật | [system_text_prompt.md](system_text_prompt.md) |
| `lang_influence.json` | `Influence` | Danh tiếng khu vực, cấp bậc uy tín | Dịch cấp bậc danh tiếng | Dịch UI/Hệ thống |
| `lang_infodisplay.json` | `InfoDisplay` | Giao diện hiển thị thông tin nhân vật, tài liệu dài | UI dùng ui prompt; tài liệu dài dùng lore prompt | [ui_prompt.md](ui_prompt.md), [lore_prompt.md](lore_prompt.md) |
| `lang_instance_dungeon.json` | `InstanceDungeon` | Thông tin các phó bản khiêu chiến | Dịch mô tả phó bản | Dịch UI/Hệ thống |
| `lang_instance_dungeon_entrance.json`|`InstanceDungeonEntrance`| Lối vào phó bản khiêu chiến | Dịch giao diện lối vào phó bản | Dịch UI/Hệ thống |
| `lang_loadingtips.json` | `LoadingTips` | Gợi ý hiển thị ở màn hình loading | Ngắn dùng UI; dài/lore dùng lore prompt | [ui_prompt.md](ui_prompt.md), [lore_prompt.md](lore_prompt.md) |
| `lang_mail.json` | `Mail` | Giao diện hòm thư, tiêu đề thư | Dịch giao diện hòm thư | [system_text_prompt.md](system_text_prompt.md) |
| `lang_mapping.json` | `Mapping` | Ánh xạ phím bấm, nút điều khiển | Dịch tên phím điều khiển | Dịch UI chung |
| `lang_once_tower_challenge.json`|`OnceTowerChallenge`| Tháp thử thách một lần | Dịch mô tả buff tháp | Dịch UI/Hệ thống |
| `lang_payshop.json` | `PayShop` | Cửa hàng nạp tiền, vật phẩm mua bằng tiền | Dịch mô tả gói nạp | [ui_prompt.md](ui_prompt.md) |
| `lang_photograph.json` | `Photograph` | Giao diện chụp ảnh, kính ngắm | Dịch giao diện chụp ảnh UI | Dịch UI chung |
| `lang_property.json` | `Property` | Thuộc tính chỉ số nhân vật/quái vật | Dịch tên thuộc tính (HP, ATK, DEF...) | Dịch UI chung |
| `lang_questtype.json` | `QuestType` | Loại nhiệm vụ (Nhiệm vụ chính, phụ, sự kiện...) | Dịch loại nhiệm vụ ngắn | Dịch UI chung |
| `lang_revive.json` | `Revive` | Hồi sinh nhân vật, điểm hồi sinh | Dịch giao diện hồi sinh | Dịch UI chung |
| `lang_shop.json` | `Shop` | Cửa hàng trong game, giao diện mua bán | Dịch giao diện shop | Dịch UI chung |
| `lang_time_of_day.json` | `TimeOfDay` | Thời gian trong ngày (Sáng, Trưa, Chiều, Tối) | Dịch tên mốc thời gian | Dịch UI chung |

---

## Quy Tắc Chi Tiết & Hướng Dẫn Dịch Cho Các Nhóm File Mới

### 1. Nhóm Vật Phẩm (lang_item.json)
* **Tên vật phẩm**: Giữ nguyên tiếng Anh (ví dụ: `Lustrous Tide`, `Astrite`), không dịch.
* **Mô tả vật phẩm & Lore**: Dịch sang tiếng Việt tự nhiên. Giữ nguyên các thuật ngữ nằm trong glossary.

### 2. Nhóm Hướng Dẫn & Gợi Ý (lang_guide_new.json, lang_generic_tips.json, lang_loadingtips.json)
* **Đặc điểm**: Chứa hướng dẫn thao tác nút bấm, cơ chế combat.
* **Quy tắc**: Dịch câu hướng dẫn tự nhiên, giữ nguyên phím bấm tiếng Anh (ví dụ: `Press [F] to...` -> `Nhấn [F] để...`).

### 3. Nhóm Giao Diện UI & Menu (lang_text.json, lang_ui.json, lang_menu.json, lang_confirmbox.json)
* **Đặc điểm**: Các từ đơn, cụm từ ngắn trên nút bấm, menu lựa chọn.
* **Quy tắc**: Dịch cực kỳ ngắn gọn, dùng các từ tiếng Việt chuẩn game (ví dụ: `Confirm` -> `Xác nhận`, `Cancel` -> `Hủy`, `Settings` -> `Cài đặt`).

### 4. Nhóm Bản Đồ & Địa Danh (lang_area.json, lang_country.json, lang_map_mark.json)
* **Đặc điểm**: Tên các vùng đất, quốc gia hoặc ghi chú bản đồ.
* **Quy tắc**: **Giữ nguyên chính xác 100% tất cả tên địa danh, quốc gia lớn nhỏ bằng tiếng Anh** (ví dụ: `Jinzhou`, `Huanglong`, `Taoyuan Vale`). Không dịch hoặc Việt hóa tên địa danh.

### 5. Nhóm NPC & Lời Thoại (lang_quest_chapter.json, lang_npc_headinfo.json, lang_speaker.json, lang_subtitle_text.json)
* **Tên NPC / Speaker**: Giữ nguyên tên riêng tiếng Anh của NPC (ví dụ: `Chixia`, `Yangyang`).
* **Hội thoại & Chương nhiệm vụ**: Dịch tự nhiên, giàu cảm xúc, giữ nguyên các tag màu và tag liên kết thông qua [story_dialogue_prompt.md](story_dialogue_prompt.md).

---

## Các Script Chạy Quy Trình Cập Nhật

### 1. Chỉ kiểm tra và xuất tệp batch đầu vào
```powershell
python tools/check_translation_updates.py --old-dir mistral_translate_work/review_translated_only --new-dir mistral_translate_work/new_review --out-dir mistral_translate_work/update_check
```

### 2. Chạy quy trình đầy đủ: Phân loại -> Dịch qua API -> Áp dụng vào game
```powershell
python tools/run_translation_update_pipeline.py --old-dir mistral_translate_work/review_translated_only --new-dir mistral_translate_work/new_review --work-dir mistral_translate_work/update_run --apply
```

### 3. Ý nghĩa của các tệp tin đầu ra quan trọng
* `update_report.json`: Báo cáo phân loại các thay đổi dữ liệu.
* `keep_english_patch.json`: Các dòng tự động gán tiếng Anh.
* `changed_or_new.json`: Tổng hợp tất cả các dòng mới hoặc dòng bị thay đổi source.
* `batches/*.txt`: Tệp batch thô để đưa vào dịch (được tách theo prompt tương ứng).
* `translations_success.json`: Tổng hợp các câu dịch thành công và hợp lệ.
* `translations_failed.json`: Tổng hợp các câu lỗi cấu trúc (cần review lại).
* `pipeline_report.json`: Nhật ký báo cáo hoàn thành quy trình dịch tự động.
