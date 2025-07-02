import React from 'react';

const AlertsList: React.FC = () => {
  // Mock data for MVP
  const alerts = [
    { id: 1, title: 'Stock Bajo', message: 'Mouse Logitech con stock bajo (5 unidades)', severity: 'high', time: '2 min' },
    { id: 2, title: 'Restock Sugerido', message: 'Teclados HP necesitan reposición', severity: 'medium', time: '15 min' },
    { id: 3, title: 'Nuevo Producto', message: 'Monitor LG agregado al inventario', severity: 'low', time: '1 hora' },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3>Alertas Recientes</h3>
      </div>
      <div className="card-body">
        <div className="alerts-list">
          {alerts.map(alert => (
            <div key={alert.id} className={`alert-item severity-${alert.severity}`}>
              <div className="alert-content">
                <h4 className="alert-title">{alert.title}</h4>
                <p className="alert-message">{alert.message}</p>
              </div>
              <div className="alert-time">
                {alert.time}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AlertsList;
