# Heavy Metal Pollution Index (HMPI) Monitoring & Visualization System

A lightweight, attractive, and user-friendly Python application to calculate the **Heavy Metal Pollution Index (HMPI)** from environmental monitoring site data, visualize pollution hotspots on an interactive **PyDeck** map, analyze multi-metal contributions, and export comprehensive assessment reports.

---

## 🌟 Key Features

1. **Flexible Data Ingestion**
   - Upload any environmental monitoring dataset in **CSV**, **Excel (.xlsx)**, or **.xls** format.
   - Built-in **1-Click Sample Dataset** containing 25 realistic monitoring sites (springs, agricultural runoff, industrial discharge, landfills, and smelter sites).
   - Downloadable CSV template for sample formatting.

2. **Smart Column Mapping & Auto-Detection**
   - Automatically detects Site Name, Latitude, Longitude, and candidate metal columns (e.g., `Pb`, `Cd`, `Cr`, `Ni`, `Zn`, `Cu`, `As`, `Fe`).
   - Allows users to select or remap columns dynamically in the sidebar.

3. **Configurable Permissible Standards & Thresholds**
   - Pre-populated with **WHO** and **BIS** maximum permissible limits ($S_i$ in mg/L).
   - Fully customizable limits ($S_i$) and ideal values ($I_i$) directly via sidebar inputs.
   - Configurable classification thresholds (Default: Low $< 50$, Moderate $50\text{--}100$, High $> 100$).

4. **Rigorous Scientific Formulation (Mohan et al., 1996; Prasad & Bose, 2001)**
   - Normalized unit weight factors: $W_i = \frac{1/S_i}{\sum (1/S_j)}$
   - Quality rating sub-indices: $Q_i = \frac{|M_i - I_i|}{S_i - I_i} \times 100$
   - Composite HMPI: $HMPI = \sum_{i=1}^n (W_i \times Q_i)$
   - Dominant pollutant metal identified for each station.

5. **Interactive PyDeck Geospatial Map**
   - Dynamic circle sizing proportional to HMPI severity.
   - Intuitive color coding:
     - 🟢 **Green** (`#28a745`): Low Pollution ($HMPI < 50$)
     - 🟠 **Orange** (`#ff9800`): Moderate Pollution ($50 \le HMPI \le 100$)
     - 🔴 **Red** (`#dc3545`): High Pollution ($HMPI > 100$)
   - Multiple visualization modes: **2D Hotspot Scatter** and **3D Extruded Columns** (elevation scaled by HMPI score).
   - Rich interactive tooltips displaying Site Name, HMPI Score, Category, Dominant Pollutant, and Coordinates.
   - Map style toggling (Light Carto Positron, Dark Matter, Road).

6. **Pollution Diagnostics & Analytics**
   - Executive KPI cards: Total Sites, Low/Moderate/High counts & percentages, Average HMPI, Maximum HMPI site.
   - Average Heavy Metal Contribution to HMPI (ranking metals driving environmental stress).
   - Category distribution donut chart.
   - Stacked multi-metal bar chart per site showing exact sub-index contributions.
   - Single-station inspector drill-down displaying metal-by-metal breakdown.

7. **Multi-Format Export & Reporting**
   - 📥 **CSV Export**: Full dataset with sub-indices ($Q_i$), weighted scores ($W_i \times Q_i$), category, and dominant pollutants.
   - 📥 **Excel Export (.xlsx)**: Formatted workbook including both full results and an executive summary KPI sheet.
   - 📄 **JSON Assessment Report**: Complete structured summary with metadata, active weights, and thresholds.

8. **Optional Lightweight Flask REST API**
   - Ready-to-use headless backend with endpoints for health checks, default standards, sample data, computation, and CSV export.

---

## 🧮 Mathematical Formulation

### 1. Unit Weight Factor ($W_i$)
The unit weight is inversely proportional to the permissible standard limit ($S_i$):
$$W_i = \frac{k}{S_i} = \frac{1 / S_i}{\sum_{j=1}^{n} (1 / S_j)}$$
where $k$ is the proportionality constant ensuring that $\sum_{i=1}^{n} W_i = 1$.

