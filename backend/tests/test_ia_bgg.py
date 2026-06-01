"""
Tests for the new AI + BoardGameGeek endpoints and regression on existing /api/games endpoints.

Endpoints under test:
- POST /api/identify-game            (GPT-4o vision)
- GET  /api/bgg/search               (BGG XML search)
- GET  /api/bgg/details/{bgg_id}     (BGG XML thing + Spanish translation)
- Regression: /api/games CRUD, /api/statistics, /api/autocomplete
"""
import base64
import io
import os
import time

import pytest
import requests
from PIL import Image, ImageDraw, ImageFont

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://repo-restore-9.preview.emergentagent.com").rstrip("/")
# OpenAI vision + BGG translation can be slow.
LLM_TIMEOUT = 90
BGG_TIMEOUT = 90


# ------------- Helpers -------------
def _make_test_image(text: str = "CATAN") -> str:
    """Create a small JPEG with visible text and return raw base64 string."""
    img = Image.new("RGB", (640, 360), color=(220, 180, 90))
    draw = ImageDraw.Draw(img)
    # use default font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 96)
    except Exception:
        font = ImageFont.load_default()
    # roughly center
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((640 - tw) / 2, (360 - th) / 2), text, fill=(20, 20, 20), font=font)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


# ------------- Fixtures -------------
@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ------------- 1) Smoke -------------
def test_api_root(api):
    r = api.get(f"{BASE_URL}/api/", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "message" in body
    assert "Ludoteca" in body["message"]


# ------------- 2) /api/identify-game -------------
def test_identify_game_valid_image(api):
    img_b64 = _make_test_image("CATAN")
    r = api.post(
        f"{BASE_URL}/api/identify-game",
        json={"imagen": img_b64},
        timeout=LLM_TIMEOUT,
    )
    assert r.status_code == 200, f"body={r.text}"
    data = r.json()
    # structure
    assert "titulos" in data
    assert "codigo_barras" in data
    assert isinstance(data["titulos"], list)
    # codigo_barras may be null or string
    assert data["codigo_barras"] is None or isinstance(data["codigo_barras"], str)
    # at least one candidate detected (image clearly says CATAN)
    assert len(data["titulos"]) >= 1
    # contains "Catan" (case insensitive) in any candidate ideally
    joined = " | ".join(data["titulos"]).lower()
    assert "catan" in joined, f"Expected 'catan' in detected titles, got: {data['titulos']}"


def test_identify_game_with_data_url_prefix(api):
    """Server should also strip 'data:image/jpeg;base64,' prefix."""
    img_b64 = _make_test_image("CATAN")
    payload = f"data:image/jpeg;base64,{img_b64}"
    r = api.post(
        f"{BASE_URL}/api/identify-game",
        json={"imagen": payload},
        timeout=LLM_TIMEOUT,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data.get("titulos"), list)


def test_identify_game_missing_image(api):
    """Missing imagen → 400 (validation 422 also acceptable for pydantic missing field)."""
    # Empty string -> our code raises 400. Missing key -> pydantic 422.
    r = api.post(
        f"{BASE_URL}/api/identify-game",
        json={"imagen": ""},
        timeout=20,
    )
    assert r.status_code == 400, f"Expected 400 for empty imagen, got {r.status_code}: {r.text}"


def test_identify_game_no_field(api):
    r = api.post(f"{BASE_URL}/api/identify-game", json={}, timeout=20)
    assert r.status_code in (400, 422), r.text


# ------------- 3) /api/bgg/search -------------
def test_bgg_search_catan(api):
    r = api.get(f"{BASE_URL}/api/bgg/search", params={"q": "Catan", "limit": 5}, timeout=BGG_TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert 1 <= len(data) <= 5
    first = data[0]
    # required keys
    for k in ("bgg_id", "nombre"):
        assert k in first
    assert "año" in first  # may be null
    assert "thumbnail" in first  # may be null
    # bgg_id should be numeric string
    assert first["bgg_id"].isdigit()
    # at least one item should contain 'Catan'
    assert any("catan" in (item["nombre"] or "").lower() for item in data)


def test_bgg_search_no_results(api):
    r = api.get(
        f"{BASE_URL}/api/bgg/search",
        params={"q": "xkjsdkjdsh", "limit": 5},
        timeout=BGG_TIMEOUT,
    )
    assert r.status_code == 200, r.text
    assert r.json() == []


def test_bgg_search_empty_query_validation(api):
    r = api.get(f"{BASE_URL}/api/bgg/search", params={"q": "", "limit": 5}, timeout=20)
    # FastAPI Query(..., min_length=1) → 422
    assert r.status_code == 422


# ------------- 4) /api/bgg/details/{id} -------------
def test_bgg_details_catan_spanish(api):
    # BGG ID 13 = Catan
    r = api.get(f"{BASE_URL}/api/bgg/details/13", timeout=BGG_TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    # required keys present
    for k in (
        "bgg_id", "nombre", "descripcion", "categoria", "autor", "editorial",
        "año_publicacion", "jugadores_minimo", "jugadores_maximo",
        "duracion_minima", "duracion_maxima", "complejidad", "imagen",
    ):
        assert k in data, f"Missing key {k}"

    assert data["bgg_id"] == "13"
    assert "catan" in data["nombre"].lower()
    # Catan 1995
    assert data["año_publicacion"] == 1995
    assert data["jugadores_minimo"] == 3
    assert data["jugadores_maximo"] == 4
    # Designer Klaus Teuber
    assert "teuber" in data["autor"].lower()
    # Image should be a URL
    assert isinstance(data["imagen"], str) and data["imagen"].startswith("http")
    # Complexity 1..5
    assert data["complejidad"] is None or 1 <= data["complejidad"] <= 5
    # Description must be non-empty and translated to Spanish (heuristic: contains common Spanish words)
    desc = (data["descripcion"] or "").lower()
    assert len(desc) > 100, f"Descripcion too short: {len(desc)} chars"
    spanish_markers = [" de ", " que ", " los ", " las ", " el ", " la ", " un ", " una ", " para ", " con ", " jugador"]
    hits = sum(1 for m in spanish_markers if m in desc)
    assert hits >= 3, f"Description does not look Spanish (markers hit={hits}). First 200 chars: {desc[:200]}"
    # Category translated (heuristic)
    assert data["categoria"]  # non-empty


def test_bgg_details_no_translate(api):
    """translate=false should skip GPT translation and be much faster."""
    t0 = time.time()
    r = api.get(f"{BASE_URL}/api/bgg/details/13", params={"translate": "false"}, timeout=BGG_TIMEOUT)
    elapsed = time.time() - t0
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["bgg_id"] == "13"
    # English description usually contains "Catan" and English connectors
    assert data["descripcion"]
    # Should be faster than translated path (sanity, not strict)
    assert elapsed < 60


def test_bgg_details_invalid_id(api):
    r = api.get(f"{BASE_URL}/api/bgg/details/99999999", timeout=BGG_TIMEOUT)
    # Our endpoint raises 404 when BGG returns no <item>
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"


# ------------- 5) Regression: /api/games CRUD -------------
class TestGamesRegression:
    created_id = None

    def test_create_game(self, api):
        payload = {
            "nombre": "TEST_Catan_Regresion",
            "descripcion": "Juego de prueba creado por test",
            "categoria": "Estrategia",
            "autor": "Klaus Teuber",
            "editorial": "Devir",
            "año_publicacion": 1995,
            "jugadores_minimo": 3,
            "jugadores_maximo": 4,
            "duracion_minima": 60,
            "duracion_maxima": 120,
            "complejidad": 2,
            "idioma": "Español",
        }
        r = api.post(f"{BASE_URL}/api/games", json=payload, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["nombre"] == payload["nombre"]
        assert data["autor"] == payload["autor"]
        assert data["año_publicacion"] == 1995
        assert "id" in data
        TestGamesRegression.created_id = data["id"]

    def test_get_game_by_id(self, api):
        assert TestGamesRegression.created_id
        r = api.get(f"{BASE_URL}/api/games/{TestGamesRegression.created_id}", timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["nombre"] == "TEST_Catan_Regresion"

    def test_list_games(self, api):
        r = api.get(f"{BASE_URL}/api/games", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_update_game(self, api):
        assert TestGamesRegression.created_id
        r = api.put(
            f"{BASE_URL}/api/games/{TestGamesRegression.created_id}",
            json={"notas": "actualizado por test"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        # verify persisted
        g = api.get(f"{BASE_URL}/api/games/{TestGamesRegression.created_id}", timeout=15).json()
        assert g["notas"] == "actualizado por test"

    def test_search_games(self, api):
        r = api.post(
            f"{BASE_URL}/api/games/search",
            json={"nombre": "TEST_Catan_Regresion"},
            timeout=15,
        )
        assert r.status_code == 200
        results = r.json()
        assert any(g["id"] == TestGamesRegression.created_id for g in results)

    def test_statistics_endpoint(self, api):
        r = api.get(f"{BASE_URL}/api/statistics", timeout=20)
        assert r.status_code == 200
        data = r.json()
        for k in ("total_juegos", "categorias_populares", "autores_populares", "rango_jugadores"):
            assert k in data

    def test_autocomplete_endpoint(self, api):
        r = api.get(f"{BASE_URL}/api/autocomplete", timeout=15)
        assert r.status_code == 200
        data = r.json()
        for k in ("categorias", "autores", "editoriales", "idiomas"):
            assert k in data and isinstance(data[k], list)

    def test_delete_game(self, api):
        assert TestGamesRegression.created_id
        r = api.delete(f"{BASE_URL}/api/games/{TestGamesRegression.created_id}", timeout=15)
        assert r.status_code == 200
        # verify gone
        r2 = api.get(f"{BASE_URL}/api/games/{TestGamesRegression.created_id}", timeout=15)
        assert r2.status_code == 404
