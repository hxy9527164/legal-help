"""
探测律所官网和搜索平台的真实URL结构
"""
import requests, re
from bs4 import BeautifulSoup
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

session = requests.Session()
session.headers.update(HEADERS)

# ====== 1. 探测律所官网 ======
print("=" * 60)
print("Phase 1: 探测律所官网")
print("=" * 60)

firm_sites = {
    '广东广信君达律师事务所': ['https://www.gxjunda.com', 'https://www.etrlawfirm.com'],
    '广东法制盛邦律师事务所': ['https://www.fazhishengbang.com', 'https://www.everwinlaw.com'],
    '广东金桥百信律师事务所': ['https://www.jqbx.com', 'https://www.goldenbridgelaw.com'],
    '广东国智律师事务所': ['https://www.guozhilaw.com'],
    '广东环球经纬律师事务所': ['https://www.globallaw.com.cn', 'https://www.grandall.com.cn'],
    '广东南国德赛律师事务所': ['https://www.desailaw.com'],
    '广东国信信扬律师事务所': ['https://www.gx-lawfirm.com'],
    '广东连越律师事务所': ['https://www.lianyuelaw.com'],
    '广东红棉律师事务所': ['https://www.hongmianlaw.com'],
    '广东天穗律师事务所': ['https://www.tiansuilaw.com'],
    '广东卓信律师事务所': ['https://www.zhuoxinlaw.com'],
}

for firm_name, urls in firm_sites.items():
    print(f'\n{firm_name}:')
    for url in urls:
        try:
            resp = session.get(url, timeout=10, allow_redirects=True)
            final_url = resp.url
            status = resp.status_code
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = (soup.title.string if soup.title else 'N/A')[:80]

            # Find all links
            links = soup.find_all('a', href=True)
            team_links = []
            for a in links:
                href = a['href']
                txt = a.get_text(strip=True)
                if any(kw in (txt + href).lower() for kw in ['team', 'lawyer', 'people', 'professional', '律师', '团队', '合伙人', '专业人员']):
                    team_links.append(f'  {txt[:40]} -> {href[:80]}')

            print(f'  {url}: HTTP{status}, title="{title}"')
            if team_links:
                print(f'  Team links ({len(team_links)}):')
                for tl in team_links[:8]:
                    print(tl)
        except Exception as e:
            print(f'  {url}: ERROR - {str(e)[:80]}')
    time.sleep(0.5)

# ====== 2. 探测搜索平台 ======
print("\n" + "=" * 60)
print("Phase 2: 探测法律平台搜索")
print("=" * 60)

# lawtime.cn - check the search form
print("\n--- lawtime.cn ---")
try:
    resp = session.get('https://www.lawtime.cn/', timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find search forms
    for form in soup.find_all('form'):
        action = form.get('action', '')
        method = form.get('method', 'get')
        print(f'  Form: {method} {action}')
        for inp in form.find_all('input'):
            print(f'    Input: name={inp.get("name","")}, type={inp.get("type","")}')

    # Find search-related elements
    for el in soup.select('[class*=search], [id*=search], input[type=text]'):
        print(f'  Search element: {el.name}#{el.get("id","")}.{" ".join(el.get("class",[]))}')

    # Check if there's a sitemap or navigation
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'lawyer' in href.lower() and '/lll' not in href:
            print(f'  Lawyer list link: {a.get_text(strip())[:40]} -> {href[:80]}')
except Exception as e:
    print(f'  ERROR: {e}')

# 66law.cn - check search
print("\n--- 66law.cn ---")
try:
    resp = session.get('https://www.66law.cn/', timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')

    for form in soup.find_all('form'):
        action = form.get('action', '')
        print(f'  Form: {form.get("method","get")} {action}')
        for inp in form.find_all('input'):
            print(f'    Input: name={inp.get("name","")}')

    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'lawyer' in href.lower() and 'lawyer' not in href[:10]:
            print(f'  Lawyer link: {a.get_text(strip=True)[:40]} -> {href[:80]}')
except Exception as e:
    print(f'  ERROR: {e}')

# ====== 3. 已确认的 lawtime.cn 律师页面（之前采集到的） ======
print("\n" + "=" * 60)
print("Phase 3: 尝试 lawtime.cn 律师列表API")
print("=" * 60)

# 尝试数值递增方式抓取律师
for i in range(1, 6):
    try:
        url = f'https://www.lawtime.cn/guangzhou/p{i}/'
        resp = session.get(url, timeout=10)
        print(f'  Page {i}: HTTP {resp.status_code}')
    except Exception as e:
        print(f'  Page {i}: {e}')
    time.sleep(0.5)
