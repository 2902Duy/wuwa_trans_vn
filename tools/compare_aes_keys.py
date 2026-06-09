import json, re

# Doc key hien tai trong Fmodel config
with open(r'C:\Users\tduy2\AppData\Roaming\Fmodel\AppSettings.json', encoding='utf-8') as f:
    cfg = json.load(f)

game_dir = r'E:\Wuthering Waves\Wuthering Waves Game\Client\Content\Paks'
fmodel_keys = cfg['PerDirectory'][game_dir]['AesKeys']['dynamicKeys']
fmodel_guids = set(k['guid'] for k in fmodel_keys)
fmodel_map = {k['guid']: k['key'] for k in fmodel_keys}

# Doc key tu endpoint (da cache)
with open(r'C:\Users\tduy2\.gemini\antigravity\brain\bb8a7efd-8a70-4c28-b8cb-6ba5d47d22f0\.system_generated\steps\67\content.md', encoding='utf-8') as f:
    raw = f.read()

# Parse JSON
start = raw.index('{')
endpoint_data = json.loads(raw[start:])
endpoint_keys = endpoint_data['dynamicKeys']
endpoint_guids = set(k['guid'] for k in endpoint_keys)
endpoint_map = {k['guid']: k['key'] for k in endpoint_keys}

new_guids = endpoint_guids - fmodel_guids
missing_guids = fmodel_guids - endpoint_guids

print(f'Fmodel hien tai: {len(fmodel_guids)} dynamic keys')
print(f'Endpoint hien tai: {len(endpoint_guids)} dynamic keys')
print()

if new_guids:
    print(f'=== KEY MOI tren endpoint ma Fmodel CHUA CO ({len(new_guids)} keys) ===')
    for g in sorted(new_guids):
        print(f'  GUID: {g}')
        print(f'  Key:  {endpoint_map[g]}')
        print()
else:
    print('Khong co key moi - Fmodel da co tat ca key tu endpoint')
    print()
    print('>>> Van de la Fmodel khong reload vi endpoint khong co key moi cho PAK 08/06!')
    print('>>> PAK moi co the dung key GUID khac chua duoc public len endpoint nay.')
