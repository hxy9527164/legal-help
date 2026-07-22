import json
from collections import Counter

with open('data/lawyers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

GZ_DISTRICTS = ['天河区','越秀区','海珠区','荔湾区','白云区','黄埔区','番禺区','花都区','南沙区','增城区','从化区']

firm_to_district = {
    '广东广信君达律师事务所': '天河区','广东法制盛邦律师事务所': '天河区',
    '广东金桥百信律师事务所': '天河区','广东国智律师事务所': '天河区',
    '广东君信经纶君厚律师事务所': '天河区','广东环球经纬律师事务所': '天河区',
    '广东南国德赛律师事务所': '天河区','广东国信信扬律师事务所': '天河区',
    '广东卓信律师事务所': '天河区','广东正大方略律师事务所': '天河区',
    '广东南方福瑞德律师事务所': '天河区','广东连越律师事务所': '天河区',
    '广东合盛律师事务所': '天河区','广东启源律师事务所': '天河区',
    '广东红棉律师事务所': '天河区','广东天穗律师事务所': '天河区',
    '广东盈隆律师事务所': '天河区','广东国鼎律师事务所': '越秀区',
    '广东岭南律师事务所': '越秀区','广东君厚律师事务所': '越秀区',
    '广东海际明律师事务所': '海珠区','广东法全律师事务所': '海珠区',
    '广东金轮律师事务所': '荔湾区',
    '广东维永律师事务所': '白云区','广东广开律师事务所': '黄埔区',
    '广东厚载律师事务所': '黄埔区','广东仲衡律师事务所': '番禺区',
    '广东金本色律师事务所': '番禺区','广东合誉律师事务所': '花都区',
    '广东港宏律师事务所': '南沙区','广东丰信律师事务所': '南沙区',
    '广东民诚众信律师事务所': '增城区','广东政衡律师事务所': '从化区',
}

fixed = 0
for l in data:
    d = l.get('district', '')
    if d not in GZ_DISTRICTS:
        firm = l.get('firm', '')
        if firm in firm_to_district:
            l['district'] = firm_to_district[firm]
            fixed += 1
        elif l.get('address'):
            for dd in GZ_DISTRICTS:
                if dd in l.get('address', ''):
                    l['district'] = dd
                    fixed += 1
                    break

# Re-ID
for i, l in enumerate(data):
    l['id'] = i + 1

with open('data/lawyers.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

with open('data/lawyers-data.js', 'w', encoding='utf-8') as f:
    f.write('window.__lawyersData = ' + json.dumps(data, ensure_ascii=False, indent=2) + ';\n')

dc = Counter(l.get('district', '未知') for l in data)
print(f'Fixed: {fixed} | Total: {len(data)}')
for d in GZ_DISTRICTS:
    print(f'  {d}: {dc.get(d, 0)}')
print(f'  Other: {sum(c for d,c in dc.items() if d not in GZ_DISTRICTS)}')
