// User types
export interface User {
  id: number;
  email: string;
  full_name: string;
  is_premium: boolean;
  subscription_type?: string;
  created_at: string;
}

// Auth types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ErrorResponse {
  detail: string;
}

// CV types (imported from services, but defined here for consistency)
export interface CV {
  id: number;
  user_id: number;
  original_content: string;
  improved_content?: string;
  feedback?: string;
  status: 'processing' | 'completed' | 'error';
  created_at: string;
}

// Cover Letter types
export interface CoverLetter {
  id: number;
  user_id: number;
  job_title: string;
  company_name: string;
  job_description?: string;
  user_experience?: string;
  generated_content?: string;
  created_at: string;
}

// Interview types
export interface Interview {
  id: number;
  user_id: number;
  job_title: string;
  company_name?: string;
  current_question?: string;
  status: 'active' | 'completed';
  created_at: string;
}

export interface InterviewChat {
  id: number;
  interview_id: number;
  question: string;
  user_response?: string;
  feedback?: string;
  created_at: string;
}

// Payment types
export interface Payment {
  id: number;
  user_id: number;
  subscription_type: string;
  amount: number;
  status: 'pending' | 'completed' | 'failed';
  payment_method: string;
  created_at: string;
}

export interface SubscriptionStatus {
  is_premium: boolean;
  subscription_type?: string;
  expires_at?: string;
}