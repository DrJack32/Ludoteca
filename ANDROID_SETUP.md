# Cómo obtener el APK de Mi Ludoteca

Tienes **3 caminos** para conseguir el `.apk` instalable en tu Android. Elige el que mejor se adapte a ti. Recomiendo el **Camino 1** porque es el más sencillo: no necesitas instalar nada en tu ordenador.

---

## ✅ Camino 1: Compilación automática en la nube con GitHub Actions (RECOMENDADO)

GitHub compila el APK por ti en sus servidores y te lo entrega listo para descargar. **No necesitas instalar Java, Android Studio, ni nada**. Solo necesitas una cuenta gratuita de GitHub.

### Pasos:

1. **Sube tu código a GitHub** desde Emergent:
   - En el chat de Emergent, busca el botón **"Save to Github"** (arriba a la derecha del chat).
   - Crea un repositorio nuevo (puede ser privado).
   - Pulsa "Push" o "Save".

2. **GitHub Actions se ejecuta automáticamente**:
   - Ve a tu repositorio en `https://github.com/TU_USUARIO/NOMBRE_REPO`.
   - Pulsa la pestaña **"Actions"** (arriba).
   - Verás un workflow llamado **"Build Android APK"** en ejecución (toma 4–7 minutos).
   - Espera a que aparezca un ✅ verde.

3. **Descarga el APK**:
   - Haz clic en el workflow completado.
   - Baja hasta la sección **"Artifacts"**.
   - Pulsa en **`mi-ludoteca-apk`** y se descargará un `.zip`.
   - Descomprímelo: dentro encontrarás **`mi-ludoteca.apk`**.

4. **Instala el APK en tu móvil**:
   - Pasa el archivo `mi-ludoteca.apk` a tu móvil (por cable USB, Google Drive, correo, WhatsApp Web…).
   - En tu Android, ve a **Ajustes → Seguridad → Instalar apps de orígenes desconocidos** y permite tu explorador de archivos / navegador.
   - Abre el `.apk` desde el móvil y pulsa **"Instalar"**.
   - Listo, ya tendrás Mi Ludoteca en tu pantalla de inicio. 🎉

### Si necesitas cambiar la URL del backend más adelante:
En tu repositorio de GitHub → **Settings → Secrets and variables → Actions → New repository secret**:
- Nombre: `REACT_APP_BACKEND_URL`
- Valor: la URL de tu backend (la que aparece en `/app/frontend/.env`)

---

## 🛠 Camino 2: Compilar en tu ordenador con Android Studio

Más lento de configurar la primera vez (~1 h), pero te da control total y podrás generar APKs firmados para la Play Store.

### Requisitos previos (instala una sola vez):

1. **Node.js 20+** → https://nodejs.org/
2. **Yarn** → tras instalar Node, abre la terminal y ejecuta: `npm install -g yarn`
3. **Java JDK 21** → https://adoptium.net/ (Temurin 21)
4. **Android Studio** → https://developer.android.com/studio
   - Durante la instalación deja marcadas todas las casillas (incluido Android SDK).
   - Al abrirlo por primera vez, deja que descargue componentes (~3 GB).

### Pasos para compilar:

1. **Descarga tu proyecto** desde GitHub (botón verde "Code → Download ZIP") o clonando:
   ```bash
   git clone https://github.com/TU_USUARIO/NOMBRE_REPO.git
   cd NOMBRE_REPO/frontend
   ```

2. **Instala dependencias y haz build**:
   ```bash
   yarn install
   yarn build
   npx cap sync android
   ```

3. **Compila el APK**:
   ```bash
   cd android
   ./gradlew assembleDebug
   ```
   *(En Windows usa `gradlew.bat assembleDebug` en lugar de `./gradlew`)*

4. **Encuentra el APK**:
   ```
   frontend/android/app/build/outputs/apk/debug/app-debug.apk
   ```

5. **Instálalo** en tu móvil siguiendo el paso 4 del Camino 1.

### Alternativa visual (sin terminal):
Después de `yarn build && npx cap sync android`, ejecuta:
```bash
npx cap open android
```
Esto abre Android Studio con tu proyecto. Después: menú **Build → Build Bundle(s) / APK(s) → Build APK(s)**. Espera y pulsa "locate" para encontrarlo.

---

## 🌐 Camino 3: PWABuilder (la app como Progressive Web App)

Si no quieres compilar nada y aceptas pequeñas limitaciones (la cámara nativa de Capacitor no se usa, pero la web funciona perfectamente):

1. Ve a **https://www.pwabuilder.com/**
2. Pega la URL de tu app: `https://repo-restore-9.preview.emergentagent.com`
3. Pulsa **Start** → **Package For Stores → Android**.
4. Descarga el `.apk` generado.

> ⚠️ Este método usa la web envuelta. Si Emergent reinicia el preview, la app puede no funcionar. Para uso estable, usa Camino 1 o 2.

---

## ❓ Preguntas frecuentes

**¿Por qué no me genera Emergent directamente el APK?**
El contenedor de Emergent no tiene Java/Android SDK instalados (la compilación de Android pesa ~5 GB), por eso usamos GitHub Actions, que sí lo tiene.

**¿El APK necesita internet?**
Sí, para conectarse al backend. Sin embargo, la app guarda los últimos juegos en caché para verlos sin conexión.

**¿Funciona en cualquier Android?**
Sí, Android 7.0 (API 24) o superior.

**¿Cómo actualizo la app cuando cambio el código?**
Cada vez que pulses "Save to Github" en Emergent, GitHub Actions vuelve a compilar el APK automáticamente. Descárgalo de nuevo desde **Actions → Artifacts** e instálalo encima del anterior.

**¿Puedo subirlo a Google Play?**
Sí, pero necesitas un APK/AAB firmado con tu clave (keystore) y una cuenta de desarrollador de Google (25 USD una sola vez). En Android Studio: **Build → Generate Signed Bundle / APK**.

---

## 🎯 Resumen rápido

| Camino | Tiempo | Dificultad | Requiere instalar algo |
|--------|--------|------------|------------------------|
| 1. GitHub Actions | 10 min | ⭐ Fácil | No |
| 2. Android Studio | 1–2 h | ⭐⭐⭐ Media | Sí (~5 GB) |
| 3. PWABuilder | 5 min | ⭐ Fácil | No (pero más limitado) |

**👉 Mi recomendación: Camino 1.**
