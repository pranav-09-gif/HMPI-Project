"""
Lightweight Flask REST API for HMPI Calculation and Reporting
=============================================================
Endpoints:
  - GET  /api/health      : Healthcheck and system status
  - GET  /api/standards   : Default permissible standards (WHO/BIS)
  - GET  /api/sample      : Retrieve sample dataset
  - POST /api/calculate   : Compute HMPI from JSON payload or file upload
  - POST /api/export      : Compute and return results as downloadable CSV
"""

import io
from flask import Flask, request, jsonify, Response
import pandas as pd
from hmpi_engine import (
    DEFAULT_STANDARDS,
    detect_columns,
    validate_input_data,
    compute_hmpi,
)

api = Flask(__name__)


@api.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Heavy Metal Pollution Index (HMPI) API",
        "version": "1.0.0"
    })


@api.route("/api/standards", methods=["GET"])
def get_standards():
    return jsonify({
        "default_standards_mg_L": DEFAULT_STANDARDS,
        "default_thresholds": {"low": 50.0, "high": 100.0}
    })


@api.route("/api/sample", methods=["GET"])
def get_sample_data():
    try:
        df = pd.read_csv("sample_data.csv")
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/api/calculate", methods=["POST"])
def calculate():
    """
    Accepts:
      - JSON body: {"data": [...], "metals": [...], "standards": {...}, "thresholds": {"low": 50, "high": 100}}
      OR
      - Multipart form-data with file upload ('file')
    """
    try:
        standards = DEFAULT_STANDARDS.copy()
        thresh_low = 50.0
        thresh_high = 100.0
        metals = None

        if request.is_json:
            payload = request.get_json()
            raw_records = payload.get("data", [])
            df = pd.DataFrame(raw_records)
            metals = payload.get("metals")
            if "standards" in payload:
                standards.update(payload["standards"])
            if "thresholds" in payload:
                thresh_low = float(payload["thresholds"].get("low", 50.0))
                thresh_high = float(payload["thresholds"].get("high", 100.0))
        elif "file" in request.files:
            uploaded = request.files["file"]
            if uploaded.filename.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
        else:
            return jsonify({"error": "No JSON payload or file provided."}), 400

        if df.empty:
            return jsonify({"error": "Dataset is empty."}), 400

        detected = detect_columns(df)
        site_col = detected["site_col"]
        lat_col = detected["lat_col"]
        lon_col = detected["lon_col"]
        selected_metals = metals if metals else detected["metal_cols"]

        if not selected_metals:
            return jsonify({"error": "No valid metal columns identified or provided."}), 400

        is_valid, msgs, clean_df = validate_input_data(
            df=df,
            site_col=site_col,
            lat_col=lat_col,
            lon_col=lon_col,
            metal_cols=selected_metals
        )

        if not is_valid:
            return jsonify({"error": "Validation failed", "details": msgs}), 400

        result_df, summary = compute_hmpi(
            df=clean_df,
            site_col=site_col,
            lat_col=lat_col,
            lon_col=lon_col,
            metal_cols=selected_metals,
            standards=standards,
            threshold_low=thresh_low,
            threshold_high=thresh_high
        )

        return jsonify({
            "status": "success",
            "summary": summary,
            "validation_notes": msgs,
            "results": result_df.to_dict(orient="records")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route("/api/export", methods=["POST"])
def export_csv():
    try:
        calc_response = calculate()
        if isinstance(calc_response, tuple) and calc_response[1] != 200:
            return calc_response

        data = calc_response.get_json()
        results = data.get("results", [])
        res_df = pd.DataFrame(results)

        csv_str = res_df.to_csv(index=False)
        return Response(
            csv_str,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=hmpi_results.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Starting HMPI Lightweight Flask API on http://127.0.0.1:5000 ...")
    api.run(host="127.0.0.1", port=5000, debug=True)
