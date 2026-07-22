import requests, re, json
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

print("=== lawtime.cn Guangzhou lawyer detail ===")
resp = requests.get('https://www.lawtime.cn/guangzhou/', headers=headers, timeout=15)
soup = BeautifulSoup(resp.text, 'html.parser')

# Look at .lawyer divs
print("--- .lawyer.bdb1 ---")
for i, div in enumerate(soup.select('.lawyer.bdb1')):
    print(f"\n  Lawyer block {i}:")
    print(f"  HTML: {str(div)[:500]}")
    for a in div.find_all('a', href=True):
        print(f"    Link: {a.get_text(strip=True)[:50]} -> {a['href'][:80]}")
    for img in div.find_all('img'):
        print(f"    Img: {img.get('src','')[:80]} alt={img.get('alt','')[:50]}")

# Look at lawyer-rank-list
print("\n--- .lawyer-rank-list ---")
for i, ul in enumerate(soup.select('.lawyer-rank-list')[:3]):
    print(f"\n  Rank list {i}:")
    for li in ul.find_all('li')[:3]:
        text = li.get_text(strip=True)[:150]
        print(f"    {text}")
        for a in li.find_all('a', href=True):
            print(f"      Link: {a.get_text(strip=True)[:50]} -> {a['href'][:80]}")

# Look at wl-recommon-list
print("\n--- .wl-recommon-list ---")
for i, div in enumerate(soup.select('.wl-recommon-list')[:2]):
    print(f"\n  Recommend list {i}:")
    for child in div.find_all(recursive=False)[:3]:
        text = child.get_text(strip=True)[:200]
        print(f"    {text}")
        for a in child.find_all('a', href=True):
            href = a.get('href', '')
            if 'lawyer' in href.lower() or 'law' in href.lower():
                print(f"      Lawyer link: {a.get_text(strip=True)[:50]} -> {href[:80]}")

# Let's also search for "天河" in the page
print("\n--- Searching for Tianhe ---")
tianhe_elems = soup.find_all(string=re.compile('天河'))
print(f"Found {len(tianhe_elems)} elements mentioning Tianhe")
for e in tianhe_elems[:5]:
    parent = e.parent
    if parent:
        print(f"  Context: {parent.get_text(strip=True)[:200]}")
        for a in parent.find_all('a', href=True):
            print(f"    Link: {a.get_text(strip=True)[:50]} -> {a['href'][:80]}")
