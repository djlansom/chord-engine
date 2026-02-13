"""Progression generator — ties the Turing register to music theory.

Two modes:
- Raw: pure register output -> scale degree -> chord
- Smooth: transition weights bias toward musical movements (ii-V-I etc.)
"""

import random
from .turing import TuringRegister
from .theory import get_scale_notes, get_diatonic_chord, SCALES

# Transition weights: from_degree -> {to_degree: weight}
# Higher weight = more likely to transition there in smooth mode
TRANSITION_WEIGHTS = {
    0: {3: 3, 4: 3, 5: 2, 1: 1, 2: 1, 6: 0.5},  # I -> IV, V preferred
    1: {4: 3, 0: 2, 3: 1, 5: 1},                   # ii -> V strongly preferred
    2: {5: 3, 3: 2, 0: 1},                          # iii -> vi, IV
    3: {4: 3, 0: 2, 1: 2, 6: 1},                    # IV -> V, I, ii
    4: {0: 4, 5: 2, 3: 1},                          # V -> I very strongly
    5: {3: 3, 4: 2, 1: 2, 2: 1},                    # vi -> IV, V, ii
    6: {0: 3, 4: 2, 5: 1},                          # vii -> I, V
}


def _weighted_choice(weights: dict[int, float], candidate: int, num_degrees: int) -> int:
    """Pick a degree biased by transition weights.

    Uses the Turing register candidate as entropy source to pick
    a point in the weighted distribution.
    """
    targets = list(weights.keys())
    w = [weights[t] for t in targets]
    total = sum(w)

    # Use candidate to pick a point in the weighted distribution
    point = (candidate / num_degrees) * total
    cumulative = 0.0
    for t, weight in zip(targets, w):
        cumulative += weight
        if point < cumulative:
            return t
    return targets[-1]


class ProgressionGenerator:
    """Generates chord progressions driven by a Turing Machine register."""

    def __init__(self, key='C', scale='ionian', length=8,
                 mutation=0.1, voicing='sevenths', mode='raw', seed=None):
        self.key = key
        self.scale = scale
        self.voicing = voicing
        self.mode = mode  # 'raw' or 'smooth'

        self.turing = TuringRegister(seed=seed, length=length)
        self.turing.set_probability(mutation)

        self.scale_notes = get_scale_notes(key, scale)
        self.num_degrees = len(self.scale_notes)
        self.last_degree = 0
        self.history = []

    def set_key(self, key: str):
        self.key = key
        self.scale_notes = get_scale_notes(key, self.scale)
        self.num_degrees = len(self.scale_notes)

    def set_scale(self, scale: str):
        self.scale = scale
        self.scale_notes = get_scale_notes(self.key, scale)
        self.num_degrees = len(self.scale_notes)

    def set_voicing(self, voicing: str):
        self.voicing = voicing

    def set_mode(self, mode: str):
        self.mode = mode

    def set_mutation(self, mutation: float):
        self.turing.set_probability(mutation)

    def set_length(self, length: int):
        self.turing.set_length(length)

    def step(self) -> dict:
        """Advance one step and return the current chord."""
        raw_value = self.turing.step()
        raw_degree = raw_value % self.num_degrees

        if self.mode == 'smooth' and self.last_degree in TRANSITION_WEIGHTS:
            degree = _weighted_choice(
                TRANSITION_WEIGHTS[self.last_degree],
                raw_degree,
                self.num_degrees,
            )
        else:
            degree = raw_degree

        chord = get_diatonic_chord(
            self.scale, degree, self.voicing, self.scale_notes, self.key
        )
        chord['register_value'] = raw_value
        chord['mutated'] = (raw_degree != degree)

        self.last_degree = degree
        self.history.append(chord)
        return chord

    def generate(self, count: int) -> list[dict]:
        """Generate `count` chords in sequence."""
        return [self.step() for _ in range(count)]

    def get_state(self) -> dict:
        """Return full generator state for save/restore."""
        return {
            'register_state': self.turing.get_state(),
            'key': self.key,
            'scale': self.scale,
            'voicing': self.voicing,
            'mode': self.mode,
            'length': self.turing.length,
            'mutation': self.turing.probability,
        }
