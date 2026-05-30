import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

export const startAnalysis = async (target_url) => {
    const response = await axios.post(`${API_URL}/analyze`, { target_url });
    return response.data;
};

export const getAnalysisStatus = async (analysis_id) => {
    const response = await axios.get(`${API_URL}/analyze/${analysis_id}`);
    return response.data;
};
