"""Parsing rules of the experimental table (catalog.py). See knowledge/dataset/test_matrix_notes.md §5."""
from pathlib import Path

import numpy as np
import pytest

from bass2 import catalog

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "data/docs/Experimental table_BASS-II.csv"


# ------------------------------------------------------------------ air display rules

def test_O13a_swap_cm_s_inside_parentheses():
    """Fan displays outside, cm/s inside the parentheses: never take ~49 as cm/s."""
    p = catalog.parse_air_display("49  44  42  41  41  40.5 (5   2   0)", 2,
                                  "1.3   0.7   0.45   0.36   0.32   0.31")
    assert p["steps"] == [5.0, 2.0, 0.0]
    assert p["rule"] == "swap_paren_cm_s_outside_fan_display"
    assert p["confidence"] == "medium"  # confirmed by pot -> display relation


def test_swap_unconfirmed_by_pots_is_low_confidence():
    p = catalog.parse_air_display("49  44  42 (5   2   0)", 2, "10 9 8")
    assert p["steps"] == [5.0, 2.0, 0.0]
    assert p["confidence"] == "low"


def test_O5a_cm_s_outside_fan_display_inside():
    p = catalog.parse_air_display("5  10  5   2   0 (49   62   49   44   42)", 2,
                                  "1.3   2.7   1.3   0.7   0.45. 4.0")
    assert p["steps"] == [5.0, 10.0, 5.0, 2.0, 0.0]
    assert p["rule"] == "outside_cm_s_paren_fan_display"
    assert p["confidence"] == "high"


def test_O5b_explicit_unit_drops_fan_display():
    p = catalog.parse_air_display("49   5 cm/s", 2, "1.3")
    assert p["steps"] == [5.0]
    assert p["rule"] == "explicit_cm_s_unit"


def test_B10_plain_list():
    p = catalog.parse_air_display("5  4  3  2  1", 2, "1.7 (52)   1.25   0.9   0.6   0.4   0.35")
    assert p["steps"] == [5.0, 4.0, 3.0, 2.0, 1.0]
    assert (p["rule"], p["confidence"]) == ("plain_list", "high")


def test_M10_plain_list_with_fan_drift_in_fan_column():
    p = catalog.parse_air_display("10  17  14  10  8", 2,
                                  "75   105   94/91   72/69   63/61  (4.4   8.0   6.6/6.3   4.0/3.7   3/0/2.7)")
    assert p["steps"] == [10.0, 17.0, 14.0, 10.0, 8.0]
    assert p["confidence"] == "high"


def test_P5_events_are_not_numbers():
    p = catalog.parse_air_display("5 down to ext", 2,
                                  "Fan pot 1.5 (5cm/s)   0.9   0.4   0.36   0.32   0.308   0.3   0.29   0.28   0 ext")
    assert p["steps"] == [5.0]
    assert "extinction" in p["events"] and "decrease" in p["events"]
    assert p["min_upper_bound"]


def test_P5_fan_column_cm_s_used_when_air_empty():
    p = catalog.parse_air_display(None, 2, "Fan pot 1.5 (5cm/s)   0.9   0.4")
    assert p["steps"] == [5.0]
    assert p["rule"] == "fan_column_explicit_cm_s"


def test_T15_two_values_restrictor0():
    p = catalog.parse_air_display("9   29", 0, "80122")
    assert p["steps"] == [9.0, 29.0]
    assert p["confidence"] == "high"


def test_overlap_zone_restrictor0_is_medium():
    p = catalog.parse_air_display("6   53", 0, None)  # T17: 53 cm/s plausible with 0 restrictors
    assert p["steps"] == [6.0, 53.0]
    assert p["confidence"] == "medium"


def test_implausible_value_with_two_restrictors_is_dropped():
    p = catalog.parse_air_display("5  49", 2, None)
    assert p["steps"] == [5.0]
    assert p["rule"] == "dropped_implausible_values"


def test_max_value_in_parentheses_T21():
    p = catalog.parse_air_display("11   max(47)", 0, "1.6 pot   52")
    assert p["steps"] == [11.0, 47.0]
    assert not p["max_lower_bound"]


def test_max_without_value_is_lower_bound():
    p = catalog.parse_air_display("10   max", 0, "1.4    incr to 10.0")
    assert p["steps"] == [10.0]
    assert p["max_lower_bound"]
    p = catalog.parse_air_display("5  8  2  max   0", 2, None)  # P19
    assert p["steps"] == [5.0, 8.0, 2.0, 0.0] and p["max_lower_bound"]


def test_pots_in_air_column_are_ignored():
    assert catalog.parse_air_display("3  0.5 pot   0.4 pot", 2)["steps"] == [3.0]   # B16 (CSV)
    assert catalog.parse_air_display("3, 5 pot, 0.4 pot", 2)["steps"] == [3.0]     # B16 (report)
    assert catalog.parse_air_display("5   3    pot 0.4", 2)["steps"] == [5.0, 3.0]  # B17
    assert catalog.parse_air_display("5   pots 0.4   0.36   0.32   0.308   .3   off", 2)["steps"] == [5.0]
    assert catalog.parse_air_display("5   2.5 (1.15   .5   .35   .33. .32)", 2)["steps"] == [5.0, 2.5]


