# Introduction

## Objective

The project builds a reproducible workflow to classify rural roads into surface-related classes using open geodata and Earth observation data.

Target classes:
- sealed_hard
- unsealed_mineral
- vegetated_earthy

## Core Idea

The modeling concept combines two complementary information sources:
- OSM provides where roads are located.
- Sentinel data provides how the road surface behaves spectrally and radiometrically.

## Pipeline Architecture

The implementation is organized into three scripts:

1. 01_osm_extraction_laubach.py
- Queries OSM road segments for Laubach
- Creates line and buffered polygons
- Exports GeoPackage layers for downstream analysis

2. 02_openeo_feature_extraction_laubach.py
- Connects to CDSE openEO
- Builds Sentinel-2 and Sentinel-1 feature products
- Aggregates raster signals to road-segment features
- Produces the project feature table

3. 03_classification_export_laubach.py
- Trains and evaluates ML models
- Predicts road class per segment
- Exports GIS layers, CSV, model files and style resources

## Documentation Design

This documentation follows a training-style structure similar to SETAC-Training:
- compact overview pages
- explicit technical sections for data and methods
- reproducibility-oriented commands
- clear mapping between code and outputs
