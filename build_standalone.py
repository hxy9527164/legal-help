"""
打包法律自助助手为单个独立HTML文件
可以微信发送/邮件发送/USB拷贝，双击即用
"""
import re
from pathlib import Path

BASE = Path(__file__).parent

# 1. 读取 HTML 模板
with open(BASE / 'index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 2. 内嵌 CSS
with open(BASE / 'css' / 'style.css', 'r', encoding='utf-8') as f:
    css = f.read()
html = html.replace(
    '<link rel="stylesheet" href="css/style.css">',
    '<style>\n' + css + '\n</style>'
)

# 3. 内嵌数据文件（移除script标签引用，改为内嵌）
data_files = [
    ('data/knowledge-base-data.js', 'knowledge-base-data.js'),
    ('data/lawyers-data.js', 'lawyers-data.js'),
    ('data/templates-data.js', 'templates-data.js'),
]

for src_path, script_name in data_files:
    with open(BASE / src_path, 'r', encoding='utf-8') as f:
        data_js = f.read()
    # Replace the external script tag with inline script
    pattern = f'<script src="{src_path}"></script>'
    replacement = f'<script>\n{data_js}\n</script>'
    html = html.replace(pattern, replacement)

# 4. 内嵌 JS 文件
js_files = [
    'js/main.js',
    'js/wizard.js',
    'js/lawyer-search.js',
]

for js_path in js_files:
    with open(BASE / js_path, 'r', encoding='utf-8') as f:
        js_code = f.read()
    # Replace external script tag with inline script
    pattern = f'<script src="{js_path}"></script>'
    replacement = f'<script>\n{js_code}\n</script>'
    html = html.replace(pattern, replacement)

# 5. 删除防缓存 meta（独立文件不需要）
html = html.replace('<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">\n    ', '')
html = html.replace('<meta http-equiv="Pragma" content="no-cache">\n    ', '')
html = html.replace('<meta http-equiv="Expires" content="0">\n    ', '')

# 6. 输出
output_path = BASE / '法律自助助手.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = len(html.encode('utf-8')) / 1024
print(f'✅ 打包完成: {output_path}')
print(f'   文件大小: {size_kb:.0f} KB')
print(f'   可直接通过微信/邮件发送，双击即可打开')
print(f'   所有CSS/JS/数据已内嵌，无需网络')

# 7. 同时复制一份到桌面
import shutil
desktop_path = Path.home() / 'Desktop' / '法律自助助手.html'
shutil.copy(output_path, desktop_path)
print(f'   已复制到桌面: {desktop_path}')
