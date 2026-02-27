# IBIS (Integrated Brain Information System) — Quick start

1. **Install**
   ```bash
   cd IBIS
   pip install -r requirements.txt
   python check_setup.py
   ```

2. **Add data**  
   Place NIfTI images in `input/images/`, ROI masks in `input/masks/`. Optionally add CSVs to `input/QNP_vox_coords/`, `input/coordinates/`, and EDT/Var images as in the main README.

3. **Run**
   ```bash
   python run_ibis_pipeline.py
   ```

4. **Results**  
   Check `output/roi/`, `output/buffer_zone/`, `output/variables/`, `output/consolidated/`, and `output/logs/`.

For step-by-step runs or config details, see [README.md](README.md).
