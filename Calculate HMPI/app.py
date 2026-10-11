"""
Heavy Metal Pollution Index (HMPI) Monitoring and Visualization System
=======================================================================
Streamlit Web Application for environmental monitoring, spatial hotspot
visualization with PyDeck, per-metal pollution analysis, and report export.
"""

import io
import json
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import altair as alt

from hmpi_engine import (
    DEFAULT_STANDARDS,
    DEFAULT_IDEAL_VALUES,
    CATEGORY_COLORS,
    detect_columns,
    validate_input_data,
    compute_hmpi,
    calculate_weights,
)

# Page configuration
st.set_page_config(
    page_title="HMPI Monitoring & Visualization System",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished environmental dashboard styling
st.markdown("""
<style>
    /* Metric card improvements */
    [data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        font-weight: 600;
        color: #4b5563;
    }
    
    /* Custom info cards */
    .metric-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border-left: 5px solid #3b82f6;
        margin-bottom: 12px;
    }
    .metric-card-low {
        border-left-color: #28a745 !important;
    }
    .metric-card-mod {
        border-left-color: #ff9800 !important;
    }
    .metric-card-high {
        border-left-color: #dc3545 !important;
    }
    
    /* Category Badges */
    .badge-low {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-mod {
        background-color: #fff3cd;
        color: #856404;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-high {
        background-color: #f8d7da;
        color: #721c24;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        display: inline-block;
    }

    /* Subtitle and header styling */
    .header-subtext {
        color: #4b5563;
        font-size: 1.05rem;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    
    /* Clean tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "df_raw" not in st.session_state:
    st.session_state["df_raw"] = None
if "data_source_name" not in st.session_state:
    st.session_state["data_source_name"] = None
if "custom_standards" not in st.session_state:
    st.session_state["custom_standards"] = DEFAULT_STANDARDS.copy()


def load_sample_dataset():
    """Load pre-packaged sample dataset."""
    try:
        sample_df = pd.read_csv("sample_data.csv")
        st.session_state["df_raw"] = sample_df
        st.session_state["data_source_name"] = "Sample Dataset (25 Environmental Sites)"
    except Exception as e:
        st.error(f"Error loading sample dataset: {e}")


# ==============================================================================
# SIDEBAR: DATA UPLOAD & CONFIGURATION
# ==============================================================================
with st.sidebar:
    st.title("⚙️ HMPI Configuration")
    st.caption("Heavy Metal Pollution Index Setup")

    st.markdown("---")
    st.subheader("1. 📂 Data Ingestion")

    # Sample dataset quick loader button
    col_s1, col_s2 = st.columns([1, 1])
    with col_s1:
        if st.button("🚀 Load Sample", use_container_width=True, help="Load built-in 25-site environmental monitoring dataset"):
            load_sample_dataset()
    with col_s2:
        try:
            with open("sample_data.csv", "rb") as f:
                st.download_button(
                    label="📥 Sample CSV",
                    data=f.read(),
                    file_name="hmpi_sample_template.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Download sample data CSV template"
                )
        except Exception:
            pass

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload environmental monitoring data containing site name, latitude, longitude, and metal concentrations."
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_loaded = pd.read_csv(uploaded_file)
            else:
                df_loaded = pd.read_excel(uploaded_file)
            st.session_state["df_raw"] = df_loaded
            st.session_state["data_source_name"] = uploaded_file.name
            st.success(f"Loaded {uploaded_file.name} ({len(df_loaded)} rows)")
        except Exception as e:
            st.error(f"Failed to read file: {e}")

    # If no data is loaded yet, automatically load sample data as friendly default
    if st.session_state["df_raw"] is None:
        load_sample_dataset()

    df_current = st.session_state["df_raw"]

    st.markdown("---")
    st.subheader("2. 🎯 Column Mapping")

    if df_current is not None and not df_current.empty:
        detected = detect_columns(df_current)
        all_cols = df_current.columns.tolist()

        # Site column
        site_col_default_idx = (
            all_cols.index(detected["site_col"]) if detected["site_col"] in all_cols else 0
        )
        site_col = st.selectbox(
            "Site Identifier Column",
            options=all_cols,
            index=site_col_default_idx,
            help="Column containing monitoring station or site name"
        )

        # Latitude column
        lat_candidates = [c for c in all_cols if c != site_col]
        lat_default_idx = (
            lat_candidates.index(detected["lat_col"])
            if detected["lat_col"] in lat_candidates
            else 0
        )
        lat_col = st.selectbox(
            "Latitude Column",
            options=lat_candidates,
            index=lat_default_idx if lat_candidates else 0,
            help="Latitude coordinates (decimal degrees: -90 to +90)"
        )

        # Longitude column
        lon_candidates = [c for c in all_cols if c not in [site_col, lat_col]]
        lon_default_idx = (
            lon_candidates.index(detected["lon_col"])
            if detected["lon_col"] in lon_candidates
            else 0
        )
        lon_col = st.selectbox(
            "Longitude Column",
            options=lon_candidates,
            index=lon_default_idx if lon_candidates else 0,
            help="Longitude coordinates (decimal degrees: -180 to +180)"
        )

        # Metal columns selection
        metal_candidates = [c for c in all_cols if c not in [site_col, lat_col, lon_col]]
        default_metals = [c for c in detected["metal_cols"] if c in metal_candidates]
        if not default_metals:
            default_metals = metal_candidates[:6]

        selected_metals = st.multiselect(
            "Heavy Metal Columns",
            options=metal_candidates,
            default=default_metals,
            help="Select all heavy metal concentration columns to include in the HMPI calculation (e.g. Pb, Cd, Cr, Ni, Zn, Cu)"
        )

        st.markdown("---")
        st.subheader("3. 🧪 Permissible Limits (Si)")
        st.caption("Standard limits in mg/L (WHO / BIS standards)")

        # Expandable metal limits modifier
        with st.expander("Modify Standard Limits (Si)", expanded=False):
            st.info("Values correspond to maximum permissible limits in drinking/surface water standard (mg/L).")
            active_standards = {}
            for metal in selected_metals:
                clean_key = metal.split("(")[0].strip().upper()
                default_val = st.session_state["custom_standards"].get(
                    clean_key,
                    DEFAULT_STANDARDS.get(clean_key, 1.0)
                )
                limit_val = st.number_input(
                    f"{metal} Limit (mg/L)",
                    min_value=0.0001,
                    max_value=1000.0,
                    value=float(default_val),
                    step=0.001,
                    format="%.4f",
                    key=f"limit_{metal}"
                )
                active_standards[metal] = limit_val
                st.session_state["custom_standards"][clean_key] = limit_val

        st.markdown("---")
        st.subheader("4. 🚦 Classification Thresholds")
        threshold_low = st.number_input(
            "Low / Moderate Threshold",
            min_value=1.0,
            max_value=500.0,
            value=50.0,
            step=5.0,
            help="HMPI values below this are categorized as Low Pollution (Default: 50)"
        )
        threshold_high = st.number_input(
            "Moderate / High Threshold",
            min_value=threshold_low + 1.0,
            max_value=1000.0,
            value=100.0,
            step=5.0,
            help="HMPI values above this are categorized as High Pollution (Default: 100)"
        )

    else:
        site_col = lat_col = lon_col = None
        selected_metals = []
        active_standards = {}
        threshold_low, threshold_high = 50.0, 100.0


# ==============================================================================
# MAIN DASHBOARD AREA
# ==============================================================================

# Title Banner
st.title("🌊 Heavy Metal Pollution Index (HMPI) Monitoring System")
st.markdown(
    '<p class="header-subtext">Comprehensive environmental indexing, spatial hotspot mapping, and multi-metal pollution diagnostics.</p>',
    unsafe_allow_html=True
)

if df_current is None or df_current.empty:
    st.info("👈 Please upload an environmental monitoring dataset or click **'Load Sample'** in the sidebar to begin.")
    st.stop()

if not selected_metals:
    st.warning("⚠️ Please select at least one metal concentration column in the sidebar.")
    st.stop()

# Validate data
is_valid, validation_msgs, clean_df = validate_input_data(
    df=df_current,
    site_col=site_col,
    lat_col=lat_col,
    lon_col=lon_col,
    metal_cols=selected_metals,
)

if not is_valid:
    st.error("Validation Error:")
    for msg in validation_msgs:
        st.error(f"• {msg}")
    st.stop()

# Show non-fatal warnings if any
if validation_msgs:
    with st.expander("ℹ️ Data Ingestion Notes & Warnings", expanded=False):
        for msg in validation_msgs:
            st.warning(msg)

# Compute HMPI
result_df, summary = compute_hmpi(
    df=clean_df,
    site_col=site_col,
    lat_col=lat_col,
    lon_col=lon_col,
    metal_cols=selected_metals,
    standards=active_standards,
    threshold_low=threshold_low,
    threshold_high=threshold_high,
)

# ------------------------------------------------------------------------------
# TOP ROW: EXECUTIVE KPI METRICS
# ------------------------------------------------------------------------------
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(
        label="Total Sites Monitored",
        value=f"{summary['total_sites']}",
        delta=f"{len(selected_metals)} Metals Analyzed",
        delta_color="off"
    )

with kpi2:
    low_cnt = summary['category_counts']['Low']
    low_pct = summary['category_percentages']['Low']
    st.metric(
        label="🟢 Low Pollution",
        value=f"{low_cnt} sites",
        delta=f"{low_pct}% of total",
        delta_color="normal"
    )

with kpi3:
    mod_cnt = summary['category_counts']['Moderate']
    mod_pct = summary['category_percentages']['Moderate']
    st.metric(
        label="🟠 Moderate Pollution",
        value=f"{mod_cnt} sites",
        delta=f"{mod_pct}% of total",
        delta_color="off"
    )

with kpi4:
    high_cnt = summary['category_counts']['High']
    high_pct = summary['category_percentages']['High']
    st.metric(
        label="🔴 High Pollution",
        value=f"{high_cnt} sites",
        delta=f"{high_pct}% critical",
        delta_color="inverse"
    )

with kpi5:
    st.metric(
        label="Average HMPI",
        value=f"{summary['avg_hmpi']:.1f}",
        delta=f"Max: {summary['max_hmpi']:.1f}",
        delta_color="off"
    )

st.markdown("<br/>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# DASHBOARD TABS
# ------------------------------------------------------------------------------
tab_map, tab_analytics, tab_data, tab_formula = st.tabs([
    "🗺️ Geospatial Hotspot Map",
    "📊 Pollution Analytics & Breakdown",
    "📋 Tabular Results & Inspector",
    "🧮 Mathematical Formulation & Standards",
])

# ==============================================================================
# TAB 1: GEOSPATIAL MAP (PyDeck)
# ==============================================================================
with tab_map:
    st.subheader("Spatial Hotspot Distribution")
    st.caption("Interactive map rendering monitoring stations with color-coded pollution categories and proportional radii.")

    # Map control bar
    map_ctrl1, map_ctrl2, map_ctrl3 = st.columns([2, 2, 2])
    with map_ctrl1:
        category_filter = st.multiselect(
            "Filter by Category",
            options=["Low", "Moderate", "High"],
            default=["Low", "Moderate", "High"],
            help="Filter stations visible on the map"
        )
    with map_ctrl2:
        map_style = st.selectbox(
            "Map Base Style",
            options=[
                ("Light (Carto Positron)", "light"),
                ("Dark (Carto Dark)", "dark"),
                ("Roads", "road"),
            ],
            format_func=lambda x: x[0],
            index=0
        )[1]
    with map_ctrl3:
        layer_mode = st.selectbox(
            "Visualization Layer",
            options=["2D Hotspot Scatter", "3D Extruded Columns"],
            index=0
        )

    # Filtered dataframe for mapping
    filtered_map_df = result_df[result_df["Category"].isin(category_filter)].copy()

    # Drop any remaining NaNs in coordinates
    filtered_map_df = filtered_map_df.dropna(subset=[lat_col, lon_col])

    if filtered_map_df.empty:
        st.warning("No sites match the current filter selection.")
    else:
        # Dynamic radius based on HMPI
        # Minimum radius 250m, maximum 2500m
        filtered_map_df["Radius"] = (
            250 + (filtered_map_df["HMPI"] / (summary["max_hmpi"] + 1e-5)) * 2000
        ).clip(lower=200, upper=3000)

        # Elevation for 3D column layer (scaled for visibility)
        filtered_map_df["Elevation"] = filtered_map_df["HMPI"] * 30

        # Center point
        avg_lat = float(filtered_map_df[lat_col].mean())
        avg_lon = float(filtered_map_df[lon_col].mean())

        # Construct PyDeck Layer
        layers = []
        if layer_mode == "2D Hotspot Scatter":
            scatter_layer = pdk.Layer(
                "ScatterplotLayer",
                data=filtered_map_df,
                get_position=[lon_col, lat_col],
                get_color="Color_RGBA",
                get_radius="Radius",
                pickable=True,
                opacity=0.85,
                stroked=True,
                filled=True,
                line_width_min_pixels=1,
                get_line_color=[255, 255, 255, 200],
            )
            layers.append(scatter_layer)
        else:
            column_layer = pdk.Layer(
                "ColumnLayer",
                data=filtered_map_df,
                get_position=[lon_col, lat_col],
                get_elevation="Elevation",
                elevation_scale=1,
                radius=400,
                get_fill_color="Color_RGBA",
                pickable=True,
                auto_highlight=True,
            )
            layers.append(column_layer)

        # Tooltip HTML
        tooltip = {
            "html": f"""
                <div style="font-family: sans-serif; padding: 6px; font-size: 13px;">
                    <b style="font-size: 14px; color: #60a5fa;">{{{site_col}}}</b><br/>
                    <b>HMPI Score:</b> {{{'HMPI'}}}<br/>
                    <b>Category:</b> {{{'Category'}}}<br/>
                    <b>Dominant Pollutant:</b> {{{'Dominant_Metal'}}}<br/>
                    <b>Coordinates:</b> {{{lat_col}}}, {{{lon_col}}}
                </div>
            """,
            "style": {
                "backgroundColor": "#111827",
                "color": "#ffffff",
                "borderRadius": "8px",
                "boxShadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            }
        }

        view_state = pdk.ViewState(
            latitude=avg_lat,
            longitude=avg_lon,
            zoom=10.2,
            pitch=45 if layer_mode == "3D Extruded Columns" else 0,
            bearing=0,
        )

        deck = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            map_style=map_style,
            tooltip=tooltip,
        )

        st.pydeck_chart(deck, use_container_width=True)

        # Legend strip
        leg_col1, leg_col2, leg_col3, leg_col4 = st.columns([1, 1, 1, 1.5])
        with leg_col1:
            st.markdown("🟢 **Low Pollution** (`HMPI < 50`)")
        with leg_col2:
            st.markdown("🟠 **Moderate Pollution** (`50 ≤ HMPI ≤ 100`)")
        with leg_col3:
            st.markdown("🔴 **High Pollution** (`HMPI > 100`)")
        with leg_col4:
            st.caption(f"Currently displaying **{len(filtered_map_df)}** of **{len(result_df)}** sites.")


# ==============================================================================
# TAB 2: ANALYTICS & BREAKDOWN
# ==============================================================================
with tab_analytics:
    st.subheader("Pollution Diagnostics & Metal Contribution")

    an_row1_col1, an_row1_col2 = st.columns([1.2, 1])

    with an_row1_col1:
        st.markdown("##### 📌 Average Heavy Metal Contribution to HMPI")
        st.caption("Shows which metals contribute most heavily across all monitoring stations.")

        # Data for metal contribution bar chart
        contrib_data = []
        for m in selected_metals:
            mean_wq = float(result_df[f"W_Q_{m}"].mean())
            weight = summary["weights"][m]
            mean_conc = float(result_df[m].mean())
            limit = active_standards[m]
            contrib_data.append({
                "Metal": m,
                "Weighted Contribution (Wi * Qi)": round(mean_wq, 2),
                "Unit Weight (Wi)": round(weight, 4),
                "Mean Concentration (mg/L)": round(mean_conc, 4),
                "Standard Limit (mg/L)": round(limit, 4),
                "Mean / Limit Ratio": round(mean_conc / limit, 2),
            })
        contrib_df = pd.DataFrame(contrib_data).sort_values("Weighted Contribution (Wi * Qi)", ascending=False)

        chart_contrib = alt.Chart(contrib_df).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            x=alt.X("Weighted Contribution (Wi * Qi):Q", title="Average Weighted Sub-Index (Wi * Qi)"),
            y=alt.Y("Metal:N", sort="-x", title="Heavy Metal"),
            color=alt.Color("Weighted Contribution (Wi * Qi):Q", scale=alt.Scale(scheme="reds"), legend=None),
            tooltip=["Metal", "Weighted Contribution (Wi * Qi)", "Unit Weight (Wi)", "Mean Concentration (mg/L)", "Standard Limit (mg/L)", "Mean / Limit Ratio"]
        ).properties(height=280)

        st.altair_chart(chart_contrib, use_container_width=True)

    with an_row1_col2:
        st.markdown("##### 📊 Pollution Category Distribution")
        st.caption("Breakdown of monitored sites by risk category.")

        cat_summary_df = pd.DataFrame([
            {"Category": "Low (< 50)", "Count": summary["category_counts"]["Low"], "Color": "#28a745"},
            {"Category": "Moderate (50-100)", "Count": summary["category_counts"]["Moderate"], "Color": "#ff9800"},
            {"Category": "High (> 100)", "Count": summary["category_counts"]["High"], "Color": "#dc3545"},
        ])

        cat_chart = alt.Chart(cat_summary_df).mark_arc(innerRadius=45).encode(
            theta=alt.Theta("Count:Q"),
            color=alt.Color("Category:N", scale=alt.Scale(
                domain=["Low (< 50)", "Moderate (50-100)", "High (> 100)"],
                range=["#28a745", "#ff9800", "#dc3545"]
            )),
            tooltip=["Category", "Count"]
        ).properties(height=280)

        st.altair_chart(cat_chart, use_container_width=True)

    st.markdown("---")

    # Stacked site breakdown
    st.markdown("##### 🔬 Stacked Metal Contribution Per Site")
    st.caption("Detailed visual breakdown of weighted metal sub-indices contributing to each station's total HMPI.")

    # Reshape for stacked bar chart
    melt_cols = [f"W_Q_{m}" for m in selected_metals]
    melt_df = result_df[[site_col, "HMPI", "Category"] + melt_cols].copy()
    melt_df = melt_df.melt(
        id_vars=[site_col, "HMPI", "Category"],
        value_vars=melt_cols,
        var_name="Metal_Col",
        value_name="Weighted_Qi"
    )
    melt_df["Metal"] = melt_df["Metal_Col"].str.replace("W_Q_", "")

    # Top sites selector to avoid cluttering if > 25 sites
    max_sites_to_show = min(len(result_df), 25)
    sorted_sites = result_df.sort_values("HMPI", ascending=False)[site_col].head(max_sites_to_show).tolist()
    melt_df_filtered = melt_df[melt_df[site_col].isin(sorted_sites)]

    stacked_chart = alt.Chart(melt_df_filtered).mark_bar().encode(
        x=alt.X(f"{site_col}:N", sort="-y", title="Monitoring Site (Sorted by HMPI)"),
        y=alt.Y("Weighted_Qi:Q", title="HMPI Sub-Index Contribution"),
        color=alt.Color("Metal:N", scale=alt.Scale(scheme="category10"), title="Metal"),
        tooltip=[site_col, "Metal", "Weighted_Qi", "HMPI", "Category"]
    ).properties(height=380)

    st.altair_chart(stacked_chart, use_container_width=True)


# ==============================================================================
# TAB 3: TABULAR RESULTS & INSPECTOR
# ==============================================================================
with tab_data:
    st.subheader("Computed Results Table & Site Inspector")

    # Filter and search controls
    search_col1, search_col2, search_col3 = st.columns([2, 1.5, 1.5])
    with search_col1:
        search_query = st.text_input("🔍 Search Site Name", placeholder="Type site name...")
    with search_col2:
        table_cat_filter = st.selectbox(
            "Filter Category",
            options=["All Categories", "Low", "Moderate", "High"],
            index=0
        )
    with search_col3:
        sort_by = st.selectbox(
            "Sort By",
            options=["HMPI (High to Low)", "HMPI (Low to High)", "Site Name"],
            index=0
        )

    # Apply filters
    display_df = result_df.copy()
    if search_query:
        display_df = display_df[display_df[site_col].astype(str).str.contains(search_query, case=False, na=False)]
    if table_cat_filter != "All Categories":
        display_df = display_df[display_df["Category"] == table_cat_filter]

    # Sort
    if sort_by == "HMPI (High to Low)":
        display_df = display_df.sort_values("HMPI", ascending=False)
    elif sort_by == "HMPI (Low to High)":
        display_df = display_df.sort_values("HMPI", ascending=True)
    else:
        display_df = display_df.sort_values(site_col, ascending=True)

    # Select columns to display clearly
    primary_display_cols = [site_col, "HMPI", "Category", "Dominant_Metal", lat_col, lon_col] + selected_metals
    
    # Styled dataframe
    st.dataframe(
        display_df[primary_display_cols],
        use_container_width=True,
        column_config={
            "HMPI": st.column_config.NumberColumn(
                "HMPI Score",
                format="%.2f",
                help="Heavy Metal Pollution Index",
            ),
            "Category": st.column_config.TextColumn(
                "Category",
                help="Pollution classification based on configured thresholds",
            ),
            "Dominant_Metal": st.column_config.TextColumn(
                "Primary Driver",
                help="Metal with highest contribution to the site's HMPI",
            ),
            lat_col: st.column_config.NumberColumn("Latitude", format="%.4f"),
            lon_col: st.column_config.NumberColumn("Longitude", format="%.4f"),
        },
        hide_index=True,
    )

    st.markdown("---")
    
    # Site Drill-down inspector
    st.subheader("🔬 Single Site Detailed Breakdown")
    site_names_list = result_df[site_col].tolist()
    selected_inspect_site = st.selectbox("Select Station to Inspect:", site_names_list)

    if selected_inspect_site:
        site_record = result_df[result_df[site_col] == selected_inspect_site].iloc[0]
        
        ins_col1, ins_col2, ins_col3 = st.columns([1, 1, 2])
        with ins_col1:
            st.metric("Site HMPI", f"{site_record['HMPI']:.2f}")
            badge_html = CATEGORY_COLORS[site_record['Category']]['badge']
            st.markdown(f"**Classification:** {badge_html}")
            st.write(f"**Primary Driver:** {site_record['Dominant_Metal']}")
        with ins_col2:
            st.write(f"**Latitude:** {site_record[lat_col]:.4f}")
            st.write(f"**Longitude:** {site_record[lon_col]:.4f}")

        with ins_col3:
            # Per-metal table for this specific site
            site_metal_details = []
            for m in selected_metals:
                site_metal_details.append({
                    "Metal": m,
                    "Monitored (mg/L)": float(site_record[m]),
                    "Standard Si (mg/L)": float(active_standards[m]),
                    "Quality Rating (Qi)": float(site_record[f"Q_{m}"]),
                    "Weight (Wi)": float(summary["weights"][m]),
                    "Contribution (Wi * Qi)": float(site_record[f"W_Q_{m}"]),
                    "% of Site HMPI": float(site_record[f"Contrib_{m}_pct"]),
                })
            st.dataframe(pd.DataFrame(site_metal_details), use_container_width=True, hide_index=True)


# ==============================================================================
# TAB 4: MATHEMATICAL FORMULATION & STANDARDS
# ==============================================================================
with tab_formula:
    st.subheader("Heavy Metal Pollution Index (HMPI) Methodology")

    st.markdown(r"""
    The **Heavy Metal Pollution Index (HMPI)** represents the composite influence of individual heavy metals on overall environmental quality.
    
    ### 1. Unit Weight Factor ($W_i$)
    The unit weight is inversely proportional to the recommended permissible limit ($S_i$) of the respective metal:
    """)

    st.latex(r"W_i = \frac{k}{S_i} = \frac{1 / S_i}{\sum_{j=1}^{n} (1 / S_j)}")
    st.markdown("where $k$ is the proportionality constant ensuring that $\\sum_{i=1}^{n} W_i = 1$.")

    st.markdown(r"""
    ### 2. Quality Rating / Sub-Index ($Q_i$)
    The quality rating reflects how closely the monitored concentration ($M_i$) conforms to permissible limits ($S_i$):
    """)

    st.latex(r"Q_i = \frac{|M_i - I_i|}{S_i - I_i} \times 100")
    st.markdown("where $I_i$ is the ideal permissible limit (typically $0.0\\text{ mg/L}$ for toxic heavy metals).")

    st.markdown(r"""
    ### 3. Overall Heavy Metal Pollution Index ($HMPI$)
    The overall index is computed as the weighted sum of individual sub-indices:
    """)

    st.latex(r"HMPI = \frac{\sum_{i=1}^{n} (W_i \times Q_i)}{\sum_{i=1}^{n} W_i} = \sum_{i=1}^{n} (W_i \times Q_i)")

    st.markdown("---")
    st.subheader("Active Parameter Standards & Unit Weights")
    
    param_summary = []
    for m in selected_metals:
        param_summary.append({
            "Metal": m,
            "Permissible Standard Si (mg/L)": active_standards[m],
            "Inverse Standard (1 / Si)": round(1.0 / active_standards[m], 4),
            "Normalized Weight (Wi)": round(summary["weights"][m], 5),
            "Weight Share (%)": f"{summary['weights'][m] * 100:.2f}%",
        })
    st.table(pd.DataFrame(param_summary))

    st.markdown(r"""
    ### Categorization Scale (Prasad & Bose, 2001)
    - **🟢 Low Pollution ($HMPI < 50$):** Metal concentrations well within permissible limits; clean water/soil baseline.
    - **🟠 Moderate Pollution ($50 \le HMPI \le 100$):** Approaching critical contamination threshold; elevated risk.
    - **🔴 High Pollution ($HMPI > 100$):** Exceeds the critical pollution threshold; remediation and intervention recommended.
    """)


# ==============================================================================
# EXPORT SECTION
# ==============================================================================
st.markdown("---")
st.subheader("💾 Export Results & Reports")

exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 1.5])

with exp_col1:
    # CSV export
    csv_buffer = io.StringIO()
    result_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download Results (CSV)",
        data=csv_buffer.getvalue(),
        file_name="hmpi_monitoring_results.csv",
        mime="text/csv",
        use_container_width=True,
    )

with exp_col2:
    # Excel export
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        result_df.to_excel(writer, sheet_name="HMPI_Results", index=False)
        # Also write summary metadata sheet
        summary_records = [
            {"Metric": "Total Sites", "Value": summary["total_sites"]},
            {"Metric": "Low Pollution Sites", "Value": summary["category_counts"]["Low"]},
            {"Metric": "Moderate Pollution Sites", "Value": summary["category_counts"]["Moderate"]},
            {"Metric": "High Pollution Sites", "Value": summary["category_counts"]["High"]},
            {"Metric": "Average HMPI", "Value": summary["avg_hmpi"]},
            {"Metric": "Maximum HMPI", "Value": summary["max_hmpi"]},
            {"Metric": "Highest Risk Site", "Value": summary["highest_site_name"]},
        ]
        pd.DataFrame(summary_records).to_excel(writer, sheet_name="Summary_KPIs", index=False)

    st.download_button(
        label="📥 Download Results (Excel)",
        data=excel_buffer.getvalue(),
        file_name="hmpi_monitoring_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with exp_col3:
    # Summary JSON report
    report_json = {
        "title": "Heavy Metal Pollution Index (HMPI) Assessment Report",
        "dataset_name": st.session_state.get("data_source_name", "Uploaded Data"),
        "metrics": {
            "total_sites": summary["total_sites"],
            "category_counts": summary["category_counts"],
            "category_percentages": summary["category_percentages"],
            "average_hmpi": summary["avg_hmpi"],
            "highest_pollution_site": summary["highest_site_name"],
            "max_hmpi": summary["max_hmpi"],
        },
        "standards_used": active_standards,
        "weights_calculated": summary["weights"],
        "thresholds": summary["thresholds"]
    }
    st.download_button(
        label="📄 Download Assessment Report (JSON)",
        data=json.dumps(report_json, indent=2),
        file_name="hmpi_assessment_summary.json",
        mime="application/json",
        use_container_width=True,
    )
