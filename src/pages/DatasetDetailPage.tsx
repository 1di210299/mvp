import React from 'react';
import { useParams } from 'react-router-dom';

function DatasetDetailPage() {
  const { id } = useParams(); // /datasets/:id

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Dataset Detail: {id}</h1>
      <p>Aquí podrías mostrar gráficos, tablas, etc. específicos del dataset {id}.</p>
    </div>
  );
}

export default DatasetDetailPage;
