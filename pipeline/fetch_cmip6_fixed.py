"""
fetch_cmip6_fixed.py — downloads the global CMIP6 MRI-ESM2-0 SSP2-4.5 +
historical near-surface air temperature NetCDF files that process.py's
export_cmip6_grid_geojson() consumes to build the raw grid layer.

CDS API FIXES (all three caused server-side TypeErrors on the pre-2024 API)
----------------------------------------------------------------------------
FIX 1 — wrong format field:
    OLD: "format": "zip"
    NEW: "download_format": "zip"           # archive wrapper
         "data_format":     "netcdf_legacy" # data format inside archive

FIX 2 — "level": "single_levels" must be omitted:
    near_surface_air_temperature is 2D/surface; the CDS constraints JSON
    lists no level field for it. Only 3D pressure-level variables use level.

FIX 3 — "date" range must be replaced by "year"/"month" lists:
    The new CDS API has no date field. Constraints only list year and month.
    OLD: "date": "2015-01-01/2100-12-31"
    NEW: "year": ["2015", ...], "month": ["01", ..., "12"]

OTHER
-----
SSL fix: pip install pip-system-certs  (routes Python SSL through Windows CA store)

.cdsapirc format:
    url: https://cds.climate.copernicus.eu/api
    key: YOUR-API-KEY-ONLY   (no UID: prefix)

Run:
    cd Pipeline/
    pip install cdsapi xarray netCDF4 pip-system-certs
    python fetch_cmip6_fixed.py
"""

import sys
import logging
import warnings
import zipfile
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.resolve()
RAW = SCRIPT_DIR / "raw_data"
RAW.mkdir(parents=True, exist_ok=True)

SSP_NC  = RAW / "cmip6_tas_ssp245.nc"
HIST_NC = RAW / "cmip6_tas_historical.nc"

BASELINE_START = 1990

_ALL_MONTHS = [f"{m:02d}" for m in range(1, 13)]

# CDS request fields shared by both historical and SSP requests.
_CDS_COMMON = {
    "download_format":     "zip",            # FIX 1
    "data_format":         "netcdf_legacy",  # FIX 1
    "temporal_resolution": "monthly",
    "variable":            "near_surface_air_temperature",
    "model":               "mri_esm2_0",
    "month":               _ALL_MONTHS,      # FIX 3
}


def _extract_nc(zip_path: Path, dest: Path):
    with zipfile.ZipFile(zip_path, "r") as z:
        nc_files = [f for f in z.namelist() if f.endswith(".nc")]
        if not nc_files:
            log.error(f"No .nc file found in {zip_path.name} — check CDS output.")
            sys.exit(1)
        z.extract(nc_files[0], RAW)
        extracted = RAW / nc_files[0]
        if extracted != dest:
            extracted.rename(dest)


def download_cmip6():
    """Download SSP2-4.5 (2015-2100) and historical (BASELINE_START-2014) tas, global."""
    if SSP_NC.exists() and HIST_NC.exists():
        log.info("CMIP6 NetCDF files already downloaded — skipping.")
        return

    try:
        import cdsapi
    except ImportError:
        log.error("cdsapi not installed. Run: pip install cdsapi")
        sys.exit(1)

    log.info("Connecting to Copernicus CDS ...")
    client = cdsapi.Client()

    if not SSP_NC.exists():
        ssp_zip = RAW / "cmip6_tas_ssp245.zip"
        log.info("Requesting CMIP6 SSP2-4.5 tas (2015-2100) — global, ~100-800 MB ...")
        client.retrieve(
            "projections-cmip6",
            {
                **_CDS_COMMON,
                "experiment": "ssp2_4_5",
                "year":       [str(y) for y in range(2015, 2101)],  # FIX 3
            },
            str(ssp_zip),
        )
        log.info("Extracting SSP2-4.5 NetCDF ...")
        _extract_nc(ssp_zip, SSP_NC)
        log.info(f"Extracted -> {SSP_NC}")

    if not HIST_NC.exists():
        hist_zip = RAW / "cmip6_tas_historical.zip"
        log.info(f"Requesting CMIP6 historical tas ({BASELINE_START}-2014) ...")
        client.retrieve(
            "projections-cmip6",
            {
                **_CDS_COMMON,
                "experiment": "historical",
                "year":       [str(y) for y in range(BASELINE_START, 2015)],  # FIX 3
            },
            str(hist_zip),
        )
        log.info("Extracting historical NetCDF ...")
        _extract_nc(hist_zip, HIST_NC)
        log.info(f"Extracted -> {HIST_NC}")

    log.info("Download complete.")


def main():
    log.info("=" * 60)
    log.info("Climate Atlas -- CMIP6 global grid NetCDF fetch")
    log.info("=" * 60)
    download_cmip6()
    log.info("\nDone. Run: python process.py")


if __name__ == "__main__":
    main()
