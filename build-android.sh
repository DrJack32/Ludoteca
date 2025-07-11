#!/bin/bash

# 🚀 Script de Construcción para Mi Ludoteca Android
# Este script automatiza la generación del APK

echo "🎲 Mi Ludoteca - Construcción Android"
echo "====================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
show_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

show_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

show_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si estamos en el directorio correcto
if [ ! -f "package.json" ]; then
    show_error "No se encontró package.json. Ejecuta este script desde el directorio frontend/"
    exit 1
fi

# Verificar si Capacitor está instalado
if [ ! -f "capacitor.config.json" ]; then
    show_error "No se encontró capacitor.config.json. Ejecuta primero 'npx cap init'"
    exit 1
fi

echo
show_message "Iniciando proceso de construcción..."
echo

# Paso 1: Limpiar build anterior
show_message "1. Limpiando build anterior..."
rm -rf build/
rm -rf android/app/src/main/assets/public/

# Paso 2: Instalar dependencias
show_message "2. Instalando dependencias..."
yarn install

# Paso 3: Crear build de producción
show_message "3. Creando build de producción..."
yarn build

if [ $? -ne 0 ]; then
    show_error "Error en el build de React. Revisa los errores arriba."
    exit 1
fi

# Paso 4: Sincronizar con Android
show_message "4. Sincronizando con Android..."
npx cap sync android

if [ $? -ne 0 ]; then
    show_error "Error en la sincronización con Android."
    exit 1
fi

# Paso 5: Verificar si existe Android SDK
if [ -z "$ANDROID_HOME" ]; then
    show_warning "ANDROID_HOME no está configurado."
    show_warning "Para generar el APK necesitas:"
    show_warning "1. Instalar Android Studio"
    show_warning "2. Configurar ANDROID_HOME"
    show_warning "3. Ejecutar: npx cap open android"
    echo
    show_message "Construcción completada hasta sincronización."
    show_message "Ejecuta 'npx cap open android' para continuar en Android Studio."
    exit 0
fi

# Paso 6: Verificar Gradle
if [ ! -f "android/gradlew" ]; then
    show_error "No se encontró gradlew. Ejecuta 'npx cap sync android' primero."
    exit 1
fi

# Paso 7: Intentar generar APK
show_message "5. Intentando generar APK..."
cd android

# Hacer gradlew ejecutable
chmod +x gradlew

# Generar APK debug
./gradlew assembleDebug

if [ $? -eq 0 ]; then
    show_message "✅ APK generado exitosamente!"
    show_message "Ubicación: android/app/build/outputs/apk/debug/app-debug.apk"
    
    # Mostrar información del APK
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
    if [ -f "$APK_PATH" ]; then
        APK_SIZE=$(ls -lh "$APK_PATH" | awk '{print $5}')
        show_message "Tamaño del APK: $APK_SIZE"
    fi
else
    show_error "Error al generar el APK."
    show_warning "Para generar APK manualmente:"
    show_warning "1. npx cap open android"
    show_warning "2. En Android Studio: Build > Generate Signed Bundle/APK"
    exit 1
fi

echo
show_message "🎉 ¡Construcción completada!"
echo
echo "📱 Para instalar el APK en tu dispositivo:"
echo "   1. Habilita 'Fuentes desconocidas' en Android"
echo "   2. Transfiere el APK a tu dispositivo"
echo "   3. Abre el APK e instala"
echo
echo "🔧 Para generar APK de release:"
echo "   1. npx cap open android"
echo "   2. Build > Generate Signed Bundle/APK"
echo "   3. Selecciona 'APK' y configura keystore"
echo