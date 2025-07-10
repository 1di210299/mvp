import React, { useState, useCallback } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, X, Download, Settings } from 'lucide-react';

interface DataImportProps {
  onImportComplete?: (results: any) => void;
  importTypes?: Array<{
    value: string;
    label: string;
    description: string;
  }>;
}

interface ColumnMapping {
  sourceColumn: string;
  targetField: string;
  fieldType: string;
  isRequired: boolean;
  isEditable: boolean;
}

interface DetectedColumn {
  name: string;
  type: string;
  sampleValues: string[];
  stats?: any;
}

interface AvailableField {
  field_name: string;
  display_name: string;
  field_type: string;
  description: string;
  is_required: boolean;
  is_unique: boolean;
}

const DataImport: React.FC<DataImportProps> = ({ 
  onImportComplete,
  importTypes = [
    { value: 'products', label: 'Productos', description: 'Importar catálogo de productos' },
    { value: 'suppliers', label: 'Proveedores', description: 'Importar datos de proveedores' },
    { value: 'categories', label: 'Categorías', description: 'Importar categorías de productos' },
    { value: 'customers', label: 'Clientes', description: 'Importar base de datos de clientes' },
    { value: 'leads', label: 'Leads', description: 'Importar prospectos de ventas' },
  ]
}) => {
  const [currentStep, setCurrentStep] = useState<'upload' | 'mapping' | 'processing' | 'completed'>('upload');
  const [selectedImportType, setSelectedImportType] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [detectedColumns, setDetectedColumns] = useState<DetectedColumn[]>([]);
  const [availableFields, setAvailableFields] = useState<AvailableField[]>([]);
  const [columnMappings, setColumnMappings] = useState<ColumnMapping[]>([]);
  const [sampleData, setSampleData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [processingResults, setProcessingResults] = useState<any>(null);

  // Función para subir archivo
  const handleFileUpload = useCallback(async () => {
    if (!file || !selectedImportType) {
      setError('Por favor selecciona un archivo y tipo de importación');
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('import_type', selectedImportType);
    formData.append('header_row', '1');

    try {
      const response = await fetch('/api/data-import/api/sessions/upload_file/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Error al subir el archivo');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      await analyzeFile(data.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setIsLoading(false);
    }
  }, [file, selectedImportType]);

  // Función para analizar archivo
  const analyzeFile = useCallback(async (sessionId: number) => {
    try {
      const response = await fetch(`/api/data-import/api/sessions/${sessionId}/analyze_file/`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Error al analizar el archivo');
      }

      const data = await response.json();
      
      setDetectedColumns(data.detected_columns.map((col: string, index: number) => ({
        name: col,
        type: data.column_info?.[col]?.inferred_type || 'text',
        sampleValues: data.column_info?.[col]?.sample_values || [],
        stats: data.column_info?.[col]?.stats
      })));

      setAvailableFields(data.available_fields);
      setSampleData(data.sample_data);

      // Crear mapeos iniciales basados en sugerencias
      const initialMappings = data.detected_columns.map((col: string) => ({
        sourceColumn: col,
        targetField: data.suggested_mappings[col] || '',
        fieldType: data.column_info?.[col]?.inferred_type || 'text',
        isRequired: false,
        isEditable: true
      }));

      setColumnMappings(initialMappings);
      setCurrentStep('mapping');
      setShowModal(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al analizar archivo');
    }
  }, []);

  // Función para configurar mapeo
  const handleMappingConfiguration = useCallback(async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const mappings = columnMappings
        .filter(mapping => mapping.targetField)
        .map(mapping => ({
          source_column: mapping.sourceColumn,
          target_field: mapping.targetField,
          default_value: ''
        }));

      const response = await fetch(`/api/data-import/api/sessions/${sessionId}/configure_mapping/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          mappings
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al configurar mapeo');
      }

      setShowModal(false);
      await processImport();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al configurar mapeo');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, columnMappings]);

  // Función para procesar importación
  const processImport = useCallback(async () => {
    if (!sessionId) return;

    setCurrentStep('processing');
    setIsLoading(true);

    try {
      const response = await fetch(`/api/data-import/api/sessions/${sessionId}/process_import/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          skip_duplicates: true,
          update_existing: false,
          start_row: 2
        }),
      });

      if (!response.ok) {
        throw new Error('Error al procesar importación');
      }

      const data = await response.json();
      setProcessingResults(data.results);
      setCurrentStep('completed');
      
      if (onImportComplete) {
        onImportComplete(data.results);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al procesar importación');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, onImportComplete]);

  // Función para actualizar mapeo de columna
  const updateColumnMapping = useCallback((sourceColumn: string, targetField: string) => {
    setColumnMappings(prev =>
      prev.map(mapping =>
        mapping.sourceColumn === sourceColumn
          ? { ...mapping, targetField }
          : mapping
      )
    );
  }, []);

  // Función para reiniciar el proceso
  const resetImport = useCallback(() => {
    setCurrentStep('upload');
    setFile(null);
    setSessionId(null);
    setDetectedColumns([]);
    setAvailableFields([]);
    setColumnMappings([]);
    setSampleData([]);
    setError(null);
    setShowModal(false);
    setProcessingResults(null);
    setSelectedImportType('');
  }, []);

  // Renderizar paso de subida de archivo
  const renderUploadStep = () => (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <Upload className="mx-auto h-12 w-12 text-blue-500 mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Importar Datos
          </h2>
          <p className="text-gray-600">
            Sube tu archivo Excel o CSV para importar datos a tu sistema
          </p>
        </div>

        {/* Selección de tipo de importación */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Tipo de Importación
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {importTypes.map((type) => (
              <div
                key={type.value}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedImportType === type.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedImportType(type.value)}
              >
                <h3 className="font-medium text-gray-900">{type.label}</h3>
                <p className="text-sm text-gray-600 mt-1">{type.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Subida de archivo */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Archivo a Importar
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <FileText className="mx-auto h-8 w-8 text-gray-400 mb-2" />
              <p className="text-sm text-gray-600">
                {file ? file.name : 'Haz clic para seleccionar archivo o arrastra aquí'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Formatos soportados: Excel (.xlsx, .xls) y CSV
              </p>
            </label>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        <button
          onClick={handleFileUpload}
          disabled={!file || !selectedImportType || isLoading}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Analizando archivo...
            </>
          ) : (
            'Continuar'
          )}
        </button>
      </div>
    </div>
  );

  // Renderizar modal de mapeo de columnas
  const renderMappingModal = () => {
    const mappedFields = columnMappings.filter(m => m.targetField).map(m => m.targetField);
    const requiredFields = availableFields.filter(f => f.is_required);
    const missingRequired = requiredFields.filter(f => !mappedFields.includes(f.field_name));

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
          {/* Header del modal */}
          <div className="bg-gray-50 px-6 py-4 border-b flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Mapeo de Columnas
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Configura cómo se mapearán las columnas de tu archivo a los campos del sistema
              </p>
            </div>
            <button
              onClick={() => setShowModal(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="flex-1 overflow-auto p-6">
            {/* Información detectada */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">Columnas Detectadas</h4>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex items-center mb-2">
                  <CheckCircle className="h-5 w-5 text-blue-500 mr-2" />
                  <span className="text-blue-800 font-medium">
                    Se detectaron {detectedColumns.length} columnas en tu archivo
                  </span>
                </div>
                <p className="text-blue-700 text-sm">
                  Las columnas en <span className="font-medium text-green-600">verde</span> se 
                  mapearon automáticamente. Las columnas <span className="font-medium text-gray-600">grises</span> no 
                  encontraron relación automática.
                </p>
              </div>
            </div>

            {/* Tabla de mapeo */}
            <div className="overflow-x-auto">
              <table className="min-w-full border border-gray-200 rounded-lg">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 border-b">
                      Columna del Archivo
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 border-b">
                      Valores de Muestra
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 border-b">
                      Campo del Sistema
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 border-b">
                      Descripción
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {columnMappings.map((mapping, index) => {
                    const detectedCol = detectedColumns.find(col => col.name === mapping.sourceColumn);
                    const availableField = availableFields.find(f => f.field_name === mapping.targetField);
                    const isMapped = !!mapping.targetField;
                    const isRequired = availableField?.is_required;

                    return (
                      <tr key={index} className="border-b">
                        <td className="px-4 py-3">
                          <div className={`font-medium ${isMapped ? 'text-green-600' : 'text-gray-600'}`}>
                            {mapping.sourceColumn}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            Tipo: {detectedCol?.type || 'text'}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-sm text-gray-600">
                            {detectedCol?.sampleValues.slice(0, 3).map((value, idx) => (
                              <div key={idx} className="truncate max-w-32">
                                "{value}"
                              </div>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <select
                            value={mapping.targetField}
                            onChange={(e) => updateColumnMapping(mapping.sourceColumn, e.target.value)}
                            className={`w-full border rounded px-3 py-2 text-sm ${
                              mapping.isEditable 
                                ? 'border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
                                : 'border-gray-200 bg-gray-100 cursor-not-allowed'
                            }`}
                            disabled={!mapping.isEditable}
                          >
                            <option value="">-- No mapear --</option>
                            {availableFields.map((field) => (
                              <option key={field.field_name} value={field.field_name}>
                                {field.display_name} {field.is_required ? '*' : ''}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-sm text-gray-600">
                            {availableField?.description || 'Sin descripción'}
                            {isRequired && (
                              <span className="text-red-500 font-medium ml-1">
                                (Requerido)
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Campos faltantes */}
            {missingRequired.length > 0 && (
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center mb-2">
                  <AlertCircle className="h-5 w-5 text-yellow-500 mr-2" />
                  <span className="text-yellow-800 font-medium">
                    Campos Requeridos Faltantes
                  </span>
                </div>
                <p className="text-yellow-700 text-sm mb-2">
                  Los siguientes campos son obligatorios y deben ser mapeados:
                </p>
                <ul className="list-disc list-inside text-yellow-700 text-sm">
                  {missingRequired.map((field) => (
                    <li key={field.field_name}>
                      {field.display_name} - {field.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Footer del modal */}
          <div className="bg-gray-50 px-6 py-4 border-t flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {mappedFields.length} de {columnMappings.length} columnas mapeadas
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleMappingConfiguration}
                disabled={missingRequired.length > 0 || isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Procesando...
                  </>
                ) : (
                  'Iniciar Importación'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Renderizar paso de procesamiento
  const renderProcessingStep = () => (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8 text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Procesando Importación
        </h3>
        <p className="text-gray-600">
          Estamos importando tus datos. Este proceso puede tomar unos minutos...
        </p>
      </div>
    </div>
  );

  // Renderizar paso completado
  const renderCompletedStep = () => (
    <div className="max-w-2xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-6">
          <CheckCircle className="mx-auto h-16 w-16 text-green-500 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Importación Completada
          </h3>
        </div>

        {processingResults && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {processingResults.total_rows}
                </div>
                <div className="text-sm text-blue-800">Total Filas</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {processingResults.successful_rows}
                </div>
                <div className="text-sm text-green-800">Exitosas</div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {processingResults.failed_rows}
                </div>
                <div className="text-sm text-red-800">Con Error</div>
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Progreso</span>
                <span className="text-sm text-gray-600">
                  {processingResults.completion_percentage?.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${processingResults.completion_percentage}%` }}
                ></div>
              </div>
            </div>

            {processingResults.errors && processingResults.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h4 className="font-medium text-red-900 mb-2">Errores Encontrados</h4>
                <div className="max-h-32 overflow-y-auto">
                  {processingResults.errors.slice(0, 5).map((error: any, index: number) => (
                    <div key={index} className="text-sm text-red-700 mb-1">
                      Fila {error.row}: {error.error}
                    </div>
                  ))}
                  {processingResults.errors.length > 5 && (
                    <div className="text-sm text-red-600 mt-2">
                      ... y {processingResults.errors.length - 5} errores más
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex justify-center space-x-4 mt-6">
          <button
            onClick={resetImport}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Nueva Importación
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Ver Datos Importados
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {currentStep === 'upload' && renderUploadStep()}
      {currentStep === 'processing' && renderProcessingStep()}
      {currentStep === 'completed' && renderCompletedStep()}
      {showModal && renderMappingModal()}
    </div>
  );
};

export default DataImport;