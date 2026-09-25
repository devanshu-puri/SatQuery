import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const fetchHealth = async () => {
    const response = await axios.get(`${API_BASE_URL}/healthz`);
    return response.data;
};

export const fetchModels = async () => {
    const response = await axios.get(`${API_BASE_URL}/models`);
    return response.data;
};

export const fetchDemoSamples = async () => {
    const response = await axios.get(`${API_BASE_URL}/demo/samples`);
    return response.data;
};

export const fetchSessionHistory = async (sessionId = 'default_session') => {
    const response = await axios.get(`${API_BASE_URL}/session/${sessionId}/history`);
    return response.data;
};

export const uploadRasterFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const fetchGEE = async (payload) => {
    const response = await axios.post(`${API_BASE_URL}/fetch/gee`, payload);
    return response.data;
};

export const executeQuery = async (payload) => {
    const response = await axios.post(`${API_BASE_URL}/query`, payload);
    return response.data;
};

export const downloadPdfReport = async (queryResult, imageBase64) => {
    const response = await axios.post(
        `${API_BASE_URL}/report/pdf`,
        {
            query_result: queryResult,
            image_base64: imageBase64,
        },
        {
            responseType: 'blob',
        }
    );
    return response.data;
};

// Benchmark Evaluation APIs
export const fetchEvalResults = async () => {
    const response = await axios.get(`${API_BASE_URL}/eval-results`);
    return response.data;
};

export const fetchBenchmarkReceipt = async (benchmarkName) => {
    const response = await axios.get(`${API_BASE_URL}/eval-results/${benchmarkName}`);
    return response.data;
};

export const runBenchmarkEvaluation = async () => {
    const response = await axios.post(`${API_BASE_URL}/eval-results/run`);
    return response.data;
};

// Legacy compatibility
export const fetchStates = async () => {
    const response = await axios.get(`${API_BASE_URL}/states`);
    return response.data;
};

export const fetchAreas = async (state) => {
    const response = await axios.get(`${API_BASE_URL}/areas/${state}`);
    return response.data;
};

export const fetchLocation = async (state, area) => {
    const response = await axios.get(`${API_BASE_URL}/location/${encodeURIComponent(state)}/${encodeURIComponent(area)}`);
    return response.data;
};

export const runAgentAnalysis = executeQuery;
