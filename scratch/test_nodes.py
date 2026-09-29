import re, glob

for path in sorted(glob.glob('tests/*.js')):
    content = open(path, encoding='utf-8').read()
    matches = re.findall(r'selectGraphNode\([\'"]([^\'"]+)[\'"]\)', content)
    if matches:
        print(f"{path}: {sorted(set(matches))}")
