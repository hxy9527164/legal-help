import requests, re
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','Accept-Language': 'zh-CN,zh;q=0.9'}
s = requests.Session()
s.headers.update(HEADERS)

# 1. Check 广信君达 pagination
print("=== 广信君达 pagination ===")
resp = s.get('https://www.etrlawfirm.com/cn/zyls/list_68.aspx', timeout=15)
soup = BeautifulSoup(resp.text, 'html.parser')

for a in soup.find_all('a', href=True):
    href = a['href']
    txt = a.get_text(strip=True)
    if 'page' in href.lower() or 'list_68' in href or txt in ['下一页','尾页','首页','上一页','>','>>']:
        print(f"  [{txt[:20]}] -> {href}")

# Check for ASP.NET pagination
for span in soup.select('[class*=page], [class*=pager], [id*=page]'):
    print(f"  Page element: {span.name}.{'.'.join(span.get('class',[]))} #{span.get('id','')}")

# Find __doPostBack or similar
scripts = soup.find_all('script')
for script in scripts:
    txt = script.get_text()
    if 'page' in txt.lower() or 'pager' in txt.lower() or 'postback' in txt.lower():
        for line in txt.split('\n')[:5]:
            line = line.strip()
            if line and 'page' in line.lower():
                print(f"  Script: {line[:120]}")

# Try alternative pagination URLs for ASP.NET
print("\n=== Trying ASP.NET pagination patterns ===")
patterns = [
    '/cn/zyls/list_68.aspx?page=2',
    '/cn/zyls/list_68.aspx?p=2',
    '/cn/zyls/list_68.aspx?pageindex=2',
    '/cn/zyls/list_68_2.aspx',
]
for pat in patterns:
    url = 'https://www.etrlawfirm.com' + pat
    try:
        r = s.get(url, timeout=10, allow_redirects=True)
        items = BeautifulSoup(r.text, 'html.parser').select('a[href]')
        lawyer_count = len([a for a in items if len(a.get_text(strip=True)) in (2,3,4)])
        print(f"  {pat}: HTTP{r.status_code}, lawyers={lawyer_count}")
    except Exception as e:
        print(f"  {pat}: ERROR {e}")

# 2. Check 国浩律师事务所
print("\n=== 国浩律师事务所 ===")
resp2 = s.get('https://www.grandall.com.cn/lsss/index.aspx', timeout=15)
soup2 = BeautifulSoup(resp2.text, 'html.parser')

# Find form inputs
for inp in soup2.find_all(['input', 'select']):
    name = inp.get('name', '')
    inp_id = inp.get('id', '')
    inp_type = inp.get('type', '')
    print(f"  {inp.name}: name={name}, id={inp_id}, type={inp_type}")

# Check for lawyer search
lawyer_links = soup2.find_all('a', href=True)
for a in lawyer_links:
    txt = a.get_text(strip=True)
    href = a['href']
    if len(txt) >= 2 and len(txt) <= 4 and re.match(r'^[一-鿿]+$', txt):
        print(f"  Lawyer name: {txt} -> {href[:80]}")

# 3. Try other big firm websites
print("\n=== 探测其他大所网站 ===")
firm_domains = [
    ('金桥百信', 'https://www.kbfirm.com'),
    ('金桥百信', 'https://www.jqblaw.com'),
    ('金桥百信', 'https://www.jqblawyer.com'),
    ('法制盛邦', 'https://www.everwinlawyer.com'),
    ('法制盛邦', 'https://www.fzsb.com'),
    ('君信经纶君厚', 'https://www.jxjjlaw.com'),
    ('君信经纶君厚', 'https://www.junxinlaw.com'),
    ('国信信扬', 'https://www.gx-lawyer.com'),
    ('国信信扬', 'https://www.gxxylaw.com'),
    ('天穗', 'https://www.tslawyer.com'),
    ('天穗', 'https://www.tiansui-law.com'),
    ('红棉', 'https://www.hmlaw.com.cn'),
    ('红棉', 'https://www.hongmian-law.com'),
    ('卓信', 'https://www.zx-lawfirm.com'),
    ('卓信', 'https://www.zhuoxin-law.com'),
    ('连越', 'https://www.lianyue-law.com'),
    ('连越', 'https://www.lianyuelawyer.com'),
]

for firm, domain in firm_domains:
    try:
        r = s.get(domain, timeout=8, allow_redirects=True)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            title = (soup.title.string if soup.title else '')[:60]
            links = soup.find_all('a', href=True)
            team_links = [a for a in links if any(kw in (a.get_text()+a.get('href','')).lower()
                         for kw in ['team','lawyer','people','律师','团队','合伙人','专业'])]
            if '律师' in title or 'law' in title.lower() or team_links:
                print(f"  {firm}: FOUND {domain} - {title}")
                for tl in team_links[:3]:
                    print(f"    Team: {tl.get_text(strip=True)[:30]} -> {tl.get('href','')[:60]}")
            else:
                print(f"  {firm}: HTTP200 but not law firm: {title}")
        else:
            print(f"  {firm}: {domain} -> HTTP {r.status_code}")
    except Exception as e:
        print(f"  {firm}: {domain} -> {str(e)[:60]}")
