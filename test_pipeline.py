#!/usr/bin/env python3
"""Basic tests for IBIS (Integrated Brain Information System) pipeline components."""

import os
import sys

# Run from pipeline root
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)

from scripts.utils import validate_config, validate_dataframe, safe_divide, extract_subject_id

def test_utils():
    assert validate_dataframe(None) is False
    import pandas as pd
    assert validate_dataframe(pd.DataFrame({'A': [1], 'B': [2]}), required_columns=['A', 'B']) is True
    assert safe_divide(10, 2) == 5.0 and safe_divide(10, 0, 0.0) == 0.0
    assert extract_subject_id("6966_coords.csv") == "6966"
    print("Utils OK")

def test_config_validation():
    config = {
        'pipeline': {'name': 'Test', 'version': '1.0'},
        'paths': {'input_dir': 'in', 'output_dir': 'out', 'logs_dir': 'out/logs'},
        'logging': {'level': 'INFO'}
    }
    validate_config(config)
    print("Config validation OK")

def test_imports():
    from scripts.roi_extraction import ROIExtractor
    from scripts.buffer_zone import BufferZoneAnalyzer
    from scripts.variable_extraction import VariableExtractor
    from scripts.data_consolidation import DataConsolidator
    print("Imports OK")

def main():
    print("IBIS (Integrated Brain Information System) tests")
    print("-" * 40)
    test_utils()
    test_config_validation()
    test_imports()
    print("-" * 40)
    print("All checks passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
