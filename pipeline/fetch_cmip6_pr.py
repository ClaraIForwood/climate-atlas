"""
fetch_cmip6_pr.py — downloads the global CMIP6 MRI-ESM2-0 SSP2-4.5 +
historical precipitation NetCDF files that process.py's
export_precipitation_grid_geojson() consumes to build the precipitation
grid layer.

Mirrors fetch_cmip6_fixed.py exactly (same CDS API fixes, same dataset,
model, and experiments) — only the requested variable differs: precipitation
instead of near-surface air temperature. The NetCDF variable inside the
downloaded file is `pr` (precipitation flux, kg m-2 s-1 — converted to
mm/day in process.py).

.cdsapirc format:
    url: https://cds.climate.copernicus.eu/api
    key: YOUR-API-KEY-ONLY   (no UID: prefix)

Run:
    cd Pipeline/
    pip install cdsapi xarray netCDF4 pip-system-certs
    python fetch_cmip6_pr.py
"""

import sys
import logging
import warnings
from pathlib import Path

from fetch_cmip6_fixed import _extract_nc

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

SSP_NC  = RAW / "cmip6_pr_ssp245.nc"
HIST_NC = RAW / "cmip6_pr_historical.nc"

BASELINE_START = 1990

_ALL_MONTHS = [f"{m:02d}" for m in range(1, 13)]

# CDS request fields shared by both historical and SSP requests.
_CDS_COMMON = {
    "download_format":     "zip",            # FIX 1
    "data_format":         "netcdf_legacy",  # FIX 1
    "temporal_resolution": "monthly",
    "variable":            "precipitation",  # CDS-side name; NetCDF variable inside is `pr`
    "model":               "mri_esm2_0",
    "month":               _ALL_MONTHS,      # FIX 3
}


def download_cmip6_pr():
    """Download SSP2-4.5 (2015-2100) and historical (BASELINE_START-2014) pr, global."""
    if SSP_NC.exists() and HIST_NC.exists():
        log.info("CMIP6 precipitation NetCDF files already downloaded — skipping.")
        return

    try:
        import cdsapi
    except ImportError:
        log.error("cdsapi not installed. Run: pip install cdsapi")
        sys.exit(1)

    log.info("Connecting to Copernicus CDS ...")
    client = cdsapi.Client()

    if not SSP_NC.exists():
        ssp_zip = RAW / "cmip6_pr_ssp245.zip"
        log.info("Requesting CMIP6 SSP2-4.5 pr (2015-2100) — global, ~100-800 MB ...")
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
        hist_zip = RAW / "cmip6_pr_historical.zip"
        log.info(f"Requesting CMIP6 historical pr ({BASELINE_START}-2014) ...")
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
    log.info("Climate Atlas -- CMIP6 precipitation grid NetCDF fetch")
    log.info("=" * 60)
    download_cmip6_pr()
    log.info("\nDone. Run: python process.py")


if __name__ == "__main__":
    main()
