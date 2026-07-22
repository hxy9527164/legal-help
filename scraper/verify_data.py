import json
from collections import Counter

data = json.load(open('data/lawyers.json', 'r', encoding='utf-8'))
tianhe = [l for l in data if l.get('district') == '天河区']

print(f'Total lawyers: {len(data)}')
print(f'Tianhe lawyers: {len(tianhe)}')

firms = Counter(l['firm'] for l in tianhe)
print(f'\nLaw firms: {len(firms)}')
print('Top 10:')
for firm, count in firms.most_common(10):
    print(f'  {firm}: {count}')

all_fields = []
for l in tianhe:
    all_fields.extend(l.get('fields', []))
fc = Counter(all_fields)
print('\nTop 10 fields:')
for f, c in fc.most_common(10):
    print(f'  {f}: {c}')

print('\nSample (first 5):')
for l in tianhe[:5]:
    fields_str = ', '.join(l.get('fields', [])[:3])
    print(f'  {l["name"]} | {l["firm"][:30]} | {fields_str} | {l["experience"]}yr')
