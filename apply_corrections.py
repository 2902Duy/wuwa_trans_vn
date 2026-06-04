import json
import os

ROOT = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json"

def apply_overrides(split_id, en, vi):
    if split_id == "LORE_0001761":
        return "Tôi chỉ có thể mang sức mạnh của ngài trong khoảnh khắc ngắn ngủi... Nhưng như thế là đủ để bảo đảm một tương lai tốt đẹp hơn cho Jinzhou, bất chấp mọi dự đoán của ngài. Và tôi có thể bảo vệ ngài an toàn."
    elif split_id == "LORE_0004408":
        return "Hello, {Male=ngài;Female=bà}! {Male=Ngài;Female=Bà} có thể dành cho tôi vài phút được không? Xin lỗi đã làm phiền, nhưng {Male=ngài;Female=bà} có từng thấy vật gì giống chiếc chuông bao quanh bởi nốt nhạc trên núi không?"
    elif split_id == "LORE_0002256":
        return "\"Niềm tin chân chính khởi nguồn từ trái tim, và lời dẫn dắt của Sentinel vang lên qua giọng nói của ta. Từ đáy lòng, ta cảm ơn sự giúp đỡ của {Male=anh;Female=chị}, {Male=anh;Female=chị} {PlayerName}.\""
    return vi

def main():
    with open('proposed_corrections.json', 'r', encoding='utf-8') as f:
        corrections = json.load(f)

    # Group corrections by file path
    by_file = {}
    for c in corrections:
        fpath = c['file']
        if fpath not in by_file:
            by_file[fpath] = []
        by_file[fpath].append(c)

    updated_count = 0
    for rel_path, items in by_file.items():
        full_path = os.path.join(ROOT, rel_path)
        if not os.path.exists(full_path):
            print(f"Warning: File {full_path} not found.")
            continue
            
        print(f"Loading {rel_path}...")
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f, strict=False)

        # Build lookup dict for the target file list items
        lookup = {item['split_id']: item for item in data if 'split_id' in item}

        file_changed = False
        for c in items:
            split_id = c['split_id']
            if split_id in lookup:
                # Apply custom overrides if applicable
                new_vi = apply_overrides(split_id, c['source_en'], c['new_translation_vi'])
                
                # Check if it actually changed
                old_vi = lookup[split_id].get('new_translation_vi', '')
                if old_vi != new_vi:
                    lookup[split_id]['new_translation_vi'] = new_vi
                    file_changed = True
                    updated_count += 1

        if file_changed:
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Successfully updated {updated_count} translation items in JSON files.")

if __name__ == '__main__':
    main()
