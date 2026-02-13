"""Tests for engine.generator — ProgressionGenerator."""

import pytest
from engine.generator import ProgressionGenerator, TRANSITION_WEIGHTS


class TestProgressionGeneratorInit:

    def test_create_with_defaults(self):
        gen = ProgressionGenerator()
        assert gen.key == 'C'
        assert gen.scale == 'ionian'
        assert gen.voicing == 'sevenths'
        assert gen.mode == 'raw'
        assert gen.num_degrees == 7

    def test_create_with_all_params(self):
        gen = ProgressionGenerator(
            key='Bb', scale='dorian', length=4,
            mutation=0.5, voicing='extensions', mode='smooth', seed=9999,
        )
        assert gen.key == 'Bb'
        assert gen.scale == 'dorian'
        assert gen.voicing == 'extensions'
        assert gen.mode == 'smooth'
        assert gen.turing.length == 4
        assert gen.turing.probability == 0.5
        assert gen.turing.register == 9999


class TestRawMode:

    def test_raw_mode_returns_chord_dicts(self):
        gen = ProgressionGenerator(seed=42, mode='raw')
        chord = gen.step()
        assert isinstance(chord, dict)
        for key in ('symbol', 'quality', 'root', 'notes', 'roman',
                    'category', 'register_value'):
            assert key in chord, f"Missing key: {key}"

    def test_raw_mode_locked_loop_repeats(self):
        gen = ProgressionGenerator(seed=0xA5C3, mutation=0.0, length=8, mode='raw')
        first_cycle = [gen.step()['symbol'] for _ in range(8)]
        second_cycle = [gen.step()['symbol'] for _ in range(8)]
        assert first_cycle == second_cycle

    def test_raw_mode_degree_range_matches_scale(self):
        gen = ProgressionGenerator(seed=42, mode='raw', scale='ionian')
        for _ in range(50):
            chord = gen.step()
            # Root should be a note from the C ionian scale
            assert chord['root'] in gen.scale_notes


class TestSmoothMode:

    def test_smooth_mode_returns_chord_dicts(self):
        gen = ProgressionGenerator(seed=42, mode='smooth')
        chord = gen.step()
        assert isinstance(chord, dict)
        assert 'symbol' in chord
        assert 'quality' in chord
        assert 'root' in chord

    def test_smooth_mode_prefers_V_to_I(self):
        """After degree 4 (V), smooth mode should strongly prefer degree 0 (I)."""
        # Run many trials from degree 4
        resolved_to_I = 0
        trials = 200
        for i in range(trials):
            gen = ProgressionGenerator(seed=i * 7, mode='smooth', mutation=1.0)
            # Force last_degree to 4 (V)
            gen.last_degree = 4
            chord = gen.step()
            # Check if the resulting degree is 0 (I)
            # We can infer degree from root matching scale_notes[0]
            if chord['root'] == gen.scale_notes[0]:
                resolved_to_I += 1
        # V -> I has weight 4 out of total 7, so expect ~57%, allow wide margin
        assert resolved_to_I > trials * 0.3, \
            f"V->I resolution too rare: {resolved_to_I}/{trials}"

    def test_smooth_mode_ii_V_I_common(self):
        """ii -> V transition should be frequent in smooth mode."""
        ii_to_V = 0
        trials = 200
        for i in range(trials):
            gen = ProgressionGenerator(seed=i * 13, mode='smooth', mutation=1.0)
            gen.last_degree = 1  # ii
            chord = gen.step()
            if chord['root'] == gen.scale_notes[4]:  # V
                ii_to_V += 1
        # ii -> V has weight 3 out of total 7, expect ~43%
        assert ii_to_V > trials * 0.2, \
            f"ii->V transition too rare: {ii_to_V}/{trials}"


class TestProgressionGeneration:

    def test_generate_returns_list_of_chords(self):
        gen = ProgressionGenerator(seed=42)
        chords = gen.generate(8)
        assert isinstance(chords, list)
        assert len(chords) == 8
        assert all(isinstance(c, dict) for c in chords)

    def test_progression_length_matches_request(self):
        gen = ProgressionGenerator(seed=42)
        for count in [1, 4, 8, 16, 32]:
            gen2 = ProgressionGenerator(seed=42)
            chords = gen2.generate(count)
            assert len(chords) == count

    def test_seed_replay_produces_same_progression(self):
        gen1 = ProgressionGenerator(seed=12345, mutation=0.0, mode='raw')
        gen2 = ProgressionGenerator(seed=12345, mutation=0.0, mode='raw')
        symbols1 = [gen1.step()['symbol'] for _ in range(16)]
        symbols2 = [gen2.step()['symbol'] for _ in range(16)]
        assert symbols1 == symbols2

    def test_get_state_returns_full_config(self):
        gen = ProgressionGenerator(
            key='F', scale='mixolydian', length=12,
            mutation=0.3, voicing='altered', mode='smooth', seed=7777,
        )
        state = gen.get_state()
        assert state['key'] == 'F'
        assert state['scale'] == 'mixolydian'
        assert state['voicing'] == 'altered'
        assert state['mode'] == 'smooth'
        assert state['length'] == 12
        assert state['mutation'] == pytest.approx(0.3)
        assert isinstance(state['register_state'], int)
