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
