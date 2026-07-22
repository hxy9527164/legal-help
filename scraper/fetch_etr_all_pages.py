"""
全量抓取广东广信君达律师事务所所有律师 (9页, ~270人)
https://www.etrlawfirm.com/cn/zyls/list_68.aspx?page=1-9
"""
import json, re, sys, time, random
from pathlib import Path
import requests
from bs4 import BeautifulSoup

OUTPUT_FILE = Path(__file__).parent.parent / 'data' / 'lawyers.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://www.etrlawfirm.com/',
}
BASE = 'https://www.etrlawfirm.com'
FIRM_NAME = '广东广信君达律师事务所'

session = requests.Session()
session.headers.update(HEADERS)

def fetch_page(page_num, list_type='zyls'):
    """抓取单页律师列表"""
    if list_type == 'zyls':
        url = f'{BASE}/cn/zyls/list_68.aspx?page={page_num}'
    else:
        url = f'{BASE}/cn/hhr/list_11.aspx?lcid=2&page={page_num}'

    try:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            print(f'    HTTP {resp.status_code}')
            return []
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Find lawyer name links
        lawyers = []
        all_links = soup.find_all('a', href=True)
        seen_names = set()

        for a in all_links:
            name = a.get_text(strip=True)
            href = a['href']

            # Filter: Chinese name 2-4 chars, not navigation
            if not re.match(r'^[一-鿿·]{2,6}$', name):
                continue
            if name in seen_names:
                continue
            if any(kw in name for kw in ['首页','律师','团队','关于','联系','新闻','业务','服务','中文','英文']):
                continue

            seen_names.add(name)

            # Get parent container for more info
            parent = a.find_parent('li') or a.find_parent('div')
            parent_text = parent.get_text() if parent else ''

            # Extract position
            position = ''
            for pos_kw in ['高级合伙人','合伙人','副主任','主任','律师','实习律师','顾问','兼职律师']:
                if pos_kw in parent_text.replace(name, '', 1):
                    position = pos_kw
                    break

            # Extract specialty areas from parent text
            fields = ['民商事']
            field_section = re.search(r'(?:擅长|专业|领域|业务)[：:]\s*([^。\n]{3,150})', parent_text)
            if field_section:
                fields_text = field_section.group(1)
                fields = [f.strip() for f in re.split(r'[、，,/\s]+', fields_text) if len(f.strip()) > 1][:6]

            # Make full URL
            profile_url = href if href.startswith('http') else BASE + href

            lawyers.append({
                'name': name.replace('·', ''),
                'position': position,
                'firm': FIRM_NAME,
                'city': '广州',
                'province': '广东',
                'district': '天河区',
                'address': '天河区珠江东路6号周大福金融中心',
                'fields': fields,
                'experience': 0,
                'education': '暂无学历信息',
                'cases': '暂无案例信息',
                'contact': '暂无联系方式',
                'type': list_type,
                'profile_url': profile_url,
                'source': 'etrlawfirm.com',
            })

        return lawyers
    except Exception as e:
        print(f'    Error: {e}')
        return []


def main():
    print('=' * 60)
    print(f'  全量抓取: {FIRM_NAME}')
    print('  9页律师列表 + 合伙人列表')
    print('=' * 60)

    # Load existing
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    print(f'\n当前数据库: {len(existing)} 位律师')

    all_new_lawyers = []

    # 抓取执业律师 (9 pages)
    print('\n--- 执业律师 (1-9页) ---')
    for page in range(1, 10):
        print(f'  Page {page}/9...', end=' ', flush=True)
        lawyers = fetch_page(page, 'zyls')
        print(f'{len(lawyers)} lawyers')
        for l in lawyers:
            l['type'] = '执业律师'
            all_new_lawyers.append(l)
        time.sleep(random.uniform(0.5, 1.0))

    # 抓取合伙人 (2 pages based on earlier finding)
    print('\n--- 合伙人 ---')
    for page in range(1, 3):
        print(f'  Page {page}...', end=' ', flush=True)
        lawyers = fetch_page(page, 'hhr')
        print(f'{len(lawyers)} lawyers')
        for l in lawyers:
            l['type'] = '合伙人'
            all_new_lawyers.append(l)
        time.sleep(random.uniform(0.5, 1.0))

    print(f'\n总计抓取: {len(all_new_lawyers)} 位律师')

    # 去重 (by name within same firm)
    unique = {}
    for l in all_new_lawyers:
        key = (l['name'], l['firm'])
        if key not in unique:
            unique[key] = l

    all_new_lawyers = list(unique.values())
    print(f'去重后: {len(all_new_lawyers)} 位')

    # 统计职位分布
    from collections import Counter
    pos_dist = Counter(l.get('position', '') for l in all_new_lawyers)
    print('\n职位分布:')
    for pos, count in pos_dist.most_common():
        print(f'  {pos or "未标注"}: {count}人')

    # 合并
    existing_keys = {(l['name'], l.get('firm', '')) for l in existing}
    added = 0
    for l in all_new_lawyers:
        key = (l['name'], l.get('firm', ''))
        if key not in existing_keys and l['name']:
            existing.append(l)
            existing_keys.add(key)
            added += 1

    # 重新编号
    for i, l in enumerate(existing):
        l['id'] = i + 1

    # 删除旧的合成数据中与广信君达相关且无profile_url的重复项
    # (keep the real scraped data, remove older synthetic duplicates)
    cleaned = []
    seen_etr_names = set()
    # First pass: collect all real profile URLs
    for l in existing:
        if l.get('firm') == FIRM_NAME and l.get('profile_url', '').startswith('http'):
            seen_etr_names.add(l['name'])
        cleaned.append(l)

    # Second pass: remove synthetic duplicates
    final = []
    removed = 0
    for l in cleaned:
        if (l.get('firm') == FIRM_NAME and
            not l.get('profile_url', '').startswith('http') and
            l['name'] in seen_etr_names):
            removed += 1
            continue
        final.append(l)

    for i, l in enumerate(final):
        l['id'] = i + 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    tianhe = len([l for l in final if l.get('district') == '天河区'])
    firm_count = len([l for l in final if l.get('firm') == FIRM_NAME])

    print(f'\n{"=" * 60}')
    print(f'  广信君达新增: {added} 位')
    print(f'  清理旧合成重复: {removed} 位')
    print(f'  广信君达总计: {firm_count} 位')
    print(f'  天河区总计: {tianhe} 位')
    print(f'  数据库总计: {len(final)} 位')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
