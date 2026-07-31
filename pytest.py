"""
Pytest Compatibility Module & Standalone Test Runner for Mkulima Gemma
Supports running 'pytest' or 'python pytest.py tests/test_rag.py -v'.
"""

import sys
import os
import inspect
import asyncio
import traceback
import time
import importlib.util
from contextlib import contextmanager

# 1. Try loading real pytest package if present in site-packages
_real_pytest = None
_cwd = os.path.abspath(os.getcwd())
_clean_sys_path = [p for p in sys.path if p and os.path.abspath(p) != _cwd]

for _p in _clean_sys_path:
    _target = os.path.join(_p, "pytest", "__init__.py")
    if os.path.exists(_target):
        try:
            _spec = importlib.util.spec_from_file_location("pytest", _target)
            if _spec and _spec.loader:
                _real_pytest = importlib.util.module_from_spec(_spec)
                sys.modules["pytest"] = _real_pytest
                _spec.loader.exec_module(_real_pytest)
                break
        except Exception:
            _real_pytest = None

if _real_pytest:
    for _k, _v in _real_pytest.__dict__.items():
        if not _k.startswith("__"):
            globals()[_k] = _v
    main = _real_pytest.main
else:
    # 2. Standalone test runner shim
    _fixtures = {}

    def fixture(func=None, scope="function", autouse=False, name=None):
        def decorator(fn):
            fixture_name = name or fn.__name__
            _fixtures[fixture_name] = fn
            fn._is_fixture = True
            return fn

        if callable(func):
            return decorator(func)
        return decorator

    class _Mark:
        def __getattr__(self, name):
            def decorator(fn):
                setattr(fn, f"_mark_{name}", True)
                return fn
            return decorator

    mark = _Mark()

    @contextmanager
    def raises(expected_exception, match=None):
        class ExceptionInfo:
            def __init__(self):
                self.value = None

        info = ExceptionInfo()
        try:
            yield info
            assert False, f"Expected exception {expected_exception} was not raised"
        except expected_exception as exc:
            info.value = exc
            if match and match not in str(exc):
                raise AssertionError(f"Exception message '{str(exc)}' did not match '{match}'")

    def _resolve_fixture(fix_name, available_fixtures, active_generators):
        if fix_name not in available_fixtures:
            if "mock" in fix_name or fix_name.startswith("patch_"):
                from unittest.mock import MagicMock
                return MagicMock()
            raise ValueError(f"Fixture {fix_name} not found")
        fix_fn = available_fixtures[fix_name]
        sig = inspect.signature(fix_fn)
        kwargs = {}
        for p in sig.parameters:
            kwargs[p] = _resolve_fixture(p, available_fixtures, active_generators)
        fix_res = fix_fn(**kwargs)
        if inspect.isgenerator(fix_res):
            val = next(fix_res)
            active_generators.append(fix_res)
            return val
        return fix_res

    def main(args=None):
        if args is None:
            args = sys.argv[1:]

        verbose = "-v" in args or "--verbose" in args
        test_paths = [a for a in args if not a.startswith("-")]

        if not test_paths:
            test_paths = [
                "tests/test_rag.py",
                "tests/test_activities.py",
                "tests/test_weather.py",
                "tests/test_pest_disease.py",
                "tests/test_extension.py",
                "tests/test_health.py",
            ]

        # Load conftest.py if exists
        conftest_path = os.path.join("tests", "conftest.py")
        if os.path.exists(conftest_path):
            spec = importlib.util.spec_from_file_location("conftest", conftest_path)
            conf_mod = importlib.util.module_from_spec(spec)
            sys.modules["conftest"] = conf_mod
            spec.loader.exec_module(conf_mod)
            for name, obj in inspect.getmembers(conf_mod):
                if hasattr(obj, "_is_fixture") or callable(obj):
                    if name in ["db_session", "client"]:
                        _fixtures[name] = obj

        print("============================= test session starts ==============================")
        print(f"platform {sys.platform} -- Python {sys.version.split()[0]}")
        print(f"rootdir: {os.getcwd()}")
        print(f"collected tests: {', '.join(test_paths)}")
        print()

        total_passed = 0
        total_failed = 0
        start_time = time.time()

        for path in test_paths:
            if not os.path.exists(path):
                print(f"WARNING: file not found: {path}")
                continue

            mod_name = os.path.basename(path).replace(".py", "")
            spec = importlib.util.spec_from_file_location(mod_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)

            # Discover fixtures in module
            module_fixtures = dict(_fixtures)
            for name, obj in inspect.getmembers(module):
                if hasattr(obj, "_is_fixture"):
                    module_fixtures[name] = obj

            test_funcs = [
                (name, obj) for name, obj in inspect.getmembers(module)
                if (name.startswith("test_") or name.endswith("_test")) and callable(obj)
            ]

            for name, func in test_funcs:
                test_id = f"{path}::{name}"
                sig = inspect.signature(func)
                kwargs = {}

                # Resolve generator fixtures safely
                active_generators = []
                try:
                    for param in sig.parameters:
                        if param in module_fixtures:
                            kwargs[param] = _resolve_fixture(param, module_fixtures, active_generators)

                    if inspect.iscoroutinefunction(func):
                        asyncio.run(func(**kwargs))
                    else:
                        func(**kwargs)

                    total_passed += 1
                    print(f"{test_id} PASSED")
                except Exception as exc:
                    total_failed += 1
                    print(f"{test_id} FAILED")
                    traceback.print_exc()
                finally:
                    # Tear down generator fixtures in reverse order
                    for gen in reversed(active_generators):
                        try:
                            next(gen)
                        except StopIteration:
                            pass
                        except Exception:
                            pass

        duration = time.time() - start_time
        print()
        print(f"===================== {total_passed} passed, {total_failed} failed in {duration:.2f}s =====================")
        return 0 if total_failed == 0 else 1


if "pytest" not in sys.modules:
    sys.modules["pytest"] = sys.modules[__name__]

if __name__ == "__main__":
    sys.exit(main())
