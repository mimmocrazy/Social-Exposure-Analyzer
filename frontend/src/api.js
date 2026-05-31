import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_URL,
});

// Interceptor per iniettare il token JWT in ogni richiesta
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = async (email, password) => {
    // OAuth2PasswordRequestForm expects x-www-form-urlencoded
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    const response = await apiClient.post(`/auth/login`, params);
    return response.data;
};

export const register = async (email, password) => {
    const response = await apiClient.post(`/auth/register`, { email, password });
    return response.data;
};

export const startAnalysis = async (target_url, enable_ddg = true, enable_holehe = true, ig_sessionid = null, enable_fb_scan = false, fb_c_user = null, fb_xs = null) => {
    const response = await apiClient.post(`/analyze`, { 
        target_url,
        enable_ddg,
        enable_holehe,
        ig_sessionid,
        enable_fb_scan,
        fb_c_user,
        fb_xs
    });
    return response.data;
};

export const getAnalysisStatus = async (analysis_id) => {
    const response = await apiClient.get(`/analyze/${analysis_id}`);
    return response.data;
};

export const getAnalysisHistory = async () => {
    const response = await apiClient.get(`/history`);
    return response.data;
};
