import React from 'react';
import { Link } from 'react-router-dom';
import { DocumentIcon, BookOpenIcon, LockClosedIcon, ClipboardDocumentCheckIcon } from '@heroicons/react/24/solid';
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
          <img
            alt="Predico"
            src={logo}
            className="mx-auto h-8 sm:h-12 md:h-16 lg:h-20 w-auto"
          />
        </div>
        
        {/* Grid Section */}
        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-3xl">
          <div
            className="bg-gradient-to-b from-orange-100 via-white to-orange-200 px-6 py-12 shadow sm:rounded-lg sm:px-12 text-center">
            {/*<h2 className="text-xs text-gray-700 mb-6">Explore the documentation for more details or sign in to access*/}
            {/*  your dashboard</h2>*/}
            
            {/* Grid Layout */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-6">
              {/* Quick Guide Documentation Card */}
              <a
                href="http://predico-elia.inesctec.pt/quick-guide"
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col items-center rounded-lg p-6 bg-transparent hover:bg-white hover:bg-opacity-30 hover:shadow-lg transition-transform transform"
              >
                <ClipboardDocumentCheckIcon className="h-12 w-12 text-gray-700 mb-4" aria-hidden="true"/>
                <h3 className="text-lg font-semibold text-gray-700">Quick Guide Documentation</h3>
                <p className="text-sm text-gray-600 mt-2 text-center">Get started with a quick guide</p>
              </a>
              
              {/* Swagger Documentation Card */}
              <a
                href="https://predico-elia.inesctec.pt/swagger/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col items-center rounded-lg p-6 bg-transparent hover:bg-white hover:bg-opacity-30 hover:shadow-lg transition-transform transform"
              >
                <DocumentIcon className="h-12 w-12 text-gray-700 mb-4" aria-hidden="true"/>
                <h3 className="text-lg font-semibold text-gray-700">Swagger Documentation</h3>
                <p className="text-sm text-gray-600 mt-2 text-center">View API documentation with Swagger</p>
              </a>
              
              {/* Redoc Documentation Card */}
              <a
                href="https://predico-elia.inesctec.pt/redoc/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col items-center rounded-lg p-6 bg-transparent hover:bg-white hover:bg-opacity-30 hover:shadow-lg transition-transform transform"
              >
                <BookOpenIcon className="h-12 w-12 text-gray-700 mb-4" aria-hidden="true"/>
                <h3 className="text-lg font-semibold text-gray-700">Redoc Documentation</h3>
                <p className="text-sm text-gray-600 mt-2 text-center">View API documentation with Redoc</p>
              </a>
              
              {/* Sign In Card - Differentiated Styling */}
              <Link
                to="/signin"
                className="flex flex-col items-center rounded-lg p-6 bg-transparent hover:bg-blue-200 hover:text-white hover:shadow-lg transition-transform transform"
              >
                <LockClosedIcon className="h-12 w-12 text-gray-700 mb-4" aria-hidden="true"/>
                <h3 className="text-lg font-semibold text-gray-700">Sign In Dashboard</h3>
                <p className="text-sm text-gray-600 mt-2 text-center">Access the admin dashboard</p>
              </Link>
            </div>
            
            {/* Discreet note for admins */}
            <p className="text-xs text-gray-500 mt-4 italic">
              * Sign In is restricted to Admins only
            </p>
            
            {/* Additional Links as Side Notes */}
            <div className="mt-8 text-left">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Other resources</h3>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">
                  <a href="https://predico-elia.inesctec.pt/quick-guide/bruno-api-client/Predico-Collabforecast.zip"
                     target="_self"
                     rel="noopener noreferrer" className="hover:underline text-indigo-600">
                    Bruno Documentation
                  </a> - Access in-depth documentation
                </p>
                <p className="text-sm text-gray-600">
                  <a href="https://predico-elia.inesctec.pt/quick-guide/jpynb-client/forecaster_tutorial.ipynb"
                     target="_self" rel="noopener noreferrer"
                     className="hover:underline text-indigo-600">
                    Jupyter Notebooks
                  </a> - Access interactive Jupyter notebooks for data exploration
                </p>
                <p className="text-sm text-gray-600">
                  <Link to="/forgot-password" className="hover:underline text-indigo-600">
                    Forgot Password
                  </Link> - Reset your password if you've forgotten it
                </p>
              </div>
            </div>
            
            {/* Support Links */}
            <div className="mt-4 text-left border-t border-gray-300 pt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Email</h3>
              <div className="space-y-1 text-gray-600 text-sm ">
                <p>
                  <a href="mailto:predico@inesctec.pt" className="hover:underline text-indigo-600">
                    Technical support
                  </a> - For assistance with technical issues, system errors, or troubleshooting
                </p>
                <p>
                  <a href="mailto:predico@elia.be" className="hover:underline text-indigo-600">
                    Other questions
                  </a> - For inquiries related to logistics, administration, or general questions
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Homepage;
