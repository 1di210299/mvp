// Tipos para autenticación
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'superadmin' | 'admin' | 'analyst';
  company: Company;
  phone?: string;
  position?: string;
  department?: string;
  is_active: boolean;
  created_at: string;
}

export interface Company {
  id: number;
  name: string;
  ruc: string;
  address: string;
  phone?: string;
  email: string;
  industry?: string;
  website?: string;
  subscription_type: 'trial' | 'basic' | 'premium';
  is_active: boolean;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

// Tipos para inventarios
export interface Product {
  id: number;
  name: string;
  sku: string;
  description?: string;
  category: number;
  category_name?: string;
  supplier?: number;
  supplier_name?: string;
  unit_price?: number;
  cost_price: number | string;
  sale_price?: number | string;
  min_stock: number | string;
  max_stock: number | string;
  reorder_point: number | string;
  weight?: number | string;
  dimensions?: string;
  unit: string;
  barcode?: string;
  track_batches: boolean;
  has_expiration: boolean;
  shelf_life_days?: number;
  current_stock?: number;
  stock_value?: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface Warehouse {
  id: number;
  name: string;
  address: string;
  manager?: string;
  phone?: string;
  is_active: boolean;
}

export interface Inventory {
  id: number;
  product: Product;
  location: Location;
  quantity: number;
  reserved_quantity: number;
  unit_cost: number;
  batch_number?: string;
  manufacturing_date?: string;
  expiration_date?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Location {
  id: number;
  name: string;
  code: string;
  description?: string;
  warehouse: string;
  zone?: string;
  aisle?: string;
  rack?: string;
  shelf?: string;
  is_active: boolean;
}

export interface Transaction {
  id: number;
  product: Product; // Always a complete Product object for display purposes
  warehouse?: number | Warehouse; // Puede ser ID o objeto completo
  location?: number; // Para ubicaciones específicas
  transaction_type: 'IN' | 'OUT' | 'PURCHASE' | 'SALE' | 'TRANSFER' | 'ADJUSTMENT' | 'RETURN';
  quantity: number;
  unit_cost?: number;
  reference_number?: string;
  notes?: string;
  created_by?: number | User;
  created_at: string;
}

// Tipos para alertas
export interface Alert {
  id: number;
  title: string;
  message: string;
  alert_type: 'low_stock' | 'high_stock' | 'expired' | 'reorder_point' | 'custom';
  severity: 'low' | 'medium' | 'high' | 'critical';
  is_read: boolean;
  is_resolved: boolean;
  product?: Product;
  warehouse?: Warehouse;
  created_at: string;
}

export interface AlertData {
  id: number;
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved' | 'dismissed';
  current_value: number;
  threshold_value: number;
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  product_data?: {
    id: number;
    name: string;
    sku: string;
  };
  location_data?: {
    id: number;
    name: string;
  };
  rule_data?: {
    id: number;
    name: string;
    alert_type: string;
  };
}

// Tipos para reportes
export interface Report {
  id: number;
  title: string;
  report_type: 'inventory' | 'sales' | 'financial' | 'movement' | 'forecast';
  filters: Record<string, any>;
  data: Record<string, any>;
  created_by: User;
  created_at: string;
}

// Tipos para dashboard
export interface DashboardStats {
  total_products: number;
  total_value: number;
  low_stock_alerts: number;
  total_transactions_today: number;
  top_products: Array<{
    product: Product;
    quantity: number;
    value: number;
  }>;
  stock_levels: Array<{
    warehouse: string;
    current_stock: number;
    min_stock: number;
    max_stock: number;
  }>;
}

export interface DashboardData {
  total_alerts: number;
  active_alerts: number;
  critical_alerts: number;
  acknowledged_alerts: number;
  resolved_alerts: number;
  alerts_by_severity: Record<string, number>;
  alerts_by_type: Record<string, number>;
  recent_alerts: AlertData[];
  alert_trends: Record<string, number>;
}

// Tipos para forecasting
export interface ForecastData {
  product: Product;
  warehouse: Warehouse;
  predicted_demand: number;
  confidence_interval: {
    lower: number;
    upper: number;
  };
  period: string;
  created_at: string;
}

// Tipos para API responses
export interface ApiResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
}
