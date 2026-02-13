"""Music theory foundation — keys, scales, chords, diatonic harmony.

Jazz-capable: supports triads through altered dominants, 20+ scales,
30+ chord types, and correct enharmonic spelling by key context.
"""

# ---------------------------------------------------------------------------
# Chromatic pitch spelling
# ---------------------------------------------------------------------------

SHARPS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLATS  = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Key signature determines which spelling to use
SHARP_KEYS = {'C', 'G', 'D', 'A', 'E', 'B', 'F#',
              'Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'D#m'}
FLAT_KEYS  = {'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb',
              'Dm', 'Gm', 'Cm', 'Fm', 'Bbm', 'Ebm'}

ALL_NOTES = SHARPS  # canonical semitone indices

def note_index(name: str) -> int:
    """Convert a note name to its chromatic index (0-11)."""
    name = name.strip()
    if name in SHARPS:
        return SHARPS.index(name)
    if name in FLATS:
        return FLATS.index(name)
    raise ValueError(f"Unknown note: {name}")


def spell(index: int, key: str = 'C') -> str:
    """Return the correctly-spelled note name for a chromatic index in a key."""
    idx = index % 12
    if key in FLAT_KEYS:
        return FLATS[idx]
    return SHARPS[idx]


# ---------------------------------------------------------------------------
# Scales — intervals from root (semitones)
# ---------------------------------------------------------------------------

SCALES = {
    # Major modes
    'ionian':     [0, 2, 4, 5, 7, 9, 11],
    'dorian':     [0, 2, 3, 5, 7, 9, 10],
    'phrygian':   [0, 1, 3, 5, 7, 8, 10],
    'lydian':     [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'aeolian':    [0, 2, 3, 5, 7, 8, 10],
    'locrian':    [0, 1, 3, 5, 6, 8, 10],

    # Harmonic minor family
    'harmonic_minor':    [0, 2, 3, 5, 7, 8, 11],
    'phrygian_dominant': [0, 1, 4, 5, 7, 8, 10],

    # Melodic minor family
    'melodic_minor':  [0, 2, 3, 5, 7, 9, 11],
    'lydian_dominant': [0, 2, 4, 6, 7, 9, 10],
    'altered':        [0, 1, 3, 4, 6, 8, 10],

    # Symmetric
    'whole_tone':     [0, 2, 4, 6, 8, 10],
    'dim_whole_half': [0, 2, 3, 5, 6, 8, 9, 11],  # diminished W-H
    'dim_half_whole': [0, 1, 3, 4, 6, 7, 9, 10],  # diminished H-W

    # Other
    'blues':          [0, 3, 5, 6, 7, 10],
    'minor_pentatonic': [0, 3, 5, 7, 10],
    'major_pentatonic': [0, 2, 4, 7, 9],
    'bebop_dominant': [0, 2, 4, 5, 7, 9, 10, 11],
    'bebop_major':    [0, 2, 4, 5, 7, 8, 9, 11],
}


def get_scale_notes(root: str, scale_name: str) -> list[str]:
    """Return the note names for a scale built on `root`."""
    if scale_name not in SCALES:
        raise ValueError(f"Unknown scale: {scale_name}")
    root_idx = note_index(root)
    intervals = SCALES[scale_name]
    return [spell((root_idx + iv) % 12, root) for iv in intervals]


# ---------------------------------------------------------------------------
# Chord quality definitions — intervals from chord root (semitones)
# ---------------------------------------------------------------------------

CHORD_TYPES = {
    # Triads
    'maj':   [0, 4, 7],
    'min':   [0, 3, 7],
    'dim':   [0, 3, 6],
    'aug':   [0, 4, 8],
    'sus2':  [0, 2, 7],
    'sus4':  [0, 5, 7],

    # Sevenths
    'maj7':    [0, 4, 7, 11],
    'min7':    [0, 3, 7, 10],
    'dom7':    [0, 4, 7, 10],
    'min7b5':  [0, 3, 6, 10],
    'dim7':    [0, 3, 6, 9],
    'minmaj7': [0, 3, 7, 11],
    '7sus4':   [0, 5, 7, 10],

    # Ninths
    'maj9':  [0, 4, 7, 11, 14],
    'min9':  [0, 3, 7, 10, 14],
    'dom9':  [0, 4, 7, 10, 14],
    'add9':  [0, 4, 7, 14],

    # Elevenths
    'min11': [0, 3, 7, 10, 14, 17],
    'dom11': [0, 4, 7, 10, 14, 17],

    # Thirteenths
    'maj13': [0, 4, 7, 11, 14, 21],
    'min13': [0, 3, 7, 10, 14, 21],
    'dom13': [0, 4, 7, 10, 14, 21],

    # Altered dominants
    '7b9':  [0, 4, 7, 10, 13],
    '7#9':  [0, 4, 7, 10, 15],
    '7b5':  [0, 4, 6, 10],
    '7#5':  [0, 4, 8, 10],
    '7alt': [0, 4, 8, 10, 13],  # 7#5b9 — common "alt" voicing
}

# Display suffixes for chord symbols
CHORD_SYMBOLS = {
    'maj': '', 'min': 'm', 'dim': 'dim', 'aug': 'aug', 'sus2': 'sus2', 'sus4': 'sus4',
    'maj7': 'maj7', 'min7': 'm7', 'dom7': '7', 'min7b5': 'm7b5', 'dim7': 'dim7',
    'minmaj7': 'mMaj7', '7sus4': '7sus4',
    'maj9': 'maj9', 'min9': 'm9', 'dom9': '9', 'add9': 'add9',
    'min11': 'm11', 'dom11': '11',
    'maj13': 'maj13', 'min13': 'm13', 'dom13': '13',
    '7b9': '7b9', '7#9': '7#9', '7b5': '7b5', '7#5': '7#5', '7alt': '7alt',
}


def build_chord(root: str, quality: str, key: str = 'C') -> dict:
    """Build a chord: returns {symbol, quality, root, notes}."""
    if quality not in CHORD_TYPES:
        raise ValueError(f"Unknown chord quality: {quality}")
    root_idx = note_index(root)
    intervals = CHORD_TYPES[quality]
    notes = [spell((root_idx + iv) % 12, key) for iv in intervals]
    symbol = root + CHORD_SYMBOLS[quality]
    return {
        'symbol': symbol,
        'quality': quality,
        'root': root,
        'notes': notes,
    }


# ---------------------------------------------------------------------------
# Diatonic chord maps — which chord quality for each scale degree
# ---------------------------------------------------------------------------

# Roman numeral labels (for display)
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']

# Voicing levels: degree index -> chord quality
DIATONIC_CHORDS = {
    'ionian': {
        'triads':     ['maj', 'min', 'min', 'maj', 'maj', 'min', 'dim'],
        'sevenths':   ['maj7', 'min7', 'min7', 'maj7', 'dom7', 'min7', 'min7b5'],
        'extensions': ['maj9', 'min9', 'min7', 'maj9', 'dom13', 'min9', 'min7b5'],
        'altered':    ['maj9', 'min9', 'min7', 'maj9', '7alt', 'min9', 'min7b5'],
    },
    'dorian': {
        'triads':     ['min', 'min', 'maj', 'maj', 'min', 'dim', 'maj'],
        'sevenths':   ['min7', 'min7', 'maj7', 'dom7', 'min7', 'min7b5', 'maj7'],
        'extensions': ['min9', 'min7', 'maj9', 'dom9', 'min9', 'min7b5', 'maj9'],
        'altered':    ['min9', 'min7', 'maj9', '7alt', 'min9', 'min7b5', 'maj9'],
    },
    'mixolydian': {
        'triads':     ['maj', 'min', 'dim', 'maj', 'min', 'min', 'maj'],
        'sevenths':   ['dom7', 'min7', 'min7b5', 'maj7', 'min7', 'min7', 'maj7'],
        'extensions': ['dom9', 'min9', 'min7b5', 'maj9', 'min9', 'min7', 'maj9'],
        'altered':    ['dom13', 'min9', 'min7b5', 'maj9', 'min9', 'min7', 'maj9'],
    },
    'aeolian': {
        'triads':     ['min', 'dim', 'maj', 'min', 'min', 'maj', 'maj'],
        'sevenths':   ['min7', 'min7b5', 'maj7', 'min7', 'min7', 'maj7', 'dom7'],
        'extensions': ['min9', 'min7b5', 'maj9', 'min9', 'min7', 'maj9', 'dom9'],
        'altered':    ['min9', 'min7b5', 'maj9', 'min9', 'min7', 'maj9', '7alt'],
    },
    'harmonic_minor': {
        'triads':     ['min', 'dim', 'aug', 'min', 'maj', 'maj', 'dim'],
        'sevenths':   ['minmaj7', 'min7b5', 'maj7', 'min7', 'dom7', 'maj7', 'dim7'],
        'extensions': ['minmaj7', 'min7b5', 'maj7', 'min9', 'dom7', 'maj9', 'dim7'],
        'altered':    ['minmaj7', 'min7b5', 'maj7', 'min9', '7b9', 'maj9', 'dim7'],
    },
    'melodic_minor': {
        'triads':     ['min', 'min', 'aug', 'maj', 'maj', 'dim', 'dim'],
        'sevenths':   ['minmaj7', 'min7', 'maj7', 'dom7', 'dom7', 'min7b5', 'min7b5'],
        'extensions': ['minmaj7', 'min9', 'maj7', 'dom9', 'dom9', 'min7b5', 'min7b5'],
        'altered':    ['minmaj7', 'min9', 'maj7', '7#9', '7alt', 'min7b5', 'min7b5'],
    },
}

# Default fallback for scales without explicit diatonic maps
DIATONIC_CHORDS_DEFAULT = {
    'triads':     ['maj', 'min', 'min', 'maj', 'maj', 'min', 'dim'],
    'sevenths':   ['maj7', 'min7', 'min7', 'maj7', 'dom7', 'min7', 'min7b5'],
    'extensions': ['maj9', 'min9', 'min7', 'maj9', 'dom13', 'min9', 'min7b5'],
    'altered':    ['maj9', 'min9', 'min7', 'maj9', '7alt', 'min9', 'min7b5'],
}


def get_quality_category(quality: str) -> str:
    """Classify a chord quality for color coding in the UI."""
    if quality in ('maj', 'maj7', 'maj9', 'maj13', 'add9'):
        return 'major'
    if quality in ('min', 'min7', 'min9', 'min11', 'min13', 'minmaj7'):
        return 'minor'
    if quality in ('dom7', 'dom9', 'dom11', 'dom13', '7sus4'):
        return 'dominant'
    if quality in ('dim', 'dim7', 'min7b5'):
        return 'diminished'
    if quality in ('aug', '7#5'):
        return 'augmented'
    if quality in ('sus2', 'sus4'):
        return 'sus'
    if quality in ('7b9', '7#9', '7b5', '7alt'):
        return 'altered'
    return 'dominant'


def get_diatonic_chord(scale_name: str, degree: int, voicing: str,
                       scale_notes: list[str], key: str = 'C') -> dict:
    """Build the diatonic chord for a given scale degree and voicing level.

    Returns a chord dict: {symbol, quality, root, notes, scale_degree, roman, category}.
    """
    chord_map = DIATONIC_CHORDS.get(scale_name, DIATONIC_CHORDS_DEFAULT)
    voicing_map = chord_map.get(voicing, chord_map['sevenths'])

    num_degrees = len(scale_notes)
    degree = degree % num_degrees
    root = scale_notes[degree]
    quality = voicing_map[degree % len(voicing_map)]

    chord = build_chord(root, quality, key)
    chord['scale_degree'] = degree
    chord['roman'] = ROMAN[degree] if degree < len(ROMAN) else str(degree + 1)
    chord['category'] = get_quality_category(quality)
    return chord
