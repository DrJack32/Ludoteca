from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import base64
import re


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Pydantic Models
class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    descripcion: str = ""
    categoria: str = ""
    autor: str = ""
    editorial: str = ""
    año_publicacion: Optional[int] = None
    jugadores_minimo: Optional[int] = None
    jugadores_maximo: Optional[int] = None
    duracion_minima: Optional[int] = None  # en minutos
    duracion_maxima: Optional[int] = None  # en minutos
    complejidad: Optional[int] = None  # 1-5
    ubicacion_estanteria: str = ""
    ubicacion_balda: str = ""
    ubicacion_posicion: str = ""
    idioma: str = ""
    notas: str = ""
    imagen: str = ""  # base64 encoded image
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)

class GameCreate(BaseModel):
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
    ubicacion_estanteria: str = ""
    ubicacion_balda: str = ""
    ubicacion_posicion: str = ""
    idioma: str = ""
    notas: str = ""
    imagen: str = ""

class GameUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    autor: Optional[str] = None
    editorial: Optional[str] = None
    año_publicacion: Optional[int] = None
    jugadores_minimo: Optional[int] = None
    jugadores_maximo: Optional[int] = None
    duracion_minima: Optional[int] = None
    duracion_maxima: Optional[int] = None
    complejidad: Optional[int] = None
    ubicacion_estanteria: Optional[str] = None
    ubicacion_balda: Optional[str] = None
    ubicacion_posicion: Optional[str] = None
    idioma: Optional[str] = None
    notas: Optional[str] = None
    imagen: Optional[str] = None

class SearchFilters(BaseModel):
    nombre: Optional[str] = None
    autor: Optional[str] = None
    categoria: Optional[str] = None
    año_publicacion: Optional[int] = None
    jugadores_minimo: Optional[int] = None
    jugadores_maximo: Optional[int] = None
    complejidad: Optional[int] = None

class Statistics(BaseModel):
    total_juegos: int
    categorias_populares: Dict[str, int]
    autores_populares: Dict[str, int]
    editoriales_populares: Dict[str, int]
    años_populares: Dict[str, int]
    complejidad_promedio: float
    rango_jugadores: Dict[str, int]
    ubicaciones: Dict[str, int]

class AutocompleteResponse(BaseModel):
    categorias: List[str]
    autores: List[str]
    editoriales: List[str]
    idiomas: List[str]
    ubicaciones_estanteria: List[str]
    ubicaciones_balda: List[str]


# Routes
@api_router.get("/")
async def root():
    return {"message": "Ludoteca API - Sistema de Gestión de Juegos de Mesa"}

# Game CRUD operations
@api_router.post("/games", response_model=Game)
async def create_game(game_data: GameCreate):
    game_dict = game_data.dict()
    game_obj = Game(**game_dict)
    
    # Insert into database
    result = await db.games.insert_one(game_obj.dict())
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Error al crear el juego")
    
    return game_obj

@api_router.get("/games", response_model=List[Game])
async def get_games(
    limit: int = Query(100, le=1000),
    skip: int = Query(0, ge=0)
):
    games = await db.games.find().skip(skip).limit(limit).to_list(limit)
    return [Game(**game) for game in games]

