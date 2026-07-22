"""
法律自助助手 - 从 lawtime.cn 采集广州天河区真实律师数据
=========================================================
数据源: lawtime.cn (找法网)
采集内容: 律师姓名、律所、擅长领域、执业经验、学历、联系方式
"""

import json, re, sys, time, random
from pathlib import Path
from collections import Counter

import requests
from bs4 import BeautifulSoup

OUTPUT_FILE = Path(__file__).parent.parent / 'data' / 'lawyers.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

GY_LICENSE_PATTERN = re.compile(r'14401\d{11}')
EXP_PATTERN = re.compile(r'(\d+)年')
FIELD_SPLIT = re.compile(r'[、，,/;\s|]+')

session = requests.Session()
session.headers.update(HEADERS)


def scrape_lawyer_profile(url):
    """抓取单个律师详情页，提取完整信息"""
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()

        info = {
            'name': '',
            'firm': '未知律所',
            'fields': ['民商事'],
            'experience': 0,
            'education': '暂无学历信息',
            'license': '',
            'city': '广州',
            'province': '广东',
            'district': '',
        }

        # 律师姓名
        name_el = soup.select_one('.lawyer-name, .name, h1, .username, [class*=name]')
        if name_el:
            full = name_el.get_text(strip=True)
            # Clean "律师" suffix
            info['name'] = re.sub(r'律师.*$', '', full).strip()

        # 律所名称
        firm_el = soup.select_one('.firm, .lawfirm, .law-firm, .company, .office, [class*=firm], [class*=office]')
        if firm_el:
            info['firm'] = firm_el.get_text(strip=True)
        else:
            # Try to find from text
            firm_match = re.search(r'(广东|广州|北京|上海|深圳).{2,20}(律师.{2,10}所|律所)', text)
            if firm_match:
                info['firm'] = firm_match.group()

        # 执业证号
        lic_match = GY_LICENSE_PATTERN.search(text)
        if lic_match:
            info['license'] = lic_match.group()

        # 擅长领域
        fields_el = soup.select_one('.goodat, .specialty, .skill, .tag-list, [class*=good], [class*=special], [class*=tag]')
        if fields_el:
            fields_text = fields_el.get_text(strip=True)
            info['fields'] = [f.strip() for f in FIELD_SPLIT.split(fields_text) if len(f.strip()) > 1][:6]

        # 执业年限
        exp_el = soup.select_one('.experience, .exp, .year, [class*=exp], [class*=year]')
        if exp_el:
            exp_text = exp_el.get_text(strip=True)
            exp_match = EXP_PATTERN.search(exp_text)
            if exp_match:
                info['experience'] = int(exp_match.group(1))
        else:
            exp_match = EXP_PATTERN.search(text)
            if exp_match:
                val = int(exp_match.group(1))
                if 1 <= val <= 50:
                    info['experience'] = val

        # 学历
        edu_match = re.search(r'(博士|硕士|学士|研究生|本科|法学(博士|硕士|学士))', text)
        if edu_match:
            edu_start = max(0, edu_match.start() - 20)
            edu_end = min(len(text), edu_match.end() + 10)
            info['education'] = text[edu_start:edu_end].strip()[:50]

        # 所在地区
        dist_match = re.search(r'(天河区|越秀区|海珠区|荔湾区|白云区|黄埔区|番禺区|花都区|南沙区|增城区|从化区)', text)
        if dist_match:
            info['district'] = dist_match.group(1)

        # 联系方式（脱敏）
        phone_match = re.search(r'1[3-9]\d{9}|\d{3,4}-\d{7,8}', text)
        if phone_match:
            phone = phone_match.group()
            if len(phone) == 11:
                info['contact'] = phone[:3] + '****' + phone[-4:]
            else:
                info['contact'] = phone

        return info

    except Exception as e:
        print(f'    Profile error: {e}')
        return None


def scrape_lawtime_guangzhou():
    """从找法网广州站采集律师列表"""
    lawyers = []
    print('\n=== Scraping lawtime.cn Guangzhou ===')

    base_url = 'https://www.lawtime.cn/guangzhou/'
    resp = session.get(base_url, timeout=15)
    if resp.status_code != 200:
        print(f'  HTTP {resp.status_code}')
        return lawyers

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Collect all lawyer profile URLs
    profile_urls = set()

    # From lawyer blocks
    for div in soup.select('.lawyer.bdb1'):
        for a in div.find_all('a', href=True):
            href = a['href']
            if '/lawyer/lll' in href:
                profile_urls.add(href)

    # From rank lists
    for ul in soup.select('.lawyer-rank-list'):
        for a in ul.find_all('a', href=True):
            href = a['href']
            if '/lawyer/lll' in href:
                profile_urls.add(href)

    print(f'  Found {len(profile_urls)} unique lawyer profiles')

    # Scrape each profile
    for i, url in enumerate(sorted(profile_urls)):
        print(f'  [{i+1}/{len(profile_urls)}] {url[-30:]} ...', end=' ')
        info = scrape_lawyer_profile(url)
        if info and info['name']:
            # Check if Tianhe or Guangzhou
            lawyers.append(info)
            district = info.get('district', 'unknown')
            print(f'{info["name"]} ({district})')
        else:
            print('skip')

        # Polite delay
        time.sleep(random.uniform(1.0, 2.0))

    # Filter for Tianhe district
    tianhe_lawyers = [l for l in lawyers if '天河' in (l.get('district', '') or '')]

    print(f'\n  Total scraped: {len(lawyers)}')
    print(f'  Tianhe district: {len(tianhe_lawyers)}')
    print(f'  Guangzhou others: {len(lawyers) - len(tianhe_lawyers)}')

    return lawyers


def merge_lawyers(existing, new_data):
    """合并，按姓名+律所去重"""
    existing_keys = {(l['name'], l.get('firm', '')) for l in existing}
    added = 0
    for lawyer in new_data:
        if not lawyer.get('name'):
            continue
        key = (lawyer['name'], lawyer.get('firm', ''))
        if key not in existing_keys:
            lawyer['id'] = len(existing) + 1
            existing.append(lawyer)
            existing_keys.add(key)
            added += 1

    for i, l in enumerate(existing):
        l['id'] = i + 1

    return existing, added


def main():
    print('=' * 60)
    print('  天河区律师数据 - 从 lawtime.cn 真实采集')
    print('=' * 60)

    # Load existing
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    print(f'\nExisting lawyers: {len(existing)}')

    # Scrape
    try:
        new_lawyers = scrape_lawtime_guangzhou()
    except Exception as e:
        print(f'\nScraping failed: {e}')
        new_lawyers = []

    if new_lawyers:
        # Add default fields for scraped lawyers
        for l in new_lawyers:
            l.setdefault('source', 'lawtime.cn')
            l.setdefault('cases', '暂无案例信息')
            if not l.get('contact'):
                l['contact'] = '暂无联系方式'

        merged, added = merge_lawyers(existing, new_lawyers)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        tianhe_count = len([l for l in merged if l.get('district') == '天河区'])
        print(f'\n{"=" * 60}')
        print(f'  Results:')
        print(f'    New from web: {len(new_lawyers)}')
        print(f'    Added to DB: {added}')
        print(f'    Total DB: {len(merged)}')
        print(f'    Tianhe total: {tianhe_count}')
        print(f'{"=" * 60}')
    else:
        print('\nNo new lawyers found online.')


if __name__ == '__main__':
    main()
