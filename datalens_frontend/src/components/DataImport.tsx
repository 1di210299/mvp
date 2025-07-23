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
  // Campos mejorados por IA
  ai_description?: string;
  ai_example?: string;
  ai_tips?: string;
}

const DataImport: React.FC<DataImportProps> = ({ 
  onImportComplete,
  importTypes = [
    { value: 'products', label: 'Productos', description: 'Importar catálogo de productos' },
    { value: 'suppliers', label: 'Proveedores', description: 'Importar datos de proveedores' },
    { value: 'categories', label: 'Categorías', description: 'Importar categorías de productos' },
    { value: 'customers', label: 'Clientes', description: 'Importar base de datos de clientes' },
    { value: 'leads', label: 'Leads', description: 'Importar prospectos de ventas' },
    { value: 'sales', label: 'Ventas', description: 'Importar transacciones de ventas' },
    { value: 'purchases', label: 'Compras', description: 'Importar órdenes de compra' },
    { value: 'inventory', label: 'Inventario', description: 'Importar niveles de stock' },
    { value: 'auto', label: '🇵🇪 Auto-detectar Inteligente', description: 'Sistema híbrido: Patrones + OpenAI para empresas peruanas' },
  ]
}) => {
  console.log('🚀 FRONTEND: DataImport component iniciado');
  console.log('📋 FRONTEND: Tipos de importación disponibles:', importTypes);
  
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

  // Función para detectar automáticamente el tipo de datos (Sistema híbrido: Patrones + OpenAI)
  const detectDataType = useCallback(async (file: File) => {
    console.log('🤖🇵🇪 FRONTEND: Iniciando detección automática híbrida de tipo de datos...');
    console.log('📊 FRONTEND: Usando sistema de patrones + OpenAI para empresa peruana');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('header_row', '1');
    formData.append('use_openai', 'true'); // Activar detección con OpenAI
    formData.append('country_context', 'peru'); // Contexto peruano
    
    try {
      const token = localStorage.getItem('access_token');
      console.log('🌐 FRONTEND: Enviando a detección híbrida...');
      
      const response = await fetch('http://localhost:8080/api/data-import/sessions/detect_type/', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('🤖 FRONTEND: Detección por patrones:', data.pattern_detection);
        console.log('🧠 FRONTEND: Detección por OpenAI:', data.openai_detection);
        console.log('⚡ FRONTEND: Resultado final:', data.detected_type);
        console.log('📊 FRONTEND: Confianza combinada:', data.confidence);
        console.log('🎯 FRONTEND: Razones:', data.reasons);
        
        setSelectedImportType(data.detected_type);
        
        // Mostrar información detallada al usuario
        const detectionInfo = [
          `🎯 Tipo detectado: ${data.detected_type_label}`,
          `📊 Confianza: ${data.confidence}%`,
          `🤖 Patrones: ${data.pattern_detection?.detected_type || 'No detectado'}`,
          `🧠 OpenAI: ${data.openai_detection?.detected_type || 'No usado'}`,
          `📝 Contexto: Empresa peruana`
        ];
        
        console.log('🇵🇪 FRONTEND: Detección completa:', detectionInfo.join(' | '));
        
        // Mostrar popup informativo si OpenAI dio una sugerencia diferente
        if (data.openai_detection && data.pattern_detection && 
            data.openai_detection.detected_type !== data.pattern_detection.detected_type) {
          console.log('⚠️ FRONTEND: Discrepancia detectada entre métodos');
          const confirmMessage = `🤖 Detección híbrida:\n\n` +
            `🔍 Patrones encontraron: ${data.pattern_detection.detected_type}\n` +
            `🧠 OpenAI sugiere: ${data.openai_detection.detected_type}\n` +
            `📊 Confianza final: ${data.confidence}%\n\n` +
            `¿Continuar con: ${data.detected_type_label}?`;
          
          if (!confirm(confirmMessage)) {
            return null; // Usuario decidió no continuar
          }
        }
        
        return data.detected_type;
      } else {
        console.warn('🤖 FRONTEND: Detección híbrida falló, intentando solo patrones...');
        // Fallback: intentar solo con patrones
        return await detectDataTypePattern(file);
      }
    } catch (error) {
      console.warn('🤖 FRONTEND: Error en detección híbrida:', error);
      console.log('🔄 FRONTEND: Intentando fallback con solo patrones...');
      return await detectDataTypePattern(file);
    }
  }, []);

  // Función de fallback: detección solo por patrones
  const detectDataTypePattern = useCallback(async (file: File) => {
    console.log('🔍 FRONTEND: Usando solo detección por patrones...');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('header_row', '1');
    formData.append('use_openai', 'false'); // Solo patrones
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8080/api/data-import/sessions/detect_type/', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('🔍 FRONTEND: Detección por patrones exitosa:', data.detected_type);
        return data.detected_type;
      }
    } catch (error) {
      console.warn('🔍 FRONTEND: Error en detección por patrones:', error);
    }
    
    return null;
  }, []);

  // Función para subir archivo (modificada para auto-detección)
  const handleFileUpload = useCallback(async () => {
    console.log('🔄 FRONTEND: Iniciando proceso de subida de archivo...');
    console.log('📁 FRONTEND: Archivo seleccionado:', file?.name, 'Tamaño:', file?.size);
    console.log('📋 FRONTEND: Tipo de importación:', selectedImportType);
    console.log('🔧 FRONTEND: Estado completo - isLoading:', isLoading, 'error:', error);
    
    // Verificación detallada de condiciones
    if (!file) {
      console.error('❌ FRONTEND: No hay archivo seleccionado');
      setError('Por favor selecciona un archivo');
      return;
    }

    console.log('✅ FRONTEND: Archivo validado correctamente');

    // Si se seleccionó auto-detectar, intentar detectar el tipo primero
    let finalImportType = selectedImportType;
    if (selectedImportType === 'auto') {
      console.log('🤖 FRONTEND: Auto-detección activada...');
      setIsLoading(true); // Activar loading para auto-detección
      const detectedType = await detectDataType(file);
      if (detectedType) {
        finalImportType = detectedType;
        console.log('✅ FRONTEND: Usando tipo detectado:', finalImportType);
      } else {
        setError('No se pudo detectar automáticamente el tipo de datos. Por favor selecciona manualmente.');
        setIsLoading(false);
        return;
      }
    }

    if (!finalImportType) {
      console.error('❌ FRONTEND: No hay tipo de importación seleccionado');
      setError('Por favor selecciona un tipo de importación');
      return;
    }

    console.log('🚀 FRONTEND: Todas las validaciones pasadas, procediendo con upload...');
    
    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('import_type', finalImportType);
    formData.append('header_row', '2'); // Usamos fila 2 para tu archivo específico
    
    console.log('📤 FRONTEND: Enviando FormData con:', {
      file: file.name,
      import_type: finalImportType,
      header_row: '2'
    });

    try {
      const token = localStorage.getItem('access_token');
      console.log('🔑 FRONTEND: Token presente:', !!token);
      console.log('🌐 FRONTEND: Enviando request a:', 'http://localhost:8080/api/data-import/sessions/upload_file/');
      
      const response = await fetch('http://localhost:8080/api/data-import/sessions/upload_file/', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('📥 FRONTEND: Response status:', response.status);
      console.log('📥 FRONTEND: Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ FRONTEND: Error response:', errorText);
        throw new Error(`Error al subir el archivo: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ FRONTEND: Upload exitoso, datos recibidos:', data);
      setSessionId(data.session_id);
      await analyzeFile(data.session_id);
    } catch (err) {
      console.error('❌ FRONTEND: Error en handleFileUpload:', err);
      setError(err instanceof Error ? err.message : 'Error desconocido al subir archivo');
    } finally {
      console.log('🏁 FRONTEND: Finalizando proceso de upload');
      setIsLoading(false);
    }
  }, [file, selectedImportType, detectDataType]);

  // Función para analizar archivo
  const analyzeFile = useCallback(async (sessionId: number) => {
    console.log('🔍 FRONTEND: Iniciando análisis de archivo para session:', sessionId);
    
    try {
      const token = localStorage.getItem('access_token');
      console.log('🔑 FRONTEND: Token para análisis presente:', !!token);
      console.log('🌐 FRONTEND: Enviando request a:', `http://localhost:8080/api/data-import/sessions/${sessionId}/analyze_file/`);
      
      const response = await fetch(`http://localhost:8080/api/data-import/sessions/${sessionId}/analyze_file/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('📥 FRONTEND: Analyze response status:', response.status);
      console.log('📥 FRONTEND: Analyze response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ FRONTEND: Error en analyze response:', errorText);
        throw new Error(`Error al analizar el archivo: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ FRONTEND: Análisis exitoso, datos recibidos:', data);
      console.log('📊 FRONTEND: Columnas detectadas:', data.detected_columns);
      console.log('🔧 FRONTEND: Campos disponibles:', data.available_fields);
      console.log('💡 FRONTEND: Mapeos sugeridos:', data.suggested_mappings);
      
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

      console.log('🗂️ FRONTEND: Mapeos iniciales creados:', initialMappings);
      setColumnMappings(initialMappings);
      setCurrentStep('mapping');
      setShowModal(true);
    } catch (err) {
      console.error('❌ FRONTEND: Error en analyzeFile:', err);
      setError(err instanceof Error ? err.message : 'Error al analizar archivo');
    }
  }, []);

  // Función para configurar mapeo
  const handleMappingConfiguration = useCallback(async () => {
    console.log('🔧 FRONTEND: Iniciando configuración de mapeo para session:', sessionId);
    
    if (!sessionId) {
      console.error('❌ FRONTEND: No hay sessionId para configurar mapeo');
      return;
    }

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

      console.log('📋 FRONTEND: Mapeos a enviar:', mappings);
      console.log('🌐 FRONTEND: Enviando request a:', `http://localhost:8080/api/data-import/sessions/${sessionId}/configure_mapping/`);

      const token = localStorage.getItem('access_token');
      console.log('🔑 FRONTEND: Token para mapeo presente:', !!token);

      const response = await fetch(`http://localhost:8080/api/data-import/sessions/${sessionId}/configure_mapping/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          mappings
        }),
      });

      console.log('📥 FRONTEND: Mapping response status:', response.status);
      console.log('📥 FRONTEND: Mapping response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ FRONTEND: Error en mapping response:', errorData);
        throw new Error(errorData.error || 'Error al configurar mapeo');
      }

      console.log('✅ FRONTEND: Mapeo configurado exitosamente');
      setShowModal(false);
      await processImport();
    } catch (err) {
      console.error('❌ FRONTEND: Error en handleMappingConfiguration:', err);
      setError(err instanceof Error ? err.message : 'Error al configurar mapeo');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, columnMappings]);

  // Función para procesar importación
  const processImport = useCallback(async () => {
    console.log('⚙️ FRONTEND: Iniciando procesamiento de importación para session:', sessionId);
    
    if (!sessionId) {
      console.error('❌ FRONTEND: No hay sessionId para procesar importación');
      return;
    }

    setCurrentStep('processing');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      console.log('🔑 FRONTEND: Token para procesamiento presente:', !!token);
      console.log('🌐 FRONTEND: Enviando request a:', `http://localhost:8080/api/data-import/sessions/${sessionId}/process_import/`);
      
      const processData = {
        session_id: sessionId,
        skip_duplicates: true,
        update_existing: false,
        start_row: 2
      };
      
      console.log('📋 FRONTEND: Datos de procesamiento:', processData);

      const response = await fetch(`http://localhost:8080/api/data-import/sessions/${sessionId}/process_import/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(processData),
      });

      console.log('📥 FRONTEND: Process response status:', response.status);
      console.log('📥 FRONTEND: Process response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ FRONTEND: Error en process response:', errorText);
        throw new Error(`Error al procesar importación: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ FRONTEND: Procesamiento exitoso, resultados:', data);
      setProcessingResults(data.results);
      setCurrentStep('completed');
      
      if (onImportComplete) {
        console.log('📤 FRONTEND: Llamando callback de importación completada');
        onImportComplete(data.results);
      }
    } catch (err) {
      console.error('❌ FRONTEND: Error en processImport:', err);
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

  // Función de debug para probar conexión
  const testBackendConnection = async () => {
    console.log('🧪 FRONTEND: Probando conexión al backend...');
    try {
      const response = await fetch('http://localhost:8080/api/data-import/sessions/', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      console.log('🧪 FRONTEND: Status de prueba:', response.status);
      const data = await response.text();
      console.log('🧪 FRONTEND: Respuesta de prueba:', data);
      alert(`Conexión: ${response.status} - Ver consola para más detalles`);
    } catch (error) {
      console.error('🧪 FRONTEND: Error de conexión:', error);
      alert(`Error: ${error instanceof Error ? error.message : 'Error desconocido'}`);
    }
  };

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
          
          {/* Botón de debug */}
          <button
            onClick={testBackendConnection}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            🧪 PROBAR CONEXIÓN BACKEND
          </button>
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
                onClick={() => {
                  console.log('📋 FRONTEND: Tipo de importación seleccionado:', type.value, type.label);
                  setSelectedImportType(type.value);
                }}
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
              onChange={(e) => {
                const selectedFile = e.target.files?.[0] || null;
                console.log('📁 FRONTEND: Archivo seleccionado:', selectedFile?.name, 'Tipo:', selectedFile?.type, 'Tamaño:', selectedFile?.size);
                setFile(selectedFile);
                if (selectedFile) {
                  console.log('✅ FRONTEND: Archivo establecido en estado');
                } else {
                  console.log('❌ FRONTEND: No se seleccionó archivo');
                }
              }}
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

        {/* Indicador de estado */}
        <div className="mb-4 p-3 bg-gray-100 rounded-lg">
          <div className="text-sm text-gray-700 space-y-1">
            <div className="flex items-center">
              {file ? '✅' : '❌'} 
              <span className="ml-2">Archivo: {file ? file.name : 'No seleccionado'}</span>
            </div>
            <div className="flex items-center">
              {selectedImportType ? '✅' : '❌'} 
              <span className="ml-2">Tipo de importación: {selectedImportType ? selectedImportType : 'No seleccionado'}</span>
            </div>
            {(!file || !selectedImportType) && (
              <div className="text-red-600 font-medium mt-2">
                ⚠️ {!file && !selectedImportType ? 'Selecciona un archivo y tipo de importación' : 
                     !file ? 'Selecciona un archivo' : 'Selecciona un tipo de importación'}
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        <button
          onClick={() => {
            console.log('🖱️ FRONTEND: Botón de upload clickeado');
            console.log('📋 FRONTEND: Estado actual - file:', !!file, 'selectedImportType:', selectedImportType, 'isLoading:', isLoading);
            console.log('🔒 FRONTEND: Botón deshabilitado?', !file || (!selectedImportType) || isLoading);
            console.log('📁 FRONTEND: ¿Hay archivo?', !!file);
            console.log('📋 FRONTEND: ¿Tipo seleccionado?', !!selectedImportType);
            console.log('⏳ FRONTEND: ¿Está cargando?', isLoading);
            
            if (!file) {
              console.error('❌ FRONTEND: No se puede proceder - falta archivo');
              return;
            }
            if (!selectedImportType) {
              console.error('❌ FRONTEND: No se puede proceder - falta tipo de importación');
              alert('Por favor selecciona un tipo de importación antes de continuar');
              return;
            }
            if (isLoading) {
              console.error('❌ FRONTEND: No se puede proceder - ya está cargando');
              return;
            }
            
            console.log('✅ FRONTEND: Llamando handleFileUpload...');
            handleFileUpload();
          }}
          disabled={!file || (!selectedImportType) || isLoading}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              {selectedImportType === 'auto' ? 'Analizando con IA + Patrones...' : 'Analizando archivo...'}
            </>
          ) : (
            selectedImportType === 'auto' ? '🇵🇪 Detectar Inteligentemente' : 'Continuar'
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
        <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
          {/* Header del modal */}
          <div className="bg-gray-50 px-6 py-4 border-b flex items-center justify-between flex-shrink-0">
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

          {/* Contenido scrolleable */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-6">
              {/* Banner de IA mejorada */}
            {availableFields.some(field => field.ai_description) && (
              <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
                <div className="flex items-center mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-2xl">🧠</span>
                    <span className="font-semibold text-purple-800">IA Empresarial Peruana Activada</span>
                  </div>
                </div>
                <p className="text-purple-700 text-sm">
                  Los campos han sido analizados y mejorados con inteligencia artificial especializada en empresas peruanas. 
                  Verás descripciones más precisas, ejemplos locales y consejos específicos para cada campo.
                </p>
                <div className="mt-2 flex items-center space-x-4 text-xs text-purple-600">
                  <span>🇵🇪 Contexto peruano</span>
                  <span>📝 Ejemplos locales</span>
                  <span>💡 Consejos inteligentes</span>
                  <span>⚡ Mapeo automático</span>
                </div>
              </div>
            )}

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
                          <div className="text-sm text-gray-600 space-y-2">
                            {/* Descripción principal (IA o fallback) */}
                            <div className="font-medium text-gray-900">
                              {availableField?.description || 'Sin descripción'}
                            </div>
                            
                            {/* Ejemplo de IA si está disponible */}
                            {availableField?.ai_example && (
                              <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                                📝 Ejemplo: {availableField.ai_example}
                              </div>
                            )}
                            
                            {/* Tips de IA si están disponibles */}
                            {availableField?.ai_tips && (
                              <div className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                                💡 Tip: {availableField.ai_tips}
                              </div>
                            )}
                            
                            {/* Indicador de campo requerido */}
                            {isRequired && (
                              <span className="inline-flex items-center text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                                ⚠️ Campo obligatorio
                              </span>
                            )}
                            
                            {/* Indicador de que fue mejorado por IA */}
                            {availableField?.ai_description && (
                              <span className="inline-flex items-center text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded">
                                🧠 Mejorado por IA
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
            </div> {/* Cerrar div de contenido con padding */}
          </div> {/* Cerrar div scrolleable */}

          {/* Footer del modal */}
          <div className="bg-gray-50 px-6 py-4 border-t flex items-center justify-between flex-shrink-0">
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