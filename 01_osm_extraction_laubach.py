"""
Schritt 1: OSM-Extraktion – Feldwege Gemeinde Laubach (35321)
=============================================================
Extrahiert highway=track/path/service aus OSM via Overpass API,
puffert die Segmente (5 m) und speichert als GeoPackage.

Abhängigkeiten:
    pip install requests geopandas shapely pyproj
"""

import json
import time
import requests
import geopandas as gpd
from shapely.geometry import LineString, shape
from shapely.ops import transform
import pyproj

# ---------------------------------------------------------------------------
# Bounding Box Laubach, Hessen (PLZ 35321)
# ---------------------------------------------------------------------------
BBOX = {
    "south": 50.45,
    "west":  8.85,
    "north": 50.60,
    "east":  9.10,
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OSM_HIGHWAY_TYPES = ["track", "path", "service", "unclassified", "tertiary"]

# ---------------------------------------------------------------------------
# Overpass-Query
# ---------------------------------------------------------------------------
def build_overpass_query(bbox: dict, highway_types: list[str]) -> str:
    union_parts = "\n".join(
        f'  way["highway"="{hw}"]({bbox["south"]},{bbox["west"]},{bbox["north"]},{bbox["east"]});'
        for hw in highway_types
    )
    return f"""
[out:json][timeout:60];
(
{union_parts}
);
out body;
>;
out skel qt;
"""


def fetch_osm_ways(query: str) -> dict:
    headers = {
        "User-Agent": "LandwerkFeldwegeClassifier/1.0 (landwerk@example.org)",
        "Accept": "application/json",
    }
    resp = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=90)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Geometrie aufbauen
# ---------------------------------------------------------------------------
def parse_osm_to_geodataframe(osm_data: dict) -> gpd.GeoDataFrame:
    nodes = {
        el["id"]: (el["lon"], el["lat"])
        for el in osm_data["elements"]
        if el["type"] == "node"
    }

    records = []
    for el in osm_data["elements"]:
        if el["type"] != "way":
            continue
        coords = [nodes[nid] for nid in el["nodes"] if nid in nodes]
        if len(coords) < 2:
            continue
        tags = el.get("tags", {})
        records.append(
            {
                "osm_id":    el["id"],
                "highway":   tags.get("highway", "unknown"),
                "surface":   tags.get("surface", "unknown"),
                "tracktype": tags.get("tracktype", "unknown"),
                "name":      tags.get("name", ""),
                "geometry":  LineString(coords),
            }
        )

    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    return gdf


# ---------------------------------------------------------------------------
# Puffern (5 m) in metrischem CRS
# ---------------------------------------------------------------------------
def buffer_segments(gdf: gpd.GeoDataFrame, buffer_m: float = 5.0) -> gpd.GeoDataFrame:
    gdf_utm = gdf.to_crs("EPSG:25832")          # UTM Zone 32N (Hessen)
    gdf_utm["geometry"] = gdf_utm.geometry.buffer(buffer_m, cap_style=2)
    return gdf_utm.to_crs("EPSG:4326")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Lade OSM-Daten für Laubach (35321) …")
    query = build_overpass_query(BBOX, OSM_HIGHWAY_TYPES)
    osm_data = fetch_osm_ways(query)

    gdf = parse_osm_to_geodataframe(osm_data)
    print(f"  {len(gdf)} Wegsegmente geladen")

    gdf_buffered = buffer_segments(gdf, buffer_m=5)

    out_lines    = "laubach_feldwege_linien.gpkg"
    out_buffered = "laubach_feldwege_buffer5m.gpkg"

    gdf.to_file(out_lines,    driver="GPKG", layer="feldwege")
    gdf_buffered.to_file(out_buffered, driver="GPKG", layer="feldwege_buffer")

    print(f"  Gespeichert: {out_lines}")
    print(f"  Gespeichert: {out_buffered}")
    return gdf, gdf_buffered


if __name__ == "__main__":
    gdf, gdf_buf = main()
