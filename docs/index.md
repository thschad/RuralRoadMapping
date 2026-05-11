# RuralRoadMapping Documentation

Welcome to the project documentation for rural road surface classification in Laubach (35321).

This documentation describes the full implementation pipeline from geodata extraction to model outputs and QGIS distribution.

## Scope

The workflow covers:
- OSM road extraction and geometric preprocessing
- Sentinel-2 and Sentinel-1 feature generation through openEO/CDSE
- Feature engineering and weak-label construction
- Machine learning classification
- GIS export and QGIS project packaging

## Where to Start

If you are new to the project:
1. Read Introduction for architecture and objectives.
2. Read Data for full input and schema details.
3. Read Methods for implementation and modeling details.
4. Use Reproducibility to execute or rebuild outputs.

## Project Status

The workflow has been executed end-to-end and generates a complete output package.
Current bottleneck is model quality, not pipeline stability.
