// SettingsPage.js

import { useEffect } from 'react';
import { InformationCircleIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'; // Added status icons
import { useDispatch, useSelector } from 'react-redux';
import {
  clearUserMessages,
  fetchUserDetails,
  selectUserDetails,
  selectUserError,
  selectUserLoading,
  selectUserSuccess,
} from '../../slices/userSlice';
import {
  selectActiveUsersHours,
  selectNewRegistrationsDays,
  selectNewUsersOverTimeDays,
  setActiveUsersHours,
  setNewRegistrationsDays,
  setNewUsersOverTimeDays,
} from '../../slices/preferencesSlice';
import { toast } from 'react-toastify'; // For user feedback

export default function SettingsPage() {
  const dispatch = useDispatch();
  
  // Selectors to access Redux state
  const userDetails = useSelector(selectUserDetails);
  const loading = useSelector(selectUserLoading);
  const errorMessage = useSelector(selectUserError);
  const successMessage = useSelector(selectUserSuccess);
  
  // Preferences selectors
  const newUsersOverTimeDays = useSelector(selectNewUsersOverTimeDays);
  const activeUsersHours = useSelector(selectActiveUsersHours);
  const newRegistrationsDays = useSelector(selectNewRegistrationsDays);
  
  useEffect(() => {
    dispatch(fetchUserDetails());
  }, [dispatch]);
  
  useEffect(() => {
    if (errorMessage) {
      toast.error(errorMessage);
      dispatch(clearUserMessages());
    }
  }, [errorMessage, dispatch]);
  
  useEffect(() => {
    if (successMessage) {
      toast.success(successMessage);
      dispatch(clearUserMessages());
    }
  }, [successMessage, dispatch]);
  
  // Handle preferences changes
  const handlePreferenceChange = (preferenceType, value) => {
    switch (preferenceType) {
      case 'newUsersOverTimeDays':
        dispatch(setNewUsersOverTimeDays(Number(value)));
        break;
      case 'activeUsersHours':
        dispatch(setActiveUsersHours(Number(value)));
        break;
      case 'newRegistrationsDays':
        dispatch(setNewRegistrationsDays(Number(value)));
        break;
      default:
        break;
    }
  };
  
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-sm text-gray-600">Profile and preferences management.</p>
        <div className="mt-8">Loading...</div>
      </div>
    );
  }
  
  return (
    <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
      <p className="mt-2 text-sm text-gray-600">Profile and preferences management.</p>
      
      {/* Layout Grid */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Information */}
        <div className="lg:col-span-2 space-y-10">
          {/* Profile Information Section */}
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Profile Information</h2>
              <p className="mt-1 text-sm text-gray-600">Your personal information is displayed below.</p>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* First Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700">First Name</label>
                <p className="mt-1 text-sm text-gray-900">{userDetails.first_name || 'N/A'}</p>
              </div>
              
              {/* Last Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Last Name</label>
                <p className="mt-1 text-sm text-gray-900">{userDetails.last_name || 'N/A'}</p>
              </div>
              
              {/* Email Address */}
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700">Email Address</label>
                <p className="mt-1 text-sm text-gray-900">{userDetails.email || 'N/A'}</p>
              </div>
            </div>
          </div>
          
          {/* Account Status Section */}
          <div className="mt-8 space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Account Status</h2>
              <p className="mt-1 text-sm text-gray-600">Your account statuses are displayed below.</p>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              {/* Active Account */}
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-700">Active Account</span>
                <span className="ml-auto">
                  {userDetails.is_active ? (
                    <CheckIcon className="h-5 w-5 text-green-500" aria-hidden="true"/>
                  ) : (
                    <XMarkIcon className="h-5 w-5 text-red-500" aria-hidden="true"/>
                  )}
                </span>
              </div>
              
              {/* Verified Account */}
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-700">Verified Account</span>
                <span className="ml-auto">
                  {userDetails.is_verified ? (
                    <CheckIcon className="h-5 w-5 text-green-500" aria-hidden="true"/>
                  ) : (
                    <XMarkIcon className="h-5 w-5 text-red-500" aria-hidden="true"/>
                  )}
                </span>
              </div>
              
              {/* Superuser Access */}
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-700">Superuser Access</span>
                <span className="ml-auto">
                  {userDetails.is_superuser ? (
                    <CheckIcon className="h-5 w-5 text-green-500" aria-hidden="true"/>
                  ) : (
                    <XMarkIcon className="h-5 w-5 text-red-500" aria-hidden="true"/>
                  )}
                </span>
              </div>
            </div>
          </div>
          
          {/* Preferences Section */}
          <div className="mt-8 space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Preferences</h2>
              <p className="mt-1 text-sm text-gray-600">Customize how data is presented in your charts.</p>
            </div>
            
            <div className="space-y-4">
              {/* New Users Over Time */}
              <div>
                <label htmlFor="newUsersOverTime" className="block text-sm font-medium text-gray-700">
                  New Users Over Time (days)
                </label>
                <select
                  id="newUsersOverTime"
                  name="newUsersOverTime"
                  value={newUsersOverTimeDays}
                  onChange={(e) => handlePreferenceChange('newUsersOverTimeDays', e.target.value)}
                  className="mt-1 block w-full pl-3 pr-10 py-2 border border-gray-300 bg-white rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  {/* Example options: 1, 2, 4, 8 weeks */}
                  <option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={28}>28 days</option>
                  <option value={56}>56 days</option>
                </select>
              </div>
              
              {/* Active Users */}
              <div>
                <label htmlFor="activeUsers" className="block text-sm font-medium text-gray-700">
                  Active Users (Hours)
                </label>
                <select
                  id="activeUsers"
                  name="activeUsers"
                  value={activeUsersHours}
                  onChange={(e) => handlePreferenceChange('activeUsersHours', e.target.value)}
                  className="mt-1 block w-full pl-3 pr-10 py-2 border border-gray-300 bg-white rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  {/* Example options: 24, 48, 72 hours */}
                  <option value={24}>24 Hours</option>
                  <option value={48}>48 Hours</option>
                  <option value={72}>72 Hours</option>
                </select>
              </div>
              
              {/* New Registrations */}
              <div>
                <label htmlFor="newRegistrations" className="block text-sm font-medium text-gray-700">
                  New Registrations (days)
                </label>
                <select
                  id="newRegistrations"
                  name="newRegistrations"
                  value={newRegistrationsDays}
                  onChange={(e) => handlePreferenceChange('newRegistrationsDays', e.target.value)}
                  className="mt-1 block w-full pl-3 pr-10 py-2 border border-gray-300 bg-white rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  {/* Example options: 1, 2, 4 weeks */}
                  <option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={21}>21 days</option>
                </select>
              </div>
            </div>
          </div>
        </div>
        
        {/* Right Column: Instructions with Information Icon */}
        <div className="lg:col-span-1 bg-blue-50 rounded-lg p-6">
          <div className="flex items-center">
          <InformationCircleIcon className="h-6 w-6 text-blue-500 mr-2" aria-hidden="true"/>
            <h2 className="text-xl font-semibold text-blue-900">Instructions</h2>
          </div>
          <p className="mt-2 text-gray-700">
            This section allows you to view your account information and manage your data presentation preferences.
            You cannot edit your personal information here.
          </p>
          <p className="mt-2 text-gray-700">
            In the "Preferences" section, customize how data is presented in your charts by selecting the desired time
            frames. Changes are applied automatically.
          </p>
        </div>
      </div>
      
      {/* Save Changes Button Removed */}
    </div>
  );
}
