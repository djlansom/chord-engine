# Chord Engine — Build Plan

> This plan was developed in a MAPIS-ONE deliberation session (2026-02-12).
> Step 0 (cross-project wiring) was completed in MAPIS-ONE context.
> Steps 1-5 are for this repo.

## Step 1: Project Setup (~10 min)

- Python venv + `pip install fastapi uvicorn`
- Create `__init__.py` files in engine/ and api/
- `requirements.txt`: fastapi, uvicorn
- Git init

## Step 2: Music Theory Engine + Turing Machine Core (~60 min)

This is the heart of the project. Three modules that work together.

### `engine/turing.py` — The Sequence Engine (Turing Machine adaptation)

Based on Music Thing Modular's Turing Machine by Tom Whitwell. The original hardware uses a 16-bit shift register with probabilistic feedback to create **looping sequences that gradually mutate** — not random, not fixed, but evolving.

**How the original hardware works (on each clock pulse):**
1. All bits in a 16-bit register shift one position right
2. The bit that falls off the end feeds back to bit 0, BUT:
   - Probability knob fully CW: bit returns unchanged (locked loop)
   - Probability knob at noon: fresh random bit (fully random)
   - Probability knob in between: bit has a chance of being XOR-flipped (gradual mutation)
3. First 8 bits of register -> DAC -> output voltage (0-255 range mapped to pitch)
4. Length switch (2/3/4/5/6/8/12/16) controls which bit feeds back, setting loop length

**Our adaptation:** bits -> scale degree index -> chord.

```python
class TuringRegister:
    """16-bit shift register with probabilistic feedback,
    adapted from Music Thing Modular's Turing Machine."""

    def __init__(self, seed=None, length=8):
        self.register = seed or random.getrandbits(16)  # 16-bit initial state
        self.length = length        # loop length (2-16)
        self.probability = 0.0      # 0.0 = locked, 1.0 = fully random, 0.0-1.0 = mutation rate

    def step(self) -> int:
        """Advance one clock step. Returns current output value."""
        # 1. Read the feedback bit (the bit at position 'length')
        feedback_bit = (self.register >> self.length) & 1

        # 2. Probabilistic flip: maybe XOR the feedback bit
        if random.random() < self.probability:
            feedback_bit ^= 1  # flip it

        # 3. Shift register right by 1
        self.register >>= 1

        # 4. Write feedback bit to the top position
        self.register |= (feedback_bit << 15)

        # 5. Output: first 8 bits -> value 0-255
        return self.register & 0xFF

    def get_scale_degree(self, num_degrees=7) -> int:
        """Map the 8-bit output to a scale degree index (0-6 for diatonic)."""
        raw = self.register & 0xFF
        return raw % num_degrees
```

**Key behaviors preserved from hardware:**
- `probability = 0.0` -> locked loop, same chord sequence repeats forever
- `probability = 1.0` -> fully random, no repetition
- `probability = 0.1-0.3` -> "the sweet spot" — loop with occasional mutations
- Same seed + same probability + same length = deterministic (reproducible)
- Changing length mid-play creates new loop points without resetting

**Extensions beyond hardware:**
- Multiple registers at different lengths -> polymetric chord layers
- "Write" mode: manually inject a scale degree into the register
- UI complexity slider maps to probability (simple=0.05, medium=0.15, complex=0.4)

### `engine/theory.py` — Music Theory Foundation (Jazz-capable)

```python
# Two chromatic representations — context determines which to use
SHARPS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLATS  = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Key signature determines spelling:
#   Sharp keys (G, D, A, E, B, F#) -> SHARPS
#   Flat keys (F, Bb, Eb, Ab, Db, Gb) -> FLATS
#   C -> default to sharps
```

**Scales (20+):** All 7 major modes, harmonic minor + phrygian dominant, melodic minor + lydian dominant + altered, whole tone, both diminished scales, blues, pentatonics, bebop dominant, bebop major.

