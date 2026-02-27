#!/usr/bin/env python3
"""Verify IBIS (Integrated Brain Information System) dependencies and configuration."""

import sys
import os
import importlib

try:
    import yaml
except ImportError:
    yaml = None

def check_python():
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 7):
        print(f"Python 3.7+ required; found {v.major}.{v.minor}")
        return False
    print(f"Python {v.major}.{v.minor}.{v.micro} OK")
    return True

def check_packages():
    required = ['numpy', 'pandas', 'nibabel', 'nilearn', 'scikit-learn', 'scipy', 'joblib', 'PyYAML', 'matplotlib', 'seaborn', 'tqdm']
    missing = []
    for pkg in required:
        try:
            importlib.import_module(pkg)
            print(f"  {pkg} OK")
        except ImportError:
            missing.append(pkg)
            print(f"  {pkg} MISSING")
    if missing:
        print("Install: pip install -r requirements.txt")
        return False
    return True

def check_config():
    if yaml is None:
        print("  PyYAML not installed; skip config check")
        return True
    for name in ['config/pipeline_config.yaml', 'config/roi_config.yaml', 'config/buffer_zone_config.yaml']:
        if not os.path.exists(name):
            print(f"  {name} missing")
            return False
        try:
            with open(name) as f:
                yaml.safe_load(f)
            print(f"  {name} OK")
        except Exception as e:
            print(f"  {name} invalid: {e}")
            return False
    return True

def check_dirs():
    for d in ['scripts', 'config', 'input', 'output']:
        if d in ['input', 'output'] and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            print(f"  {d}/ created")
        elif d == 'scripts' or d == 'config':
            if not os.path.isdir(d):
                print(f"  {d}/ missing")
                return False
            print(f"  {d}/ OK")
    return True

def main():
    print("IBIS (Integrated Brain Information System) setup check")
    print("-" * 40)
    ok = check_python() and check_packages() and check_config() and check_dirs()
    print("-" * 40)
    print("OK - ready to run" if ok else "Fix issues above, then run: python run_ibis_pipeline.py")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
