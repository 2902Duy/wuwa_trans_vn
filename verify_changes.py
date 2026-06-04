import json
import os

ROOT = r"C:\Users\tduy2\Documents\antigravity\silly-darwin\mistral_translate_work\split_by_prompt\json"

def main():
    with open('proposed_corrections.json', 'r', encoding='utf-8') as f:
        corrections = json.load(f)

    overrides = {
        'LORE_0001761': 'Tôi chỉ có thể mang sức mạnh của ngài trong khoảnh khắc ngắn ngủi... Nhưng như thế là đủ để bảo đảm một tương lai tốt đẹp hơn cho Jinzhou, bất chấp mọi dự đoán của ngài. Và tôi có thể bảo vệ ngài an toàn.',
        'LORE_0004408': 'Hello, {Male=ngài;Female=bà}! {Male=Ngài;Female=Bà} có thể dành cho tôi vài phút được không? Xin lỗi đã làm phiền, nhưng {Male=ngài;Female=bà} có từng thấy vật gì giống chiếc chuông bao quanh bởi nốt nhạc trên núi không?',
        'LORE_0002256': '"Niềm tin chân chính khởi nguồn từ trái tim, và lời dẫn dắt của Sentinel vang lên qua giọng nói của ta. Từ đáy lòng, ta cảm ơn sự giúp đỡ của {Male=anh;Female=chị}, {Male=anh;Female=chị} {PlayerName}."'
    }

    errors = []
    for c in corrections:
        split_id = c['split_id']
        rel_path = c['file']
        full_path = os.path.join(ROOT, rel_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f, strict=False)
            
        item = next((x for x in data if x.get('split_id') == split_id), None)
        if not item:
            errors.append(f"{split_id}: Not found in JSON file")
            continue
            
        actual = item.get('new_translation_vi', '')
        expected = overrides.get(split_id, c['new_translation_vi'])
        
        if actual != expected:
            errors.append(f"{split_id}: Mismatch!\n  Expected: {repr(expected)}\n  Actual:   {repr(actual)}")
            
        if 'anh/ch' in actual.lower() or 'anh/chi' in actual.lower() or 'anh / ch' in actual.lower() or 'anh/ chi' in actual.lower():
            errors.append(f"{split_id}: Still contains static address term! Value: {repr(actual)}")

    print(f"Verification finished. Total errors: {len(errors)}")
    for e in errors[:50]:
        print(e)

if __name__ == '__main__':
    main()