def test_qualifiers_and_changes():
    p = catalog.parse_air_display("5   3   1   <1", 2)
    assert p["steps"] == [5.0, 3.0, 1.0, 1.0] and p["confidence"] == "medium" and p["min_upper_bound"]
    assert catalog.parse_air_display("10   5>7  5 decr", 2)["steps"] == [10.0, 5.0, 7.0, 5.0]
    assert catalog.parse_air_display("10   3   0ext", 2)["steps"] == [10.0, 3.0, 0.0]
    assert catalog.parse_air_display("5   2(?)", 1)["confidence"] == "medium"
    assert catalog.parse_air_display("10   15 (brief)   10   8", 2)["steps"] == [10.0, 15.0, 10.0, 8.0]


def test_ramps():
    p = catalog.parse_air_display("incr to 28", 0, "46 (pot 0.8)    pot 7   10")  # O21
    assert p["initial_unknown"] and p["rule"] == "ramp_target_only" and p["confidence"] == "low"
    assert catalog.parse_air_display("4 incr to 26.5", 0)["steps"] == [4.0, 26.5]
    assert catalog.parse_air_display("5   8    incr to max 38.5", 0)["steps"] == [5.0, 8.0, 38.5]


def test_fan_column_ignition_velocity_and_no_ignition():
    p = catalog.parse_air_display(None, 2, "5   .36  .32  ..305   blowoff fan max 10")  # O7
    assert p["steps"] == [5.0] and p["rule"] == "fan_column_ignition_velocity"
    p = catalog.parse_air_display("no ign at any flow", 2, "pots 1.4   3   0.9   0.7")  # O12
    assert p["steps"] == [] and "no_ignition" in p["events"] and "ignition" not in p["events"]


# --------------------------------------------------------------------------- geometry

@pytest.mark.parametrize("text, key, value", [
    ('1/2" clear rod ', "rod_diameter_mm", 12.7),
    ('0.5" black rod', "rod_diameter_mm", 12.7),
    ('3/8"clear rod', "rod_diameter_mm", 9.525),
    ("1/4 blac rod", "rod_diameter_mm", 6.35),
    ("4 cm spherical section", "sphere_diameter_mm", 40.0),
    ("4 mm thick   2 cm 2ide PMMA slab", "width_mm", 20.0),
    ("4 mm thick   2 cm 2ide PMMA slab", "thickness_mm", 4.0),
    ("2 cm   4 mm 1 sided PMMA slab", "thickness_mm", 4.0),
    ("2 cm   4 mm 1 sided PMMA slab", "sides_burned", 1),
    ("3 mm thick PMMA   2 sided   2 cm thick", "width_mm", 20.0),
    ("1 cm wide 200 micron thick PMMA", "thickness_mm", 0.2),
    ("2 cm SIBAL", "thickness_mm", 0.32),
])
def test_geometry(text, key, value):
    assert catalog._material(text)[key] == pytest.approx(value)


def test_geometry_classes_and_flags():
    m = catalog._material("1/4 blac rod")
    assert m["rod_color"] == "black" and "typo_blac->black" in m["material_parse_flags"]
    m = catalog._material("4 cm spherical section")
    assert m["material_class"] == "PMMA spherical section" and np.isnan(m["width_mm"])
    assert catalog._material("2 cm   0.4 mm thick film")["geometry"] == "film"
    assert catalog._material("1 mm thick PMMA   2 cm wide")["geometry"] == "slab"
    assert "typo_2ide->wide" in catalog._material("4 mm thick   2 cm 2ide PMMA slab")["material_parse_flags"]


# --------------------------------------------------------------- full table (real data)

@pytest.fixture(scope="module")
def table():
    if not TABLE.exists():
        pytest.skip("experimental table not downloaded")
    return catalog.load_experimental_table(write=False).set_index("test_id")


def test_table_rows_and_backward_compatible_columns(table):
    assert len(table) == 129
    for c in ("fan_steps", "air_steps", "extinction", "blowoff", "no_ignition", "flow_initial_cm_s",
              "air_display_raw", "fan_display_raw", "material_class", "o2_initial_pct"):
        assert c in table.columns
    assert set(table.flow_parse_confidence) <= {"high", "medium", "low"}


@pytest.mark.parametrize("test_id, initial_air", [
    ("O13a", 5), ("O5a", 5), ("B10", 5), ("M10", 10), ("P5", 5), ("T15", 9)])
def test_table_initial_flow(table, test_id, initial_air):
    r = table.loc[test_id]
    assert r.flow_initial_cm_s == pytest.approx(catalog.U_ANEMOMETER_CORR * initial_air)
    assert r.flow_asrun_cm_s == pytest.approx(catalog.U_ANEMOMETER_CORR * initial_air)


def test_table_no_fan_display_taken_as_cm_s(table):
    """Regression for G13: no O test may show ~38-125 'cm/s' coming from fan displays."""
    o = table[table.pi == "Olson"]
    assert (o.flow_initial_cm_s.dropna() < 30).all()
    assert table.loc["O13a"].flow_max_cm_s == pytest.approx(5 * catalog.U_ANEMOMETER_CORR)
    assert all(v <= catalog.AIR_MAX_CM_S * catalog.U_ANEMOMETER_CORR
               for steps in table.flow_steps_cm_s for v in steps)


def test_table_asrun_o2_and_regime(table):
    r = table.loc["B1"]
    assert r.o2_asrun_pct == pytest.approx(22.2) and r.o2_raw_csa_cp_pct == pytest.approx(20.6)
    assert table.loc["P16"].regime == "concurrent"         # per Summary Report App. A
    assert table.loc["O15a"].regime == "stagnation"
    assert table.loc["M10"].regime == "opposed"
    assert table.loc["O20"].regime_source == "pi_default"  # 2016 tests not in the report
    assert set(table.regime) <= {"opposed", "concurrent", "stagnation", "mixed"}
