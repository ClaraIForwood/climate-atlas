"""
Main pipeline script: ingest -> enrich -> export.

Run from the pipeline/ directory:
    python process.py

Reads raw CSVs/GeoJSON/NetCDF from pipeline/raw_data/, writes to
public/data/: countries.geojson, meta.json, cmip6_grid_{year}.geojson,
precip_grid_{year}.geojson. Also writes pipeline/pipeline_diagnostics.json
(pre-clip QA stats, internal — not a public asset) for check.py to read.
"""

import json
import os
from datetime import datetime, timezone

import geopandas as gpd
import numpy as np
import pandas as pd

from calculations import (
    normalise_scores,
    invert_vulnerability,
    compute_temp_anomaly,
    compute_precip_pct_change,
)
from sources import (
    CMIP6_SCENARIO,
    BASELINE_YEAR,
    YEARS,
    RAW_NDGAIN_RAW_PATH,
    RAW_NDGAIN_GAIN_PATH,
    RAW_COUNTRIES_GEOJSON,
    RAW_HIST_NC,
    RAW_SSP_NC,
    OUT_CMIP6_GRID,
    RAW_PR_HIST_NC,
    RAW_PR_SSP_NC,
    OUT_PRECIP_GRID,
    PIPELINE_DIAGNOSTICS,
    PR_MM_PER_DAY,
    PR_BASELINE_FLOOR_MM_DAY,
    PR_PCT_CLIP_MIN,
    PR_PCT_CLIP_MAX,
    TEMP_ANOMALY_CLIP_MIN,
    TEMP_ANOMALY_CLIP_MAX,
    OUT_COUNTRIES,
    OUT_META,
    OUTPUT_DIR,
)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_countries() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(RAW_COUNTRIES_GEOJSON)
    print(f"  Loaded {len(gdf):,} country polygons")
    return gdf


# ---------------------------------------------------------------------------
# Country ND-GAIN enrichment
# ---------------------------------------------------------------------------

def _load_ndgain_scores_by_iso3() -> dict[str, dict[str, float]]:
    """
    Derive readiness and vulnerability for every country from the two raw files:
      ndgain_raw.csv  — readiness (0-1 scale, annual)
      gain.csv        — overall ND-GAIN score (0-100 scale, annual)

    ND-GAIN formula:  GAIN = (readiness - vulnerability + 1) / 2 × 100
    Inverted:         vulnerability = readiness + 1 - GAIN/50

    Both are then min-max normalised globally so the full 0-1 scale is used
    for the choropleth colour ramp.

    Returns {ISO3: {"readiness": float, "vulnerability": float}}
    """
    def _latest(df: pd.DataFrame) -> dict[str, float]:
        year_cols = [c for c in df.columns if c.isdigit()]
        out: dict[str, float] = {}
        for _, row in df.iterrows():
            iso3 = str(row.get("ISO3", "")).strip().upper()
            if not iso3:
                continue
            for yr in reversed(year_cols):
                v = pd.to_numeric(row[yr], errors="coerce")
                if pd.notna(v):
                    out[iso3] = float(v)
                    break
        return out

    readiness_raw = _latest(pd.read_csv(RAW_NDGAIN_RAW_PATH))   # 0-1 scale
    gain_raw      = _latest(pd.read_csv(RAW_NDGAIN_GAIN_PATH))  # 0-100 scale

    # Compute raw vulnerability for countries that have both files
    vuln_raw: dict[str, float] = {}
    for iso3, r in readiness_raw.items():
        g = gain_raw.get(iso3)
        if g is not None:
            vuln_raw[iso3] = invert_vulnerability(r, g)

    r_norm = normalise_scores(readiness_raw)
    v_norm = normalise_scores(vuln_raw)

    all_iso3 = set(r_norm) | set(v_norm)
    return {
        iso3: {
            "readiness":     r_norm.get(iso3, float("nan")),
            "vulnerability": v_norm.get(iso3, float("nan")),
        }
        for iso3 in all_iso3
    }


