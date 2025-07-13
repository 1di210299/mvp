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
  email_notifications?: boolean;
  whatsapp_notifications?: boolean;
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
  email: string;
  password: string;
}

export interface AuthResponse {
  tokens: {
    access: string;
    refresh: string;
  };
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
  stock?: number;
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

export interface Supplier {
  id: number;
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  country?: string;
  tax_id?: string;
  payment_terms?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
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
  product: Product;
  warehouse?: number | Warehouse;
  location?: number;
  transaction_type: 'IN' | 'OUT' | 'PURCHASE' | 'SALE' | 'TRANSFER' | 'ADJUSTMENT' | 'RETURN';
  quantity: number;
  unit_cost?: number;
  reference_number?: string;
  notes?: string;
  created_by?: number | User;
  created_at: string;
}

// Tipos para forecasting
export interface ForecastModel {
  id: number;
  name: string;
  model_type: 'prophet' | 'arima' | 'linear_regression' | 'random_forest' | 'lstm';
  status: 'training' | 'active' | 'deprecated' | 'failed';
  accuracy_score?: number;
  mae?: number;
  mape?: number;
  rmse?: number;
  r2_score?: number;
  created_at: string;
  updated_at: string;
}

export interface DemandForecast {
  id: number;
  product: number;
  forecast_date: string;
  forecast_type: 'daily' | 'weekly' | 'monthly';
  predicted_demand: number;
  lower_bound: number;
  upper_bound: number;
  confidence_level: number;
  seasonality_factor?: number;
  trend_factor?: number;
  external_factors?: Record<string, any>;
  created_at: string;
}

export interface ReorderRecommendation {
  id: number;
  product: number;
  recommended_quantity: number;
  current_stock: number;
  projected_demand: number;
  recommended_order_date: string;
  expected_stockout_date?: string;
  lead_time_days: number;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'approved' | 'ordered' | 'received' | 'cancelled';
  estimated_cost: number;
  potential_lost_sales?: number;
  notes?: string;
  created_at: string;
}

// Tipos para alertas mejoradas
export interface AlertRule {
  id: number;
  name: string;
  description?: string;
  alert_type: 'low_stock' | 'high_stock' | 'expiration' | 'expired' | 'high_demand' | 
              'demand_vs_stock' | 'stockout_risk' | 'reorder_urgent' | 'forecast_accuracy' | 
              'seasonal_demand' | 'no_movement' | 'negative_stock' | 'inventory_value' | 
              'supplier_delay' | 'abc_analysis';
  threshold_value?: number;
  threshold_percentage?: number;
  days_before_expiration?: number;
  forecast_horizon_days?: number;
  accuracy_threshold?: number;
  seasonal_factor_threshold?: number;
  send_email: boolean;
  send_whatsapp: boolean;
  send_notification: boolean;
  frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
  recipients: User[];
  additional_emails?: string;
  additional_phones?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

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
  source: 'rule' | 'system' | 'forecast' | 'manual';
  current_value?: number;
  threshold_value?: number;
  priority_score?: number;
  context_data?: Record<string, any>;
  recommended_actions?: string[];
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
  // Forecasting related fields
  demand_forecast?: {
    id: number;
    predicted_demand: number;
    lower_bound: number;
    upper_bound: number;
    confidence_level: number;
    forecast_date: string;
  };
  reorder_recommendation?: {
    id: number;
    recommended_quantity: number;
    recommended_order_date: string;
    priority: string;
    estimated_cost?: number;
    expected_stockout_date?: string;
    lead_time_days?: number;
  };
  forecast_model?: {
    id: number;
    name: string;
    model_type: string;
    accuracy_score?: number;
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
  notification_stats?: Record<string, number>;
  recent_alerts: AlertData[];
  alert_trends: Record<string, number>;
}

export interface NotificationLog {
  id: number;
  alert: AlertData;
  notification_type: 'email' | 'whatsapp' | 'in_app' | 'sms' | 'webhook';
  recipient: string;
  subject?: string;
  content: string;
  status: 'pending' | 'sent' | 'failed' | 'delivered';
  sent_at?: string;
  delivered_at?: string;
  error_message?: string;
  whatsapp_message_id?: string;
  created_at: string;
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

// Tipos para filtros de alertas
export interface AlertFilters {
  severity?: string;
  status?: string;
  alert_type?: string;
  source?: string;
  product_id?: number;
  location_id?: number;
  created_after?: string;
  created_before?: string;
}

// Tipos para métricas de alertas
export interface AlertMetrics {
  total_alerts: number;
  active_alerts: number;
  resolved_alerts: number;
  critical_alerts: number;
  avg_resolution_time: number;
  alerts_by_type: Record<string, number>;
  alerts_by_severity: Record<string, number>;
  forecasting_alerts: number;
  notification_success_rate: number;
}
