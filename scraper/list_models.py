import requests
r = requests.get(
    'https://api.siliconflow.cn/v1/models',
    headers={'Authorization': 'Bearer sk-wbtzxngfywxeetfscvfqfjzlbdaiptwliceyqgnhmrslvlqd'},
    timeout=15
)
data = r.json()
models = data.get('data', [])
print(f"Total models: {len(models)}")

# Find vision models
vision_keywords = ['vl', 'vision', 'visual', 'video', 'glm-4v', 'internvl', 'qwenvl', 'qwen-vl', 'multimodal']
vision_models = []
for m in models:
    mid = m['id']
    if any(kw in mid.lower() for kw in vision_keywords):
        vision_models.append(mid)

print(f"\nVision models ({len(vision_models)}):")
for vm in sorted(vision_models):
    print(f"  {vm}")

# Also show all model IDs if no vision models
if not vision_models:
    print("\nAll available models:")
    for m in sorted(models, key=lambda x: x['id'])[:50]:
        print(f"  {m['id']}")
