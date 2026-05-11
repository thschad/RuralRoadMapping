"""
Schritt 2 & 3: Sentinel-2 + Sentinel-1 Feature-Extraktion via openEO (CDSE)
============================================================================
Berechnet spektrale Indizes (NDVI, NDWI, NDBI) und SAR-Backscatter (VV, VH)
für die gepufferten Feldwege-Segmente in Laubach.

Zeitraum: vegetationsarme Periode (Winter) + Sommer → Differenz als Feature

Abhängigkeiten:
    pip install openeo geopandas shapely numpy pandas
    CDSE-Account + Service-Account-Credentials erforderlich
    https://documentation.dataspace.copernicus.eu/APIs/openEO/openEO.html
"""

import json
import openeo
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask as rio_mask
from pathlib import Path
from shapely.geometry import mapping

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
CDSE_URL       = "https://openeo.dataspace.copernicus.eu"
BBOX           = {"west": 8.85, "south": 50.45, "east": 9.10, "north": 50.60}
CRS            = "EPSG:4326"

# Zwei Zeitfenster: Sommer (Vegetationssignal) und Winter (Basislinie)
PERIOD_SUMMER  = ("2024-05-01", "2024-09-30")
PERIOD_WINTER  = ("2023-12-01", "2024-02-28")

MAX_CLOUD_COVER = 20       # % Wolkenbedeckung
BUFFER_GPKG    = "laubach_feldwege_buffer5m.gpkg"
OUT_DIR        = Path("openeo_outputs")
ENABLE_SENTINEL1 = True


# ---------------------------------------------------------------------------
# Verbindung zu CDSE openEO
# ---------------------------------------------------------------------------
def connect_cdse() -> openeo.Connection:
    """
    Authentifizierung über OIDC (Browser-Flow beim ersten Aufruf).
    Alternativ: conn.authenticate_basic(user, password)
    """
    conn = openeo.connect(CDSE_URL)
    conn.authenticate_oidc()
    return conn


# ---------------------------------------------------------------------------
# Sentinel-2 Indizes
# ---------------------------------------------------------------------------
def build_s2_features(conn: openeo.Connection, period: tuple[str, str]) -> openeo.DataCube:
    """
    Lädt Sentinel-2 L2A, maskiert Wolken, berechnet NDVI/NDWI/NDBI
    und gibt den Median-Komposit des Zeitraums zurück.
    """
    s2 = conn.load_collection(
        "SENTINEL2_L2A",
        spatial_extent=BBOX,
        temporal_extent=list(period),
        bands=["B02", "B03", "B04", "B08", "B11", "B12", "SCL"],
        max_cloud_cover=MAX_CLOUD_COVER,
    )

    # Wolkenmaske: SCL-Klassen 3 (Schatten), 8–10 (Wolken)
    scl = s2.band("SCL")
    cloud_mask = (
        (scl == 3) | (scl == 8) | (scl == 9) | (scl == 10)
    )
    s2_masked = s2.mask(cloud_mask)

    # Bandaliase
    blue  = s2_masked.band("B02")
    green = s2_masked.band("B03")
    red   = s2_masked.band("B04")
    nir   = s2_masked.band("B08")
    swir1 = s2_masked.band("B11")
    swir2 = s2_masked.band("B12")

    # Indizes (Ergebnis hat keine bands-Dimension → add_dimension)
    ndvi = (nir - red)  / (nir + red  + 1e-6)
    ndwi = (green - nir)/ (green + nir + 1e-6)
    ndbi = (swir1 - nir)/ (swir1 + nir + 1e-6)

    ndvi_cube = ndvi.add_dimension(name="bands", label="NDVI", type="bands")
    ndwi_cube = ndwi.add_dimension(name="bands", label="NDWI", type="bands")
    ndbi_cube = ndbi.add_dimension(name="bands", label="NDBI", type="bands")

    # Median-Komposit
    cube = ndvi_cube.merge_cubes(ndwi_cube)
    cube = cube.merge_cubes(ndbi_cube)

    return cube.reduce_dimension(dimension="t", reducer="median")


