"""
Minimal smoke-test for the corrected CDS projections-cmip6 request.
Downloads 2 years of MRI-ESM2-0 SSP2-4.5 tas (~10-50 MB) to confirm
the fixed field names work before running the full 2015-2100 fetch.

Run from Pipeline/:
    python test_cmip6_request.py

If it completes without error and produces a .nc file, fetch_cmip6_fixed.py
is safe to run.
"""

import sys
import zipfile
from pathlib import Path

try:
    import cdsapi
except ImportError:
    sys.exit("cdsapi not installed. Run: pip install cdsapi")

OUT_DIR = Path(__file__).parent / "raw_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ZIP_OUT = OUT_DIR / "test_cmip6_2015_2016.zip"
NC_OUT  = OUT_DIR / "test_cmip6_2015_2016.nc"

if NC_OUT.exists():
    print(f"Test file already exists: {NC_OUT}")
    print("Delete it and re-run if you want to re-test.")
    sys.exit(0)

print("Connecting to Copernicus CDS ...")
c = cdsapi.Client()

print("Submitting test request (2015-2016, ~10-50 MB) ...")
print()
print("FIXES applied vs original request:")
print('  FIX 1: "format": "zip"             -> "download_format"+"data_format" (API migration 2024)')
print('  FIX 2: "level": "single_levels"    -> omitted (surface var; no level field in constraints)')
print('  FIX 3: "date": "2015-01-01/..."    -> "year": [...] + "month": [...] (new API, no date field)')
print()

ALL_MONTHS = [f"{m:02d}" for m in range(1, 13)]

c.retrieve(
    "projections-cmip6",
    {
        "download_format":     "zip",            # FIX 1: was "format": "zip"
        "data_format":         "netcdf_legacy",  # FIX 1: was missing
        "temporal_resolution": "monthly",
        "experiment":          "ssp2_4_5",
        "variable":            "near_surface_air_temperature",
        "model":               "mri_esm2_0",
        "year":                ["2015", "2016"],  # FIX 3: was "date": "2015-01-01/2016-12-31"
        "month":               ALL_MONTHS,        # FIX 3: was absent (implied by date range)
    },
    str(ZIP_OUT),
)

print(f"\nDownload complete: {ZIP_OUT}")
print("Extracting ...")

with zipfile.ZipFile(ZIP_OUT, "r") as z:
    nc_files = [f for f in z.namelist() if f.endswith(".nc")]
    if not nc_files:
        sys.exit("ERROR: no .nc file found in zip -- check CDS output.")
    z.extract(nc_files[0], OUT_DIR)
    extracted = OUT_DIR / nc_files[0]
    if extracted != NC_OUT:
        extracted.rename(NC_OUT)

print(f"Extracted: {NC_OUT}")
print()
print("SUCCESS -- all three fixes confirmed working.")
print("Run fetch_cmip6_fixed.py for the full 2015-2100 download.")
