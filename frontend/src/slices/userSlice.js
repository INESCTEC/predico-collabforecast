import {createSlice, createAsyncThunk} from '@reduxjs/toolkit';
import axiosInstance from '../routes/axiosInstance';

// Thunk to fetch logged-in user details
export const fetchUserDetails = createAsyncThunk(
  'user/fetchUserDetails',
  async (_, { getState, rejectWithValue }) => {
    try {
      const response = await axiosInstance.get('/user/user-detail');
      return response.data;
    } catch (error) {
      return rejectWithValue('Failed to fetch user details.');
    }
  }
);

// Thunk to fetch list of users
export const fetchUsers = createAsyncThunk(
  'user/fetchUsers',
  async (_, { getState, rejectWithValue }) => {
    try {
      const response = await axiosInstance.get('/user/list');
      return response.data.data;
    } catch (error) {
      return rejectWithValue('Failed to fetch users.');
    }
  }
);

// Thunk to send an invitation
export const sendInvite = createAsyncThunk(
  'user/sendInvite',
  async (email, { getState, rejectWithValue }) => {
    try {
      const response = await axiosInstance.post(
        '/user/register-invite',
        { email });
      // Assuming the response structure contains the invitation link at response.data.data.link
      return response.data.data.link;
    } catch (error) {
      // Extract detailed error message if available
      if (error.response && error.response.data && error.response.data.message) {
        return rejectWithValue(error.response.data.message);
      }
      return rejectWithValue('Error sending invitation. Please try again.');
    }
  }
);

const userSlice = createSlice({
  name: 'user',
  initialState: {
    userDetails: {},
    usersList: [],
    loading: false,
    errorMessage: '',
    successMessage: '',
    invitationLink: '',
  },
  reducers: {
    clearUserMessages(state) {
      state.errorMessage = '';
      state.successMessage = '';
    },
    clearInvitationLink(state) {
      state.invitationLink = '';
    },
    // Add other user-related reducers if necessary
  },
  extraReducers: (builder) => {
    builder
      // Handle fetchUserDetails actions
      .addCase(fetchUserDetails.pending, (state) => {
        state.loading = true;
        state.errorMessage = '';
      })
      .addCase(fetchUserDetails.fulfilled, (state, action) => {
        state.loading = false;
        state.userDetails = action.payload;
      })
      .addCase(fetchUserDetails.rejected, (state, action) => {
        state.loading = false;
        state.errorMessage = action.payload || 'Failed to fetch user details.';
      })
      // Handle fetchUsers actions
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.errorMessage = '';
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.usersList = action.payload;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.errorMessage = action.payload || 'Failed to fetch users.';
      })
      // Handle sendInvite actions
      .addCase(sendInvite.pending, (state) => {
        state.loading = true;
        state.errorMessage = '';
        state.successMessage = '';
        state.invitationLink = '';
      })
      .addCase(sendInvite.fulfilled, (state, action) => {
        state.loading = false;
        state.successMessage = 'Invitation sent successfully.';
        state.invitationLink = action.payload; // The invitation link
      })
      .addCase(sendInvite.rejected, (state, action) => {
        state.loading = false;
        state.errorMessage = action.payload || 'Failed to send invitation.';
      });
  },
});

export const { clearUserMessages, clearInvitationLink } = userSlice.actions;
export default userSlice.reducer;
export const selectUserDetails = (state) => state.user.userDetails;
export const selectUsersList = (state) => state.user.usersList;
export const selectUserLoading = (state) => state.user.loading;
export const selectUserError = (state) => state.user.errorMessage;
export const selectUserSuccess = (state) => state.user.successMessage;
export const selectInvitationLink = (state) => state.user.invitationLink;