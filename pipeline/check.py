"""
check.py — validates public/data/*.geojson outputs after running process.py.

Reads already-written files (the 12 grid GeoJSON files plus the
pipeline_diagnostics.json QA sidecar) — no NetCDF/xarray dependency, no
recomputation, fast.

Run: python check.py   (exit 0 = all pass, 1 = any failure)

Design note: checking "are output values within [CLIP_MIN, CLIP_MAX]" would
be tautological, since process.py already clamps every value to exactly that
range before writing the GeoJSON — such a check is guaranteed to pass
regardless of what the underlying model data looks like. The meaningful
checks here instead read pipeline_diagnostics.json, which records values
*before* clipping (clip_applied_count, near-boundary soft-band flags).
"""

import json
import os
import sys

from sources import (
    YEARS,
    OUT_CMIP6_GRID,
    OUT_PRECIP_GRID,
    PIPELINE_DIAGNOSTICS,
    TEMP_ANOMALY_SOFT_MIN,
    TEMP_ANOMALY_SOFT_MAX,
    PR_PCT_SOFT_MIN,
    PR_PCT_SOFT_MAX,
)

_failures = 0


def check(label: str, condition: bool, detail: str = "") -> bool:
    global _failures
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        _failures += 1
    return condition


def info(message: str) -> None:
    print(f"  [INFO] {message}")


def _load(path: str):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def _feature_schema_ok(feat: dict, prop_key: str) -> bool:
    geom = feat.get("geometry", {})
    ring = geom.get("coordinates", [[]])[0]
    props = feat.get("properties", {})
    return (
        geom.get("type") == "Polygon"
        and len(ring) == 5
        and ring[0] == ring[-1]
        and prop_key in props
        and "lat" in props
        and "lon" in props
    )


def check_temperature_grid(diag: dict | None) -> dict[int, int]:
    counts: dict[int, int] = {}
    temp_diag = (diag or {}).get("cmip6_grid", {})
    years_diag = temp_diag.get("years", {})

    for yr in YEARS:
        path = OUT_CMIP6_GRID.format(year=yr)
        fc = _load(path)
        check(f"cmip6_grid_{yr}_exists", fc is not None, path)
        if not fc:
            continue

        feats = fc["features"]
        n = len(feats)
        counts[yr] = n
        check(f"cmip6_grid_{yr}_feature_count_in_range", 10_000 <= n <= 25_000, f"got {n}")
        check(
            f"cmip6_grid_{yr}_schema_ok",
            all(_feature_schema_ok(f, "temp_anomaly") for f in feats[:50]),
        )

    check("cmip6_grid_oslo_anomaly_rises_2030_to_2080", _oslo_check(), "")

    # Non-tautological diagnostics from pipeline_diagnostics.json (pre-clip values)
    if not years_diag:
        info("no pipeline_diagnostics.json temperature stats found — skipping clip/soft-band diagnostics")
    else:
        for yr in YEARS:
            y = years_diag.get(str(yr)) or years_diag.get(yr)
            if not y:
                continue
            clipped = y.get("clip_applied_count", 0)
            info(f"cmip6_grid_{yr}: {clipped} cell(s) altered by clipping")
            lo, hi = y.get("min"), y.get("max")
            if lo is not None and hi is not None and not (TEMP_ANOMALY_SOFT_MIN <= lo and hi <= TEMP_ANOMALY_SOFT_MAX):
                info(
                    f"cmip6_grid_{yr} range [{lo}, {hi}] outside typical "
                    f"[{TEMP_ANOMALY_SOFT_MIN}, {TEMP_ANOMALY_SOFT_MAX}] soft band (not a failure)"
                )

    return counts


def _oslo_check() -> bool:
    def _oslo_val(yr: int):
        fc = _load(OUT_CMIP6_GRID.format(year=yr))
        if not fc or not fc["features"]:
            return None
        nearest = min(
            fc["features"],
            key=lambda f: (f["properties"]["lat"] - 59.91) ** 2 + (f["properties"]["lon"] - 10.75) ** 2,
        )
        return nearest["properties"]["temp_anomaly"]

    o30, o80 = _oslo_val(2030), _oslo_val(2080)
    if o30 is None or o80 is None:
        return False
    return o80 > o30


def check_precipitation_grid(temp_counts: dict[int, int], diag: dict | None) -> None:
    precip_diag = (diag or {}).get("precip_grid", {})
    years_diag = precip_diag.get("years", {})

    check("pipeline_diagnostics_exists", diag is not None, PIPELINE_DIAGNOSTICS)

    for yr in YEARS:
        path = OUT_PRECIP_GRID.format(year=yr)
        fc = _load(path)
        check(f"precip_grid_{yr}_exists", fc is not None, path)
        if not fc:
            continue

        feats = fc["features"]
        n = len(feats)
        check(
            f"precip_grid_{yr}_feature_count_matches_temp_grid",
            n == temp_counts.get(yr),
            f"precip={n} temp={temp_counts.get(yr)} — land masks diverged",
        )
        check(
            f"precip_grid_{yr}_schema_ok",
            all(_feature_schema_ok(f, "precip_change_pct") for f in feats[:50]),
        )

        y = years_diag.get(str(yr)) or years_diag.get(yr)
        if y:
            raw_max = y.get("raw_mm_day_max", 0)
            check(
                f"precip_{yr}_unit_conversion_sane",
                raw_max > 0.5,
                f"max mm/day={raw_max} — check *86400 conversion ran",
            )
            info(
                f"precip_grid_{yr}: {y.get('pct_clip_applied_count', 0)} cell(s) pct-clipped, "
                f"{y.get('baseline_floor_applied_count', 0)} baseline-floored"
            )
            lo, hi = y.get("min_pct"), y.get("max_pct")
            if lo is not None and hi is not None and not (PR_PCT_SOFT_MIN <= lo and hi <= PR_PCT_SOFT_MAX):
                info(
                    f"precip_grid_{yr} pct range [{lo}, {hi}] outside typical "
                    f"[{PR_PCT_SOFT_MIN}, {PR_PCT_SOFT_MAX}] soft band (not a failure)"
                )

    neg = precip_diag.get("raw_negative_mm_day_count")
    if neg is not None:
        total_cells = sum(temp_counts.values()) or 1
        check(
            "precip_raw_negative_mm_day_negligible",
            neg <= 0.01 * total_cells,
            f"{neg} negative raw cells (numerical noise tolerance 1%)",
        )


def main() -> None:
    print("Climate Atlas pipeline checks")
    print("=" * 40)

    diag = _load(PIPELINE_DIAGNOSTICS)

    print("\nTemperature grid:")
    temp_counts = check_temperature_grid(diag)

    print("\nPrecipitation grid:")
    check_precipitation_grid(temp_counts, diag)

    print()
    if _failures:
        print(f"{_failures} check(s) FAILED.")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
