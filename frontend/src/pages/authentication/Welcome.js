import {CheckCircleIcon} from '@heroicons/react/24/outline'; // Importing an icon for success message
import {Link, useNavigate} from 'react-router-dom';
import logo from '../../assets/images/logo.svg';
import windTurbineImage from '../../assets/images/windturbine.jpg';
import React from "react"; // Importing the background image

export default function Welcome() {
  const navigate = useNavigate();
  
  const navigateToHomePage = () => {
    navigate('/'); // Redirect to the Homepage
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
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <img
            alt="Predico"
            src={logo}
            className="mx-auto h-8 sm:h-12 md:h-16 lg:h-20 w-auto"
          />
        </div>
        
        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div
            className="bg-gradient-to-b from-orange-100 via-white to-orange-200 px-6 py-12 shadow sm:rounded-lg sm:px-12">
            <div className="text-center">
              <CheckCircleIcon className="mx-auto h-16 w-16 text-green-600" aria-hidden="true"/>
              <h2 className="mt-6 text-center text-3xl font-bold leading-9 tracking-tight text-gray-900">
                Registration Successful!
              </h2>
              <p className="mt-4 text-sm text-gray-600">
                Welcome! You have been successfully registered. Please check your email to confirm your registration and
                activate your account.
              </p>
            </div>
            
            <div className="mt-8 space-y-6 text-center">
              {/* API Documentation */}
              <Link to="https://127.0.0.1/swagger"
                    className="block text-indigo-600 font-semibold hover:text-indigo-500"
                    target="_blank"
                    rel="noopener noreferrer">
                Swagger Documentation
              </Link>
              
              {/* Styled Back to Sign In link */}
              <p className="text-sm text-gray-600 mt-6">
                Ready to get started?{' '}
                <span
                  onClick={navigateToHomePage}
                  className="text-indigo-600 font-semibold hover:text-indigo-500 cursor-pointer"
                >
                  Go back to homepage
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
