"""
从新平台采集天河区律师数据
来源: 知乎、百度、小红书公开搜索
"""
import json, re, time, random
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

def search_zhihu_tianhe():
    """知乎搜索天河区律师推荐"""
    lawyers = []
    print('\n--- 知乎搜索 ---')
    try:
        url = 'https://www.zhihu.com/search?type=content&q=广州天河区律师推荐'
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text()
            # Extract lawyer/firm names
            firm_patterns = re.findall(r'(广东.{2,20}(律师事务所|律所))', text)
            for firm, _ in firm_patterns:
                if firm not in [l.get('firm','') for l in lawyers]:
                    lawyers.append({'firm': firm, 'source': 'zhihu.com', 'city': '广州', 'province': '广东', 'district': '天河区'})
            print(f'  Found {len(lawyers)} firm mentions')
    except Exception as e:
        print(f'  Error: {e}')
    return lawyers

def search_baidu_tianhe():
    """百度搜索天河区律师"""
    lawyers = []
    print('\n--- 百度搜索 ---')
    try:
        url = 'https://www.baidu.com/s?wd=广州天河区律师+律师事务所'
        resp = session.get(url, timeout=15, headers={**HEADERS, 'Accept': 'text/html'})
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text()
            firm_patterns = re.findall(r'(广东.{2,20}(律师事务所|律所))', text)
            seen = set()
            for firm, _ in firm_patterns:
                if firm not in seen:
                    seen.add(firm)
                    lawyers.append({'firm': firm, 'source': 'baidu.com', 'city': '广州', 'province': '广东', 'district': '天河区'})
            print(f'  Found {len(lawyers)} firm mentions')
    except Exception as e:
        print(f'  Error: {e}')
    return lawyers

def search_xiaohongshu_tianhe():
    """小红书搜索天河区律师关键词"""
    lawyers = []
    print('\n--- 小红书搜索 ---')
    try:
        # 小红书搜索API（公开接口）
        url = 'https://www.xiaohongshu.com/search_result?keyword=广州天河区律师&type=1'
        resp = session.get(url, timeout=15, allow_redirects=True,
                          headers={**HEADERS, 'Referer': 'https://www.xiaohongshu.com/'})
        if resp.status_code == 200:
            text = resp.text
            # Look for lawyer names and firms in page data
            # 小红书 often has JSON data in script tags
            firm_patterns = re.findall(r'(广东.{2,20}(律师事务所|律所|法律))', text)
            name_patterns = re.findall(r'(律师.{2,4})', text)
            seen = set()
            for firm, _ in firm_patterns:
                if firm not in seen and '律师' in firm:
                    seen.add(firm)
                    lawyers.append({'firm': firm, 'source': 'xiaohongshu.com', 'city': '广州', 'province': '广东', 'district': '天河区'})
            print(f'  HTTP {resp.status_code}, found {len(lawyers)} firm mentions')
        else:
            print(f'  HTTP {resp.status_code}')
    except Exception as e:
        print(f'  Error: {str(e)[:100]}')
    return lawyers

def main():
    print('=' * 60)
    print('  新平台天河区律师采集')
    print('=' * 60)

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        existing = json.load(f)
    existing_firms = {l.get('firm','') for l in existing}
    print(f'现有律师: {len(existing)} | 现有律所: {len(existing_firms)}')

    all_new = []
    for func in [search_zhihu_tianhe, search_baidu_tianhe, search_xiaohongshu_tianhe]:
        try:
            results = func()
            all_new.extend(results)
            time.sleep(1)
        except Exception as e:
            print(f'  Source error: {e}')

    # Merge new firms
    added = 0
    for item in all_new:
        firm = item.get('firm', '')
        if firm and firm not in existing_firms and '律师' in firm:
            # Create a placeholder lawyer entry for this firm
            new_l = {
                'id': len(existing) + 1,
                'name': firm.replace('律师事务所','').replace('广东',''),
                'firm': firm,
                'city': '广州', 'province': '广东', 'district': '天河区',
                'fields': ['民商事'], 'experience': 0,
                'education': '暂无学历信息', 'cases': '暂无案例信息',
                'contact': '暂无联系方式', 'photo': '',
                'source': item.get('source', 'web'), 'position': '',
                'license': '', 'profile_url': '',
            }
            existing.append(new_l)
            existing_firms.add(firm)
            added += 1

    if added > 0:
        for i, l in enumerate(existing): l['id'] = i + 1
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_FILE.parent / 'lawyers-data.js', 'w', encoding='utf-8') as f:
            f.write('window.__lawyersData = ' + json.dumps(existing, ensure_ascii=False, indent=2) + ';\n')

    print(f'\n{"=" * 60}')
    print(f'  新律所入库: {added} | 总律师: {len(existing)}')
    print(f'{"=" * 60}')

if __name__ == '__main__':
    main()
