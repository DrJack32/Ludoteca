"""
Servicio de identificación de juegos: GPT-4o vision + BoardGameGeek API.
"""
import os
import re
import uuid
import json
import logging
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any

import httpx
from pydantic import BaseModel
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

logger = logging.getLogger(__name__)

BGG_BASE = "https://boardgamegeek.com/xmlapi2"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
BGG_TOKEN = os.environ.get("BGG_API_TOKEN", "")


def _bgg_headers() -> Dict[str, str]:
    h = {"User-Agent": "MiLudoteca/1.0 (+https://ludoteca.app)"}
    if BGG_TOKEN:
        h["Authorization"] = f"Bearer {BGG_TOKEN}"
    return h


# ---------- Pydantic models ----------
class IdentifyRequest(BaseModel):
    imagen: str  # base64 data URL or raw base64


class IdentifyResponse(BaseModel):
    titulos: List[str]
    codigo_barras: Optional[str] = None


class BggSearchResult(BaseModel):
    bgg_id: str
    nombre: str
    año: Optional[int] = None
    thumbnail: Optional[str] = None


class BggDetails(BaseModel):
    bgg_id: str
    nombre: str
    descripcion: str = ""
    categoria: str = ""
    autor: str = ""
    editorial: str = ""
    año_publicacion: Optional[int] = None
    jugadores_minimo: Optional[int] = None
    jugadores_maximo: Optional[int] = None
    duracion_minima: Optional[int] = None
    duracion_maxima: Optional[int] = None
    complejidad: Optional[int] = None
    imagen: str = ""


# ---------- Helpers ----------
def _clean_base64(data: str) -> str:
    """Strip 'data:image/...;base64,' prefix if present."""
    if "," in data and data.strip().startswith("data:"):
        return data.split(",", 1)[1]
    return data


