import {useEffect, useState} from 'react';
import {Link, useNavigate, useParams} from 'react-router-dom';
import axiosInstance from "../../routes/axiosInstance";
import logo from '../../assets/images/elia-group-logo-svg.svg';
import windTurbineImage from '../../assets/images/windturbine.jpg'; // Import the background image

export default function SetPassword() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  const [passwordsMatch, setPasswordsMatch] = useState(null); // Password match state
  const { token } = useParams(); // Get the token from the URL params
  
  useEffect(() => {
    if (confirmPassword) {
      setPasswordsMatch(password === confirmPassword);
    }
  }, [password, confirmPassword]);
  
  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    // Password complexity requirements
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$/;
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    // Check password complexity
    if (!passwordRegex.test(password)) {
      setError('Password must be at least 8 characters long, include an uppercase letter,' +
        ' a lowercase letter, a number, and a special character.');
      return;
    }
    
    try {
      const response = await axiosInstance.post(`/user/password-reset/confirm`, {
        "new_password": password,
        token,
      });
      
      if (response.status === 200) {
        setMessage('Password reset successful. Redirecting to sign in...');
        setTimeout(() => {
          navigate('/'); // Redirect to sign in page after a few seconds
        }, 3000);
      }
    } catch (error) {
      setError('Failed to reset password. Please try again.');
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
            <form onSubmit={handleResetPassword} className="space-y-6">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-900">New Password</label>
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
              
              <div>
                <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-900">Confirm
                  Password</label>
                <input
                  id="confirm-password"
                  name="confirm-password"
                  type="password"
                  required
                  className="block w-full rounded-md py-1.5 px-3"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
              {/* Password matching message */}
              {confirmPassword && (
                <span className={`text-sm ${passwordsMatch ? 'text-green-600' : 'text-red-600'}`}>
                    {passwordsMatch ? 'Passwords match' : 'Passwords do not match'}
                  </span>
              )}
              
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
              
              {error && <p className="text-red-500 text-sm">{error}</p>}
              {message && <p className="text-green-500 text-sm">{message}</p>}
              
              <div>
                <button type="submit" className="flex w-full justify-center bg-indigo-600 py-2 text-sm text-white">
                  Reset Password
                </button>
              </div>
              
              <div className="mt-4 text-sm">
                <Link
                  to={"/signin"}
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
