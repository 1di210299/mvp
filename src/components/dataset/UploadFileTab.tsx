// src/components/dataset/UploadFileTab.tsx
import React, { useState } from 'react';
import { Upload } from 'lucide-react';

interface UploadFileTabProps {
  onFileSelect: (file: File) => void;
}

const UploadFileTab: React.FC<UploadFileTabProps> = ({ onFileSelect }) => {
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setFilePreview(`${file.name} (${Math.round(file.size / 1024)} KB)`);
      onFileSelect(file);
    }
  };

  return (
    <div className="mt-4">
      <div className="border-2 border-dashed border-cyber-detail rounded-lg p-6 flex flex-col items-center justify-center">
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
              Remove file
            </button>
          </div>
        ) : (
          <>
            <Upload className="w-10 h-10 mb-3 text-cyber-detail" />
            <p className="mb-2 text-sm text-center text-cyber-text">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-cyber-text/70">
              CSV, XLSX, JSON up to 10MB
            </p>
            <input
              id="file-upload"
              name="file-upload"
              type="file"
              className="sr-only"
              accept=".csv,.xlsx,.json,.parquet"
              onChange={handleFileChange}
            />
            <label
              htmlFor="file-upload"
              className="mt-4 px-4 py-2 bg-cyber-detail text-cyber-text rounded cursor-pointer hover:bg-cyber-detail/70"
            >
              Select File
            </label>
          </>
        )}
      </div>
    </div>
  );
};

export default UploadFileTab;