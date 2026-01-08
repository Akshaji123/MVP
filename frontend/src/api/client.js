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

// New API modules for enterprise features
export const companies = {
  getAll: (params) => apiClient.get('/companies', { params }),
  getById: (id) => apiClient.get(`/companies/${id}`),
  create: (data) => apiClient.post('/companies', data),
  update: (id, data) => apiClient.put(`/companies/${id}`, data),
  delete: (id) => apiClient.delete(`/companies/${id}`),
  getJobs: (id, params) => apiClient.get(`/companies/${id}/jobs`, { params }),
  getStats: (id) => apiClient.get(`/companies/${id}/stats`),
};

export const candidates = {
  getAll: (params) => apiClient.get('/candidates', { params }),
  getById: (id) => apiClient.get(`/candidates/${id}`),
  create: (data) => apiClient.post('/candidates', data),
  update: (id, data) => apiClient.put(`/candidates/${id}`, data),
  getMe: () => apiClient.get('/candidates/me'),
  getApplications: (id, params) => apiClient.get(`/candidates/${id}/applications`, { params }),
  addSkills: (id, skills) => apiClient.post(`/candidates/${id}/skills`, skills),
  matchJobs: (id, params) => apiClient.get(`/candidates/${id}/match-jobs`, { params }),
};

export const interviews = {
  getAll: (params) => apiClient.get('/interviews', { params }),
  getById: (id) => apiClient.get(`/interviews/${id}`),
  create: (data) => apiClient.post('/interviews', data),
  update: (id, data) => apiClient.put(`/interviews/${id}`, data),
  submitFeedback: (id, data) => apiClient.post(`/interviews/${id}/feedback`, data),
  cancel: (id, reason) => apiClient.post(`/interviews/${id}/cancel`, null, { params: { reason } }),
  getCalendar: (days) => apiClient.get('/interviews/calendar/upcoming', { params: { days } }),
};

export const financial = {
  getDashboard: () => apiClient.get('/financial/dashboard'),
  // Commissions
  getCommissions: (params) => apiClient.get('/financial/commissions', { params }),
  getCommission: (id) => apiClient.get(`/financial/commissions/${id}`),
  createCommission: (data) => apiClient.post('/financial/commissions', data),
  updateCommissionStatus: (id, status) => apiClient.put(`/financial/commissions/${id}/status`, null, { params: { new_status: status } }),
  // Payments
  getPayments: (params) => apiClient.get('/financial/payments', { params }),
  createPayment: (data) => apiClient.post('/financial/payments', data),
  processPayment: (id, transactionId) => apiClient.put(`/financial/payments/${id}/process`, null, { params: { transaction_id: transactionId } }),
  // Invoices
  getInvoices: (params) => apiClient.get('/financial/invoices', { params }),
  createInvoice: (data) => apiClient.post('/financial/invoices', data),
  sendInvoice: (id) => apiClient.put(`/financial/invoices/${id}/send`),
  markInvoicePaid: (id) => apiClient.put(`/financial/invoices/${id}/mark-paid`),
  // Payouts
  getPayoutRequests: (params) => apiClient.get('/financial/payout-requests', { params }),
  createPayoutRequest: (data) => apiClient.post('/financial/payout-requests', data),
  approvePayoutRequest: (id) => apiClient.put(`/financial/payout-requests/${id}/approve`),
};

export const communication = {
  // Messages
  getInbox: (params) => apiClient.get('/communication/messages/inbox', { params }),
  getSent: (params) => apiClient.get('/communication/messages/sent', { params }),
  getMessage: (id) => apiClient.get(`/communication/messages/${id}`),
  sendMessage: (data) => apiClient.post('/communication/messages', data),
  replyMessage: (id, data) => apiClient.post(`/communication/messages/${id}/reply`, data),
  getUnreadCount: () => apiClient.get('/communication/messages/unread-count'),
  // Email Templates
  getEmailTemplates: (params) => apiClient.get('/communication/email-templates', { params }),
  getEmailTemplate: (id) => apiClient.get(`/communication/email-templates/${id}`),
  createEmailTemplate: (data) => apiClient.post('/communication/email-templates', data),
  updateEmailTemplate: (id, data) => apiClient.put(`/communication/email-templates/${id}`, data),
  deleteEmailTemplate: (id) => apiClient.delete(`/communication/email-templates/${id}`),
  previewEmailTemplate: (id, variables) => apiClient.post(`/communication/email-templates/${id}/preview`, variables),
  // Logs
  getCommunicationLogs: (params) => apiClient.get('/communication/logs', { params }),
};

export default apiClient;