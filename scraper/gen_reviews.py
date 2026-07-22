"""
为所有律师生成文字综合评价
"""
import json, random, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

OUTPUT = Path(__file__).parent.parent / 'data' / 'lawyers.json'
random.seed(42)

def gen_review(lawyer):
    name = lawyer['name']
    exp = lawyer.get('experience', 0)
    edu = lawyer.get('education', '')
    fields = lawyer.get('fields', [])
    cases = lawyer.get('cases', '')
    firm = lawyer.get('firm', '')
    city = lawyer.get('city', '')
    position = lawyer.get('position', '')

    parts = []

    # 执业经验评价
    if exp >= 20:
        parts.append(random.choice([
            f'{name}律师执业超过{exp}年，是业内资深法律专家，',
            f'拥有{exp}年丰富执业经验的{name}律师，',
        ]))
    elif exp >= 10:
        parts.append(random.choice([
            f'{name}律师执业{exp}年，已成长为业务骨干，',
            f'执业{exp}年的{name}律师具备扎实的实战经验，',
        ]))
    elif exp >= 5:
        parts.append(random.choice([
            f'{name}律师执业{exp}年，正处于职业上升期，',
        ]))
    elif exp > 0:
        parts.append(random.choice([
            f'{name}律师执业{exp}年，充满干劲的新锐律师，',
        ]))
    else:
        parts.append(f'{name}律师，')

    # 学历评价
    if '博士' in edu:
        parts.append(random.choice(['法学博士学历背景为其提供了深厚的理论功底，','拥有博士学位的他/她在法律理论研究方面有独特优势，']))
    elif '硕士' in edu:
        parts.append(random.choice(['法学硕士学历为其奠定了扎实的专业基础，','硕士阶段的深造使其具备出色的法律分析能力，']))
    elif '学士' in edu:
        parts.append(random.choice(['法学本科教育为其执业打下了良好基础，',]))

    # 擅长领域评价
    if len(fields) >= 3:
        main_fields = '、'.join(fields[:3])
        parts.append(f'擅长{main_fields}等多个领域，')
    elif len(fields) > 0:
        parts.append(f'专注于{fields[0]}领域，')

    # 案例/经验评价
    if exp >= 15 and len(fields) >= 3:
        parts.append(random.choice([
            '能够为复杂案件提供全方位的法律解决方案。',
            '处理过大量疑难案件，实战经验丰富。',
            '在多类型案件处理中展现出全面的法律素养。',
        ]))
    elif exp >= 8:
        parts.append(random.choice([
            '已积累丰富的办案经验，能够独立处理各类案件。',
            '在执业过程中形成了自己独特的办案风格。',
            '对案件细节把控到位，善于发现关键突破点。',
        ]))
    elif exp > 0:
        parts.append(random.choice([
            '工作认真负责，对每个案件都投入十足精力。',
            '虽然执业年限不长，但办案态度严谨细致。',
        ]))
    else:
        parts.append('专业能力和服务态度值得信赖。')

    # 服务态度评价
    service = lawyer.get('service_count', 0)
    if service >= 100:
        parts.append(random.choice([' 已累计服务大量客户，口碑良好。',' 丰富的服务经验使其能准确把握客户需求。']))
    elif service >= 20:
        parts.append(random.choice([' 服务过多位客户，积累了良好的客户口碑。',' 客户反馈积极，服务态度认真负责。']))

    review = ''.join(parts)

    # 律所背书
    if '律师' in firm and firm != '个体律师' and exp >= 8:
        suffix = random.choice([
            f' 执业于{firm}，依托律所平台资源，能为客户提供更有力的法律支持。',
            f' 所在的{firm}是{city}知名律所，团队协作能力强。',
        ])
        if random.random() > 0.5:
            review += suffix

    return review

def main():
    with open(OUTPUT, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for l in data:
        l['review'] = gen_review(l)

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(OUTPUT.parent / 'lawyers-data.js', 'w', encoding='utf-8') as f:
        f.write('window.__lawyersData = ' + json.dumps(data, ensure_ascii=False, indent=2) + ';\n')

    # Sample
    print(f'Generated reviews for {len(data)} lawyers')
    for l in data[:3]:
        print(f'\n{l["name"]} ({l["city"]} {l.get("district","")}):')
        print(f'  {l["review"][:120]}...')

if __name__ == '__main__':
    main()
