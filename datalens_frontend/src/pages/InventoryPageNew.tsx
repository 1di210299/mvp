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
      setError('');
      
      // Obtener productos reales de la API
      const productsResponse = await inventoryService.getProducts();
      const productsData = productsResponse.results || productsResponse;
      setProducts(productsData);
      
      // Obtener inventario real de la API
      const inventoryResponse = await inventoryService.getInventoryItems();
      const inventoryData = inventoryResponse.results || inventoryResponse;
      setInventory(inventoryData);
      
    } catch (err) {
      console.error('Error loading inventory data:', err);
      setError('Error al cargar datos del inventario. Verificar conexión con API.');
      
      // No usar fallback, mostrar el error
      setProducts([]);
      setInventory([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getInventoryForProduct = (productId: number) => {
    return inventory.find(inv => {
      const invProductId = typeof inv.product === 'number' ? inv.product : inv.product?.id;
      return invProductId === productId;
    });
  };

  const getStockStatus = (product: Product) => {
    const inv = getInventoryForProduct(product.id);
    const currentStock = inv?.quantity || 0;
    
    if (currentStock <= 0) return { status: 'out-of-stock', label: 'Sin Stock', color: 'red' };
    if (currentStock <= product.min_stock) return { status: 'low-stock', label: 'Stock Bajo', color: 'orange' };
    if (currentStock >= product.max_stock) return { status: 'high-stock', label: 'Stock Alto', color: 'blue' };
    return { status: 'normal', label: 'Normal', color: 'green' };
  };

  if (loading) {
    return (
      <div className="inventory-page">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando inventario...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="inventory-page">
      <div className="page-header">
        <h1>Gestión de Inventario</h1>
        <p>Monitor y gestiona el stock de todos tus productos</p>
      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={loadInventoryData}>Reintentar</button>
        </div>
      )}

      <div className="inventory-stats">
        <div className="stat-card">
          <h3>Total Productos</h3>
          <div className="stat-value">{products.length}</div>
        </div>
        <div className="stat-card">
          <h3>Stock Bajo</h3>
          <div className="stat-value">
            {products.filter(p => {
              const inv = getInventoryForProduct(p.id);
              return (inv?.quantity || 0) <= p.min_stock;
            }).length}
          </div>
        </div>
        <div className="stat-card">
          <h3>Sin Stock</h3>
          <div className="stat-value">
            {products.filter(p => {
              const inv = getInventoryForProduct(p.id);
              return (inv?.quantity || 0) <= 0;
            }).length}
          </div>
        </div>
        <div className="stat-card">
          <h3>Valor Total</h3>
          <div className="stat-value">
            S/ {inventory.reduce((total, inv) => {
              const productId = typeof inv.product === 'number' ? inv.product : inv.product?.id;
              const product = products.find(p => p.id === productId);
              const costPrice = typeof product?.cost_price === 'string' ? parseFloat(product.cost_price) : (product?.cost_price || 0);
              return total + ((inv.quantity || 0) * costPrice);
            }, 0).toFixed(2)}
          </div>
        </div>
      </div>

      <div className="search-controls">
        <input
          type="text"
          placeholder="Buscar productos..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="inventory-table">
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>SKU</th>
              <th>Categoría</th>
              <th>Stock Actual</th>
              <th>Stock Mín.</th>
              <th>Stock Máx.</th>
              <th>Estado</th>
              <th>Valor Stock</th>
              <th>Ubicación</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map(product => {
              const inv = getInventoryForProduct(product.id);
              const stockStatus = getStockStatus(product);
              const currentStock = inv?.quantity || 0;
              const costPrice = typeof product.cost_price === 'string' ? parseFloat(product.cost_price) : product.cost_price;
              const stockValue = currentStock * costPrice;

              return (
                <tr key={product.id}>
                  <td>
                    <div className="product-info">
                      <strong>{product.name}</strong>
                      {product.description && (
                        <small>{product.description}</small>
                      )}
                    </div>
                  </td>
                  <td>{product.sku}</td>
                  <td>{product.category_name || 'Sin categoría'}</td>
                  <td className="stock-cell">
                    <span className={`stock-amount ${stockStatus.status}`}>
                      {currentStock}
                    </span>
                  </td>
                  <td>{product.min_stock}</td>
                  <td>{product.max_stock}</td>
                  <td>
                    <span 
                      className={`status-badge ${stockStatus.status}`}
                      style={{ color: stockStatus.color }}
                    >
                      {stockStatus.label}
                    </span>
                  </td>
                  <td>S/ {stockValue.toFixed(2)}</td>
                  <td>{inv?.location?.name || 'No asignada'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredProducts.length === 0 && !loading && (
          <div className="no-data">
            {searchTerm ? 'No se encontraron productos' : 'No hay productos disponibles'}
          </div>
        )}
      </div>
    </div>
  );
};

export default InventoryPage;
