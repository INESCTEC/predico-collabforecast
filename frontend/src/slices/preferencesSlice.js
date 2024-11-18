// src/slices/preferencesSlice.js

import { createSlice } from '@reduxjs/toolkit';

// Define default preferences
const defaultPreferences = {
  newUsersOverTimeDays: 28, // 4 weeks
  activeUsersHours: 48,
  newRegistrationsDays: 14, // 2 weeks
};

// Function to load preferences from localStorage
const loadPreferences = () => {
  try {
    const serializedPrefs = localStorage.getItem('userPreferences');
    if (serializedPrefs === null) {
      return defaultPreferences;
    }
    return JSON.parse(serializedPrefs);
  } catch (err) {
    console.error('Could not load preferences from localStorage:', err);
    return defaultPreferences;
  }
};

// Function to save preferences to localStorage
const savePreferences = (preferences) => {
  try {
    const serializedPrefs = JSON.stringify(preferences);
    localStorage.setItem('userPreferences', serializedPrefs);
  } catch (err) {
    console.error('Could not save preferences to localStorage:', err);
  }
};

const preferencesSlice = createSlice({
  name: 'preferences',
  initialState: loadPreferences(),
  reducers: {
    setNewUsersOverTimeDays(state, action) {
      state.newUsersOverTimeDays = action.payload;
      savePreferences(state);
    },
    setActiveUsersHours(state, action) {
      state.activeUsersHours = action.payload;
      savePreferences(state);
    },
    setNewRegistrationsDays(state, action) {
      state.newRegistrationsDays = action.payload;
      savePreferences(state);
    },
    resetPreferences(state) {
      Object.assign(state, defaultPreferences);
      savePreferences(state);
    },
  },
});

export const {
  setNewUsersOverTimeDays,
  setActiveUsersHours,
  setNewRegistrationsDays,
  resetPreferences,
} = preferencesSlice.actions;

export const selectNewUsersOverTimeDays = (state) =>
  state.preferences.newUsersOverTimeDays;
export const selectActiveUsersHours = (state) =>
  state.preferences.activeUsersHours;
export const selectNewRegistrationsDays = (state) =>
  state.preferences.newRegistrationsDays;

export default preferencesSlice.reducer;
