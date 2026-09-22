import axios from 'axios';

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api', timeout: 20000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing;
api.interceptors.response.use((response) => response, async (error) => {
  const original = error.config;
  if (error.response?.status !== 401 || original?._retry || original?.url?.includes('/auth/refresh')) throw error;
  original._retry = true;
  refreshing ||= api.post('/auth/refresh', { refresh_token: localStorage.getItem('refresh_token') })
    .then(({ data }) => {
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return data.access_token;
    }).finally(() => { refreshing = null; });
  original.headers.Authorization = `Bearer ${await refreshing}`;
  return api(original);
});

export default api;