def build_countries_geojson(countries_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Enrich Natural Earth polygons with ND-GAIN readiness scores.

    Primary join: ISO_A3 → ndgain_raw.csv (covers ~180 countries).
    The ISO_A3 column in Natural Earth is reliable for nearly all countries,
    unlike ISO_A2 which has -99 entries for Norway, France, Kosovo, etc.
    """
    iso3_col = next((c for c in countries_gdf.columns
                     if c.upper() in ("ISO_A3", "ISO3", "ADM0_A3")), None)

    # Load globally-normalised readiness + vulnerability for all countries
    iso3_scores = _load_ndgain_scores_by_iso3()

    countries_gdf = countries_gdf.copy()

    def _lookup(row) -> tuple[float, float]:
        if iso3_col:
            iso3 = str(row[iso3_col]).strip().upper()
            if iso3 and iso3 != "-99" and iso3 in iso3_scores:
                s = iso3_scores[iso3]
                return s["readiness"], s["vulnerability"]
        return float("nan"), float("nan")

    results = countries_gdf.apply(_lookup, axis=1, result_type="expand")
    countries_gdf["readiness"]     = results[0]
    countries_gdf["vulnerability"] = results[1]

    r_matched = countries_gdf["readiness"].notna().sum()
    v_matched = countries_gdf["vulnerability"].notna().sum()
    print(f"  Joined ND-GAIN readiness to {r_matched}/{len(countries_gdf)} countries")
    print(f"  Joined ND-GAIN vulnerability to {v_matched}/{len(countries_gdf)} countries")
    return countries_gdf


def write_meta() -> None:
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario": CMIP6_SCENARIO,
        "baseline_year": BASELINE_YEAR,
        "projection_years": YEARS,
        "variables": {
            "temp_anomaly": {
                "description": f"Projected temperature anomaly above {BASELINE_YEAR} baseline (°C), CMIP6 global grid",
                "source": f"CMIP6 {CMIP6_SCENARIO}",
            },
            "precip_change_pct": {
                "description": f"Projected precipitation change vs {BASELINE_YEAR} baseline (% of baseline daily mean), CMIP6 global grid",
                "source": f"CMIP6 {CMIP6_SCENARIO}",
            },
            "vulnerability": {
                "description": "Country ND-GAIN vulnerability score (0–1, lower is less vulnerable)",
                "source": "Notre Dame Global Adaptation Initiative (ND-GAIN)",
            },
            "readiness": {
                "description": "Country ND-GAIN readiness score (0–1, higher is more ready)",
                "source": "Notre Dame Global Adaptation Initiative (ND-GAIN)",
            },
        },
    }
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"  Wrote {OUT_META}")


# ---------------------------------------------------------------------------
# CMIP6 global grid export
# ---------------------------------------------------------------------------

GRID_HALF_DEG = 0.5625  # half of 1.125° grid spacing


def _build_land_mask(countries_gdf: gpd.GeoDataFrame, lats: np.ndarray, lons: np.ndarray):
    """
    Spatial-join grid-cell centres against country polygons -> land cell set.

    Shared by both grid exporters so land coverage is IDENTICAL between the
    temperature and precipitation layers — a mismatch would show up as a
    visual/geometric discrepancy between the two fills, and check.py
    cross-validates feature counts between the two layers to guard against
    this drifting apart.

    Returns (land_set: set[(lat_i, lon_i)], lons_180: np.ndarray).
    """
    from shapely.geometry import Point

    n_lat, n_lon = len(lats), len(lons)
    lons_180 = np.where(lons > 180, lons - 360, lons)

    lat_grid, lon_grid = np.meshgrid(lats, lons_180, indexing="ij")  # (160, 320)
    flat_lat_idx = np.repeat(np.arange(n_lat), n_lon)
    flat_lon_idx = np.tile(np.arange(n_lon), n_lat)

    points_gdf = gpd.GeoDataFrame(
        {"lat_i": flat_lat_idx, "lon_i": flat_lon_idx},
        geometry=[Point(lo, la) for la, lo in zip(lat_grid.ravel(), lon_grid.ravel())],
        crs="EPSG:4326",
    )

    land_gdf = countries_gdf[["geometry"]].copy().to_crs("EPSG:4326")
    joined = gpd.sjoin(points_gdf, land_gdf, how="inner", predicate="within")
    land_set = set(zip(joined["lat_i"].values, joined["lon_i"].values))
    print(f"  Land cells: {len(land_set):,} of {n_lat * n_lon:,}")
    return land_set, lons_180


def export_cmip6_grid_geojson(countries_gdf: gpd.GeoDataFrame) -> dict:
    """
    Export the CMIP6 temperature anomaly field as per-decade GeoJSON polygon files.
    Land cells only (ocean cells skipped). One file per year in YEARS.
    Anomaly = 5-year symmetric window mean (SSP2-4.5) minus 1990-2014 baseline mean.

    Values are clipped to [TEMP_ANOMALY_CLIP_MIN, TEMP_ANOMALY_CLIP_MAX] as a sanity
    guard, but — unlike the old version of this function — negative (cooling)
    values are preserved rather than floored to 0.0; single CMIP6 runs can show
    real, if noisy, cooling relative to baseline in specific cells/decades due to
    internal variability, and silently flattening that to "no change" misrepresents
    the projection. See sources.py for the empirical grounding of the clip range.

    Returns a stats dict for check.py to validate (no printed pass/fail here —
    validation responsibility now lives in check.py, reading the written files).
    """
    import xarray as xr

    print("\n[3/4] Exporting CMIP6 temperature grid GeoJSON...")

    for nc_path in (RAW_HIST_NC, RAW_SSP_NC):
        if not os.path.exists(nc_path):
            print(f"  WARNING: {nc_path} not found — skipping grid export")
            return {}

    # ── Load NetCDF files into numpy ───────────────────────────────────────
    print("  Loading historical NetCDF...")
    ds_hist = xr.open_dataset(RAW_HIST_NC)
    hist_tas = ds_hist["tas"].values          # (300, 160, 320) Kelvin
    lats = ds_hist["lat"].values              # (160,)
    lons = ds_hist["lon"].values              # (320,) 0–360
    ds_hist.close()

    print("  Loading SSP2-4.5 NetCDF...")
    ds_ssp = xr.open_dataset(RAW_SSP_NC)
    ssp_tas = ds_ssp["tas"].values            # (1032, 160, 320) Kelvin
    ssp_years = pd.DatetimeIndex(ds_ssp["time"].values).year.values  # (1032,)
    ds_ssp.close()

    # ── Baseline: 1990-2014 mean ───────────────────────────────────────────
    baseline_2d = hist_tas.mean(axis=0)      # (160, 320) Kelvin

    # ── Land mask via spatial join ─────────────────────────────────────────
    print("  Building land mask via spatial join...")
    land_set, lons_180 = _build_land_mask(countries_gdf, lats, lons)

    # ── Per-decade precompute year masks ───────────────────────────────────
    year_masks = {
        yr: (ssp_years >= yr - 2) & (ssp_years <= yr + 2)
        for yr in YEARS
    }

    oslo_lat_i = int(np.argmin(np.abs(lats - 59.91)))
    oslo_lon_i = int(np.argmin(np.abs(lons - 10.75)))

    years_stats: dict[int, dict] = {}
    oslo_anomalies: dict[int, float] = {}
    global_min, global_max = float("inf"), float("-inf")

    for yr in YEARS:
        mask = year_masks[yr]
        proj_2d = ssp_tas[mask].mean(axis=0)           # (160, 320) Kelvin
        anomaly_2d = proj_2d - baseline_2d             # °C (K difference)

        features: list[dict] = []
        clip_applied_count = 0

        for lat_i, lon_i in land_set:
            lon_c = float(lons_180[lon_i])
            lat_c = float(lats[lat_i])

            w = lon_c - GRID_HALF_DEG
            e = lon_c + GRID_HALF_DEG

            # Skip cells whose polygon would cross the antimeridian
            if w < -180 or e > 180:
                continue

            s = lat_c - GRID_HALF_DEG
            n = lat_c + GRID_HALF_DEG

            val, clip_applied = compute_temp_anomaly(
                float(proj_2d[lat_i, lon_i]), float(baseline_2d[lat_i, lon_i]),
                TEMP_ANOMALY_CLIP_MIN, TEMP_ANOMALY_CLIP_MAX,
            )
            if clip_applied:
                clip_applied_count += 1

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [round(w, 6), round(s, 6)],
                        [round(w, 6), round(n, 6)],
                        [round(e, 6), round(n, 6)],
                        [round(e, 6), round(s, 6)],
                        [round(w, 6), round(s, 6)],
                    ]],
                },
                "properties": {
                    "temp_anomaly": round(val, 3),
                    "lat": round(lat_c, 4),
                    "lon": round(lon_c, 4),
                },
            })

        out_path = OUT_CMIP6_GRID.format(year=yr)
        fc = {"type": "FeatureCollection", "features": features}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(fc, f, separators=(",", ":"))

        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        n_feat = len(features)
        all_vals = [feat["properties"]["temp_anomaly"] for feat in features]
        lo, hi = min(all_vals), max(all_vals)
        global_min, global_max = min(global_min, lo), max(global_max, hi)

        print(f"  cmip6_grid_{yr}.geojson — {n_feat:,} features, {size_mb:.1f} MB, "
              f"range [{lo:.3f}, {hi:.3f}], clipped {clip_applied_count}")

        oslo_anomalies[yr] = round(float(anomaly_2d[oslo_lat_i, oslo_lon_i]), 3)
        years_stats[yr] = {
            "n_features": n_feat,
            "min": lo,
            "max": hi,
            "clip_applied_count": clip_applied_count,
        }

    print("\n  CMIP6 grid summary:")
    print(f"  {'Year':>6}  {'Min°C':>7}  {'Max°C':>7}  {'Features':>9}  {'Clipped':>7}")
    for yr, s in years_stats.items():
        print(f"  {yr:>6}  {s['min']:>7.3f}  {s['max']:>7.3f}  {s['n_features']:>9,}  {s['clip_applied_count']:>7,}")
    print("  Run `python check.py` to validate against expected ranges.")

    return {
        "years": years_stats,
        "oslo_anomaly_by_year": oslo_anomalies,
        "global_min": global_min,
        "global_max": global_max,
    }


# ---------------------------------------------------------------------------
# CMIP6 precipitation grid export
# ---------------------------------------------------------------------------

def export_precipitation_grid_geojson(countries_gdf: gpd.GeoDataFrame) -> dict:
    """
    Export CMIP6 precipitation change as per-decade GeoJSON polygon files.
    Value = % change in mean daily precipitation (mm/day) vs the 1990-2014
    baseline, land cells only. Mirrors export_cmip6_grid_geojson's structure
    (shared land mask, same 5-year symmetric windows, same GRID_HALF_DEG
    polygons) but is framed as a percent, matching the temperature layer's
    anomaly framing (both layers show "how much has this changed", not one
    absolute + one relative).

    IMPORTANT DEVIATION from the temperature exporter: temperature clips to
    [TEMP_ANOMALY_CLIP_MIN, TEMP_ANOMALY_CLIP_MAX] but preserves negative
    values as real cooling signal. Precipitation must ALSO preserve negative
    values (drying — Mediterranean, Amazon, southern Africa — is a real,
    important AR6 signal), but must NOT floor them to 0 the way temperature
    used to. Only a symmetric [PR_PCT_CLIP_MIN, PR_PCT_CLIP_MAX] clip is
    applied to the percent-change value itself.
    """
    import xarray as xr

    print("\n[4/4] Exporting CMIP6 precipitation grid GeoJSON...")

    for nc_path in (RAW_PR_HIST_NC, RAW_PR_SSP_NC):
        if not os.path.exists(nc_path):
            print(f"  WARNING: {nc_path} not found — skipping precipitation grid export")
            return {}

    print("  Loading historical NetCDF...")
    ds_hist = xr.open_dataset(RAW_PR_HIST_NC)
    hist_pr_raw = ds_hist["pr"].values         # kg m-2 s-1
    lats = ds_hist["lat"].values
    lons = ds_hist["lon"].values
    ds_hist.close()

    print("  Loading SSP2-4.5 NetCDF...")
    ds_ssp = xr.open_dataset(RAW_PR_SSP_NC)
    ssp_pr_raw = ds_ssp["pr"].values
    ssp_years = pd.DatetimeIndex(ds_ssp["time"].values).year.values
    ds_ssp.close()

    # Unit conversion: kg m-2 s-1 -> mm/day. Clip physically-impossible negative
    # precipitation (numerical noise only) and track how often it occurs.
    raw_negative_mm_day_count = int((hist_pr_raw < 0).sum() + (ssp_pr_raw < 0).sum())
    hist_pr = np.clip(hist_pr_raw * PR_MM_PER_DAY, 0.0, None)
    ssp_pr  = np.clip(ssp_pr_raw  * PR_MM_PER_DAY, 0.0, None)

    baseline_2d = hist_pr.mean(axis=0)

    print("  Building land mask via spatial join...")
    land_set, lons_180 = _build_land_mask(countries_gdf, lats, lons)

    year_masks = {
        yr: (ssp_years >= yr - 2) & (ssp_years <= yr + 2)
        for yr in YEARS
    }

    years_stats: dict[int, dict] = {}
    floor_applied_total = 0

    for yr in YEARS:
        proj_2d = ssp_pr[year_masks[yr]].mean(axis=0)

        features: list[dict] = []
        floor_applied_count = 0
        pct_clip_applied_count = 0

        for lat_i, lon_i in land_set:
            lon_c = float(lons_180[lon_i])
            lat_c = float(lats[lat_i])

            w = lon_c - GRID_HALF_DEG
            e = lon_c + GRID_HALF_DEG
            if w < -180 or e > 180:
                continue
            s = lat_c - GRID_HALF_DEG
            n = lat_c + GRID_HALF_DEG

            base_val = float(baseline_2d[lat_i, lon_i])
            proj_val = float(proj_2d[lat_i, lon_i])

            pct, floor_applied, clip_applied = compute_precip_pct_change(
                proj_val, base_val, PR_BASELINE_FLOOR_MM_DAY,
                PR_PCT_CLIP_MIN, PR_PCT_CLIP_MAX,
            )
            if floor_applied:
                floor_applied_count += 1
            if clip_applied:
                pct_clip_applied_count += 1

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [round(w, 6), round(s, 6)],
                        [round(w, 6), round(n, 6)],
                        [round(e, 6), round(n, 6)],
                        [round(e, 6), round(s, 6)],
                        [round(w, 6), round(s, 6)],
                    ]],
                },
                "properties": {
                    "precip_change_pct": round(pct, 1),
                    "lat": round(lat_c, 4),
                    "lon": round(lon_c, 4),
                },
            })

        out_path = OUT_PRECIP_GRID.format(year=yr)
        fc = {"type": "FeatureCollection", "features": features}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(fc, f, separators=(",", ":"))

        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        n_feat = len(features)
        all_pct = [feat["properties"]["precip_change_pct"] for feat in features]
        lo, hi = min(all_pct), max(all_pct)

        print(f"  precip_grid_{yr}.geojson — {n_feat:,} features, {size_mb:.1f} MB, "
              f"pct range [{lo:.1f}, {hi:.1f}], baseline-floored {floor_applied_count}, "
              f"pct-clipped {pct_clip_applied_count}")

        years_stats[yr] = {
            "n_features": n_feat,
            "min_pct": lo,
            "max_pct": hi,
            "raw_mm_day_max": float(proj_2d.max()),
            "baseline_floor_applied_count": floor_applied_count,
            "pct_clip_applied_count": pct_clip_applied_count,
        }
        floor_applied_total += floor_applied_count

    print(f"\n  Baseline floor (<{PR_BASELINE_FLOOR_MM_DAY} mm/day) applied to "
          f"{floor_applied_total} (cell,year) combos.")
    print("  Run `python check.py` to validate against expected ranges.")

    return {
        "years": years_stats,
        "raw_negative_mm_day_count": raw_negative_mm_day_count,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("Climate Atlas pipeline")
    print("=" * 40)
    _ensure_output_dir()

    print("\n[1/4] Loading raw data...")
    countries_raw = load_countries()

    print("\n[2/4] Building countries GeoJSON + meta...")
    countries_enriched = build_countries_geojson(countries_raw)
    countries_enriched.to_file(OUT_COUNTRIES, driver="GeoJSON")
    print(f"  Wrote {OUT_COUNTRIES}")
    write_meta()

    temp_stats = export_cmip6_grid_geojson(countries_raw)
    precip_stats = export_precipitation_grid_geojson(countries_raw)

    with open(PIPELINE_DIAGNOSTICS, "w", encoding="utf-8") as f:
        json.dump({"cmip6_grid": temp_stats, "precip_grid": precip_stats}, f, indent=2)
    print(f"\n  Wrote {PIPELINE_DIAGNOSTICS}")

    print("\nDone.")
    print(f"  {len(countries_enriched)} countries")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
