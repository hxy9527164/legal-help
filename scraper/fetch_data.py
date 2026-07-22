"""
法律自助助手 - 公开律师数据采集脚本
=====================================
功能：从公开渠道采集律师信息，自动更新 lawyers.json

使用方式：
  1. 安装依赖：pip install requests beautifulsoup4
  2. 运行脚本：python fetch_data.py
  3. 脚本会自动更新 ../data/lawyers.json

数据来源（均为公开信息）：
  - 12348中国法律服务网
  - 各地律师协会网站
  - 中国法律服务网（公开律师查询）

免责声明：
  本脚本仅采集公开可访问的律师信息，用于个人学习和参考。
  采集的数据来源于各官方网站的公开信息展示页面。
  请遵守各网站的 robots.txt 和使用条款。
  采集频率已做限制，避免对目标服务器造成负担。
"""

import json
import os
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# 输出文件路径
OUTPUT_FILE = Path(__file__).parent.parent / 'data' / 'lawyers.json'

# 请求头（模拟浏览器访问）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# 请求间隔（秒），避免对服务器造成压力
REQUEST_DELAY = 2


def fetch_12348_lawyers(page=1):
    """
    从 12348 中国法律服务网采集律师信息
    网址: http://www.12348.gov.cn/#/home
    采集公开的律师查询结果
    """
    lawyers = []
    try:
        # 12348 法网律师查询 API（公开接口）
        url = "http://www.12348.gov.cn/api/lawyer/search"
        params = {
            'pageNum': page,
            'pageSize': 20,
            # 可根据需要修改地区筛选
            # 'areaCode': '110000',  # 北京
        }
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get('code') == 200 and 'data' in data:
            for item in data['data'].get('list', []):
                lawyer = {
                    "id": len(lawyers) + 100,  # 临时ID，之后会重新编号
                    "name": item.get('name', '未知'),
                    "firm": item.get('lawFirmName', '未知律所'),
                    "city": item.get('cityName', '未知'),
                    "province": item.get('provinceName', '未知'),
                    "fields": item.get('specialty', '民商事').split('、'),
                    "experience": item.get('practiceYears', 0),
                    "cases": item.get('typicalCases', '暂无案例信息'),
                    "contact": item.get('contactInfo', '暂无联系方式'),
                    "education": item.get('education', '暂无学历信息')
                }
                lawyers.append(lawyer)

            print(f'  ✅ 12348法网第{page}页获取到 {len(lawyers)} 条律师信息')

    except requests.exceptions.RequestException as e:
        print(f'  ⚠️ 12348法网请求失败（可能需VPN或API已变更）: {e}')
    except Exception as e:
        print(f'  ⚠️ 12348法网解析失败: {e}')

    return lawyers


def fetch_local_bar_association(city_code='110000'):
    """
    从地方律师协会采集律师信息
    示例：北京律师协会
    各地律协网站结构不同，这里以北京为例
    """
    lawyers = []
    try:
        # 北京律师协会 - 律师查询页面
        url = f'http://www.beijinglawyers.org.cn/search/lawyer'
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 注意：各律协网站HTML结构不同，以下为示例选择器，需根据实际情况调整
        lawyer_items = soup.select('.lawyer-list .lawyer-item')
        for item in lawyer_items:
            name_el = item.select_one('.lawyer-name')
            firm_el = item.select_one('.lawyer-firm')
            specialty_el = item.select_one('.lawyer-specialty')

            if name_el:
                lawyer = {
                    "id": len(lawyers) + 200,
                    "name": name_el.get_text(strip=True),
                    "firm": firm_el.get_text(strip=True) if firm_el else '未知律所',
                    "city": "北京",
                    "province": "北京",
                    "fields": [specialty_el.get_text(strip=True)] if specialty_el else ['民商事'],
                    "experience": 0,
                    "cases": '暂无案例信息',
                    "contact": '暂无联系方式',
                    "education": '暂无学历信息'
                }
                lawyers.append(lawyer)

        if lawyers:
            print(f'  ✅ 律协网站获取到 {len(lawyers)} 条律师信息')
        else:
            print(f'  ℹ️ 律协网站未获取到数据（可能需要调整选择器或网站已更新）')

    except requests.exceptions.RequestException as e:
        print(f'  ⚠️ 律协网站请求失败: {e}')
    except Exception as e:
        print(f'  ⚠️ 律协网站解析失败: {e}')

    return lawyers


def merge_lawyers(existing, new_data):
    """合并新旧数据：以姓名为去重标准，保留已有数据的完整性"""
    existing_names = {l['name'] for l in existing}

    for lawyer in new_data:
        if lawyer['name'] not in existing_names and lawyer['name'] != '未知':
            existing.append(lawyer)
            existing_names.add(lawyer['name'])

    # 重新编号
    for i, lawyer in enumerate(existing):
        lawyer['id'] = i + 1

    return existing


def main():
    print('=' * 60)
    print('  法律自助助手 - 律师数据采集')
    print('  采集公开律师信息，更新本地数据文件')
    print('=' * 60)
    print()

    # 加载现有数据
    existing_lawyers = []
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_lawyers = json.load(f)
            print(f'📂 已加载现有律师数据：{len(existing_lawyers)} 条\n')
        except Exception as e:
            print(f'⚠️ 读取现有数据失败: {e}\n')

    new_lawyers = []

    # 1. 从 12348 法网采集（尝试前3页）
    print('🔍 [1/2] 采集 12348 中国法律服务网...')

    # 注意：12348 API 可能需要特定的认证或已被限制。
    # 如果 API 不可用，脚本不会报错，会继续执行其他数据源。
    # 你可以搜索 "12348 律师查询 API" 了解最新的接口地址。
    for page in range(1, 4):
        print(f'  正在获取第 {page} 页...')
        lawyers = fetch_12348_lawyers(page)
        new_lawyers.extend(lawyers)
        if lawyers:
            time.sleep(REQUEST_DELAY)
        else:
            print(f'  第 {page} 页无数据，停止翻页')
            break

    # 2. 从地方律协采集（可根据需要添加更多城市）
    print('\n🔍 [2/2] 采集地方律师协会网站...')
    # 可以扩展更多城市的律协网站
    cities = [
        ('110000', '北京'),
        # ('310000', '上海'),
        # ('440100', '广州'),
        # ('440300', '深圳'),
        # 根据你的需求取消注释以上城市
    ]

    for city_code, city_name in cities:
        print(f'  正在获取 {city_name}...')
        lawyers = fetch_local_bar_association(city_code)
        new_lawyers.extend(lawyers)
        time.sleep(REQUEST_DELAY)

    # 合并数据
    print(f'\n📊 新采集到 {len(new_lawyers)} 条律师信息')
    merged = merge_lawyers(existing_lawyers, new_lawyers)
    added = len(merged) - len(existing_lawyers)
    print(f'📊 合并后共 {len(merged)} 条（新增 {added} 条）')

    # 保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f'\n✅ 数据已保存至: {OUTPUT_FILE}')
    print(f'   刷新网站页面即可看到更新后的律师数据。\n')

    # 提示
    if added == 0:
        print('💡 提示：公开数据接口可能因政策调整而变化。')
        print('   如果自动采集未获取到新数据，你可以：')
        print('   1. 手动搜索 "12348 律师查询API" 了解最新接口')
        print('   2. 手动编辑 data/lawyers.json 添加律师信息')
        print('   3. 从各地律协网站手动复制律师信息\n')


if __name__ == '__main__':
    main()
