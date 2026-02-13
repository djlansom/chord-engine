"""Tests for engine.theory — music theory foundation."""

import pytest
from engine.theory import (
    note_index, spell, get_scale_notes, build_chord,
    get_quality_category, get_diatonic_chord,
    SHARPS, FLATS, SHARP_KEYS, FLAT_KEYS,
    SCALES, CHORD_TYPES, CHORD_SYMBOLS,
    DIATONIC_CHORDS, DIATONIC_CHORDS_DEFAULT,
)


# ---------------------------------------------------------------------------
# note_index
# ---------------------------------------------------------------------------

class TestNoteIndex:

    @pytest.mark.parametrize("name,expected", [
        ('C', 0), ('C#', 1), ('D', 2), ('D#', 3), ('E', 4), ('F', 5),
        ('F#', 6), ('G', 7), ('G#', 8), ('A', 9), ('A#', 10), ('B', 11),
    ])
    def test_sharp_notes(self, name, expected):
        assert note_index(name) == expected

    @pytest.mark.parametrize("name,expected", [
        ('Db', 1), ('Eb', 3), ('Gb', 6), ('Ab', 8), ('Bb', 10),
    ])
    def test_flat_notes(self, name, expected):
        assert note_index(name) == expected

    def test_whitespace_stripped(self):
        assert note_index(' C ') == 0
        assert note_index('Bb ') == 10

    def test_unknown_note_raises(self):
        with pytest.raises(ValueError, match="Unknown note"):
            note_index('H')

    def test_double_sharp_raises(self):
        with pytest.raises(ValueError, match="Unknown note"):
            note_index('C##')

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Unknown note"):
            note_index('')


# ---------------------------------------------------------------------------
# spell
# ---------------------------------------------------------------------------

class TestSpell:

    def test_sharp_key_uses_sharps(self):
        assert spell(1, 'G') == 'C#'

    def test_flat_key_uses_flats(self):
        assert spell(1, 'F') == 'Db'

    def test_c_defaults_to_sharps(self):
        assert spell(1, 'C') == 'C#'

    def test_minor_sharp_key(self):
        assert spell(3, 'Am') == 'D#'

    def test_minor_flat_key(self):
        assert spell(3, 'Dm') == 'Eb'

    def test_index_wraps_mod_12(self):
        assert spell(14, 'C') == 'D'

    def test_negative_index_wraps(self):
        assert spell(-1, 'C') == 'B'

    @pytest.mark.parametrize("key", sorted(SHARP_KEYS))
    def test_all_sharp_keys_produce_sharps(self, key):
        result = spell(1, key)
        assert result == 'C#'

    @pytest.mark.parametrize("key", sorted(FLAT_KEYS))
    def test_all_flat_keys_produce_flats(self, key):
        result = spell(1, key)
        assert result == 'Db'


# ---------------------------------------------------------------------------
# get_scale_notes
# ---------------------------------------------------------------------------

class TestGetScaleNotes:

    def test_c_ionian(self):
        assert get_scale_notes('C', 'ionian') == ['C', 'D', 'E', 'F', 'G', 'A', 'B']

    def test_c_ionian_has_7_notes(self):
        assert len(get_scale_notes('C', 'ionian')) == 7

    def test_g_ionian_has_f_sharp(self):
        notes = get_scale_notes('G', 'ionian')
        assert 'F#' in notes

    def test_f_ionian_uses_bb_not_a_sharp(self):
        notes = get_scale_notes('F', 'ionian')
        assert 'Bb' in notes
        assert 'A#' not in notes

    def test_bb_dorian_no_sharps(self):
        notes = get_scale_notes('Bb', 'dorian')
        for note in notes:
            assert '#' not in note, f"Sharp {note} in Bb dorian"

    def test_unknown_scale_raises(self):
        with pytest.raises(ValueError, match="Unknown scale"):
            get_scale_notes('C', 'nonexistent')

    def test_unknown_root_raises(self):
        with pytest.raises(ValueError, match="Unknown note"):
            get_scale_notes('X', 'ionian')

    @pytest.mark.parametrize("scale_name,expected_len", [
        ('ionian', 7), ('dorian', 7), ('phrygian', 7), ('lydian', 7),
        ('mixolydian', 7), ('aeolian', 7), ('locrian', 7),
        ('harmonic_minor', 7), ('melodic_minor', 7),
        ('whole_tone', 6), ('blues', 6),
        ('minor_pentatonic', 5), ('major_pentatonic', 5),
        ('dim_whole_half', 8), ('dim_half_whole', 8),
        ('bebop_dominant', 8), ('bebop_major', 8),
    ])
    def test_scale_note_count(self, scale_name, expected_len):
        assert len(get_scale_notes('C', scale_name)) == expected_len

    def test_all_scales_start_on_root(self, all_scale_names):
        for name in all_scale_names:
            notes = get_scale_notes('C', name)
            assert notes[0] == 'C', f"Scale {name} does not start on C"

    def test_no_duplicate_notes_in_diatonic_scales(self):
        for name in ['ionian', 'dorian', 'phrygian', 'lydian',
                     'mixolydian', 'aeolian', 'locrian']:
            notes = get_scale_notes('C', name)
            assert len(set(notes)) == 7, f"Duplicate notes in {name}"

    def test_whole_tone_intervals_all_two(self):
        notes = get_scale_notes('C', 'whole_tone')
        indices = [note_index(n) for n in notes]
        for i in range(1, len(indices)):
            interval = (indices[i] - indices[i - 1]) % 12
            assert interval == 2


