"""
calculations.py — pure numerical logic extracted from process.py.

No file I/O, no third-party imports (stdlib only) — deliberately kept
lightweight so pipeline/tests/test_process.py can import these functions
without pulling in geopandas/numpy/pandas.
"""


def normalise_scores(d: dict[str, float]) -> dict[str, float]:
    """Min-max normalise a {key: value} dict to the [0, 1] range."""
    if not d:
        return {}
    lo, hi = min(d.values()), max(d.values())
    span = hi - lo or 1.0
    return {k: round((v - lo) / span, 4) for k, v in d.items()}


def invert_vulnerability(readiness: float, gain: float) -> float:
    """
    Invert the ND-GAIN formula GAIN = (readiness - vulnerability + 1) / 2 * 100
    to recover vulnerability from readiness and gain, clipped to [0, 1].
    """
    v = readiness + 1.0 - gain / 50.0
    return max(0.0, min(1.0, v))


def compute_temp_anomaly(
    proj_val: float, baseline_val: float, clip_min: float, clip_max: float
) -> tuple[float, bool]:
    """
    Temperature anomaly = proj_val - baseline_val, clipped to
    [clip_min, clip_max]. Negative (cooling) values are preserved, not
    floored to 0. Returns (clipped value, whether clipping was applied).
    """
    raw_val = proj_val - baseline_val
    val = max(clip_min, min(clip_max, raw_val))
    return val, val != raw_val


def compute_precip_pct_change(
    proj_val: float, baseline_val: float, floor: float, clip_min: float, clip_max: float
) -> tuple[float, bool, bool]:
    """
    Percent change in precipitation vs baseline, with a baseline floor to
    avoid dividing by a near-zero baseline, then clipped to
    [clip_min, clip_max]. Returns (pct, floor_applied, clip_applied).
    """
    denom = baseline_val
    floor_applied = denom < floor
    if floor_applied:
        denom = floor
    raw_pct = 100.0 * (proj_val - baseline_val) / denom
    pct = max(clip_min, min(clip_max, raw_pct))
    return pct, floor_applied, pct != raw_pct
