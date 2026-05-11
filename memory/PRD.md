# Mi Ludoteca - PRD

## Original problem statement
Aplicación web/móvil (Android) para gestionar una ludoteca personal de 600+ juegos de mesa. Lenguaje del usuario: **español**.

## Core requirements
- 4 botones principales: Añadir juego, Buscar, Estadísticas, Ubicaciones.
- Campos del juego: Nombre, Descripción, Categoría, Autor, Editorial, Año, Min/Max jugadores, Min/Max duración, Complejidad (1-5), Ubicación (Estantería, Balda, Posición), Idioma, Notas, Imagen.
- Autocompletado de campos.
- Botón "volver al inicio" en todas las pantallas.

## Architecture
- **Frontend**: React (CRA) + Tailwind + Capacitor para Android. Archivo principal `/app/frontend/src/App.js` (monolítico, 1738 líneas).
- **Backend**: FastAPI + Motor (async MongoDB). Entry `/app/backend/server.py`, módulos auxiliares `/app/backend/game_identifier.py`.
- **DB**: MongoDB. Colección `games` (UUID como id).
- **Mobile**: Capacitor v7 (`/app/frontend/android/`), `MobileImageCapture.js`, `useCapacitor.js`.

## 3rd-party integrations
- **OpenAI GPT-4o (vision)** vía `emergentintegrations` con `EMERGENT_LLM_KEY`. Usado para identificar juegos en fotos y traducir descripciones al español.
- **BoardGameGeek XML API v2** con Bearer token (`BGG_API_TOKEN` en `.env`). Usado para enriquecer datos del juego.

## What's been implemented
### Original MVP (sesiones previas)
- CRUD completo de juegos, búsqueda, estadísticas, ubicaciones.
- Editar y eliminar juego.
- Subida de imágenes (base64).
- Capacitor configurado: proyecto Android generado en `frontend/android/`, plugins (Camera, Filesystem, Storage), CSS mobile.

### Esta sesión
1. **APK build pipeline (Feb 2026)**:
   - `/app/.github/workflows/build-apk.yml`: GitHub Actions que compila APK automáticamente en la nube al hacer push (Node 20 + JDK 21 + Android SDK).
   - `/app/ANDROID_SETUP.md`: guía en español con 3 caminos (GitHub Actions, Android Studio local, PWABuilder).

2. **Identificación con IA + BoardGameGeek (Feb 2026)**:
   - Backend `POST /api/identify-game`: recibe imagen base64, GPT-4o vision extrae hasta 3 candidatos de título.
   - Backend `GET /api/bgg/search?q=…&limit=5`: busca en BGG con header `Authorization: Bearer <token>`, devuelve top resultados con thumbnail.
   - Backend `GET /api/bgg/details/{bgg_id}?translate=true`: obtiene detalles completos de BGG + GPT-4o traduce nombre/descripción/categoría al español.
   - Frontend: al subir foto en AddGameScreen, modal automático muestra: "identifying → searching → choosing (top 5) → fetching → done". Selección rellena todos los campos. Búsqueda manual de fallback incluida.
   - Tests pytest `/app/backend/tests/test_ia_bgg.py` (19 casos, 100% pasando).

## Files of reference
- `/app/backend/server.py`: API routes
- `/app/backend/game_identifier.py`: lógica IA + BGG + traducción
- `/app/backend/.env`: `MONGO_URL`, `DB_NAME`, `EMERGENT_LLM_KEY`, `BGG_API_TOKEN`
- `/app/frontend/src/App.js`: SPA monolítica; `AddGameScreen` líneas ~178-784
- `/app/.github/workflows/build-apk.yml`: pipeline APK
- `/app/ANDROID_SETUP.md`: guía APK
- `/app/backend/tests/test_ia_bgg.py`: regresión backend

## Key API endpoints
- `GET/POST/PUT/DELETE /api/games`
- `POST /api/games/search`
- `GET /api/statistics`, `/api/autocomplete`, `/api/locations`
- `POST /api/identify-game` (nuevo)
- `GET /api/bgg/search` (nuevo)
- `GET /api/bgg/details/{bgg_id}` (nuevo)

## Backlog / Roadmap

### P1 - Mejoras de la IA
- Cachear traducciones de BGG en MongoDB (reduce latencia de 15-25s a <1s en juegos repetidos).
- Cuando el usuario selecciona un BGG match, también descargar la imagen oficial de BGG como fallback si no hay foto del usuario.

### P2 - UX
- Refactorizar `App.js` (1738 líneas) en componentes separados: `AddGameForm`, `EditGameForm`, `SearchScreen`, `StatsScreen`, `LocationsScreen`, `IAIdentifyModal`.
- Importación masiva CSV/Excel (para los 600+ juegos de golpe).
- Exportación de la colección a Excel/PDF.
- Modo oscuro.
- Sistema de préstamos (quién tiene qué juego).
- Valoraciones personales y notas extendidas por juego.

### P3 - Nice-to-have
- Lectura nativa de códigos de barras vía Capacitor (sin IA).
- Compartir colección con URL pública.
- Sincronización multi-dispositivo con cuentas.

## Test credentials
No auth configurada (app local de uso personal).

## Known issues
Ninguno crítico. Latencia de BGG details + traducción ~15-25s en primera consulta de un juego (P1: cachear).
