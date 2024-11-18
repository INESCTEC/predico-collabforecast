// src/store.js
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice'; // We'll create this next
import userReducer from './userSlice'; // We'll create this next
import preferencesReducer from "./preferencesSlice";

const store = configureStore({
  reducer: {
    auth: authReducer,
    user: userReducer,
    preferences: preferencesReducer,
    // Add other reducers here if needed
  },
});

export default store;