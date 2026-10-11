"""
Heavy Metal Pollution Index (HMPI / HPI) Calculation Engine
===========================================================
Implements the Heavy Metal Pollution Index based on standard environmental
assessment methodology (Mohan et al., 1996; Prasad & Bose, 2001).

Formulation:
  1. Unit Weight (Wi):
       Wi = (1 / Si) / sum(1 / Sj for all j)
       where Si is the permissible standard for metal i.
  2. Quality Rating / Sub-index (Qi):
       Qi = (|Mi - Ii| / (Si - Ii)) * 100
       where Mi is the monitored concentration,
             Ii is the ideal permissible limit (typically 0 for toxic metals),
             Si is the standard permissible limit.
  3. HMPI:
       HMPI = sum(Wi * Qi) / sum(Wi)  (sum(Wi) == 1 when normalized)
  4. Categorization:
       - Low: HMPI < threshold_low (default 50)
       - Moderate: threshold_low <= HMPI <= threshold_high (default 50 to 100)
       - High: HMPI > threshold_high (default > 100)
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


# Default standard permissible limits according to WHO / BIS (in mg/L)
DEFAULT_STANDARDS: Dict[str, float] = {
    "Pb": 0.010,   # Lead (WHO/BIS: 0.01 mg/L)
    "Cd": 0.003,   # Cadmium (WHO/BIS: 0.003 mg/L)
    "Cr": 0.050,   # Chromium (WHO/BIS: 0.05 mg/L)
    "Ni": 0.020,   # Nickel (WHO/BIS: 0.02 mg/L)
    "Zn": 3.000,   # Zinc (WHO/BIS: 3.0 mg/L)
    "Cu": 1.000,   # Copper (WHO/BIS: 1.0 mg/L)
    "As": 0.010,   # Arsenic (WHO: 0.01 mg/L)
    "Fe": 0.300,   # Iron (BIS: 0.3 mg/L)
    "Mn": 0.100,   # Manganese (WHO: 0.1 mg/L)
    "Hg": 0.001,   # Mercury (WHO/BIS: 0.001 mg/L)
}

# Default ideal concentrations (Ii) in mg/L (typically 0.0 for toxic heavy metals)
DEFAULT_IDEAL_VALUES: Dict[str, float] = {
    metal: 0.0 for metal in DEFAULT_STANDARDS
}

# Category colors & labels
CATEGORY_COLORS = {
    "Low": {"hex": "#28a745", "rgba": [40, 167, 69, 210], "badge": "🟢 Low"},
    "Moderate": {"hex": "#ff9800", "rgba": [255, 152, 0, 220], "badge": "🟠 Moderate"},
    "High": {"hex": "#dc3545", "rgba": [220, 53, 69, 230], "badge": "🔴 High"},
}


def calculate_weights(standards: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate unit weights (Wi) inversely proportional to permissible limits (Si).
    Wi = (1 / Si) / sum(1 / Sj)
    """
    inv_sum = sum(1.0 / limit for limit in standards.values() if limit > 0)
    if inv_sum == 0:
        raise ValueError("Invalid standards: sum of inverse limits cannot be zero.")
    return {metal: (1.0 / limit) / inv_sum for metal, limit in standards.items()}


