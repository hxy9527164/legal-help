"""
从 lawtime.cn 和 etrlawfirm.com 采集律师照片、联系方式、详细资料
"""
import json, re, time, random, sys
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


def scrape_lawtime_profile(url):
    """从找法网律师个人页提取完整信息，包含照片"""
    try:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()

        info = {
            'name': '', 'firm': '未知律所', 'fields': ['民商事'],
            'experience': 0, 'education': '暂无学历信息',
            'city': '广州', 'province': '广东', 'district': '',
            'cases': '暂无案例信息', 'contact': '暂无联系方式',
            'photo': '', 'license': '', 'position': '',
            'languages': '', 'awards': '', 'service_count': 0,
            'consultation_count': 0, 'source': 'lawtime.cn',
            'profile_url': url,
        }

        # Photo - look for lawyer avatar/image
        for sel in ['.lawyer-img-box img', '.lawyer-photo img', '.avatar img', '.lawyer-avatar img', '.photo img', 'img.cover-img']:
            img_el = soup.select_one(sel)
            if img_el:
                src = img_el.get('src', '') or img_el.get('data-src', '')
                if src and 'lawyer' in src.lower() or 'photo' in src.lower() or 'avatar' in src.lower():
                    info['photo'] = 'https:' + src if src.startswith('//') else src
                    break

        # Also try finding any image that looks like a photo
        if not info['photo']:
            for img in soup.find_all('img', src=True):
                src = img['src']
                alt = img.get('alt', '')
                if any(kw in (src + alt).lower() for kw in ['photo', 'avatar', 'lawyer', 'portrait']):
                    info['photo'] = 'https:' + src if src.startswith('//') else src
                    break

        # Name
        for sel in ['.lawyer-name', '.name', 'h1', '.username', '.profile-name']:
            el = soup.select_one(sel)
            if el:
                name_text = el.get_text(strip=True)
                info['name'] = re.sub(r'(律师|主任|合伙人|实习律师).*$', '', name_text).strip()
                if len(info['name']) >= 2:
                    break

        # Position/title
        pos_match = re.search(r'(高级合伙人|合伙人|主任律师|副主任|执业律师|实习律师|律师助理|创始合伙人|首席合伙人)', text)
        if pos_match:
            info['position'] = pos_match.group(1)

        # Firm
        for sel in ['.lawfirm-name', '.firm-name', '.firm', '.company-name', '.law-firm']:
            el = soup.select_one(sel)
            if el:
                info['firm'] = el.get_text(strip=True)
                break
        if info['firm'] == '未知律所':
            fm = re.search(r'([广北上深杭成渝].{2,30}(律师.{2,12}所|律所|法律))', text)
            if fm: info['firm'] = fm.group(1)

        # License number
        lic_match = re.search(r'14401\d{11}|\d{17}', text)
        if lic_match: info['license'] = lic_match.group()

        # District
        dm = re.search(r'(天河区|越秀区|海珠区|荔湾区|白云区|黄埔区|番禺区|花都区|南沙区|增城区|从化区)', text)
        if dm: info['district'] = dm.group(1)

        # Fields/specialty
        for sel in ['.specialty-list', '.goodat-list', '.skill-tags', '.tag-list', '.lawyer-tags']:
            el = soup.select_one(sel)
            if el:
                ft = el.get_text(strip=True)
                info['fields'] = [f.strip() for f in re.split(r'[、，/\s]+', ft) if len(f.strip()) > 1][:8]
                break
        if len(info['fields']) <= 1:
            # Try finding from text
            field_section = re.search(r'(?:擅长|专业|领域|业务|专长)[：:]\s*([^。\n]{3,200})', text)
            if field_section:
                info['fields'] = [f.strip() for f in re.split(r'[、，/\s]+', field_section.group(1)) if len(f.strip()) > 1][:8]

        # Experience
        for m in re.finditer(r'(?:执业|从业|工作)[^\d]*(\d+)\s*年|(\d+)\s*年\s*(?:执业|从业|律师)', text):
            for g in m.groups():
                if g and 1 <= int(g) <= 50:
                    info['experience'] = int(g)
                    break
            if info['experience'] > 0:
                break

        # Education
        edu_patterns = [
            r'(中山大学|华南理工|华南师范|暨南大学|广东外语|广东财经|广州大学|西南政法|中国政法|武汉大学|中南财经|华东政法|北京大学|中国人民大学|吉林大学|西北政法|中南大学|厦门大学|浙江大学|复旦大学|南京大学|深圳大学)\s*(法学)?\s*(博士|硕士|学士|研究生|本科|MBA|EMBA)',
            r'(法学|法律)\s*(博士|硕士|学士|研究生|本科)',
        ]
        for pat in edu_patterns:
            em = re.search(pat, text)
            if em:
                info['education'] = em.group()
                break

        # Cases
        case_section = re.search(r'(?:经典案例|代表案例|典型案例|成功案例|代理案件)[：:]*\s*([^。\n]{10,300})', text)
        if case_section:
            info['cases'] = case_section.group(1)[:300]

        # Contact
        phone_match = re.search(r'(1[3-9]\d{9})', text)
        if phone_match:
            p = phone_match.group(1)
            info['contact'] = p[:3] + '****' + p[-4:]
        else:
            # Look for phone/fax pattern
            tel_match = re.search(r'(?:电话|手机|联系电话|咨询电话|Tel|Phone)[：:]\s*([\d\-]{7,20})', text)
            if tel_match:
                info['contact'] = tel_match.group(1)

        # Service count
        sc = re.search(r'(?:已服务|服务次数|咨询人数)[^\d]*(\d+)\s*次', text)
        if sc: info['service_count'] = int(sc.group(1))

        # Consultation count
        cc = re.search(r'(?:解答|回复|咨询)[^\d]*(\d+)\s*(?:次|条)', text)
        if cc: info['consultation_count'] = int(cc.group(1))

        return info
    except Exception as e:
        return None


