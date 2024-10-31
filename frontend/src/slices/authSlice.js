// src/slices/authSlice.js

import {createSlice, createAsyncThunk} from '@reduxjs/toolkit';
import {axiosInstance} from '../routes/axiosInstance';

export const login = createAsyncThunk(
  'auth/login',
  async ({ email, password, rememberMe }, { rejectWithValue }) => {
    try {
      // Authenticate user and get tokens
      const response = await axiosInstance.post('/admin/token', { email, password });
      
      if (response.status === 200) {
        const { access: accessToken, refresh: refreshToken } = response.data;
        // Store tokens in local storage
        localStorage.setItem('authToken', accessToken);
        localStorage.setItem('refreshToken', refreshToken);
        if (rememberMe) {
          localStorage.setItem('rememberMe', 'true');
        }
        
        return { accessToken, refreshToken };
      }
    } catch (error) {
      if (error.response && error.response.data) {
        if (error.response.data.non_field_errors) {
          // Handle non_field_errors
          return rejectWithValue(error.response.data.non_field_errors[0]);
        } else if (error.response.data.detail) {
          // Handle other error messages
          return rejectWithValue(error.response.data.detail);
        } else {
          return rejectWithValue('An unexpected error occurred.');
        }
      } else {
        return rejectWithValue('Something went wrong. Please try again.');
      }
    }
  }
);

export const refreshAccessToken = createAsyncThunk(
  'auth/refreshAccessToken',
  async (_, { getState, rejectWithValue }) => {
    const { refreshToken } = getState().auth;
    try {
      const response = await axiosInstance.post('/token/refresh/', {
        refresh: refreshToken,
      });
      const { access: accessToken } = response.data;
      
      // Store the new access token
      localStorage.setItem('authToken', accessToken);
      return accessToken;
    } catch (error) {
      return rejectWithValue('Failed to refresh access token.');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    isAuth: localStorage.getItem('authToken') !== null,
    token: localStorage.getItem('authToken'),
    refreshToken: localStorage.getItem('refreshToken'),
    errorMessage: '',
    loading: false,
  },
  reducers: {
    // Synchronous logout action
    logout(state) {
      state.user = null;
      state.token = null;
      localStorage.removeItem('user');
      localStorage.removeItem('authToken');
      state.successMessage = 'Logged out successfully.';
      state.error = null;
    },
    clearAuthMessages(state) {
      state.error = null;
      state.successMessage = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Handle login actions
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.errorMessage = '';
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuth = true;
        state.token = action.payload.accessToken;
        state.refreshToken = action.payload.refreshToken;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.errorMessage = action.payload || 'Login failed.';
      })
      // Handle refresh token actions
      .addCase(refreshAccessToken.fulfilled, (state, action) => {
        state.token = action.payload;
      })
      .addCase(refreshAccessToken.rejected, (state) => {
        state.isAuth = false;
        state.token = null;
        state.refreshToken = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
      });
  },
});

export const { logout, clearAuthMessages } = authSlice.actions;
export default authSlice.reducer;
// Export selectors

export const selectAuthUser = (state) => state.auth.user;
export const selectAuthToken = (state) => state.auth.token;
export const selectAuthRefreshToken = (state) => state.auth.refreshToken;
export const selectAuthLoading = (state) => state.auth.loading;
export const selectAuthError = (state) => state.auth.error;
export const selectAuthSuccessMessage = (state) => state.auth.successMessage;