def _strip_html(text: str) -> str:
    """Decode BGG description (has &amp;#10; etc) and remove HTML."""
    if not text:
        return ""
    # BGG returns numeric entities like &#10;
    text = re.sub(r"&#10;", "\n", text)
    text = re.sub(r"&#13;", "", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&rsquo;|&lsquo;", "'", text)
    text = re.sub(r"&rdquo;|&ldquo;", '"', text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


# ---------- GPT-4o vision: identify game from photo ----------
async def identify_game_from_image(image_base64: str) -> IdentifyResponse:
    """Use GPT-4o vision to extract probable game titles (and barcode if visible)."""
    clean_b64 = _clean_base64(image_base64)

    system_msg = (
        "Eres un experto en juegos de mesa. Te darán una foto de la portada de un juego de mesa "
        "(o un código de barras). Tu tarea es identificar el TÍTULO del juego visible. "
        "Responde SIEMPRE en formato JSON puro, sin comentarios ni markdown, con esta estructura exacta:\n"
        '{"titulos": ["Título principal", "Variante alternativa 1", "Variante alternativa 2"], "codigo_barras": "1234567890123" o null}\n'
        "- 'titulos' debe contener entre 1 y 3 candidatos, ordenados de más probable a menos probable. "
        "Si la foto es claramente un juego conocido, pon el nombre OFICIAL en inglés en primer lugar "
        "(BoardGameGeek usa inglés). Si solo ves texto en español, déjalo en español. "
        "- 'codigo_barras' SOLO si ves un EAN/UPC visible y legible (13 o 12 dígitos). Si no, null. "
        "- Si no es un juego de mesa, devuelve {\"titulos\": [], \"codigo_barras\": null}."
    )

    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"identify-{uuid.uuid4()}",
        system_message=system_msg,
    ).with_model("openai", "gpt-4o")

    msg = UserMessage(
        text="Identifica este juego de mesa. Devuelve solo JSON.",
        file_contents=[ImageContent(image_base64=clean_b64)],
    )

    try:
        raw = await chat.send_message(msg)
    except Exception as e:
        logger.exception("GPT-4o identify failed: %s", e)
        raise

    logger.info("GPT-4o identify raw response: %s", raw)
    # Extract JSON from response
    text = raw.strip()
    # Remove markdown fences if present
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find first JSON object
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
        else:
            data = {"titulos": [], "codigo_barras": None}

    titulos = [t for t in (data.get("titulos") or []) if isinstance(t, str) and t.strip()]
    barcode = data.get("codigo_barras")
    if isinstance(barcode, str):
        barcode = barcode.strip() or None

    return IdentifyResponse(titulos=titulos[:3], codigo_barras=barcode)


# ---------- BGG: search ----------
async def bgg_search(query: str, limit: int = 5) -> List[BggSearchResult]:
    """Search BGG for board games by name. Returns top results with thumbnails."""
    if not query.strip():
        return []
    async with httpx.AsyncClient(timeout=20.0, headers=_bgg_headers()) as client:
        # Step 1: search
        r = await client.get(
            f"{BGG_BASE}/search",
            params={"query": query, "type": "boardgame"},
        )
        if r.status_code != 200:
            logger.warning("BGG search returned %s", r.status_code)
            return []
        root = ET.fromstring(r.text)
        items = root.findall("item")
        # Take first N
        first = items[:limit]
        if not first:
            return []
        ids = [it.attrib["id"] for it in first]

        # Step 2: batch thing fetch for thumbnails
        r2 = await client.get(f"{BGG_BASE}/thing", params={"id": ",".join(ids)})
        thumbs: Dict[str, str] = {}
        if r2.status_code == 200:
            root2 = ET.fromstring(r2.text)
            for it in root2.findall("item"):
                bid = it.attrib.get("id", "")
                thumb_el = it.find("thumbnail")
                if thumb_el is not None and thumb_el.text:
                    thumbs[bid] = thumb_el.text

    results: List[BggSearchResult] = []
    for it in first:
        bid = it.attrib["id"]
        name_el = it.find("name")
        year_el = it.find("yearpublished")
        nombre = name_el.attrib.get("value", "") if name_el is not None else ""
        año = None
        if year_el is not None:
            try:
                año = int(year_el.attrib.get("value", "0"))
                if año == 0:
                    año = None
            except ValueError:
                año = None
        results.append(BggSearchResult(
            bgg_id=bid,
            nombre=nombre,
            año=año,
            thumbnail=thumbs.get(bid),
        ))
    return results


# ---------- BGG: details + Spanish translation ----------
async def bgg_get_details(bgg_id: str, translate: bool = True) -> BggDetails:
    """Fetch full BGG details and translate name/description to Spanish via GPT-4o."""
    async with httpx.AsyncClient(timeout=30.0, headers=_bgg_headers()) as client:
        r = await client.get(f"{BGG_BASE}/thing", params={"id": bgg_id, "stats": 1})
        if r.status_code != 200:
            raise ValueError(f"BGG returned {r.status_code}")
        root = ET.fromstring(r.text)
        item = root.find("item")
        if item is None:
            raise ValueError("Juego no encontrado en BGG")

        # Primary name
        nombre_en = ""
        for n in item.findall("name"):
            if n.attrib.get("type") == "primary":
                nombre_en = n.attrib.get("value", "")
                break

        desc_raw = item.findtext("description") or ""
        desc_clean = _strip_html(desc_raw)

        año = None
        yel = item.find("yearpublished")
        if yel is not None:
            try:
                año = int(yel.attrib.get("value", "0")) or None
            except ValueError:
                pass

        min_p = None
        max_p = None
        mpel = item.find("minplayers")
        mxel = item.find("maxplayers")
        if mpel is not None:
            try:
                min_p = int(mpel.attrib.get("value", "0")) or None
            except ValueError:
                pass
        if mxel is not None:
            try:
                max_p = int(mxel.attrib.get("value", "0")) or None
            except ValueError:
                pass

        min_t = None
        max_t = None
        mintime = item.find("minplaytime")
        maxtime = item.find("maxplaytime")
        if mintime is not None:
            try:
                min_t = int(mintime.attrib.get("value", "0")) or None
            except ValueError:
                pass
        if maxtime is not None:
            try:
                max_t = int(maxtime.attrib.get("value", "0")) or None
            except ValueError:
                pass

        # Categoria: first boardgamecategory link
        categoria = ""
        autores = []
        editoriales = []
        for link in item.findall("link"):
            ltype = link.attrib.get("type", "")
            value = link.attrib.get("value", "")
            if ltype == "boardgamecategory" and not categoria:
                categoria = value
            elif ltype == "boardgamedesigner":
                autores.append(value)
            elif ltype == "boardgamepublisher":
                editoriales.append(value)

        autor = ", ".join(autores[:3])
        editorial = editoriales[0] if editoriales else ""

        # Complejidad: averageweight from statistics (1.0 - 5.0)
        complejidad = None
        stats = item.find("statistics")
        if stats is not None:
            ratings = stats.find("ratings")
            if ratings is not None:
                aw = ratings.find("averageweight")
                if aw is not None:
                    try:
                        w = float(aw.attrib.get("value", "0"))
                        if w > 0:
                            complejidad = max(1, min(5, round(w)))
                    except ValueError:
                        pass

        # Image
        img_el = item.find("image")
        imagen = img_el.text if img_el is not None and img_el.text else ""

    # Translate to Spanish
    nombre_es = nombre_en
    desc_es = desc_clean
    categoria_es = categoria
    if translate and EMERGENT_KEY and (desc_clean or categoria):
        try:
            nombre_es, desc_es, categoria_es = await _translate_to_spanish(
                nombre_en, desc_clean, categoria
            )
        except Exception as e:
            logger.warning("Translation failed, using English: %s", e)

    return BggDetails(
        bgg_id=bgg_id,
        nombre=nombre_es or nombre_en,
        descripcion=desc_es,
        categoria=categoria_es,
        autor=autor,
        editorial=editorial,
        año_publicacion=año,
        jugadores_minimo=min_p,
        jugadores_maximo=max_p,
        duracion_minima=min_t,
        duracion_maxima=max_t,
        complejidad=complejidad,
        imagen=imagen,
    )


async def _translate_to_spanish(name: str, desc: str, categoria: str):
    """Translate BGG fields to Spanish via GPT-4o."""
    system = (
        "Eres un traductor profesional especializado en juegos de mesa. "
        "Te darán el nombre, la descripción y la categoría de un juego en inglés. "
        "Devuelve SIEMPRE un JSON puro, sin markdown, con la estructura exacta:\n"
        '{"nombre": "...", "descripcion": "...", "categoria": "..."}\n'
        "Reglas:\n"
        "- Si el nombre del juego es el TÍTULO OFICIAL (ej. 'Catan', 'Wingspan'), MANTENLO TAL CUAL.\n"
        "- Traduce la descripción al español natural, fluido y completo.\n"
        "- Traduce la categoría al español (ej. 'Strategy Game' → 'Estrategia').\n"
        "- No añadas texto fuera del JSON."
    )
    payload = json.dumps({"nombre": name, "descripcion": desc, "categoria": categoria}, ensure_ascii=False)

    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"translate-{uuid.uuid4()}",
        system_message=system,
    ).with_model("openai", "gpt-4o")

    msg = UserMessage(text=f"Traduce al español este JSON:\n{payload}")
    raw = await chat.send_message(msg)
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            raise
        data = json.loads(m.group(0))
    return (
        data.get("nombre", name),
        data.get("descripcion", desc),
        data.get("categoria", categoria),
    )