def scrape_etr_profile(url, firm_name):
    """从广信君达官网律师个人页提取详细信息"""
    try:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()

        info = {
            'name': '', 'firm': firm_name, 'fields': ['民商事'],
            'experience': 0, 'education': '暂无学历信息',
            'city': '广州', 'province': '广东', 'district': '天河区',
            'cases': '暂无案例信息', 'contact': '暂无联系方式',
            'photo': '', 'license': '', 'position': '',
            'languages': '', 'awards': '',
            'source': 'etrlawfirm.com', 'profile_url': url,
        }

        # Photo
        for img in soup.find_all('img', src=True):
            src = img['src']
            if any(kw in src.lower() for kw in ['photo', 'head', 'avatar', 'portrait', 'pic', 'image']):
                info['photo'] = src if src.startswith('http') else 'https://www.etrlawfirm.com' + src
                break

        # Name
        for sel in ['.name', 'h1', '.lawyer-name', '.title', '.member-name']:
            el = soup.select_one(sel)
            if el:
                name_text = el.get_text(strip=True)
                info['name'] = re.sub(r'(律师|合伙人|主任|博士|教授).*$', '', name_text).strip()
                if len(info['name']) >= 2:
                    break

        # Position
        pos_match = re.search(r'(高级合伙人|合伙人|主任|副主任|执业律师|实习律师|律师|顾问)', text)
        if pos_match:
            info['position'] = pos_match.group(1)

        # Experience years
        for m in re.finditer(r'(\d+)\s*年', text):
            y = int(m.group(1))
            if 1 <= y <= 50:
                info['experience'] = y
                break

        # Fields
        field_section = re.search(r'(?:业务领域|专业领域|擅长|执业领域|服务领域)[：:]*\s*([^。\n]{5,300})', text)
        if field_section:
            info['fields'] = [f.strip() for f in re.split(r'[、，/\s]+', field_section.group(1)) if len(f.strip()) > 1][:8]

        # Education
        edu_match = re.search(r'(中山大学|华南理工|华南师范|暨南大学|广东外语|广东财经|广州大学|西南政法|中国政法|武汉大学|中南财经|华东政法|北京大学|中国人民大学|吉林大学|深圳大学)[^。\n]{0,20}(博士|硕士|学士|研究生|本科)', text)
        if edu_match:
            info['education'] = edu_match.group()

        # Cases/experience
        case_section = re.search(r'(?:代表业绩|经典案例|项目经验|执业经验|工作经历)[：:]*\s*([^。\n]{10,300})', text)
        if case_section:
            info['cases'] = case_section.group(1)[:300]

        return info
    except Exception as e:
        return None


