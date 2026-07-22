"""
使用硅基流动视觉模型分析网站截图中的律师数据板块问题
"""
import json, base64, requests

# API配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-wbtzxngfywxeetfscvfqfjzlbdaiptwliceyqgnhmrslvlqd"
MODEL = "Qwen/Qwen3-VL-8B-Instruct"

# 读取base64图片
with open("scraper/screenshot_b64.txt", "r") as f:
    img_b64 = f.read()

print(f"Base64 length: {len(img_b64)}")

# 构建请求
payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_b64}"
                    }
                },
                {
                    "type": "text",
                    "text": """请仔细分析这张法律自助网站"查找律师"板块的截图。

重点分析：
1. 页面上显示的具体错误信息是什么？（完整复制错误文字）
2. 律师卡片是否显示了？显示了多少条？卡片上的信息是否完整（姓名、律所、领域标签、案例、联系方式、学历、已验证标签）？
3. 如果有错误，错误的根本原因是什么？
4. 筛选下拉框和搜索框是否正常显示？
5. 搜索结果计数显示了什么？
6. "已验证"标签和学历信息是否正常显示？
7. 整体布局有没有排版混乱的问题？

请非常具体地描述你看到的内容，包括任何错误文字、UI bug、排版问题。用中文回答。"""
                }
            ]
        }
    ],
    "max_tokens": 2048,
    "temperature": 0.3,
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

print("Calling SiliconFlow API...")
resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)

print(f"HTTP {resp.status_code}")

if resp.status_code == 200:
    result = resp.json()
    content = result["choices"][0]["message"]["content"]
    print("\n" + "=" * 60)
    print("视觉模型分析结果：")
    print("=" * 60)
    print(content)
else:
    print(f"Error: {resp.text[:500]}")
