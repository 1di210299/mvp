import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';

// Layouts
import MainLayout from './components/layout/MainLayout';

// Páginas
import Dashboard from './components/dashboard/Dashboard';
import ProductList from './components/products/ProductList';
import ProductDetails from './components/products/ProductDetails';
import OrderList from './components/orders/OrderList';
import OrderDetails from './components/orders/OrderDetails';
import CustomerList from './components/customers/CustomerList';
import CustomerDetails from './components/customers/CustomerDetails';
import SecurityIncidents from './components/security/SecurityIncidents';
import SecurityIncidentDetails from './components/security/SecurityIncidentDetails';
import Login from './components/auth/Login';

// Redux y servicios
import { useSelector, useDispatch } from 'react-redux';
import { autoLogin } from './store/authSlice';

function App() {
  const dispatch = useDispatch();
  const { isAuthenticated, isLoading } = useSelector(state => state.auth);
  const [appReady, setAppReady] = useState(false);

  useEffect(() => {
    // Intentar auto-login con token almacenado
    dispatch(autoLogin());
    setAppReady(true);
  }, [dispatch]);

  if (!appReady || isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Componente para rutas protegidas
  const ProtectedRoute = ({ children }) => {
    if (!isAuthenticated) {
      return <Navigate to="/login" />;
    }
    return children;
  };

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="products" element={<ProductList />} />
        <Route path="products/:id" element={<ProductDetails />} />
        <Route path="orders" element={<OrderList />} />
        <Route path="orders/:id" element={<OrderDetails />} />
        <Route path="customers" element={<CustomerList />} />
        <Route path="customers/:id" element={<CustomerDetails />} />
        <Route path="security" element={<SecurityIncidents />} />
        <Route path="security/:id" element={<SecurityIncidentDetails />} />
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;