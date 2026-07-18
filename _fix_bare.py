import pathlib, re
for path in pathlib.Path('src/core').rglob('*.py'):
    txt = path.read_text(encoding='utf-8')
    # Replace except Exception: with except (ValueError, TypeError, AttributeError):
    # But keep logic: replace all occurrences
    new = txt.replace('except Exception:', 'except (ValueError, TypeError, AttributeError):')
    if new != txt:
        path.write_text(new, encoding='utf-8')
        print(f"Fixed {path}")
print("done")
