import json
import re

def clean_text(en, vi):
    # Determine the target term based on context
    is_senior = "senior" in en.lower()
    is_narrator = "instincts" in en.lower() or "hesitate" in en.lower()
    is_merchant = "customer" in en.lower() or "quý khách" in vi.lower() or "buy" in en.lower() or "selling" in en.lower() or "shop" in en.lower() or "menu" in en.lower()
    
    has_placeholder = False
    for p in ["{Male=Mr.;Female=Ms.}", "{Male=Mr.;Female=Miss}", "{Male=mister;Female=miss}", "{Male=Sir;Female=Miss}", "{Male=sir;Female=lady}", "{Male=Mister;Female=Miss}", "{Male=Big Brother;Female=Big Sister}", "{Male=brother;Female=sister}", "{Male=him;Female=her}", "{Male=good sir;Female=good lady}"]:
        if p.lower() in en.lower():
            has_placeholder = True
            break

    # We want to match: (anh|Anh)\s*/\s*(chị|Chị|chi|chỉ|cậu|bạn) or (anh/chị/bạn) etc.
    # Regex pattern to match any variation of "anh/chị/bạn"
    pattern_triple = re.compile(r'\b(anh/chị/bạn|Anh/chị/bạn)\b', re.IGNORECASE)
    # Regex pattern to match any variation of "anh/chị", "anh/chi", "anh/chỉ", "anh / chị", "anh/ chi"
    pattern_double = re.compile(r'\b(anh\s*/\s*(chị|chi|chỉ))\b', re.IGNORECASE)

    # 1. First replace triples "anh/chị/bạn"
    def replace_triple(match):
        word = match.group(1)
        if is_narrator:
            return "Bạn" if word[0].isupper() else "bạn"
        else:
            return "Cậu" if word[0].isupper() else "cậu"
            
    vi = pattern_triple.sub(replace_triple, vi)

    # 2. Replace doubles "anh/chị"
    def replace_double(match):
        word = match.group(1)
        is_upper = word[0].isupper()
        
        if is_senior:
            return "Tiền bối" if is_upper else "tiền bối"
        elif has_placeholder:
            return "{Male=Anh;Female=Chị}" if is_upper else "{Male=anh;Female=chị}"
        elif is_merchant:
            return "Quý khách" if is_upper else "quý khách"
        else:
            # General peer
            return "Cậu" if is_upper else "cậu"

    vi = pattern_double.sub(replace_double, vi)

    # Clean up double spacing or consecutive duplicate punctuation if any
    vi = vi.replace('quý khách trông thật quyến rũ, thưa quý khách', 'quý khách trông thật quyến rũ')
    
    return vi

def main():
    with open('found_matches.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    proposed = []
    for item in data:
        en = item['item']['source_en']
        vi = item['item']['new_translation_vi']
        new_vi = clean_text(en, vi)
        proposed.append({
            'split_id': item['item']['split_id'],
            'file': item['file'],
            'index': item['index'],
            'source_en': en,
            'old_translation_vi': vi,
            'new_translation_vi': new_vi
        })

    with open('proposed_corrections.json', 'w', encoding='utf-8') as out:
        json.dump(proposed, out, ensure_ascii=False, indent=2)
    print(f'Wrote {len(proposed)} proposed changes to proposed_corrections.json')

if __name__ == '__main__':
    main()
