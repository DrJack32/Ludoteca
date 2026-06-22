"""Backend tests for the 3-tier categorization feature:
- Estilo de juego (categoria)
- Temática (subestilo)
- Interacción (interaccion)

Validates: autocomplete defaults+merge, CRUD persistence of subestilo/interaccion,
search filters (case-insensitive partial), and the recommend endpoint AND-filter +
scoring with Spanish reasons.
"""
import os
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load frontend .env to get public REACT_APP_BACKEND_URL
load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


DEFAULT_CATEGORIAS = {
    "Eurogame", "Familiar", "Party", "Estrategia", "Abstracto", "Sandbox",
    "Wargame", "Colocación de trabajadores", "Filler", "Deckbuilding",
    "Set collection", "Area control", "Push your luck", "Tile placement",
    "Roll & write",
}
DEFAULT_SUBESTILOS = {
    "Espacio", "Granja", "Mar", "Fantasía", "Medieval", "Ciencia ficción",
    "Histórico", "Naturaleza", "Mitología", "Aventura", "Terror",
    "Económico", "Guerra",
}
DEFAULT_INTERACCIONES = {
    "Solitario", "Cooperativo", "Semi-cooperativo", "Competitivo directo",
    "Competitivo indirecto", "Negociación", "Equipos", "Todos contra uno",
}


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def created_ids():
    ids = []
    yield ids
    # Cleanup
    s = requests.Session()
    for gid in ids:
        try:
            s.delete(f"{API}/games/{gid}", timeout=10)
        except Exception:
            pass


def _make_game(client, payload, created_ids):
    r = client.post(f"{API}/games", json=payload, timeout=15)
    assert r.status_code == 200, f"create failed {r.status_code}: {r.text}"
    data = r.json()
    created_ids.append(data["id"])
    return data


# ---------- Autocomplete ----------
class TestAutocomplete:
    def test_autocomplete_has_new_fields_and_defaults(self, client):
        r = client.get(f"{API}/autocomplete", timeout=15)
        assert r.status_code == 200
        data = r.json()
        # New fields present
        assert "subestilos" in data
        assert "interacciones" in data
        assert "categorias" in data
        assert isinstance(data["subestilos"], list)
        assert isinstance(data["interacciones"], list)

        # Defaults are merged in (even if DB has values)
        missing_cat = DEFAULT_CATEGORIAS - set(data["categorias"])
        assert not missing_cat, f"categorias missing defaults: {missing_cat}"
        missing_sub = DEFAULT_SUBESTILOS - set(data["subestilos"])
        assert not missing_sub, f"subestilos missing defaults: {missing_sub}"
        missing_int = DEFAULT_INTERACCIONES - set(data["interacciones"])
        assert not missing_int, f"interacciones missing defaults: {missing_int}"

    def test_autocomplete_merge_no_duplicates_case_insensitive(self, client, created_ids):
        # Create a game with a case-variant of a default value
        payload = {
            "nombre": "TEST_Autocomplete_Merge",
            "categoria": "eurogame",  # lowercase variant of default "Eurogame"
            "subestilo": "ESPACIO",    # upper variant of default "Espacio"
            "interaccion": "cooperativo",  # lower variant
        }
        _make_game(client, payload, created_ids)

        r = client.get(f"{API}/autocomplete", timeout=15)
        assert r.status_code == 200
        data = r.json()

        # No case-insensitive duplicates across categorias/subestilos/interacciones
        for field in ("categorias", "subestilos", "interacciones"):
            lowered = [v.lower() for v in data[field]]
            assert len(lowered) == len(set(lowered)), (
                f"Duplicate case-insensitive entries in {field}: {data[field]}"
            )

    def test_autocomplete_includes_db_custom_value(self, client, created_ids):
        # Add a non-default value to ensure DB values are merged with defaults
        payload = {
            "nombre": "TEST_Custom_Subestilo",
            "categoria": "TEST_CustomCategoria",
            "subestilo": "TEST_CustomSubestilo",
            "interaccion": "TEST_CustomInteraccion",
        }
        _make_game(client, payload, created_ids)

        r = client.get(f"{API}/autocomplete", timeout=15)
        data = r.json()
        assert "TEST_CustomCategoria" in data["categorias"]
        assert "TEST_CustomSubestilo" in data["subestilos"]
        assert "TEST_CustomInteraccion" in data["interacciones"]


# ---------- CRUD ----------
class TestGamesCRUD:
    def test_create_and_get_persists_new_fields(self, client, created_ids):
        payload = {
            "nombre": "TEST_Crud_Persist",
            "categoria": "Eurogame",
            "subestilo": "Espacio",
            "interaccion": "Cooperativo",
            "jugadores_minimo": 2,
            "jugadores_maximo": 4,
            "duracion_minima": 30,
            "duracion_maxima": 60,
            "complejidad": 3,
        }
        created = _make_game(client, payload, created_ids)
        assert created["subestilo"] == "Espacio"
        assert created["interaccion"] == "Cooperativo"
        assert created["categoria"] == "Eurogame"

        r = client.get(f"{API}/games/{created['id']}", timeout=10)
        assert r.status_code == 200
        g = r.json()
        assert g["subestilo"] == "Espacio"
        assert g["interaccion"] == "Cooperativo"
        assert g["categoria"] == "Eurogame"

    def test_update_subestilo_and_interaccion(self, client, created_ids):
        # Create
        created = _make_game(client, {
            "nombre": "TEST_Update_NewFields",
            "categoria": "Familiar",
            "subestilo": "Granja",
            "interaccion": "Competitivo directo",
        }, created_ids)
        gid = created["id"]

        # Update
        upd = client.put(f"{API}/games/{gid}", json={
            "subestilo": "Mar",
            "interaccion": "Negociación",
        }, timeout=10)
        assert upd.status_code == 200
        updated = upd.json()
        assert updated["subestilo"] == "Mar"
        assert updated["interaccion"] == "Negociación"
        assert updated["categoria"] == "Familiar"  # unchanged

        # GET to verify persistence
        g = client.get(f"{API}/games/{gid}", timeout=10).json()
        assert g["subestilo"] == "Mar"
        assert g["interaccion"] == "Negociación"


