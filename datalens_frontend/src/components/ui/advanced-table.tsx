import React, { useState, useMemo } from 'react';
import { Button } from './button';
import { Input } from './input';
import { Select } from './select';

interface Column<T> {
  key: keyof T | string;
  title: string;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
}

interface TableAction<T> {
  label: string;
  onClick: (record: T) => void;
  variant?: 'primary' | 'secondary' | 'destructive';
  icon?: React.ReactNode;
}

interface AdvancedTableProps<T> {
  data: T[];
  columns: Column<T>[];
  actions?: TableAction<T>[];
  pagination?: {
    pageSize?: number;
    showSizeChanger?: boolean;
  };
  loading?: boolean;
  onRowClick?: (record: T) => void;
  className?: string;
  searchable?: boolean;
  exportable?: boolean;
}

export function AdvancedTable<T extends Record<string, any>>({
  data,
  columns,
  actions = [],
  pagination = { pageSize: 10 },
  loading = false,
  onRowClick,
  className = '',
  searchable = true,
  exportable = false
}: AdvancedTableProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(pagination.pageSize || 10);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);
  const [filters, setFilters] = useState<Record<string, string>>({});

  // Filtrado y búsqueda
  const filteredData = useMemo(() => {
    let filtered = [...data];

    // Búsqueda global
    if (searchTerm) {
      filtered = filtered.filter(item =>
        Object.values(item).some(value =>
          String(value || '').toLowerCase().includes((searchTerm || '').toLowerCase())
        )
      );
    }

    // Filtros por columna
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        filtered = filtered.filter(item =>
          String(item[key] || '').toLowerCase().includes((value || '').toLowerCase())
        );
      }
    });

    return filtered;
  }, [data, searchTerm, filters]);

  // Ordenamiento
  const sortedData = useMemo(() => {
    if (!sortConfig) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [filteredData, sortConfig]);

  // Paginación
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return sortedData.slice(startIndex, startIndex + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  const handleSort = (key: string) => {
    setSortConfig(current => {
      if (current?.key === key) {
        return {
          key,
          direction: current.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return { key, direction: 'asc' };
    });
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const exportToCSV = () => {
    const headers = columns.map(col => col.title).join(',');
    const rows = filteredData.map(item =>
      columns.map(col => {
        const key = col.key as keyof T;
        return `"${String(item[key] || '')}"`;
      }).join(',')
    );
    
    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'export.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Controles superiores */}
      <div className="flex justify-between items-center">
        <div className="flex space-x-4">
          {searchable && (
            <Input
              placeholder="Buscar..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-64"
            />
          )}
          
          {exportable && (
            <Button
              onClick={exportToCSV}
              variant="secondary"
            >
              Exportar CSV
            </Button>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">
            Mostrando {((currentPage - 1) * pageSize) + 1} a{' '}
            {Math.min(currentPage * pageSize, sortedData.length)} de{' '}
            {sortedData.length} registros
          </span>
        </div>
      </div>

      {/* Filtros por columna */}
      <div className="flex space-x-2 flex-wrap">
        {columns.filter(col => col.filterable).map(col => (
          <Input
            key={String(col.key)}
            placeholder={`Filtrar por ${col.title}`}
            value={filters[String(col.key)] || ''}
            onChange={(e) => handleFilterChange(String(col.key), e.target.value)}
            className="w-48"
          />
        ))}
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                    column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                  }`}
                  style={{ width: column.width }}
                  onClick={() => column.sortable && handleSort(String(column.key))}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.title}</span>
                    {column.sortable && (
                      <span className="text-gray-400">
                        {sortConfig?.key === column.key ? (
                          sortConfig.direction === 'asc' ? '↑' : '↓'
                        ) : '↕'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
              {actions.length > 0 && (
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.map((record, index) => (
              <tr
                key={index}
                className={`hover:bg-gray-50 ${onRowClick ? 'cursor-pointer' : ''}`}
                onClick={() => onRowClick?.(record)}
              >
                {columns.map((column) => (
                  <td
                    key={String(column.key)}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                  >
                    {column.render
                      ? column.render(record[column.key as keyof T], record, index)
                      : String(record[column.key as keyof T] || '')
                    }
                  </td>
                ))}
                {actions.length > 0 && (
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {actions.map((action, actionIndex) => (
                        <button
                          key={actionIndex}
                          className={`px-3 py-1 text-xs rounded ${
                            action.variant === 'destructive'
                              ? 'bg-red-100 text-red-800 hover:bg-red-200'
                              : action.variant === 'primary'
                              ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                          }`}
                          onClick={(e: React.MouseEvent) => {
                            e.stopPropagation();
                            action.onClick(record);
                          }}
                        >
                          {action.icon && <span className="mr-1">{action.icon}</span>}
                          {action.label}
                        </button>
                      ))}
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Filas por página:</span>
            <select
              value={pageSize.toString()}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="w-20 border border-gray-300 rounded px-2 py-1"
            >
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="secondary"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(1)}
            >
              Primero
            </Button>
            <Button
              variant="secondary"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(currentPage - 1)}
            >
              Anterior
            </Button>
            
            <span className="text-sm text-gray-600">
              Página {currentPage} de {totalPages}
            </span>
            
            <Button
              variant="secondary"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              Siguiente
            </Button>
            <Button
              variant="secondary"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(totalPages)}
            >
              Último
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