# ---------------------------------------------------------------------------
# Sentinel-1 Backscatter
# ---------------------------------------------------------------------------
def build_s1_features(conn: openeo.Connection, period: tuple[str, str]) -> openeo.DataCube:
    """
    Lädt Sentinel-1 GRD (VV + VH), berechnet Median, Mittelwert und VV/VH-Ratio.
    """
    s1 = conn.load_collection(
        "SENTINEL1_GRD",
        spatial_extent=BBOX,
        temporal_extent=list(period),
        bands=["VV", "VH"],
        properties={
            "sat:orbit_state": lambda orbdir: orbdir == "DESCENDING"
        },
    )

    vv = s1.band("VV")
    vh = s1.band("VH")

    # VV/VH-Ratio (dB-Raum → Differenz; add_dimension nötig nach Band-Arithmetik)
    ratio = vv - vh

    vv_cube    = vv.add_dimension(name="bands", label="VV",          type="bands")
    vh_cube    = vh.add_dimension(name="bands", label="VH",          type="bands")
    ratio_cube = ratio.add_dimension(name="bands", label="VV_VH_ratio", type="bands")

    cube = vv_cube.merge_cubes(vh_cube).merge_cubes(ratio_cube)

    median = cube.reduce_dimension(dimension="t", reducer="median")
    mean   = cube.reduce_dimension(dimension="t", reducer="mean")

    med_renamed = median.rename_labels("bands", ["VV_med", "VH_med", "VV_VH_ratio_med"])
    mean_renamed = mean.rename_labels( "bands", ["VV_mean", "VH_mean", "VV_VH_ratio_mean"])

    return med_renamed.merge_cubes(mean_renamed)


# ---------------------------------------------------------------------------
# Raster-Export via openEO Batch Job
# ---------------------------------------------------------------------------
def export_raster(
    conn: openeo.Connection,
    cube: openeo.DataCube,
    out_name: str,
) -> Path:
    """
    Exportiert den Cube als GeoTIFF via CDSE Batch Job.
    Gibt den Pfad zum heruntergeladenen GeoTIFF zurück.
    """
    OUT_DIR.mkdir(exist_ok=True)
    out_dir = OUT_DIR / out_name
    out_dir.mkdir(exist_ok=True)

    existing_tiffs = list(out_dir.glob("*.tif")) + list(out_dir.glob("*.tiff"))
    if existing_tiffs:
        print(f"    Vorhandenes Raster gefunden: {existing_tiffs[0]}")
        return existing_tiffs[0]

    job = cube.create_job(
        title=f"Laubach Feldwege – {out_name}",
        out_format="GTiff",
        job_options={"tile_grid": "wgs84-1deg"},
    )
    print(f"    Job {job.job_id} gestartet …")
    job.start_and_wait()
    job.get_results().download_files(str(out_dir))
    # Ersten GeoTIFF-Datei zurückgeben
    tiffs = list(out_dir.glob("*.tif")) + list(out_dir.glob("*.tiff"))
    if not tiffs:
        raise FileNotFoundError(f"Kein GeoTIFF in {out_dir}")
    print(f"    Raster gespeichert: {tiffs[0]}")
    return tiffs[0]


# ---------------------------------------------------------------------------
# Lokale Zonal Statistics mit rasterstats
# ---------------------------------------------------------------------------
def compute_zonal_stats(
    tiff_path: Path,
    segments: gpd.GeoDataFrame,
    band_names: list[str],
) -> pd.DataFrame:
    """
    Berechnet Mittelwert pro Polygon mit reinem rasterio (kein fiona/rasterstats).
    """
    segs_wgs84 = segments.to_crs("EPSG:4326")
    all_stats: dict[str, list] = {"segment_idx": list(range(len(segs_wgs84)))}

    with rasterio.open(tiff_path) as src:
        n_bands = src.count
        band_names_used = band_names[:n_bands]
        for band_name in band_names_used:
            all_stats[band_name] = []

        for _, row in segs_wgs84.iterrows():
            geom = [mapping(row.geometry)]
            try:
                out_image, _ = rio_mask(src, geom, crop=True, nodata=np.nan, filled=True)
                for b_idx, band_name in enumerate(band_names_used):
                    data = out_image[b_idx].astype(float)
                    nodata = src.nodata
                    if nodata is not None:
                        data[data == nodata] = np.nan
                    mean_val = float(np.nanmean(data)) if not np.all(np.isnan(data)) else np.nan
                    all_stats[band_name].append(mean_val)
            except Exception:
                for band_name in band_names_used:
                    all_stats[band_name].append(np.nan)

    return pd.DataFrame(all_stats)


# ---------------------------------------------------------------------------
# Gesamtergebnis zusammenführen
# ---------------------------------------------------------------------------
S2_BANDS  = ["NDVI", "NDWI", "NDBI"]
S1_BANDS  = ["VV_med", "VH_med", "VV_VH_ratio_med",
             "VV_mean", "VH_mean", "VV_VH_ratio_mean"]


