"""Tests for engine.rhythm — pattern parsing, beat math, swing calculation."""

import pytest
from engine.rhythm import parse_pattern, expand_pattern, simple_to_pattern, calc_swing_delays


# ---------------------------------------------------------------------------
# parse_pattern
# ---------------------------------------------------------------------------

class TestParsePattern:

    def test_single_one(self):
        assert parse_pattern("1") == [1]

    def test_multi_entry(self):
        assert parse_pattern("1 1 1 2") == [1, 1, 1, 2]

    def test_with_hold(self):
        assert parse_pattern("1 0") == [1, 0]

    def test_single_two(self):
        assert parse_pattern("2") == [2]

    def test_four_chords_per_bar(self):
        assert parse_pattern("4") == [4]

    def test_complex_pattern(self):
        assert parse_pattern("1 0 0 0 2 2") == [1, 0, 0, 0, 2, 2]

    def test_empty_string_returns_default(self):
        assert parse_pattern("") == [1]

    def test_whitespace_only_returns_default(self):
        assert parse_pattern("   ") == [1]

    def test_extra_whitespace_ignored(self):
        assert parse_pattern("  1  1   2  ") == [1, 1, 2]

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            parse_pattern("-1")

    def test_non_integer_raises(self):
        with pytest.raises(ValueError, match="Invalid pattern"):
            parse_pattern("1 abc 2")

    def test_float_raises(self):
        with pytest.raises(ValueError, match="Invalid pattern"):
            parse_pattern("1.5")


# ---------------------------------------------------------------------------
# expand_pattern
# ---------------------------------------------------------------------------

class TestExpandPattern:

    def test_one_chord_per_bar_4_4(self):
        assert expand_pattern([1], 4) == [4.0]

    def test_two_chords_per_bar_4_4(self):
        assert expand_pattern([2], 4) == [2.0, 2.0]

    def test_four_chords_per_bar_4_4(self):
        assert expand_pattern([4], 4) == [1.0, 1.0, 1.0, 1.0]

    def test_hold_across_two_bars(self):
        assert expand_pattern([1, 0], 4) == [8.0]

    def test_hold_across_four_bars(self):
        assert expand_pattern([1, 0, 0, 0], 4) == [16.0]

    def test_mixed_pattern(self):
        result = expand_pattern([1, 1, 1, 2], 4)
        assert result == [4.0, 4.0, 4.0, 2.0, 2.0]

    def test_three_four_meter(self):
        assert expand_pattern([1], 3) == [3.0]

    def test_hold_in_three_four(self):
        assert expand_pattern([1, 0], 3) == [6.0]

    def test_two_chords_in_three_four(self):
        result = expand_pattern([2], 3)
        assert result == [1.5, 1.5]

    def test_complex_with_holds(self):
        result = expand_pattern([1, 0, 0, 0, 2, 2], 4)
        # Bar 1: 1 chord (4 beats), bars 2-4: hold (+12 beats) = 16 beats
        # Bar 5: 2 chords (2 each), bar 6: 2 chords (2 each)
        assert result == [16.0, 2.0, 2.0, 2.0, 2.0]

    def test_empty_pattern_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            expand_pattern([], 4)

    def test_starts_with_hold_raises(self):
        with pytest.raises(ValueError, match="cannot start with 0"):
            expand_pattern([0, 1], 4)


# ---------------------------------------------------------------------------
# simple_to_pattern
# ---------------------------------------------------------------------------

class TestSimpleToPattern:

    def test_default_one_one(self):
        assert simple_to_pattern(1, 1) == [1]

    def test_two_bars_per_chord(self):
        assert simple_to_pattern(2, 1) == [1, 0]

    def test_four_bars_per_chord(self):
        assert simple_to_pattern(4, 1) == [1, 0, 0, 0]

    def test_two_chords_per_bar(self):
        assert simple_to_pattern(1, 2) == [2]

    def test_four_chords_per_bar(self):
        assert simple_to_pattern(1, 4) == [4]

    def test_both_greater_than_one_raises(self):
        with pytest.raises(ValueError, match="Only one"):
            simple_to_pattern(2, 2)

    def test_zero_bars_raises(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            simple_to_pattern(0, 1)

    def test_zero_chords_raises(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            simple_to_pattern(1, 0)


# ---------------------------------------------------------------------------
# calc_swing_delays
# ---------------------------------------------------------------------------

class TestCalcSwingDelays:

    def test_straight_feel(self):
        long_b, short_b = calc_swing_delays(500.0, 50)
        assert long_b == pytest.approx(500.0)
        assert short_b == pytest.approx(500.0)

    def test_triplet_swing(self):
        long_b, short_b = calc_swing_delays(500.0, 67)
        # pair = 1000, long = 670, short = 330
        assert long_b == pytest.approx(670.0)
        assert short_b == pytest.approx(330.0)

    def test_moderate_swing(self):
        long_b, short_b = calc_swing_delays(500.0, 58)
        assert long_b == pytest.approx(580.0)
        assert short_b == pytest.approx(420.0)

    def test_sum_equals_pair(self):
        """Long + short should always equal 2 * beat_ms."""
        for swing in [50, 55, 60, 65, 67]:
            long_b, short_b = calc_swing_delays(500.0, swing)
            assert long_b + short_b == pytest.approx(1000.0)

    def test_clamp_below_50(self):
        long_b, short_b = calc_swing_delays(500.0, 30)
        assert long_b == pytest.approx(500.0)
        assert short_b == pytest.approx(500.0)

    def test_clamp_above_67(self):
        long_b, short_b = calc_swing_delays(500.0, 90)
        assert long_b == pytest.approx(670.0)
        assert short_b == pytest.approx(330.0)
