import pathlib
for f in ["_verify_isolation.py","_update_debt.py","_run_pytest.py","_cleanup.py"]:
    p=pathlib.Path(f)
    if p.exists():
        p.unlink()
        print(f"removed {f}")
