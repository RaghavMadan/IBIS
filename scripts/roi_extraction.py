"""
ROI Voxel Extraction Module
"""

import os
import glob
import pandas as pd
import numpy as np
import nibabel as nib
from nilearn import image, masking
from nilearn.input_data import NiftiMasker
import logging
from pathlib import Path
import re

from .utils import (
    get_file_list, extract_subject_id, validate_dataframe,
    create_progress_logger, log_memory_usage
)


class ROIExtractor:
    """Extract voxel coordinates and intensity values from ROIs."""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.roi_config = self._load_roi_config()
        self.input_dir = config['paths']['input_dir']
        self.output_dir = os.path.join(config['paths']['output_dir'], 'roi')
        self.mask_dir = os.path.join(self.input_dir, 'masks')
        os.makedirs(self.output_dir, exist_ok=True)
        self.roi_settings = config.get('roi_extraction', {})
        self.coordinate_columns = self.roi_settings.get('coordinate_columns', ['X', 'Y', 'Z'])
        self.intensity_column = self.roi_settings.get('intensity_column', 'Intensity')
        self.subject_pattern = self.roi_settings.get('subject_id_pattern', r'(\d{4})')

    def _load_roi_config(self):
        roi_config_path = os.path.join('config', 'roi_config.yaml')
        if os.path.exists(roi_config_path):
            try:
                import yaml
                with open(roi_config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                self.logger.warning(f"Could not load ROI config: {e}")
        return {}

    def extract_coordinates_from_nifti(self, nifti_file, mask_file, subject_id):
        try:
            img = image.load_img(nifti_file)
            mask_img = image.load_img(mask_file)
            masked_data = masking.apply_mask(img, mask_img, dtype='f')
            mask_indices = np.where(mask_img.get_fdata() > 0)
            coordinates = np.vstack(mask_indices).T
            df = pd.DataFrame(coordinates, columns=self.coordinate_columns)
            df[self.intensity_column] = masked_data
            df['sub.id'] = subject_id
            return df
        except Exception as e:
            self.logger.error(f"Error extracting from {nifti_file}: {e}")
            return pd.DataFrame()

    def extract_coordinates_from_csv(self, csv_file, subject_id):
        try:
            df = pd.read_csv(csv_file)
            required_cols = self.coordinate_columns + [self.intensity_column]
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                self.logger.warning(f"Missing columns in {csv_file}: {missing}")
                return pd.DataFrame()
            df['sub.id'] = subject_id
            return df[required_cols + ['sub.id']]
        except Exception as e:
            self.logger.error(f"Error reading {csv_file}: {e}")
            return pd.DataFrame()

    def combine_coordinates_and_intensity(self, directory_path):
        csv_files = glob.glob(f"{directory_path}/QNP_vox_coords/*.csv")
        if not csv_files:
            return pd.DataFrame()
        combined_df = pd.DataFrame(columns=self.coordinate_columns + [self.intensity_column, 'sub.id'])
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                subject_id = extract_subject_id(os.path.basename(csv_file), self.subject_pattern)
                if subject_id is None:
                    continue
                df['sub.id'] = subject_id
                if 'Intensity' in df.columns and self.intensity_column not in df.columns:
                    df.rename(columns={'Intensity': self.intensity_column}, inplace=True)
                combined_df = pd.concat([combined_df, df], ignore_index=True)
            except Exception as e:
                self.logger.error(f"Error processing {csv_file}: {e}")
        if not combined_df.empty:
            combined_df.drop_duplicates(subset=self.coordinate_columns + [self.intensity_column, 'sub.id'], inplace=True)
        return combined_df

    def process_nifti_files(self):
        nifti_files = get_file_list(os.path.join(self.input_dir, 'images'), ['.nii.gz', '.nii'])
        if not nifti_files:
            return
        mask_files = get_file_list(self.mask_dir, ['.nii.gz', '.nii'])
        if not mask_files:
            return
        default_mask = mask_files[0]
        all_data = []
        for nifti_file in nifti_files:
            subject_id = extract_subject_id(os.path.basename(nifti_file), self.subject_pattern)
            if subject_id is None:
                continue
            df = self.extract_coordinates_from_nifti(nifti_file, default_mask, subject_id)
            if not df.empty:
                all_data.append(df)
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df.to_csv(os.path.join(self.output_dir, 'extracted_coordinates.csv'), index=False)

    def process_csv_files(self):
        qnp_dir = os.path.join(self.input_dir, 'QNP_vox_coords')
        if os.path.exists(qnp_dir):
            combined_df = self.combine_coordinates_and_intensity(self.input_dir)
            if not combined_df.empty:
                combined_df.to_csv(os.path.join(self.output_dir, 'combined_coordinates.csv'), index=False)

    def run(self):
        self.logger.info("Starting ROI extraction...")
        log_memory_usage(self.logger, "Initial")
        try:
            self.process_nifti_files()
            self.process_csv_files()
            log_memory_usage(self.logger, "Final")
        except Exception as e:
            self.logger.error(f"ROI extraction failed: {e}")
            raise
