import json

with open('data/rdso_manuals_knowledge.json', 'r', encoding='utf-8') as f:
    mk = json.load(f)

c_dict = mk.get('clauses', {})
matches = []
for cid, c in c_dict.items():
    text = (cid + ' ' + c.get('title', '') + ' ' + c.get('summary', '') + ' ' + c.get('verbatim', '')).lower()
    if 'destress' in text or 'de-stress' in text or 'temperature' in text:
        if 'destress' in text or 'de-stress' in text:
            matches.append((cid, c.get('title'), c.get('chapter'), c.get('page'), c.get('verbatim', '')[:160]))

print(f"Total destress matches: {len(matches)}")
for cid, title, ch, pg, verb in matches:
    print(f"[{cid}] (Page {pg}, Ch: {ch}): {title}")
    print(f"   Excerpt: {repr(verb)}")
