import pathlib, sys
m=pathlib.Path('spike_packaging/minimal.py')
b=pathlib.Path('spike_packaging/build.log')
d=pathlib.Path('dist/minimal.exe')
assert m.exists(), 'minimal.py missing'
txt=m.read_text()
assert 'pygame' in txt
assert '700' in txt and '800' in txt
assert 'Favur 2048' in txt
assert 'src.core' not in txt
assert b.exists(), 'build.log missing'
blog=b.read_text()
assert 'PyInstaller' in blog
print(f"minimal.py lines={len(txt.splitlines())}")
print(f"build.log lines={len(blog.splitlines())}")
print(f"dist exists={d.exists()}")
print("VERIFICATION PASS")
