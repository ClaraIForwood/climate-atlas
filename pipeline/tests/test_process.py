"""
Unit tests for the pure calculation functions extracted from process.py
into calculations.py. Synthetic inputs only — no NetCDF/CSV files touched.
"""

import pytest

from calculations import (
    normalise_scores,
    invert_vulnerability,
    compute_temp_anomaly,
    compute_precip_pct_change,
)
from sources import (
    TEMP_ANOMALY_CLIP_MIN,
    TEMP_ANOMALY_CLIP_MAX,
    PR_BASELINE_FLOOR_MM_DAY,
    PR_PCT_CLIP_MIN,
    PR_PCT_CLIP_MAX,
)


# ---------------------------------------------------------------------------
# normalise_scores
# ---------------------------------------------------------------------------

def test_normalise_scores_multiple_distinct_values():
    result = normalise_scores({"A": 10.0, "B": 20.0, "C": 30.0})
    assert result == pytest.approx({"A": 0.0, "B": 0.5, "C": 1.0})


def test_normalise_scores_all_identical_values():
    # Guards the `span = hi - lo or 1.0` divide-by-zero fallback.
    result = normalise_scores({"A": 5.0, "B": 5.0, "C": 5.0})
    assert result == pytest.approx({"A": 0.0, "B": 0.0, "C": 0.0})


def test_normalise_scores_single_entry():
    result = normalise_scores({"A": 7.0})
    assert result == pytest.approx({"A": 0.0})


def test_normalise_scores_empty_dict():
    assert normalise_scores({}) == {}


# ---------------------------------------------------------------------------
# invert_vulnerability
# ---------------------------------------------------------------------------

def test_invert_vulnerability_round_trip():
    # GAIN = (readiness - vulnerability + 1) / 2 * 100
    readiness, vulnerability = 0.6, 0.3
    gain = (readiness - vulnerability + 1.0) / 2.0 * 100.0
    recovered = invert_vulnerability(readiness, gain)
    assert recovered == pytest.approx(vulnerability)


def test_invert_vulnerability_clips_at_upper_boundary():
    # readiness=1.0, gain=0.0 -> raw v = 1.0 + 1.0 - 0.0/50.0 = 2.0 -> clipped to 1.0
    assert invert_vulnerability(1.0, 0.0) == 1.0


def test_invert_vulnerability_clips_at_lower_boundary():
    # readiness=0.0, gain=100.0 -> raw v = 0.0 + 1.0 - 100.0/50.0 = -1.0 -> clipped to 0.0
    assert invert_vulnerability(0.0, 100.0) == 0.0


# ---------------------------------------------------------------------------
# compute_temp_anomaly
# ---------------------------------------------------------------------------

def test_compute_temp_anomaly_inside_range_unchanged():
    val, clipped = compute_temp_anomaly(15.0, 14.5, TEMP_ANOMALY_CLIP_MIN, TEMP_ANOMALY_CLIP_MAX)
    assert val == pytest.approx(0.5)
    assert clipped is False


def test_compute_temp_anomaly_above_max_is_clipped():
    val, clipped = compute_temp_anomaly(30.0, 15.0, TEMP_ANOMALY_CLIP_MIN, TEMP_ANOMALY_CLIP_MAX)
    assert val == TEMP_ANOMALY_CLIP_MAX
    assert clipped is True


def test_compute_temp_anomaly_cooling_value_preserved_not_floored():
    # A real, negative (cooling) anomaly inside the clip range must be
    # returned as-is, not floored to 0.0 — this is real single-run
    # internal-variability signal, not a data error.
    val, clipped = compute_temp_anomaly(14.2, 14.5, TEMP_ANOMALY_CLIP_MIN, TEMP_ANOMALY_CLIP_MAX)
    assert val == pytest.approx(-0.3)
    assert clipped is False


def test_compute_temp_anomaly_below_min_is_clipped():
    val, clipped = compute_temp_anomaly(10.0, 13.0, TEMP_ANOMALY_CLIP_MIN, TEMP_ANOMALY_CLIP_MAX)
    assert val == TEMP_ANOMALY_CLIP_MIN
    assert clipped is True


# ---------------------------------------------------------------------------
# compute_precip_pct_change
# ---------------------------------------------------------------------------

def test_compute_precip_pct_change_baseline_above_floor_not_floored():
    pct, floor_applied, clip_applied = compute_precip_pct_change(
        6.0, 5.0, PR_BASELINE_FLOOR_MM_DAY, PR_PCT_CLIP_MIN, PR_PCT_CLIP_MAX
    )
    assert pct == pytest.approx(20.0)
    assert floor_applied is False
    assert clip_applied is False


def test_compute_precip_pct_change_baseline_exactly_at_floor_not_floored():
    # denom < floor is a strict inequality — exact equality does NOT trigger
    # the floor.
    pct, floor_applied, clip_applied = compute_precip_pct_change(
        0.6, PR_BASELINE_FLOOR_MM_DAY, PR_BASELINE_FLOOR_MM_DAY, PR_PCT_CLIP_MIN, PR_PCT_CLIP_MAX
    )
    assert floor_applied is False
    assert pct == pytest.approx(20.0)
    assert clip_applied is False


def test_compute_precip_pct_change_baseline_below_floor_prevents_blowup():
    # Without the floor, a near-zero baseline would blow raw_pct up to
    # ~49900%. With the floor applied, the result stays bounded/reasonable.
    pct, floor_applied, clip_applied = compute_precip_pct_change(
        0.5, 0.001, PR_BASELINE_FLOOR_MM_DAY, PR_PCT_CLIP_MIN, PR_PCT_CLIP_MAX
    )
    assert floor_applied is True
    assert pct == pytest.approx(99.8)
    assert clip_applied is False


def test_compute_precip_pct_change_above_clip_max_is_clipped():
    pct, floor_applied, clip_applied = compute_precip_pct_change(
        10.0, 1.0, PR_BASELINE_FLOOR_MM_DAY, PR_PCT_CLIP_MIN, PR_PCT_CLIP_MAX
    )
    assert floor_applied is False
    assert pct == PR_PCT_CLIP_MAX
    assert clip_applied is True


def test_compute_precip_pct_change_below_clip_min_is_clipped():
    # A severe drying case (precipitation effectively disappears relative
    # to baseline) — mirrors the temperature side's negative-value handling,
    # but here the magnitude genuinely exceeds the clip range and should be
    # clipped, not preserved.
    pct, floor_applied, clip_applied = compute_precip_pct_change(
        0.0, 10.0, PR_BASELINE_FLOOR_MM_DAY, PR_PCT_CLIP_MIN, PR_PCT_CLIP_MAX
    )
    assert floor_applied is False
    assert pct == PR_PCT_CLIP_MIN
    assert clip_applied is True
