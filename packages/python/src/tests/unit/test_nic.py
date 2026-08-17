"""
Author: Sean Froning
Created Date: 6.3.2026
Unit tests for NICUtils acuity mix calculations
"""

from focus_python import NICUtils, Property


def test_acuity_mix_uses_total_units():
    prop = Property(
        total_units=100,
        cottage_units=10,
        independent_units=20,
        assisted_units=30,
        memory_units=40,
    )
    mix = NICUtils._acuity_mix(prop)
    assert mix == {
        "pct_cottage": 0.1,
        "pct_il": 0.2,
        "pct_al": 0.3,
        "pct_mc": 0.4,
    }


def test_acuity_mix_derives_total_from_unit_counts():
    prop = Property(
        cottage_units=5,
        independent_units=5,
        assisted_units=5,
        memory_units=5,
    )
    mix = NICUtils._acuity_mix(prop)
    assert mix["pct_cottage"] == 0.25
    assert mix["pct_il"] == 0.25
    assert mix["pct_al"] == 0.25
    assert mix["pct_mc"] == 0.25


def test_acuity_mix_returns_zeros_when_no_units():
    prop = Property()
    mix = NICUtils._acuity_mix(prop)
    assert mix == {
        "pct_cottage": 0.0,
        "pct_il": 0.0,
        "pct_al": 0.0,
        "pct_mc": 0.0,
    }
