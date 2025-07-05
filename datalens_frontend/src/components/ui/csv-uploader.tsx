import React, { useState, useRef } from 'react';
import { Button } from './button';

interface CSVColumn {
  key: string;
  label: string;
  type?: 'string' | 'number' | 'date' | 'boolean';
  required?: boolean;
}

interface CSVUploaderProps {
  onDataLoaded: (data: any[]) => void;
  expectedColumns?: CSVColumn[];
  maxFileSize?: number; // in MB
  className?: string;
  downloadTemplate?: boolean;
  templateColumns?: CSVColumn[];
}

export const CSVUploader: React.FC<CSVUploaderProps> = ({
  onDataLoaded,
  expectedColumns = [],
  maxFileSize = 10,
  className = '',
  downloadTemplate = false,
  templateColumns = expectedColumns
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any[] | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const parseCSV = (csvText: string): any[] => {
    const lines = csvText.split('\n').filter(line => line.trim() !== '');
    if (lines.length === 0) return [];

    const headers = lines[0].split(',').map(h => h.trim().replace(/['"]/g, ''));
    const data = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/['"]/g, ''));
      if (values.length === headers.length) {
        const row: any = {};
        headers.forEach((header, index) => {
          row[header] = values[index];
        });
        data.push(row);
      }
    }

    return data;
  };

  const validateData = (data: any[]): string[] => {
    const errors: string[] = [];

    if (expectedColumns.length > 0) {
      const dataKeys = data.length > 0 ? Object.keys(data[0]) : [];
      
      // Verificar columnas requeridas
      expectedColumns.forEach(col => {
        if (col.required && !dataKeys.includes(col.key)) {
          errors.push(`Columna requerida faltante: ${col.label}`);
        }
      });

      // Validar tipos de datos
      data.forEach((row, index) => {
        expectedColumns.forEach(col => {
          if (row[col.key] !== undefined && row[col.key] !== '') {
            const value = row[col.key];
            
            switch (col.type) {
              case 'number':
                if (isNaN(Number(value))) {
                  errors.push(`Fila ${index + 1}: ${col.label} debe ser un número`);
                }
                break;
              case 'date':
                if (isNaN(Date.parse(value))) {
                  errors.push(`Fila ${index + 1}: ${col.label} debe ser una fecha válida`);
                }
                break;
              case 'boolean':
                if (!['true', 'false', '1', '0', 'yes', 'no'].includes(value.toLowerCase())) {
                  errors.push(`Fila ${index + 1}: ${col.label} debe ser verdadero/falso`);
                }
                break;
            }
          }
        });
      });
    }

    return errors;
  };

  const processFile = async (file: File) => {
    setUploading(true);
    setError(null);

    try {
      // Validar tamaño del archivo
      if (file.size > maxFileSize * 1024 * 1024) {
        throw new Error(`El archivo es demasiado grande. Máximo ${maxFileSize}MB permitido.`);
      }

      // Validar tipo de archivo
      if (!file.name.toLowerCase().endsWith('.csv')) {
        throw new Error('Solo se permiten archivos CSV (.csv)');
      }

      const text = await file.text();
      const data = parseCSV(text);

      if (data.length === 0) {
        throw new Error('El archivo CSV está vacío o no tiene un formato válido');
      }

      // Validar datos
      const validationErrors = validateData(data);
      if (validationErrors.length > 0) {
        throw new Error(`Errores de validación:\n${validationErrors.join('\n')}`);
      }

      setPreviewData(data.slice(0, 5)); // Mostrar solo las primeras 5 filas
      setFileName(file.name);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al procesar el archivo');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      processFile(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      processFile(files[0]);
    }
  };

  const confirmUpload = () => {
    if (previewData) {
      onDataLoaded(previewData);
      setPreviewData(null);
      setFileName('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDownloadTemplate = () => {
    if (templateColumns.length === 0) return;

    const headers = templateColumns.map(col => col.label).join(',');
    const exampleRow = templateColumns.map(col => {
      switch (col.type) {
        case 'number': return '100';
        case 'date': return '2024-01-01';
        case 'boolean': return 'true';
        default: return 'Ejemplo';
      }
    }).join(',');

    const csv = `${headers}\n${exampleRow}`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'plantilla.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Área de carga */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileSelect}
          className="hidden"
        />

        <div className="space-y-4">
          <div className="text-4xl text-gray-400">📄</div>
          <div>
            <p className="text-lg font-medium text-gray-900">
              Arrastra tu archivo CSV aquí
            </p>
            <p className="text-sm text-gray-600">
              o{' '}
              <button
                type="button"
                className="text-blue-600 hover:text-blue-500"
                onClick={() => fileInputRef.current?.click()}
              >
                selecciona un archivo
              </button>
            </p>
          </div>
          <p className="text-xs text-gray-500">
            Máximo {maxFileSize}MB • Solo archivos CSV
          </p>
        </div>
      </div>

      {/* Botones de acción */}
      <div className="flex justify-between">
        <div>
          {downloadTemplate && templateColumns.length > 0 && (
            <Button
              variant="outline"
              onClick={handleDownloadTemplate}
            >
              📥 Descargar Plantilla
            </Button>
          )}
        </div>
        
        <Button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          {uploading ? 'Procesando...' : 'Seleccionar Archivo'}
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <div className="flex">
            <div className="text-red-400">⚠️</div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700 whitespace-pre-line">
                {error}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Vista previa */}
      {previewData && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-medium text-green-800">
                ✅ Archivo procesado correctamente
              </h3>
              <p className="text-sm text-green-600">
                {fileName} • {previewData.length} filas detectadas
              </p>
            </div>
            <div className="flex space-x-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setPreviewData(null);
                  setFileName('');
                }}
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={confirmUpload}
              >
                Confirmar Carga
              </Button>
            </div>
          </div>

          {/* Tabla de vista previa */}
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="bg-green-100">
                  {Object.keys(previewData[0]).map(key => (
                    <th key={key} className="px-2 py-1 text-left font-medium text-green-800">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData.map((row, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-green-25'}>
                    {Object.values(row).map((value, colIndex) => (
                      <td key={colIndex} className="px-2 py-1 text-green-700">
                        {String(value)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {previewData.length > 5 && (
            <p className="text-xs text-green-600 mt-2">
              Mostrando las primeras 5 filas de {previewData.length} total
            </p>
          )}
        </div>
      )}

      {/* Columnas esperadas */}
      {expectedColumns.length > 0 && (
        <div className="bg-gray-50 rounded-md p-3">
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            Columnas esperadas:
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {expectedColumns.map(col => (
              <div key={col.key} className="text-xs">
                <span className="font-medium">{col.label}</span>
                {col.required && <span className="text-red-500 ml-1">*</span>}
                {col.type && (
                  <span className="text-gray-500 ml-1">({col.type})</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
