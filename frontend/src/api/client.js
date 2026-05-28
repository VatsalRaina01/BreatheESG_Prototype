import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401 and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/api/auth/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem('access_token', data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } else {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Auth
export const login = (email, password) =>
  api.post('/auth/login/', { email, password });

// Data Sources
export const getSources = () => api.get('/sources/');
export const createSource = (data) => api.post('/sources/', data);

// Ingestion
export const uploadFile = (formData) =>
  api.post('/ingest/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const getJobs = () => api.get('/ingest/jobs/');
export const getJob = (id) => api.get(`/ingest/jobs/${id}/`);

// Records
export const getRecords = (params) => api.get('/records/', { params });
export const getRecord = (id) => api.get(`/records/${id}/`);
export const approveRecord = (id, comment = '') =>
  api.post(`/records/${id}/approve/`, { comment });
export const rejectRecord = (id, comment = '') =>
  api.post(`/records/${id}/reject/`, { comment });
export const flagRecord = (id, reasons) =>
  api.post(`/records/${id}/flag/`, { reasons });
export const lockRecord = (id) =>
  api.post(`/records/${id}/lock/`);
export const bulkApprove = (ids) =>
  api.post('/records/bulk-approve/', { ids });
export const bulkReject = (ids, comment = '') =>
  api.post('/records/bulk-reject/', { ids, comment });

// Dashboard
export const getDashboardSummary = () => api.get('/dashboard/summary/');

export default api;
