"""Tests for engine.turing — TuringRegister (16-bit shift register)."""

import random as rng

import pytest
from engine.turing import TuringRegister


# ---------------------------------------------------------------------------
# Construction and initialization
# ---------------------------------------------------------------------------

class TestTuringInit:

    def test_explicit_seed_sets_register(self):
        reg = TuringRegister(seed=0xBEEF, length=8)
        assert reg.get_state() == 0xBEEF

    def test_default_seed_is_random_16bit(self):
        reg = TuringRegister()
        assert 0 <= reg.get_state() <= 0xFFFF

    def test_two_default_seeds_differ(self):
        a = TuringRegister()
        b = TuringRegister()
        # 1/65536 chance of false failure — acceptable
        assert a.get_state() != b.get_state()

    def test_length_clamp_minimum(self):
        reg = TuringRegister(seed=0, length=0)
        assert reg.length == 2

    def test_length_clamp_maximum(self):
        reg = TuringRegister(seed=0, length=99)
        assert reg.length == 16

    @pytest.mark.parametrize("n", [2, 8, 16])
    def test_length_in_range_preserved(self, n):
        reg = TuringRegister(seed=0, length=n)
        assert reg.length == n

    def test_default_probability_is_zero(self):
        reg = TuringRegister(seed=0)
        assert reg.probability == 0.0


# ---------------------------------------------------------------------------
# Deterministic behavior (probability=0.0) — CRITICAL
# ---------------------------------------------------------------------------

class TestTuringDeterminism:

    def test_locked_loop_repeats_at_length(self, locked_register):
        length = locked_register.length
        first_cycle = [locked_register.step() for _ in range(length)]
        second_cycle = [locked_register.step() for _ in range(length)]
        assert first_cycle == second_cycle

    def test_locked_loop_repeats_multiple_cycles(self, locked_register):
        length = locked_register.length
        first_cycle = [locked_register.step() for _ in range(length)]
        for cycle_num in range(4):
            this_cycle = [locked_register.step() for _ in range(length)]
            assert this_cycle == first_cycle, f"Mismatch at cycle {cycle_num + 2}"

    @pytest.mark.parametrize("length", [2, 3, 4, 5, 6, 8, 12, 16])
    def test_locked_loop_repeats_for_all_lengths(self, length):
        reg = TuringRegister(seed=0xA5C3, length=length)
        reg.set_probability(0.0)
        first_cycle = [reg.step() for _ in range(length)]
        second_cycle = [reg.step() for _ in range(length)]
        assert first_cycle == second_cycle

    def test_same_seed_same_sequence(self):
        a = TuringRegister(seed=42, length=8)
        b = TuringRegister(seed=42, length=8)
        a.set_probability(0.0)
        b.set_probability(0.0)
        seq_a = [a.step() for _ in range(32)]
        seq_b = [b.step() for _ in range(32)]
        assert seq_a == seq_b

    def test_different_seeds_different_sequences(self):
        a = TuringRegister(seed=0x0001, length=8)
        b = TuringRegister(seed=0xFFFE, length=8)
        seq_a = [a.step() for _ in range(8)]
        seq_b = [b.step() for _ in range(8)]
        assert seq_a != seq_b


# ---------------------------------------------------------------------------
# Step mechanics — bit-level verification
# ---------------------------------------------------------------------------

class TestTuringStepMechanics:

    def test_output_range_0_to_255(self):
        reg = TuringRegister(seed=0xFFFF, length=8)
        reg.set_probability(0.5)
        rng.seed(12345)
        for _ in range(500):
            val = reg.step()
            assert 0 <= val <= 255

    def test_register_stays_16bit(self):
        reg = TuringRegister(seed=0xFFFF, length=16)
        reg.set_probability(1.0)
        rng.seed(99)
        for _ in range(200):
            reg.step()
            assert 0 <= reg.get_state() <= 0xFFFF

    def test_zero_register_stays_zero_when_locked(self, zero_register):
        zero_register.set_probability(0.0)
        for _ in range(20):
            val = zero_register.step()
            assert val == 0
            assert zero_register.get_state() == 0

    def test_all_ones_locked_behavior(self, max_register):
        """0xFFFF with prob=0: feedback bit=1 at any position, shift right,
        write 1 to bit 15 -> register stays 0xFFFF, output stays 0xFF."""
        max_register.set_probability(0.0)
        for _ in range(20):
            val = max_register.step()
            assert val == 0xFF
            assert max_register.get_state() == 0xFFFF

    def test_single_step_manual_trace(self):
        """seed=0xA5C3, length=8:
        Loop bits = 0xC3 = 1100_0011
        Feedback = bit 0 = 1
        Shift loop right: 0xC3 >> 1 = 0x61 = 0110_0001
        Write 1 to bit 7: 0x61 | 0x80 = 0xE1
        Upper bits preserved: 0xA500
        Register = 0xA5E1, Output = 0xE1 = 225"""
        reg = TuringRegister(seed=0xA5C3, length=8)
        reg.set_probability(0.0)
        val = reg.step()
        assert val == 0xE1
        assert reg.get_state() == 0xA5E1

    def test_two_step_manual_trace(self):
        """After step 1: register=0xA5E1, loop=0xE1=1110_0001
        Feedback = bit 0 = 1
        Shift loop right: 0xE1 >> 1 = 0x70 = 0111_0000
        Write 1 to bit 7: 0x70 | 0x80 = 0xF0
        Register = 0xA5F0, Output = 0xF0 = 240"""
        reg = TuringRegister(seed=0xA5C3, length=8)
        reg.set_probability(0.0)
        reg.step()  # -> 0xA5E1
        val = reg.step()
        assert val == 0xF0
        assert reg.get_state() == 0xA5F0


