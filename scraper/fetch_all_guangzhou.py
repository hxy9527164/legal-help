"""
全量采集广州市11区执业律师数据
===============================
数据源: lawtime.cn (找法网) - 已确认可访问
策略: 从广州站发现律师 → 爬取详情 → 按区分类入库

广州市辖区: 天河 越秀 海珠 荔湾 白云 黄埔 番禺 花都 南沙 增城 从化
"""
import json, re, time, random, sys
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

GZ_DISTRICTS = ['天河区','越秀区','海珠区','荔湾区','白云区','黄埔区','番禺区','花都区','南沙区','增城区','从化区']

session = requests.Session()
session.headers.update(HEADERS)


def discover_profile_urls():
    """从多个入口发现律师个人页URL"""
    urls = set()
    print('\n--- 发现律师URL ---')

    # 入口1: 广州站主页
    try:
        resp = session.get('https://www.lawtime.cn/guangzhou/', timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/lawyer/lll' in href:
                urls.add(href)
        print(f'  广州主页: {len(urls)} URLs')
    except Exception as e:
        print(f'  广州主页: {e}')

    # 入口2: 广州站排名列表
    for ul in soup.select('.lawyer-rank-list'):
        for a in ul.find_all('a', href=True):
            if '/lawyer/lll' in a['href']:
                urls.add(a['href'])

    # 入口3: 律师区块
    for div in soup.select('.lawyer.bdb1'):
        for a in div.find_all('a', href=True):
            if '/lawyer/lll' in a['href']:
                urls.add(a['href'])

    print(f'  总计发现: {len(urls)} 个唯一URL')

    # 入口4: 基于已知广州律师ID扩展搜索（+-1000万范围内采样）
    known_base = [109233272109238366, 120487133120492227, 128486136128491230,
                  134976999134982093, 135726583135731677, 135859744135864838]
    extra_urls = set()
    for kid in known_base:
        for delta in range(-2000000, 2000001, 250000):
            try_id = kid + delta
            extra_urls.add(f'https://www.lawtime.cn/lawyer/lll{try_id}')

    # 采样检测这些URL是否有效（只测试部分）
    sample = list(extra_urls)[:80]
    valid_extra = 0
    for url in sample:
        try:
            r = session.head(url, timeout=8, allow_redirects=True)
            if r.status_code == 200:
                urls.add(url)
                valid_extra += 1
        except:
            pass
        time.sleep(0.1)
    print(f'  ID扩展: 测试{len(sample)}个, 有效{valid_extra}个')
    print(f'  最终URL总数: {len(urls)}')

    return list(urls)


def scrape_profile(url):
    """抓取律师个人页完整信息"""
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()

        # 检查是否广州律师
        if '广州' not in text:
            return None

        info = {
            'name': '', 'firm': '未知律所', 'fields': ['民商事'],
            'experience': 0, 'education': '暂无学历信息',
            'city': '广州', 'province': '广东', 'district': '',
            'cases': '暂无案例信息', 'contact': '暂无联系方式',
            'photo': '', 'license': '', 'position': '',
            'service_count': 0, 'source': 'lawtime.cn',
            'profile_url': url,
        }

        # Photo
        for sel in ['.lawyer-img-box img', '.lawyer-photo img', '.avatar img', 'img.cover-img']:
            img_el = soup.select_one(sel)
            if img_el:
                src = img_el.get('src', '') or img_el.get('data-src', '')
                if src and len(src) > 10:
                    info['photo'] = 'https:' + src if src.startswith('//') else src
                    break

        # Name
        for sel in ['.lawyer-name', '.name', 'h1']:
            el = soup.select_one(sel)
            if el:
                name_text = el.get_text(strip=True)
                info['name'] = re.sub(r'(律师|主任|合伙人|实习律师|团队).*$', '', name_text).strip()
                break

        # Position
        pos_match = re.search(r'(高级合伙人|合伙人|主任律师|副主任|执业律师|实习律师|创始合伙人|首席合伙人|专职律师)', text)
        if pos_match: info['position'] = pos_match.group(1)

        # Firm
        fm = re.search(r'([广北上深杭成渝武].{2,30}(律师.{2,12}所|律所|法律))', text)
        if fm: info['firm'] = fm.group(1)

        # District
        for d in GZ_DISTRICTS:
            if d in text:
                info['district'] = d
                break

        # Fields
        field_sec = re.search(r'(?:擅长|专业|领域|业务|专长)[：:]\s*([^。\n]{3,200})', text)
        if field_sec:
            info['fields'] = [f.strip() for f in re.split(r'[、，/\s]+', field_sec.group(1)) if len(f.strip()) > 1][:8]

        # Experience
        for m in re.finditer(r'(\d+)\s*年', text):
            y = int(m.group(1))
            if 1 <= y <= 50: info['experience'] = y; break

        # Education
        edu_m = re.search(r'(中山大学|华南理工|暨南大学|广东外语|广东财经|广州大学|西南政法|中国政法|武汉大学|中南财经|华东政法|北京大学|中国人民大学|深圳大学|华南师范|吉林大学|厦门大学|浙江大学|复旦大学|南京大学|西北政法)[^。\n]{0,20}(博士|硕士|学士|本科)', text)
        if edu_m: info['education'] = edu_m.group()

        # Service count
        sc = re.search(r'(\d+)\s*次', text)
        if sc: info['service_count'] = int(sc.group(1))

        # License
        lic_m = re.search(r'14401\d{11}', text)
        if lic_m: info['license'] = lic_m.group()

        # Phone
        phone_m = re.search(r'(1[3-9]\d{9})', text)
        if phone_m:
            p = phone_m.group(1)
            info['contact'] = p[:3] + '****' + p[-4:]

        return info
    except Exception:
        return None


def main():
    print('=' * 60)
    print('  全广州11区律师数据采集')
    print('=' * 60)

    # Load existing
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    print(f'\n现有律师: {len(existing)}')

    # Discover URLs
    all_urls = discover_profile_urls()

    # Scrape each profile
    new_lawyers = []
    existing_urls = {l.get('profile_url', '') for l in existing}

    print(f'\n--- 抓取律师详情 ({len(all_urls)} URLs) ---')
    for i, url in enumerate(all_urls):
        if url in existing_urls:
            continue
        print(f'  [{i+1}/{len(all_urls)}]', end=' ')
        info = scrape_profile(url)
        if info and info['name'] and len(info['name']) >= 2:
            dist = info.get('district', '?')
            photo = '📷' if info.get('photo') else ''
            print(f'{info["name"]} [{dist}] {photo}')
            new_lawyers.append(info)
        else:
            print('skip')
        time.sleep(random.uniform(0.3, 0.7))

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

    # Stats
    dist_counts = Counter(l.get('district', '未知') for l in existing)
    photo_count = len([l for l in existing if l.get('photo', '').startswith('http')])

    print(f'\n{"=" * 60}')
    print(f'  采集结果')
    print(f'  新增: {added} | 总计: {len(existing)}')
    print(f'  有照片: {photo_count}')
    print(f'  各区分布:')
    for d in GZ_DISTRICTS:
        c = dist_counts.get(d, 0)
        bar = '█' * (c // 5) if c > 0 else ''
        print(f'    {d}: {c} {bar}')
    other = sum(c for d, c in dist_counts.items() if d not in GZ_DISTRICTS and d != '未知')
    if other > 0:
        print(f'    其他: {other}')
    print(f'{"=" * 60}')

    # Regenerate JS data file
    js_path = OUTPUT_FILE.parent / 'lawyers-data.js'
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write('window.__lawyersData = ' + json.dumps(existing, ensure_ascii=False, indent=2) + ';\n')
    print(f'JS数据文件已更新: {js_path}')


if __name__ == '__main__':
    main()
