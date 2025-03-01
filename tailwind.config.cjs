// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'cyber-dark': '#0A192F',      // Azul oscuro
        'cyber-detail': '#1C3D5A',    // Gris metálico
        'cyber-cyan': '#00E6E6',      // Cian brillante
        'cyber-text': '#E6E6E6',      // Blanco para texto
      },
    },
  },
  plugins: [],
};
