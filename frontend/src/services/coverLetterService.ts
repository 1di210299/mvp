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

export interface CoverLetter {
  id: number;
  job_title: string;
  company_name: string;
  job_description?: string;
  user_experience?: string;
  generated_content?: string;
  status: string;
  created_at: string;
}

export interface CoverLetterRequest {
  job_title: string;
  company_name: string;
  job_description?: string;
  user_experience?: string;
}

export class CoverLetterService {
  async generateCoverLetter(data: CoverLetterRequest): Promise<CoverLetter> {
    const response = await apiClient.post('/api/cover-letter/generate', data);
    return response.data;
  }

  async getCoverLetterHistory(): Promise<CoverLetter[]> {
    const response = await apiClient.get('/api/cover-letter/history');
    return response.data;
  }

  async getCoverLetter(id: number): Promise<CoverLetter> {
    const response = await apiClient.get(`/api/cover-letter/${id}`);
    return response.data;
  }

  async deleteCoverLetter(id: number): Promise<void> {
    await apiClient.delete(`/api/cover-letter/${id}`);
  }
}

export const coverLetterService = new CoverLetterService();