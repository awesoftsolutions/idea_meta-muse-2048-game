import subprocess, sys
result = subprocess.run([sys.executable, "-m", "pytest", "tests/test_isolation_phase4.py", "-v"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
print(f"exit code {result.returncode}")
