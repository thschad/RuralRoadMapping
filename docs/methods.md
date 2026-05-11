# Methods

## Overview

The method integrates vector extraction, remote sensing feature generation, supervised learning with weak labels, and GIS delivery.

## Provenance Logic in the Method

The processing chain separates information sources strictly:
- OSM contributes geometry and metadata (plus weak labels via mapping).
- Sentinel contributes EO feature variables only.
- The classifier combines EO features with training labels to produce final predictions.

## Step 1 - OSM Extraction and Geometry Processing

Implemented in 01_osm_extraction_laubach.py.

Processing steps:
1. Query OSM ways from Overpass API with defined highway tags.
2. Parse node and way structures to line geometry.
3. Preserve key attributes: highway, surface, tracktype, osm_id.
4. Reproject to metric CRS (EPSG:25832).
5. Buffer lines by 5 m to capture Sentinel pixel footprints.
6. Export both line and polygon representations as GeoPackage.

Method rationale:
- The line geometry preserves network topology.
- Buffered polygons support robust zonal raster aggregation.

## Step 2 - Earth Observation Feature Extraction

Implemented in 02_openeo_feature_extraction_laubach.py.

### Sentinel-2 Feature Engineering

Input bands:
- B02, B03, B04, B08, B11, B12, SCL

Cloud handling:
- SCL classes 3, 8, 9, 10 are masked.

Computed indices:
- NDVI = (NIR - RED) / (NIR + RED)
- NDWI = (GREEN - NIR) / (GREEN + NIR)
- NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)

Temporal reduction:
- median across time for each season.

### Sentinel-1 Feature Engineering

Input bands:
- VV, VH (descending orbit filter)

Derived signal:
- VV_VH_ratio = VV - VH (log-domain difference proxy)

Temporal reduction:
- median across time
- mean across time

### Segment-Level Aggregation

Method:
- Export seasonal raster feature cubes as GeoTIFF.
- Aggregate per buffered segment using masked raster extraction.
- Compute mean signal within each polygon and band.

Resilience decisions:
- Existing raster exports are reused to avoid rerunning completed jobs.
- Sentinel-1 can fallback to S2-only mode if backend instability occurs.

## Step 3 - Classification

Implemented in 03_classification_export_laubach.py.

Models:
- RandomForestClassifier
- GradientBoostingClassifier

Training setup:
- weak labels from OSM surface mapping
- stratified 5-fold CV for macro F1 comparison
- class-balanced random forest configuration

Provenance clarification:
- Input predictors: Sentinel-derived features (`NDVI_*`, `NDWI_*`, `NDBI_*`, `VV_*`, `VH_*`).
- Training target: OSM-derived `label_weak`.
- Output target: model-predicted `class_label` and associated confidence/probabilities.

This means the final map is not a direct OSM copy and not a direct Sentinel rule-based class.
It is an ML inference result trained on OSM weak supervision.

Evaluation artifacts:
- confusion matrix plot
- feature importance plot
- classification report

## Step 4 - GIS Export and Styling

Exports:
- classified lines and buffers as GeoPackage
- per-segment prediction table CSV
- QGIS SLD style
- packaged QGIS project for distribution

Distribution package:
- qgis_package folder and laubach_qgis_package.zip

## Method Limitations

Current quality constraints:
- weak-label noise from OSM surface metadata
- incomplete label coverage
- segment-level NaN values for some raster intersections

Method improvements recommended:
- introduce manually validated labels for calibration and test
- improve feature robustness on sparse/noisy segments
- test temporal and spatial cross-validation splits
