import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/images/elia-group-logo-svg.svg';
import windTurbineImage from '../assets/images/windturbine.jpg';

function Homepage() {
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
      
      {/* Content */}
      <div className="flex flex-col justify-start sm:px-6 lg:px-8 pt-12">
        {/* Logo */}
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <img alt="Predico" src={logo} className="mx-auto h-10 w-auto" />
        </div>
        
        {/* Form Section */}
        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-gradient-to-b from-orange-100 via-white to-orange-200 px-6 py-12 shadow sm:rounded-lg sm:px-12">
            <p className="text-center text-sm font-medium text-gray-600 mb-6">
              Explore the documentation for more details or sign in to access your dashboard.
            </p>
            <div className="space-y-4">
              <a
                href="https://predico-elia.inesctec.pt/swagger/"
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full text-center bg-indigo-600 text-white py-2 rounded-md hover:bg-indigo-700 transition"
              >
                Swagger Documentation
              </a>
              <a
                href="https://predico-elia.inesctec.pt/redoc/"
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full text-center bg-indigo-600 text-white py-2 rounded-md hover:bg-indigo-700 transition"
              >
                Redoc Documentation
              </a>
              <Link
                to="/signin"
                className="block w-full text-center bg-indigo-600 text-white py-2 rounded-md hover:bg-indigo-700 transition"
              >
                Sign In
              </Link>
              {/* Discreet note for admins */}
              <p className="text-xs text-gray-500 mt-2 italic text-center">
                * Sign In is restricted to Admins only
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Homepage;
