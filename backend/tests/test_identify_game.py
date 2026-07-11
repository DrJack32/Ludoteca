"""Tests for POST /api/identify-game - robustness against various image inputs."""
import base64
import io
import os

import pytest
import requests
from PIL import Image, ImageDraw

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://repo-restore-9.preview.emergentagent.com").rstrip("/")
ENDPOINT = f"{BASE_URL}/api/identify-game"


def _make_image_bytes(fmt: str, size=(600, 400), text="CATAN") -> bytes:
    img = Image.new("RGB", size, color=(240, 220, 180))
    d = ImageDraw.Draw(img)
    # Big text so GPT can read it
    try:
        d.text((size[0] // 6, size[1] // 3), text, fill=(20, 20, 20))
    except Exception:
        pass
    buf = io.BytesIO()
    if fmt.upper() == "JPEG":
        img.save(buf, format="JPEG", quality=90)
    elif fmt.upper() == "WEBP":
        img.save(buf, format="WEBP", quality=90)
    elif fmt.upper() == "PNG":
        img.save(buf, format="PNG")
    else:
        img.save(buf, format=fmt)
    return buf.getvalue()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


# ---------- Success cases (call OpenAI) ----------

def test_identify_valid_jpeg_returns_200():
    """A synthetic JPEG with the word CATAN should return 200 with titulos array (possibly empty)."""
    payload = {"imagen": f"data:image/jpeg;base64,{_b64(_make_image_bytes('JPEG'))}"}
    r = requests.post(ENDPOINT, json=payload, timeout=60)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert "titulos" in data
    assert isinstance(data["titulos"], list)


def test_identify_webp_returns_200():
    """WEBP should now be accepted (was rejected before fix)."""
    payload = {"imagen": f"data:image/webp;base64,{_b64(_make_image_bytes('WEBP'))}"}
    r = requests.post(ENDPOINT, json=payload, timeout=60)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert "titulos" in data
    assert isinstance(data["titulos"], list)


def test_identify_large_png_returns_200():
    """A large 4000x5000 PNG should be resized server-side and accepted."""
    payload = {"imagen": _b64(_make_image_bytes("PNG", size=(4000, 5000), text="WINGSPAN"))}
    r = requests.post(ENDPOINT, json=payload, timeout=90)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert "titulos" in data
    assert isinstance(data["titulos"], list)


def test_identify_raw_base64_no_prefix_returns_200():
    """Raw base64 (no data:image/... prefix) should work."""
    payload = {"imagen": _b64(_make_image_bytes("JPEG", text="AZUL"))}
    r = requests.post(ENDPOINT, json=payload, timeout=60)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert "titulos" in r.json()


# ---------- Error cases (no OpenAI call) ----------

def test_identify_malformed_base64_returns_422():
    """Invalid base64 should return 422 with Spanish error message."""
    r = requests.post(ENDPOINT, json={"imagen": "invalid_base64!!!"}, timeout=15)
    # Note: b64decode with validate=False might still decode, so it may fall through to Image.open
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
    detail = r.json().get("detail", "")
    assert (
        "No se pudo decodificar la imagen" in detail
        or "No se pudo abrir la imagen" in detail
        or "demasiado pequeña" in detail
    ), f"Unexpected detail: {detail}"


def test_identify_valid_b64_but_not_image_returns_422():
    """Valid base64 encoding of plain text (not image) should return 422."""
    fake = base64.b64encode(b"this is just some plain text, definitely not an image file at all, padding padding" * 5).decode()
    r = requests.post(ENDPOINT, json={"imagen": fake}, timeout=15)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}: {r.text}"
    detail = r.json().get("detail", "")
    assert (
        "No se pudo abrir la imagen" in detail
        or "demasiado pequeña" in detail
        or "No se pudo decodificar" in detail
    ), f"Unexpected detail: {detail}"


def test_identify_empty_image_returns_400():
    """Empty imagen field should return 400 with 'Falta la imagen'."""
    r = requests.post(ENDPOINT, json={"imagen": ""}, timeout=10)
    assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
    assert r.json().get("detail") == "Falta la imagen"


def test_identify_never_leaks_openai_error():
    """Any failing case must NOT surface litellm/OpenAI internals as HTTP 500."""
    # Send a corrupt image
    fake = base64.b64encode(b"\x00\x01\x02" * 100).decode()
    r = requests.post(ENDPOINT, json={"imagen": fake}, timeout=30)
    # Must be 422 (not 500)
    assert r.status_code != 500, f"Should not return 500; got {r.status_code}: {r.text}"
    body = r.text.lower()
    assert "litellm" not in body
    assert "unsupported image" not in body
    assert "badrequesterror" not in body
