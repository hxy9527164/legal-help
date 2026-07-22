"""
从 etrlawfirm.com (广东广信君达律师事务所) 抓取约1000位律师信息
该律所是广州最大的律所之一，位于天河区珠江新城
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
session = requests.Session()
session.headers.update(HEADERS)

# 目标URLs
# 执业律师列表 (1000+ lawyers)
LAWYER_LIST_URL = BASE + '/cn/zyls/list_68.aspx'
# 合伙人列表
PARTNER_LIST_URL = BASE + '/cn/hhr/list_11.aspx?lcid=2'

FOUND_LAWYERS = []


def fetch_page(url):
    """获取页面"""
    try:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            print(f'  HTTP {resp.status_code}')
            return None
        resp.encoding = 'utf-8'
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f'  Error: {e}')
        return None


def scrape_lawyer_list(list_url, lawyer_type='执业律师'):
    """抓取律师列表页（支持分页）"""
    lawyers = []
    page = 1

    while True:
        page_url = list_url if page == 1 else list_url.replace('.aspx', f'_{page}.aspx')
        if page > 1 and page_url == list_url:
            # Try query param pagination
            page_url = list_url + ('&' if '?' in list_url else '?') + f'page={page}'

        print(f'  Page {page}...', end=' ')
        soup = fetch_page(page_url)
        if not soup:
            break

        # Find lawyer entries
        items = soup.select('.team-list li, .lawyer-list li, .team-item, .lawyer-item, .member-list li, .list-item')
        if not items:
            items = soup.select('[class*=team] li, [class*=lawyer] li, [class*=member] li, [class*=people] li')

        if not items:
            # Try to find any name-like links
            all_links = soup.find_all('a', href=True)
            items = [a for a in all_links if a.get_text(strip=True) and len(a.get_text(strip=True)) in (2, 3, 4)
                     and re.match(r'^[一-鿿]{2,4}$', a.get_text(strip=True))
                     and a.find_parent('li')]

        print(f'{len(items)} items')

        if len(items) == 0:
            break

        for item in items:
            # Extract name
            if item.name == 'a':
                name = item.get_text(strip=True)
                link = item.get('href', '')
            else:
                name_el = item.find('a')
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                link = name_el.get('href', '')

            # Clean name
            name = re.sub(r'(律师|合伙人|主任|博士|教授|先生|女士)$', '', name).strip()
            if not name or len(name) < 2 or len(name) > 4:
                continue
            if not re.match(r'^[一-鿿]{2,4}$', name):
                continue

            # Make full URL
            if link and not link.startswith('http'):
                link = BASE.rstrip('/') + '/' + link.lstrip('/')

            # Extract other info from parent element
            parent = item if item.name != 'a' else item.find_parent('li') or item.find_parent('div')
            text = parent.get_text() if parent else ''

            # Find title/position
            position = ''
            pos_match = re.search(r'(合伙人|高级合伙人|主任|副主任|律师|实习律师|顾问)', text.replace(name, '', 1))
            if pos_match:
                position = pos_match.group(1)

            # Find specialty
            fields = ['民商事']
            field_match = re.search(r'(擅长|专业|领域|业务)[：:]\s*([^。\n]{5,100})', text)
            if field_match:
                fields = [f.strip() for f in re.split(r'[、，,/\s]+', field_match.group(2)) if len(f.strip()) > 1][:6]

            lawyers.append({
                'name': name,
                'position': position,
                'firm': '广东广信君达律师事务所',
                'city': '广州',
                'province': '广东',
                'district': '天河区',
                'fields': fields,
                'experience': 0,
                'education': '暂无学历信息',
                'cases': '暂无案例信息',
                'contact': '暂无联系方式',
                'type': lawyer_type,
                'profile_url': link if link else '',
                'source': 'etrlawfirm.com',
            })

        page += 1
        time.sleep(random.uniform(0.8, 1.5))
        if page > 100:  # Safety limit
            break

    return lawyers


def main():
    print('=' * 60)
    print('  抓取广东广信君达律师事务所律师数据')
    print('  (广州天河区最大律所之一，1000+律师)')
    print('=' * 60)

    # Load existing
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    print(f'\n现有律师: {len(existing)}')

    # Scrape partners
    print('\n--- 合伙人 ---')
    partners = scrape_lawyer_list(PARTNER_LIST_URL, '合伙人')
    print(f'  合伙人: {len(partners)}')

    # Scrape all lawyers
    print('\n--- 执业律师 ---')
    lawyers = scrape_lawyer_list(LAWYER_LIST_URL, '执业律师')
    print(f'  执业律师: {len(lawyers)}')

    all_new = partners + lawyers
    print(f'\n总计抓取: {len(all_new)} 位律师')

    # Merge
    existing_keys = {(l['name'], l.get('firm', '')) for l in existing}
    added = 0
    for l in all_new:
        key = (l['name'], l.get('firm', ''))
        if key not in existing_keys and l['name']:
            l['id'] = len(existing) + 1
            existing.append(l)
            existing_keys.add(key)
            added += 1

    for i, l in enumerate(existing):
        l['id'] = i + 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    tianhe = len([l for l in existing if l.get('district') == '天河区'])
    print(f'\n{"=" * 60}')
    print(f'  新增入库: {added} 位')
    print(f'  天河区总计: {tianhe}')
    print(f'  数据库总计: {len(existing)}')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
