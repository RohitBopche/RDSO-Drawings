import json

with open('data/rdso_canonical_kg.json', 'r', encoding='utf-8') as f:
    kg = json.load(f)

nodes = kg.get('entities', [])
query = "destressing temperature"
q = query.lower()
tokens = [t for t in q.split() if len(t) > 2]

scored = []
for n in nodes:
    nid = n.get('id', '').lower()
    label = n.get('label', '').lower()
    desc = n.get('desc', '').lower()
    specs_str = json.dumps(n.get('specs', {})).lower()
    ntype = n.get('type', '').upper()
    domain = n.get('domain', '').lower()
    all_text = f"{nid} {label} {desc} {specs_str}"

    sLexical = 0
    sMetadata = 0
    sSemantic = 0
    sGraph = 0

    # Token matching
    token_matches = sum(1 for tok in tokens if tok in all_text)
    if token_matches > 0:
        sLexical += token_matches * 80
        if token_matches == len(tokens) and len(tokens) > 1:
            sLexical += 300  # Multi-token all-match bonus

    if q in all_text:
        sLexical += 250

    if q in label:
        sLexical += 400
    elif any(tok in label for tok in tokens):
        sLexical += 150

    # Only reward drawings if query actually mentions drawings
    isDrawingQuery = any(k in q for k in ['6155', '6154', '6216', '6280', '6275', 'drg', 'drawing', 't-'])
    if ntype == 'DRAWING' and isDrawingQuery:
        sMetadata += 300

    # Only add graph score if there was an actual text match
    if sLexical > 0:
        sGraph += 40

    total = sLexical + sMetadata + sSemantic + sGraph
    if total > 0:
        scored.append((total, n.get('id'), n.get('label'), ntype))

scored.sort(key=lambda x: x[0], reverse=True)
print(f"Top 10 results with new ranking for '{query}':")
for s in scored[:10]:
    print(s)
