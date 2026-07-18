from pathlib import Path
p = Path('dist')
print('exists', p.exists())
if p.exists():
    files = list(p.iterdir())
    print('files', files)
    print('len', len(files))
    for f in files:
        print(f, f.is_file(), f.stat().st_size if f.is_file() else 'dir')
