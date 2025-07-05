import React, { useState } from 'react';
import {
  Form,
  CRUDForm,
  CRUDActions,
  CreateButton,
  AdvancedTable,
  CSVUploader,
  AdvancedBarChart,
  AdvancedLineChart,
  AdvancedPieChart,
  ChartDashboard,
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from './ui';

// Datos de ejemplo
const sampleInventoryData = [
  { id: 1, producto: 'Laptop Dell', categoria: 'Electrónicos', stock: 15, precio: 1200, ventas: 85 },
  { id: 2, producto: 'Mouse Logitech', categoria: 'Accesorios', stock: 50, precio: 25, ventas: 120 },
  { id: 3, producto: 'Monitor Samsung', categoria: 'Electrónicos', stock: 8, precio: 300, ventas: 45 },
  { id: 4, producto: 'Teclado Mecánico', categoria: 'Accesorios', stock: 30, precio: 80, ventas: 60 },
  { id: 5, producto: 'Tablet iPad', categoria: 'Electrónicos', stock: 12, precio: 800, ventas: 30 }
];

const salesData = [
  { mes: 'Ene', ventas: 4000, ganancias: 2400 },
  { mes: 'Feb', ventas: 3000, ganancias: 1398 },
  { mes: 'Mar', ventas: 2000, ganancias: 9800 },
  { mes: 'Abr', ventas: 2780, ganancias: 3908 },
  { mes: 'May', ventas: 1890, ganancias: 4800 },
  { mes: 'Jun', ventas: 2390, ganancias: 3800 }
];

const categoryData = [
  { categoria: 'Electrónicos', valor: 35 },
  { categoria: 'Accesorios', valor: 25 },
  { categoria: 'Software', valor: 20 },
  { categoria: 'Servicios', valor: 20 }
];

// Configuración de formulario para productos
const productFormFields = [
  {
    name: 'nombre' as const,
    label: 'Nombre del Producto',
    type: 'text' as const,
    required: true,
    placeholder: 'Ingrese el nombre del producto'
  },
  {
    name: 'categoria' as const,
    label: 'Categoría',
    type: 'select' as const,
    required: true,
    options: [
      { value: 'electronica', label: 'Electrónicos' },
      { value: 'accesorios', label: 'Accesorios' },
      { value: 'software', label: 'Software' },
      { value: 'servicios', label: 'Servicios' }
    ]
  },
  {
    name: 'precio' as const,
    label: 'Precio',
    type: 'number' as const,
    required: true,
    placeholder: '0.00',
    validation: { min: 0 }
  },
  {
    name: 'stock' as const,
    label: 'Stock Inicial',
    type: 'number' as const,
    required: true,
    placeholder: '0',
    validation: { min: 0 }
  },
  {
    name: 'descripcion' as const,
    label: 'Descripción',
    type: 'textarea' as const,
    placeholder: 'Descripción del producto...'
  }
];

// Configuración de columnas para la tabla
const inventoryColumns = [
  {
    key: 'producto',
    title: 'Producto',
    sortable: true,
    filterable: true
  },
  {
    key: 'categoria',
    title: 'Categoría',
    sortable: true,
    filterable: true
  },
  {
    key: 'stock',
    title: 'Stock',
    sortable: true,
    render: (value: number) => (
      <span className={`px-2 py-1 rounded text-sm ${
        value < 10 ? 'bg-red-100 text-red-800' : 
        value < 20 ? 'bg-yellow-100 text-yellow-800' : 
        'bg-green-100 text-green-800'
      }`}>
        {value}
      </span>
    )
  },
  {
    key: 'precio',
    title: 'Precio',
    sortable: true,
    render: (value: number) => `$${value.toFixed(2)}`
  },
  {
    key: 'ventas',
    title: 'Ventas',
    sortable: true,
    render: (value: number) => value.toString()
  }
];

// CSV columns configuration
const csvColumns = [
  { key: 'producto', label: 'Producto', type: 'string' as const, required: true },
  { key: 'categoria', label: 'Categoría', type: 'string' as const, required: true },
  { key: 'stock', label: 'Stock', type: 'number' as const, required: true },
  { key: 'precio', label: 'Precio', type: 'number' as const, required: true }
];

// Mock API service
const mockApiService = {
  create: async (data: any) => {
    console.log('Creando producto:', data);
    await new Promise(resolve => setTimeout(resolve, 1000));
    return { ...data, id: Date.now() };
  },
  update: async (id: string | number, data: any) => {
    console.log('Actualizando producto:', id, data);
    await new Promise(resolve => setTimeout(resolve, 1000));
    return { ...data, id };
  }
};

export const ComponentsShowcase: React.FC = () => {
  const [activeTab, setActiveTab] = useState('forms');
  const [csvData, setCsvData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFormSubmit = async (data: any) => {
    setIsLoading(true);
    setError(null);
    try {
      // Simular llamada a API
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert('Producto guardado exitosamente!');
    } catch (err) {
      setError('Error al guardar el producto');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCSVData = (data: any[]) => {
    setCsvData(data);
    console.log('Datos CSV cargados:', data);
    alert(`Se cargaron ${data.length} registros desde el CSV`);
  };

  const tableActions = [
    {
      label: 'Editar',
      onClick: (record: any) => {
        console.log('Editando:', record);
        alert(`Editando: ${record.producto}`);
      },
      variant: 'primary' as const
    },
    {
      label: 'Eliminar',
      onClick: (record: any) => {
        console.log('Eliminando:', record);
        if (confirm(`¿Eliminar ${record.producto}?`)) {
          alert('Producto eliminado');
        }
      },
      variant: 'destructive' as const
    }
  ];

  const chartConfigs = [
    {
      type: 'bar' as const,
      title: 'Ventas vs Ganancias Mensuales',
      gridSize: 'lg' as const,
      props: {
        data: salesData,
        xAxisKey: 'mes',
        yAxisKey: 'ventas',
        multiple: ['ventas', 'ganancias'],
        height: 300
      }
    },
    {
      type: 'line' as const,
      title: 'Tendencia de Ventas',
      gridSize: 'md' as const,
      props: {
        data: salesData,
        xAxisKey: 'mes',
        yAxisKey: 'ventas',
        curved: true,
        height: 300
      }
    },
    {
      type: 'pie' as const,
      title: 'Distribución por Categorías',
      gridSize: 'md' as const,
      props: {
        data: categoryData,
        nameKey: 'categoria',
        valueKey: 'valor',
        height: 300
      }
    }
  ];

  const tabs = [
    { id: 'forms', label: 'Formularios CRUD' },
    { id: 'tables', label: 'Tablas Avanzadas' },
    { id: 'csv', label: 'Carga CSV' },
    { id: 'charts', label: 'Gráficos Avanzados' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Showcase de Componentes Avanzados
        </h1>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Forms Tab */}
        {activeTab === 'forms' && (
          <Card>
            <CardHeader>
              <CardTitle>Formulario CRUD de Productos</CardTitle>
            </CardHeader>
            <CardContent>
              <Form
                fields={productFormFields}
                onSubmit={handleFormSubmit}
                isLoading={isLoading}
                submitText="Guardar Producto"
              />
              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Tables Tab */}
        {activeTab === 'tables' && (
          <Card>
            <CardHeader>
              <CardTitle>Tabla de Inventario con Funciones Avanzadas</CardTitle>
            </CardHeader>
            <CardContent>
              <AdvancedTable
                data={sampleInventoryData}
                columns={inventoryColumns}
                actions={tableActions}
                searchable={true}
                exportable={true}
                pagination={{ pageSize: 5, showSizeChanger: true }}
                onRowClick={(record: any) => {
                  console.log('Fila clickeada:', record);
                }}
              />
            </CardContent>
          </Card>
        )}

        {/* CSV Tab */}
        {activeTab === 'csv' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Carga de Datos desde CSV</CardTitle>
              </CardHeader>
              <CardContent>
                <CSVUploader
                  onDataLoaded={handleCSVData}
                  expectedColumns={csvColumns}
                  downloadTemplate={true}
                  templateColumns={csvColumns}
                  maxFileSize={5}
                />
              </CardContent>
            </Card>

            {csvData.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Datos Cargados desde CSV</CardTitle>
                </CardHeader>
                <CardContent>
                  <AdvancedTable
                    data={csvData}
                    columns={[
                      { key: 'producto', title: 'Producto', sortable: true },
                      { key: 'categoria', title: 'Categoría', sortable: true },
                      { key: 'stock', title: 'Stock', sortable: true },
                      { key: 'precio', title: 'Precio', sortable: true }
                    ]}
                    pagination={{ pageSize: 10 }}
                    searchable={true}
                  />
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Charts Tab */}
        {activeTab === 'charts' && (
          <div className="space-y-8">
            <ChartDashboard
              title="Dashboard de Análisis"
              charts={chartConfigs}
            />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Gráfico de Barras Personalizado</CardTitle>
                </CardHeader>
                <CardContent>
                  <AdvancedBarChart
                    data={salesData}
                    xAxisKey="mes"
                    yAxisKey="ventas"
                    color="#10B981"
                    height={250}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Gráfico de Líneas Múltiples</CardTitle>
                </CardHeader>
                <CardContent>
                  <AdvancedLineChart
                    data={salesData}
                    xAxisKey="mes"
                    yAxisKey="ventas"
                    multiple={['ventas', 'ganancias']}
                    curved={true}
                    height={250}
                  />
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
