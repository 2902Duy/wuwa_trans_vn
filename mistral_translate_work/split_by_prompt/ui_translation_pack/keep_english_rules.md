# Quy Tắc Giữ Nguyên Tiếng Anh (Keep English Rules)

Tài liệu này định nghĩa các nhóm dòng văn bản không cần gửi đi dịch qua LLM. Khi hệ thống phát hiện các dòng thỏa mãn các điều kiện dưới đây, hệ thống sẽ tự động gán thẳng giá trị:

```json
"translation_vi": "source_en"
```

Điều này giúp tiết kiệm chi phí dịch thuật API và đảm bảo tính đồng bộ của các tên riêng trong game.

---

## 1. Tên Vũ Khí (Weapon Names)

* **Tệp tin áp dụng**: `lang_weapon.json`
* **Điều kiện lọc**:
  - Tên bảng: `table = "WeaponConf"`
  - Định dạng: Dòng ngắn, dạng tên riêng của vũ khí.
  - Loại trừ: Không chứa các ký tự đặc biệt `{ }`, thẻ định dạng (tag HTML/game), các chỉ số số học, hoặc câu mô tả hiệu ứng.

> [!TIP]
> **Ví dụ giữ nguyên:**
> - `Primordial Broadblade`
> - `Training Broadblade`
> - `Broadblade of night`
> - `Ultrasonic Matrix`
> - `Emerald of Genesis`
> - `Verdant Summit`
> - `Static Mist`
> - `Stringmaster`
> - `Abyss Surges`
> - `Lumingloss`
> - `Discord`
> - `Autumntrace`
> - `Guardian Broadblade`
> - `Broadblade of Voyager`
> - `Aether Strike`
> - `Beguiling Melody`

> [!WARNING]
> **Không áp dụng quy tắc này cho:**
> - Từ đơn lẻ `Weapon` -> Vẫn có thể dịch là `Vũ khí`.
> - Các từ chỉ loại/phân loại vũ khí chính đứng độc lập hoặc trong cụm từ UI (ví dụ: `Sword` -> `Kiếm đơn`, `Broadblade` -> `Đại kiếm`, `Pistols` -> `Súng`, `Gauntlets` -> `Găng tay`, `Rectifier` -> `Pháp khí`).
> - Các câu mô tả cốt truyện (lore) dài của vũ khí.
> - Các dòng mô tả hiệu ứng chứa các chỉ số như `ATK`, `DMG`, `HP`.

---

## 2. Tên Thú Cưng / Echo / Boss / Quái Vật (Echo, Boss & Monster Names)

* **Tệp tin áp dụng**: `lang_phantom.json`, `lang_monster_Info.json`, `lang_condition.json`
* **Điều kiện lọc**:
  - Tên bảng: `table = "PhantomItem"`, `table = "MonsterInfo"`, `table = "Condition"`
  - Định dạng: Dòng ngắn dạng tên riêng của quái vật/Echo/Boss.

> [!TIP]
> **Ví dụ giữ nguyên:**
> - `Vanguard Junrock`
> - `Impulse Predator`
> - `Whiff Whoosh`
> - `Glacio Prism`
> - `Crownless`
> - `Bell-Borne Geochelone`
> - `Seatrail Narwhal`
> - `Inferno Rider`
> - `Hoochief`
> - `Sentinel`
> - `Sentinel Jué`
> - `Impermanence Heron`
> - `Thundering Mephis`
> - `Mourning Aix`
> - `Chasm Rider`
> - `Traffic Illuminator`
> - `Flautist`
> - `Abyssal Gladius`
> - `Aero Predator`

> [!WARNING]
> **Không áp dụng quy tắc này cho:**
> - Từ đơn lẻ `Echo`.
> - Các câu thông báo hệ thống như `Wutrelic Unlocked.`.
> - Các câu mô tả dài về cốt truyện hoặc hành vi của quái vật.

---

## 3. Tên Nhân vật & Địa danh (Resonator & Location Names)

* **Tệp tin áp dụng**: `lang_role.json`, `lang_map.json`, `lang_multi_text.json`
* **Điều kiện lọc**:
  - Tên bảng: `table = "RoleInfo"`, `table = "MapBoundary"`, `table = "MultiText"`
  - Định dạng: Dòng ngắn chứa tên riêng nhân vật hoặc tên địa danh.

