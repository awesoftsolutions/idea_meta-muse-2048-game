"""Validate visual-proof/phase-3-first-light.png header and manifest."""
import pathlib
p = pathlib.Path("visual-proof/phase-3-first-light.png")
data = p.read_bytes()
print(f"size={len(data)}")
header = data[:8]
print(f"header_hex={header.hex()}")
expected = bytes([0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A])
print(f"valid_png={header==expected}")
print(f"header_bytes={list(header)}")
# Check manifest
readme = pathlib.Path("visual-proof/README.md").read_text(encoding="utf-8")
checks = {
    "filename_present": "phase-3-first-light.png" in readme,
    "what_it_shows": "what it shows" in readme.lower() or "shows" in readme.lower(),
    "input_sequence": "input" in readme.lower(),
    "observation_id": "observation" in readme.lower() or "first-light-001" in readme,
}
for k,v in checks.items():
    print(f"{k}={v}")
# Check render dir
render_dir = pathlib.Path("src/render")
files = [x.name for x in render_dir.glob("*.py")]
print(f"render_files={files}")
print(f"only_init_tiles={set(files)=={'__init__.py','tiles.py'}}")
# Check core no pygame import
core_dir = pathlib.Path("src/core")
violations=[]
for py_file in core_dir.glob("*.py"):
    content=py_file.read_text(encoding="utf-8")
    for i,line in enumerate(content.splitlines(),1):
        stripped=line.strip()
        if stripped.startswith("#"):
            continue
        if "import pygame" in stripped or "from pygame" in stripped:
            violations.append(f"{py_file}:{i}:{stripped}")
print(f"core_pygame_violations={violations}")
print(f"core_no_pygame={len(violations)==0}")
# Check tiles.py no image.load
tiles_path = pathlib.Path("src/render/tiles.py")
content = tiles_path.read_text(encoding="utf-8")
print(f"has_image_load={'pygame.image.load' in content}")
print(f"has_SysFont={'SysFont' in content}")
print(f"has_heat_colors={all(x in content for x in ['59, 130, 246','245, 158, 11','239, 68, 68','255, 255, 255'])}")
print(f"has_reactor_chrome={all(x in content for x in ['15, 23, 42','30, 41, 59','51, 65, 85','71, 85, 105'])}")
