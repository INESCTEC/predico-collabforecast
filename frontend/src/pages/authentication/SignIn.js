import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {login, clearAuthMessages} from '../../slices/authSlice';
import {Link, useNavigate} from 'react-router-dom';
import {EyeIcon, EyeSlashIcon} from '@heroicons/react/24/outline';
import logo from '../../assets/images/elia-group-logo-svg.svg';
import windTurbineImage from '../../assets/images/windturbine.jpg';

export default function SignIn() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const errorMessage = useSelector((state) => state.auth.errorMessage);
  const loading = useSelector((state) => state.auth.loading);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false); // State to toggle password visibility
  const [rememberMe, setRememberMe] = useState(false);
  
  const handleSignIn = (e) => {
    e.preventDefault();
    dispatch(clearAuthMessages());
    dispatch(login({ email, password, rememberMe }))
      .unwrap()
      .then(() => {
        navigate('/dashboard');
      })
      .catch(() => {
        // Error message is handled in Redux state
      });
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
          <img alt="Your Company" src={logo} className="mx-auto h-10 w-auto"/>
        </div>
        
        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div
            className="bg-gradient-to-b from-orange-100 via-white to-orange-200 px-6 py-12 shadow sm:rounded-lg sm:px-12">
            <p className="text-center text-sm font-medium text-gray-600 mb-4">
              This form is for authorized Admins only. Other users may reset their passwords.
            </p>
            <form onSubmit={handleSignIn} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-900">
                  Email address
                </label>
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
              
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-900">
                  Password
                </label>
                <div className="flex items-center relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'} // Toggle input type
                    required
                    className="block w-full rounded-md py-1.5 px-3 pr-10" // Add padding to the right
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  {/* Toggle Password Visibility */}
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 flex items-center pr-3"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ height: '100%' }} // Ensure button spans the input height
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-5 w-5 text-gray-500" aria-hidden="true"/>
                    ) : (
                      <EyeIcon className="h-5 w-5 text-gray-500" aria-hidden="true"/>
                    )}
                  </button>
                </div>
              </div>
              
              {errorMessage && <p className="text-red-500 text-sm">{errorMessage}</p>}
              
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"
                    checked={rememberMe}
                    onChange={() => setRememberMe(!rememberMe)}
                  />
                  <label htmlFor="remember-me" className="ml-3 block text-sm text-gray-900">
                    Remember me
                  </label>
                </div>
                
                <div className="text-sm">
                  <Link to="/forgot-password"
                        className="font-semibold text-indigo-600 hover:text-indigo-500">
                    Forgot password?
                  </Link>
                </div>
              </div>
              
              <div>
                <button
                  type="submit"
                  className="flex w-full justify-center bg-indigo-600 py-2 text-sm text-white rounded-md hover:bg-indigo-700 transition"
                  disabled={loading}
                >
                  {loading ? (
                    <svg
                      className="animate-spin h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291a7.978 7.978 0 01-1.664-1.415A8.018 8.018 0 012.34 14H.12A9.985 9.985 0 006 19.29V17.29z"
                      ></path>
                    </svg>
                  ) : (
                    'Sign in'
                  )}
                </button>
              </div>
            </form>
            
            {/* Link back to Homepage */}
            <div className="mt-4 text-sm">
              <Link
                to={'/'}
                className="font-semibold text-indigo-600 hover:text-indigo-500"
              >
                Back to homepage
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
