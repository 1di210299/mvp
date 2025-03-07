// src/components/ImportarDatosModal.tsx

import React, { useState } from 'react';
import { X, Upload, Database, FileText, Settings, Check, CreditCard, Receipt, Store, ShoppingBag } from 'lucide-react';

type ModalStep = 'upload' | 'configure' | 'advanced' | 'confirm';

interface ImportarDatosModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (datasetInfo: any) => void;
}

const ImportarDatosModal: React.FC<ImportarDatosModalProps> = ({ isOpen, onClose, onSave }) => {
  // Estados del modal
  const [currentStep, setCurrentStep] = useState<ModalStep>('upload');
  const [nombreDataset, setNombreDataset] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [categoria, setCategoria] = useState('');
  const [tipoData, setTipoData] = useState<'ventas' | 'clientes' | 'productos' | 'otros'>('ventas');
  const [uploadMethod, setUploadMethod] = useState<'file' | 'api' | 'paste'>('file');
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [columns, setColumns] = useState<{ name: string; type: string }[]>([]);
  const [dataAccess, setDataAccess] = useState<'private' | 'team' | 'public'>('private');

  if (!isOpen) return null;

  // Maneja la carga del archivo
  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    setFilePreview(`${file.name} (${Math.round(file.size / 1024)} KB)`);
    
    // Simulación de extracción de columnas según el tipo de datos
    let mockColumns = [];
    
    if (tipoData === 'ventas') {
      mockColumns = [
        { name: 'fecha', type: 'date' },
        { name: 'documento', type: 'string' },
        { name: 'tipo_comprobante', type: 'string' },
        { name: 'cliente_id', type: 'number' },
        { name: 'producto_id', type: 'number' },
        { name: 'cantidad', type: 'number' },
        { name: 'precio_unitario', type: 'number' },
        { name: 'monto_total', type: 'number' },
        { name: 'igv', type: 'number' },
        { name: 'forma_pago', type: 'string' },
        { name: 'vendedor', type: 'string' },
        { name: 'sucursal', type: 'string' },
      ];
    } else if (tipoData === 'clientes') {
      mockColumns = [
        { name: 'cliente_id', type: 'number' },
        { name: 'tipo_documento', type: 'string' },
        { name: 'documento', type: 'string' },
        { name: 'nombres', type: 'string' },
        { name: 'apellidos', type: 'string' },
        { name: 'telefono', type: 'string' },
        { name: 'email', type: 'string' },
        { name: 'direccion', type: 'string' },
        { name: 'distrito', type: 'string' },
        { name: 'provincia', type: 'string' },
        { name: 'departamento', type: 'string' },
        { name: 'fecha_registro', type: 'date' },
      ];
    } else if (tipoData === 'productos') {
      mockColumns = [
        { name: 'producto_id', type: 'number' },
        { name: 'sku', type: 'string' },
        { name: 'nombre', type: 'string' },
        { name: 'descripcion', type: 'string' },
        { name: 'categoria', type: 'string' },
        { name: 'precio_costo', type: 'number' },
        { name: 'precio_venta', type: 'number' },
        { name: 'stock', type: 'number' },
        { name: 'unidad_medida', type: 'string' },
        { name: 'proveedor', type: 'string' },
        { name: 'fecha_ingreso', type: 'date' },
      ];
    } else {
      mockColumns = [
        { name: 'id', type: 'number' },
        { name: 'nombre', type: 'string' },
        { name: 'fecha', type: 'date' },
        { name: 'valor', type: 'number' },
        { name: 'categoria', type: 'string' },
      ];
    }
    
    setColumns(mockColumns);
  };

  // Evento para seleccionar archivo desde input
  const onFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileChange(file);
    }
  };

  // Soporte para arrastrar y soltar
  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      const file = event.dataTransfer.files[0];
      handleFileChange(file);
      event.dataTransfer.clearData();
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  // Guarda la información del dataset y resetea el estado
  const handleSave = () => {
    const datasetInfo = {
      nombre: nombreDataset,
      descripcion,
      categoria,
      tipoData,
      file: selectedFile,
      columns,
      access: dataAccess,
      createdAt: new Date(),
    };

    onSave(datasetInfo);
    onClose();
    // Resetea estados
    setCurrentStep('upload');
    setNombreDataset('');
    setDescripcion('');
    setCategoria('');
    setTipoData('ventas');
    setUploadMethod('file');
    setFilePreview(null);
    setSelectedFile(null);
    setColumns([]);
    setDataAccess('private');
  };

  // Renderiza el ícono de cada paso con estilos condicionales
  const renderStepIcon = (step: ModalStep, currentIcon: React.ReactNode) => (
    <div
      className={`flex items-center justify-center w-10 h-10 rounded-full ${
        currentStep === step 
          ? 'bg-cyber-cyan text-cyber-dark' 
          : 'bg-cyber-detail/70 text-cyber-text'
      }`}
    >
      {currentIcon}
    </div>
  );

  // Indicador de progreso de pasos
  const renderStepIndicator = () => (
    <div className="flex items-center justify-between mb-8" aria-label="Indicador de Progreso">
      <div className="flex flex-col items-center">
        {renderStepIcon('upload', <Upload size={20} />)}
        <span className="text-xs mt-1 font-medium text-cyber-text">Importar</span>
      </div>
      <div className="flex-1 h-0.5 mx-2 bg-cyber-detail/70">
        <div className={`h-full bg-cyber-cyan ${currentStep !== 'upload' ? 'w-full' : 'w-0'} transition-all duration-300`}></div>
      </div>
      <div className="flex flex-col items-center">
        {renderStepIcon('configure', <Database size={20} />)}
        <span className="text-xs mt-1 font-medium text-cyber-text">Configurar</span>
      </div>
      <div className="flex-1 h-0.5 mx-2 bg-cyber-detail/70">
        <div className={`h-full bg-cyber-cyan ${(currentStep === 'advanced' || currentStep === 'confirm') ? 'w-full' : 'w-0'} transition-all duration-300`}></div>
      </div>
      <div className="flex flex-col items-center">
        {renderStepIcon('advanced', <Settings size={20} />)}
        <span className="text-xs mt-1 font-medium text-cyber-text">Avanzado</span>
      </div>
      <div className="flex-1 h-0.5 mx-2 bg-cyber-detail/70">
        <div className={`h-full bg-cyber-cyan ${currentStep === 'confirm' ? 'w-full' : 'w-0'} transition-all duration-300`}></div>
      </div>
      <div className="flex flex-col items-center">
        {renderStepIcon('confirm', <Check size={20} />)}
        <span className="text-xs mt-1 font-medium text-cyber-text">Confirmar</span>
      </div>
    </div>
  );

  // Paso 1: Upload
  const renderUploadStep = () => (
    <div className="space-y-6 transition-opacity duration-300">
      <div className="space-y-2">
        <label htmlFor="nombreDataset" className="block text-sm font-medium text-cyber-text">
          Nombre del Dataset*
        </label>
        <input
          id="nombreDataset"
          type="text"
          value={nombreDataset}
          onChange={(e) => setNombreDataset(e.target.value)}
          className="w-full px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
          placeholder="Ej: Ventas Mensuales 2024"
          required
        />
      </div>
      
      <div className="space-y-2">
        <label htmlFor="descripcion" className="block text-sm font-medium text-cyber-text">
          Descripción
        </label>
        <textarea
          id="descripcion"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          className="w-full px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
          placeholder="Breve descripción de estos datos"
          rows={3}
        />
      </div>
      
      <div className="space-y-2">
        <label htmlFor="categoria" className="block text-sm font-medium text-cyber-text">
          Categoría
        </label>
        <select
          id="categoria"
          value={categoria}
          onChange={(e) => setCategoria(e.target.value)}
          className="w-full px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
        >
          <option value="">Selecciona una categoría</option>
          <option value="retail">Retail</option>
          <option value="restaurante">Restaurante/Cafetería</option>
          <option value="servicios">Servicios</option>
          <option value="manufactura">Manufactura</option>
          <option value="tecnologia">Tecnología</option>
          <option value="otro">Otro</option>
        </select>
      </div>
      
      <div className="space-y-2">
        <label className="block text-sm font-medium text-cyber-text">Tipo de Datos</label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            type="button"
            onClick={() => setTipoData('ventas')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-28 ${
              tipoData === 'ventas'
                ? 'border-cyber-cyan bg-cyber-detail/80 text-cyber-cyan'
                : 'border-cyber-detail bg-cyber-detail/30 text-cyber-text hover:bg-cyber-detail/50'
            }`}
          >
            <Receipt className="mb-2" size={24} />
            <span>Ventas</span>
            <span className="text-xs mt-1 opacity-70">
              Boletas, facturas, etc.
            </span>
          </button>
          
          <button
            type="button"
            onClick={() => setTipoData('clientes')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-28 ${
              tipoData === 'clientes'
                ? 'border-cyber-cyan bg-cyber-detail/80 text-cyber-cyan'
                : 'border-cyber-detail bg-cyber-detail/30 text-cyber-text hover:bg-cyber-detail/50'
            }`}
          >
            <Users className="mb-2" size={24} />
            <span>Clientes</span>
            <span className="text-xs mt-1 opacity-70">
              Datos demográficos
            </span>
          </button>
          
          <button
            type="button"
            onClick={() => setTipoData('productos')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-28 ${
              tipoData === 'productos'
                ? 'border-cyber-cyan bg-cyber-detail/80 text-cyber-cyan'
                : 'border-cyber-detail bg-cyber-detail/30 text-cyber-text hover:bg-cyber-detail/50'
            }`}
          >
            <ShoppingBag className="mb-2" size={24} />
            <span>Productos</span>
            <span className="text-xs mt-1 opacity-70">
              Inventario, SKUs
            </span>
          </button>
          
          <button
            type="button"
            onClick={() => setTipoData('otros')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-28 ${
              tipoData === 'otros'
                ? 'border-cyber-cyan bg-cyber-detail/80 text-cyber-cyan'
                : 'border-cyber-detail bg-cyber-detail/30 text-cyber-text hover:bg-cyber-detail/50'
            }`}
          >
            <Database className="mb-2" size={24} />
            <span>Otros</span>
            <span className="text-xs mt-1 opacity-70">
              Datos personalizados
            </span>
          </button>
        </div>
      </div>
      
      <div className="space-y-3">
        <label className="block text-sm font-medium text-cyber-text">Método de Importación</label>
        <div className="grid grid-cols-3 gap-3">
          <button
            type="button"
            onClick={() => setUploadMethod('file')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-24 ${
              uploadMethod === 'file'
                ? 'border-cyber-cyan bg-cyber-detail/80 text-cyber-cyan'
                : 'border-cyber-detail bg-cyber-detail/30 text-cyber-text hover:bg-cyber-detail/50'
            }`}
          >
            <Upload className="mb-2" size={20} />
            <span>Subir Archivo</span>
            <span className="text-xs mt-1 opacity-70">
              CSV, Excel, JSON
            </span>
          </button>
          
          <button
            type="button"
            onClick={() => setUploadMethod('api')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-24 ${
              uploadMethod === 'api'
                ? 'border-cyber-cyan bg-cyber-detail/80 text-cyber-cyan'
                : 'border-cyber-detail bg-cyber-detail/30 text-cyber-text hover:bg-cyber-detail/50'
            }`}
          >
            <Database className="mb-2" size={20} />
            <span>Conectar Sistema</span>
            <span className="text-xs mt-1 opacity-70">
              NubeFact, Siigo, SQL
            </span>
          </button>
          
          <button
            type="button"
            onClick={() => setUploadMethod('paste')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-24 ${
              uploadMethod === 'paste'
                ? 'border-cyber-cyan bg-cyber-detail/80 text-cyber-cyan'
                : 'border-cyber-detail bg-cyber-detail/30 text-cyber-text hover:bg-cyber-detail/50'
            }`}
          >
            <FileText className="mb-2" size={20} />
            <span>Pegar Datos</span>
            <span className="text-xs mt-1 opacity-70">
              Copiar y pegar
            </span>
          </button>
        </div>
        
        {uploadMethod === 'file' && (
          <div className="mt-4">
            <div
              className="border-2 border-dashed border-cyber-detail rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              tabIndex={0}
              role="button"
              aria-label="Zona para subir archivos"
            >
              {filePreview ? (
                <div className="text-center">
                  <p className="mb-2 text-cyber-cyan">{filePreview}</p>
                  <button
                    type="button"
                    onClick={() => {
                      setFilePreview(null);
                      setSelectedFile(null);
                    }}
                    className="text-sm text-cyber-text hover:text-cyber-cyan"
                  >
                    Quitar archivo
                  </button>
                </div>
              ) : (
                <>
                  <Upload className="w-10 h-10 mb-3 text-cyber-detail" />
                  <p className="mb-2 text-sm text-center text-cyber-text">
                    <span className="font-semibold">Haz clic para subir</span> o arrastra y suelta
                  </p>
                  <p className="text-xs text-cyber-text/70">Excel, CSV, JSON (hasta 10MB)</p>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".csv,.xlsx,.xls,.json"
                    onChange={onFileInputChange}
                  />
                  <label
                    htmlFor="file-upload"
                    className="mt-4 px-4 py-2 bg-cyber-detail text-cyber-text rounded cursor-pointer hover:bg-cyber-detail/70"
                  >
                    Seleccionar Archivo
                  </label>
                </>
              )}
            </div>
          </div>
        )}
        
        {uploadMethod === 'api' && (
          <div className="mt-4 space-y-4">
            <div className="border rounded-lg border-cyber-detail bg-cyber-detail/30 p-4">
              <h4 className="text-sm font-medium text-cyber-text mb-3">Conectar con Sistema Externo</h4>
              
              <div className="space-y-3">
                <div className="space-y-2">
                  <label className="block text-xs text-cyber-text/70">
                    Sistema
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-cyber-detail/50 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                  >
                    <option value="nubefact">NubeFact</option>
                    <option value="siigo">Siigo</option>
                    <option value="sunat">SUNAT Operaciones en Línea</option>
                    <option value="visanet">VisaNet Perú</option>
                    <option value="izipay">Izipay</option>
                    <option value="custom">Base de datos personalizada</option>
                  </select>
                </div>
                
                <div className="space-y-2">
                  <label className="block text-xs text-cyber-text/70">
                    URL o Endpoint
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-cyber-detail/50 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                    placeholder="https://api.example.com/v1"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <label className="block text-xs text-cyber-text/70">
                      Usuario o API Key
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 bg-cyber-detail/50 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                      placeholder="usuario"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="block text-xs text-cyber-text/70">
                      Contraseña o Token
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 bg-cyber-detail/50 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
                
                <button
                  type="button"
                  className="mt-2 w-full bg-cyber-detail text-cyber-text px-4 py-2 rounded hover:bg-cyber-detail/70 transition-colors"
                >
                  Probar Conexión
                </button>
              </div>
            </div>
          </div>
        )}
        
        {uploadMethod === 'paste' && (
          <div className="mt-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-cyber-text">
                Pega tus datos (CSV, JSON, texto)
              </label>
              <textarea
                className="w-full h-40 px-3 py-2 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan font-mono text-xs"
                placeholder="Pega tus datos aquí. Ej: para CSV:&#10;fecha,cliente,monto&#10;2024-01-01,Juan Pérez,120.50&#10;2024-01-02,María López,85.75"
              />
            </div>
            <p className="mt-1 text-xs text-cyber-text/70">Formato detectado: CSV</p>
          </div>
        )}
      </div>
    </div>
  );

  // Paso 2: Configure
  const renderConfigureStep = () => (
    <div className="space-y-6 transition-opacity duration-300">
      <div>
        <h3 className="text-lg font-medium text-cyber-text mb-4">Configuración de Columnas</h3>
        <div className="border border-cyber-detail rounded">
          <div className="grid grid-cols-12 bg-cyber-detail/80 p-3 rounded-t">
            <div className="col-span-5 font-medium text-cyber-text">Nombre de Columna</div>
            <div className="col-span-3 font-medium text-cyber-text">Tipo de Dato</div>
            <div className="col-span-2 font-medium text-cyber-text">Formatear</div>
            <div className="col-span-2 font-medium text-cyber-text">Requerido</div>
          </div>
          <div className="divide-y divide-cyber-detail">
            {columns.map((column, index) => (
              <div key={index} className="grid grid-cols-12 p-3 items-center">
                <div className="col-span-5">
                  <input
                    type="text"
                    value={column.name}
                    onChange={(e) => {
                      const newColumns = [...columns];
                      newColumns[index].name = e.target.value;
                      setColumns(newColumns);
                    }}
                    className="w-full px-2 py-1 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                  />
                </div>
                <div className="col-span-3">
                  <select
                    value={column.type}
                    onChange={(e) => {
                      const newColumns = [...columns];
                      newColumns[index].type = e.target.value;
                      setColumns(newColumns);
                    }}
                    className="w-full px-2 py-1 bg-cyber-detail/30 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
                  >
                    <option value="string">Texto</option>
                    <option value="number">Número</option>
                    <option value="date">Fecha</option>
                    <option value="boolean">Sí/No</option>
                    <option value="currency">Moneda (S/)</option>
                  </select>
                </div>
                <div className="col-span-2 flex justify-center">
                  <button 
                    type="button"
                    className="text-cyber-cyan hover:text-cyber-cyan/80 focus:outline-none"
                    title="Configurar formato"
                  >
                    <Settings size={16} />
                  </button>
                </div>
                <div className="col-span-2 flex justify-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
                    defaultChecked={
                      column.name === 'fecha' || 
                      column.name === 'cliente_id' || 
                      column.name === 'monto_total' ||
                      column.name === 'producto_id'
                    }
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium text-cyber-text mb-4">Vista Previa de Datos</h3>
        <div className="border border-cyber-detail rounded overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-cyber-detail">
              <thead className="bg-cyber-detail/80">
                <tr>
                  {columns.map((column, index) => (
                    <th
                      key={index}
                      className="px-4 py-3 text-left text-xs font-medium text-cyber-text uppercase tracking-wider"
                    >
                      {column.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-cyber-detail/30 divide-y divide-cyber-detail">
                {[...Array(3)].map((_, rowIndex) => (
                  <tr key={rowIndex}>
                    {columns.map((column, colIndex) => (
                      <td key={colIndex} className="px-4 py-2 whitespace-nowrap text-sm text-cyber-text">
                        {column.type === 'number'
                          ? Math.floor(Math.random() * 1000)
                          : column.type === 'date'
                          ? new Date(2024, Math.floor(Math.random() * 3), Math.floor(Math.random() * 28) + 1).toLocaleDateString('es-PE')
                          : column.type === 'boolean'
                          ? Math.random() > 0.5 ? 'Sí' : 'No'
                          : column.type === 'currency'
                          ? `S/ ${(Math.random() * 1000).toFixed(2)}`
                          : column.name.includes('cliente')
                          ? `Cliente ${rowIndex + 1}`
                          : column.name.includes('producto')
                          ? `Producto ${(rowIndex * 3) + colIndex + 1}`
                          : `Dato ${rowIndex + 1}`}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );

  // Paso 3: Advanced
  const renderAdvancedStep = () => (
    <div className="space-y-6 transition-opacity duration-300">
      <div>
        <h3 className="text-lg font-medium text-cyber-text mb-4">Transformaciones de Datos</h3>
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              id="normalize-dates"
              type="checkbox"
              className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
            />
            <label htmlFor="normalize-dates" className="ml-2 block text-sm text-cyber-text">
              Normalizar fechas al formato DD/MM/AAAA
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              id="format-currency"
              type="checkbox"
              className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
            />
            <label htmlFor="format-currency" className="ml-2 block text-sm text-cyber-text">
              Formatear montos como soles peruanos (S/)
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              id="replace-nulls"
              type="checkbox"
              className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
            />
            <label htmlFor="replace-nulls" className="ml-2 block text-sm text-cyber-text">
              Reemplazar valores nulos con valor por defecto
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              id="auto-tag"
              type="checkbox"
              className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
            />
            <label htmlFor="auto-tag" className="ml-2 block text-sm text-cyber-text">
              Auto-etiquetar datos basado en contenido (IA)
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              id="anomaly-detection"
              type="checkbox"
              className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
            />
            <label htmlFor="anomaly-detection" className="ml-2 block text-sm text-cyber-text">
              Detectar anomalías y valores atípicos
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              id="validation-sunat"
              type="checkbox"
              defaultChecked={tipoData === 'ventas' || tipoData === 'clientes'}
              className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
            />
            <label htmlFor="validation-sunat" className="ml-2 block text-sm text-cyber-text">
              Validar RUCs/DNIs con SUNAT (solo Perú)
            </label>
          </div>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium text-cyber-text mb-4">Permisos de Acceso</h3>
        <div className="space-y-3">
          <div className="flex items-center p-3 border border-cyber-detail rounded bg-cyber-detail/30 hover:bg-cyber-detail/50 cursor-pointer">
            <input
              id="private-access"
              name="access-permission"
              type="radio"
              className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan"
              checked={dataAccess === 'private'}
              onChange={() => setDataAccess('private')}
            />
            <label htmlFor="private-access" className="ml-3 block">
              <span className="block text-sm font-medium text-cyber-text">Privado</span>
              <span className="block text-xs text-cyber-text/70">Solo tú puedes acceder a estos datos</span>
            </label>
          </div>
          
          <div className="flex items-center p-3 border border-cyber-detail rounded bg-cyber-detail/30 hover:bg-cyber-detail/50 cursor-pointer">
            <input
              id="team-access"
              name="access-permission"
              type="radio"
              className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan"
              checked={dataAccess === 'team'}
              onChange={() => setDataAccess('team')}
            />
            <label htmlFor="team-access" className="ml-3 block">
              <span className="block text-sm font-medium text-cyber-text">Equipo</span>
              <span className="block text-xs text-cyber-text/70">Tu equipo puede acceder a estos datos</span>
            </label>
          </div>
          
          <div className="flex items-center p-3 border border-cyber-detail rounded bg-cyber-detail/30 hover:bg-cyber-detail/50 cursor-pointer">
            <input
              id="public-access"
              name="access-permission"
              type="radio"
              className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan"
              checked={dataAccess === 'public'}
              onChange={() => setDataAccess('public')}
            />
            <label htmlFor="public-access" className="ml-3 block">
              <span className="block text-sm font-medium text-cyber-text">Público</span>
              <span className="block text-xs text-cyber-text/70">Todos en tu organización pueden ver estos datos</span>
            </label>
          </div>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium text-cyber-text mb-4">Configuración Específica para Perú</h3>
        <div className="space-y-4 p-4 border border-cyber-detail rounded bg-cyber-detail/30">
          <div className="flex items-center">
            <CreditCard className="flex-shrink-0 h-5 w-5 text-cyber-cyan mr-2" />
            <div>
              <h4 className="text-sm font-medium text-cyber-text">Configuración de Facturación Electrónica</h4>
              <p className="text-xs text-cyber-text/70 mt-1">Habilita la integración con facturación electrónica de SUNAT</p>
            </div>
            <div className="ml-auto">
              <input
                type="checkbox"
                className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
              />
            </div>
          </div>
          
          <div className="flex items-center">
            <Store className="flex-shrink-0 h-5 w-5 text-cyber-cyan mr-2" />
            <div>
              <h4 className="text-sm font-medium text-cyber-text">Configuración Regional</h4>
              <p className="text-xs text-cyber-text/70 mt-1">Formato de moneda en soles peruanos (S/) y fechas DD/MM/AAAA</p>
            </div>
            <div className="ml-auto">
              <input
                type="checkbox"
                className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
                defaultChecked
              />
            </div>
          </div>
          
          <div className="flex items-center">
            <Receipt className="flex-shrink-0 h-5 w-5 text-cyber-cyan mr-2" />
            <div>
              <h4 className="text-sm font-medium text-cyber-text">Análisis Fiscal</h4>
              <p className="text-xs text-cyber-text/70 mt-1">Habilita análisis automático para IGV, impuesto a la renta y detracciones</p>
            </div>
            <div className="ml-auto">
              <input
                type="checkbox"
                className="h-4 w-4 text-cyber-cyan focus:ring-cyber-cyan border-cyber-detail rounded"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Paso 4: Confirm
  const renderConfirmStep = () => (
    <div className="space-y-6 transition-opacity duration-300">
      <div className="bg-cyber-detail/30 p-4 rounded border border-cyber-detail">
        <h3 className="text-lg font-medium text-cyber-text mb-4">Resumen del Dataset</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-cyber-text/70 mb-1">Nombre</p>
            <p className="text-cyber-text">{nombreDataset || 'No especificado'}</p>
          </div>
          <div>
            <p className="text-sm text-cyber-text/70 mb-1">Categoría</p>
            <p className="text-cyber-text capitalize">{categoria || 'No especificado'}</p>
          </div>
          <div>
            <p className="text-sm text-cyber-text/70 mb-1">Tipo de Datos</p>
            <p className="text-cyber-text capitalize">{tipoData}</p>
          </div>
          <div>
            <p className="text-sm text-cyber-text/70 mb-1">Método de Importación</p>
            <p className="text-cyber-text capitalize">
              {uploadMethod === 'file' ? 'Archivo' : uploadMethod === 'api' ? 'Conexión API/DB' : 'Datos Pegados'}
            </p>
          </div>
          <div>
            <p className="text-sm text-cyber-text/70 mb-1">Archivo</p>
            <p className="text-cyber-text">{selectedFile?.name || 'No seleccionado'}</p>
          </div>
          <div>
            <p className="text-sm text-cyber-text/70 mb-1">Columnas</p>
            <p className="text-cyber-text">{columns.length}</p>
          </div>
          <div>
            <p className="text-sm text-cyber-text/70 mb-1">Acceso</p>
            <p className="text-cyber-text capitalize">
              {dataAccess === 'private' ? 'Privado' : dataAccess === 'team' ? 'Equipo' : 'Público'}
            </p>
          </div>
          <div>
            <p className="text-sm text-cyber-text/70 mb-1">Configuración Perú</p>
            <p className="text-cyber-text">Activa</p>
          </div>
        </div>
        <div className="mt-4">
          <p className="text-sm text-cyber-text/70 mb-1">Descripción</p>
          <p className="text-cyber-text">{descripcion || 'No se proporcionó descripción'}</p>
        </div>
      </div>
      
      <div className="bg-cyber-detail/30 p-4 rounded border border-cyber-detail">
        <h3 className="text-lg font-medium text-cyber-text mb-4">¿Qué sigue?</h3>
        <div className="space-y-3">
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 text-cyber-cyan">
              <Check size={20} />
            </div>
            <p className="ml-3 text-sm text-cyber-text">
              Explorar los datos en formato tabla con filtros
            </p>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 text-cyber-cyan">
              <Check size={20} />
            </div>
            <p className="ml-3 text-sm text-cyber-text">
              Generar visualizaciones automáticas adaptadas para MYPES peruanas
            </p>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 text-cyber-cyan">
              <Check size={20} />
            </div>
            <p className="ml-3 text-sm text-cyber-text">
              Aplicar modelos de IA para obtener insights sobre tus datos de ventas
            </p>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 text-cyber-cyan">
              <Check size={20} />
            </div>
            <p className="ml-3 text-sm text-cyber-text">
              Obtener recomendaciones específicas para tu negocio en Perú
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div
      className="fixed inset-0 z-50 overflow-auto bg-black/60 backdrop-blur-sm flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-cyber-dark/90 border border-cyber-cyan/30 rounded-lg shadow-lg w-full max-w-3xl mx-4 overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b border-cyber-detail">
          <h2 id="modal-title" className="text-xl font-semibold text-cyber-text">
            {currentStep === 'upload' && 'Importar Datos'}
            {currentStep === 'configure' && 'Configurar Columnas'}
            {currentStep === 'advanced' && 'Opciones Avanzadas'}
            {currentStep === 'confirm' && 'Confirmar Dataset'}
          </h2>
          <button onClick={onClose} aria-label="Cerrar Modal" className="text-cyber-text/70 hover:text-cyber-text">
            <X size={20} />
          </button>
        </div>
        <div className="p-6">
          {renderStepIndicator()}
          {currentStep === 'upload' && renderUploadStep()}
          {currentStep === 'configure' && renderConfigureStep()}
          {currentStep === 'advanced' && renderAdvancedStep()}
          {currentStep === 'confirm' && renderConfirmStep()}
        </div>
        <div className="flex justify-between items-center p-4 border-t border-cyber-detail bg-cyber-detail/20">
          <button
            type="button"
            onClick={() => {
              if (currentStep === 'upload') onClose();
              else if (currentStep === 'configure') setCurrentStep('upload');
              else if (currentStep === 'advanced') setCurrentStep('configure');
              else if (currentStep === 'confirm') setCurrentStep('advanced');
            }}
            className="px-4 py-2 border border-cyber-detail text-cyber-text bg-transparent hover:bg-cyber-detail/40 rounded"
          >
            {currentStep === 'upload' ? 'Cancelar' : 'Atrás'}
          </button>
          <button
            type="button"
            onClick={() => {
              if (currentStep === 'upload') setCurrentStep('configure');
              else if (currentStep === 'configure') setCurrentStep('advanced');
              else if (currentStep === 'advanced') setCurrentStep('confirm');
              else if (currentStep === 'confirm') handleSave();
            }}
            disabled={currentStep === 'upload' && !nombreDataset}
            className={`px-4 py-2 bg-cyber-cyan text-cyber-dark hover:bg-cyber-cyan/90 rounded ${
              currentStep === 'upload' && !nombreDataset ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {currentStep === 'confirm' ? 'Guardar Dataset' : 'Siguiente'}
          </button>
        </div>
      </div>
    </div>
  );
};

import { Users } from 'lucide-react';

export default ImportarDatosModal;