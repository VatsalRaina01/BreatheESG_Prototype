"""Quick script to upload all 3 sample data files for testing."""
import requests
import sys
import os

BASE = "http://localhost:8000/api"

# Login
r = requests.post(f"{BASE}/auth/login/", json={
    "email": "analyst@breatheesg.com",
    "password": "analyst123"
})
assert r.status_code == 200, f"Login failed: {r.text}"
token = r.json()["access"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Logged in as analyst")

# Get sources
r = requests.get(f"{BASE}/sources/", headers=headers)
sources = {s["source_type"]: s["id"] for s in r.json()["results"]}
print(f"Sources: {list(sources.keys())}")

# Upload files
sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")
files_to_upload = [
    ("sap_fuel_procurement.csv", "sap"),
    ("utility_electricity.csv", "utility"),
    ("travel_concur_export.csv", "travel"),
]

for filename, source_type in files_to_upload:
    filepath = os.path.join(sample_dir, filename)
    with open(filepath, "rb") as f:
        r = requests.post(
            f"{BASE}/ingest/upload/",
            headers=headers,
            files={"file": (filename, f, "text/csv")},
            data={
                "source_type": source_type,
                "data_source_id": sources[source_type],
            },
        )
    
    if r.status_code in (200, 201):
        result = r.json()
        print(f"\n{filename}:")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Total: {result.get('total_rows', 0)}")
        print(f"  Parsed: {result.get('parsed_rows', 0)}")
        print(f"  Failed: {result.get('failed_rows', 0)}")
        print(f"  Flagged: {result.get('flagged_rows', 0)}")
    else:
        print(f"\n{filename}: FAILED ({r.status_code})")
        print(f"  {r.text[:200]}")

# Check dashboard
r = requests.get(f"{BASE}/dashboard/summary/", headers=headers)
if r.status_code == 200:
    summary = r.json()
    print(f"\nDashboard Summary:")
    print(f"  Total: {summary['total']}")
    print(f"  Pending: {summary['pending']}")
    print(f"  Flagged: {summary['flagged']}")
    print(f"  By Scope: {summary['by_scope']}")
    print(f"  By Source: {summary['by_source']}")

print("\nDone!")
