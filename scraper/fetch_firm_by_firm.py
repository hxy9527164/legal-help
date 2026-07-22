"""
法律自助助手 - 逐所采集天河区律所真实律师数据
==============================================
策略:
  第1步: 在各法律平台搜索每家律所 → 获取该律所的律师列表
  第2步: 访问律师个人详情页 → 提取完整信息
  第3步: 对于平台上找不到的律所，尝试访问其官网

目标平台:
  - lawtime.cn (找法网) - 已确认可访问
  - 66law.cn (华律网)
  - 各律所官方网站
"""

import json, re, sys, time, random
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

OUTPUT_FILE = Path(__file__).parent.parent / 'data' / 'lawyers.json'
LOG_FILE = Path(__file__).parent / 'firm_scrape_log.txt'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.lawtime.cn/',
}

# 天河区35家律所
TIANHE_FIRMS = [
    ('广东广信君达律师事务所', 'large', '珠江东路6号周大福金融中心'),
    ('广东法制盛邦律师事务所', 'large', '天河路385号太古汇'),
    ('广东金桥百信律师事务所', 'large', '珠江新城珠江东路16号'),
    ('广东国智律师事务所', 'large', '珠江新城兴民路222号'),
    ('广东君信经纶君厚律师事务所', 'large', '珠江新城华夏路10号'),
    ('广东环球经纬律师事务所', 'large', '体育东路122号羊城国际商贸中心'),
    ('广东南国德赛律师事务所', 'large', '天河北路233号中信广场'),
    ('广东国信信扬律师事务所', 'large', '天河路101号兴业银行大厦'),
    ('广东卓信律师事务所', 'medium', '体育西路109号高盛大厦'),
    ('广东正大方略律师事务所', 'medium', '体育西路189号城建大厦'),
    ('广东南方福瑞德律师事务所', 'medium', '天河路208号粤海天河城'),
    ('广东连越律师事务所', 'medium', '体育西路103号维多利广场'),
    ('广东合盛律师事务所', 'medium', '天河路625号天娱广场'),
    ('广东启源律师事务所', 'medium', '天河路383号'),
    ('广东天禄盟德律师事务所', 'medium', '珠江新城金穗路62号'),
    ('广东恒益律师事务所', 'medium', '珠江新城珠江西路5号'),
    ('广东红棉律师事务所', 'medium', '体育西路57号红棉大厦'),
    ('广东达生律师事务所', 'medium', '珠江新城花城大道68号'),
    ('广东天穗律师事务所', 'medium', '体育西路111号建和中心'),
    ('广东科德律师事务所', 'medium', '天河北路898号信源大厦'),
    ('广东盈隆律师事务所', 'medium', '珠江新城华夏路28号'),
    ('广东保典律师事务所', 'small', '体育东路140号南方证券大厦'),
    ('广东洛亚律师事务所', 'small', '华夏路30号富力盈通大厦'),
    ('广东格方律师事务所', 'small', '天河北路559号太平洋保险大厦'),
    ('广东创杰律师事务所', 'small', '体育西路109号高盛大厦'),
    ('广东大钧律师事务所', 'small', '花城大道85号高德置地广场'),
    ('广东瑞辉律师事务所', 'small', '珠江新城临江大道5号保利中心'),
    ('广东骏道律师事务所', 'small', '天河路351号广东外经贸大厦'),
    ('广东拓孚创展律师事务所', 'small', '体育西路189号城建大厦'),
    ('广东经纶律师事务所', 'small', '体育西路109号高盛大厦'),
    ('广东林和律师事务所', 'small', '林和西路167号威尼国际大厦'),
    ('广东粤高律师事务所', 'small', '体育东路116号财富广场'),
    ('广东法仪律师事务所', 'small', '珠江新城华强路2号'),
    ('广东明思律师事务所', 'small', '天河路228号正佳广场'),
    ('广东尚辰律师事务所', 'small', '华穗路406号保利克洛维广场'),
]

FOUND_LAWYERS = []
LOG_ENTRIES = []


def log(msg):
    print(msg)
    LOG_ENTRIES.append(msg)


