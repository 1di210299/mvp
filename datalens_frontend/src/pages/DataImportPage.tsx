import React from 'react';
import DataImport from '../components/DataImport';

const DataImportPage: React.FC = () => {
  const handleImportComplete = (results: any) => {
    console.log('Importación completada:', results);
    // Aquí puedes agregar lógica adicional como notificaciones o redirecciones
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="md:flex md:items-center md:justify-between">
              <div className="flex-1 min-w-0">
                <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
                  Importación de Datos
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                  Importa tus datos desde archivos Excel o CSV de manera sencilla
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="py-8">
        <DataImport onImportComplete={handleImportComplete} />
      </div>
    </div>
  );
};

export default DataImportPage;