def merge_features(
    segments: gpd.GeoDataFrame,
    s2_summer_tiff: Path,
    s2_winter_tiff: Path,
    s1_tiff: Path | None,
) -> pd.DataFrame:
    """
    Berechnet Zonal Stats aus GeoTIFFs lokal und erstellt Feature-Tabelle.
    """
    print("  Berechne Zonal Stats S2 Sommer …")
    df_s2s = compute_zonal_stats(s2_summer_tiff, segments, S2_BANDS)
    df_s2s = df_s2s.add_suffix("_summer").rename(columns={"segment_idx_summer": "segment_idx"})

    print("  Berechne Zonal Stats S2 Winter …")
    df_s2w = compute_zonal_stats(s2_winter_tiff, segments, S2_BANDS)
    df_s2w = df_s2w.add_suffix("_winter").rename(columns={"segment_idx_winter": "segment_idx"})

    df = df_s2s.merge(df_s2w, on="segment_idx")

    if s1_tiff is not None:
        print("  Berechne Zonal Stats S1 …")
        df_s1 = compute_zonal_stats(s1_tiff, segments, S1_BANDS)
        df = df.merge(df_s1, on="segment_idx")
    else:
        print("  S1 übersprungen – verwende nur Sentinel-2 Features")

    # Saisondifferenz als zusätzliches Feature
    for idx in ["NDVI", "NDWI", "NDBI"]:
        df[f"{idx}_diff"] = df[f"{idx}_summer"] - df[f"{idx}_winter"]

    # OSM-Label als schwaches Ziel-Label
    label_map = {
        "asphalt": "versiegelt",
        "paved":   "versiegelt",
        "concrete":"versiegelt",
        "compacted":   "mineralisch",
        "gravel":      "mineralisch",
        "fine_gravel": "mineralisch",
        "dirt":  "begrünt_erdig",
        "grass": "begrünt_erdig",
        "mud":   "begrünt_erdig",
        "unpaved": "mineralisch",
    }
    segs = segments.reset_index(drop=True)
    df["osm_surface"]  = segs["surface"]
    df["osm_tracktype"]= segs["tracktype"]
    df["osm_id"]       = segs["osm_id"]
    df["label_weak"]   = segs["surface"].map(label_map).fillna("unbekannt")

    out_csv = OUT_DIR / "laubach_feature_table.csv"
    df.to_csv(out_csv, index=False)
    print(f"  Feature-Tabelle: {out_csv}")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(exist_ok=True)

    # Gepufferte Segmente laden
    if not Path(BUFFER_GPKG).exists():
        raise FileNotFoundError(
            f"{BUFFER_GPKG} nicht gefunden – bitte zuerst 01_osm_extraction_laubach.py ausführen."
        )
    segments = gpd.read_file(BUFFER_GPKG, layer="feldwege_buffer")
    print(f"  {len(segments)} Segmente geladen")

    # Verbindung
    conn = connect_cdse()

    # Sentinel-2 Cubes
    print("Baue Sentinel-2 Sommer-Cube …")
    s2_summer = build_s2_features(conn, PERIOD_SUMMER)

    print("Baue Sentinel-2 Winter-Cube …")
    s2_winter = build_s2_features(conn, PERIOD_WINTER)

    s1_tiff = None
    if ENABLE_SENTINEL1:
        try:
            print("Baue Sentinel-1 Cube …")
            s1_cube = build_s1_features(conn, PERIOD_SUMMER)

            print("Starte openEO Batch-Job: S1 …")
            s1_tiff = export_raster(conn, s1_cube, "s1_raster")
        except Exception as exc:
            print(f"S1-Export fehlgeschlagen, fahre mit Sentinel-2-only fort: {exc}")
    else:
        print("Sentinel-1 ist deaktiviert – fahre mit Sentinel-2-only fort")

    # Raster-Export via openEO Batch Jobs
    print("Starte openEO Batch-Job: S2 Sommer …")
    s2s_tiff = export_raster(conn, s2_summer, "s2_summer_raster")

    print("Starte openEO Batch-Job: S2 Winter …")
    s2w_tiff = export_raster(conn, s2_winter, "s2_winter_raster")

    # Lokale Zonal Statistics + Feature-Tabelle
    print("Erstelle Feature-Tabelle …")
    df = merge_features(segments, s2s_tiff, s2w_tiff, s1_tiff)
    print(df.head())


if __name__ == "__main__":
    main()
