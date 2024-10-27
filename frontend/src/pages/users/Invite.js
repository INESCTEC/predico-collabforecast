import {EnvelopeIcon, InformationCircleIcon, KeyIcon} from '@heroicons/react/24/outline';
import {useEffect, useState} from 'react';
import {useDispatch, useSelector} from "react-redux";
import {
  clearInvitationLink,
  clearUserMessages,
  selectInvitationLink,
  selectUserError,
  selectUserLoading,
  selectUserSuccess,
  sendInvite
} from "../../slices/userSlice";
import {toast} from 'react-toastify';

export default function Invite() {
  
  const [email, setEmail] = useState('');
  // Selectors for Redux state
  const loading = useSelector(selectUserLoading);
  const successMessage = useSelector(selectUserSuccess);
  const errorMessage = useSelector(selectUserError);
  const invitationLink = useSelector(selectInvitationLink);
  const dispatch = useDispatch();
  
  // Clear messages after 2 seconds
  useEffect(() => {
    if (errorMessage || successMessage) {
      const timer = setTimeout(() => {
        dispatch(clearUserMessages());
      }, 2000);
      return () => clearTimeout(timer);  // Clean up the timer
    }
  }, [errorMessage, successMessage, dispatch]);
  
  
  // Handle form submission
  const handleInvitation = async (e) => {
    e.preventDefault();  // Prevent default form submission behavior
    if (!email) {
      dispatch(clearUserMessages());
      dispatch({ type: 'user/sendInvite/rejected', payload: 'Please enter a valid email address.' });
      return;
    }
    dispatch(sendInvite(email)); // Dispatch the sendInvite action
  };
  
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(invitationLink); // Await the promise for better error handling
      dispatch(clearInvitationLink());
      toast.success('URL copied to clipboard!'); // Display a success toast
    } catch (err) {
      console.error('Failed to copy!', err);
      toast.error('Failed to copy token. Please try again.'); // Display an error toast
    }
  };
  
  return (
    <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold text-gray-900">Manage Users</h1>
      <p className="mt-2 text-sm text-gray-600">Here you can manage users, create tokens, and send email
        invitations.</p>
      
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <div className="lg:col-span-2 bg-white shadow-none rounded-lg p-0">
          <h2 className="text-xl font-semibold text-gray-800">Create Invitation Token</h2>
          <form onSubmit={handleInvitation} className="mt-4 space-y-6"> {/* Use onSubmit */}
            <div className="relative">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email Address
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <EnvelopeIcon className="h-5 w-5 text-gray-400" aria-hidden="true"/>
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Enter user's email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              {/* Error and Success Message */}
              <div className="mt-2">
                {errorMessage && (
                  <p className="text-sm text-red-600">{errorMessage}</p>
                )}
                {successMessage && (
                  <p className="text-sm text-green-600">{successMessage}</p>
                )}
              </div>
            </div>
            
            <div className="flex space-x-2">
              <button
                type="submit"
                disabled={loading} // Disable button while loading
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                {loading ? (
                  <svg className="animate-spin h-5 w-5 text-white mr-2" xmlns="http://www.w3.org/2000/svg" fill="none"
                       viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                            strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291a7.978 7.978 0 01-1.664-1.415A8.018 8.018 0 012.34 14H.12A9.985 9.985 0 006 19.29V17.29z"></path>
                  </svg>
                ) : (
                  'Send email invitation'
                )}
              </button>
            </div>
            
            <div className="relative mt-6">
              <label htmlFor="token" className="block text-sm font-medium text-gray-700">
                Token
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <KeyIcon className="h-5 w-5 text-gray-400" aria-hidden="true"/>
                </div>
                <input
                  id="token"
                  name="token"
                  type="text"
                  readOnly
                  value={invitationLink}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Generated token"
                  disabled
                />
              </div>
            </div>
            
            <div className="flex space-x-2 mt-4">
              <button
                type="button"
                onClick={copyToClipboard}
                disabled={!invitationLink}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                Copy to Clipboard
              </button>
            </div>
          </form>
        </div>
        
        <div className="lg:col-span-1 bg-blue-50 rounded-lg p-6">
          <div className="flex items-center">
            <InformationCircleIcon className="h-6 w-6 text-blue-500 mr-2" aria-hidden="true"/>
            <h2 className="text-xl font-semibold text-blue-900">Instructions</h2>
          </div>
          <p className="mt-2 text-gray-700">
            You can generate a token and share it directly or send an invitation to the user's email.
          </p>
        </div>
      </div>
    </div>
  );
}
