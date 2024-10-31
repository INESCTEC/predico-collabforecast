import axios from 'axios';
import store from '../slices/store';
import {logout, refreshAccessToken, selectAuthToken} from '../slices/authSlice';

const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to add the access token to all requests
axiosInstance.interceptors.request.use(
  (config) => {
    const token = selectAuthToken(store.getState());
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle token refresh on 401 errors
axiosInstance.interceptors.response.use(
  response => response, // Pass through successful responses
  async error => {
    const originalRequest = error.config;
    
    // If error is due to an expired access token (401)
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Attempt to refresh the access token
        const newAccessToken = await store.dispatch(refreshAccessToken()).unwrap();
        
        // Update authorization header with new access token
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        console.log("Access token refreshed. Retrying original request...");
        // Retry the original request with the new token
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // Refresh token is also expired or invalid; log out the user
        store.dispatch(logout());
        window.location.href = '/signin'; // Redirect to sign-in page
      }
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
