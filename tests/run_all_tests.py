"""SpendSense — Standalone Test Runner & Verification Suite

Executes all test functions across tests/test_*.py without requiring external test runners.
Reports individual test outcomes, assertion status, and execution timings.
"""

import importlib
import inspect
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def run_tests():
    test_files = sorted(Path(ROOT / "tests").glob("test_*.py"))
    passed = 0
    failed = 0
    skipped = 0

    print("=" * 70)
    print("SpendSense Test Suite Runner")
    print(f"Discovered {len(test_files)} test files in tests/")
    print("=" * 70)

    start_total = time.time()

    for tf in test_files:
        mod_name = f"tests.{tf.stem}"
        print(f"\n[FILE] {tf.name}")
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            print(f"  ❌ FAILED TO IMPORT {mod_name}: {e}")
            traceback.print_exc()
            failed += 1
            continue

        test_funcs = [
            (name, func)
            for name, func in inspect.getmembers(mod, inspect.isfunction)
            if name.startswith("test_")
        ]

        if not test_funcs:
            print("  ⚠️  No test_* functions discovered.")
            continue

        for name, func in test_funcs:
            t0 = time.time()
            try:
                # Inspect if func expects arguments
                sig = inspect.signature(func)
                if len(sig.parameters) > 0:
                    print(f"  ⏭️  {name} (requires fixtures - skipped)")
                    skipped += 1
                    continue

                func()
                dt = (time.time() - t0) * 1000
                print(f"  ✅ {name} ({dt:.1f}ms)")
                passed += 1
            except Exception as e:
                dt = (time.time() - t0) * 1000
                print(f"  ❌ {name} FAILED ({dt:.1f}ms): {e}")
                traceback.print_exc()
                failed += 1

    total_time = (time.time() - start_total) * 1000
    print("\n" + "=" * 70)
    print(f"TEST EXECUTION SUMMARY: {passed} PASSED | {failed} FAILED | {skipped} SKIPPED ({total_time:.1f}ms)")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