# ---------------------------------------------------------------------------
# build_chord
# ---------------------------------------------------------------------------

class TestBuildChord:

    def test_c_major_triad(self):
        chord = build_chord('C', 'maj')
        assert chord['symbol'] == 'C'
        assert chord['root'] == 'C'
        assert chord['quality'] == 'maj'
        assert chord['notes'] == ['C', 'E', 'G']

    def test_a_minor_seventh(self):
        chord = build_chord('A', 'min7')
        assert chord['symbol'] == 'Am7'
        assert chord['notes'] == ['A', 'C', 'E', 'G']

    def test_g_dominant_seventh(self):
        chord = build_chord('G', 'dom7')
        assert chord['symbol'] == 'G7'
        assert chord['notes'] == ['G', 'B', 'D', 'F']

    def test_bb_major_seventh_in_flat_key(self):
        chord = build_chord('Bb', 'maj7', key='F')
        assert chord['symbol'] == 'Bbmaj7'
        assert chord['notes'] == ['Bb', 'D', 'F', 'A']

    def test_f_sharp_minor_in_sharp_key(self):
        chord = build_chord('F#', 'min', key='D')
        assert chord['symbol'] == 'F#m'
        assert 'F#' in chord['notes']

    def test_unknown_quality_raises(self):
        with pytest.raises(ValueError, match="Unknown chord quality"):
            build_chord('C', 'power5')

    def test_unknown_root_raises(self):
        with pytest.raises(ValueError, match="Unknown note"):
            build_chord('X', 'maj')

    @pytest.mark.parametrize("quality", list(CHORD_TYPES.keys()))
    def test_all_qualities_build_successfully(self, quality):
        chord = build_chord('C', quality)
        assert chord['symbol']
        assert chord['root'] == 'C'
        assert len(chord['notes']) == len(CHORD_TYPES[quality])

    def test_chord_note_count_matches_intervals(self):
        for quality, intervals in CHORD_TYPES.items():
            chord = build_chord('C', quality)
            assert len(chord['notes']) == len(intervals), \
                f"Note count mismatch for {quality}"

    def test_major_triad_has_empty_suffix(self):
        chord = build_chord('E', 'maj')
        assert chord['symbol'] == 'E'

    def test_symbol_format_min7b5(self):
        chord = build_chord('D', 'min7b5')
        assert chord['symbol'] == 'Dm7b5'


# ---------------------------------------------------------------------------
# get_quality_category
# ---------------------------------------------------------------------------

class TestGetQualityCategory:

    @pytest.mark.parametrize("quality,expected", [
        ('maj', 'major'), ('maj7', 'major'), ('maj9', 'major'),
        ('maj13', 'major'), ('add9', 'major'),
        ('min', 'minor'), ('min7', 'minor'), ('min9', 'minor'),
        ('min11', 'minor'), ('min13', 'minor'), ('minmaj7', 'minor'),
        ('dom7', 'dominant'), ('dom9', 'dominant'), ('dom11', 'dominant'),
        ('dom13', 'dominant'), ('7sus4', 'dominant'),
        ('dim', 'diminished'), ('dim7', 'diminished'), ('min7b5', 'diminished'),
        ('aug', 'augmented'), ('7#5', 'augmented'),
        ('sus2', 'sus'), ('sus4', 'sus'),
        ('7b9', 'altered'), ('7#9', 'altered'), ('7b5', 'altered'), ('7alt', 'altered'),
    ])
    def test_known_quality_categories(self, quality, expected):
        assert get_quality_category(quality) == expected

    def test_unknown_quality_defaults_to_dominant(self):
        assert get_quality_category('mystery_chord') == 'dominant'

    def test_every_chord_type_has_a_category(self, all_chord_qualities):
        valid_categories = {'major', 'minor', 'dominant', 'diminished',
                            'augmented', 'sus', 'altered'}
        for quality in all_chord_qualities:
            cat = get_quality_category(quality)
            assert cat in valid_categories, f"{quality} -> {cat}"


# ---------------------------------------------------------------------------
# get_diatonic_chord
# ---------------------------------------------------------------------------