# ---------------------------------------------------------------------------
# Mutation behavior (probabilistic)
# ---------------------------------------------------------------------------

class TestTuringMutation:

    @pytest.mark.statistical
    def test_full_random_diverges_from_locked(self):
        rng.seed(777)
        locked = TuringRegister(seed=0xA5C3, length=8)
        locked.set_probability(0.0)
        random_reg = TuringRegister(seed=0xA5C3, length=8)
        random_reg.set_probability(1.0)
        locked_seq = [locked.step() for _ in range(16)]
        random_seq = [random_reg.step() for _ in range(16)]
        assert locked_seq != random_seq

    @pytest.mark.statistical
    @pytest.mark.slow
    def test_mutation_rate_correlates_with_changes(self):
        rng.seed(42)

        def count_mutations(prob, seed=0xA5C3, length=8, cycles=100):
            reg = TuringRegister(seed=seed, length=length)
            reg.set_probability(0.0)
            baseline = [reg.step() for _ in range(length)]
            reg.set_state(seed)
            reg.set_probability(prob)
            changes = 0
            for _ in range(cycles):
                cycle = [reg.step() for _ in range(length)]
                changes += sum(1 for a, b in zip(baseline, cycle) if a != b)
                baseline = cycle
            return changes

        low_changes = count_mutations(0.1)
        high_changes = count_mutations(0.9)
        assert high_changes > low_changes

    @pytest.mark.statistical
    def test_probability_zero_means_no_mutation(self, locked_register):
        rng.seed(12345)  # should not matter when prob=0
        first_cycle = [locked_register.step() for _ in range(8)]
        second_cycle = [locked_register.step() for _ in range(8)]
        assert first_cycle == second_cycle


# ---------------------------------------------------------------------------
# Scale degree mapping
# ---------------------------------------------------------------------------

class TestTuringScaleDegree:

    def test_scale_degree_range_7(self):
        reg = TuringRegister(seed=0xFFFF, length=8)
        reg.set_probability(0.5)
        rng.seed(42)
        for _ in range(200):
            reg.step()
            deg = reg.get_scale_degree(7)
            assert 0 <= deg <= 6

    def test_scale_degree_range_custom(self):
        reg = TuringRegister(seed=0xFFFF, length=8)
        for _ in range(50):
            reg.step()
            deg = reg.get_scale_degree(5)
            assert 0 <= deg <= 4

    def test_scale_degree_matches_manual_calc(self):
        reg = TuringRegister(seed=0xA5C3, length=8)
        reg.set_probability(0.0)
        reg.step()  # state -> 0xA5E1
        expected = (0xA5E1 & 0xFF) % 7  # 0xE1 = 225, 225 % 7 = 1
        assert reg.get_scale_degree(7) == expected

    def test_scale_degree_without_step_has_no_side_effect(self):
        reg = TuringRegister(seed=0x0042, length=8)
        deg1 = reg.get_scale_degree(7)
        deg2 = reg.get_scale_degree(7)
        assert deg1 == deg2
        assert reg.get_state() == 0x0042


# ---------------------------------------------------------------------------
# State save/restore
# ---------------------------------------------------------------------------

class TestTuringStateManagement:

    def test_save_restore_produces_identical_output(self):
        reg = TuringRegister(seed=0xCAFE, length=8)
        reg.set_probability(0.0)
        state = reg.get_state()
        seq1 = [reg.step() for _ in range(8)]
        reg.set_state(state)
        seq2 = [reg.step() for _ in range(8)]
        assert seq1 == seq2

    def test_set_state_masks_to_16_bits(self):
        reg = TuringRegister(seed=0)
        reg.set_state(0x1FFFF)  # 17-bit value
        assert reg.get_state() == 0xFFFF

    def test_set_state_accepts_zero(self):
        reg = TuringRegister(seed=0xBEEF)
        reg.set_state(0)
        assert reg.get_state() == 0

    def test_set_probability_clamp_low(self):
        reg = TuringRegister(seed=0)
        reg.set_probability(-0.5)
        assert reg.probability == 0.0

    def test_set_probability_clamp_high(self):
        reg = TuringRegister(seed=0)
        reg.set_probability(1.5)
        assert reg.probability == 1.0

    def test_set_probability_in_range(self):
        reg = TuringRegister(seed=0)
        reg.set_probability(0.37)
        assert reg.probability == pytest.approx(0.37)

    def test_set_length_changes_feedback_tap(self):
        reg = TuringRegister(seed=0xA5C3, length=4)
        reg.set_probability(0.0)
        seq_len4 = [reg.step() for _ in range(4)]

        reg.set_state(0xA5C3)
        reg.set_length(8)
        seq_len8 = [reg.step() for _ in range(4)]

        # Different feedback tap position -> (very likely) different output
        assert reg.length == 8
