import re, json

with open('js/lawyer-search.js','r',encoding='utf-8') as f: js = f.read()
with open('index.html','r',encoding='utf-8') as f: html = f.read()

js_ids = set(re.findall(r"getElementById\('([^']+)'\)", js))
html_ids = set(re.findall(r'id="([^"]+)"', html))

print('JS -> HTML ID check:')
missing = []
for i in sorted(js_ids):
    if i in html_ids:
        print(f'  OK: {i}')
    else:
        print(f'  MISSING in HTML: {i}')
        missing.append(i)

if missing:
    print(f'\nERROR: {len(missing)} IDs missing from HTML!')
else:
    print(f'\nALL {len(js_ids)} JS IDs found in HTML')

# Also check the other way
print(f'\nTotal HTML IDs: {len(html_ids)}')
