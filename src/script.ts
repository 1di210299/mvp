import Chart from 'chart.js/auto';
import L from 'leaflet';

// ----------------------
// Gráfica de Expenses
// ----------------------
const expensesCanvas = document.getElementById('expensesChart') as HTMLCanvasElement | null;
if (expensesCanvas) {
  const ctxExpenses = expensesCanvas.getContext('2d');
  if (ctxExpenses) {
    void new Chart(ctxExpenses, {
      type: 'bar',
      data: {
        labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
        datasets: [{
          label: 'Expenses',
          data: [3000, 4000, 3200, 5000, 4500, 5400, 4800, 6000, 7000, 6500, 6200, 8000],
          backgroundColor: '#4e63d9'
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  }
}

// ----------------------
// Gráfica de Trips
// ----------------------
const tripsCanvas = document.getElementById('tripsChart') as HTMLCanvasElement | null;
if (tripsCanvas) {
  const ctxTrips = tripsCanvas.getContext('2d');
  if (ctxTrips) {
    void new Chart(ctxTrips, {
      type: 'line',
      data: {
        labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
        datasets: [{
          label: 'Trips',
          data: [10, 15, 8, 20, 18, 22, 25, 30, 28, 35, 40, 45],
          fill: false,
          borderColor: '#4e63d9',
          tension: 0.1
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  }
}

// ----------------------
// Mapa con Leaflet
// ----------------------
const mapElement = document.getElementById('map');
if (mapElement) {
  const map = L.map('map').setView([40.7128, -74.0060], 10); // Centrado en Nueva York
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
  }).addTo(map);
  const marker = L.marker([40.7128, -74.0060]).addTo(map);
  marker.bindPopup("Ubicación de ejemplo").openPopup();
}
