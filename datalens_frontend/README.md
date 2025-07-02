# DataLens Frontend

Frontend de la aplicación DataLens - Plataforma de gestión y análisis de inventarios para PYMEs peruanas.

## 🚀 Características

- **Dashboard Interactivo**: Visualización en tiempo real de estadísticas de inventario
- **Gestión de Productos**: CRUD completo de productos e inventario
- **Alertas Inteligentes**: Sistema de notificaciones para stock bajo y reposición
- **Reportes Visuales**: Gráficos y reportes de análisis de inventario
- **Diseño Responsivo**: Interfaz optimizada para desktop, tablet y móvil
- **Autenticación JWT**: Sistema seguro de autenticación

## 🛠️ Tecnologías

- **React 18** con TypeScript
- **CSS personalizado** con variables CSS y diseño moderno
- **Axios** para comunicación con API
- **Recharts** para gráficos y visualizaciones
- **Create React App** como base del proyecto

## 📋 Requisitos Previos

- Node.js 16+ y npm
- Backend DataLens ejecutándose en http://localhost:8080

## 🔧 Instalación y Configuración

### 1. Instalar dependencias
```bash
cd datalens_frontend
npm install
```

### 2. Configurar variables de entorno
Crear archivo `.env` en la raíz del proyecto:
```env
REACT_APP_API_URL=http://localhost:8080/api
REACT_APP_APP_NAME=DataLens
```

### 3. Ejecutar en desarrollo
```bash
npm start
```

La aplicación estará disponible en http://localhost:3000

### 4. Construir para producción
```bash
npm run build
```

## 📁 Estructura del Proyecto

```
datalens_frontend/
├── public/
│   ├── index.html
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── Login/
│   │   │   ├── Login.tsx
│   │   │   └── Login.css
│   │   ├── Dashboard/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Dashboard.css
│   │   │   ├── StatsCard.tsx
│   │   │   ├── InventoryChart.tsx
│   │   │   ├── RecentTransactions.tsx
│   │   │   └── AlertsList.tsx
│   │   └── Navbar/
│   │       ├── Navbar.tsx
│   │       └── Navbar.css
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   │   └── index.ts
│   ├── styles/
│   │   └── global.css
│   ├── App.tsx
│   └── index.tsx
├── package.json
├── tsconfig.json
└── README.md
```

## 🎨 Características del Diseño

### Sistema de Colores
- **Primario**: Azul (#2563eb) - Para elementos principales y navegación
- **Secundario**: Gris (#64748b) - Para texto secundario y elementos de apoyo
- **Éxito**: Verde (#10b981) - Para estados positivos y confirmaciones
- **Advertencia**: Amarillo (#f59e0b) - Para alertas y advertencias
- **Error**: Rojo (#ef4444) - Para errores y estados críticos

### Componentes Reutilizables
- **Cards**: Contenedores con sombra y bordes redondeados
- **Botones**: Múltiples variantes (primary, secondary, success, warning, error)
- **Forms**: Inputs con validación visual y estados de error
- **Tables**: Tablas responsivas con hover effects
- **Badges**: Etiquetas de estado con colores semánticos

### Diseño Responsivo
- **Desktop**: Layout de 2 columnas para dashboard
- **Tablet**: Layout adaptativo con navegación simplificada
- **Móvil**: Layout de una columna con navegación hamburguesa

## 🔐 Autenticación

### Credenciales de Prueba
- **Usuario**: juan
- **Contraseña**: [la que configuraste al crear el superusuario]

### Flujo de Autenticación
1. Login con credenciales
2. Recepción de JWT token
3. Almacenamiento en localStorage
4. Intercepción automática en requests
5. Renovación automática de token
6. Logout y limpieza de tokens

## 📊 Funcionalidades del Dashboard

### Tarjetas de Estadísticas
- **Total Productos**: Contador de productos en inventario
- **Valor Total**: Valor monetario total del stock
- **Alertas de Stock**: Número de productos con stock bajo
- **Transacciones Hoy**: Movimientos del día actual

### Gráficos y Visualizaciones
- **Niveles de Stock**: Barras de progreso por almacén
- **Transacciones Recientes**: Lista de movimientos recientes
- **Alertas**: Panel de notificaciones y advertencias

## 🔌 Integración con Backend

### Endpoints Utilizados
- `POST /api/auth/login/` - Autenticación
- `GET /api/auth/profile/` - Perfil de usuario
- `GET /api/inventory/products/` - Lista de productos
- `GET /api/inventory/inventory/` - Estado de inventario
- `GET /api/alerts/alerts/` - Alertas activas
- `GET /api/reports/reports/` - Reportes disponibles

### Manejo de Errores
- Interceptores Axios para respuestas HTTP
- Manejo automático de errores 401 (No autorizado)
- Mensajes de error amigables al usuario
- Retry automático para fallos de red

## 🚀 Despliegue

### Desarrollo Local
```bash
npm start
```

### Construcción para Producción
```bash
npm run build
npm install -g serve
serve -s build -l 3000
```

### Variables de Entorno para Producción
```env
REACT_APP_API_URL=https://api.tu-dominio.com/api
REACT_APP_APP_NAME=DataLens
```

## 🧪 Testing

```bash
# Ejecutar tests
npm test

# Tests con coverage
npm test -- --coverage

# Linting
npm run lint
npm run lint:fix
```

## 📝 Próximas Funcionalidades

- [ ] Gestión completa de productos (CRUD)
- [ ] Módulo de reportes avanzados
- [ ] Sistema de notificaciones en tiempo real
- [ ] Gestión de usuarios y permisos
- [ ] Forecasting y predicciones
- [ ] Exportación de datos (PDF, Excel)
- [ ] Configuración de empresa
- [ ] Modo oscuro
- [ ] PWA (Progressive Web App)

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte técnico o consultas:
- Email: soporte@datalens.pe
- GitHub Issues: [Crear Issue](https://github.com/tu-usuario/datalens/issues)

---

**DataLens** - Transformando la gestión de inventarios para PYMEs peruanas 🇵🇪
