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

export interface Interview {
  id: number;
  job_title: string;
  company_name?: string;
  current_question?: string;
  feedback?: string;
  status: string;
  created_at: string;
}

export interface InterviewRequest {
  job_title: string;
  company_name?: string;
}

export interface InterviewChat {
  question: string;
  feedback?: string;
  next_question?: string;
}

export class InterviewService {
  async startInterview(data: InterviewRequest): Promise<Interview> {
    const response = await apiClient.post('/api/interview/start', data);
    return response.data;
  }

  async respondToInterview(interviewId: number, userResponse: string): Promise<InterviewChat> {
    const response = await apiClient.post(`/api/interview/${interviewId}/respond`, {
      user_response: userResponse,
    });
    return response.data;
  }

  async finishInterview(interviewId: number): Promise<void> {
    await apiClient.put(`/api/interview/${interviewId}/finish`);
  }

  async getInterviewHistory(): Promise<Interview[]> {
    const response = await apiClient.get('/api/interview/history');
    return response.data;
  }

  async getInterview(id: number): Promise<Interview> {
    const response = await apiClient.get(`/api/interview/${id}`);
    return response.data;
  }

  async deleteInterview(id: number): Promise<void> {
    await apiClient.delete(`/api/interview/${id}`);
  }
}

export const interviewService = new InterviewService();