class TestGetDiatonicChord:

    def test_c_ionian_degree_0_triads(self, c_ionian_notes):
        chord = get_diatonic_chord('ionian', 0, 'triads', c_ionian_notes, key='C')
        assert chord['root'] == 'C'
        assert chord['quality'] == 'maj'
        assert chord['roman'] == 'I'
        assert chord['category'] == 'major'

    def test_c_ionian_degree_1_sevenths(self, c_ionian_notes):
        chord = get_diatonic_chord('ionian', 1, 'sevenths', c_ionian_notes, key='C')
        assert chord['symbol'] == 'Dm7'
        assert chord['roman'] == 'II'

    def test_c_ionian_degree_4_dom7(self, c_ionian_notes):
        chord = get_diatonic_chord('ionian', 4, 'sevenths', c_ionian_notes, key='C')
        assert chord['symbol'] == 'G7'
        assert chord['quality'] == 'dom7'
        assert chord['category'] == 'dominant'

    def test_c_ionian_degree_6_diminished(self, c_ionian_notes):
        chord = get_diatonic_chord('ionian', 6, 'sevenths', c_ionian_notes, key='C')
        assert chord['symbol'] == 'Bm7b5'
        assert chord['category'] == 'diminished'

    def test_altered_voicing_on_V(self, c_ionian_notes):
        chord = get_diatonic_chord('ionian', 4, 'altered', c_ionian_notes, key='C')
        assert chord['quality'] == '7alt'
        assert chord['category'] == 'altered'

    def test_degree_wraps_modulo(self, c_ionian_notes):
        chord_0 = get_diatonic_chord('ionian', 0, 'sevenths', c_ionian_notes, key='C')
        chord_7 = get_diatonic_chord('ionian', 7, 'sevenths', c_ionian_notes, key='C')
        assert chord_0['root'] == chord_7['root']
        assert chord_0['quality'] == chord_7['quality']

    def test_unknown_voicing_falls_back_to_sevenths(self, c_ionian_notes):
        chord = get_diatonic_chord('ionian', 0, 'bogus_voicing', c_ionian_notes, key='C')
        expected = get_diatonic_chord('ionian', 0, 'sevenths', c_ionian_notes, key='C')
        assert chord['quality'] == expected['quality']

    def test_unknown_scale_uses_default_map(self):
        notes = get_scale_notes('C', 'lydian')
        chord = get_diatonic_chord('lydian', 0, 'sevenths', notes, key='C')
        assert chord['quality'] == 'maj7'  # default sevenths degree 0

    def test_flat_key_diatonic_spelling(self, bb_dorian_notes):
        chord = get_diatonic_chord('dorian', 0, 'sevenths', bb_dorian_notes, key='Bb')
        assert chord['root'] == 'Bb'
        for note in chord['notes']:
            assert '#' not in note, f"Sharp {note} found in Bb dorian chord"

    def test_all_mapped_scales_all_degrees_all_voicings(self):
        voicings = ['triads', 'sevenths', 'extensions', 'altered']
        for scale_name in DIATONIC_CHORDS:
            notes = get_scale_notes('C', scale_name)
            for degree in range(len(notes)):
                for voicing in voicings:
                    chord = get_diatonic_chord(
                        scale_name, degree, voicing, notes, key='C'
                    )
                    assert 'symbol' in chord
                    assert 'notes' in chord
                    assert 'roman' in chord
                    assert 'category' in chord

    def test_roman_numeral_for_degree_beyond_seven(self):
        notes = get_scale_notes('C', 'dim_whole_half')  # 8 notes
        chord = get_diatonic_chord('dim_whole_half', 7, 'sevenths', notes, key='C')
        assert chord['roman'] == '8'


# ---------------------------------------------------------------------------
# Data integrity
# ---------------------------------------------------------------------------

class TestDataIntegrity:

    def test_all_diatonic_qualities_exist_in_chord_types(self):
        for scale_name, voicing_map in DIATONIC_CHORDS.items():
            for voicing_name, qualities in voicing_map.items():
                for quality in qualities:
                    assert quality in CHORD_TYPES, \
                        f"{quality} in {scale_name}/{voicing_name} not in CHORD_TYPES"

    def test_default_diatonic_qualities_exist_in_chord_types(self):
        for voicing_name, qualities in DIATONIC_CHORDS_DEFAULT.items():
            for quality in qualities:
                assert quality in CHORD_TYPES, \
                    f"{quality} in default/{voicing_name} not in CHORD_TYPES"

    def test_all_chord_types_have_symbols(self):
        for quality in CHORD_TYPES:
            assert quality in CHORD_SYMBOLS, f"{quality} missing from CHORD_SYMBOLS"

    def test_all_diatonic_maps_have_seven_entries(self):
        for scale_name, voicing_map in DIATONIC_CHORDS.items():
            for voicing_name, qualities in voicing_map.items():
                assert len(qualities) == 7, \
                    f"{scale_name}/{voicing_name} has {len(qualities)} entries"

    def test_scale_intervals_are_ascending(self):
        for name, intervals in SCALES.items():
            for i in range(1, len(intervals)):
                assert intervals[i] > intervals[i - 1], \
                    f"Scale {name} not ascending at position {i}"

    def test_scale_intervals_start_at_zero(self):
        for name, intervals in SCALES.items():
            assert intervals[0] == 0, f"Scale {name} does not start at 0"

    def test_scale_intervals_within_octave(self):
        for name, intervals in SCALES.items():
            for iv in intervals:
                assert 0 <= iv < 12, f"Scale {name} has out-of-octave interval {iv}"

    def test_chord_intervals_start_at_zero(self):
        for name, intervals in CHORD_TYPES.items():
            assert intervals[0] == 0, f"Chord {name} does not start at 0"
