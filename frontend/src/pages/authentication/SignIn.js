import {useState} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import logo from '../../static/images/elia-group-logo-svg.svg';
import windTurbineImage from '../../static/images/windturbine.jpg';
import {useAuth} from "../../AuthContext";
import axiosInstance from "../../routes/axiosInstance";

export default function SignIn() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false); // New loading state
  const navigate = useNavigate();
  
  const { login } = useAuth();
  
  const navigateToSignIn = () => {
    navigate('/'); // Redirect to the homepage
  };
  
  const handleSignIn = async (e) => {
    e.preventDefault();
    setLoading(true); // Start loading
    
    try {
      // Authenticate user and get tokens
      const response = await axiosInstance.post('/token', {
        email,
        password
      });
      
      console.log(response.data)
      if (response.status === 200) {
        const accessToken = response.data.access;
        const refreshToken = response.data.refresh;
        
        // Store tokens in local storage
        localStorage.setItem('authToken', accessToken);
        localStorage.setItem('refreshToken', refreshToken);
        if (rememberMe) {
          localStorage.setItem('rememberMe', 'true');
        }
        
        // Fetch user details using the access token
        const userResponse = await axiosInstance.get('/user/user-detail', {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
        
        const user = userResponse.data;
        
        // Check if the user is a superuser
        if (user.is_superuser) {
          login(accessToken); // Log the user in if they are a superuser
          navigate('/dashboard'); // Redirect to dashboard
        } else {
          setError('Access denied. You are not authorized to sign in.'); // Error if not a superuser
        }
      }
    } catch (error) {
      if (error.response && error.response.data) {
        if (error.response.data.non_field_errors) {
          const errorMessage = error.response.data.non_field_errors[0];
          setError(errorMessage);
        } else {
          // Handle other possible error messages
          setError('An unexpected error occurred.');
        }
      } else {
        setError('Something went wrong. Please try again.');
      }
    } finally {
      setLoading(false); // End loading
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
              
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-900">Password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  className="block w-full rounded-md py-1.5 px-3"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              
              {error && <p className="text-red-500 text-sm">{error}</p>}
              
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
                  <Link
                    to={'/forgot-password'}
                    className="font-semibold text-indigo-600 hover:text-indigo-500"
                  >
                    Forgot password?
                  </Link>
                </div>
              </div>
              
              <div>
                <button
                  type="submit"
                  className="flex w-full justify-center bg-indigo-600 py-2 text-sm text-white rounded-md hover:bg-indigo-700 transition"
                  disabled={loading} // Disable button when loading
                >
                  {loading ? (
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none"
                         viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                              strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291a7.978 7.978 0 01-1.664-1.415A8.018 8.018 0 012.34 14H.12A9.985 9.985 0 006 19.29V17.29z"></path>
                    </svg>
                  ) : (
                    'Sign in'
                  )}
                </button>
              </div>
            </form>
            
            {/* Link back to Homepage */}
            <div className="mt-4 text-sm">
              <a
                href="#"
                onClick={navigateToSignIn}
                className="font-semibold text-indigo-600 hover:text-indigo-500"
              >
                Back to homepage
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
