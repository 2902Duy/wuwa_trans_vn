import json
import re

def clean_translation(en, vi):
    # Rule 1: Senior
    if "senior" in en.lower():
        vi = re.sub(r'anh/chị\b', 'tiền bối', vi, flags=re.IGNORECASE)
        vi = re.sub(r'anh/chị', 'tiền bối', vi, flags=re.IGNORECASE)
        vi = re.sub(r'Anh/Chị\b', 'Tiền bối', vi)
        vi = re.sub(r'anh\s*/\s*chị', 'tiền bối', vi, flags=re.IGNORECASE)
        vi = vi.replace('anh/chị', 'cậu')
        vi = vi.replace('Anh/Chị', 'Cậu')
        return vi

    # Rule 2: Dynamic placeholders
    has_placeholder = False
    for placeholder in ["{Male=Mr.;Female=Ms.}", "{Male=Mr.;Female=Miss}", "{Male=mister;Female=miss}", "{Male=Sir;Female=Miss}", "{Male=sir;Female=lady}", "{Male=Mister;Female=Miss}", "{Male=Big Brother;Female=Big Sister}", "{Male=brother;Female=sister}", "{Male=him;Female=her}", "{Male=good sir;Female=good lady}"]:
        if placeholder.lower() in en.lower():
            has_placeholder = True
            break
    
    if has_placeholder:
        vi = vi.replace('anh/chị', '{Male=anh;Female=chị}')
        vi = vi.replace('Anh/Chị', '{Male=Anh;Female=Chị}')
        vi = vi.replace('anh / chị', '{Male=anh;Female=chị}')
        vi = vi.replace('Anh / Chị', '{Male=Anh;Female=Chị}')
        vi = vi.replace('anh/ chi', '{Male=anh;Female=chị}')
        vi = vi.replace('anh/chi', '{Male=anh;Female=chị}')
        return vi

    # Rule 3: System Text or Narrator Text
    is_narrator = False
    if "instincts" in en.lower() or "hesitate" in en.lower():
        is_narrator = True
    if is_narrator:
        vi = vi.replace('anh/chị/bạn', 'bạn')
        vi = vi.replace('anh/chị', 'bạn')
        vi = vi.replace('Anh/Chị', 'Bạn')
        return vi

    # Rule 4: Shopkeeper/Merchant dialogue
    if "customer" in en.lower() or "quý khách" in vi.lower() or "buy" in en.lower() or "selling" in en.lower():
        vi = vi.replace('anh/chị', 'quý khách')
        vi = vi.replace('Anh/Chị', 'Quý khách')
        vi = vi.replace('quý khách trông thật quyến rũ, thưa quý khách', 'quý khách trông thật quyến rũ')
        return vi

    # Rule 5: General substitution of static "anh/chị" with "cậu"
    vi = vi.replace('anh/chị/bạn', 'cậu')
    vi = vi.replace('anh/chị', 'cậu')
    vi = vi.replace('Anh/Chị', 'Cậu')
    vi = vi.replace('anh / chị', 'cậu')
    vi = vi.replace('Anh / Chị', 'Cậu')
    vi = vi.replace('anh/ chi', 'cậu')
    vi = vi.replace('anh/chi', 'cậu')
    vi = vi.replace('Anh/chi', 'Cậu')
    
    return vi

def main():
    with open('found_matches.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    proposed = []
    for item in data:
        en = item['item']['source_en']
        vi = item['item']['new_translation_vi']
        new_vi = clean_translation(en, vi)
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
