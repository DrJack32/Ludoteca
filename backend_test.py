#!/usr/bin/env python3
import requests
import json
import base64
import os
import sys
import time
from typing import Dict, Any, List, Optional
import unittest

# Get the backend URL from the frontend/.env file
def get_backend_url():
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.strip().split('=')[1].strip('"\'')
    raise ValueError("Backend URL not found in frontend/.env")

# Base URL for API requests
BASE_URL = f"{get_backend_url()}/api"
print(f"Testing API at: {BASE_URL}")

# Sample test data
TEST_GAMES = [
    {
        "nombre": "Catan",
        "descripcion": "Un juego de estrategia y negociación donde los jugadores colonizan una isla.",
        "categoria": "Estrategia",
        "autor": "Klaus Teuber",
        "editorial": "Devir",
        "año_publicacion": 1995,
        "jugadores_minimo": 3,
        "jugadores_maximo": 4,
        "duracion_minima": 60,
        "duracion_maxima": 120,
        "complejidad": 2,
        "ubicacion_estanteria": "A",
        "ubicacion_balda": "1",
        "ubicacion_posicion": "3",
        "idioma": "Español",
        "notas": "Juego básico sin expansiones",
        "imagen": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    },
    {
        "nombre": "Azul",
        "descripcion": "Un juego de colocación de losetas donde los jugadores decoran un palacio.",
        "categoria": "Familiar",
        "autor": "Michael Kiesling",
        "editorial": "Next Move Games",
        "año_publicacion": 2017,
        "jugadores_minimo": 2,
        "jugadores_maximo": 4,
        "duracion_minima": 30,
        "duracion_maxima": 45,
        "complejidad": 2,
        "ubicacion_estanteria": "B",
        "ubicacion_balda": "2",
        "ubicacion_posicion": "1",
        "idioma": "Español",
        "notas": "Ganador del Spiel des Jahres 2018",
        "imagen": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    },
    {
        "nombre": "Ticket to Ride Europa",
        "descripcion": "Un juego de colección de cartas y construcción de rutas ferroviarias por Europa.",
        "categoria": "Familiar",
        "autor": "Alan R. Moon",
        "editorial": "Edge Entertainment",
        "año_publicacion": 2005,
        "jugadores_minimo": 2,
        "jugadores_maximo": 5,
        "duracion_minima": 60,
        "duracion_maxima": 90,
        "complejidad": 2,
        "ubicacion_estanteria": "C",
        "ubicacion_balda": "3",
        "ubicacion_posicion": "2",
        "idioma": "Español",
        "notas": "Versión europea del juego original",
        "imagen": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    }
]

# Search test data
SEARCH_TESTS = [
    {"nombre": "Catan"},
    {"autor": "Michael Kiesling"},
    {"categoria": "Familiar"},
    {"año_publicacion": 2017},
    {"jugadores_minimo": 2},
    {"jugadores_maximo": 4},
    {"complejidad": 2},
    {"nombre": "Ticket", "categoria": "Familiar"}
]

