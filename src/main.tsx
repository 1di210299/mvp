import React from 'react'
import ReactDOM from 'react-dom/client'
import ChatbotButton from './components/ChatbotButton'
import './index.css'

// Esta función se ejecuta cuando el DOM está listo
document.addEventListener('DOMContentLoaded', async () => {
  // Montar el botón de chatbot
  const chatbotRoot = document.getElementById('chatbot-root')
  if (chatbotRoot) {
    ReactDOM.createRoot(chatbotRoot).render(
      <React.StrictMode>
        <ChatbotButton />
      </React.StrictMode>
    )
  } else {
    console.error('No se encontró el elemento con id "chatbot-root"')
  }

  try {
    // Importación dinámica para DatasetsChart
    const DatasetsChartModule = await import('./components/DatasetsChart')
    const DatasetsChart = DatasetsChartModule.default
    
    // Montar el gráfico de datasets
    const datasetsChartContainer = document.getElementById('chart-datasets')
    if (datasetsChartContainer && DatasetsChart) {
      ReactDOM.createRoot(datasetsChartContainer).render(
        <React.StrictMode>
          <DatasetsChart />
        </React.StrictMode>
      )
    } else {
      console.error('No se pudo montar el gráfico de datasets')
    }

    // Importación dinámica para ExperimentsChart
    const ExperimentsChartModule = await import('./components/ExperimentsChart')
    const ExperimentsChart = ExperimentsChartModule.default
    
    // Montar el gráfico de experimentos
    const experimentsChartContainer = document.getElementById('chart-experiments')
    if (experimentsChartContainer && ExperimentsChart) {
      ReactDOM.createRoot(experimentsChartContainer).render(
        <React.StrictMode>
          <ExperimentsChart />
        </React.StrictMode>
      )
    } else {
      console.error('No se pudo montar el gráfico de experimentos')
    }
  } catch (error) {
    console.error('Error al cargar los componentes de gráficos:', error)
  }
})