### 2. Quality Rating Sub-Index ($Q_i$)
The quality rating reflects how closely the monitored concentration ($M_i$) conforms to permissible limits ($S_i$):
$$Q_i = \frac{|M_i - I_i|}{S_i - I_i} \times 100$$
*(For toxic heavy metals, the ideal permissible value $I_i$ is typically $0.0\text{ mg/L}$, simplifying to $Q_i = \frac{M_i}{S_i} \times 100$)*.

### 3. Overall Heavy Metal Pollution Index ($HMPI$)
$$HMPI = \frac{\sum_{i=1}^{n} (W_i \times Q_i)}{\sum_{i=1}^{n} W_i} = \sum_{i=1}^{n} (W_i \times Q_i)$$

### 4. Classification Scale (Prasad & Bose, 2001)
| HMPI Range | Pollution Category | Action / Meaning | Color Indicator |
| :--- | :--- | :--- | :--- |
| **$< 50$** | **Low Pollution** | Within permissible limits; pristine or baseline conditions | 🟢 Green |
| **$50 - 100$** | **Moderate Pollution** | Approaching critical pollution limit; elevated risk | 🟠 Orange |
| **$> 100$** | **High Pollution** | Exceeds critical threshold; intervention required | 🔴 Red |

---

## 📁 Project Structure

```text
Calculate HMPI/
├── .streamlit/
│   └── config.toml          # Streamlit theme & headless server configuration
├── app.py                   # Streamlit web application & PyDeck dashboard
├── hmpi_engine.py           # Core scientific calculation engine & validation
├── api.py                   # Optional lightweight Flask REST API
├── generate_sample_data.py  # Script generating sample dataset
├── sample_data.csv          # 25-site sample environmental dataset (CSV)
├── sample_data.xlsx         # 25-site sample environmental dataset (Excel)
├── test_hmpi.py             # Unit tests for HMPI calculation engine
├── test_api.py              # Unit tests for Flask API endpoints
├── requirements.txt         # Project dependencies
└── README.md                # Documentation & usage guide
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have **Python 3.9+** installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Streamlit Web Application
```bash
streamlit run app.py
```
Open your browser at **`http://localhost:8501`**.

---

## 🧪 Optional: Running the Flask REST API

If you wish to expose the HMPI calculation engine as a lightweight backend microservice:

```bash
python api.py
```
The API starts on **`http://127.0.0.1:5000`**.

### API Endpoints:
- `GET /api/health`: Health status.
- `GET /api/standards`: Default WHO/BIS permissible limits.
- `GET /api/sample`: Retrieve sample monitoring data.
- `POST /api/calculate`: Compute HMPI (accepts JSON payload or CSV file upload).
- `POST /api/export`: Compute and download results as CSV.

#### Example API Request (curl):
```bash
curl -X POST http://127.0.0.1:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"Site_Name": "Site A", "Latitude": 28.61, "Longitude": 77.20, "Pb": 0.005, "Cd": 0.001, "Cr": 0.02, "Ni": 0.01, "Zn": 1.0, "Cu": 0.3}
    ],
    "metals": ["Pb", "Cd", "Cr", "Ni", "Zn", "Cu"]
  }'
```

---

## 📊 Default Permissible Limits (WHO / BIS Standards)

| Metal | Symbol | Permissible Standard ($S_i$) [mg/L] | Ideal Limit ($I_i$) [mg/L] |
| :--- | :--- | :--- | :--- |
| Lead | **Pb** | 0.010 | 0.0 |
| Cadmium | **Cd** | 0.003 | 0.0 |
| Chromium | **Cr** | 0.050 | 0.0 |
| Nickel | **Ni** | 0.020 | 0.0 |
| Zinc | **Zn** | 3.000 | 0.0 |
| Copper | **Cu** | 1.000 | 0.0 |
| Arsenic | **As** | 0.010 | 0.0 |
| Iron | **Fe** | 0.300 | 0.0 |
| Manganese | **Mn** | 0.100 | 0.0 |
| Mercury | **Hg** | 0.001 | 0.0 |

*All standard limits are user-configurable in the application.*

---

## 🧪 Running Tests

Run the test suites to verify mathematical accuracy and API endpoints:

```bash
# Verify HMPI calculation engine
python test_hmpi.py

# Verify Flask REST API
python test_api.py
```

---

## 📜 License
MIT License. Built for environmental monitoring, research, and resource management.
