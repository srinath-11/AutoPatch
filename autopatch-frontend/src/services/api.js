import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // Increased timeout for container operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service functions
export const apiService = {
  // Health check
  checkHealth: () => api.get('/health'),
  
  // Containers
  getContainers: () => api.get('/containers'),
  restartContainer: (name) => api.post(`/container/${name}/restart`),
  stopContainer: (name) => api.post(`/container/${name}/stop`),
  
  // Updates
  checkUpdates: () => api.get('/check-updates'),
  runUpdate: () => api.post('/run-update'),
  
  // System info
  getSystemInfo: () => api.get('/system-info'),
};

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.error('💡 Backend server is not running. Please start the Flask server:');
      console.error('   cd "C:\\Users\\moham\\Projects\\Linux project\\AutoPatch"');
      console.error('   python src\\api_server.py');
    }
    
    if (error.response) {
      // Server responded with error status
      console.error(`📊 Server error ${error.response.status}:`, error.response.data);
    } else if (error.request) {
      // Request was made but no response received
      console.error('📡 No response received from server');
    }
    
    return Promise.reject(error);
  }
);

export default api;