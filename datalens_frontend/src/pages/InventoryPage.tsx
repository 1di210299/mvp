import React, { useState, useEffect } from 'react';
import { Product, Inventory } from '../types';
import { inventoryService } from '../services/api';
import './InventoryPage.css';

const InventoryPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadInventoryData();
  }, []);

  const loadInventoryData = async () => {
    try {
      setLoading(true);
      
      // Cargar productos reales desde la API
      const productsResponse = await inventoryService.getProducts();
      const inventoryResponse = await inventoryService.getInventory();
      
      setProducts(productsResponse.results || []);
      setInventory(inventoryResponse.results || []);
    } catch (err: any) {
      console.error('Error loading inventory data:', err);
      setError('Error al cargar los datos del inventario. Verificar conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter((product: any) =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStockLevel = (productId: number) => {
    // Buscar el inventario real para este producto
    const productInventory = inventory.find((inv: any) => inv.product.id === productId);
    const product = products.find((p: any) => p.id === productId);
    
    if (productInventory && product) {
      return {
        current: productInventory.quantity,
        min: product.min_stock,
        max: product.max_stock
      };
    }
    
    // Si no se encuentra inventario, usar datos del producto
    if (product) {
      return {
        current: 0, // No hay stock si no está en inventario
        min: product.min_stock || 0,
        max: product.max_stock || 0
      };
    }
    
    return { current: 0, min: 0, max: 0 };
  };

  const getStockStatus = (current: number, min: number) => {
    if (current === 0) return 'out-of-stock';
    if (current <= min) return 'low-stock';
    return 'in-stock';
  };

  if (loading) {
    return (
      <div className="inventory-loading">
        <div className="loading-spinner"></div>
        <p>Cargando inventario...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="inventory-error">
        <p>{error}</p>
        <button onClick={loadInventoryData} className="btn btn-primary">
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="inventory-page">
      <div className="inventory-header">
        <h1 className="inventory-title">Gestión de Inventario</h1>
        <p className="inventory-subtitle">
          Administra tu stock y productos
        </p>
      </div>

      <div className="inventory-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="Buscar productos por nombre o SKU..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="form-input"
          />
        </div>
        <div className="control-buttons">
          <button className="btn btn-primary">
            Agregar Producto
          </button>
          <button className="btn btn-secondary">
            Exportar
          </button>
        </div>
      </div>

      <div className="inventory-table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Producto</th>
              <th>SKU</th>
              <th>Categoría</th>
              <th>Stock Actual</th>
              <th>Stock Mín/Máx</th>
              <th>Estado</th>
              <th>Precio Unitario</th>
              <th>Valor Total</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map(product => {
              const stock = getStockLevel(product.id);
              const status = getStockStatus(stock.current, stock.min);
              
              return (
                <tr key={product.id}>
                  <td>
                    <div className="product-info">
                      <span className="product-name">{product.name}</span>
                      <span className="product-description">{product.description}</span>
                    </div>
                  </td>
                  <td>
                    <code className="product-sku">{product.sku}</code>
                  </td>
                  <td>{product.category.name}</td>
                  <td>
                    <span className={`stock-current ${status}`}>
                      {stock.current}
                    </span>
                  </td>
                  <td>
                    <span className="stock-range">
                      {stock.min} / {stock.max}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-${status === 'in-stock' ? 'success' : status === 'low-stock' ? 'warning' : 'error'}`}>
                      {status === 'in-stock' ? 'En Stock' : 
                       status === 'low-stock' ? 'Stock Bajo' : 'Agotado'}
                    </span>
                  </td>
                  <td>S/ {product.unit_price.toLocaleString()}</td>
                  <td>S/ {(product.unit_price * stock.current).toLocaleString()}</td>
                  <td>
                    <div className="action-buttons">
                      <button className="btn btn-sm btn-secondary">
                        Ver
                      </button>
                      <button className="btn btn-sm btn-primary">
                        Editar
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {filteredProducts.length === 0 && (
        <div className="no-results">
          <p>No se encontraron productos que coincidan con tu búsqueda.</p>
        </div>
      )}
    </div>
  );
};

export default InventoryPage;
