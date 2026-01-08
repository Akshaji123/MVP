import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = `${BACKEND_URL}/api`;

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);

export const auth = {
  register: (data) => apiClient.post('/auth/register', data),
  login: (data) => apiClient.post('/auth/login', data),
  me: () => apiClient.get('/auth/me'),
};

export const jobs = {
  getAll: (params) => apiClient.get('/jobs', { params }),
  getById: (id) => apiClient.get(`/jobs/${id}`),
  create: (data) => apiClient.post('/jobs', data),
};

export const resumes = {
  getAll: () => apiClient.get('/resumes'),
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/resumes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const applications = {
  getAll: (params) => apiClient.get('/applications', { params }),
  create: (data) => apiClient.post('/applications', data),
  updateStatus: (id, status) => apiClient.patch(`/applications/${id}/status`, null, {
    params: { status }
  }),
};

export const referrals = {
  getAll: () => apiClient.get('/referrals'),
  create: (data) => apiClient.post('/referrals', data),
};

export const dashboard = {
  getStats: () => apiClient.get('/dashboard/stats'),
};

export const leaderboard = {
  get: () => apiClient.get('/leaderboard'),
};

export const users = {
  getAll: (params) => apiClient.get('/users', { params }),
};

export default apiClient;