def detect_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Automatically identify site name, latitude, longitude, and candidate metal columns.
    """
    cols = df.columns.tolist()
    lower_map = {str(c).strip().lower(): c for c in cols}

    # Detect site name
    site_candidates = ["site", "site_name", "sitename", "station", "station_name", "location", "sample_id", "name"]
    site_col = None
    for cand in site_candidates:
        if cand in lower_map:
            site_col = lower_map[cand]
            break
    if not site_col:
        # Fallback to first text column
        for c in cols:
            if df[c].dtype == object or pd.api.types.is_string_dtype(df[c]):
                site_col = c
                break
        if not site_col and len(cols) > 0:
            site_col = cols[0]

    # Detect latitude
    lat_candidates = ["lat", "latitude", "y", "site_lat", "lat_dd", "latdd"]
    lat_col = None
    for cand in lat_candidates:
        if cand in lower_map:
            lat_col = lower_map[cand]
            break

    # Detect longitude
    lon_candidates = ["lon", "long", "longitude", "x", "site_lon", "lon_dd", "londd"]
    lon_col = None
    for cand in lon_candidates:
        if cand in lower_map:
            lon_col = lower_map[cand]
            break

    # Detect metal columns
    known_metals = set(DEFAULT_STANDARDS.keys())
    metal_cols = []
    for c in cols:
        clean_c = str(c).strip()
        # Direct match or casing match
        matched = False
        for km in known_metals:
            if clean_c.upper() == km.upper() or clean_c.upper().startswith(f"{km.upper()}_") or clean_c.upper().startswith(f"{km.upper()} ("):
                metal_cols.append(c)
                matched = True
                break
        if not matched and c not in [site_col, lat_col, lon_col]:
            # Check if numeric
            if pd.api.types.is_numeric_dtype(df[c]):
                metal_cols.append(c)

    return {
        "site_col": site_col,
        "lat_col": lat_col,
        "lon_col": lon_col,
        "metal_cols": metal_cols,
    }


def validate_input_data(
    df: pd.DataFrame,
    site_col: str,
    lat_col: str,
    lon_col: str,
    metal_cols: List[str]
) -> Tuple[bool, List[str], pd.DataFrame]:
    """
    Validate the uploaded dataset for required columns, data types, and value sanity.
    Returns (is_valid, error_or_warning_messages, cleaned_dataframe).
    """
    messages = []
    
    if df.empty:
        return False, ["Dataset is empty."], df

    # Check existence
    missing = [c for c in [site_col, lat_col, lon_col] + metal_cols if c not in df.columns]
    if missing:
        return False, [f"Missing required columns in dataset: {', '.join(missing)}"], df

    if not metal_cols:
        return False, ["Please select at least one metal column to calculate HMPI."], df

    cleaned_df = df.copy()

    # Clean Lat/Lon
    try:
        cleaned_df[lat_col] = pd.to_numeric(cleaned_df[lat_col], errors="coerce")
        cleaned_df[lon_col] = pd.to_numeric(cleaned_df[lon_col], errors="coerce")
    except Exception as e:
        messages.append(f"Could not parse latitude/longitude as numeric: {str(e)}")

    invalid_coords = cleaned_df[lat_col].isna() | cleaned_df[lon_col].isna()
    if invalid_coords.any():
        n_invalid = int(invalid_coords.sum())
        messages.append(f"Warning: {n_invalid} row(s) have invalid or missing latitude/longitude.")

    # Validate coordinate range
    out_of_bounds = (
        (cleaned_df[lat_col] < -90) | (cleaned_df[lat_col] > 90) |
        (cleaned_df[lon_col] < -180) | (cleaned_df[lon_col] > 180)
    )
    if out_of_bounds.any():
        messages.append(f"Warning: {int(out_of_bounds.sum())} row(s) have latitude outside [-90, 90] or longitude outside [-180, 180].")

    # Clean Metals
    for m in metal_cols:
        cleaned_df[m] = pd.to_numeric(cleaned_df[m], errors="coerce")
        neg_count = (cleaned_df[m] < 0).sum()
        if neg_count > 0:
            messages.append(f"Warning: Column '{m}' contains {neg_count} negative value(s). Replaced with 0.")
            cleaned_df[m] = cleaned_df[m].clip(lower=0)

        nan_count = cleaned_df[m].isna().sum()
        if nan_count > 0:
            messages.append(f"Notice: Column '{m}' contains {nan_count} missing/non-numeric value(s). Imputed with 0.")
            cleaned_df[m] = cleaned_df[m].fillna(0.0)

    # Clean Site
    cleaned_df[site_col] = cleaned_df[site_col].astype(str).fillna("Unknown Site")

    return True, messages, cleaned_df


def compute_hmpi(
    df: pd.DataFrame,
    site_col: str,
    lat_col: str,
    lon_col: str,
    metal_cols: List[str],
    standards: Dict[str, float],
    ideal_values: Optional[Dict[str, float]] = None,
    threshold_low: float = 50.0,
    threshold_high: float = 100.0,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform the complete HMPI calculation on the dataset.
    Returns:
      (result_df, summary_metadata)
    """
    if ideal_values is None:
        ideal_values = {m: 0.0 for m in metal_cols}

    # Ensure standards exist for each selected metal
    filtered_standards = {}
    for m in metal_cols:
        val = standards.get(m, DEFAULT_STANDARDS.get(m.upper(), 1.0))
        if val <= 0:
            val = 1.0
        filtered_standards[m] = val

    filtered_ideals = {m: ideal_values.get(m, 0.0) for m in metal_cols}

    # 1. Weights
    weights = calculate_weights(filtered_standards)

    result_df = df.copy()

    # Sub-indices Qi and weighted sub-indices Wi * Qi
    qi_cols = []
    w_qi_cols = []
    contrib_pct_cols = []

    for m in metal_cols:
        si = filtered_standards[m]
        ii = filtered_ideals[m]
        wi = weights[m]

        # Qi = (|Mi - Ii| / (Si - Ii)) * 100
        denom = (si - ii) if (si - ii) != 0 else 1.0
        qi_series = (result_df[m] - ii).abs() / denom * 100.0
        w_qi_series = wi * qi_series

        qi_col = f"Q_{m}"
        w_qi_col = f"W_Q_{m}"

        result_df[qi_col] = qi_series.round(3)
        result_df[w_qi_col] = w_qi_series.round(4)

        qi_cols.append(qi_col)
        w_qi_cols.append(w_qi_col)

    # Overall HMPI = sum(Wi * Qi)
    result_df["HMPI"] = result_df[w_qi_cols].sum(axis=1).round(2)

    # Relative contribution per metal (%)
    for m in metal_cols:
        pct_col = f"Contrib_{m}_pct"
        result_df[pct_col] = np.where(
            result_df["HMPI"] > 0,
            (result_df[f"W_Q_{m}"] / result_df["HMPI"] * 100.0).round(2),
            0.0
        )
        contrib_pct_cols.append(pct_col)

    # Categorization
    def categorize(hpi: float) -> str:
        if hpi < threshold_low:
            return "Low"
        elif hpi <= threshold_high:
            return "Moderate"
        else:
            return "High"

    result_df["Category"] = result_df["HMPI"].apply(categorize)
    result_df["Color_Hex"] = result_df["Category"].apply(lambda c: CATEGORY_COLORS[c]["hex"])
    result_df["Color_RGBA"] = result_df["Category"].apply(lambda c: CATEGORY_COLORS[c]["rgba"])

    # Dominant pollutant metal for each site
    metal_wqi_df = result_df[w_qi_cols]
    dominant_metals = []
    for idx, row in metal_wqi_df.iterrows():
        if row.max() > 0:
            top_col = row.idxmax()
            top_metal = top_col.replace("W_Q_", "")
            dominant_metals.append(top_metal)
        else:
            dominant_metals.append("None")
    result_df["Dominant_Metal"] = dominant_metals

    # Summary statistics
    total_sites = len(result_df)
    cat_counts = result_df["Category"].value_counts().to_dict()
    low_count = cat_counts.get("Low", 0)
    mod_count = cat_counts.get("Moderate", 0)
    high_count = cat_counts.get("High", 0)

    # Average HMPI and metal contribution overall
    avg_hmpi = float(result_df["HMPI"].mean()) if total_sites > 0 else 0.0
    max_hmpi = float(result_df["HMPI"].max()) if total_sites > 0 else 0.0
    min_hmpi = float(result_df["HMPI"].min()) if total_sites > 0 else 0.0

    # Highest pollution site
    if total_sites > 0:
        max_site_row = result_df.loc[result_df["HMPI"].idxmax()]
        highest_site_name = str(max_site_row[site_col])
    else:
        highest_site_name = "N/A"

    # Overall average metal contribution
    avg_metal_contrib = {}
    for m in metal_cols:
        avg_metal_contrib[m] = float(result_df[f"W_Q_{m}"].mean())

    summary = {
        "total_sites": total_sites,
        "category_counts": {
            "Low": low_count,
            "Moderate": mod_count,
            "High": high_count,
        },
        "category_percentages": {
            "Low": round((low_count / total_sites * 100), 1) if total_sites > 0 else 0,
            "Moderate": round((mod_count / total_sites * 100), 1) if total_sites > 0 else 0,
            "High": round((high_count / total_sites * 100), 1) if total_sites > 0 else 0,
        },
        "avg_hmpi": round(avg_hmpi, 2),
        "min_hmpi": round(min_hmpi, 2),
        "max_hmpi": round(max_hmpi, 2),
        "highest_site_name": highest_site_name,
        "weights": weights,
        "standards": filtered_standards,
        "ideals": filtered_ideals,
        "avg_metal_contrib": avg_metal_contrib,
        "metal_cols": metal_cols,
        "thresholds": {"low": threshold_low, "high": threshold_high},
    }

    return result_df, summary
