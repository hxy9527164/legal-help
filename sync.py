"""
一键同步脚本
用法: python sync.py "更新说明"
"""
import json, sys, time, subprocess
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).parent
MSG = sys.argv[1] if len(sys.argv) > 1 else '更新数据'

# 1. 重新生成JS数据文件
for jf, jsf, vn in [
    ('data/lawyers.json', 'data/lawyers-data.js', '__lawyersData'),
    ('data/templates.json', 'data/templates-data.js', '__templatesData'),
    ('data/knowledge-base.json', 'data/knowledge-base-data.js', '__knowledgeBaseData'),
]:
    with open(BASE / jf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(BASE / jsf, 'w', encoding='utf-8') as f:
        f.write(f'window.{vn} = ' + json.dumps(data, ensure_ascii=False, indent=2) + ';\n')
    print(f'  ✅ {jsf}')

# 2. 更新版本号
import re
version = time.strftime('%Y%m%d%H%M')
with open(BASE / 'index.html', 'r', encoding='utf-8') as f:
    html = f.read()
html = re.sub(r'\?v=\d+', f'?v={version}', html)
html = re.sub(r'var v="\d+"', f'var v="{version}"', html)
with open(BASE / 'index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'  OK 版本号: {version}')

# 3. Git 推送
import os
os.environ['PATH'] = r'C:\Git\bin;C:\Git\cmd;' + os.environ.get('PATH', '')
commands = [
    ['git', 'add', '-A'],
    ['git', 'commit', '-m', MSG],
    ['git', 'push'],
]
for cmd in commands:
    result = subprocess.run(cmd, cwd=str(BASE), capture_output=True, text=True)
    if result.returncode != 0 and 'nothing to commit' not in result.stdout + result.stderr:
        print(f'  ⚠️ {" ".join(cmd)}: {result.stderr[:100]}')

print(f'\n✅ 同步完成！等30秒后刷新页面即可看到更新。')
print(f'   链接: https://hxy9527164.github.io/legal-help/')
