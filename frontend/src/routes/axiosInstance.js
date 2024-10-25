import axios from 'axios';

// Create an Axios instance with a base URL
const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL
});

// You can set other global configurations like headers here
axiosInstance.defaults.headers.common['Content-Type'] = 'application/json';

export default axiosInstance;
