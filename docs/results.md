# Results and Outputs

## Model Artifacts

Generated model files:
- classification_outputs/random_forest_laubach.joblib
- classification_outputs/gradient_boosting_laubach.joblib

Evaluation visuals:
- classification_outputs/confusion_matrix.png
- classification_outputs/feature_importance.png

## GIS Deliverables

Classified layers:
- classification_outputs/laubach_feldwege_klassifiziert_linien.gpkg
- classification_outputs/laubach_feldwege_klassifiziert_buffer.gpkg

Tabular predictions:
- classification_outputs/laubach_prediction_table.csv

Styling:
- classification_outputs/feldwege_klassifikation.sld

## QGIS Distribution

Project and package:
- laubach_feldwege.qgs
- laubach_qgis_package.zip

This enables direct viewing and handover in GIS teams without rebuilding the pipeline.

## Current Performance Note

The pipeline is technically stable and reproducible.
Model performance is currently limited by weak-label quality and should be improved with validated training data.
