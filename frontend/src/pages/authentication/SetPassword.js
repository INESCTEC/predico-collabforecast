import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { axiosInstance } from "../../routes/axiosInstance";
import logo from '../../assets/images/elia-group-logo-svg.svg';
import windTurbineImage from '../../assets/images/windturbine.jpg'; // Import the background image
import { EyeIcon, EyeSlashIcon } from "@heroicons/react/24/outline";

export default function SetPassword() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [passwordsMatch, setPasswordsMatch] = useState(null); // Password match state
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordValidation, setPasswordValidation] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    specialChar: false,
  });

  const navigate = useNavigate();
  const { token } = useParams(); // Get the token from the URL params

  useEffect(() => {
    if (confirmPassword) {
      setPasswordsMatch(password === confirmPassword);
    }
  }, [password, confirmPassword]);

  useEffect(() => {
    const validations = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      specialChar: /[@$!%*?&#]/.test(password),
    };
    setPasswordValidation(validations);
  }, [password]);

  const handleResetPassword = async (e) => {
    e.preventDefault();

    if (!Object.values(passwordValidation).every((isValid) => isValid)) {
      setError('Password does not meet the required criteria.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    try {
      const response = await axiosInstance.post(`/user/password-reset/confirm`, {
        new_password: password,
        token,
      });

      if (response.status === 200) {
        setMessage('Password reset successful. Redirecting to sign in...');
        setTimeout(() => {
          navigate('/'); // Redirect to sign-in page after a few seconds
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
            <img
                alt="Predico"
                src={logo}
                className="mx-auto h-8 sm:h-12 md:h-16 lg:h-20 w-auto"
            />
          </div>

          <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-[480px]">
            <div
                className="bg-gradient-to-b from-orange-100 via-white to-orange-200 px-6 py-12 shadow sm:rounded-lg sm:px-12">
              <form onSubmit={handleResetPassword} className="space-y-6">
                {/* Password */}
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-900">New Password</label>
                  <div className="flex items-center relative">
                    <input
                        id="password"
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        required
                        className="block w-full rounded-md py-1.5 px-3 pr-10"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    <button
                        type="button"
                        className="absolute inset-y-0 right-0 flex items-center pr-3"
                        onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                          <EyeSlashIcon className="h-5 w-5 text-gray-500" aria-hidden="true" />
                      ) : (
                          <EyeIcon className="h-5 w-5 text-gray-500" aria-hidden="true" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Confirm Password */}
                <div>
                  <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-900">Confirm Password</label>
                  <div className="flex items-center relative">
                    <input
                        id="confirm-password"
                        name="confirm-password"
                        type={showConfirmPassword ? 'text' : 'password'}
                        required
                        className="block w-full rounded-md py-1.5 px-3 pr-10"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                    <button
                        type="button"
                        className="absolute inset-y-0 right-0 flex items-center pr-3"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? (
                          <EyeSlashIcon className="h-5 w-5 text-gray-500" aria-hidden="true" />
                      ) : (
                          <EyeIcon className="h-5 w-5 text-gray-500" aria-hidden="true" />
                      )}
                    </button>
                  </div>
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
                    <li className={passwordValidation.length ? 'text-green-600' : 'text-gray-500'}>At least 8 characters long</li>
                    <li className={passwordValidation.uppercase ? 'text-green-600' : 'text-gray-500'}>Includes an uppercase letter</li>
                    <li className={passwordValidation.lowercase ? 'text-green-600' : 'text-gray-500'}>Includes a lowercase letter</li>
                    <li className={passwordValidation.number ? 'text-green-600' : 'text-gray-500'}>Contains a number</li>
                    <li className={passwordValidation.specialChar ? 'text-green-600' : 'text-gray-500'}>Has a special character</li>
                  </ul>
                </div>

                {error && <p className="text-red-500 text-sm">{error}</p>}
                {message && <p className="text-green-500 text-sm">{message}</p>}

                <div>
                  <button type="submit" className="flex w-full justify-center bg-indigo-600 py-2 text-sm text-white">
                    Set Password
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