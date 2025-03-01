// src/components/dataset/ConnectApiDbTab.tsx
import React, { useState } from 'react';

interface ConnectApiDbTabProps {
  onConnectionSetup: (connectionConfig: any) => void;
}

const ConnectApiDbTab: React.FC<ConnectApiDbTabProps> = ({ onConnectionSetup }) => {
  const [connectionType, setConnectionType] = useState('');
  const [connectionString, setConnectionString] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [query, setQuery] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [metadataInfo, setMetadataInfo] = useState<any>(null);

  const handleTestConnection = async () => {
    if (!connectionString || !connectionType) {
      alert('Please fill in the required fields (Connection Type and Connection String)');
      return;
    }

    // Configuración para enviar al backend
    const config = {
      connectionType,
      connectionString,
      username,
      password,
      query
    };

    setIsConnecting(true);
    setConnectionStatus('connecting');
    setErrorMessage('');
    setMetadataInfo(null);

    try {
      // Conexión con el backend de Django
      const response = await fetch('http://localhost:8000/api/test-connection/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to connect');
      }

      setConnectionStatus('success');
      setMetadataInfo(data.metadata);
      
      onConnectionSetup({
        ...config,
        metadata: data.metadata,
      });
    } catch (error) {
      console.error('Connection error:', error);
      setConnectionStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Unknown error occurred');
    } finally {
      setIsConnecting(false);
    }
  };

  // Helper para render condicional basado en tipo de conexión
  const renderConnectionTypeHelp = () => {
    if (connectionType === 'sql') {
      return (
        <p className="text-xs text-cyber-text/70">
          Format: mysql://hostname/database or postgresql://hostname/database
        </p>
      );
    } else if (connectionType === 'aws') {
      return (
        <p className="text-xs text-cyber-text/70">
          Enter the bucket name or S3 URI (s3://bucket-name)
        </p>
      );
    } else if (connectionType === 'bigquery') {
      return (
        <p className="text-xs text-cyber-text/70">
          Enter the dataset ID (project.dataset)
        </p>
      );
    }
    return null;
  };

  return (
    <div className="mt-4 space-y-4">
      <div className="space-y-2">
        <label className="block text-sm font-medium text-cyber-text">Connection Type</label>
        <select
          value={connectionType}
          onChange={(e) => setConnectionType(e.target.value)}
          className="w-full px-3 py-2 bg-cyber-detail/50 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
          disabled={isConnecting}
        >
          <option value="">Select connection type</option>
          <option value="sql">SQL Database</option>
          <option value="aws">AWS S3</option>
          <option value="bigquery">Google BigQuery</option>
        </select>
      </div>
      
      <div className="space-y-2">
        <label className="block text-sm font-medium text-cyber-text">Connection String/URL</label>
        <input
          type="text"
          value={connectionString}
          onChange={(e) => setConnectionString(e.target.value)}
          className="w-full px-3 py-2 bg-cyber-detail/50 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
          placeholder="Enter connection string or URL"
          disabled={isConnecting}
        />
        {renderConnectionTypeHelp()}
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-cyber-text">Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-3 py-2 bg-cyber-detail/50 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
            placeholder="Username"
            disabled={isConnecting}
          />
        </div>
        
        <div className="space-y-2">
          <label className="block text-sm font-medium text-cyber-text">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 bg-cyber-detail/50 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
            placeholder="Password"
            disabled={isConnecting}
          />
        </div>
      </div>
      
      <div className="space-y-2">
        <label className="block text-sm font-medium text-cyber-text">Query/Table</label>
        <textarea
          rows={3}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full px-3 py-2 bg-cyber-detail/50 border border-cyber-detail text-cyber-text rounded focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
          placeholder="Enter SQL query or table name"
          disabled={isConnecting}
        />
      </div>
      
      {connectionStatus === 'success' && (
        <div className="p-4 bg-green-900/50 border border-green-700 rounded text-sm text-green-300">
          <p className="font-medium mb-2">Connection successful!</p>
          {metadataInfo && (
            <div className="mt-2">
              {metadataInfo.columns && metadataInfo.columns.length > 0 && (
                <p>Detected {metadataInfo.columns.length} columns.</p>
              )}
              {metadataInfo.sample_data && (
                <p>Retrieved {metadataInfo.sample_data.length} sample rows.</p>
              )}
              {connectionType === 'aws' && metadataInfo.bucket && (
                <p>Connected to bucket: {metadataInfo.bucket}</p>
              )}
            </div>
          )}
        </div>
      )}
      
      {connectionStatus === 'error' && (
        <div className="p-3 bg-red-900/50 border border-red-700 rounded text-sm text-red-300">
          <p className="font-medium mb-1">Connection failed:</p>
          <p>{errorMessage || "Please check your credentials and try again."}</p>
        </div>
      )}
      
      <button
        type="button"
        onClick={handleTestConnection}
        className={`px-4 py-2 ${
          isConnecting 
            ? 'bg-cyber-detail/50 cursor-not-allowed' 
            : 'bg-cyber-detail hover:bg-cyber-detail/70'
        } text-cyber-text rounded flex items-center justify-center`}
        disabled={isConnecting}
      >
        {isConnecting ? (
          <>
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-cyber-cyan" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Connecting...
          </>
        ) : (
          'Test Connection'
        )}
      </button>
      
      {connectionStatus === 'success' && metadataInfo && metadataInfo.columns && metadataInfo.columns.length > 0 && (
        <div className="mt-4 p-4 bg-cyber-detail/30 border border-cyber-detail rounded">
          <h4 className="text-sm font-medium text-cyber-text mb-2">Data Preview</h4>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-cyber-detail/70">
              <thead>
                <tr>
                  {metadataInfo.columns.map((column: string, index: number) => (
                    <th key={index} className="px-3 py-2 text-left text-xs font-medium text-cyber-cyan tracking-wider">
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-cyber-detail/30">
                {metadataInfo.sample_data && metadataInfo.sample_data.map((row: any, rowIndex: number) => (
                  <tr key={rowIndex}>
                    {Array.isArray(row) ? 
                      row.map((cell, cellIndex) => (
                        <td key={cellIndex} className="px-3 py-2 whitespace-nowrap text-xs text-cyber-text">
                          {String(cell)}
                        </td>
                      )) : 
                      metadataInfo.columns.map((column: string, colIndex: number) => (
                        <td key={colIndex} className="px-3 py-2 whitespace-nowrap text-xs text-cyber-text">
                          {String(row[column] !== undefined ? row[column] : '')}
                        </td>
                      ))
                    }
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectApiDbTab;