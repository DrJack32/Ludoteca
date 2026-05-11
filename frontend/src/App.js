import React, { useState, useEffect } from "react";
import "./App.css";
import "./mobile.css";
import axios from "axios";
import MobileImageCapture from "./components/MobileImageCapture";
import { useCapacitor } from "./hooks/useCapacitor";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('home');
  const [games, setGames] = useState([]);
  const [autocompleteData, setAutocompleteData] = useState({});
  const [statistics, setStatistics] = useState(null);
  const [locations, setLocations] = useState({});
  const [editingGame, setEditingGame] = useState(null);
  const { isNative, saveLocalData, getLocalData, shareGame } = useCapacitor();

  // Fetch initial data
  useEffect(() => {
    fetchGames();
    fetchAutocompleteData();
    
    // Load cached data if available (for offline support)
    if (isNative) {
      loadCachedData();
    }
  }, [isNative]);

  const loadCachedData = async () => {
    try {
      const cachedGames = await getLocalData('games');
      const cachedAutocomplete = await getLocalData('autocomplete');
      
      if (cachedGames) {
        setGames(cachedGames);
      }
      if (cachedAutocomplete) {
        setAutocompleteData(cachedAutocomplete);
      }
    } catch (error) {
      console.error('Error loading cached data:', error);
    }
  };

  const fetchGames = async () => {
    try {
      const response = await axios.get(`${API}/games`);
      setGames(response.data);
      
      // Cache data for offline use
      if (isNative) {
        await saveLocalData('games', response.data);
      }
    } catch (error) {
      console.error('Error fetching games:', error);
      
      // Try to load from cache if network fails
      if (isNative) {
        const cachedGames = await getLocalData('games');
        if (cachedGames) {
          setGames(cachedGames);
        }
      }
    }
  };

  const fetchAutocompleteData = async () => {
    try {
      const response = await axios.get(`${API}/autocomplete`);
      setAutocompleteData(response.data);
      
      // Cache data for offline use
      if (isNative) {
        await saveLocalData('autocomplete', response.data);
      }
    } catch (error) {
      console.error('Error fetching autocomplete data:', error);
      
      // Try to load from cache if network fails
      if (isNative) {
        const cachedAutocomplete = await getLocalData('autocomplete');
        if (cachedAutocomplete) {
          setAutocompleteData(cachedAutocomplete);
        }
      }
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API}/statistics`);
      setStatistics(response.data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`);
      setLocations(response.data);
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  // Home Screen
  const HomeScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 safe-area-top">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-purple-800 mb-4">
            🎲 Mi Ludoteca
          </h1>
          <p className="text-lg md:text-xl text-purple-600 mb-2">
            Sistema de Gestión de Juegos de Mesa
          </p>
          <p className="text-base md:text-lg text-purple-500">
            {games.length} juegos en tu colección
          </p>
          {isNative && (
            <p className="text-sm text-green-600 mt-2">
              📱 Versión Móvil - Funciona sin conexión
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto">
          <button
            onClick={() => setCurrentView('add')}
            className="nav-button bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700"
          >
            <div className="text-4xl mb-3">➕</div>
            <h3 className="text-xl font-semibold mb-2">Añadir Juego</h3>
            <p className="text-sm opacity-90">Agregar un nuevo juego a tu colección</p>
          </button>

          <button
            onClick={() => setCurrentView('search')}
            className="nav-button bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700"
          >
            <div className="text-4xl mb-3">🔍</div>
            <h3 className="text-xl font-semibold mb-2">Buscar</h3>
            <p className="text-sm opacity-90">Encontrar juegos por diversos criterios</p>
          </button>

          <button
            onClick={() => {
              setCurrentView('statistics');
              fetchStatistics();
            }}
            className="nav-button bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700"
          >
            <div className="text-4xl mb-3">📊</div>
            <h3 className="text-xl font-semibold mb-2">Estadísticas</h3>
            <p className="text-sm opacity-90">Ver análisis de tu colección</p>
          </button>

          <button
            onClick={() => {
              setCurrentView('locations');
              fetchLocations();
            }}
            className="nav-button bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700"
          >
            <div className="text-4xl mb-3">📍</div>
            <h3 className="text-xl font-semibold mb-2">Ubicaciones</h3>
            <p className="text-sm opacity-90">Gestionar ubicaciones físicas</p>
          </button>
        </div>
      </div>
    </div>
  );

  // Add Game Screen
  const AddGameScreen = () => {
    const [formData, setFormData] = useState({
      nombre: '',
      descripcion: '',
      categoria: '',
      autor: '',
      editorial: '',
      año_publicacion: '',
      jugadores_minimo: '',
      jugadores_maximo: '',
      duracion_minima: '',
      duracion_maxima: '',
      complejidad: '',
      ubicacion_estanteria: '',
      ubicacion_balda: '',
      ubicacion_posicion: '',
      idioma: '',
      notas: '',
      imagen: ''
    });

    // ---------- IA + BGG state ----------
    const [iaStatus, setIaStatus] = useState('idle'); // idle | identifying | searching | choosing | fetching | done | error
    const [iaCandidates, setIaCandidates] = useState([]);
    const [iaError, setIaError] = useState('');
    const [iaSearchedTitle, setIaSearchedTitle] = useState('');
    const [iaManualQuery, setIaManualQuery] = useState('');

    const runAIFlow = async (imageBase64) => {
      setIaError('');
      setIaCandidates([]);
      setIaStatus('identifying');
      try {
        // 1) Ask GPT-4o to identify the game
        const idRes = await axios.post(`${API}/identify-game`, { imagen: imageBase64 });
        const titulos = idRes.data.titulos || [];
        if (titulos.length === 0) {
          setIaStatus('error');
          setIaError('La IA no reconoció ningún juego en la foto. Puedes buscar a mano abajo.');
          return;
        }
        // 2) Search BGG using the top guess
        setIaStatus('searching');
        const topTitle = titulos[0];
        setIaSearchedTitle(topTitle);
        setIaManualQuery(topTitle);
        const bggRes = await axios.get(`${API}/bgg/search`, {
          params: { q: topTitle, limit: 5 },
        });
        if (!bggRes.data || bggRes.data.length === 0) {
          // Try second candidate if available
          if (titulos[1]) {
            const bggRes2 = await axios.get(`${API}/bgg/search`, {
              params: { q: titulos[1], limit: 5 },
            });
            if (bggRes2.data && bggRes2.data.length > 0) {
              setIaSearchedTitle(titulos[1]);
              setIaManualQuery(titulos[1]);
              setIaCandidates(bggRes2.data);
              setIaStatus('choosing');
              return;
            }
          }
          setIaStatus('error');
          setIaError(`No se encontró "${topTitle}" en BGG. Prueba a buscar manualmente.`);
          return;
        }
        setIaCandidates(bggRes.data);
        setIaStatus('choosing');
      } catch (err) {
        console.error('AI flow error:', err);
        setIaStatus('error');
        setIaError(err.response?.data?.detail || 'Error al identificar el juego con IA.');
      }
    };

    const runManualBggSearch = async () => {
      if (!iaManualQuery.trim()) return;
      setIaError('');
      setIaStatus('searching');
      try {
        const bggRes = await axios.get(`${API}/bgg/search`, {
          params: { q: iaManualQuery.trim(), limit: 5 },
        });
        if (!bggRes.data || bggRes.data.length === 0) {
          setIaStatus('error');
          setIaError(`Sin resultados en BGG para "${iaManualQuery}".`);
          return;
        }
        setIaCandidates(bggRes.data);
        setIaSearchedTitle(iaManualQuery);
        setIaStatus('choosing');
      } catch (err) {
        setIaStatus('error');
        setIaError('Error al buscar en BGG.');
      }
    };

    const selectBggCandidate = async (bggId) => {
      setIaStatus('fetching');
      setIaError('');
      try {
        const det = await axios.get(`${API}/bgg/details/${bggId}`);
        const d = det.data;
        setFormData(prev => ({
          ...prev,
          nombre: d.nombre || prev.nombre,
          descripcion: d.descripcion || prev.descripcion,
          categoria: d.categoria || prev.categoria,
          autor: d.autor || prev.autor,
          editorial: d.editorial || prev.editorial,
          año_publicacion: d.año_publicacion ? String(d.año_publicacion) : prev.año_publicacion,
          jugadores_minimo: d.jugadores_minimo ? String(d.jugadores_minimo) : prev.jugadores_minimo,
          jugadores_maximo: d.jugadores_maximo ? String(d.jugadores_maximo) : prev.jugadores_maximo,
          duracion_minima: d.duracion_minima ? String(d.duracion_minima) : prev.duracion_minima,
          duracion_maxima: d.duracion_maxima ? String(d.duracion_maxima) : prev.duracion_maxima,
          complejidad: d.complejidad ? String(d.complejidad) : prev.complejidad,
        }));
        setIaStatus('done');
        setIaCandidates([]);
      } catch (err) {
        setIaStatus('error');
        setIaError('Error al obtener los detalles del juego desde BGG.');
      }
    };

    const cancelIa = () => {
      setIaStatus('idle');
      setIaCandidates([]);
      setIaError('');
    };

    const handleInputChange = (e) => {
      const { name, value } = e.target;
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    };

    const handleImageUpload = (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const dataUrl = event.target.result;
          setFormData(prev => ({
            ...prev,
            imagen: dataUrl
          }));
          // Auto-trigger AI identification
          runAIFlow(dataUrl);
        };
        reader.readAsDataURL(file);
      }
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const submitData = {
          ...formData,
          año_publicacion: formData.año_publicacion ? parseInt(formData.año_publicacion) : null,
          jugadores_minimo: formData.jugadores_minimo ? parseInt(formData.jugadores_minimo) : null,
          jugadores_maximo: formData.jugadores_maximo ? parseInt(formData.jugadores_maximo) : null,
          duracion_minima: formData.duracion_minima ? parseInt(formData.duracion_minima) : null,
          duracion_maxima: formData.duracion_maxima ? parseInt(formData.duracion_maxima) : null,
          complejidad: formData.complejidad ? parseInt(formData.complejidad) : null,
        };

        await axios.post(`${API}/games`, submitData);
        alert('¡Juego añadido correctamente!');
        fetchGames();
        fetchAutocompleteData();
        setCurrentView('home');
      } catch (error) {
        console.error('Error adding game:', error);
        alert('Error al añadir el juego');
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
        {/* ---------- IA / BGG modal ---------- */}
        {iaStatus !== 'idle' && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="ia-modal">
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold text-purple-800">
                  🤖 Identificación con IA
                </h3>
                <button
                  onClick={cancelIa}
                  className="text-gray-500 hover:text-gray-800 text-2xl leading-none"
                  data-testid="ia-modal-close"
                >×</button>
              </div>

              {iaStatus === 'identifying' && (
                <div className="text-center py-8" data-testid="ia-status-identifying">
                  <div className="inline-block w-12 h-12 border-4 border-purple-300 border-t-purple-600 rounded-full animate-spin mb-4"></div>
                  <p className="text-purple-700 font-medium">Analizando la foto con GPT-4o…</p>
                </div>
              )}

              {iaStatus === 'searching' && (
                <div className="text-center py-8" data-testid="ia-status-searching">
                  <div className="inline-block w-12 h-12 border-4 border-blue-300 border-t-blue-600 rounded-full animate-spin mb-4"></div>
                  <p className="text-blue-700 font-medium">Buscando en BoardGameGeek…</p>
                  {iaSearchedTitle && (
                    <p className="text-sm text-gray-500 mt-1">Consulta: "{iaSearchedTitle}"</p>
                  )}
                </div>
              )}

              {iaStatus === 'fetching' && (
                <div className="text-center py-8" data-testid="ia-status-fetching">
                  <div className="inline-block w-12 h-12 border-4 border-green-300 border-t-green-600 rounded-full animate-spin mb-4"></div>
                  <p className="text-green-700 font-medium">Obteniendo detalles y traduciendo al español…</p>
                </div>
              )}

              {iaStatus === 'choosing' && (
                <div data-testid="ia-status-choosing">
                  <p className="text-gray-700 mb-4">
                    Resultados en BGG para <span className="font-semibold">"{iaSearchedTitle}"</span>. Elige el correcto:
                  </p>
                  <div className="space-y-3">
                    {iaCandidates.map((c) => (
                      <button
                        key={c.bgg_id}
                        onClick={() => selectBggCandidate(c.bgg_id)}
                        className="w-full flex items-center gap-4 p-3 border-2 border-purple-100 hover:border-purple-500 hover:bg-purple-50 rounded-xl transition-all text-left"
                        data-testid={`ia-candidate-${c.bgg_id}`}
                      >
                        {c.thumbnail ? (
                          <img src={c.thumbnail} alt={c.nombre} className="w-16 h-16 object-cover rounded-lg flex-shrink-0" />
                        ) : (
                          <div className="w-16 h-16 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">🎲</div>
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-purple-900 truncate">{c.nombre}</div>
                          {c.año && <div className="text-sm text-gray-500">{c.año}</div>}
                          <div className="text-xs text-purple-500">BGG ID: {c.bgg_id}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <p className="text-sm text-gray-600 mb-2">¿Ninguno coincide? Busca a mano:</p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={iaManualQuery}
                        onChange={(e) => setIaManualQuery(e.target.value)}
                        className="form-input flex-1"
                        placeholder="Nombre del juego…"
                        data-testid="ia-manual-search-input"
                      />
                      <button onClick={runManualBggSearch} className="btn-primary whitespace-nowrap" data-testid="ia-manual-search-btn">
                        🔍 Buscar
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {iaStatus === 'error' && (
                <div data-testid="ia-status-error">
                  <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
                    <p className="text-red-800 font-medium">⚠️ {iaError}</p>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={iaManualQuery}
                      onChange={(e) => setIaManualQuery(e.target.value)}
                      className="form-input flex-1"
                      placeholder="Buscar manualmente en BGG…"
                      data-testid="ia-manual-search-input-err"
                    />
                    <button onClick={runManualBggSearch} className="btn-primary whitespace-nowrap" data-testid="ia-manual-search-btn-err">
                      🔍 Buscar
                    </button>
                  </div>
                  <button onClick={cancelIa} className="btn-secondary w-full mt-3" data-testid="ia-skip-btn">
                    Continuar rellenando manualmente
                  </button>
                </div>
              )}

              {iaStatus === 'done' && (
                <div className="text-center py-6" data-testid="ia-status-done">
                  <div className="text-5xl mb-3">✅</div>
                  <p className="text-green-700 font-semibold mb-4">¡Datos rellenados automáticamente!</p>
                  <p className="text-sm text-gray-600 mb-4">Revisa los campos y completa la ubicación.</p>
                  <button onClick={cancelIa} className="btn-primary" data-testid="ia-done-btn">
                    Perfecto, continuar
                  </button>
                </div>
              )}
            </div>
          </div>
        )}


        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-4xl font-bold text-purple-800">➕ Añadir Juego</h1>
              <button
                onClick={() => setCurrentView('home')}
                className="back-button"
              >
                ← Volver al Inicio
              </button>
            </div>

            <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-8">
              {/* Información Básica */}
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-purple-700 mb-6 border-b border-purple-200 pb-2">
                  📋 Información Básica
                </h2>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="form-label">Nombre del Juego *</label>
                    <input
                      type="text"
                      name="nombre"
                      value={formData.nombre}
                      onChange={handleInputChange}
                      className="form-input"
                      required
                    />
                  </div>
                  <div>
                    <label className="form-label">Categoría</label>
                    <input
                      type="text"
                      name="categoria"
                      value={formData.categoria}
                      onChange={handleInputChange}
                      className="form-input"
                      list="categorias"
                    />
                    <datalist id="categorias">
                      {autocompleteData.categorias?.map(cat => (
                        <option key={cat} value={cat} />
                      ))}
                    </datalist>
                  </div>
                  <div className="md:col-span-2">
                    <label className="form-label">Descripción</label>
                    <textarea
                      name="descripcion"
                      value={formData.descripcion}
                      onChange={handleInputChange}
                      className="form-input"
                      rows="3"
                    />
                  </div>
                  <div>
                    <label className="form-label">Autor</label>
                    <input
                      type="text"
                      name="autor"
                      value={formData.autor}
                      onChange={handleInputChange}
                      className="form-input"
                      list="autores"
                    />
                    <datalist id="autores">
                      {autocompleteData.autores?.map(autor => (
                        <option key={autor} value={autor} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Editorial</label>
                    <input
                      type="text"
                      name="editorial"
                      value={formData.editorial}
                      onChange={handleInputChange}
                      className="form-input"
                      list="editoriales"
                    />
                    <datalist id="editoriales">
                      {autocompleteData.editoriales?.map(editorial => (
                        <option key={editorial} value={editorial} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Año de Publicación</label>
                    <input
                      type="number"
                      name="año_publicacion"
                      value={formData.año_publicacion}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1900"
                      max="2030"
                    />
                  </div>
                  <div>
                    <label className="form-label">Idioma</label>
                    <input
                      type="text"
                      name="idioma"
                      value={formData.idioma}
                      onChange={handleInputChange}
                      className="form-input"
                      list="idiomas"
                    />
                    <datalist id="idiomas">
                      {autocompleteData.idiomas?.map(idioma => (
                        <option key={idioma} value={idioma} />
                      ))}
                    </datalist>
                  </div>
                </div>
              </div>

              {/* Detalles del Juego */}
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-purple-700 mb-6 border-b border-purple-200 pb-2">
                  🎮 Detalles del Juego
                </h2>
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <label className="form-label">Jugadores Mínimo</label>
                    <input
                      type="number"
                      name="jugadores_minimo"
                      value={formData.jugadores_minimo}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="form-label">Jugadores Máximo</label>
                    <input
                      type="number"
                      name="jugadores_maximo"
                      value={formData.jugadores_maximo}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="form-label">Complejidad (1-5)</label>
                    <select
                      name="complejidad"
                      value={formData.complejidad}
                      onChange={handleInputChange}
                      className="form-input"
                    >
                      <option value="">Seleccionar</option>
                      <option value="1">1 - Muy Fácil</option>
                      <option value="2">2 - Fácil</option>
                      <option value="3">3 - Medio</option>
                      <option value="4">4 - Difícil</option>
                      <option value="5">5 - Muy Difícil</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Duración Mínima (min)</label>
                    <input
                      type="number"
                      name="duracion_minima"
                      value={formData.duracion_minima}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="form-label">Duración Máxima (min)</label>
                    <input
                      type="number"
                      name="duracion_maxima"
                      value={formData.duracion_maxima}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1"
                    />
                  </div>
                </div>
              </div>

              {/* Ubicación */}
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-purple-700 mb-6 border-b border-purple-200 pb-2">
                  📍 Ubicación
                </h2>
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <label className="form-label">Estantería</label>
                    <input
                      type="text"
                      name="ubicacion_estanteria"
                      value={formData.ubicacion_estanteria}
                      onChange={handleInputChange}
                      className="form-input"
                      list="estanterias"
                    />
                    <datalist id="estanterias">
                      {autocompleteData.ubicaciones_estanteria?.map(est => (
                        <option key={est} value={est} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Balda</label>
                    <input
                      type="text"
                      name="ubicacion_balda"
                      value={formData.ubicacion_balda}
                      onChange={handleInputChange}
                      className="form-input"
                      list="baldas"
                    />
                    <datalist id="baldas">
                      {autocompleteData.ubicaciones_balda?.map(balda => (
                        <option key={balda} value={balda} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Posición</label>
                    <input
                      type="text"
                      name="ubicacion_posicion"
                      value={formData.ubicacion_posicion}
                      onChange={handleInputChange}
                      className="form-input"
                    />
                  </div>
                </div>
              </div>

              {/* Imagen y Notas */}
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-purple-700 mb-6 border-b border-purple-200 pb-2">
                  🖼️ Imagen y Notas
                </h2>
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border-l-4 border-purple-500 rounded-lg p-4 mb-6">
                  <p className="text-sm text-purple-900">
                    <span className="font-semibold">🤖 ¡Magia con IA!</span> Sube una foto de la portada y la IA identificará el juego automáticamente,
                    buscará en BoardGameGeek y rellenará todos los campos en español.
                  </p>
                </div>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="form-label">Imagen del Juego</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="form-input"
                      data-testid="add-game-image-input"
                    />
                    {formData.imagen && (
                      <div className="mt-4 flex items-center gap-3">
                        <img
                          src={formData.imagen}
                          alt="Preview"
                          className="w-32 h-32 object-cover rounded-lg border-2 border-purple-200"
                        />
                        <button
                          type="button"
                          onClick={() => runAIFlow(formData.imagen)}
                          className="btn-primary text-sm"
                          data-testid="ia-retry-btn"
                        >
                          🤖 Reintentar IA
                        </button>
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="form-label">Notas</label>
                    <textarea
                      name="notas"
                      value={formData.notas}
                      onChange={handleInputChange}
                      className="form-input"
                      rows="4"
                      placeholder="Notas adicionales sobre el juego..."
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={() => setCurrentView('home')}
                  className="btn-secondary"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                >
                  ➕ Añadir Juego
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  };

  // Edit Game Screen
  const EditGameScreen = () => {
    const [formData, setFormData] = useState({
      nombre: '',
      descripcion: '',
      categoria: '',
      autor: '',
      editorial: '',
      año_publicacion: '',
      jugadores_minimo: '',
      jugadores_maximo: '',
      duracion_minima: '',
      duracion_maxima: '',
      complejidad: '',
      ubicacion_estanteria: '',
      ubicacion_balda: '',
      ubicacion_posicion: '',
      idioma: '',
      notas: '',
      imagen: ''
    });

    // Pre-populate form with existing game data
    useEffect(() => {
      if (editingGame) {
        setFormData({
          nombre: editingGame.nombre || '',
          descripcion: editingGame.descripcion || '',
          categoria: editingGame.categoria || '',
          autor: editingGame.autor || '',
          editorial: editingGame.editorial || '',
          año_publicacion: editingGame.año_publicacion ? editingGame.año_publicacion.toString() : '',
          jugadores_minimo: editingGame.jugadores_minimo ? editingGame.jugadores_minimo.toString() : '',
          jugadores_maximo: editingGame.jugadores_maximo ? editingGame.jugadores_maximo.toString() : '',
          duracion_minima: editingGame.duracion_minima ? editingGame.duracion_minima.toString() : '',
          duracion_maxima: editingGame.duracion_maxima ? editingGame.duracion_maxima.toString() : '',
          complejidad: editingGame.complejidad ? editingGame.complejidad.toString() : '',
          ubicacion_estanteria: editingGame.ubicacion_estanteria || '',
          ubicacion_balda: editingGame.ubicacion_balda || '',
          ubicacion_posicion: editingGame.ubicacion_posicion || '',
          idioma: editingGame.idioma || '',
          notas: editingGame.notas || '',
          imagen: editingGame.imagen || ''
        });
      }
    }, [editingGame]);

    const handleInputChange = (e) => {
      const { name, value } = e.target;
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    };

    const handleImageUpload = (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          setFormData(prev => ({
            ...prev,
            imagen: event.target.result
          }));
        };
        reader.readAsDataURL(file);
      }
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const submitData = {
          ...formData,
          año_publicacion: formData.año_publicacion ? parseInt(formData.año_publicacion) : null,
          jugadores_minimo: formData.jugadores_minimo ? parseInt(formData.jugadores_minimo) : null,
          jugadores_maximo: formData.jugadores_maximo ? parseInt(formData.jugadores_maximo) : null,
          duracion_minima: formData.duracion_minima ? parseInt(formData.duracion_minima) : null,
          duracion_maxima: formData.duracion_maxima ? parseInt(formData.duracion_maxima) : null,
          complejidad: formData.complejidad ? parseInt(formData.complejidad) : null,
        };

        await axios.put(`${API}/games/${editingGame.id}`, submitData);
        alert('¡Juego actualizado correctamente!');
        fetchGames();
        fetchAutocompleteData();
        setEditingGame(null);
        setCurrentView('home');
      } catch (error) {
        console.error('Error updating game:', error);
        alert('Error al actualizar el juego');
      }
    };

    if (!editingGame) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-4">❌</div>
            <p className="text-xl text-purple-600">No hay juego seleccionado para editar</p>
            <button
              onClick={() => setCurrentView('home')}
              className="btn-primary mt-4"
            >
              Volver al Inicio
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-4xl font-bold text-purple-800">✏️ Editar Juego</h1>
              <div className="space-x-2">
                <button
                  onClick={() => {
                    setEditingGame(null);
                    setCurrentView('search');
                  }}
                  className="back-button"
                >
                  ← Volver a Búsqueda
                </button>
                <button
                  onClick={() => {
                    setEditingGame(null);
                    setCurrentView('home');
                  }}
                  className="back-button"
                >
                  🏠 Inicio
                </button>
              </div>
            </div>

            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
              <p className="text-yellow-800">
                <strong>Editando:</strong> {editingGame.nombre}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-8">
              {/* Información Básica */}
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-purple-700 mb-6 border-b border-purple-200 pb-2">
                  📋 Información Básica
                </h2>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="form-label">Nombre del Juego *</label>
                    <input
                      type="text"
                      name="nombre"
                      value={formData.nombre}
                      onChange={handleInputChange}
                      className="form-input"
                      required
                    />
                  </div>
                  <div>
                    <label className="form-label">Categoría</label>
                    <input
                      type="text"
                      name="categoria"
                      value={formData.categoria}
                      onChange={handleInputChange}
                      className="form-input"
                      list="categorias"
                    />
                    <datalist id="categorias">
                      {autocompleteData.categorias?.map(cat => (
                        <option key={cat} value={cat} />
                      ))}
                    </datalist>
                  </div>
                  <div className="md:col-span-2">
                    <label className="form-label">Descripción</label>
                    <textarea
                      name="descripcion"
                      value={formData.descripcion}
                      onChange={handleInputChange}
                      className="form-input"
                      rows="3"
                    />
                  </div>
                  <div>
                    <label className="form-label">Autor</label>
                    <input
                      type="text"
                      name="autor"
                      value={formData.autor}
                      onChange={handleInputChange}
                      className="form-input"
                      list="autores"
                    />
                    <datalist id="autores">
                      {autocompleteData.autores?.map(autor => (
                        <option key={autor} value={autor} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Editorial</label>
                    <input
                      type="text"
                      name="editorial"
                      value={formData.editorial}
                      onChange={handleInputChange}
                      className="form-input"
                      list="editoriales"
                    />
                    <datalist id="editoriales">
                      {autocompleteData.editoriales?.map(editorial => (
                        <option key={editorial} value={editorial} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Año de Publicación</label>
                    <input
                      type="number"
                      name="año_publicacion"
                      value={formData.año_publicacion}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1900"
                      max="2030"
                    />
                  </div>
                  <div>
                    <label className="form-label">Idioma</label>
                    <input
                      type="text"
                      name="idioma"
                      value={formData.idioma}
                      onChange={handleInputChange}
                      className="form-input"
                      list="idiomas"
                    />
                    <datalist id="idiomas">
                      {autocompleteData.idiomas?.map(idioma => (
                        <option key={idioma} value={idioma} />
                      ))}
                    </datalist>
                  </div>
                </div>
              </div>

              {/* Detalles del Juego */}
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-purple-700 mb-6 border-b border-purple-200 pb-2">
                  🎮 Detalles del Juego
                </h2>
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <label className="form-label">Jugadores Mínimo</label>
                    <input
                      type="number"
                      name="jugadores_minimo"
                      value={formData.jugadores_minimo}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="form-label">Jugadores Máximo</label>
                    <input
                      type="number"
                      name="jugadores_maximo"
                      value={formData.jugadores_maximo}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="form-label">Complejidad (1-5)</label>
                    <select
                      name="complejidad"
                      value={formData.complejidad}
                      onChange={handleInputChange}
                      className="form-input"
                    >
                      <option value="">Seleccionar</option>
                      <option value="1">1 - Muy Fácil</option>
                      <option value="2">2 - Fácil</option>
                      <option value="3">3 - Medio</option>
                      <option value="4">4 - Difícil</option>
                      <option value="5">5 - Muy Difícil</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Duración Mínima (min)</label>
                    <input
                      type="number"
                      name="duracion_minima"
                      value={formData.duracion_minima}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="form-label">Duración Máxima (min)</label>
                    <input
                      type="number"
                      name="duracion_maxima"
                      value={formData.duracion_maxima}
                      onChange={handleInputChange}
                      className="form-input"
                      min="1"
                    />
                  </div>
                </div>
              </div>

              {/* Ubicación */}
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-purple-700 mb-6 border-b border-purple-200 pb-2">
                  📍 Ubicación
                </h2>
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <label className="form-label">Estantería</label>
                    <input
                      type="text"
                      name="ubicacion_estanteria"
                      value={formData.ubicacion_estanteria}
                      onChange={handleInputChange}
                      className="form-input"
                      list="estanterias"
                    />
                    <datalist id="estanterias">
                      {autocompleteData.ubicaciones_estanteria?.map(est => (
                        <option key={est} value={est} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Balda</label>
                    <input
                      type="text"
                      name="ubicacion_balda"
                      value={formData.ubicacion_balda}
                      onChange={handleInputChange}
                      className="form-input"
                      list="baldas"
                    />
                    <datalist id="baldas">
                      {autocompleteData.ubicaciones_balda?.map(balda => (
                        <option key={balda} value={balda} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Posición</label>
                    <input
                      type="text"
                      name="ubicacion_posicion"
                      value={formData.ubicacion_posicion}
                      onChange={handleInputChange}
                      className="form-input"
                    />
                  </div>
                </div>
              </div>

              {/* Imagen y Notas */}
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-purple-700 mb-6 border-b border-purple-200 pb-2">
                  🖼️ Imagen y Notas
                </h2>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="form-label">Imagen del Juego</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="form-input"
                    />
                    {formData.imagen && (
                      <div className="mt-4">
                        <img
                          src={formData.imagen}
                          alt="Preview"
                          className="w-32 h-32 object-cover rounded-lg border-2 border-purple-200"
                        />
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="form-label">Notas</label>
                    <textarea
                      name="notas"
                      value={formData.notas}
                      onChange={handleInputChange}
                      className="form-input"
                      rows="4"
                      placeholder="Notas adicionales sobre el juego..."
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={() => {
                    setEditingGame(null);
                    setCurrentView('search');
                  }}
                  className="btn-secondary"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                >
                  💾 Actualizar Juego
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  };
  const SearchScreen = () => {
    const [searchFilters, setSearchFilters] = useState({
      nombre: '',
      autor: '',
      categoria: '',
      año_publicacion: '',
      jugadores_minimo: '',
      jugadores_maximo: '',
      complejidad: ''
    });
    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);

    const handleSearchChange = (e) => {
      const { name, value } = e.target;
      setSearchFilters(prev => ({
        ...prev,
        [name]: value
      }));
    };

    const handleSearch = async (e) => {
      e.preventDefault();
      setIsSearching(true);
      try {
        const filters = {};
        Object.keys(searchFilters).forEach(key => {
          if (searchFilters[key]) {
            if (key === 'año_publicacion' || key === 'complejidad' || key === 'jugadores_minimo' || key === 'jugadores_maximo') {
              filters[key] = parseInt(searchFilters[key]);
            } else {
              filters[key] = searchFilters[key];
            }
          }
        });

        const response = await axios.post(`${API}/games/search`, filters);
        setSearchResults(response.data);
      } catch (error) {
        console.error('Error searching games:', error);
        alert('Error al buscar juegos');
      } finally {
        setIsSearching(false);
      }
    };

    const clearSearch = () => {
      setSearchFilters({
        nombre: '',
        autor: '',
        categoria: '',
        año_publicacion: '',
        jugadores_minimo: '',
        jugadores_maximo: '',
        complejidad: ''
      });
      setSearchResults([]);
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-4xl font-bold text-purple-800">🔍 Buscar Juegos</h1>
              <button
                onClick={() => setCurrentView('home')}
                className="back-button"
              >
                ← Volver al Inicio
              </button>
            </div>

            {/* Search Form */}
            <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
              <form onSubmit={handleSearch}>
                <div className="grid md:grid-cols-3 gap-6 mb-6">
                  <div>
                    <label className="form-label">Nombre del Juego</label>
                    <input
                      type="text"
                      name="nombre"
                      value={searchFilters.nombre}
                      onChange={handleSearchChange}
                      className="form-input"
                      placeholder="Buscar por nombre..."
                    />
                  </div>
                  <div>
                    <label className="form-label">Autor</label>
                    <input
                      type="text"
                      name="autor"
                      value={searchFilters.autor}
                      onChange={handleSearchChange}
                      className="form-input"
                      placeholder="Buscar por autor..."
                      list="search-autores"
                    />
                    <datalist id="search-autores">
                      {autocompleteData.autores?.map(autor => (
                        <option key={autor} value={autor} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Categoría</label>
                    <input
                      type="text"
                      name="categoria"
                      value={searchFilters.categoria}
                      onChange={handleSearchChange}
                      className="form-input"
                      placeholder="Buscar por categoría..."
                      list="search-categorias"
                    />
                    <datalist id="search-categorias">
                      {autocompleteData.categorias?.map(cat => (
                        <option key={cat} value={cat} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="form-label">Año de Publicación</label>
                    <input
                      type="number"
                      name="año_publicacion"
                      value={searchFilters.año_publicacion}
                      onChange={handleSearchChange}
                      className="form-input"
                      placeholder="Ej: 2020"
                    />
                  </div>
                  <div>
                    <label className="form-label">Jugadores Mínimo</label>
                    <input
                      type="number"
                      name="jugadores_minimo"
                      value={searchFilters.jugadores_minimo}
                      onChange={handleSearchChange}
                      className="form-input"
                      placeholder="Ej: 2"
                    />
                  </div>
                  <div>
                    <label className="form-label">Jugadores Máximo</label>
                    <input
                      type="number"
                      name="jugadores_maximo"
                      value={searchFilters.jugadores_maximo}
                      onChange={handleSearchChange}
                      className="form-input"
                      placeholder="Ej: 4"
                    />
                  </div>
                  <div>
                    <label className="form-label">Complejidad</label>
                    <select
                      name="complejidad"
                      value={searchFilters.complejidad}
                      onChange={handleSearchChange}
                      className="form-input"
                    >
                      <option value="">Todas</option>
                      <option value="1">1 - Muy Fácil</option>
                      <option value="2">2 - Fácil</option>
                      <option value="3">3 - Medio</option>
                      <option value="4">4 - Difícil</option>
                      <option value="5">5 - Muy Difícil</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-center space-x-4">
                  <button
                    type="submit"
                    disabled={isSearching}
                    className="btn-primary"
                  >
                    {isSearching ? '🔄 Buscando...' : '🔍 Buscar'}
                  </button>
                  <button
                    type="button"
                    onClick={clearSearch}
                    className="btn-secondary"
                  >
                    🗑️ Limpiar
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setSearchResults(games);
                    }}
                    className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-8 rounded-xl transition-all duration-300 transform hover:scale-105"
                  >
                    📋 Ver Todos
                  </button>
                </div>
              </form>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <h2 className="text-2xl font-bold text-purple-800 mb-6">
                  📋 Resultados ({searchResults.length} juegos encontrados)
                </h2>
                <div className="grid gap-4">
                  {searchResults.map(game => (
                    <div key={game.id} className="game-card">
                      <div className="flex items-start space-x-4">
                        {game.imagen && (
                          <img
                            src={game.imagen}
                            alt={game.nombre}
                            className="w-20 h-20 object-cover rounded-lg border-2 border-purple-200"
                          />
                        )}
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-2">
                            <h3 className="text-xl font-bold text-purple-800">{game.nombre}</h3>
                            <div className="flex space-x-2">
                              <button
                                onClick={() => {
                                  setEditingGame(game);
                                  setCurrentView('edit');
                                }}
                                className="bg-yellow-500 hover:bg-yellow-600 text-white font-medium py-1 px-3 rounded-lg transition-all duration-200 transform hover:scale-105 text-sm"
                              >
                                ✏️ Editar
                              </button>
                              <button
                                onClick={() => shareGame(game)}
                                className="bg-blue-500 hover:bg-blue-600 text-white font-medium py-1 px-3 rounded-lg transition-all duration-200 transform hover:scale-105 text-sm"
                              >
                                📤 Compartir
                              </button>
                              <button
                                onClick={async () => {
                                  if (window.confirm(`¿Estás seguro de que quieres eliminar "${game.nombre}"?`)) {
                                    try {
                                      await axios.delete(`${API}/games/${game.id}`);
                                      alert('¡Juego eliminado correctamente!');
                                      fetchGames();
                                      handleSearch({ preventDefault: () => {} }); // Refresh search results
                                    } catch (error) {
                                      console.error('Error deleting game:', error);
                                      alert('Error al eliminar el juego');
                                    }
                                  }
                                }}
                                className="bg-red-500 hover:bg-red-600 text-white font-medium py-1 px-3 rounded-lg transition-all duration-200 transform hover:scale-105 text-sm"
                              >
                                🗑️ Eliminar
                              </button>
                            </div>
                          </div>
                          <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                              {game.autor && <p><strong>Autor:</strong> {game.autor}</p>}
                              {game.categoria && <p><strong>Categoría:</strong> {game.categoria}</p>}
                              {game.editorial && <p><strong>Editorial:</strong> {game.editorial}</p>}
                            </div>
                            <div>
                              {game.año_publicacion && <p><strong>Año:</strong> {game.año_publicacion}</p>}
                              {(game.jugadores_minimo || game.jugadores_maximo) && (
                                <p><strong>Jugadores:</strong> {game.jugadores_minimo || '?'} - {game.jugadores_maximo || '?'}</p>
                              )}
                              {game.complejidad && <p><strong>Complejidad:</strong> {game.complejidad}/5</p>}
                            </div>
                          </div>
                          {game.descripcion && (
                            <p className="text-gray-700 mt-2">{game.descripcion}</p>
                          )}
                          {(game.ubicacion_estanteria || game.ubicacion_balda) && (
                            <p className="text-sm text-purple-600 mt-2">
                              <strong>📍 Ubicación:</strong> {game.ubicacion_estanteria} - {game.ubicacion_balda} - {game.ubicacion_posicion}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Backup & Restore panel (used inside Statistics)
  const BackupRestorePanel = ({ onRestored, totalJuegos }) => {
    const [restoring, setRestoring] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [confirmFile, setConfirmFile] = useState(null);
    const [restoreMode, setRestoreMode] = useState('reemplazar');
    const [message, setMessage] = useState(null);

    const downloadBackup = async () => {
      setDownloading(true);
      setMessage(null);
      try {
        const res = await axios.get(`${API}/backup`);
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const date = new Date().toISOString().slice(0, 10);
        a.href = url;
        a.download = `mi-ludoteca-backup-${date}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        setMessage({ type: 'success', text: `✅ Backup descargado (${res.data.total_juegos} juegos).` });
      } catch (err) {
        setMessage({ type: 'error', text: '❌ Error al descargar el backup.' });
      } finally {
        setDownloading(false);
      }
    };

    const handleFileSelect = (e) => {
      const file = e.target.files[0];
      if (!file) return;
      setMessage(null);
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const parsed = JSON.parse(event.target.result);
          if (!parsed.juegos || !Array.isArray(parsed.juegos)) {
            setMessage({ type: 'error', text: '❌ Archivo inválido: no contiene una lista de juegos.' });
            return;
          }
          setConfirmFile(parsed);
        } catch (err) {
          setMessage({ type: 'error', text: '❌ El archivo no es un JSON válido.' });
        }
      };
      reader.readAsText(file);
      // reset input so same file can be re-picked
      e.target.value = '';
    };

    const confirmRestore = async () => {
      if (!confirmFile) return;
      setRestoring(true);
      setMessage(null);
      try {
        const res = await axios.post(`${API}/restore`, {
          juegos: confirmFile.juegos,
          modo: restoreMode,
        });
        const d = res.data;
        let msg = `✅ Restauración completada. Importados: ${d.importados}`;
        if (d.actualizados) msg += `, actualizados: ${d.actualizados}`;
        if (d.eliminados_previos) msg += `, eliminados previos: ${d.eliminados_previos}`;
        if (d.omitidos) msg += `, omitidos: ${d.omitidos}`;
        setMessage({ type: 'success', text: msg });
        setConfirmFile(null);
        if (onRestored) onRestored();
      } catch (err) {
        setMessage({ type: 'error', text: '❌ Error al restaurar: ' + (err.response?.data?.detail || err.message) });
      } finally {
        setRestoring(false);
      }
    };

    return (
      <div className="bg-white rounded-2xl shadow-xl p-6 mb-8" data-testid="backup-restore-panel">
        <h2 className="text-2xl font-bold text-purple-800 mb-4">💾 Backup y Restauración</h2>
        <p className="text-sm text-gray-600 mb-4">
          Descarga toda tu ludoteca en un archivo JSON (incluye imágenes y metadatos) para guardarla en lugar seguro.
          Puedes restaurarla en cualquier momento.
        </p>

        <div className="grid md:grid-cols-2 gap-4">
          <button
            onClick={downloadBackup}
            disabled={downloading}
            className="flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-md transition-all disabled:opacity-60"
            data-testid="backup-download-btn"
          >
            {downloading ? '⏳ Descargando...' : `📥 Descargar Backup (${totalJuegos} juegos)`}
          </button>

          <label
            className="flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white font-semibold rounded-xl shadow-md transition-all cursor-pointer"
            data-testid="backup-restore-btn"
          >
            📂 Restaurar desde Backup
            <input
              type="file"
              accept="application/json,.json"
              onChange={handleFileSelect}
              className="hidden"
              data-testid="backup-file-input"
            />
          </label>
        </div>

        {message && (
          <div
            className={`mt-4 p-3 rounded-lg border-l-4 ${
              message.type === 'success'
                ? 'bg-green-50 border-green-500 text-green-800'
                : 'bg-red-50 border-red-500 text-red-800'
            }`}
            data-testid="backup-message"
          >
            {message.text}
          </div>
        )}

        {/* Confirm modal */}
        {confirmFile && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="restore-confirm-modal">
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6">
              <h3 className="text-2xl font-bold text-purple-800 mb-4">⚠️ Confirmar restauración</h3>
              <p className="text-gray-700 mb-2">
                El archivo contiene <span className="font-bold">{confirmFile.juegos.length}</span> juegos
                {confirmFile.fecha && ` (backup del ${new Date(confirmFile.fecha).toLocaleDateString('es-ES')})`}.
              </p>
              <p className="text-sm text-gray-500 mb-4">Tu colección actual: <span className="font-semibold">{totalJuegos}</span> juegos.</p>

              <div className="space-y-2 mb-4">
                <label className="flex items-start gap-3 p-3 border-2 rounded-lg cursor-pointer hover:bg-purple-50 transition-colors"
                  style={{ borderColor: restoreMode === 'reemplazar' ? '#a855f7' : '#e5e7eb' }}>
                  <input
                    type="radio"
                    name="restoreMode"
                    value="reemplazar"
                    checked={restoreMode === 'reemplazar'}
                    onChange={() => setRestoreMode('reemplazar')}
                    className="mt-1"
                    data-testid="restore-mode-replace"
                  />
                  <div>
                    <div className="font-semibold text-purple-900">🗑️ Reemplazar todo</div>
                    <div className="text-sm text-gray-600">Elimina los {totalJuegos} juegos actuales y los sustituye por los del backup. <span className="text-red-600 font-semibold">¡Destructivo!</span></div>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3 border-2 rounded-lg cursor-pointer hover:bg-purple-50 transition-colors"
                  style={{ borderColor: restoreMode === 'fusionar' ? '#a855f7' : '#e5e7eb' }}>
                  <input
                    type="radio"
                    name="restoreMode"
                    value="fusionar"
                    checked={restoreMode === 'fusionar'}
                    onChange={() => setRestoreMode('fusionar')}
                    className="mt-1"
                    data-testid="restore-mode-merge"
                  />
                  <div>
                    <div className="font-semibold text-purple-900">🔄 Fusionar</div>
                    <div className="text-sm text-gray-600">Mantiene los juegos actuales. Los del backup con el mismo ID se actualizan, los nuevos se añaden.</div>
                  </div>
                </label>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setConfirmFile(null)}
                  disabled={restoring}
                  className="btn-secondary flex-1"
                  data-testid="restore-cancel-btn"
                >
                  Cancelar
                </button>
                <button
                  onClick={confirmRestore}
                  disabled={restoring}
                  className="btn-primary flex-1 disabled:opacity-60"
                  data-testid="restore-confirm-btn"
                >
                  {restoring ? '⏳ Restaurando...' : 'Sí, restaurar'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Statistics Screen
  const StatisticsScreen = () => {
    if (!statistics) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl mb-4">🔄</div>
            <p className="text-xl text-purple-600">Cargando estadísticas...</p>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-4xl font-bold text-purple-800">📊 Estadísticas</h1>
              <button
                onClick={() => setCurrentView('home')}
                className="back-button"
              >
                ← Volver al Inicio
              </button>
            </div>

            {/* Backup & Restore */}
            <BackupRestorePanel onRestored={() => { fetchGames(); fetchStatistics(); fetchAutocompleteData(); }} totalJuegos={statistics.total_juegos} />

            {/* Overview Stats */}
            <div className="grid md:grid-cols-4 gap-6 mb-8">
              <div className="stats-card stats-card-total">
                <div className="text-3xl mb-2">🎲</div>
                <div className="text-3xl font-bold text-white">{statistics.total_juegos}</div>
                <div className="text-sm text-white opacity-90">Total de Juegos</div>
              </div>
              <div className="stats-card stats-card-completed">
                <div className="text-3xl mb-2">⭐</div>
                <div className="text-3xl font-bold text-white">{statistics.complejidad_promedio.toFixed(1)}</div>
                <div className="text-sm text-white opacity-90">Complejidad Promedio</div>
              </div>
              <div className="stats-card bg-gradient-to-br from-indigo-500 to-purple-600">
                <div className="text-3xl mb-2">🏆</div>
                <div className="text-3xl font-bold text-white">{Object.keys(statistics.categorias_populares).length}</div>
                <div className="text-sm text-white opacity-90">Categorías Diferentes</div>
              </div>
              <div className="stats-card bg-gradient-to-br from-pink-500 to-rose-600">
                <div className="text-3xl mb-2">👥</div>
                <div className="text-3xl font-bold text-white">{Object.values(statistics.rango_jugadores).reduce((a, b) => a + b, 0)}</div>
                <div className="text-sm text-white opacity-90">Juegos Catalogados</div>
              </div>
            </div>

            {/* Charts Grid */}
            <div className="grid lg:grid-cols-2 gap-8">
              {/* Top Categories */}
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h2 className="text-2xl font-bold text-purple-800 mb-6">🏷️ Categorías Populares</h2>
                <div className="space-y-4">
                  {Object.entries(statistics.categorias_populares).slice(0, 5).map(([categoria, count]) => (
                    <div key={categoria} className="flex items-center justify-between">
                      <span className="text-gray-700 font-medium">{categoria}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-purple-100 rounded-full h-2">
                          <div
                            className="h-2 bg-purple-500 rounded-full"
                            style={{ width: `${(count / Math.max(...Object.values(statistics.categorias_populares))) * 100}%` }}
                          />
                        </div>
                        <span className="text-purple-600 font-bold text-sm w-8">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Authors */}
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h2 className="text-2xl font-bold text-purple-800 mb-6">✍️ Autores Populares</h2>
                <div className="space-y-4">
                  {Object.entries(statistics.autores_populares).slice(0, 5).map(([autor, count]) => (
                    <div key={autor} className="flex items-center justify-between">
                      <span className="text-gray-700 font-medium">{autor}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-blue-100 rounded-full h-2">
                          <div
                            className="h-2 bg-blue-500 rounded-full"
                            style={{ width: `${(count / Math.max(...Object.values(statistics.autores_populares))) * 100}%` }}
                          />
                        </div>
                        <span className="text-blue-600 font-bold text-sm w-8">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Player Range */}
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h2 className="text-2xl font-bold text-purple-800 mb-6">👥 Rango de Jugadores</h2>
                <div className="space-y-4">
                  {Object.entries(statistics.rango_jugadores).map(([rango, count]) => (
                    <div key={rango} className="flex items-center justify-between">
                      <span className="text-gray-700 font-medium">{rango} jugadores</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-green-100 rounded-full h-2">
                          <div
                            className="h-2 bg-green-500 rounded-full"
                            style={{ width: `${(count / Math.max(...Object.values(statistics.rango_jugadores))) * 100}%` }}
                          />
                        </div>
                        <span className="text-green-600 font-bold text-sm w-8">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Publishers */}
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h2 className="text-2xl font-bold text-purple-800 mb-6">🏢 Editoriales Populares</h2>
                <div className="space-y-4">
                  {Object.entries(statistics.editoriales_populares).slice(0, 5).map(([editorial, count]) => (
                    <div key={editorial} className="flex items-center justify-between">
                      <span className="text-gray-700 font-medium">{editorial}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-orange-100 rounded-full h-2">
                          <div
                            className="h-2 bg-orange-500 rounded-full"
                            style={{ width: `${(count / Math.max(...Object.values(statistics.editoriales_populares))) * 100}%` }}
                          />
                        </div>
                        <span className="text-orange-600 font-bold text-sm w-8">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Locations Screen
  const LocationsScreen = () => {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-4xl font-bold text-purple-800">📍 Ubicaciones</h1>
              <button
                onClick={() => setCurrentView('home')}
                className="back-button"
              >
                ← Volver al Inicio
              </button>
            </div>

            <div className="grid gap-6">
              {Object.entries(locations).map(([estanteria, baldas]) => (
                <div key={estanteria} className="bg-white rounded-2xl shadow-xl p-6">
                  <h2 className="text-2xl font-bold text-purple-800 mb-6">
                    🏛️ {estanteria}
                  </h2>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(baldas).map(([balda, info]) => (
                      <div key={balda} className="bg-purple-50 rounded-xl p-4 border-2 border-purple-200">
                        <h3 className="text-lg font-semibold text-purple-700 mb-3">
                          📚 {balda}
                        </h3>
                        <p className="text-sm text-purple-600 mb-3">
                          {info.count} juego{info.count !== 1 ? 's' : ''}
                        </p>
                        <div className="space-y-1">
                          {info.juegos.slice(0, 3).map(juego => (
                            <div key={juego.id} className="text-sm text-gray-700 bg-white rounded px-2 py-1">
                              {juego.nombre}
                            </div>
                          ))}
                          {info.juegos.length > 3 && (
                            <div className="text-xs text-purple-500 font-medium">
                              ... y {info.juegos.length - 3} más
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              
              {Object.keys(locations).length === 0 && (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📍</div>
                  <h2 className="text-2xl font-bold text-purple-800 mb-2">No hay ubicaciones registradas</h2>
                  <p className="text-purple-600">Añade juegos con ubicaciones para ver este mapa</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render current view
  const renderCurrentView = () => {
    switch (currentView) {
      case 'add':
        return <AddGameScreen />;
      case 'edit':
        return <EditGameScreen />;
      case 'search':
        return <SearchScreen />;
      case 'statistics':
        return <StatisticsScreen />;
      case 'locations':
        return <LocationsScreen />;
      default:
        return <HomeScreen />;
    }
  };

  return <div className="App">{renderCurrentView()}</div>;
}

export default App;
