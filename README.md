# RuralRoad Mapping - Laubach (35321)

Characterisation of rural road conditions from remote sensing.

This repository contains a full workflow for rural road surface classification using:
- OpenStreetMap road geometry
- Sentinel-2 (optical) features via openEO/CDSE
- Sentinel-1 (radar) features via openEO/CDSE
- Python ML classification and QGIS-ready outputs

## Project Workflow

1. OSM extraction and buffering
- Script: `01_osm_extraction_laubach.py`
- Outputs: line and 5 m buffer GeoPackages

2. Feature extraction (openEO)
- Script: `02_openeo_feature_extraction_laubach.py`
- Outputs: `openeo_outputs/laubach_feature_table.csv`, S1/S2 raster exports

3. Classification and export
- Script: `03_classification_export_laubach.py`
- Outputs in `classification_outputs/`:
  - classified line and buffer GeoPackages
  - prediction CSV
  - models (`.joblib`)
  - QGIS style (`.sld`)
  - evaluation plots

4. QGIS packaging
- Project: `laubach_feldwege.qgs`
- Packaging script: `create_qgis_package.ps1`
- Distributable: `laubach_qgis_package.zip`

## Gitflow Initialization

Gitflow (AVH edition) is initialized in this repository with defaults:
- Production branch: `main`
- Development branch: `develop`
- Prefixes:
  - `feature/`
  - `bugfix/`
  - `release/`
  - `hotfix/`
  - `support/`

## Team Branch Policy

- Implement normal work on `develop` through `feature/*` branches.
- Merge validated releases from `develop` to `main`.
- Create urgent production fixes from `main` using `hotfix/*`.

## Current Status

- End-to-end pipeline has been executed.
- Final S1+S2 feature table is available.
- QGIS project and distributable package are available.
- Model quality still needs improvement (label quality / feature strategy), but workflow execution is stable.

## Quick Start

```powershell
# run extraction
python 01_osm_extraction_laubach.py

# run feature extraction
python 02_openeo_feature_extraction_laubach.py

# run classification
python 03_classification_export_laubach.py

# build qgis package
./create_qgis_package.ps1
```