# ---------- Search ----------
@pytest.fixture(scope="module")
def search_seed(client, created_ids):
    games_payload = [
        {
            "nombre": "TEST_Search_Eurogame_Espacio_Coop",
            "categoria": "Eurogame",
            "subestilo": "Espacio",
            "interaccion": "Cooperativo",
            "jugadores_minimo": 2, "jugadores_maximo": 4,
            "duracion_minima": 30, "duracion_maxima": 60, "complejidad": 3,
        },
        {
            "nombre": "TEST_Search_Eurogame_Granja_Compet",
            "categoria": "Eurogame",
            "subestilo": "Granja",
            "interaccion": "Competitivo directo",
            "jugadores_minimo": 2, "jugadores_maximo": 5,
            "duracion_minima": 60, "duracion_maxima": 90, "complejidad": 3,
        },
        {
            "nombre": "TEST_Search_Party_Espacio_Compet",
            "categoria": "Party",
            "subestilo": "Espacio",
            "interaccion": "Competitivo directo",
            "jugadores_minimo": 4, "jugadores_maximo": 8,
            "duracion_minima": 20, "duracion_maxima": 30, "complejidad": 1,
        },
    ]
    out = [_make_game(client, p, created_ids) for p in games_payload]
    return out


class TestSearch:
    def test_search_by_subestilo_case_insensitive_partial(self, client, search_seed):
        r = client.post(f"{API}/games/search", json={"subestilo": "espa"}, timeout=10)
        assert r.status_code == 200
        names = [g["nombre"] for g in r.json()]
        assert "TEST_Search_Eurogame_Espacio_Coop" in names
        assert "TEST_Search_Party_Espacio_Compet" in names
        assert "TEST_Search_Eurogame_Granja_Compet" not in names

    def test_search_by_interaccion_case_insensitive_partial(self, client, search_seed):
        r = client.post(f"{API}/games/search", json={"interaccion": "COMPETITIVO"}, timeout=10)
        assert r.status_code == 200
        names = [g["nombre"] for g in r.json()]
        assert "TEST_Search_Eurogame_Granja_Compet" in names
        assert "TEST_Search_Party_Espacio_Compet" in names
        assert "TEST_Search_Eurogame_Espacio_Coop" not in names

    def test_search_combined_categoria_subestilo_interaccion_players(self, client, search_seed):
        r = client.post(f"{API}/games/search", json={
            "categoria": "Eurogame",
            "subestilo": "Espacio",
            "interaccion": "Cooperativo",
            "jugadores_minimo": 3,  # game must support 3 players or more (max>=3)
            "jugadores_maximo": 4,
        }, timeout=10)
        assert r.status_code == 200
        names = [g["nombre"] for g in r.json()]
        assert "TEST_Search_Eurogame_Espacio_Coop" in names
        # Party game excluded by categoria=Eurogame
        assert "TEST_Search_Party_Espacio_Compet" not in names
        # Granja excluded by subestilo
        assert "TEST_Search_Eurogame_Granja_Compet" not in names


# ---------- Recommend ----------
class TestRecommend:
    def test_recommend_applies_subestilo_and_interaccion_as_AND_filter(self, client, search_seed):
        r = client.post(f"{API}/recommend", json={
            "jugadores": 3,
            "subestilo": "Espacio",
            "interaccion": "Cooperativo",
            "limit": 20,
        }, timeout=15)
        assert r.status_code == 200
        results = r.json()
        names = [rec["juego"]["nombre"] for rec in results]
        # Only the Eurogame_Espacio_Coop game (supports 3 players, espacio+coop) qualifies
        assert "TEST_Search_Eurogame_Espacio_Coop" in names
        assert "TEST_Search_Eurogame_Granja_Compet" not in names
        assert "TEST_Search_Party_Espacio_Compet" not in names

    def test_recommend_includes_spanish_reasons_for_new_fields(self, client, search_seed):
        r = client.post(f"{API}/recommend", json={
            "jugadores": 3,
            "subestilo": "Espacio",
            "interaccion": "Cooperativo",
            "limit": 5,
        }, timeout=15)
        assert r.status_code == 200
        results = r.json()
        assert len(results) >= 1
        target = next(
            rec for rec in results
            if rec["juego"]["nombre"] == "TEST_Search_Eurogame_Espacio_Coop"
        )
        reasons_str = " | ".join(target["razones"])
        assert "🎨 Temática:" in reasons_str, f"missing temática reason: {reasons_str}"
        assert "🤝 Interacción:" in reasons_str, f"missing interacción reason: {reasons_str}"
        # score should be a positive int
        assert isinstance(target["score"], int)
        assert target["score"] > 0

    def test_recommend_without_new_fields_still_works(self, client, search_seed):
        r = client.post(f"{API}/recommend", json={
            "jugadores": 4,
            "limit": 5,
        }, timeout=15)
        assert r.status_code == 200
        results = r.json()
        assert isinstance(results, list)
        # At least one of the seeded games supports 4 players
        names = [rec["juego"]["nombre"] for rec in results]
        assert any(n.startswith("TEST_Search_") for n in names)
