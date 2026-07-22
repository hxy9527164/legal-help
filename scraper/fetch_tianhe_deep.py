"""
从 lawtime.cn 搜索天河区律师的完整列表
使用搜索API和分页
"""
import json, re, sys, time, random
from pathlib import Path
import requests
from bs4 import BeautifulSoup

OUTPUT_FILE = Path(__file__).parent.parent / 'data' / 'lawyers.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

session = requests.Session()
session.headers.update(HEADERS)


def search_lawtime_tianhe():
    """Try various search approaches on lawtime.cn"""
    all_urls = set()

    # Approach 1: Direct search URL
    search_urls = [
        'https://www.lawtime.cn/search/?q=天河区+律师',
        'https://www.lawtime.cn/guangzhou/tianhequ/',
        'https://www.lawtime.cn/guangzhou/tianhe/',
        'https://guangzhou.lawtime.cn/tianhequ/',
    ]

    for url in search_urls:
        try:
            resp = session.get(url, timeout=15, allow_redirects=True)
            print(f'URL: {url} -> HTTP {resp.status_code}, final={resp.url}')
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Find lawyer links
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/lawyer/lll' in href:
                        all_urls.add(href)

                # Also find "next page" links
                for a in soup.find_all('a', href=True):
                    txt = a.get_text(strip=True)
                    href = a['href']
                    if txt in ['下一页', '>', 'next'] and 'page' in href.lower():
                        print(f'  Pagination: {txt} -> {href}')
        except Exception as e:
            print(f'URL: {url} -> ERROR: {e}')
        time.sleep(1)

    print(f'\nTotal unique lawyer URLs found: {len(all_urls)}')
    return all_urls


def scrape_profile_detail(url):
    """Scrape full detail from lawyer profile page"""
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()

        info = {
            'name': '', 'firm': '未知律所', 'fields': ['民商事'],
            'experience': 0, 'education': '暂无学历信息',
            'city': '广州', 'province': '广东', 'district': '',
            'cases': '暂无案例信息', 'contact': '暂无联系方式',
            'license': '', 'source': 'lawtime.cn',
        }

        # Name
        for sel in ['.lawyer-name', '.name', 'h1', '.username']:
            el = soup.select_one(sel)
            if el:
                info['name'] = re.sub(r'律师.*$', '', el.get_text(strip=True)).strip()
                break

        # Law firm
        for sel in ['.lawfirm-name', '.firm-name', '.firm', '.company-name']:
            el = soup.select_one(sel)
            if el:
                info['firm'] = el.get_text(strip=True)
                break

        if info['firm'] == '未知律所':
            fm = re.search(r'([广北上深].{2,25}(律师.{2,10}所|律所|法律))', text)
            if fm: info['firm'] = fm.group(1)

        # Fields / specialty
        for sel in ['.specialty-list', '.goodat-list', '.skill-tags', '.tag-list']:
            el = soup.select_one(sel)
            if el:
                fields_text = el.get_text(strip=True)
                info['fields'] = [f.strip() for f in re.split(r'[、，/\s]+', fields_text) if len(f.strip()) > 1][:6]
                break

        # District
        dm = re.search(r'(天河区|越秀区|海珠区|荔湾区|白云区|黄埔区|番禺区|花都区|南沙区|增城区|从化区)', text)
        if dm: info['district'] = dm.group(1)

        # Experience
        for exp_text in re.findall(r'执业(\d+)年|(\d+)年执业|从业(\d+)年', text):
            for g in exp_text:
                if g and 1 <= int(g) <= 50:
                    info['experience'] = int(g)
                    break

        # Education
        em = re.search(r'(中山大学|华南理工|华南师范|暨南大学|广东外语|广东财经|广州大学|西南政法|中国政法|武汉大学|中南财经|华东政法|北京大学|中国人民大学|吉林大学|西北政法)\s*(法学)?\s*(博士|硕士|学士|研究生|本科)', text)
        if em: info['education'] = em.group()

        # Contact
        pm = re.search(r'(1[3-9]\d{9})', text)
        if pm:
            ph = pm.group(1)
            info['contact'] = ph[:3] + '****' + ph[-4:]

        # License number
        lm = re.search(r'14401\d{11}', text)
        if lm: info['license'] = lm.group()

        return info
    except Exception as e:
        return None


def main():
    print('=' * 60)
    print('  Deep search for Tianhe lawyers on lawtime.cn')
    print('=' * 60)

    # Load existing
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)

    existing_urls = {l.get('profile_url', '') for l in existing if l.get('profile_url')}

    # Search
    urls = search_lawtime_tianhe()

    # Scrape each
    new_lawyers = []
    urls_list = sorted(urls)
    for i, url in enumerate(urls_list):
        print(f'[{i+1}/{len(urls_list)}] Scraping: {url[-40:]} ...', end=' ')
        info = scrape_profile_detail(url)
        if info and info['name']:
            info['profile_url'] = url
            dist = info.get('district', '?')
            print(f'{info["name"]} [{dist}] - {info["firm"][:25]}')
            new_lawyers.append(info)
        else:
            print('skip')
        time.sleep(random.uniform(0.8, 1.5))

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
    print(f'  Total: {len(existing)} lawyers')
    print(f'  Tianhe: {tianhe}')
    print(f'  New added this run: {added}')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
