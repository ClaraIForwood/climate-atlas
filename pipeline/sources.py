import os

# --- TIME STEPS ---
YEARS = [2030, 2040, 2050, 2060, 2070, 2080]
YEAR_INDICES = {y: i for i, y in enumerate(YEARS)}

# --- SCENARIO ---
CMIP6_SCENARIO = "ssp245"
BASELINE_YEAR = 1990

# --- FILE PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

RAW_DIR = os.path.join(BASE_DIR, "raw_data")
RAW_NDGAIN_RAW_PATH  = os.path.join(RAW_DIR, "ndgain_raw.csv")
RAW_NDGAIN_GAIN_PATH = os.path.join(RAW_DIR, "resources", "gain", "gain.csv")
RAW_COUNTRIES_GEOJSON = os.path.join(RAW_DIR, "ne_110m_admin_0_countries.geojson")

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "public", "data")
OUT_COUNTRIES = os.path.join(OUTPUT_DIR, "countries.geojson")
OUT_META = os.path.join(OUTPUT_DIR, "meta.json")

RAW_HIST_NC    = os.path.join(RAW_DIR, "cmip6_tas_historical.nc")
RAW_SSP_NC     = os.path.join(RAW_DIR, "cmip6_tas_ssp245.nc")
OUT_CMIP6_GRID = os.path.join(OUTPUT_DIR, "cmip6_grid_{year}.geojson")

RAW_PR_HIST_NC  = os.path.join(RAW_DIR, "cmip6_pr_historical.nc")
RAW_PR_SSP_NC   = os.path.join(RAW_DIR, "cmip6_pr_ssp245.nc")
OUT_PRECIP_GRID = os.path.join(OUTPUT_DIR, "precip_grid_{year}.geojson")

# QA sidecar — pre-clip diagnostics for check.py. Internal to the pipeline, not a public asset.
PIPELINE_DIAGNOSTICS = os.path.join(BASE_DIR, "pipeline_diagnostics.json")

# --- PRECIPITATION UNIT CONVERSION + FRAMING ---
PR_MM_PER_DAY            = 86400.0  # kg m-2 s-1 -> mm/day
PR_BASELINE_FLOOR_MM_DAY = 0.5      # denominator floor — prevents divide-by-near-zero in arid/polar cells
PR_PCT_CLIP_MIN          = -95.0    # hard clip (can't be < -100% of baseline)
PR_PCT_CLIP_MAX          = 300.0    # hard clip (bounds the colour scale)
PR_PCT_SOFT_MIN          = -50.0    # "typical" band — outside this is an [INFO] flag only, not a failure
PR_PCT_SOFT_MAX          = 100.0

# --- TEMPERATURE ANOMALY CLIP RANGE ---
# Replaces the old hardcoded max(0.0, min(8.0, val)). Empirically grounded: land-only raw
# range across all 6 decades is [-0.397, 9.181]°C (verified directly against the NetCDF).
# The old range silently floored negative (cooling) signal to 0.0 and already clipped
# 2060/2070 at the old 8.0 cap.
TEMP_ANOMALY_CLIP_MIN = -1.0   # was 0.0 — now preserves real single-run cooling signal
TEMP_ANOMALY_CLIP_MAX = 10.0   # was 8.0 — now covers the observed 9.18°C 2060 land max

# Soft/"typical" band for check.py's near-boundary INFO diagnostic — mirrors PR_PCT_SOFT_*.
# NOT a pass/fail bound (that would be tautological against a value already clamped to it);
# only flags cells sitting close enough to the hard clip that truncation may be occurring.
TEMP_ANOMALY_SOFT_MIN = -0.5
TEMP_ANOMALY_SOFT_MAX = 9.0
