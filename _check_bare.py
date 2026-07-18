import re, pathlib
pattern = re.compile(r'^\s*except\s*:\s*$', re.MULTILINE)
pattern2 = re.compile(r'^\s*except\s+Exception\s*:\s*$', re.MULTILINE)
files = list(pathlib.Path('src').rglob('*.py'))
violations = []
for f in files:
    txt = f.read_text(encoding='utf-8', errors='ignore')
    m1 = pattern.findall(txt)
    m2 = pattern2.findall(txt)
    if m1 or m2:
        violations.append((str(f), len(m1), len(m2)))
print(violations)
if violations:
    print("FAIL bare except found")
else:
    print("PASS no bare except")
