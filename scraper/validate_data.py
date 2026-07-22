import json

# Validate lawyers.json
with open('data/lawyers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Lawyers: {len(data)}')
print(f'File size: {len(json.dumps(data, ensure_ascii=False))} chars')

issues = []
for i, l in enumerate(data):
    if not l.get('name'):
        issues.append(f'[{i}] Missing name')
    if not l.get('firm'):
        issues.append(f'[{i}] Missing firm')
    if not isinstance(l.get('fields'), list):
        issues.append(f'[{i}] fields not list')
    if not isinstance(l.get('id'), int):
        issues.append(f'[{i}] id not int')
    for k, v in l.items():
        if isinstance(v, str) and len(v) > 2000:
            issues.append(f'[{i}] Field {k} too long: {len(v)} chars')
        if isinstance(v, str):
            for ch in v:
                if ord(ch) < 32 and ord(ch) not in (9, 10, 13):
                    issues.append(f'[{i}] Field {k} has ctrl char ord={ord(ch)}')
                    break

if issues:
    print(f'\nIssues ({len(issues)}):')
    for iss in issues[:20]:
        print(f'  {iss}')
else:
    print('No data issues found')

# Validate templates
with open('data/templates.json', 'r', encoding='utf-8') as f:
    tpl = json.load(f)
print(f'Templates: {len(tpl)}, valid')

# Validate knowledge base
with open('data/knowledge-base.json', 'r', encoding='utf-8') as f:
    kb = json.load(f)
print(f'Knowledge base categories: {len(kb["categories"])}, valid')

# Check if lawyer JSON can be parsed by JavaScript (look for common JS JSON issues)
raw = json.dumps(data, ensure_ascii=False, indent=2)
# Check for BOM or weird encoding
with open('data/lawyers.json', 'rb') as f:
    raw_bytes = f.read()
if raw_bytes[:3] == b'\xef\xbb\xbf':
    print('WARNING: File has UTF-8 BOM! This can break JS parsing')
print(f'First 100 bytes: {raw_bytes[:100]}')

# Check total file size
import os
size_kb = os.path.getsize('data/lawyers.json') / 1024
print(f'lawyers.json file size: {size_kb:.1f} KB')
