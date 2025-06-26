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

export interface CV {
  id: number;
  original_content: string;
  improved_content?: string;
  feedback?: string;
  status: string;
  created_at: string;
}

export class CVService {
  async improveCV(originalContent: string): Promise<CV> {
    const response = await apiClient.post('/api/cv/improve', {
      original_content: originalContent,
    });
    return response.data;
  }

  async getCVHistory(): Promise<CV[]> {
    const response = await apiClient.get('/api/cv/history');
    return response.data;
  }

  async getCV(id: number): Promise<CV> {
    const response = await apiClient.get(`/api/cv/${id}`);
    return response.data;
  }

  async deleteCV(id: number): Promise<void> {
    await apiClient.delete(`/api/cv/${id}`);
  }
}

export const cvService = new CVService();