> [!TIP]
> **Ví dụ giữ nguyên:**
> > - Nhân vật: `Aalto`, `Abby`, `Aemeath`, `An'ke`, `Augusta`, `Bailian`, `Baizhi`, `Calcharo`, `Camellya`, `Carlotta`, `Changli`, `Chixia`, `Danjin`, `Denia`, `Encore`, `Geshu Lin`, `Hiyuki`...
> - Địa danh: `Ashinohara`, `Asphodel Barrens`, `Avinoleum`, `Beohr Waters`, `Bjartr Woods`, `Black Alley`, `Black Shores Archipelago`, `Capitoline Hill`, `Central Plains`, `Chamber of Discipline`, `Chronorift Metropolis`, `Corrosive Ruins`, `Desorock Highland`, `Dim Forest`, `Fabricatorium of the Deep`, `Fisalia`, `Gorges of Spirits`, `Septimont`...

---

## 4. Tên Bộ Echo (Echo Set Names)

* **Tệp tin áp dụng**: `lang_phantom.json`
* **Điều kiện lọc**:
  - Tên bảng: `table = "PhantomFetter"`
  - Định dạng: Dòng ngắn dạng tên của bộ Echo.
  - Loại trừ: Không phải là các dòng mô tả hiệu ứng kích hoạt bộ (ví dụ: các dòng chứa `ATK increases...`).

> [!TIP]
> **Ví dụ giữ nguyên:**
> - `Rolling Thunder`
> - `Rock Valley Resonance`
> - `Battle Song Rhythm`
> - `Mass Displacement`

---

## 5. Waveplate, tài nguyên và tiền tệ trong game

* **Tệp tin áp dụng**: các bảng vật phẩm, shop, pay shop, UI, reward và mọi dòng mô tả có nhắc tài nguyên/tiền tệ.
* **Điều kiện lọc**:
  - Dòng là tên tài nguyên/tiền tệ/vé quay/vật phẩm shop.
  - Hoặc cụm xuất hiện trong câu mô tả nhưng là tên tài nguyên chính thức của game.

> [!TIP]
> **Ví dụ giữ nguyên:**
> - `Waveplate`
> - `Waveplate Crystal`
> - `Astrite`
> - `Lunite`
> - `Lunite Subscription`
> - `Lustrous Tide`
> - `Radiant Tide`
> - `Forging Tide`
> - `Shell Credit`
> - `Oscillated Coral`
> - `Afterglow Coral`
> - `Crystal Solvent`
> - `Voucher`

> [!WARNING]
> **Không được dịch các cụm này thành:**
> - `Waveplate` -> `Đĩa Sóng`, `Sóng Đĩa`, `Tấm Sóng`
> - `Astrite` -> `Pha Lê`, `Tinh Thạch`
> - `Shell Credit` -> `Xu`, `Tiền`, `Tín Dụng Vỏ`
> - `Lustrous Tide` / `Radiant Tide` / `Forging Tide` -> `Vé quay`

---

## 6. Tên Nút Cộng Hưởng / Resonance Chain (RC Nodes)

* **Tệp tin áp dụng**: `lang_multi_text.json`
* **Điều kiện lọc**:
  - Tên bảng: `table = "MultiText"`
  - Khóa chính (`primary_key`) thỏa mãn đồng thời:
    - Bắt đầu bằng: `ResonantChain_`
    - Kết thúc bằng: `_NodeName`

> [!NOTE]
> Giữ nguyên toàn bộ tên của các nút Resonance Chain bằng tiếng Anh gốc.

---

## 7. Tên Kỹ Năng Nhân Vật (Character Skill Names)

* **Tệp tin áp dụng**:
  - `lang_multi_text.json`
  - `lang_skill.json`
  - `lang_skillTree.json`
* **Điều kiện lọc**:
  - Khóa chính (`primary_key`) chứa cụm từ `_SkillName`
  - Hoặc `primary_key` bắt đầu bằng `Skill_` and kết thúc bằng `_SkillName`
  - Hoặc `primary_key` bắt đầu bằng `RoleSkillTreeInfo_` and kết thúc bằng `_Title`
  - Hoặc tên bảng `table = "Skill"` trong tệp `lang_skill.json`
  - Hoặc tên bảng `table = "RoleSkillTreeInfo"` trong tệp `lang_skillTree.json`

> [!TIP]
> **Ví dụ giữ nguyên:**
> - `Slayer's Trigger`
> - `Sundering Strike`
> - `Colors Never Fade!`
> - `Try Focusing, Eh?`
> - `Commedia Improvviso!`

> [!WARNING]
> **Không áp dụng quy tắc này cho:**
> Các mô tả chi tiết của kỹ năng như khóa chính chứa `_SkillDescribe`, `_Description`, hoặc `_DescList` (các dòng này bắt buộc phải gửi đi dịch).
