"""Run every test file in this folder (no pytest needed).   python tests/run_all.py"""
import glob
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

failed = total = 0
for path in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
    module = importlib.import_module(os.path.splitext(os.path.basename(path))[0])
    tests = [obj for name, obj in sorted(vars(module).items())
             if name.startswith("test_") and callable(obj) and obj.__module__ == module.__name__]
    for test in tests:
        total += 1
        try:
            test()
            print(f"PASS  {module.__name__}.{test.__name__}")
        except Exception as exc:   # report every test, do not stop at the first failure
            failed += 1
            print(f"FAIL  {module.__name__}.{test.__name__}: {type(exc).__name__}: {str(exc)[:400]}")
print(f"\n{total - failed}/{total} passed")
sys.exit(1 if failed else 0)
