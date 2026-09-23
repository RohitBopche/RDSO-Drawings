import json

with open('data/rdso_canonical_kg.json', 'r', encoding='utf-8') as f:
    kg = json.load(f)

nodes = kg.get('entities', [])
query = "destressing temperature"
q = query.lower()
tokens = q.split()

scored = []
for n in nodes:
    nid = n.get('id', '').lower()
    label = n.get('label', '').lower()
    desc = n.get('desc', '').lower()
    specs_str = json.dumps(n.get('specs', {})).lower()
    ntype = n.get('type', '').upper()
    domain = n.get('domain', '').lower()
    
    score = 0
    # Current rankSearchResults logic
    if q == nid: score += 1000
    if q in nid: score += 500
    if label.startswith(q): score += 400
    elif q in label: score += 250
    
    isDrawingQuery = any(k in q for k in ['6155', '6154', '6216', '6280', '6275', 'drg', 'drawing', 't-'])
    if ntype == 'DRAWING' and isDrawingQuery: score += 300
    elif ntype == 'DRAWING': score += 100
    
    if desc.find(q) != -1: score += 80
    if specs_str.find(q) != -1: score += 60
    
    if score > 0:
        scored.append((score, n.get('id'), n.get('label'), ntype))

scored.sort(key=lambda x: x[0], reverse=True)
print(f"Top 10 results from rankSearchResults for '{query}':")
for s in scored[:10]:
    print(s)