@api_router.get("/games/{game_id}", response_model=Game)
async def get_game(game_id: str):
    game = await db.games.find_one({"id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return Game(**game)

@api_router.put("/games/{game_id}", response_model=Game)
async def update_game(game_id: str, game_update: GameUpdate):
    # Get existing game
    existing_game = await db.games.find_one({"id": game_id})
    if not existing_game:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    
    # Update fields
    update_data = {k: v for k, v in game_update.dict().items() if v is not None}
    update_data["fecha_actualizacion"] = datetime.utcnow()
    
    result = await db.games.update_one(
        {"id": game_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Error al actualizar el juego")
    
    # Return updated game
    updated_game = await db.games.find_one({"id": game_id})
    return Game(**updated_game)

@api_router.delete("/games/{game_id}")
async def delete_game(game_id: str):
    result = await db.games.delete_one({"id": game_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return {"message": "Juego eliminado correctamente"}

# Search functionality
@api_router.post("/games/search", response_model=List[Game])
async def search_games(filters: SearchFilters):
    query = {}
    
    if filters.nombre:
        query["nombre"] = {"$regex": filters.nombre, "$options": "i"}
    if filters.autor:
        query["autor"] = {"$regex": filters.autor, "$options": "i"}
    if filters.categoria:
        query["categoria"] = {"$regex": filters.categoria, "$options": "i"}
    if filters.año_publicacion:
        query["año_publicacion"] = filters.año_publicacion
    if filters.complejidad:
        query["complejidad"] = filters.complejidad
    
    # Handle player count search
    if filters.jugadores_minimo or filters.jugadores_maximo:
        player_query = {}
        if filters.jugadores_minimo:
            player_query["jugadores_maximo"] = {"$gte": filters.jugadores_minimo}
        if filters.jugadores_maximo:
            player_query["jugadores_minimo"] = {"$lte": filters.jugadores_maximo}
        query.update(player_query)
    
    games = await db.games.find(query).to_list(1000)
    return [Game(**game) for game in games]

# Statistics
@api_router.get("/statistics", response_model=Statistics)
async def get_statistics():
    # Total games
    total_games = await db.games.count_documents({})
    
    # Aggregation pipelines
    categoria_pipeline = [
        {"$match": {"categoria": {"$ne": ""}}},
        {"$group": {"_id": "$categoria", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    autor_pipeline = [
        {"$match": {"autor": {"$ne": ""}}},
        {"$group": {"_id": "$autor", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    editorial_pipeline = [
        {"$match": {"editorial": {"$ne": ""}}},
        {"$group": {"_id": "$editorial", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    año_pipeline = [
        {"$match": {"año_publicacion": {"$ne": None}}},
        {"$group": {"_id": "$año_publicacion", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    complejidad_pipeline = [
        {"$match": {"complejidad": {"$ne": None}}},
        {"$group": {"_id": None, "promedio": {"$avg": "$complejidad"}}}
    ]
    
    ubicacion_pipeline = [
        {"$match": {"ubicacion_estanteria": {"$ne": ""}}},
        {"$group": {"_id": "$ubicacion_estanteria", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    
    # Execute aggregations
    categorias_result = await db.games.aggregate(categoria_pipeline).to_list(10)
    autores_result = await db.games.aggregate(autor_pipeline).to_list(10)
    editorial_result = await db.games.aggregate(editorial_pipeline).to_list(10)
    años_result = await db.games.aggregate(año_pipeline).to_list(10)
    complejidad_result = await db.games.aggregate(complejidad_pipeline).to_list(1)
    ubicacion_result = await db.games.aggregate(ubicacion_pipeline).to_list(10)
    
    # Process results
    categorias_populares = {item["_id"]: item["count"] for item in categorias_result}
    autores_populares = {item["_id"]: item["count"] for item in autores_result}
    editoriales_populares = {item["_id"]: item["count"] for item in editorial_result}
    años_populares = {str(item["_id"]): item["count"] for item in años_result}
    complejidad_promedio = complejidad_result[0]["promedio"] if complejidad_result else 0.0
    ubicaciones = {item["_id"]: item["count"] for item in ubicacion_result}
    
    # Player range statistics
    rango_jugadores = {
        "1-2": 0,
        "3-4": 0,
        "5-8": 0,
        "9+": 0
    }
    
    games_cursor = db.games.find({"jugadores_maximo": {"$ne": None}})
    async for game in games_cursor:
        max_players = game.get("jugadores_maximo", 0)
        if max_players <= 2:
            rango_jugadores["1-2"] += 1
        elif max_players <= 4:
            rango_jugadores["3-4"] += 1
        elif max_players <= 8:
            rango_jugadores["5-8"] += 1
        else:
            rango_jugadores["9+"] += 1
    
    return Statistics(
        total_juegos=total_games,
        categorias_populares=categorias_populares,
        autores_populares=autores_populares,
        editoriales_populares=editoriales_populares,
        años_populares=años_populares,
        complejidad_promedio=complejidad_promedio,
        rango_jugadores=rango_jugadores,
        ubicaciones=ubicaciones
    )

# Autocomplete data
@api_router.get("/autocomplete", response_model=AutocompleteResponse)
async def get_autocomplete_data():
    # Get unique values for autocomplete
    categorias = await db.games.distinct("categoria", {"categoria": {"$ne": ""}})
    autores = await db.games.distinct("autor", {"autor": {"$ne": ""}})
    editoriales = await db.games.distinct("editorial", {"editorial": {"$ne": ""}})
    idiomas = await db.games.distinct("idioma", {"idioma": {"$ne": ""}})
    ubicaciones_estanteria = await db.games.distinct("ubicacion_estanteria", {"ubicacion_estanteria": {"$ne": ""}})
    ubicaciones_balda = await db.games.distinct("ubicacion_balda", {"ubicacion_balda": {"$ne": ""}})
    
    return AutocompleteResponse(
        categorias=sorted(categorias),
        autores=sorted(autores),
        editoriales=sorted(editoriales),
        idiomas=sorted(idiomas),
        ubicaciones_estanteria=sorted(ubicaciones_estanteria),
        ubicaciones_balda=sorted(ubicaciones_balda)
    )

# Location management
@api_router.get("/locations")
async def get_locations():
    pipeline = [
        {
            "$group": {
                "_id": {
                    "estanteria": "$ubicacion_estanteria",
                    "balda": "$ubicacion_balda"
                },
                "juegos": {"$push": {"nombre": "$nombre", "id": "$id"}},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.estanteria": 1, "_id.balda": 1}}
    ]
    
    locations = await db.games.aggregate(pipeline).to_list(1000)
    
    # Organize by shelf
    organized_locations = {}
    for location in locations:
        estanteria = location["_id"]["estanteria"] or "Sin Estantería"
        balda = location["_id"]["balda"] or "Sin Balda"
        
        if estanteria not in organized_locations:
            organized_locations[estanteria] = {}
        
        organized_locations[estanteria][balda] = {
            "count": location["count"],
            "juegos": location["juegos"]
        }
    
    return organized_locations

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
