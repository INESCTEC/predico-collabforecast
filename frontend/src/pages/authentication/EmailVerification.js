import React, { useEffect, useState } from 'react';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'; // Icons for success and failure messages
import { Link, useNavigate, useParams } from 'react-router-dom';
import { axiosInstance } from "../../routes/axiosInstance";
import Logo from "../../components/Logo";
import windTurbineImage from '../../assets/images/windturbine.jpg'; // Import the background image

export default function EmailVerification() {
  const navigate = useNavigate();
  const { uidb64, token } = useParams();
  const [status, setStatus] = useState(null); // null = loading, true = success, false = failure
  const [error, setError] = useState(null); // To store any error messages from the API
  
  useEffect(() => {
    const verifyEmail = async () => {
      try {
        // Send the token to the API for verification
        console.log('Verifying email...');
        const response = await axiosInstance.get(`/user/verify/?uid=${uidb64}&token=${token}`);
        if (response.status === 200) {
          setStatus(true); // Verification succeeded
        }
      } catch (error) {
        setStatus(false); // Verification failed
        setError('Invalid or expired verification token.');
      }
    };
    verifyEmail().then();
  }, [uidb64, token]);
  
  const navigateToSignIn = () => {
    navigate('/'); // Redirect to the Sign In page
  };
  
  return (
    <div className="relative min-h-screen">
      {/* Background Image */}
      <div
        className="absolute inset-0 h-full"
        style={{
          backgroundImage: `url(${windTurbineImage})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          zIndex: -1,
        }}
      ></div>
      
      <div className="flex min-h-full flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8 relative">
        <Logo
            containerClass='sm:mx-auto sm:w-full sm:max-w-md'
            imageClass='mx-auto h-6 w-auto object-contain sm:h-8 md:h-10 lg:h-12'
        />
        
        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div
            className="bg-gradient-to-b from-orange-100 via-white to-orange-200 px-6 py-12 shadow sm:rounded-lg sm:px-12">
            <div className="text-center">
              {status === null && (
                <p className="text-sm text-gray-600">
                  Verifying your email, please wait...
                </p>
              )}
              
              {status === true && (
                <>
                  <CheckCircleIcon className="mx-auto h-16 w-16 text-green-600" aria-hidden="true"/>
                  <h2 className="mt-6 text-center text-3xl font-bold leading-9 tracking-tight text-gray-900">
                    Email Verified!
                  </h2>
                  <p className="mt-4 text-sm text-gray-600">
                    Your email has been successfully verified. You can now sign in.
                  </p>
                </>
              )}
              
              {status === false && (
                <>
                  <XCircleIcon className="mx-auto h-16 w-16 text-red-600" aria-hidden="true"/>
                  <h2 className="mt-6 text-center text-3xl font-bold leading-9 tracking-tight text-gray-900">
                    Email Verification Failed
                  </h2>
                  <p className="mt-4 text-sm text-gray-600">
                    {error ? error : 'Something went wrong. Please try again.'}
                  </p>
                </>
              )}
            </div>
            
            {status !== null && (
              <div className="mt-8 space-y-6 text-center">
                {/* API Documentation */}
                <Link
                  to="/" // Navigate to homepage using the 'to' attribute
                  className="block text-indigo-600 font-semibold hover:text-indigo-500"
                >
                  API Documentation
                </Link>
                
                {/* Styled Back to Sign In link */}
                <p className="text-sm text-gray-600 mt-6">
                  Ready to get started?{' '}
                  <span
                    onClick={navigateToSignIn}
                    className="text-indigo-600 font-semibold hover:text-indigo-500 cursor-pointer"
                  >
                    Go back to sign in
                  </span>
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
