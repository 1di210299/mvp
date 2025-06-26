import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Payment {
  id: number;
  amount: number;
  currency: string;
  status: string;
  subscription_type: string;
  expires_at?: string;
  created_at: string;
}

export interface PaymentRequest {
  subscription_type: string;
  payment_method: string;
}

export interface SubscriptionStatus {
  is_premium: boolean;
  subscription_active: boolean;
  subscription_type?: string;
  expires_at?: string;
  available_plans: {
    [key: string]: {
      price: number;
      currency: string;
      description: string;
      discount?: string;
    };
  };
}

export class PaymentService {
  async createPayment(data: PaymentRequest): Promise<Payment> {
    const response = await apiClient.post('/api/payments/create', data);
    return response.data;
  }

  async simulatePaymentSuccess(paymentId: number): Promise<void> {
    await apiClient.post(`/api/payments/simulate-success/${paymentId}`);
  }

  async getPaymentHistory(): Promise<Payment[]> {
    const response = await apiClient.get('/api/payments/history');
    return response.data;
  }

  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    const response = await apiClient.get('/api/payments/subscription-status');
    return response.data;
  }
}

export const paymentService = new PaymentService();