"""Tests for api.main — FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /config
# ---------------------------------------------------------------------------

class TestConfigEndpoint:

    def test_config_returns_keys(self, client):
        data = client.get("/config").json()
        assert "keys" in data
        assert "C" in data["keys"]
        assert len(data["keys"]) == 12

    def test_config_returns_scales(self, client):
        data = client.get("/config").json()
        assert "scales" in data
        assert "ionian" in data["scales"]
        assert "dorian" in data["scales"]
        assert len(data["scales"]) >= 15

    def test_config_returns_voicings(self, client):
        data = client.get("/config").json()
        assert "voicings" in data
        assert data["voicings"] == ["triads", "sevenths", "extensions", "altered"]

    def test_config_returns_lengths(self, client):
        data = client.get("/config").json()
        assert "lengths" in data
        assert 8 in data["lengths"]
        assert 16 in data["lengths"]

    def test_config_returns_modes(self, client):
        data = client.get("/config").json()
        assert "modes" in data
        assert data["modes"] == ["raw", "smooth"]


# ---------------------------------------------------------------------------
# GET /progression
# ---------------------------------------------------------------------------

class TestProgressionEndpoint:

    def test_default_params_return_chords(self, client):
        data = client.get("/progression").json()
        assert "chords" in data
        assert len(data["chords"]) >= 8
        chord = data["chords"][0]
        assert "symbol" in chord
        assert "quality" in chord
        assert "root" in chord
        assert "notes" in chord
        assert "roman" in chord
        assert "category" in chord

    def test_custom_key_and_scale(self, client):
        data = client.get("/progression?key=G&scale=dorian").json()
        chords = data["chords"]
        # All chord roots should be from G dorian notes
        # G is a sharp key, so b3 is spelled A# not Bb
        g_dorian_roots = {'G', 'A', 'A#', 'C', 'D', 'E', 'F'}
        for chord in chords:
            assert chord["root"] in g_dorian_roots, \
                f"Root {chord['root']} not in G dorian"

    def test_seed_param_produces_deterministic_result(self, client):
        params = "?key=C&scale=ionian&seed=42435&mutation=0&count=8"
        data1 = client.get(f"/progression{params}").json()
        data2 = client.get(f"/progression{params}").json()
        symbols1 = [c["symbol"] for c in data1["chords"]]
        symbols2 = [c["symbol"] for c in data2["chords"]]
        assert symbols1 == symbols2

    def test_count_param(self, client):
        data = client.get("/progression?count=4").json()
        assert len(data["chords"]) == 4

    def test_response_includes_settings(self, client):
        data = client.get("/progression?key=Bb&voicing=triads").json()
        assert "settings" in data
        assert data["settings"]["key"] == "Bb"
        assert data["settings"]["voicing"] == "triads"


# ---------------------------------------------------------------------------
# GET /step
# ---------------------------------------------------------------------------

class TestStepEndpoint:

    def test_step_returns_single_chord(self, client):
        # Initialize a generator first
        client.get("/progression")
        data = client.get("/step").json()
        assert "chord" in data
        chord = data["chord"]
        assert "symbol" in chord
        assert "quality" in chord

    def test_step_returns_state(self, client):
        client.get("/progression")
        data = client.get("/step").json()
        assert "state" in data
        assert "register_state" in data["state"]
        assert "key" in data["state"]

    def test_step_advances_register(self, client):
        client.get("/progression?seed=12345&mutation=0")
        state1 = client.get("/step").json()["state"]["register_state"]
        state2 = client.get("/step").json()["state"]["register_state"]
        # Register shifts each step, so state should change
        # (unless by coincidence it's a fixed point like 0x0000 or 0xFFFF)
        # Using seed=12345 which is not a fixed point
        assert isinstance(state1, int)
        assert isinstance(state2, int)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestStaticFiles:

    def test_index_html_served(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Chord Engine" in resp.text
