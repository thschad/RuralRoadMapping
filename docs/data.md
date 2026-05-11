# Data

## Data Inventory

### OSM Inputs

Source: OpenStreetMap via Overpass API.

Queried road tags include:
- highway=track
- highway=path
- highway=service
- highway=unclassified
- highway=tertiary

Spatial domain for Laubach:
- west: 8.85
- south: 50.45
- east: 9.10
- north: 50.60

### Sentinel Inputs

Source: Copernicus Data Space Ecosystem through openEO.

Collections:
- SENTINEL2_L2A
- SENTINEL1_GRD

Temporal windows:
- summer: 2024-05-01 to 2024-09-30
- winter: 2023-12-01 to 2024-02-28

### Derived Intermediate Data

Generated geospatial layers:
- laubach_feldwege_linien.gpkg
- laubach_feldwege_buffer5m.gpkg

Generated raster products:
- openeo_outputs/s2_summer_raster/openEO.tif
- openeo_outputs/s2_winter_raster/openEO.tif
- openeo_outputs/s1_raster/openEO.tif

Generated tabular data:
- openeo_outputs/laubach_feature_table.csv

## Feature Schema

### Sentinel-2 Feature Columns

Seasonal features:
- NDVI_summer, NDWI_summer, NDBI_summer
- NDVI_winter, NDWI_winter, NDBI_winter

Seasonal deltas:
- NDVI_diff
- NDWI_diff
- NDBI_diff

### Sentinel-1 Feature Columns

Backscatter summary features:
- VV_med, VH_med, VV_VH_ratio_med
- VV_mean, VH_mean, VV_VH_ratio_mean

### OSM and Label Columns

Metadata and weak labels:
- osm_id
- osm_surface
- osm_tracktype
- label_weak

## Weak-Label Mapping

The weak-label strategy maps OSM surface tags to target classes.

Mapping examples:
- asphalt, paved, concrete -> sealed_hard
- compacted, gravel, fine_gravel, unpaved -> unsealed_mineral
- dirt, grass, mud -> vegetated_earthy

Important limitation:
- Weak labels may be noisy and incomplete.
- Unknown or missing OSM surface tags reduce supervision quality.

## Output GIS Data

Final GIS outputs:
- classification_outputs/laubach_feldwege_klassifiziert_linien.gpkg
- classification_outputs/laubach_feldwege_klassifiziert_buffer.gpkg
- classification_outputs/laubach_prediction_table.csv

Styling and distribution resources:
- classification_outputs/feldwege_klassifikation.sld
- laubach_feldwege.qgs
- laubach_qgis_package.zip
