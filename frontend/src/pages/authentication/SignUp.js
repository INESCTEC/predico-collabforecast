import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from "../../routes/axiosInstance";
import logo from '../../static/images/elia-group-logo-svg.svg';
import windTurbineImage from '../../static/images/windturbine.jpg'; // Import the background image

export default function SignUp() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');
  const [confirmTerms, setConfirmTerms] = useState(false);
  const [error, setError] = useState(''); // To store any error messages
  const [token, setToken] = useState('');
  const [showTermsModal, setShowTermsModal] = useState(false); // Modal state for Terms and Conditions
  const [passwordsMatch, setPasswordsMatch] = useState(null); // Password match state
  const navigate = useNavigate();
  
  const { token: inviteToken } = useParams();
  
  useEffect(() => {
    if (inviteToken) {
      setToken(inviteToken);
    }
  }, [inviteToken]);
  
  // Check password match on every change
  useEffect(() => {
    if (repeatPassword) {
      setPasswordsMatch(password === repeatPassword);
    }
  }, [password, repeatPassword]);
  
  const handleSignup = async (e) => {
    e.preventDefault();
    
    // Password complexity requirements regex
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$/;
    
    // Validate passwords match
    if (password !== repeatPassword) {
      setError('Passwords do not match.');
      return;
    }
    
    // Validate password complexity
    if (!passwordRegex.test(password)) {
      setError('Password must be at least 8 characters long, include an uppercase letter, a ' +
        'lowercase letter, a number, and a special character.');
      return;
    }
    
    // Validate terms are agreed
    if (!confirmTerms) {
      setError('You must agree to the terms and conditions.');
      return;
    }
    
    const headers = {
      headers: { Authorization: `Bearer ${token}` },
    };
    
    axiosInstance
      .post(
        '/user/register',
        {
          email: email,
          password: password,
          first_name: firstName,
          last_name: lastName,
        },
        headers
      )
      .then((response) => {
        if (response.status === 201) {
          navigate('/welcome'); // Redirect to welcome page
        }
      })
      .catch((error) => {
        if (error.response) {
          if (error.response.data.message) {
            setError(error.response.data.message); // Display error message from server
          } else {
            setError('There was an error processing your registration. Please try again.');
          }
        } else if (error.request) {
          setError('No response from the server. Please check your connection and try again.');
        } else {
          setError('An unexpected error occurred. Please try again.');
        }
      });
  };
  
  const navigateToHomePage = () => {
    navigate('/'); // Redirect to the login panel
  };
  
  const handleTermsModal = () => {
    setShowTermsModal(!showTermsModal); // Toggle terms modal
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
          <div className="bg-gradient-to-b from-orange-100 via-white to-orange-200 px-6 py-12 shadow sm:rounded-lg sm:px-12">
            <form onSubmit={handleSignup} className="space-y-6">
              {/* First Name */}
              <div>
                <label htmlFor="first-name" className="block text-sm font-medium leading-6 text-gray-900">
                  First Name
                </label>
                <input
                  id="first-name"
                  name="first-name"
                  type="text"
                  required
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="block w-full rounded-md py-1.5 px-3"
                />
              </div>
              
              {/* Last Name */}
              <div>
                <label htmlFor="last-name" className="block text-sm font-medium leading-6 text-gray-900">
                  Last Name
                </label>
                <input
                  id="last-name"
                  name="last-name"
                  type="text"
                  required
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="block w-full rounded-md py-1.5 px-3"
                />
              </div>
              
              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium leading-6 text-gray-900">
                  Email Address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full rounded-md py-1.5 px-3"
                />
              </div>
              
              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium leading-6 text-gray-900">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full rounded-md py-1.5 px-3"
                />
              </div>
              
              {/* Repeat Password */}
              <div>
                <label htmlFor="repeat-password" className="block text-sm font-medium leading-6 text-gray-900">
                  Repeat Password
                </label>
                <input
                  id="repeat-password"
                  name="repeat-password"
                  type="password"
                  required
                  value={repeatPassword}
                  onChange={(e) => setRepeatPassword(e.target.value)}
                  className="block w-full rounded-md py-1.5 px-3"
                />
                {/* Password matching message */}
                {repeatPassword && (
                  <span className={`text-sm ${passwordsMatch ? 'text-green-600' : 'text-red-600'}`}>
                    {passwordsMatch ? 'Passwords match' : 'Passwords do not match'}
                  </span>
                )}
              </div>
              
              {/* Password complexity requirements */}
              <div className="mt-4 text-sm text-gray-500">
                <p>Your password must meet the following requirements:</p>
                <ul className="list-disc list-inside">
                  <li>At least 8 characters long</li>
                  <li>Includes both uppercase and lowercase letters</li>
                  <li>Contains at least one number</li>
                  <li>Has at least one special character (e.g., !, @, #, $)</li>
                </ul>
              </div>
              
              {/* Terms and Conditions */}
              <div className="flex items-start">
                <input
                  id="terms"
                  name="terms"
                  type="checkbox"
                  required
                  checked={confirmTerms}
                  onChange={() => setConfirmTerms(!confirmTerms)}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"
                />
                <label htmlFor="terms" className="ml-2 block text-sm text-gray-900">
                  I agree to the <span className="text-indigo-600 hover:text-indigo-500 cursor-pointer" onClick={handleTermsModal}>terms and conditions</span>
                </label>
              </div>
              
              {/* Error Message */}
              {error && <p className="text-red-500 text-sm">{error}</p>}
              
              <button
                type="submit"
                className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700"
              >
                Sign Up
              </button>
              
              {/* Back to login link */}
              <div className="mt-4 text-sm">
                <a
                  href="#"
                  onClick={navigateToHomePage}
                  className="font-semibold text-indigo-600 hover:text-indigo-500"
                >
                  Back to homepage
                </a>
              </div>
            </form>
          </div>
        </div>
      </div>
      
      {/* Terms and Conditions Modal */}
      {showTermsModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 text-center">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            
            <div className="inline-block bg-white rounded-lg text-left shadow-xl transform transition-all sm:max-w-lg sm:w-full sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Terms and Conditions</h3>
              <p className="text-sm text-gray-600">
                {/* You can add your terms and conditions content here */}
                Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                Nullam accumsan, massa vitae volutpat vehicula, velit nisi vestibulum ligula,
                eget placerat purus neque nec lectus. Nulla facilisi.
              </p>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={handleTermsModal}
                  className="bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
