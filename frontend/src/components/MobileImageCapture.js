import React from 'react';
import { useCapacitor } from '../hooks/useCapacitor';

const MobileImageCapture = ({ onImageCapture, currentImage }) => {
  const { takePhoto, selectFromGallery, isNative } = useCapacitor();

  const handleTakePhoto = async () => {
    const photo = await takePhoto();
    if (photo) {
      onImageCapture(photo);
    }
  };

  const handleSelectFromGallery = async () => {
    const photo = await selectFromGallery();
    if (photo) {
      onImageCapture(photo);
    }
  };

  const handleFileInput = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        onImageCapture(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="space-y-4">
      <label className="form-label">📸 Imagen del Juego</label>
      
      {isNative ? (
        // Controles nativos para móvil
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={handleTakePhoto}
            className="bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-4 rounded-xl transition-all duration-200 transform hover:scale-105 text-sm"
          >
            📷 Tomar Foto
          </button>
          <button
            type="button"
            onClick={handleSelectFromGallery}
            className="bg-green-500 hover:bg-green-600 text-white font-medium py-3 px-4 rounded-xl transition-all duration-200 transform hover:scale-105 text-sm"
          >
            🖼️ Galería
          </button>
        </div>
      ) : (
        // Fallback para web
        <input
          type="file"
          accept="image/*"
          onChange={handleFileInput}
          className="form-input"
        />
      )}

      {currentImage && (
        <div className="mt-4 relative">
          <img
            src={currentImage}
            alt="Preview"
            className="w-full max-w-sm h-48 object-cover rounded-lg border-2 border-purple-200 mx-auto"
          />
          <button
            type="button"
            onClick={() => onImageCapture('')}
            className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
};

export default MobileImageCapture;