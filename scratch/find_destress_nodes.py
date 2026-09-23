import json

with open('data/rdso_canonical_kg.json', 'r', encoding='utf-8') as f:
    kg = json.load(f)

nodes = kg.get('entities', [])
destress_nodes = []
for n in nodes:
    text = f"{n.get('id', '')} {n.get('label', '')} {n.get('name', '')} {n.get('desc', '')} {json.dumps(n.get('specs', {}))}".lower()
    if 'destress' in text:
        destress_nodes.append(n)

print(f"Found {len(destress_nodes)} nodes with 'destress':")
for n in destress_nodes[:15]:
    print(f"- [{n.get('type')}] {n.get('id')}: {n.get('label')}")
    if n.get('specs'):
        print(f"    specs: {list(n.get('specs', {}).keys())}")
    if n.get('desc'):
        print(f"    desc: {n.get('desc')[:120]}")
