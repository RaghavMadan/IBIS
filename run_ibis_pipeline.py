#!/usr/bin/env python3
"""
IBIS (Integrated Brain Information System) — Main entry point.

Run from the pipeline root:
  python run_ibis_pipeline.py [--config config/pipeline_config.yaml] [--steps ...]
"""

import os
import sys
import traceback

# Ensure pipeline root is on path so "scripts" package is found
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from scripts.roi_extraction import ROIExtractor
from scripts.buffer_zone import BufferZoneAnalyzer
from scripts.variable_extraction import VariableExtractor
from scripts.data_consolidation import DataConsolidator
from scripts.utils import setup_logging, validate_config

import argparse
import yaml
import logging
from datetime import datetime


class IBISPipeline:
    """Orchestrates all IBIS (Integrated Brain Information System) components."""

    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.start_time = datetime.now()
        self.roi_extractor = None
        self.buffer_zone_analyzer = None
        self.variable_extractor = None
        self.data_consolidator = None

    def _load_config(self):
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        log_config = self.config.get('logging', {})
        log_dir = self.config['paths']['logs_dir']
        os.makedirs(log_dir, exist_ok=True)
        return setup_logging(
            log_dir=log_dir,
            level=log_config.get('level', 'INFO'),
            format_str=log_config.get('format'),
            file_name=log_config.get('file', 'pipeline.log'),
            console=log_config.get('console', True)
        )

    def validate_environment(self):
        for key in ['input_dir', 'output_dir']:
            path = self.config['paths'][key]
            if not os.path.exists(path):
                self.logger.warning(f"Creating {path}")
                os.makedirs(path, exist_ok=True)
        validate_config(self.config)

    def initialize_components(self):
        self.roi_extractor = ROIExtractor(self.config, self.logger)
        self.buffer_zone_analyzer = BufferZoneAnalyzer(self.config, self.logger)
        self.variable_extractor = VariableExtractor(self.config, self.logger)
        self.data_consolidator = DataConsolidator(self.config, self.logger)

    def run_pipeline(self, steps=None):
        self.logger.info("Starting IBIS (Integrated Brain Information System)")
        pipeline_steps = {
            'roi_extraction': lambda: self.roi_extractor.run(),
            'buffer_zone': lambda: self.buffer_zone_analyzer.run(),
            'variable_extraction': lambda: self.variable_extractor.run(),
            'consolidation': lambda: self.data_consolidator.run(),
        }
        steps = steps or list(pipeline_steps.keys())
        invalid = [s for s in steps if s not in pipeline_steps]
        if invalid:
            self.logger.error(f"Invalid steps: {invalid}")
            return False
        success_count = 0
        for step_name in steps:
            try:
                if pipeline_steps[step_name]():
                    success_count += 1
                else:
                    self.logger.error(f"Step {step_name} failed")
            except Exception as e:
                self.logger.error(f"Step {step_name}: {e}")
                self.logger.error(traceback.format_exc())
        self.logger.info(f"Completed {success_count}/{len(steps)} steps in {datetime.now() - self.start_time}")
        return success_count == len(steps)


def main():
    parser = argparse.ArgumentParser(
        description="IBIS (Integrated Brain Information System)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--config', default='config/pipeline_config.yaml', help='Configuration file')
    parser.add_argument('--steps', nargs='+',
                        choices=['roi_extraction', 'buffer_zone', 'variable_extraction', 'consolidation'],
                        help='Steps to run (default: all)')
    parser.add_argument('--validate-only', action='store_true', help='Validate config and exit')
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Config not found: {args.config}")
        sys.exit(1)

    try:
        pipeline = IBISPipeline(args.config)
        pipeline.validate_environment()
        if args.validate_only:
            print("Validation OK.")
            return
        pipeline.initialize_components()
        ok = pipeline.run_pipeline(steps=args.steps)
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
