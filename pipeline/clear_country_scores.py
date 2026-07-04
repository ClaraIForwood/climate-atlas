"""
Removes the approximated ND-GAIN scores from countries.geojson.
The Natural Earth geometry is real; the scores I assigned were guesses.
Sets vulnerability and readiness to null on all features.

To populate these fields properly, download the real ND-GAIN dataset from:
  https://gain.nd.edu/our-work/country-index/download-data/
and run process.py with the real ndgain_scores.csv in Pipeline/raw_data/.
"""
import json
from pathlib import Path

path = Path(__file__).parent.parent / "public" / "data" / "countries.geojson"

with open(path, encoding="utf-8") as f:
    gj = json.load(f)

for feat in gj["features"]:
    feat["properties"]["vulnerability"] = None
    feat["properties"]["readiness"]     = None
    # Remove the pre-computed score properties added by fix_countries.py
    for key in ("score", "score_v", "score_r", "score_blend"):
        feat["properties"].pop(key, None)

with open(path, "w", encoding="utf-8") as f:
    json.dump(gj, f, separators=(",", ":"), ensure_ascii=False)

print(f"Cleared ND-GAIN scores from {len(gj['features'])} country features.")
print("Country geometries (Natural Earth 110m) retained — these are real.")
print()
print("To restore scores with real data:")
print("  1. Download ND-GAIN country index CSV from https://gain.nd.edu/our-work/country-index/download-data/")
print("  2. Place it at Pipeline/raw_data/ndgain_scores.csv")
print("  3. Run: python process.py  (requires all raw data files)")
