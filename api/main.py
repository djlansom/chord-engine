"""FastAPI app — serves API endpoints and static files."""

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from engine.generator import ProgressionGenerator
from engine.theory import SCALES, DIATONIC_CHORDS, SHARPS, FLATS

app = FastAPI(title="Chord Engine")

# Global generator instance (in-memory state)
generator: ProgressionGenerator | None = None

ALL_KEYS = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
VOICINGS = ['triads', 'sevenths', 'extensions', 'altered']
MODES = ['raw', 'smooth']


def _ensure_generator(**kwargs) -> ProgressionGenerator:
    """Create or reconfigure the global generator."""
    global generator
    generator = ProgressionGenerator(**kwargs)
    return generator


@app.get("/config")
def get_config():
    """Available keys, scales, voicings, modes, and length options."""
    return {
        "keys": ALL_KEYS,
        "scales": list(SCALES.keys()),
        "voicings": VOICINGS,
        "modes": MODES,
        "lengths": [2, 3, 4, 5, 6, 8, 12, 16],
    }


@app.get("/progression")
def get_progression(
    key: str = Query("C"),
    scale: str = Query("ionian"),
    length: int = Query(8),
    mutation: float = Query(0.1),
    voicing: str = Query("sevenths"),
    mode: str = Query("raw"),
    seed: int | None = Query(None),
    count: int = Query(8),
):
    """Generate a chord progression."""
    gen = _ensure_generator(
        key=key, scale=scale, length=length,
        mutation=mutation, voicing=voicing, mode=mode, seed=seed,
    )
    chords = gen.generate(count)
    state = gen.get_state()
    return {
        "chords": chords,
        "register_state": state["register_state"],
        "seed": seed,
        "settings": state,
    }


@app.get("/step")
def step_one():
    """Advance one step. Returns current chord + register state."""
    global generator
    if generator is None:
        generator = ProgressionGenerator()
    chord = generator.step()
    return {
        "chord": chord,
        "state": generator.get_state(),
    }


@app.post("/configure")
def configure(
    key: str = Query(None),
    scale: str = Query(None),
    length: int = Query(None),
    mutation: float = Query(None),
    voicing: str = Query(None),
    mode: str = Query(None),
):
    """Update generator settings without resetting the register."""
    global generator
    if generator is None:
        generator = ProgressionGenerator()
    if key is not None:
        generator.set_key(key)
    if scale is not None:
        generator.set_scale(scale)
    if length is not None:
        generator.set_length(length)
    if mutation is not None:
        generator.set_mutation(mutation)
    if voicing is not None:
        generator.set_voicing(voicing)
    if mode is not None:
        generator.set_mode(mode)
    return {"status": "ok", "state": generator.get_state()}


# Serve static files and SPA fallback
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")
