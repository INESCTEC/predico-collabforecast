import { useState, useEffect } from 'react';
import { InformationCircleIcon } from '@heroicons/react/24/outline';  // Added for the "i" icon
import { useAuth } from '../../AuthContext';

export default function SettingsPage() {
  const { userDetails, fetchUserDetails } = useAuth();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  useEffect(() => {
    fetchUserDetails()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  // const handleSaveChanges = () => {
  //   // Save the updated user details
  //   updateUserDetails(localUser);
  // };
  //
  // const handlePasswordChange = () => {
  //   if (newPassword === confirmPassword) {
  //     updatePassword(newPassword, confirmPassword)
  //       .then(() => alert('Password changed successfully'))
  //       .catch((err) => alert(err.message));
  //   } else {
  //     alert('Passwords do not match');
  //   }
  // };
  //
  // if (!localUser) {
  //   return <div>Loading...</div>;
  // }
  
  return (
    <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
      <p className="mt-2 text-sm text-gray-600">Manage your account settings and profile.</p>
      
      {/* Layout Grid */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Form fields */}
        <div className="lg:col-span-2 space-y-10">
          {/* Profile Information Section */}
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Profile Information</h2>
              <p className="mt-1 text-sm text-gray-600">Update your personal information.</p>
            </div>
            
            <div className="relative">
              <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">First Name</label>
              <input
                id="first_name"
                name="first_name"
                type="text"
                value={userDetails.first_name || ''}
                // onChange={(e) => setLocalUser({ ...localUser, first_name: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
            
            <div className="relative">
              <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">Last Name</label>
              <input
                id="last_name"
                name="last_name"
                type="text"
                value={userDetails.last_name || ''}
                // onChange={(e) => setLocalUser({ ...localUser, last_name: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
            
            <div className="relative">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email Address</label>
              <input
                id="email"
                name="email"
                type="email"
                value={userDetails.email || ''}
                // onChange={(e) => setLocalUser({ ...localUser, email: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
          </div>
          
          {/* Account Settings Section */}
          <div className="mt-8 space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">Account Settings</h2>
            <p className="text-sm text-gray-600">Manage your account settings and privacy.</p>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={userDetails.is_active}
                // onChange={(e) => setLocalUser({ ...localUser, is_active: e.target.checked })}
                className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
              />
              <label className="ml-3 text-sm font-medium text-gray-700">Active Account</label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={userDetails.is_verified}
                disabled
                className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
              />
              <label className="ml-3 text-sm font-medium text-gray-700">Verified Account (Email confirmed)</label>
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={userDetails.is_superuser}
                disabled
                className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
              />
              <label className="ml-3 text-sm font-medium text-gray-700">Superuser Access (Admin managed)</label>
            </div>
          </div>
          
          {/* Password Management Section */}
          <div className="mt-8 space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">Password Management</h2>
            <p className="text-sm text-gray-600">Update your password to secure your account.</p>
            
            <div className="relative">
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700">New Password</label>
              <input
                id="new_password"
                name="new_password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
            
            <div className="relative">
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">Confirm New Password</label>
              <input
                id="confirm_password"
                name="confirm_password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
            
            <div className="mt-5">
              <button
                // onClick={}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Update Password
              </button>
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
            Use this section to manage your personal and account settings. Some fields, like "Verified Account" and "Superuser Access," are admin-managed.
          </p>
          <p className="mt-2 text-gray-700">
            You can also update your password by entering a new password and confirming it. Ensure both fields match before submitting.
          </p>
        </div>
      </div>
    </div>
  );
}
