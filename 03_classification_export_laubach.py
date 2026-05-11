"""
Schritt 4 & 5: ML-Klassifikation + GeoPackage-Export
=====================================================
Trainiert einen Random Forest auf den extrahierten Features,
klassifiziert alle Wegsegmente und exportiert das Ergebnis als GeoPackage.

Klassen:
    0 – versiegelt/hart   (Asphalt, Beton, Pflaster)
    1 – mineralisch       (Schotter, Kies, Kompaktierung)
    2 – begrünt/erdig     (Gras, Erde, unbefestigt)

Abhängigkeiten:
    pip install scikit-learn pandas geopandas matplotlib seaborn
"""

import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from sklearn.inspection import permutation_importance
import joblib

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------
FEATURE_CSV  = Path("openeo_outputs/laubach_feature_table.csv")
BUFFER_GPKG  = Path("laubach_feldwege_buffer5m.gpkg")
LINE_GPKG    = Path("laubach_feldwege_linien.gpkg")
OUT_DIR      = Path("classification_outputs")

CLASS_NAMES  = ["versiegelt", "mineralisch", "begrünt_erdig"]
CLASS_COLORS = {
    "versiegelt":   "#636363",  # grau
    "mineralisch":  "#d7b48b",  # sandfarben
    "begrünt_erdig":"#74c476",  # grün
}

# ---------------------------------------------------------------------------
# Feature-Spalten (Auswahl)
# ---------------------------------------------------------------------------
FEATURE_COLS = [
    "NDVI_summer", "NDWI_summer", "NDBI_summer",
    "NDVI_winter", "NDWI_winter", "NDBI_winter",
    "NDVI_diff",   "NDWI_diff",   "NDBI_diff",
    "VV_med",  "VH_med",  "VV_VH_ratio_med",
    "VV_mean", "VH_mean", "VV_VH_ratio_mean",
]

# ---------------------------------------------------------------------------
# Daten laden & vorbereiten
# ---------------------------------------------------------------------------
def load_and_prepare(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, LabelEncoder]:
    df = pd.read_csv(path)

    # Nur Segmente mit bekanntem Label
    labeled = df[df["label_weak"] != "unbekannt"].copy()
    unlabeled = df[df["label_weak"] == "unbekannt"].copy()

    le = LabelEncoder()
    le.fit(CLASS_NAMES)
    labeled["label_enc"] = le.transform(labeled["label_weak"])

    print(f"  Labeled:   {len(labeled)} Segmente")
    print(f"  Unlabeled: {len(unlabeled)} Segmente")
    print(f"  Klassenverteilung:\n{labeled['label_weak'].value_counts()}")
    return labeled, unlabeled, le


def get_xy(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available].fillna(0).values
    y = df["label_enc"].values if "label_enc" in df.columns else None
    return X, y


