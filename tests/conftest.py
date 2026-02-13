"""Shared fixtures for chord-engine tests."""

import pytest
from engine.turing import TuringRegister
from engine.theory import (
    get_scale_notes, SCALES, CHORD_TYPES, DIATONIC_CHORDS,
    SHARP_KEYS, FLAT_KEYS,
)


# --- Turing register fixtures ---

@pytest.fixture
def locked_register():
    """Register with known seed, probability=0 (locked loop)."""
    reg = TuringRegister(seed=0b1010_0101_1100_0011, length=8)
    reg.set_probability(0.0)
    return reg


@pytest.fixture
def zero_register():
    """Register seeded with all zeros."""
    return TuringRegister(seed=0, length=8)


@pytest.fixture
def max_register():
    """Register seeded with all ones (0xFFFF)."""
    return TuringRegister(seed=0xFFFF, length=8)


@pytest.fixture
def mutating_register():
    """Register with moderate mutation for statistical tests."""
    reg = TuringRegister(seed=0xA5C3, length=8)
    reg.set_probability(0.5)
    return reg


# --- Theory fixtures ---

@pytest.fixture
def c_ionian_notes():
    """C major scale notes."""
    return get_scale_notes('C', 'ionian')


@pytest.fixture
def bb_dorian_notes():
    """Bb dorian scale notes (flat key context)."""
    return get_scale_notes('Bb', 'dorian')


@pytest.fixture
def all_scale_names():
    """List of all defined scale names."""
    return list(SCALES.keys())


@pytest.fixture
def all_chord_qualities():
    """List of all defined chord qualities."""
    return list(CHORD_TYPES.keys())
