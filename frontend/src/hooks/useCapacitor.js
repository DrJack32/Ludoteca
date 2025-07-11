import { useEffect, useState } from 'react';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Storage } from '@capacitor/storage';
import { Capacitor } from '@capacitor/core';

export const useCapacitor = () => {
  const [isNative, setIsNative] = useState(false);

  useEffect(() => {
    setIsNative(Capacitor.isNativePlatform());
  }, []);

  // Función para tomar foto con la cámara nativa
  const takePhoto = async () => {
    if (!isNative) {
      // Fallback para web
      return new Promise((resolve) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = (event) => {
          const file = event.target.files[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsDataURL(file);
          }
        };
        input.click();
      });
    }

    try {
      const image = await Camera.getPhoto({
        quality: 90,
        allowEditing: true,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Camera
      });

      return image.dataUrl;
    } catch (error) {
      console.error('Error taking photo:', error);
      return null;
    }
  };

  // Función para seleccionar foto de la galería
  const selectFromGallery = async () => {
    if (!isNative) {
      // Fallback para web
      return new Promise((resolve) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = (event) => {
          const file = event.target.files[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsDataURL(file);
          }
        };
        input.click();
      });
    }

    try {
      const image = await Camera.getPhoto({
        quality: 90,
        allowEditing: true,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Photos
      });

      return image.dataUrl;
    } catch (error) {
      console.error('Error selecting photo:', error);
      return null;
    }
  };

  // Guardar datos localmente
  const saveLocalData = async (key, value) => {
    try {
      await Storage.set({
        key: key,
        value: JSON.stringify(value)
      });
    } catch (error) {
      console.error('Error saving local data:', error);
    }
  };

  // Obtener datos locales
  const getLocalData = async (key) => {
    try {
      const result = await Storage.get({ key });
      return result.value ? JSON.parse(result.value) : null;
    } catch (error) {
      console.error('Error getting local data:', error);
      return null;
    }
  };

  // Compartir información de juego
  const shareGame = async (gameData) => {
    if (!isNative) {
      // Fallback para web
      if (navigator.share) {
        await navigator.share({
          title: `Mi Ludoteca - ${gameData.nombre}`,
          text: `${gameData.nombre} - ${gameData.descripcion}`,
          url: window.location.href
        });
      } else {
        // Copiar al portapapeles
        const text = `${gameData.nombre}\n${gameData.descripcion}\nAutor: ${gameData.autor}\nCategoría: ${gameData.categoria}`;
        await navigator.clipboard.writeText(text);
        alert('Información copiada al portapapeles');
      }
      return;
    }

    // Implementar compartir nativo aquí si es necesario
    const text = `${gameData.nombre}\n${gameData.descripcion}\nAutor: ${gameData.autor}\nCategoría: ${gameData.categoria}`;
    if (navigator.share) {
      await navigator.share({
        title: `Mi Ludoteca - ${gameData.nombre}`,
        text: text
      });
    }
  };

  return {
    isNative,
    takePhoto,
    selectFromGallery,
    saveLocalData,
    getLocalData,
    shareGame
  };
};