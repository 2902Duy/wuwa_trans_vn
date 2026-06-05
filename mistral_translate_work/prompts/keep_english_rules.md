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
> - `Abyss Surges`
> - `Aether Strike`
> - `Ambitious determination to the sky`
> - `Amity Accord`
> - `Assemble`
> - `Augment`
> - `Aureate Zenith`
> - `Autumntrace`
> - `Beguiling Melody`
> - `Blazing Brilliance`
> - `Blazing Justice`
> - `Bloodpact's Pledge`
> - `Bonds of Comrade`
> - `Boson Astrolabe`
> - `Break the chill wind`
> - `Break the skies`
> - `Broadblade improved: regularization II`
> - `Broadblade of Voyager`
> - `Broadblade of night`
> - `Broadblade prototype: REGULARIZATION`
> - `Broadblade#41`
> - `Cadenza`
> - `Carve the stone`
> - `Celestial Spiral`
> - `Comet Flare`
> - `Commando of Conviction`
> - `Conquer`
> - `Cosmic Ripples`
> - `Dance`
> - `Dauntless Evernight`
> - `Dawn from the east`
> - `Daybreaker's Spine`
> - `Defier's Thorn`
> - `Discipline`
> - `Discord`
> - `Edgy across dusk`
> - `Emerald Sentence`
> - `Emerald of Genesis`
> - `Endless Collapse`
> - `Endless adoring`
> - `Ever-lightened lone lamp`
> - `Everbright Polestar`
> - `Feather Edge`
> - `Focus`
> - `Forceful hymn for the brave`
> - `Forged Dwarf Star`
> - `Frostburn`
> - `Fusion Accretion`
> - `Gates on heavens`
> - `Gauntlet of night`
> - `Gauntlets#21D`
> - `Ground Rainbow Hanging`
> - `Guardian Broadblade`
> - `Guardian Gauntlets`
> - `Guardian Pistols`
> - `Guardian Rectifier`
> - `Guardian Sword`
> - `Gun of night`
> - `Heart of purity`
> - `Helios Cleaver`
> - `Hollow Mirage`
> - `Hum`
> - `Jinzhou Keeper`
> - `Judgement`
> - `Kumokiri`
> - `Laser Shearer`
> - `Lead horse to water`
> - `Lethean Elegy`
> - `Loyalty in bone`
> - `Lumingloss`
> - `Luminous Hymn`
> - `Lunar Cutter`
> - `Lustrous Razor`
> - `Marcato`
> - `Matrix of night`
> - `Moongazer's Sigil`
> - `No return`
> - `Novaburst`
> - `Oblivion`
> - `Ocean's Gift`
> - `Overture`
> - `Phasic Homogenizer`
> - `Pistols#26`
> - `Primordial Broadblade`
> - `Primordial Gauntlet`
> - `Primordial Rectifier`
> - `Primordial Smallblade`
> - `Primordial gun`
> - `Pulsation Bracer`
> - `Radiance Cleaver`
> - `Radiant Dawn`
> - `Ready for battle`
> - `Rectifier improved: SEQUENCE II`
> - `Rectifier prototype: SEQUENCE`
> - `Rectifier#25`
> - `Red Spring`
> - `Relativistic Jet`
> - `Revelation`
> - `Rime-Draped Sprouts`
> - `Rocks into pieces`
> - `Scale: Introduction`
> - `Scale: chop of sound`
> - `Scale: hetero`
> - `Scale: through the air`
> - `Scale: wave`
> - `Smallblade improved: Spear II`
> - `Smallblade of night`
> - `Smallblade prototype: SPEAR`
> - `Solar Flame`
> - `Solsworn Ciphers`
> - `Somnoire Anchor`
> - `Spectrum Blaster`
> - `Star across the sun`
> - `Starfield Calibrator`
> - `Static Mist`
> - `Stellar Symphony`
> - `Stonard`
> - `Stops at nothing`
> - `Stringmaster`
> - `Sword#18`
> - `T4-5Jinzhou+ Series Greatsword`
> - `Take their town`
> - `Temper`
> - `Test1-Short Sword`
> - `The Last Dance`
> - `Thunderbolt`
> - `Thunderflare Dominion`
> - `Tiancheng Watch`
> - `Tragicomedy`
> - `Training Broadblade`
> - `Training Gauntlet`
> - `Training Gauntlets`
> - `Training Pistols`
> - `Training Rectifier`
> - `Training Smallblade`
> - `Training Sword`
> - `Training gun`
> - `Triumph`
> - `Tyro Broadblade`
> - `Tyro Gauntlets`
> - `Tyro Pistols`
> - `Tyro Rectifier`
> - `Tyro Sword`
> - `Ultrasonic Blade`
> - `Ultrasonic Hellen`
> - `Ultrasonic Judgement`
> - `Ultrasonic Matrix`
> - `Ultrasonic Razor`
> - `Ultrasonic Rockbreaker`
> - `Ultrasonic Roscoe`
> - `Ultrasonic rockbreaker`
> - `Undying Flame`
> - `Unflickering Valor`
> - `Unmatched broken blade`
> - `Variation`
> - `Verdant Summit`
> - `Verity's Handle`
> - `Waning Redshift`
> - `Wildfire Mark`
> - `Will to battle`
> - `Wipe their men`
> - `Woodland Aria`
> - `Work hard`
> - `chords`
> - `set sail`

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
> - `Abyssal Gladius`
> - `Abyssal Gunmaster`
> - `Abyssal Mercator`
> - `Abyssal Patricius`
> - `Abysscrest Gladiator`
> - `Aero Drake`
> - `Aero Predator`
> - `Aero Prism`
> - `Autopuppet Scout`
> - `Baby Roseshroom`
> - `Baby Viridblaze Saurian`
> - `Bell-Borne Geochelone`
> - `Calcified Junrock`
> - `Capitaneus`
> - `Carapace`
> - `Chaserazor`
> - `Chasm Guardian`
> - `Chasm Rider`
> - `Chest Mimic`
> - `Chirpuff`
> - `Chop Chop`
> - `Clang Bang`
> - `Corrosaurus`
> - `Crownless`
> - `Cruisewing`
> - `Cuddle Wuddle`
> - `Cyan-Feathered Heron`
> - `Cyrscorpion`
> - `Devotee's Flesh`
> - `Diamondclaw`
> - `Diggy Duggy`
> - `Diurnus Knight`
> - `Dreamless`
> - `Dwarf Cassowary`
> - `Electro Drake`
> - `Electro Predator`
> - `Excarat`
> - `Exile Commoner`
> - `Exile Craftsman`
> - `Exile Technician`
> - `Fae Ignis`
> - `Feilian Beringal`
> - `Fenrico`
> - `Fission Junrock`
> - `Flamecrest Gladiator`
> - `Flautist`
> - `Fleurdelys`
> - `Flora Drone`
> - `Flora Reindeer`
> - `Flute Instrumentalist`
> - `Forsaken Abundance`
> - `Fractsidus Cannoneer`
> - `Fractsidus Executioner`
> - `Fractsidus Gunmaster`
> - `Fractsidus Mawdoll`
> - `Fractsidus Milliner`
> - `Fractsidus Ripper`
> - `Fractsidus Thruster`
> - `Frostbite Coleoid`
> - `Frostbite Tertoise`
> - `Frostcrest Gladiator`
> - `Frostscourge Stalker`
> - `Fusion Drake`
> - `Fusion Dreadmane`
> - `Fusion Dreadmane Minor`
> - `Fusion Prism`
> - `Fusion Warrior`
> - `Galecrest Gladiator`
> - `Galescourge Stalker`
> - `Geohide Saurian Major`
> - `Geohide Saurian Minor`
> - `Geospider S4`
> - `Glacio Drake`
> - `Glacio Dreadmane`
> - `Glacio Predator`
> - `Glacio Prism`
> - `Gleamtender`
> - `Glommoth`
> - `Golden Junrock`
> - `Gulpuff`
> - `Havoc Drake`
> - `Havoc Dreadmane`
> - `Havoc Prism`
> - `Havoc Warrior`
> - `Hecate`
> - `Hoartoise`
> - `Hocus Pocus`
> - `Hoochief`
> - `Hoochief Cyclone`
> - `Hoochief Menace`
> - `Hooscamp`
> - `Hooscamp Clapperclaw`
> - `Hooscamp Flinger`
> - `Hurriclaw`
> - `Hyvatia`
> - `Iceglint Dancer`
> - `Impermanence Heron`
> - `Impulse Predator`
> - `Inferno Rider`
> - `Ironhoof`
> - `Jué`
> - `Kelpie`
> - `Kerasaur`
> - `Kronablight`
> - `Kronaclaw`
> - `La Guardia`
> - `Lampylumen Myriad`
> - `Lava Larva`
> - `Lightcrest Gladiator`
> - `Lightcrusher`
> - `Lorelei`
> - `Lottie Lost`
> - `Lumiscale Construct`
> - `Mech Abomination`
> - `Midnight Ranger`
> - `Mining Drone`
> - `Mining Reindeer`
> - `Mourning Aix`
> - `Nameless Explorer`
> - `Nimbus Wraith`
> - `Nocturnus Knight`
> - `Outcast Executioner`
> - `Pilgrim's Shell`
> - `Pneuma Predator`
> - `Questless Knight`
> - `Reactor Husk`
> - `Rocksteady Guardian`
> - `Roseshroom`
> - `Roseshroom (Immature)`
> - `Roseshroom (Mature)`
> - `Rupture Dreadmane Major`
> - `Rupture Prism`
> - `Rupture Warrior`
> - `Sabercat Prowler`
> - `Sabercat Reaver`
> - `Sabyr Boar`
> - `Sacerdos`
> - `Sagittario`
> - `Scar`
> - `Seatrail Narwhal`
> - `Sentinel`
> - `Sentinel Jué`
> - `Sentry Construct`
> - `Shadow Stepper`
> - `Sigillum`
> - `Snip Snap`
> - `Spacetrek Explorer`
> - `Spearback`
> - `Spearback Ursa`
> - `Spectra Prism`
> - `Spectro Drake`
> - `Spectro Prism`
> - `Stonewall Bracer`
> - `Tambourine Instrumentalist`
> - `Tambourinist`
> - `Tempest Mephis`
> - `The False Sovereign`
> - `Thunder Squama`
> - `Thundercrest Gladiator`
> - `Thundering Mephis`
> - `Thundstaff Outcast`
> - `Tic Tac`
> - `Tick Tack`
> - `Traffic Illuminator`
> - `Tremor Warrior`
> - `Vanguard Junrock`
> - `Violet-Feathered Heron`
> - `Viridblaze Saurian`
> - `Vitreum Dancer`
> - `Voidwing Moth`
> - `Voidworm`
> - `Voltscourge Stalker`
> - `Whiff Whaff`
> - `Whiff Whoosh`
> - `Windlash Coleoid`
> - `Zig Zag`
> - `Zip Zap`

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
> > - Nhân vật: `Aalto`, `Abby`, `Aemeath`, `An'ke`, `Augusta`, `Bailian`, `Baizhi`, `Brant`, `Buling`, `Calcharo`, `Camellya`, `Cantarella`, `Carlotta`, `Cartethyia`, `Changli`, `Chisa`, `Chixia`, `Ciaccona`, `Danjin`, `Denia`, `Encore`, `Galbrena`, `Geshu Lin`, `Hiyuki`, `Iuno`, `Jianxin`, `Jinhsi`, `Jiyan`, `Lingyang`, `Lucilla`, `Lumi`, `Lupa`, `Luuk Herssen`, `Lynae`, `Mornye`, `Mortefi`, `Phoebe`, `Phrolova`, `Qiuyuan`, `Roccia`, `Rover: Aero`, `Rover: Havoc`, `Rover: Spectro`, `San'hua`, `Sanhua`, `Shorekeeper`, `Sigrika`, `Taoqi`, `The Shorekeeper`, `Verina`, `Xiangli Yao`, `Yangyang`, `Yinlin`, `Youhu`, `Yuanwu`, `Zani`, `Zhezhi`...
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