**Chord types (30+):** Triads (maj, min, dim, aug, sus2, sus4), 7ths (maj7, min7, dom7, min7b5, dim7, minmaj7, 7sus4), 9ths (maj9, min9, 9, add9), 11ths (min11, 11), 13ths (maj13, min13, 13), altered dominants (7b9, 7#9, 7b5, 7#5, 7alt).

**Diatonic chord maps:** Jazz default = 7th chords, not triads. Each scale type has its own chord quality map.

**Voicing complexity levels (independent from mutation rate):**
- triads: I, ii, iii, IV, V, vi, vii deg
- sevenths: Imaj7, ii7, iii7, IVmaj7, V7, vi7, vii half-dim
- extensions: Imaj9, ii9, IVmaj9, V13, etc.
- altered: Full jazz voicings with altered dominants

**Key design: Turing register selects DEGREE, voicing level selects EXTENSION.**

### `engine/generator.py` — Progression Generator

Ties Turing + Theory together. Two modes (switchable toggle in UI):
- **Raw mode**: Pure register output -> scale degree -> chord. Weird jumps are features.
- **Smooth mode**: Transition weight table biases toward musical movements (V->I, ii->V strongly preferred).

Transition weights:
```python
{
    0: {3: 3, 4: 3, 5: 2, 1: 1, 2: 1, 6: 0.5},  # I -> IV, V strongly preferred
    1: {4: 3, 0: 2, 3: 1, 5: 1},                   # ii -> V strongly preferred
    2: {5: 3, 3: 2, 0: 1},                          # iii -> vi, IV
    3: {4: 3, 0: 2, 1: 2, 6: 1},                    # IV -> V, I, ii
    4: {0: 4, 5: 2, 3: 1},                          # V -> I very strongly preferred
    5: {3: 3, 4: 2, 1: 2, 2: 1},                    # vi -> IV, V, ii
    6: {0: 3, 4: 2, 5: 1},                          # vii -> I, V
}
```

**Mutation slider (the "knob"):**
- Far left (~0.0): Locked loop
- Low (~0.05-0.1): Near-locked, occasional mutations (sweet spot)
- Medium (~0.15-0.25): Moderate evolution over ~32 bars
- High (~0.4+): Rapid mutation
- Far right (~1.0): Fully random / chaos mode

## Step 3: API Layer (~20 min)

`api/main.py` — FastAPI:
- `GET /progression?key=C&scale=ionian&length=8&mutation=0.1&voicing=sevenths&mode=raw&seed=optional`
- Returns JSON: `{chords: [{symbol, quality, root, scale_degree, roman, notes}], register_state, seed}`
- `GET /step` — advance one step, return current chord + register state
- `GET /config` — available keys, scales, voicings, length options
- Static file serving for frontend
- WebSocket endpoint for real-time streaming (beat-synced chord updates)

## Step 4: UI / UX (~60 min)

Dark theme. Large readable chord symbols (visible from 3-5 feet at instrument).

**Three-zone layout:**

```
+-----------------------------------------------------------+
|  HEADER: Key [C v] | Scale [Ionian v] | BPM [120] | Seed  |
+-----------------------------------------------------------+
|                                                           |
|  SCROLLING DISPLAY (main focus):                          |
|                                                           |
|  (faded)   (faded)  |  CURRENT  |  (next)   (next)       |
|   Am7       Dm7     |    G7     |  Cmaj7     Am7         |
|                     |  (LARGE)  |                        |
|                                                           |
|  [beat indicator: * o o o ]  <-- pulses with tempo        |
|                                                           |
+-----------------------------------------------------------+
|  LOOP VIEW (toggleable):                                  |
|  [Cmaj7][Am7][Dm7][G7*][Cmaj7][Fmaj7][Dm7][G7]          |
|  Mutated chords flash briefly                             |
+-----------------------------------------------------------+
|  CONTROLS:                                                |
|  Mutation: [----*-----------]  Voicing: [7ths v]          |
|  Mode: [Raw o Smooth]  Length: [8 v]                      |
|  [> Play] [~ New Seed] [Save Loop] [History]              |
|  Metronome: [Audio v] [Visual o]                          |
+-----------------------------------------------------------+
```

**Scrolling display:** Current chord 48-72px white centered. Upcoming 32px dimmed. Past faded. Smooth CSS transitions. 5-7 chords visible.

**Beat indicator:** 4 dots, current beat filled. Progress bar per chord.

**Loop view:** Full Turing loop as horizontal strip. Current position marked. Mutations flash. Toggleable.

**Color coding (chord quality):**
- Major: warm gold (#D4A843)
- Minor: cool blue (#5B8CB8)
- Dominant: amber (#D48A43)
- Diminished/half-dim: muted red (#B85B5B)
- Augmented: purple (#8B5BB8)
- Sus: green (#5BB87A)

**Audio metronome (Web Audio API):**
- Beat 1: higher click (hi-hat). Beats 2-4: softer click.
- Volume control. Synced to chord clock. 4/4 time for v0.1.

**Save system:**
- Captures 16-bit register value + all settings
- Replay: load state, set mutation=0, same loop plays
- History panel (collapsible sidebar)
- Export as text chord list

**Keyboard shortcuts:**
- Spacebar: play/pause
- S: save current loop
- Up/Down: tempo +/- 5 BPM
- Left/Right: mutation +/- 0.05
- M: toggle audio metronome
- L: toggle loop view
- N: new random seed

## Step 5: Play-Test and Tune (~20 min)

- Run with instrument, tune randomness parameters
- Verify deterministic replay (same seed = same progression)
- Adjust tempo range (40-200 BPM)

## Deployment

Phase 1: Python + local (`uvicorn api.main:app`). Share via ngrok.
Phase 2: Railway/Render free tier.
Phase 3: Port engine to JS for static deployment (Vercel/Netlify).

## Verification Checklist

- [ ] `uvicorn api.main:app` starts cleanly
- [ ] `/progression` returns valid chord JSON
- [ ] UI loads, chords scroll at selected tempo
- [ ] Can change key, scale, tempo, voicing, mutation in real-time
- [ ] Same seed = same progression (deterministic)
- [ ] Raw vs Smooth modes produce different output
- [ ] Audio metronome clicks in time
- [ ] Save/load loop works
- [ ] Keyboard shortcuts work
- [ ] Progressions sound musically coherent (play-test)

---

## Future Feature Requests

### Chromatic Chords
Option to inject non-diatonic (chromatic) chords into progressions — tritone subs, borrowed chords, chromatic approach chords. Could be a toggle or a "chromaticism" slider alongside mutation.

### Run Mode — Key Modulation
Automatic key changes every X bars following jazz modulation patterns. Defined modulation schemes (e.g., cycle of 4ths, ii-V to new key, half-step up, Coltrane changes). User picks a modulation pattern and interval — the engine shifts the tonal center while keeping the Turing loop running.

### MIDI Output
Output chord changes as MIDI messages instead of (or alongside) Web Audio metronome clicks. Would allow routing into a DAW to play alongside VSTs, solving the Windows audio exclusivity issue. Could use Web MIDI API or a local MIDI server.
