// src/components/AddDatasetModal.tsx

import React, { useState } from 'react';
import { X, Upload, Database, FileText, Settings, Check } from 'lucide-react';

type ModalStep = 'upload' | 'configure' | 'advanced' | 'confirm';

interface AddDatasetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (datasetInfo: any) => void;
}

const AddDatasetModal: React.FC<AddDatasetModalProps> = ({ isOpen, onClose, onSave }) => {
  // Estados del modal
  const [currentStep, setCurrentStep] = useState<ModalStep>('upload');
  const [datasetName, setDatasetName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
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
    // Simulación de extracción de columnas
    const mockColumns = [
      { name: 'id', type: 'number' },
      { name: 'name', type: 'string' },
      { name: 'date', type: 'date' },
      { name: 'value', type: 'number' },
      { name: 'category', type: 'string' },
    ];
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
      name: datasetName,
      description,
      category,
      file: selectedFile,
      columns,
      access: dataAccess,
      createdAt: new Date(),
    };

    onSave(datasetInfo);
    onClose();
    // Resetea estados
    setCurrentStep('upload');
    setDatasetName('');
    setDescription('');
    setCategory('');
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
          ? 'bg-[#00B8D9] text-[#1E2A38]' 
          : 'bg-[#2F3C48] text-[#E6E6E6]'
      }`}
    >
      {currentIcon}
    </div>
  );

  // Indicador de progreso de pasos
  const renderStepIndicator = () => (
    <div className="flex items-center justify-between mb-8" aria-label="Progress Indicator">
      <div className="flex flex-col items-center">
        {renderStepIcon('upload', <Upload size={20} />)}
        <span className="text-xs mt-1 font-medium text-[#E6E6E6]">Upload</span>
      </div>
      <div className="flex-1 h-0.5 mx-2 bg-[#2F3C48]">
        <div className={`h-full bg-[#00B8D9] ${currentStep !== 'upload' ? 'w-full' : 'w-0'} transition-all duration-300`}></div>
      </div>
      <div className="flex flex-col items-center">
        {renderStepIcon('configure', <Database size={20} />)}
        <span className="text-xs mt-1 font-medium text-[#E6E6E6]">Configure</span>
      </div>
      <div className="flex-1 h-0.5 mx-2 bg-[#2F3C48]">
        <div className={`h-full bg-[#00B8D9] ${(currentStep === 'advanced' || currentStep === 'confirm') ? 'w-full' : 'w-0'} transition-all duration-300`}></div>
      </div>
      <div className="flex flex-col items-center">
        {renderStepIcon('advanced', <Settings size={20} />)}
        <span className="text-xs mt-1 font-medium text-[#E6E6E6]">Advanced</span>
      </div>
      <div className="flex-1 h-0.5 mx-2 bg-[#2F3C48]">
        <div className={`h-full bg-[#00B8D9] ${currentStep === 'confirm' ? 'w-full' : 'w-0'} transition-all duration-300`}></div>
      </div>
      <div className="flex flex-col items-center">
        {renderStepIcon('confirm', <Check size={20} />)}
        <span className="text-xs mt-1 font-medium text-[#E6E6E6]">Confirm</span>
      </div>
    </div>
  );

  // Paso 1: Upload
  const renderUploadStep = () => (
    <div className="space-y-6 transition-opacity duration-300">
      <div className="space-y-2">
        <label htmlFor="datasetName" className="block text-sm font-medium text-[#E6E6E6]">
          Dataset Name*
        </label>
        <input
          id="datasetName"
          type="text"
          value={datasetName}
          onChange={(e) => setDatasetName(e.target.value)}
          className="w-full px-3 py-2 bg-[#2F3C48]/50 border border-[#2F3C48] text-[#E6E6E6] rounded focus:outline-none focus:ring-1 focus:ring-[#00B8D9]"
          placeholder="Enter dataset name"
          required
        />
      </div>
      <div className="space-y-2">
        <label htmlFor="description" className="block text-sm font-medium text-[#E6E6E6]">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 bg-[#2F3C48]/50 border border-[#2F3C48] text-[#E6E6E6] rounded focus:outline-none focus:ring-1 focus:ring-[#00B8D9]"
          placeholder="Brief description of this dataset"
          rows={3}
        />
      </div>
      <div className="space-y-2">
        <label htmlFor="category" className="block text-sm font-medium text-[#E6E6E6]">
          Category
        </label>
        <select
          id="category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full px-3 py-2 bg-[#2F3C48]/50 border border-[#2F3C48] text-[#E6E6E6] rounded focus:outline-none focus:ring-1 focus:ring-[#00B8D9]"
        >
          <option value="">Select a category</option>
          <option value="finance">Finance</option>
          <option value="sales">Sales</option>
          <option value="marketing">Marketing</option>
          <option value="health">Health</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div className="space-y-3">
        <label className="block text-sm font-medium text-[#E6E6E6]">Upload Method</label>
        <div className="grid grid-cols-3 gap-3">
          <button
            type="button"
            onClick={() => setUploadMethod('file')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-28 ${
              uploadMethod === 'file'
                ? 'border-[#00B8D9] bg-[#2F3C48]/80 text-[#00B8D9]'
                : 'border-[#2F3C48] bg-[#2F3C48]/30 text-[#E6E6E6] hover:bg-[#2F3C48]/50'
            }`}
          >
            <Upload className="mb-2" size={24} />
            <span>Upload File</span>
            <span className="text-xs mt-1 opacity-70">
              CSV, Excel, JSON, Parquet
            </span>
          </button>
          <button
            type="button"
            onClick={() => setUploadMethod('api')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-28 ${
              uploadMethod === 'api'
                ? 'border-[#00B8D9] bg-[#2F3C48]/80 text-[#00B8D9]'
                : 'border-[#2F3C48] bg-[#2F3C48]/30 text-[#E6E6E6] hover:bg-[#2F3C48]/50'
            }`}
          >
            <Database className="mb-2" size={24} />
            <span>Connect API/DB</span>
            <span className="text-xs mt-1 opacity-70">SQL, AWS, BigQuery</span>
          </button>
          <button
            type="button"
            onClick={() => setUploadMethod('paste')}
            className={`p-4 border rounded flex flex-col items-center justify-center text-center h-28 ${
              uploadMethod === 'paste'
                ? 'border-[#00B8D9] bg-[#2F3C48]/80 text-[#00B8D9]'
                : 'border-[#2F3C48] bg-[#2F3C48]/30 text-[#E6E6E6] hover:bg-[#2F3C48]/50'
            }`}
          >
            <FileText className="mb-2" size={24} />
            <span>Paste Data</span>
            <span className="text-xs mt-1 opacity-70">For small datasets</span>
          </button>
        </div>
        {uploadMethod === 'file' && (
          <div className="mt-4">
            <div
              className="border-2 border-dashed border-[#2F3C48] rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              tabIndex={0}
              role="button"
              aria-label="File Upload Drop Zone"
            >
              {filePreview ? (
                <div className="text-center">
                  <p className="mb-2 text-[#00B8D9]">{filePreview}</p>
                  <button
                    type="button"
                    onClick={() => {
                      setFilePreview(null);
                      setSelectedFile(null);
                    }}
                    className="text-sm text-[#E6E6E6] hover:text-[#00B8D9]"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <>
                  <Upload className="w-10 h-10 mb-3 text-[#2F3C48]" />
                  <p className="mb-2 text-sm text-center text-[#E6E6E6]">
                    <span className="font-semibold">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-xs text-[#E6E6E6]/70">CSV, XLSX, JSON up to 10MB</p>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".csv,.xlsx,.json,.parquet"
                    onChange={onFileInputChange}
                  />
                  <label
                    htmlFor="file-upload"
                    className="mt-4 px-4 py-2 bg-[#2F3C48] text-[#E6E6E6] rounded cursor-pointer hover:bg-[#2F3C48]/70"
                  >
                    Select File
                  </label>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // Paso 2: Configure
  const renderConfigureStep = () => (
    <div className="space-y-6 transition-opacity duration-300">
      <div>
        <h3 className="text-lg font-medium text-[#E6E6E6] mb-4">Column Configuration</h3>
        <div className="border border-[#2F3C48] rounded">
          <div className="grid grid-cols-6 bg-[#2F3C48]/80 p-3 rounded-t">
            <div className="col-span-3 font-medium text-[#E6E6E6]">Column Name</div>
            <div className="col-span-2 font-medium text-[#E6E6E6]">Data Type</div>
            <div className="col-span-1 font-medium text-[#E6E6E6]">Primary Key</div>
          </div>
          <div className="divide-y divide-[#2F3C48]">
            {columns.map((column, index) => (
              <div key={index} className="grid grid-cols-6 p-3 items-center">
                <div className="col-span-3">
                  <input
                    type="text"
                    value={column.name}
                    onChange={(e) => {
                      const newColumns = [...columns];
                      newColumns[index].name = e.target.value;
                      setColumns(newColumns);
                    }}
                    className="w-full px-2 py-1 bg-[#2F3C48]/50 border border-[#2F3C48] text-[#E6E6E6] rounded focus:outline-none focus:ring-1 focus:ring-[#00B8D9]"
                  />
                </div>
                <div className="col-span-2">
                  <select
                    value={column.type}
                    onChange={(e) => {
                      const newColumns = [...columns];
                      newColumns[index].type = e.target.value;
                      setColumns(newColumns);
                    }}
                    className="w-full px-2 py-1 bg-[#2F3C48]/50 border border-[#2F3C48] text-[#E6E6E6] rounded focus:outline-none focus:ring-1 focus:ring-[#00B8D9]"
                  >
                    <option value="string">String</option>
                    <option value="number">Number</option>
                    <option value="date">Date</option>
                    <option value="boolean">Boolean</option>
                  </select>
                </div>
                <div className="col-span-1 flex justify-center">
                  <input
                    type="radio"
                    name="primaryKey"
                    className="h-4 w-4 text-[#00B8D9] focus:ring-[#00B8D9]"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div>
        <h3 className="text-lg font-medium text-[#E6E6E6] mb-4">Data Preview</h3>
        <div className="border border-[#2F3C48] rounded overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-[#2F3C48]">
              <thead className="bg-[#2F3C48]/80">
                <tr>
                  {columns.map((column, index) => (
                    <th
                      key={index}
                      className="px-4 py-3 text-left text-xs font-medium text-[#E6E6E6] uppercase tracking-wider"
                    >
                      {column.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-[#2F3C48]/30 divide-y divide-[#2F3C48]">
                {[...Array(3)].map((_, rowIndex) => (
                  <tr key={rowIndex}>
                    {columns.map((column, colIndex) => (
                      <td key={colIndex} className="px-4 py-2 whitespace-nowrap text-sm text-[#E6E6E6]">
                        {column.type === 'number'
                          ? Math.floor(Math.random() * 1000)
                          : column.type === 'date'
                          ? new Date().toISOString().split('T')[0]
                          : column.type === 'boolean'
                          ? Math.random() > 0.5 ? 'true' : 'false'
                          : `Sample ${rowIndex + 1}`}
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
        <h3 className="text-lg font-medium text-[#E6E6E6] mb-4">Data Transformations</h3>
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              id="normalize-dates"
              type="checkbox"
              className="h-4 w-4 text-[#00B8D9] focus:ring-[#00B8D9] border-[#2F3C48] rounded"
            />
            <label htmlFor="normalize-dates" className="ml-2 block text-sm text-[#E6E6E6]">
              Normalize dates to YYYY-MM-DD format
            </label>
          </div>
          <div className="flex items-center">
            <input
              id="replace-nulls"
              type="checkbox"
              className="h-4 w-4 text-[#00B8D9] focus:ring-[#00B8D9] border-[#2F3C48] rounded"
            />
            <label htmlFor="replace-nulls" className="ml-2 block text-sm text-[#E6E6E6]">
              Replace null values with default value
            </label>
          </div>
          <div className="flex items-center">
            <input
              id="auto-tag"
              type="checkbox"
              className="h-4 w-4 text-[#00B8D9] focus:ring-[#00B8D9] border-[#2F3C48] rounded"
            />
            <label htmlFor="auto-tag" className="ml-2 block text-sm text-[#E6E6E6]">
              Auto-tag dataset based on content (AI-powered)
            </label>
          </div>
          <div className="flex items-center">
            <input
              id="anomaly-detection"
              type="checkbox"
              className="h-4 w-4 text-[#00B8D9] focus:ring-[#00B8D9] border-[#2F3C48] rounded"
            />
            <label htmlFor="anomaly-detection" className="ml-2 block text-sm text-[#E6E6E6]">
              Detect anomalies and missing values
            </label>
          </div>
        </div>
      </div>
      <div>
        <h3 className="text-lg font-medium text-[#E6E6E6] mb-4">Access Permissions</h3>
        <div className="space-y-3">
          <div className="flex items-center p-3 border border-[#2F3C48] rounded bg-[#2F3C48]/30 hover:bg-[#2F3C48]/50 cursor-pointer">
            <input
              id="private-access"
              name="access-permission"
              type="radio"
              className="h-4 w-4 text-[#00B8D9] focus:ring-[#00B8D9]"
              checked={dataAccess === 'private'}
              onChange={() => setDataAccess('private')}
            />
            <label htmlFor="private-access" className="ml-3 block">
              <span className="block text-sm font-medium text-[#E6E6E6]">Private</span>
              <span className="block text-xs text-[#E6E6E6]/70">Only you can access this dataset</span>
            </label>
          </div>
          <div className="flex items-center p-3 border border-[#2F3C48] rounded bg-[#2F3C48]/30 hover:bg-[#2F3C48]/50 cursor-pointer">
            <input
              id="team-access"
              name="access-permission"
              type="radio"
              className="h-4 w-4 text-[#00B8D9] focus:ring-[#00B8D9]"
              checked={dataAccess === 'team'}
              onChange={() => setDataAccess('team')}
            />
            <label htmlFor="team-access" className="ml-3 block">
              <span className="block text-sm font-medium text-[#E6E6E6]">Team</span>
              <span className="block text-xs text-[#E6E6E6]/70">Your team members can access this dataset</span>
            </label>
          </div>
          <div className="flex items-center p-3 border border-[#2F3C48] rounded bg-[#2F3C48]/30 hover:bg-[#2F3C48]/50 cursor-pointer">
            <input
              id="public-access"
              name="access-permission"
              type="radio"
              className="h-4 w-4 text-[#00B8D9] focus:ring-[#00B8D9]"
              checked={dataAccess === 'public'}
              onChange={() => setDataAccess('public')}
            />
            <label htmlFor="public-access" className="ml-3 block">
              <span className="block text-sm font-medium text-[#E6E6E6]">Public</span>
              <span className="block text-xs text-[#E6E6E6]/70">Anyone in your organization can access this dataset</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  // Paso 4: Confirm
  const renderConfirmStep = () => (
    <div className="space-y-6 transition-opacity duration-300">
      <div className="bg-[#2F3C48]/30 p-4 rounded border border-[#2F3C48]">
        <h3 className="text-lg font-medium text-[#E6E6E6] mb-4">Dataset Summary</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-[#E6E6E6]/70 mb-1">Name</p>
            <p className="text-[#E6E6E6]">{datasetName || 'Not specified'}</p>
          </div>
          <div>
            <p className="text-sm text-[#E6E6E6]/70 mb-1">Category</p>
            <p className="text-[#E6E6E6] capitalize">{category || 'Not specified'}</p>
          </div>
          <div>
            <p className="text-sm text-[#E6E6E6]/70 mb-1">Upload Method</p>
            <p className="text-[#E6E6E6] capitalize">{uploadMethod}</p>
          </div>
          <div>
            <p className="text-sm text-[#E6E6E6]/70 mb-1">File</p>
            <p className="text-[#E6E6E6]">{selectedFile?.name || 'No file selected'}</p>
          </div>
          <div>
            <p className="text-sm text-[#E6E6E6]/70 mb-1">Columns</p>
            <p className="text-[#E6E6E6]">{columns.length}</p>
          </div>
          <div>
            <p className="text-sm text-[#E6E6E6]/70 mb-1">Access</p>
            <p className="text-[#E6E6E6] capitalize">{dataAccess}</p>
          </div>
        </div>
        <div className="mt-4">
          <p className="text-sm text-[#E6E6E6]/70 mb-1">Description</p>
          <p className="text-[#E6E6E6]">{description || 'No description provided'}</p>
        </div>
      </div>
      <div className="bg-[#2F3C48]/30 p-4 rounded border border-[#2F3C48]">
        <h3 className="text-lg font-medium text-[#E6E6E6] mb-4">What's Next?</h3>
        <div className="space-y-3">
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 text-[#00B8D9]">
              <Check size={20} />
            </div>
            <p className="ml-3 text-sm text-[#E6E6E6]">
              Explore your dataset in a data table view
            </p>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 text-[#00B8D9]">
              <Check size={20} />
            </div>
            <p className="ml-3 text-sm text-[#E6E6E6]">
              Create a dashboard with visualizations based on this dataset
            </p>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 text-[#00B8D9]">
              <Check size={20} />
            </div>
            <p className="ml-3 text-sm text-[#E6E6E6]">
              Apply AI models to gain insights from your data
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
      <div className="bg-[#1E2A38]/90 border border-[#2F3C48] rounded-lg shadow-lg w-full max-w-3xl mx-4 overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b border-[#2F3C48]">
          <h2 id="modal-title" className="text-xl font-semibold text-[#E6E6E6]">
            {currentStep === 'upload' && 'Upload Dataset'}
            {currentStep === 'configure' && 'Configure Columns'}
            {currentStep === 'advanced' && 'Advanced Options'}
            {currentStep === 'confirm' && 'Confirm Dataset'}
          </h2>
          <button onClick={onClose} aria-label="Close Modal" className="text-[#E6E6E6]/70 hover:text-[#E6E6E6]">
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
        <div className="flex justify-between items-center p-4 border-t border-[#2F3C48] bg-[#2F3C48]/20">
          <button
            type="button"
            onClick={() => {
              if (currentStep === 'upload') onClose();
              else if (currentStep === 'configure') setCurrentStep('upload');
              else if (currentStep === 'advanced') setCurrentStep('configure');
              else if (currentStep === 'confirm') setCurrentStep('advanced');
            }}
            className="px-4 py-2 border border-[#2F3C48] text-[#E6E6E6] bg-transparent hover:bg-[#2F3C48]/40 rounded"
          >
            {currentStep === 'upload' ? 'Cancel' : 'Back'}
          </button>
          <button
            type="button"
            onClick={() => {
              if (currentStep === 'upload') setCurrentStep('configure');
              else if (currentStep === 'configure') setCurrentStep('advanced');
              else if (currentStep === 'advanced') setCurrentStep('confirm');
              else if (currentStep === 'confirm') handleSave();
            }}
            disabled={currentStep === 'upload' && !datasetName}
            className={`px-4 py-2 bg-[#00B8D9] text-[#1E2A38] hover:bg-[#00B8D9]/90 rounded ${
              currentStep === 'upload' && !datasetName ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {currentStep === 'confirm' ? 'Save Dataset' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddDatasetModal;
