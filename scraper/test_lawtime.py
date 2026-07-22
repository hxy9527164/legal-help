import requests, re
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

print("=== lawtime.cn Guangzhou page ===")
resp = requests.get('https://www.lawtime.cn/guangzhou/', headers=headers, timeout=15)
soup = BeautifulSoup(resp.text, 'html.parser')

# Find all links
print(f"Total links: {len(soup.find_all('a'))}")
print(f"Total divs: {len(soup.find_all('div'))}")

# Try various selectors
selectors = [
    '.lawyer-list li', '.lawyer_item', '.lawyer-card',
    '.l-list li', '.search-result-item', '.lawyer-info',
    'article', '.card', '.list-item', '.item',
    'li h3 a', '.title a',
]

for sel in selectors:
    items = soup.select(sel)
    if items and len(items) > 3:
        print(f"\nSelector: {sel} -> {len(items)} items")
        for i, item in enumerate(items[:3]):
            text = item.get_text(strip=True)[:150]
            print(f"  [{i}] {text}")
            for a in item.find_all('a', href=True):
                href = a.get('href', '')[:80]
                txt = a.get_text(strip=True)[:50]
                print(f"    Link: {txt} -> {href}")

# Also look at the page structure
print("\n=== Page structure ===")
for tag in soup.find_all(['div', 'ul', 'section'], class_=True):
    cls = ' '.join(tag.get('class', []))
    if 'lawyer' in cls.lower() or 'list' in cls.lower():
        children = len(tag.find_all(recursive=False))
        if children > 2:
            print(f"  <{tag.name} class='{cls}'> -> {children} direct children")

# Look for script data
print("\n=== Script data patterns ===")
for script in soup.find_all('script'):
    src = script.get('src', '')
    text = script.get_text()[:200]
    if 'lawyer' in text.lower() or 'lawyer' in src.lower():
        print(f"  src={src[:80]}")
        print(f"  text={text[:150]}")
