import React, { useState } from 'react';
import { Link } from 'react-router-dom'; // To navigate back to login
import { axiosInstance } from "../../routes/axiosInstance";
import Logo from "../../components/Logo";
import windTurbineImage from '../../assets/images/windturbine.jpg'; // Import the background image

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  
  const handleForgotPassword = async (e) => {
    e.preventDefault();
    try {
      const response = await axiosInstance.post('/user/password-reset', {
        email,
      });
      if (response.status === 200) {
        setMessage('A password reset link has been sent to your email.');
        setError('');
      }
    } catch (error) {
      setError('Failed to send reset link. Please check your email and try again.');
      setMessage('');
    }
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
            imageClass='mx-auto h-6 sm:h-8 md:h-10 lg:h-8 w-auto'>
        </Logo>

        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div
            className="bg-gradient-to-b from-orange-100 via-white to-orange-200 px-6 py-12 shadow sm:rounded-lg sm:px-12">
            
            {/* Helper Title */}
            <p className="text-center text-sm font-medium text-gray-600 mb-6">
              Enter your email to reset your password
            </p>
            
            <form onSubmit={handleForgotPassword} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-900">Email address</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className="block w-full rounded-md py-1.5 px-3"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              
              {message && <p className="text-green-500 text-sm">{message}</p>}
              {error && <p className="text-red-500 text-sm">{error}</p>}
              
              <div>
                <button type="submit" className="flex w-full justify-center bg-indigo-600 py-2 text-sm text-white">
                  Send Reset Link
                </button>
              </div>
              
              <div className="mt-4 text-sm">
                <Link
                  to={'/signin'}
                  className="font-semibold text-indigo-600 hover:text-indigo-500"
                >
                  Back to login
                </Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
