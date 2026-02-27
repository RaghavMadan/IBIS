"""
Buffer Zone Analysis Module
"""

import os
import numpy as np
import pandas as pd
import warnings
from sklearn import neighbors
from scipy import sparse
from nilearn import image, masking
from nilearn.masking import apply_mask
from nilearn._utils.niimg_conversions import check_niimg_3d
import logging

from .utils import (
    get_file_list, extract_subject_id, create_progress_logger, log_memory_usage
)


class BufferZoneAnalyzer:
    """Buffer zone analysis using spherical maskers."""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.bz_config = self._load_bz_config()
        self.input_dir = config['paths']['input_dir']
        self.output_dir = os.path.join(config['paths']['output_dir'], 'buffer_zone')
        self.coordinates_dir = os.path.join(self.input_dir, 'coordinates')
        self.images_dir = os.path.join(self.input_dir, 'images')
        os.makedirs(self.output_dir, exist_ok=True)
        self.bz_settings = config.get('buffer_zone', {})
        self.default_radius = self.bz_settings.get('default_radius', 5.0)
        self.allow_overlap = self.bz_settings.get('allow_overlap', False)

    def _load_bz_config(self):
        path = os.path.join('config', 'buffer_zone_config.yaml')
        if os.path.exists(path):
            try:
                import yaml
                with open(path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                self.logger.warning(f"Could not load buffer zone config: {e}")
        return {}

    def _apply_mask_and_get_affinity(self, seeds, niimg, radius, allow_overlap, mask_img=None):
        if niimg is None:
            mask, affine = masking._load_mask_img(mask_img)
            mask_coords = np.asarray(np.nonzero(mask)).T.tolist()
            X = None
        elif mask_img is not None:
            affine = niimg.affine
            mask_img = check_niimg_3d(mask_img)
            mask_img = image.resample_img(mask_img, target_affine=affine, target_shape=niimg.shape[:3], interpolation='nearest')
            mask, _ = masking._load_mask_img(mask_img)
            mask_coords = list(zip(*np.where(mask != 0)))
            masked = apply_mask(niimg, mask_img, dtype='f')
            X = masked.reshape(1, -1) if masked.ndim == 1 else masked
        else:
            raise ValueError("Either niimg or mask_img must be provided")
        mask_coords = np.asarray(list(zip(*mask_coords)))
        mask_coords = np.asarray(image.resampling.coord_transform(mask_coords[0], mask_coords[1], mask_coords[2], affine)).T
        clf = neighbors.NearestNeighbors(radius=radius, n_jobs=-1)
        clf.fit(mask_coords)
        A = clf.radius_neighbors_graph(seeds)
        return X, A

    def extract_buffer_zone_data(self, coordinates_file, image_file, radius=None):
        radius = radius or self.default_radius
        try:
            coords_df = pd.read_csv(coordinates_file)
            required_cols = ['X', 'Y', 'Z']
            if any(c not in coords_df.columns for c in required_cols):
                return pd.DataFrame()
            seeds = coords_df[required_cols].values
            img = image.load_img(image_file)
            X, A = self._apply_mask_and_get_affinity(seeds, img, radius, self.allow_overlap)
            results = []
            for i, seed in enumerate(seeds):
                sphere_voxels = A[i].nonzero()[1]
                if len(sphere_voxels) == 0:
                    continue
                if X is not None:
                    sphere_values = X[:, sphere_voxels]
                    mean_val, std_val = np.mean(sphere_values), np.std(sphere_values)
                    max_val, min_val = np.max(sphere_values), np.min(sphere_values)
                else:
                    mean_val = std_val = max_val = min_val = np.nan
                results.append({
                    'seed_id': i, 'x': seed[0], 'y': seed[1], 'z': seed[2],
                    'radius_mm': radius, 'voxel_count': len(sphere_voxels),
                    'mean_value': mean_val, 'std_value': std_val, 'max_value': max_val, 'min_value': min_val
                })
            return pd.DataFrame(results)
        except Exception as e:
            self.logger.error(f"Error extracting buffer zone: {e}")
            return pd.DataFrame()

    def process_coordinate_files(self):
        coord_files = get_file_list(self.coordinates_dir, ['.csv'])
        image_files = get_file_list(self.images_dir, ['.nii.gz', '.nii'])
        if not coord_files or not image_files:
            return
        default_image = image_files[0]
        radius_options = self.bz_config.get('buffer_zone', {}).get('radius_options', [self.default_radius])
        all_results = []
        for coord_file in coord_files:
            subject_id = extract_subject_id(os.path.basename(coord_file), r'(\d{4})')
            if subject_id is None:
                continue
            for radius in radius_options:
                df = self.extract_buffer_zone_data(coord_file, default_image, radius)
                if not df.empty:
                    df['subject_id'] = subject_id
                    all_results.append(df)
        if all_results:
            pd.concat(all_results, ignore_index=True).to_csv(
                os.path.join(self.output_dir, 'buffer_zone_metrics.csv'), index=False)

    def run(self):
        self.logger.info("Starting buffer zone analysis...")
        log_memory_usage(self.logger, "Initial")
        try:
            self.process_coordinate_files()
            log_memory_usage(self.logger, "Final")
        except Exception as e:
            self.logger.error(f"Buffer zone analysis failed: {e}")
            raise
