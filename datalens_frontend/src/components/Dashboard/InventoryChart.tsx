import React from 'react';

interface InventoryChartProps {
  data: Array<{
    warehouse: string;
    current_stock: number;
    min_stock: number;
    max_stock: number;
  }>;
}

const InventoryChart: React.FC<InventoryChartProps> = ({ data }) => {
  return (
    <div className="card">
      <div className="card-header">
        <h3>Niveles de Stock por Almacén</h3>
      </div>
      <div className="card-body">
        <div className="chart-container">
          {data.map((item, index) => (
            <div key={index} className="chart-bar">
              <div className="chart-bar-label">{item.warehouse}</div>
              <div className="chart-bar-container">
                <div 
                  className="chart-bar-fill"
                  style={{ 
                    width: `${(item.current_stock / item.max_stock) * 100}%`,
                    backgroundColor: item.current_stock < item.min_stock ? '#ef4444' : '#10b981'
                  }}
                ></div>
              </div>
              <div className="chart-bar-values">
                <span>{item.current_stock}</span> / <span>{item.max_stock}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default InventoryChart;