def collect_lawtime_lawyers():
    """从找法网广州站收集更多律师"""
    lawyers = []
    print('\n=== Collecting from lawtime.cn Guangzhou ===')

    # 广州律师页面 - we know this works
    try:
        resp = session.get('https://www.lawtime.cn/guangzhou/', timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Collect all lawyer profile URLs
        profile_urls = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/lawyer/lll' in href:
                profile_urls.add(href)

        # Also from rank lists
        for ul in soup.select('.lawyer-rank-list'):
            for a in ul.find_all('a', href=True):
                href = a['href']
                if '/lawyer/lll' in href:
                    profile_urls.add(href)

        # Also from lawyer blocks
        for div in soup.select('.lawyer.bdb1'):
            for a in div.find_all('a', href=True):
                href = a['href']
                if '/lawyer/lll' in href:
                    profile_urls.add(href)

        print(f'  Found {len(profile_urls)} unique profiles')

        for i, url in enumerate(sorted(profile_urls)):
            print(f'  [{i+1}/{len(profile_urls)}] {url[-30:]}', end=' ')
            details = scrape_lawtime_profile(url)
            if details and details['name']:
                lawyers.append(details)
                district = details.get('district', '?')
                has_photo = 'photo' if details.get('photo') else 'no-photo'
                print(f'-> {details["name"]} [{district}] [{has_photo}]')
            else:
                print('-> skip')
            time.sleep(random.uniform(0.8, 1.5))

    except Exception as e:
        print(f'  Error: {e}')

    return lawyers


def collect_etr_lawyers():
    """从广信君达官网收集律师详情"""
    lawyers = []
    print('\n=== Collecting from etrlawfirm.com ===')

    # We already know the URLs - let's check our existing database for ETR lawyers with profile URLs
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    etr_lawyers = [l for l in existing if l.get('profile_url', '').startswith('https://www.etrlawfirm.com')]
    print(f'  Found {len(etr_lawyers)} ETR lawyers with profile URLs in DB')

    for i, l in enumerate(etr_lawyers[:50]):
        url = l.get('profile_url', '')
        if not url:
            continue
        print(f'  [{i+1}/{min(len(etr_lawyers), 50)}] {l["name"]}', end=' ')
        details = scrape_etr_profile(url, l.get('firm', ''))
        if details:
            # Keep existing fields that are better
            if not details['name']: details['name'] = l['name']
            if not details['photo']: details['photo'] = l.get('photo', '')
            details['id'] = l.get('id', 0)
            lawyers.append(details)
            has_photo = 'photo' if details.get('photo') else 'no-photo'
            print(f'-> OK [{has_photo}]')
        else:
            print('-> skip')
        time.sleep(random.uniform(0.5, 1.0))

    return lawyers


def merge_lawyers(existing, new_data):
    """合并：更新已有律师的详细信息，新增不存在的律师"""
    # Index existing by (name, firm)
    existing_map = {}
    for i, l in enumerate(existing):
        key = (l['name'], l.get('firm', ''))
        existing_map[key] = i

    added = 0
    updated = 0
    for nl in new_data:
        if not nl.get('name'):
            continue
        key = (nl['name'], nl.get('firm', ''))
        if key in existing_map:
            # Update existing with new details, but don't overwrite better existing data
            idx = existing_map[key]
            old = existing[idx]
            for k, v in nl.items():
                if v and (k not in old or not old[k] or old[k] == '暂无案例信息' or old[k] == '暂无联系方式' or old[k] == '暂无学历信息'):
                    if v and v != '暂无案例信息' and v != '暂无联系方式' and v != '暂无学历信息':
                        old[k] = v
            updated += 1
        else:
            # Add new
            nl['id'] = len(existing) + 1
            existing.append(nl)
            existing_map[key] = len(existing) - 1
            added += 1

    # Re-ID
    for i, l in enumerate(existing):
        l['id'] = i + 1

    return existing, added, updated


def main():
    print('=' * 60)
    print('  律师详细资料采集（照片/联系方式/案件...）')
    print('=' * 60)

    # Load existing
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    print(f'\n现有律师: {len(existing)}')

    all_new = []

    # Source 1: lawtime.cn
    lt_lawyers = collect_lawtime_lawyers()
    all_new.extend(lt_lawyers)
    print(f'\n  lawtime.cn: {len(lt_lawyers)} lawyers')

    # Source 2: etrlawfirm.com
    etr_lawyers = collect_etr_lawyers()
    all_new.extend(etr_lawyers)
    print(f'  etrlawfirm.com: {len(etr_lawyers)} lawyers')

    # Merge
    merged, added, updated = merge_lawyers(existing, all_new)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    with_photo = len([l for l in merged if l.get('photo', '').startswith('http')])
    with_contact = len([l for l in merged if l.get('contact', '') not in ('暂无联系方式', '') and 'XXXX' not in l.get('contact', '')])
    tianhe = len([l for l in merged if l.get('district') == '天河区'])

    print(f'\n{"=" * 60}')
    print(f'  Results:')
    print(f'    New lawyers: {added}')
    print(f'    Updated: {updated}')
    print(f'    Total: {len(merged)}')
    print(f'    With photos: {with_photo}')
    print(f'    With contact: {with_contact}')
    print(f'    Tianhe district: {tianhe}')
    print(f'{"=" * 60}')


if __name__ == '__main__':
    main()
