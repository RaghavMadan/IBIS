"""
Variable Extraction Module - EDT and Variance from masked regions.
"""

import os
import numpy as np
import pandas as pd
import nilearn
from nilearn import image
from nilearn.masking import apply_mask
import logging
import gc

from .utils import get_file_list, create_progress_logger, log_memory_usage


class VariableExtractor:
    """Extract imaging variables (EDT, Variance) from masked regions."""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.input_dir = config['paths']['input_dir']
        self.output_dir = os.path.join(config['paths']['output_dir'], 'variables')
        self.mask_dir = os.path.join(self.input_dir, 'masks')
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'edt'), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'var'), exist_ok=True)
        var_settings = config.get('variable_extraction', {})
        self.edt_enabled = var_settings.get('edt', {}).get('enabled', True)
        self.var_enabled = var_settings.get('var', {}).get('enabled', True)

    def extract_edt_values(self, edt_dir, mask_path, roi_name):
        if not self.edt_enabled:
            return True
        try:
            mask_img = nilearn.image.load_img(mask_path)
            edt_files = get_file_list(edt_dir, ['_masked.nii.gz'])
            if not edt_files:
                return False
            for edt_file in edt_files:
                name = os.path.basename(edt_file).split('_masked.nii.gz')[0]
                img = nilearn.image.load_img(edt_file)
                masked_data = apply_mask(img, mask_img, dtype='f')
                mask_indices = np.where(mask_img.get_fdata() > 0)
                coordinates = np.vstack(mask_indices).T
                df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z'])
                df['Value'] = masked_data
                df.to_csv(os.path.join(self.output_dir, 'edt', f"v1_edt_{name}_{roi_name}.csv"), index=False)
                del img, masked_data, df
                gc.collect()
            return True
        except Exception as e:
            self.logger.error(f"EDT extraction failed: {e}")
            return False

    def extract_var_values(self, var_dir, mask_dir, roi_name):
        if not self.var_enabled:
            return True
        try:
            var_files = get_file_list(var_dir, ['.nii.gz', '.nii'])
            mask_files = get_file_list(mask_dir, ['.nii.gz', '.nii'])
            if not var_files or not mask_files:
                return False
            mask_img = nilearn.image.load_img(mask_files[0])
            for var_file in var_files:
                name = os.path.basename(var_file).split('.nii')[0]
                img = nilearn.image.load_img(var_file)
                masked_data = apply_mask(img, mask_img, dtype='f')
                mask_indices = np.where(mask_img.get_fdata() > 0)
                coordinates = np.vstack(mask_indices).T
                df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z'])
                df['Value'] = masked_data
                df.to_csv(os.path.join(self.output_dir, 'var', f"var_{name}_{roi_name}.csv"), index=False)
                del img, masked_data, df
                gc.collect()
            return True
        except Exception as e:
            self.logger.error(f"Variance extraction failed: {e}")
            return False

    def process_edt_directory(self):
        for sub in ['4_edt_m', 'EDT', 'edt']:
            edt_dir = os.path.join(self.input_dir, sub)
            if os.path.exists(edt_dir):
                mask_files = get_file_list(self.mask_dir, ['.nii.gz', '.nii'])
                if mask_files:
                    roi_name = os.path.basename(mask_files[0]).split('_')[0]
                    return self.extract_edt_values(edt_dir, mask_files[0], roi_name)
        return False

    def process_var_directory(self):
        for sub in ['Var', 'var', 'variables']:
            var_dir = os.path.join(self.input_dir, sub)
            if os.path.exists(var_dir):
                roi_name = "MFG"
                mask_files = get_file_list(self.mask_dir, ['.nii.gz', '.nii'])
                if mask_files:
                    roi_name = os.path.basename(mask_files[0]).split('_')[0]
                return self.extract_var_values(var_dir, self.mask_dir, roi_name)
        return False

    def run(self):
        self.logger.info("Starting variable extraction...")
        log_memory_usage(self.logger, "Initial")
        try:
            if self.edt_enabled:
                self.process_edt_directory()
            if self.var_enabled:
                self.process_var_directory()
            log_memory_usage(self.logger, "Final")
        except Exception as e:
            self.logger.error(f"Variable extraction failed: {e}")
            raise