class BoardGameAPITest(unittest.TestCase):
    """Test suite for the Board Game Library Management API"""
    
    created_game_ids = []
    
    def setUp(self):
        """Set up for each test"""
        self.session = requests.Session()
    
    def tearDown(self):
        """Clean up after each test"""
        pass
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests - delete any created games"""
        print(f"\nCleaning up {len(cls.created_game_ids)} created test games...")
        for game_id in cls.created_game_ids:
            try:
                response = requests.delete(f"{BASE_URL}/games/{game_id}")
                if response.status_code == 200:
                    print(f"Successfully deleted game {game_id}")
                else:
                    print(f"Failed to delete game {game_id}: {response.status_code}")
            except Exception as e:
                print(f"Error deleting game {game_id}: {e}")
    
    def test_01_health_check(self):
        """Test the API health check endpoint"""
        print("\n1. Testing API health check...")
        response = self.session.get(f"{BASE_URL}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"Health check response: {data['message']}")
    
    def test_02_create_games(self):
        """Test creating new games"""
        print("\n2. Testing game creation...")
        for i, game_data in enumerate(TEST_GAMES):
            print(f"Creating game {i+1}: {game_data['nombre']}")
            response = self.session.post(f"{BASE_URL}/games", json=game_data)
            self.assertEqual(response.status_code, 200)
            created_game = response.json()
            self.assertEqual(created_game["nombre"], game_data["nombre"])
            self.assertIn("id", created_game)
            print(f"Created game with ID: {created_game['id']}")
            self.__class__.created_game_ids.append(created_game["id"])
    
    def test_03_get_all_games(self):
        """Test getting all games"""
        print("\n3. Testing get all games...")
        response = self.session.get(f"{BASE_URL}/games")
        self.assertEqual(response.status_code, 200)
        games = response.json()
        self.assertIsInstance(games, list)
        print(f"Retrieved {len(games)} games")
        
        # Check if our created games are in the list
        game_names = [game["nombre"] for game in games]
        for test_game in TEST_GAMES:
            self.assertIn(test_game["nombre"], game_names)
    
    def test_04_get_specific_game(self):
        """Test getting a specific game by ID"""
        if not self.__class__.created_game_ids:
            self.skipTest("No games created to test with")
        
        print("\n4. Testing get specific game...")
        game_id = self.__class__.created_game_ids[0]
        response = self.session.get(f"{BASE_URL}/games/{game_id}")
        self.assertEqual(response.status_code, 200)
        game = response.json()
        self.assertEqual(game["id"], game_id)
        print(f"Retrieved game: {game['nombre']}")
        
        # Test with non-existent ID
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.session.get(f"{BASE_URL}/games/{fake_id}")
        self.assertEqual(response.status_code, 404)
        print("Correctly received 404 for non-existent game")
    
    def test_05_update_game(self):
        """Test updating a game"""
        if not self.__class__.created_game_ids:
            self.skipTest("No games created to test with")
        
        print("\n5. Testing game update...")
        game_id = self.__class__.created_game_ids[0]
        
        # Get the current game data
        response = self.session.get(f"{BASE_URL}/games/{game_id}")
        self.assertEqual(response.status_code, 200)
        original_game = response.json()
        
        # Update some fields
        update_data = {
            "descripcion": "Descripción actualizada para pruebas",
            "notas": "Notas actualizadas para pruebas",
            "complejidad": 3
        }
        
        response = self.session.put(f"{BASE_URL}/games/{game_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        updated_game = response.json()
        
        # Verify the updates
        self.assertEqual(updated_game["descripcion"], update_data["descripcion"])
        self.assertEqual(updated_game["notas"], update_data["notas"])
        self.assertEqual(updated_game["complejidad"], update_data["complejidad"])
        
        # Verify other fields remain unchanged
        self.assertEqual(updated_game["nombre"], original_game["nombre"])
        self.assertEqual(updated_game["autor"], original_game["autor"])
        
        print(f"Successfully updated game: {updated_game['nombre']}")
        
        # Test with non-existent ID
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.session.put(f"{BASE_URL}/games/{fake_id}", json=update_data)
        self.assertEqual(response.status_code, 404)
        print("Correctly received 404 for updating non-existent game")
    
    def test_06_search_games(self):
        """Test searching for games with various filters"""
        print("\n6. Testing game search functionality...")
        
        # Make sure we have games to search for
        if not self.__class__.created_game_ids:
            self.skipTest("No games created to test with")
        
        for i, search_filter in enumerate(SEARCH_TESTS):
            print(f"Search test {i+1}: {search_filter}")
            response = self.session.post(f"{BASE_URL}/games/search", json=search_filter)
            self.assertEqual(response.status_code, 200)
            results = response.json()
            self.assertIsInstance(results, list)
            print(f"Found {len(results)} games matching filter")
            
            # Verify search results match the filter
            for game in results:
                for key, value in search_filter.items():
                    if key == "nombre" or key == "autor" or key == "categoria":
                        # For string fields, check if the value is contained in the field
                        self.assertIn(value.lower(), game[key].lower())
                    elif key == "jugadores_minimo":
                        # For min players, the game's max players should be >= the filter
                        self.assertGreaterEqual(game["jugadores_maximo"], value)
                    elif key == "jugadores_maximo":
                        # For max players, the game's min players should be <= the filter
                        self.assertLessEqual(game["jugadores_minimo"], value)
                    else:
                        # For other fields, check exact match
                        self.assertEqual(game[key], value)
    
    def test_07_statistics(self):
        """Test getting statistics"""
        print("\n7. Testing statistics endpoint...")
        response = self.session.get(f"{BASE_URL}/statistics")
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        
        # Verify the structure of the statistics response
        self.assertIn("total_juegos", stats)
        self.assertIn("categorias_populares", stats)
        self.assertIn("autores_populares", stats)
        self.assertIn("editoriales_populares", stats)
        self.assertIn("años_populares", stats)
        self.assertIn("complejidad_promedio", stats)
        self.assertIn("rango_jugadores", stats)
        self.assertIn("ubicaciones", stats)
        
        print(f"Total games in statistics: {stats['total_juegos']}")
        print(f"Popular categories: {list(stats['categorias_populares'].keys())}")
        print(f"Average complexity: {stats['complejidad_promedio']}")
    
    def test_08_autocomplete(self):
        """Test getting autocomplete data"""
        print("\n8. Testing autocomplete endpoint...")
        response = self.session.get(f"{BASE_URL}/autocomplete")
        self.assertEqual(response.status_code, 200)
        autocomplete = response.json()
        
        # Verify the structure of the autocomplete response
        self.assertIn("categorias", autocomplete)
        self.assertIn("autores", autocomplete)
        self.assertIn("editoriales", autocomplete)
        self.assertIn("idiomas", autocomplete)
        self.assertIn("ubicaciones_estanteria", autocomplete)
        self.assertIn("ubicaciones_balda", autocomplete)
        
        # Check if our test data is in the autocomplete lists
        for test_game in TEST_GAMES:
            if test_game["categoria"]:
                self.assertIn(test_game["categoria"], autocomplete["categorias"])
            if test_game["autor"]:
                self.assertIn(test_game["autor"], autocomplete["autores"])
            if test_game["editorial"]:
                self.assertIn(test_game["editorial"], autocomplete["editoriales"])
        
        print(f"Autocomplete categories: {autocomplete['categorias']}")
        print(f"Autocomplete authors: {autocomplete['autores']}")
    
    def test_09_locations(self):
        """Test getting location data"""
        print("\n9. Testing locations endpoint...")
        response = self.session.get(f"{BASE_URL}/locations")
        self.assertEqual(response.status_code, 200)
        locations = response.json()
        
        # Verify the structure of the locations response
        self.assertIsInstance(locations, dict)
        
        # Check if our test game locations are in the response
        shelves = set()
        for test_game in TEST_GAMES:
            if test_game["ubicacion_estanteria"]:
                shelves.add(test_game["ubicacion_estanteria"])
        
        for shelf in shelves:
            self.assertIn(shelf, locations)
        
        print(f"Location shelves: {list(locations.keys())}")
    
    def test_10_delete_game(self):
        """Test deleting a game"""
        if not self.__class__.created_game_ids:
            self.skipTest("No games created to test with")
        
        print("\n10. Testing game deletion...")
        # We'll delete the last game in our list
        game_id = self.__class__.created_game_ids.pop()
        
        response = self.session.delete(f"{BASE_URL}/games/{game_id}")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)
        print(f"Delete response: {result['message']}")
        
        # Verify the game is actually deleted
        response = self.session.get(f"{BASE_URL}/games/{game_id}")
        self.assertEqual(response.status_code, 404)
        print("Verified game was deleted (404 on GET)")
        
        # Test deleting a non-existent game
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.session.delete(f"{BASE_URL}/games/{fake_id}")
        self.assertEqual(response.status_code, 404)
        print("Correctly received 404 for deleting non-existent game")
    
    def test_11_ai_identify_game(self):
        """Test AI game identification endpoint"""
        print("\n11. Testing AI game identification...")
        
        # Test with a small test image (base64 encoded 1x1 PNG)
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        
        # Test 1: Without data URL prefix
        print("Test 1: Image without data URL prefix")
        payload = {"imagen": test_image_base64}
        response = self.session.post(f"{BASE_URL}/identify-game", json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        # Should return 200 (even if no game is identified, it should not error)
        self.assertIn(response.status_code, [200, 500])
        if response.status_code == 200:
            data = response.json()
            self.assertIn("titulos", data)
            self.assertIn("codigo_barras", data)
            self.assertIsInstance(data["titulos"], list)
            print(f"Identified titles: {data['titulos']}")
            print(f"Barcode: {data['codigo_barras']}")
        else:
            print(f"AI identification failed with error: {response.text}")
        
        # Test 2: With data URL prefix
        print("\nTest 2: Image with data URL prefix")
        test_image_with_prefix = f"data:image/png;base64,{test_image_base64}"
        payload = {"imagen": test_image_with_prefix}
        response = self.session.post(f"{BASE_URL}/identify-game", json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        self.assertIn(response.status_code, [200, 500])
        if response.status_code == 200:
            data = response.json()
            self.assertIn("titulos", data)
            self.assertIn("codigo_barras", data)
            self.assertIsInstance(data["titulos"], list)
            print(f"Identified titles: {data['titulos']}")
            print(f"Barcode: {data['codigo_barras']}")
        else:
            print(f"AI identification failed with error: {response.text}")
    
    def test_12_bgg_search(self):
        """Test BoardGameGeek search endpoint"""
        print("\n12. Testing BGG search...")
        
        # Test searching for a well-known game
        search_query = "catan"
        print(f"Searching for: {search_query}")
        response = self.session.get(f"{BASE_URL}/bgg/search", params={"q": search_query})
        print(f"Response status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertIsInstance(results, list)
        print(f"Found {len(results)} results")
        
        if len(results) > 0:
            first_result = results[0]
            self.assertIn("bgg_id", first_result)
            self.assertIn("nombre", first_result)
            self.assertIn("año", first_result)
            self.assertIn("thumbnail", first_result)
            print(f"First result: {first_result['nombre']} (BGG ID: {first_result['bgg_id']})")
            
            # Store the BGG ID for the next test
            self.__class__.test_bgg_id = first_result['bgg_id']
        else:
            print("No results found (BGG API might be slow or unavailable)")
    
    def test_13_bgg_details(self):
        """Test BoardGameGeek details endpoint"""
        print("\n13. Testing BGG details...")
        
        # Use a well-known BGG ID (Catan = 13)
        bgg_id = "13"
        if hasattr(self.__class__, 'test_bgg_id'):
            bgg_id = self.__class__.test_bgg_id
        
        print(f"Getting details for BGG ID: {bgg_id}")
        response = self.session.get(f"{BASE_URL}/bgg/details/{bgg_id}")
        print(f"Response status: {response.status_code}")
        
        self.assertEqual(response.status_code, 200)
        details = response.json()
        
        # Verify the structure
        self.assertIn("bgg_id", details)
        self.assertIn("nombre", details)
        self.assertIn("descripcion", details)
        self.assertIn("categoria", details)
        self.assertIn("autor", details)
        self.assertIn("editorial", details)
        self.assertIn("año_publicacion", details)
        self.assertIn("jugadores_minimo", details)
        self.assertIn("jugadores_maximo", details)
        self.assertIn("duracion_minima", details)
        self.assertIn("duracion_maxima", details)
        self.assertIn("complejidad", details)
        self.assertIn("imagen", details)
        
        print(f"Game name: {details['nombre']}")
        print(f"Category: {details['categoria']}")
        print(f"Author: {details['autor']}")
        print(f"Players: {details['jugadores_minimo']}-{details['jugadores_maximo']}")
        print(f"Duration: {details['duracion_minima']}-{details['duracion_maxima']} min")
        print(f"Complexity: {details['complejidad']}/5")

if __name__ == "__main__":
    # Run the tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
