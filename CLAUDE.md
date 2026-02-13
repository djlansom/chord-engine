# Chord Engine

A gamified chord progression practice tool powered by a Turing Machine-inspired randomness engine.

## What This Is

A web-based practice tool for musicians (especially jazz pianists and improvisors) that generates evolving chord progressions using a 16-bit shift register with probabilistic feedback — adapted from the Music Thing Modular Turing Machine eurorack module.

**Key differentiator:** Unlike preset chord libraries (Scaler, Captain Chords) or pure random generators, this creates **looping sequences that gradually mutate**. The player practices a repeating progression that slowly evolves — familiar but always changing.

## Tech Stack

- **Backend:** Python (FastAPI) — serves API + static files
- **Frontend:** HTML/CSS/JS — dark theme, scrolling chord display
- **Audio:** Web Audio API — metronome clicks
- **Testing:** pytest with coverage targets
- **No database** — all state in memory, saved progressions in localStorage

## Project Structure

```
chord-engine/
├── CLAUDE.md            # This file — project rules and conventions
├── PLAN.md              # Build plan + future feature requests
├── requirements.txt     # fastapi, uvicorn
├── requirements-dev.txt # pytest, coverage, httpx
├── pyproject.toml       # pytest config, coverage thresholds
├── engine/
│   ├── __init__.py
│   ├── turing.py        # 16-bit shift register with probabilistic feedback
│   ├── theory.py        # Keys, scales, diatonic chords (jazz-capable)
│   ├── generator.py     # Progression generation (Turing + theory glue)
│   └── rhythm.py        # Pattern parsing, beat math, swing calculation
├── api/
│   ├── __init__.py
│   └── main.py          # FastAPI app (/config, /progression, /step)
├── static/
│   ├── index.html       # Main UI
│   ├── app.js           # Frontend logic, scheduler, metronome
│   └── style.css        # Dark theme, chord display styles
└── tests/
    ├── __init__.py
    ├── conftest.py       # Shared fixtures
    ├── test_turing.py    # ~30 tests
    ├── test_theory.py    # ~155 parametrized tests
    ├── test_generator.py # Generator integration tests
    ├── test_rhythm.py    # ~38 tests
    └── test_api.py       # API endpoint tests
```

## Running

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
# Open http://localhost:8000
```

## Testing

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
python -m pytest tests/ --cov=engine --cov=api --cov-report=term-missing
```

**Conventions:**
- No skipped tests. If a test exists, it must be implemented and passing.
- Every engine module gets its own test file with real assertions.
- API tests use FastAPI TestClient (synchronous), no httpx async needed.
- Coverage target: 85% minimum (enforced in pyproject.toml).
- Run the full suite before committing. Don't ship with red tests.

## Design Decisions

- **Turing register selects DEGREE** (which chord in the key), **voicing level selects EXTENSION** (triad vs 7th vs 9th vs altered) — two independent controls
- **Raw mode** = pure register output mapped to chords. **Smooth mode** = transition weights bias toward musical movements (ii-V-I etc.)
- **Enharmonic spelling** determined by key context (sharp keys use sharps, flat keys use flats). G is a sharp key, so G dorian b3 = A# not Bb.
- **Save system** captures the 16-bit register value — reload it with mutation=0 to replay the exact loop
- **Chord changes land ON the downbeat** — scheduler uses `pendingAdvance` flag so visual/audio changes are simultaneous with beat 1
- **Rhythm patterns** use a notation where each number = chords in that bar, `0` = hold previous chord. Pattern `[1, 0]` = chord lasts 2 bars. Pattern `[1, 1, 1, 2]` = 3 bars of 1 chord, bar 4 gets 2 chords.

## Development Workflow

1. Write/modify engine code
2. Write/update tests — no placeholders, no skips
3. Run `python -m pytest tests/ -v` — all green
4. Test in browser at localhost:8000
5. Commit with descriptive message

## MAPIS-ONE Integration

David's personal intelligence system lives at c:\Code_Projects\career-agent\mapis-one\

For deliberation, blind spot scans, or accountability checks:
1. Read agent prompts: src/mapis/agents/{navigator,challenger,builder}/system_prompt.md
2. Read state: data/state/goals.yaml, decisions.yaml, accountability.yaml
3. Follow protocols in CLAUDE.md (deliberation, blind spot scan, accountability check modes)

To capture MAPIS improvement ideas from this project:
- Append to: c:\Code_Projects\career-agent\mapis-one\data\state\backlog.yaml
- Format: `{date, source_project: "chord-engine", idea, status: pending}`

## Full Build Plan

The detailed implementation plan (Turing Machine algorithm, music theory engine, UI/UX specs, deployment strategy) is at:
- c:\Code_Projects\chord-engine\PLAN.md