# ---------------------------------------------------------------------------
# Modell trainieren
# ---------------------------------------------------------------------------
def train_random_forest(X: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    # Kreuzvalidierung (stratifiziert, 5-fold)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(rf, X, y, cv=cv, scoring="f1_macro")
    print(f"  CV F1-macro: {scores.mean():.3f} ± {scores.std():.3f}")

    rf.fit(X, y)
    return rf


def train_gradient_boosting(X: np.ndarray, y: np.ndarray) -> GradientBoostingClassifier:
    """Alternativmodell – besser bei kleinen Datensätzen."""
    gb = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42,
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(gb, X, y, cv=cv, scoring="f1_macro")
    print(f"  GBM CV F1-macro: {scores.mean():.3f} ± {scores.std():.3f}")
    gb.fit(X, y)
    return gb


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate(model, X: np.ndarray, y: np.ndarray, le: LabelEncoder, out_dir: Path):
    y_pred = model.predict(X)
    labels = le.classes_

    print("\nKlassifikationsbericht:")
    print(classification_report(y, y_pred, target_names=labels))

    # Konfusionsmatrix
    cm = confusion_matrix(y, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax, colorbar=False)
    ax.set_title("Konfusionsmatrix – Feldwegklassifikation Laubach")
    fig.tight_layout()
    fig.savefig(out_dir / "confusion_matrix.png", dpi=150)
    plt.close(fig)
    print(f"  Konfusionsmatrix: {out_dir / 'confusion_matrix.png'}")


def plot_feature_importance(model, feature_names: list[str], out_dir: Path):
    importances = model.feature_importances_
    indices     = np.argsort(importances)[::-1]
    sorted_names = [feature_names[i] for i in indices]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(sorted_names[::-1], importances[indices[::-1]], color="#4292c6")
    ax.set_xlabel("Feature Importance (Gini)")
    ax.set_title("Feature-Bedeutung – Random Forest")
    fig.tight_layout()
    fig.savefig(out_dir / "feature_importance.png", dpi=150)
    plt.close(fig)
    print(f"  Feature-Importance: {out_dir / 'feature_importance.png'}")


# ---------------------------------------------------------------------------
# Vorhersage + Export
# ---------------------------------------------------------------------------
def predict_and_export(
    model,
    labeled: pd.DataFrame,
    unlabeled: pd.DataFrame,
    le: LabelEncoder,
    segments: gpd.GeoDataFrame,
    lines: gpd.GeoDataFrame,
    out_dir: Path,
):
    all_df = pd.concat([labeled, unlabeled], ignore_index=True)
    available = [c for c in FEATURE_COLS if c in all_df.columns]
    X_all = all_df[available].fillna(0).values

    proba = model.predict_proba(X_all)
    pred  = model.predict(X_all)

    all_df["class_id"]    = pred
    all_df["class_label"] = le.inverse_transform(pred)
    all_df["confidence"]  = proba.max(axis=1).round(3)
    for i, cls in enumerate(le.classes_):
        all_df[f"prob_{cls}"] = proba[:, i].round(3)

    # Geometrie aus gepuffertem GeoPackage zuordnen
    segs = segments.reset_index(drop=True)
    result_buf = segs.copy()
    for col in ["class_id", "class_label", "confidence",
                "prob_versiegelt", "prob_mineralisch", "prob_begrünt_erdig",
                "osm_surface", "osm_tracktype"]:
        if col in all_df.columns:
            result_buf[col] = all_df[col].values

    # Linien-GeoPackage ebenfalls anreichern
    result_lines = lines.reset_index(drop=True).copy()
    for col in ["class_label", "confidence"]:
        if col in all_df.columns:
            result_lines[col] = all_df[col].values

    # Export
    buf_out   = out_dir / "laubach_feldwege_klassifiziert_buffer.gpkg"
    lines_out = out_dir / "laubach_feldwege_klassifiziert_linien.gpkg"

    result_buf.to_file(str(buf_out),   driver="GPKG", layer="feldwege_buffer")
    result_lines.to_file(str(lines_out), driver="GPKG", layer="feldwege")

    print(f"  GeoPackage (Puffer): {buf_out}")
    print(f"  GeoPackage (Linien): {lines_out}")

    # CSV-Vorhersagetabelle
    csv_out = out_dir / "laubach_prediction_table.csv"
    all_df[["osm_id", "osm_surface", "osm_tracktype",
            "class_label", "confidence",
            "prob_versiegelt", "prob_mineralisch", "prob_begrünt_erdig"]].to_csv(
        csv_out, index=False
    )
    print(f"  Vorhersage-CSV: {csv_out}")

    return result_lines


# ---------------------------------------------------------------------------
# QGIS-Stil (SLD) generieren
# ---------------------------------------------------------------------------
def export_qgis_sld(out_dir: Path):
    sld_rules = ""
    for cls, color in CLASS_COLORS.items():
        sld_rules += f"""
    <Rule>
      <Name>{cls}</Name>
      <ogc:Filter>
        <ogc:PropertyIsEqualTo>
          <ogc:PropertyName>class_label</ogc:PropertyName>
          <ogc:Literal>{cls}</ogc:Literal>
        </ogc:PropertyIsEqualTo>
      </ogc:Filter>
      <LineSymbolizer>
        <Stroke>
          <CssParameter name="stroke">{color}</CssParameter>
          <CssParameter name="stroke-width">2</CssParameter>
        </Stroke>
      </LineSymbolizer>
    </Rule>"""

    sld = f"""<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
  xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>Feldwege Laubach</Name>
    <UserStyle>
      <Title>Feldweg-Klassifikation</Title>
      <FeatureTypeStyle>
        {sld_rules}
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

    sld_path = out_dir / "feldwege_klassifikation.sld"
    sld_path.write_text(sld, encoding="utf-8")
    print(f"  QGIS-SLD: {sld_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(exist_ok=True)

    if not FEATURE_CSV.exists():
        raise FileNotFoundError(
            f"{FEATURE_CSV} nicht gefunden – bitte zuerst 02_openeo_feature_extraction_laubach.py ausführen."
        )

    print("Lade Feature-Tabelle …")
    labeled, unlabeled, le = load_and_prepare(FEATURE_CSV)

    X_train, y_train = get_xy(labeled)

    print("\nTrainiere Random Forest …")
    rf = train_random_forest(X_train, y_train)

    print("\nTrainiere Gradient Boosting (Vergleich) …")
    gb = train_gradient_boosting(X_train, y_train)

    print("\nEvaluation Random Forest (In-Sample) …")
    available = [c for c in FEATURE_COLS if c in labeled.columns]
    evaluate(rf, X_train, y_train, le, OUT_DIR)

    plot_feature_importance(rf, available, OUT_DIR)

    # Modelle speichern
    joblib.dump(rf, OUT_DIR / "random_forest_laubach.joblib")
    joblib.dump(gb, OUT_DIR / "gradient_boosting_laubach.joblib")
    print(f"  Modelle gespeichert: {OUT_DIR}/")

    # Geometrien laden
    segments = gpd.read_file(str(BUFFER_GPKG), layer="feldwege_buffer")
    lines    = gpd.read_file(str(LINE_GPKG),   layer="feldwege")

    print("\nKlassifiziere alle Segmente & exportiere …")
    result = predict_and_export(rf, labeled, unlabeled, le, segments, lines, OUT_DIR)

    print("\nExportiere QGIS-SLD …")
    export_qgis_sld(OUT_DIR)

    print("\nFertig. Outputs in:", OUT_DIR)


if __name__ == "__main__":
    main()
