"""
Unit and functional tests for the HMPI calculation engine.
"""
import pandas as pd
from hmpi_engine import compute_hmpi, detect_columns, validate_input_data, DEFAULT_STANDARDS

def test_engine_with_sample_data():
    df = pd.read_csv("sample_data.csv")
    assert not df.empty, "Sample data should not be empty"

    detected = detect_columns(df)
    assert detected["site_col"] == "Site_Name"
    assert detected["lat_col"] == "Latitude"
    assert detected["lon_col"] == "Longitude"
    assert len(detected["metal_cols"]) >= 6

    metal_cols = ["Pb", "Cd", "Cr", "Ni", "Zn", "Cu"]
    is_valid, msgs, clean_df = validate_input_data(
        df,
        site_col=detected["site_col"],
        lat_col=detected["lat_col"],
        lon_col=detected["lon_col"],
        metal_cols=metal_cols
    )
    assert is_valid, f"Validation failed: {msgs}"

    result_df, summary = compute_hmpi(
        clean_df,
        site_col=detected["site_col"],
        lat_col=detected["lat_col"],
        lon_col=detected["lon_col"],
        metal_cols=metal_cols,
        standards=DEFAULT_STANDARDS,
        threshold_low=50.0,
        threshold_high=100.0
    )

    assert "HMPI" in result_df.columns
    assert "Category" in result_df.columns
    assert "Color_Hex" in result_df.columns
    assert "Dominant_Metal" in result_df.columns

    # Verify category counts are populated
    cats = summary["category_counts"]
    print("Category counts:", cats)
    assert cats["Low"] > 0, "Should have low pollution sites"
    assert cats["Moderate"] > 0, "Should have moderate pollution sites"
    assert cats["High"] > 0, "Should have high pollution sites"
    assert summary["avg_hmpi"] > 0

    print("All tests passed successfully!")
    print(f"Summary: avg_hmpi={summary['avg_hmpi']}, max={summary['max_hmpi']}, highest site='{summary['highest_site_name']}'")

if __name__ == "__main__":
    test_engine_with_sample_data()
