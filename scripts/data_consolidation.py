"""
Data Consolidation Module - Combine covariate datasets.
"""

import os
import pandas as pd
import numpy as np
import logging

from .utils import get_file_list, log_memory_usage


class DataConsolidator:
    """Consolidate multiple covariate datasets into unified formats."""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.input_dir = config['paths']['input_dir']
        self.output_dir = os.path.join(config['paths']['output_dir'], 'consolidated')
        self.base_output_dir = config['paths']['output_dir']
        os.makedirs(self.output_dir, exist_ok=True)
        c = config.get('consolidation', {})
        self.remove_duplicates = c.get('remove_duplicates', True)
        self.handle_missing = c.get('handle_missing', 'drop')
        self.fill_value = c.get('fill_value', 0.0)

    def consolidate_covariates(self, base_dir, output_file, prefix_to_remove=None):
        if not os.path.isdir(base_dir):
            return False
        data_list = []
        for subfolder in os.listdir(base_dir):
            subfolder_path = os.path.join(base_dir, subfolder)
            if not os.path.isdir(subfolder_path):
                continue
            for csv_file in get_file_list(subfolder_path, ['.csv']):
                try:
                    df = pd.read_csv(csv_file)
                    if 'X' in df.columns and 'Y' in df.columns and 'Z' in df.columns:
                        coordinates = df[['X', 'Y', 'Z']].astype(np.int16)
                        coord_cols = ['X', 'Y', 'Z']
                    elif 'x' in df.columns and 'y' in df.columns and 'z' in df.columns:
                        coordinates = df[['x', 'y', 'z']].astype(np.int16)
                        coord_cols = ['x', 'y', 'z']
                    else:
                        continue
                    covariate_values = df.iloc[:, -1].astype(np.float32).round(3)
                    column_label = os.path.splitext(os.path.basename(csv_file))[0]
                    if prefix_to_remove and column_label.startswith(prefix_to_remove):
                        column_label = column_label[len(prefix_to_remove):]
                    result_df = pd.DataFrame({
                        'i': coordinates[coord_cols[0]],
                        'j': coordinates[coord_cols[1]],
                        'k': coordinates[coord_cols[2]],
                        column_label: covariate_values
                    })
                    data_list.append(result_df)
                except Exception as e:
                    self.logger.error(f"Error processing {csv_file}: {e}")
        if not data_list:
            return False
        consolidated_df = pd.concat(data_list, axis=1)
        consolidated_df = consolidated_df.loc[:, ~consolidated_df.columns.duplicated()]
        consolidated_df.to_csv(output_file, index=False)
        return True

    def consolidate_buffer_zone_data(self):
        bz_dir = os.path.join(self.base_output_dir, 'buffer_zone')
        if not os.path.exists(bz_dir):
            bz_dir = os.path.join(self.input_dir, 'buffer_zone')
        if not os.path.exists(bz_dir):
            return False
        return self.consolidate_covariates(bz_dir, os.path.join(self.output_dir, 'bz_consolidated_MFG_v1.csv'))

    def consolidate_edt_data(self):
        edt_dir = os.path.join(self.base_output_dir, 'variables', 'edt')
        if not os.path.exists(edt_dir):
            edt_dir = os.path.join(self.input_dir, 'variables', 'edt')
        if not os.path.exists(edt_dir):
            return False
        return self.consolidate_covariates(edt_dir, os.path.join(self.output_dir, 'edt_consolidated_MFG_v1.csv'), "v1_edt_")

    def consolidate_var_data(self):
        var_dir = os.path.join(self.base_output_dir, 'variables', 'var')
        if not os.path.exists(var_dir):
            var_dir = os.path.join(self.input_dir, 'variables', 'var')
        if not os.path.exists(var_dir):
            return False
        return self.consolidate_covariates(var_dir, os.path.join(self.output_dir, 'var_consolidated_MFG_v1.csv'))

    def consolidate_all_data(self):
        bz_file = os.path.join(self.output_dir, 'bz_consolidated_MFG_v1.csv')
        edt_file = os.path.join(self.output_dir, 'edt_consolidated_MFG_v1.csv')
        var_file = os.path.join(self.output_dir, 'var_consolidated_MFG_v1.csv')
        output_file = os.path.join(self.output_dir, 'Cov_all_consolidated_MFG_v1.csv')
        existing = [(f, l) for (f, l) in [(bz_file, 'buffer_zone'), (edt_file, 'EDT'), (var_file, 'variance')] if os.path.exists(f)]
        if not existing:
            return False
        dataframes = []
        for file_path, _ in existing:
            try:
                dataframes.append(pd.read_csv(file_path))
            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")
        if not dataframes:
            return False
        merged_df = pd.concat(dataframes, axis=1)
        merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]
        if self.handle_missing == 'fill':
            merged_df = merged_df.fillna(self.fill_value)
        merged_df.to_csv(output_file, index=False)
        return True

    def run(self):
        self.logger.info("Starting data consolidation...")
        log_memory_usage(self.logger, "Initial")
        try:
            self.consolidate_buffer_zone_data()
            self.consolidate_edt_data()
            self.consolidate_var_data()
            self.consolidate_all_data()
            log_memory_usage(self.logger, "Final")
        except Exception as e:
            self.logger.error(f"Data consolidation failed: {e}")
            raise
