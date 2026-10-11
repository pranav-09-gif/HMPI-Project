"""
Test Flask API endpoints using Flask test client.
"""
from api import api
import json
import pandas as pd

def test_api():
    client = api.test_client()

    # Test /api/health
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    print("[OK] Health check passed")

    # Test /api/standards
    res = client.get("/api/standards")
    assert res.status_code == 200
    data = res.get_json()
    assert "Pb" in data["default_standards_mg_L"]
    print("[OK] Standards endpoint passed")

    # Test /api/sample
    res = client.get("/api/sample")
    assert res.status_code == 200
    sample_records = res.get_json()
    assert len(sample_records) == 25
    print("[OK] Sample data endpoint passed")

    # Test /api/calculate with JSON
    calc_payload = {
        "data": sample_records,
        "metals": ["Pb", "Cd", "Cr", "Ni", "Zn", "Cu"],
    }
    res = client.post("/api/calculate", data=json.dumps(calc_payload), content_type="application/json")
    assert res.status_code == 200
    calc_data = res.get_json()
    assert calc_data["status"] == "success"
    assert "summary" in calc_data
    assert "results" in calc_data
    assert calc_data["summary"]["total_sites"] == 25
    print("[OK] Calculate endpoint passed")

    # Test /api/export
    res = client.post("/api/export", data=json.dumps(calc_payload), content_type="application/json")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    assert b"HMPI" in res.data
    print("[OK] Export endpoint passed")

    print("\nAll Flask API tests succeeded!")

if __name__ == "__main__":
    test_api()
