import React, { useState, useEffect } from 'react';
import { Transaction } from '../../types';
import { inventoryService } from '../../services/api';

const RecentTransactions: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const response = await inventoryService.getTransactions();
      // Verificar que response y results existan antes de hacer slice
      const results = response?.results || [];
      setTransactions(results.slice(0, 5));
    } catch (error) {
      console.error('Error al cargar transacciones:', error);
      // En caso de error, mostrar datos básicos
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('es-PE', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getTransactionTypeText = (type: string) => {
    const types: { [key: string]: string } = {
      'purchase': 'Compra',
      'sale': 'Venta',
      'adjustment': 'Ajuste',
      'transfer': 'Transferencia',
      'return': 'Devolución',
      'waste': 'Merma',
      'initial': 'Inicial'
    };
    return types[type] || type;
  };

  const getTransactionDirection = (type: string) => {
    const inTypes = ['purchase', 'return', 'initial', 'adjustment'];
    return inTypes.includes(type) ? 'in' : 'out';
  };

  if (loading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3>Transacciones Recientes</h3>
        </div>
        <div className="card-body">
          <p>Cargando transacciones...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>Transacciones Recientes</h3>
      </div>
      <div className="card-body">
        <div className="transactions-list">
          {transactions.length > 0 ? (
            transactions.map(transaction => {
              const direction = getTransactionDirection(transaction.transaction_type);
              return (
                <div key={transaction.id} className="transaction-item">
                  <div className="transaction-info">
                    <span className="transaction-product">{transaction.product.name}</span>
                    <span className="transaction-time">{formatTime(transaction.created_at)}</span>
                  </div>
                  <div className="transaction-details">
                    <span className={`transaction-type ${direction}`}>
                      {getTransactionTypeText(transaction.transaction_type)}
                    </span>
                    <span className="transaction-quantity">
                      {direction === 'in' ? '+' : '-'}{transaction.quantity}
                    </span>
                  </div>
                </div>
              );
            })
          ) : (
            <p>No hay transacciones recientes</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default RecentTransactions;
