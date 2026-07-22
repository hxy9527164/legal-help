"""
从华律网(66law.cn)采集广州天河区律师
该平台有按城市的律师目录
"""
import json, re, sys, time, random
from pathlib import Path
import requests
from bs4 import BeautifulSoup

OUTPUT_FILE = Path(__file__).parent.parent / 'data' / 'lawyers.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://www.66law.cn/',
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch_66law_lawyers_by_area():
    """从华律网按地区采集广州律师"""
    lawyers = []
    base = 'https://www.66law.cn'

    # 尝试分页的广州律师列表
    urls_to_try = [
        f'{base}/findlawyers/guangzhou/',
        f'{base}/lawyeroffice/guangzhou/',
        f'{base}/lawyer/area/440100/',
    ]

    for list_url in urls_to_try:
        print(f'Trying: {list_url}')
        try:
            resp = session.get(list_url, timeout=15, allow_redirects=True)
            print(f'  Status: {resp.status_code}, final: {resp.url[:80]}')
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Find lawyer cards/links
                lawyer_links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    # Match 66law lawyer profile URLs
                    if re.search(r'/lawyer/[a-f0-9]{10,}', href):
                        name = a.get_text(strip=True)
                        if name and len(name) >= 2:
                            full_url = href if href.startswith('http') else base + href
                            lawyer_links.append({'name': name, 'url': full_url})

                # Also check for list items with lawyer info
                for item in soup.select('.lawyer_list li, .lawyer-item, .lawyer_card, [class*=lawyer-item]'):
                    text = item.get_text()
                    if '广州' in text or '天河' in text or '广东' in text:
                        for a in item.find_all('a', href=True):
                            if '/lawyer/' in a['href']:
                                name = a.get_text(strip=True)
                                if len(name) >= 2:
                                    full_url = a['href'] if a['href'].startswith('http') else base + a['href']
                                    lawyer_links.append({'name': name, 'url': full_url})

                print(f'  Found {len(lawyer_links)} lawyer links')

                # Scrape each profile
                for i, ll in enumerate(lawyer_links[:30]):  # Limit per URL
                    info = scrape_66law_profile(ll['url'])
                    if info and info['name']:
                        lawyers.append(info)
                        print(f'    [{i+1}] {info["name"]} - {info.get("district","?")}')
                    time.sleep(random.uniform(0.5, 1.0))

                if lawyers:
                    break
        except Exception as e:
            print(f'  Error: {e}')
        time.sleep(1)

    return lawyers


def scrape_66law_profile(url):
    """从华律网律师个人页提取信息"""
    try:
        resp = session.get(url, timeout=15, headers=HEADERS)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()

        info = {
            'name': '', 'firm': '未知律所', 'fields': ['民商事'],
            'experience': 0, 'education': '暂无学历信息',
            'city': '广州', 'province': '广东', 'district': '',
            'cases': '暂无案例信息', 'contact': '暂无联系方式',
            'source': '66law.cn', 'profile_url': url,
        }

        # Name
        name_el = soup.select_one('h1, .name, .lawyer-name, .username')
        if name_el:
            info['name'] = re.sub(r'(律师|主任|合伙人).*$', '', name_el.get_text(strip=True)).strip()

        # Firm
        for sel in ['.lawfirm', '.firm-name', '.law-firm']:
            el = soup.select_one(sel)
            if el:
                info['firm'] = el.get_text(strip=True)
                break

        if info['firm'] == '未知律所':
            fm = re.search(r'(广东|广州).{2,30}(律师.{2,10}所|律所)', text)
            if fm: info['firm'] = fm.group(1)

        # District
        dm = re.search(r'(天河区|越秀区|海珠区|荔湾区|白云区|黄埔区|番禺区|花都区)', text)
        if dm: info['district'] = dm.group(1)

        # Specialties
        for sel in ['.goodat', '.specialty', '.skill-list', '.tag-list']:
            el = soup.select_one(sel)
            if el:
                ft = el.get_text(strip=True)
                info['fields'] = [f.strip() for f in re.split(r'[、，/\s]+', ft) if len(f.strip()) > 1][:6]
                break

        # Experience
        for m in re.finditer(r'(\d+)\s*年', text):
            y = int(m.group(1))
            if 1 <= y <= 50:
                info['experience'] = y
                break

        # Education
        em = re.search(r'(中山大学|华南理工|华南师范|暨南大学|西南政法|中国政法|武汉大学|中南财经|华东政法|北京大学|中国人民大学|吉林大学|广州大学|广东财经).{0,8}(博士|硕士|学士|本科)', text)
        if em: info['education'] = em.group()

        return info
    except Exception as e:
        return None


def main():
    print('=' * 60)
    print('  66law.cn 广州律师采集')
    print('=' * 60)

    # Load existing
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    print(f'\n现有律师: {len(existing)}')

    # Scrape
    new_lawyers = fetch_66law_lawyers_by_area()

    # Merge
    existing_keys = {(l['name'], l.get('firm', '')) for l in existing}
    added = 0
    for l in new_lawyers:
        key = (l['name'], l.get('firm', ''))
        if key not in existing_keys and l['name']:
            existing.append(l)
            existing_keys.add(key)
            added += 1

    for i, l in enumerate(existing):
        l['id'] = i + 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    tianhe = len([l for l in existing if l.get('district') == '天河区'])
    print(f'\n{"=" * 60}')
    print(f'  新增: {added} | 天河区总计: {tianhe} | 总库: {len(existing)}')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
