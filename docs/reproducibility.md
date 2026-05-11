# Reproducibility

## Environment Setup

Use Python and install dependencies:

```powershell
pip install -r requirements.txt
pip install mkdocs mkdocs-material
```

## Run the Full Workflow

```powershell
python 01_osm_extraction_laubach.py
python 02_openeo_feature_extraction_laubach.py
python 03_classification_export_laubach.py
./create_qgis_package.ps1
```

## Build and Preview Documentation

```powershell
mkdocs serve
```

Then open the local URL shown in the terminal.

For static site build:

```powershell
mkdocs build
```

## Rebuild Notes

- openEO authentication may require browser login depending on token state.
- Existing raster outputs are reused by default when present.
- QGIS package can be recreated anytime using the packaging script.