def search_firm_on_lawtime(firm_name):
    """在找法网搜索律所名称，获取该律所的律师列表"""
    lawyers = []
    try:
        # 搜索URL
        search_url = f'https://www.lawtime.cn/search/?q={quote(firm_name)}'
        resp = requests.get(search_url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            log(f'  lawtime search HTTP {resp.status_code}')
            return lawyers

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 查找律师链接
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/lawyer/lll' in href:
                lawyers.append({
                    'url': href,
                    'name': a.get_text(strip=True).replace('律师', ''),
                    'source': 'lawtime.cn/search',
                })

        log(f'  lawtime.cn search: {len(lawyers)} lawyers found')
    except Exception as e:
        log(f'  lawtime search error: {e}')

    return lawyers


def search_firm_on_66law(firm_name):
    """在华律网搜索律所"""
    lawyers = []
    try:
        search_url = f'https://www.66law.cn/search/lawyer/?q={quote(firm_name)}'
        resp = requests.get(search_url, headers=HEADERS, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            log(f'  66law search HTTP {resp.status_code}')
            return lawyers

        soup = BeautifulSoup(resp.text, 'html.parser')

        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/lawyer/' in href and re.search(r'/lawyer/\d+', href):
                lawyers.append({
                    'url': href,
                    'name': a.get_text(strip=True).replace('律师', ''),
                    'source': '66law.cn/search',
                })

        log(f'  66law.cn search: {len(lawyers)} lawyers found')
    except Exception as e:
        log(f'  66law search error: {e}')

    return lawyers


def find_firm_website(firm_name):
    """尝试找到律所的官方网站"""
    # 常见域名模式
    name_short = firm_name.replace('律师事务所', '').replace('广东', '')
    possible_domains = [
        f'https://www.{name_short}law.com',
        f'https://www.{name_short}law.cn',
        f'https://www.{name_short}lawyer.com',
        f'https://www.{name_short}.com.cn',
        f'https://www.gd{name_short}.com',
    ]

    # 更实际的方案：在搜索引擎中找
    # 由于WebSearch受限，这里使用已知的大所网站
    known_sites = {
        '广东广信君达律师事务所': 'https://www.gxjunda.com',
        '广东法制盛邦律师事务所': 'https://www.fazhishengbang.com',
        '广东金桥百信律师事务所': 'https://www.jqbx.com',
        '广东国智律师事务所': 'https://www.guozhilaw.com',
        '广东环球经纬律师事务所': 'https://www.globallaw.com.cn',
        '广东南国德赛律师事务所': 'https://www.desailaw.com',
        '广东国信信扬律师事务所': 'https://www.gx-lawfirm.com',
        '广东卓信律师事务所': 'https://www.zhuoxinlaw.com',
        '广东红棉律师事务所': 'https://www.hongmianlaw.com',
        '广东天穗律师事务所': 'https://www.tiansuilaw.com',
        '广东连越律师事务所': 'https://www.lianyuelaw.com',
    }

    if firm_name in known_sites:
        return known_sites[firm_name]

    # 对于其他律所，尝试常见模式
    for domain in possible_domains:
        try:
            resp = requests.head(domain, headers=HEADERS, timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                log(f'  Found website: {domain}')
                return domain
        except Exception:
            continue

    return None


def scrape_firm_team_page(website_url, firm_name):
    """从律所官网抓取律师团队信息"""
    lawyers = []
    if not website_url:
        return lawyers

    # 可能的团队页面路径
    team_paths = [
        '/team', '/lawyer', '/lawyers', '/about/team',
        '/professional', '/professionals', '/people',
        '/team.html', '/lawyer.html', '/list/team',
        '/index.php?c=article&a=list&catid=', '/team/list',
        '/about.html', '/gywm', '/aboutus',
    ]

    for path in team_paths:
        try:
            url = website_url.rstrip('/') + path
            resp = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text()

            # 检查页面是否像律师团队页
            lawyer_keywords = ['律师', '合伙人', '团队', '专业']
            if not any(kw in text for kw in lawyer_keywords):
                continue

            # 查找律师链接
            lawyer_links = []
            for a in soup.find_all('a', href=True):
                link_text = a.get_text(strip=True)
                href = a['href']
                # 跳过导航链接
                if len(link_text) < 2 or len(link_text) > 30:
                    continue
                # 找到人名链接（中文名2-4字，可能带职位）
                if re.match(r'^[一-鿿]{2,4}(律师|合伙人|主任)?$', link_text):
                    full_url = href if href.startswith('http') else website_url.rstrip('/') + '/' + href.lstrip('/')
                    lawyer_links.append({
                        'name': re.sub(r'(律师|合伙人|主任)$', '', link_text),
                        'url': full_url,
                    })

            if lawyer_links:
                log(f'  Found {len(lawyer_links)} lawyer links at {path}')
                for ll in lawyer_links:
                    lawyers.append({
                        'name': ll['name'],
                        'firm': firm_name,
                        'profile_url': ll['url'],
                        'source': 'firm_website',
                    })
                return lawyers  # 找到就返回

        except Exception as e:
            continue

    return lawyers


def scrape_profile_from_lawtime(lawyer_url):
    """从找法网律师个人页提取详细信息"""
    try:
        resp = requests.get(lawyer_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()

        info = {
            'name': '', 'firm': '未知律所', 'fields': ['民商事'],
            'experience': 0, 'education': '暂无学历信息',
            'city': '广州', 'province': '广东', 'district': '',
            'cases': '暂无案例信息', 'contact': '暂无联系方式',
            'source': 'lawtime.cn',
        }

        # Name
        name_el = soup.select_one('.lawyer-name, .name, h1')
        if name_el:
            info['name'] = re.sub(r'律师.*$', '', name_el.get_text(strip=True)).strip()

        # Firm
        firm_match = re.search(r'([广北上深].{2,30}(律师.{2,10}所|律所|法律))', text)
        if firm_match:
            info['firm'] = firm_match.group(1)

        # District
        dist_match = re.search(r'(天河区|越秀区|海珠区|荔湾区|白云区|黄埔区|番禺区|花都区|南沙区|增城区|从化区)', text)
        if dist_match:
            info['district'] = dist_match.group(1)

        # Experience
        for m in re.finditer(r'(\d+)\s*年', text):
            y = int(m.group(1))
            if 1 <= y <= 50:
                info['experience'] = y
                break

        # Education
        edu_match = re.search(r'(中山大学|华南理工|华南师范|暨南大学|广东外语|西南政法|中国政法|武汉大学|中南财经|华东政法|北京大学|中国人民大学|吉林大学)\s*(法学)?\s*(博士|硕士|学士|本科)', text)
        if edu_match:
            info['education'] = edu_match.group()

        # Phone
        phone_match = re.search(r'(1[3-9]\d{9})', text)
        if phone_match:
            p = phone_match.group(1)
            info['contact'] = p[:3] + '****' + p[-4:]

        return info
    except Exception:
        return None


def main():
    global FOUND_LAWYERS, LOG_ENTRIES

    log('=' * 60)
    log('  逐所采集: 天河区35家律所真实律师数据')
    log('=' * 60)

    # 加载现有数据
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    log(f'\n当前数据库: {len(existing)} 位律师')

    existing_names = {(l['name'], l.get('firm', '')) for l in existing}
    new_lawyers_all = []

    # =========================================
    # Phase 1: 在法律平台搜索每家律所
    # =========================================
    log('\n' + '=' * 40)
    log('Phase 1: 在法律平台搜索律所')
    log('=' * 40)

    for i, (firm_name, size, address) in enumerate(TIANHE_FIRMS):
        log(f'\n[{i+1}/35] {firm_name} ({size})')

        firm_lawyers = []

        # 在找法网搜索
        lt_results = search_firm_on_lawtime(firm_name)
        for r in lt_results:
            firm_lawyers.append(r)

        # 在华律网搜索
        time.sleep(random.uniform(0.5, 1.0))
        lw_results = search_firm_on_66law(firm_name)
        for r in lw_results:
            if r['url'] not in {x['url'] for x in firm_lawyers}:
                firm_lawyers.append(r)

        log(f'  Total found: {len(firm_lawyers)}')

        # 对于找到的律师，抓取详情
        for j, lw in enumerate(firm_lawyers[:10]):  # 每家最多10个
            if (lw['name'], firm_name) in existing_names:
                continue

            time.sleep(random.uniform(0.3, 0.8))
            profile = scrape_profile_from_lawtime(lw['url'])
            if profile and profile['name']:
                profile['district'] = '天河区'
                profile['firm'] = firm_name
                new_lawyers_all.append(profile)
                log(f'    [{j+1}] {profile["name"]} - {profile.get("experience", "?")}yr')

        time.sleep(random.uniform(0.5, 1.5))

    # =========================================
    # Phase 2: 尝试律所官网
    # =========================================
    log('\n' + '=' * 40)
    log('Phase 2: 尝试律所官网')
    log('=' * 40)

    firms_without_platform_data = [
        f for f, s, a in TIANHE_FIRMS
        if not any(l.get('firm') == f for l in new_lawyers_all)
    ]

    for i, firm_name in enumerate(firms_without_platform_data):
        log(f'\n[{i+1}/{len(firms_without_platform_data)}] {firm_name}')
        website = find_firm_website(firm_name)
        if website:
            log(f'  Website: {website}')
            web_lawyers = scrape_firm_team_page(website, firm_name)
            for wl in web_lawyers:
                if (wl['name'], firm_name) not in existing_names:
                    wl['district'] = '天河区'
                    wl['fields'] = ['民商事']
                    wl['experience'] = 0
                    wl['education'] = '暂无学历信息'
                    wl['cases'] = '暂无案例信息'
                    wl['contact'] = '暂无联系方式'
                    new_lawyers_all.append(wl)
            log(f'  Website lawyers: {len(web_lawyers)}')
        else:
            log(f'  No website found')

        time.sleep(random.uniform(1.0, 2.0))

    # =========================================
    # 合并 & 保存
    # =========================================
    log(f'\n{"=" * 60}')
    log(f'  采集结果汇总')
    log(f'{"=" * 60}')
    log(f'  新采集律师: {len(new_lawyers_all)}')

    added = 0
    for l in new_lawyers_all:
        key = (l.get('name', ''), l.get('firm', ''))
        if key not in existing_names and l.get('name'):
            existing.append(l)
            existing_names.add(key)
            added += 1

    for i, l in enumerate(existing):
        l['id'] = i + 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    tianhe = len([l for l in existing if l.get('district') == '天河区'])
    log(f'  新增入库: {added}')
    log(f'  天河区律师总数: {tianhe}')
    log(f'  数据库总计: {len(existing)}')

    # 保存日志
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(LOG_ENTRIES))

    log(f'\n  日志: {LOG_FILE}')


if __name__ == '__main__':
    main()
