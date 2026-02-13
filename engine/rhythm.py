"""Rhythm pattern parsing, beat math, and swing calculation.

Handles the "chord rhythm pattern" system:
- Pattern: list of ints where each entry = chords in that bar (0 = hold previous)
- Expand: converts pattern + meter into a flat list of beat-durations per chord
- Swing: calculates long/short beat delays for swing feel
"""


def parse_pattern(text: str) -> list[int]:
    """Parse a space-separated rhythm pattern string.

    Each number = chords in that bar. 0 = hold previous chord.
    Returns [1] for empty/whitespace input.

    Raises ValueError for non-integer or negative values.
    """
    text = text.strip()
    if not text:
        return [1]

    parts = text.split()
    result = []
    for part in parts:
        try:
            n = int(part)
        except ValueError:
            raise ValueError(f"Invalid pattern entry: {part!r} (must be a non-negative integer)")
        if n < 0:
            raise ValueError(f"Pattern values must be non-negative, got {n}")
        result.append(n)

    if not result:
        return [1]
    return result


def expand_pattern(pattern: list[int], beats_per_bar: int) -> list[float]:
    """Convert a pattern + meter into beat-durations per chord.

    Each pattern entry is chords-per-bar for that bar (0 = hold).
    Consecutive holds extend the previous chord's duration.

    Examples (beats_per_bar=4):
        [1]         -> [4.0]           (1 chord per bar, lasts 4 beats)
        [2]         -> [2.0, 2.0]      (2 chords per bar, each 2 beats)
        [1, 0]      -> [8.0]           (chord holds across 2 bars = 8 beats)
        [1, 1, 1, 2] -> [4, 4, 4, 2, 2]
        [4]         -> [1, 1, 1, 1]    (4 chords per bar, each 1 beat)

    Raises ValueError if pattern is empty or starts with 0 (nothing to hold).
    """
    if not pattern:
        raise ValueError("Pattern cannot be empty")
    if pattern[0] == 0:
        raise ValueError("Pattern cannot start with 0 (nothing to hold)")

    durations = []
    for bar_idx, chords_in_bar in enumerate(pattern):
        if chords_in_bar == 0:
            # Hold: extend the previous chord's duration
            if not durations:
                raise ValueError("Hold (0) with no previous chord")
            durations[-1] += beats_per_bar
        else:
            # Split bar into equal chord slots
            beat_per_chord = beats_per_bar / chords_in_bar
            for _ in range(chords_in_bar):
                durations.append(beat_per_chord)

    return durations


def simple_to_pattern(bars_per_chord: int = 1, chords_per_bar: int = 1) -> list[int]:
    """Convert simple-mode dropdowns to a pattern.

    Only one of bars_per_chord or chords_per_bar can be > 1.

    Examples:
        bars=1, chords=1 -> [1]
        bars=2, chords=1 -> [1, 0]
        bars=4, chords=1 -> [1, 0, 0, 0]
        bars=1, chords=2 -> [2]
        bars=1, chords=4 -> [4]

    Raises ValueError if both > 1, or either < 1.
    """
    if bars_per_chord < 1 or chords_per_bar < 1:
        raise ValueError("Values must be >= 1")
    if bars_per_chord > 1 and chords_per_bar > 1:
        raise ValueError("Only one of bars_per_chord or chords_per_bar can be > 1")

    if bars_per_chord > 1:
        return [1] + [0] * (bars_per_chord - 1)
    if chords_per_bar > 1:
        return [chords_per_bar]
    return [1]


def calc_swing_delays(beat_ms: float, swing_pct: float) -> tuple[float, float]:
    """Calculate long and short beat delays for swing feel.

    swing_pct: 50 = straight (equal), 67 = triplet swing (2:1 ratio).
    Clamped to [50, 67].

    Returns (long_beat_ms, short_beat_ms) where long + short = 2 * beat_ms.
    For straight feel (50%): both equal beat_ms.
    For triplet swing (67%): long = 1.34 * beat_ms, short = 0.66 * beat_ms.
    """
    swing_pct = max(50.0, min(67.0, swing_pct))
    ratio = swing_pct / 100.0
    pair_duration = beat_ms * 2
    long_beat = pair_duration * ratio
    short_beat = pair_duration * (1.0 - ratio)
    return (long_beat, short_beat)
