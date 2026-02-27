"""
Utility functions for IBIS (Integrated Brain Information System).
"""

import os
import logging
import yaml
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime


def setup_logging(log_dir, level='INFO', format_str=None, file_name='pipeline.log', console=True):
    """
    Setup logging configuration for the pipeline.

    Args:
        log_dir (str): Directory to store log files
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
        format_str (str): Log format string
        file_name (str): Name of the log file
        console (bool): Whether to output to console

    Returns:
        logging.Logger: Configured logger instance
    """
    os.makedirs(log_dir, exist_ok=True)

    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logger = logging.getLogger('IBIS')
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers.clear()
    formatter = logging.Formatter(format_str)

    log_file = os.path.join(log_dir, file_name)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def validate_config(config):
    """Validate the pipeline configuration."""
    required_sections = ['pipeline', 'paths', 'logging']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    paths = config['paths']
    for path_key in ['input_dir', 'output_dir', 'logs_dir']:
        if path_key not in paths:
            raise ValueError(f"Missing required path configuration: {path_key}")
    if 'level' in config.get('logging', {}):
        level = config['logging']['level'].upper()
        if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            raise ValueError(f"Invalid logging level: {level}")


def create_directories(directory_paths):
    """Create directories if they don't exist."""
    for path in directory_paths:
        os.makedirs(path, exist_ok=True)


def load_yaml_config(config_path):
    """Load YAML configuration file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Error loading configuration file {config_path}: {e}")


def get_file_list(directory, file_patterns=None):
    """Get list of files from directory matching patterns."""
    if not os.path.exists(directory):
        return []
    files = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            if file_patterns is None:
                files.append(file_path)
            else:
                for pattern in file_patterns:
                    if file.endswith(pattern):
                        files.append(file_path)
                        break
    return sorted(files)


def extract_subject_id(filename, pattern=None):
    """Extract subject ID from filename."""
    import re
    if pattern is None:
        pattern = r'(\d{4})'
    match = re.search(pattern, filename)
    return match.group(1) if match else None


def validate_dataframe(df, required_columns=None, min_rows=1):
    """Validate DataFrame structure and content."""
    if df is None or df.empty or len(df) < min_rows:
        return False
    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return False
    return True


def safe_divide(numerator, denominator, default=0.0):
    """Safely divide two numbers."""
    try:
        return default if denominator == 0 else numerator / denominator
    except (TypeError, ValueError):
        return default


def create_progress_logger(logger, total_items, description="Processing"):
    """Create a progress logger for tracking processing steps."""
    def log_progress(current_item, item_name=None):
        progress = (current_item / total_items) * 100
        msg = f"{description}: {current_item}/{total_items} ({progress:.1f}%)"
        if item_name:
            msg += f" - {item_name}"
        logger.info(msg)
    return log_progress


def log_memory_usage(logger, description="Current"):
    """Log current memory usage if psutil is available."""
    try:
        import psutil
        process = psutil.Process()
        mem = process.memory_info()
        logger.info(f"{description} memory: {mem.rss / 1024 / 1024:.1f} MB RSS")
    except ImportError:
        logger.debug("psutil not available for memory logging")
