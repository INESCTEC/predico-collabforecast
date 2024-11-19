import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { axiosWithoutInterceptors } from "../../routes/axiosInstance";
import Logo from "../../components/Logo";
import windTurbineImage from '../../assets/images/windturbine.jpg';
import { EyeIcon, EyeSlashIcon } from "@heroicons/react/24/outline";

export default function SignUp() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');
  const [error, setError] = useState('');
  const [token, setToken] = useState('');
  const [passwordsMatch, setPasswordsMatch] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showRepeatPassword, setShowRepeatPassword] = useState(false);
  const [passwordValidation, setPasswordValidation] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    specialChar: false,
  });

  const navigate = useNavigate();
  const { token: inviteToken } = useParams();

  useEffect(() => {
    if (inviteToken) {
      setToken(inviteToken);
    }
  }, [inviteToken]);

  useEffect(() => {
    if (repeatPassword) {
      setPasswordsMatch(password === repeatPassword);
    }
  }, [password, repeatPassword]);

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

  const handleSignup = async (e) => {
    e.preventDefault();

    if (!Object.values(passwordValidation).every((isValid) => isValid)) {
      setError('Password does not meet the required criteria.');
      return;
    }

    if (password !== repeatPassword) {
      setError('Passwords do not match.');
      return;
    }

    const headers = {
      headers: { Authorization: `Bearer ${token}` },
    };

    try {
      const response = await axiosWithoutInterceptors.post(
          '/user/register',
          {
            email: email,
            password: password,
            first_name: firstName,
            last_name: lastName,
          },
          headers
      );

      if (response.status === 201) {
        navigate('/welcome');
      }
    } catch (error) {
      if (error.response && error.response.data.message) {
        setError(error.response.data.message);
      } else if (error.request) {
        setError('No response from the server. Please check your connection and try again.');
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    }
  };

  return (
      <div className="relative min-h-screen">
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
            <div className="bg-gradient-to-b from-orange-100 via-white to-orange-200 px-6 py-12 shadow sm:rounded-lg sm:px-12">
              <form onSubmit={handleSignup} className="space-y-6">
                {/* First Name */}
                <div>
                  <label htmlFor="first-name" className="block text-sm font-medium leading-6 text-gray-900">First Name</label>
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
                  <label htmlFor="last-name" className="block text-sm font-medium leading-6 text-gray-900">Last Name</label>
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
                  <label htmlFor="email" className="block text-sm font-medium leading-6 text-gray-900">Email Address</label>
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
                  <label htmlFor="password" className="block text-sm font-medium leading-6 text-gray-900">Password</label>
                  <div className="flex items-center relative">
                    <input
                        id="password"
                        name="password"
                        type={showPassword ? 'text' : 'password'}
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="block w-full rounded-md py-1.5 px-3 pr-10"
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

                {/* Repeat Password */}
                <div>
                  <label htmlFor="repeat-password" className="block text-sm font-medium leading-6 text-gray-900">Repeat Password</label>
                  <div className="flex items-center relative">
                    <input
                        id="repeat-password"
                        name="repeat-password"
                        type={showRepeatPassword ? 'text' : 'password'}
                        required
                        value={repeatPassword}
                        onChange={(e) => setRepeatPassword(e.target.value)}
                        className="block w-full rounded-md py-1.5 px-3 pr-10"
                    />
                    <button
                        type="button"
                        className="absolute inset-y-0 right-0 flex items-center pr-3"
                        onClick={() => setShowRepeatPassword(!showRepeatPassword)}
                    >
                      {showRepeatPassword ? (
                          <EyeSlashIcon className="h-5 w-5 text-gray-500" aria-hidden="true" />
                      ) : (
                          <EyeIcon className="h-5 w-5 text-gray-500" aria-hidden="true" />
                      )}
                    </button>
                  </div>
                  {repeatPassword && (
                      <span className={`text-sm ${passwordsMatch ? 'text-green-600' : 'text-red-600'}`}>
                    {passwordsMatch ? 'Passwords match' : 'Passwords do not match'}
                  </span>
                  )}
                </div>

                {/* Password Requirements */}
                <div className="mt-4 text-sm">
                  <p>Your password must meet the following requirements:</p>
                  <ul className="list-disc list-inside">
                    <li className={passwordValidation.length ? 'text-green-600' : 'text-gray-500'}>At least 8 characters long</li>
                    <li className={passwordValidation.uppercase ? 'text-green-600' : 'text-gray-500'}>Includes an uppercase letter</li>
                    <li className={passwordValidation.lowercase ? 'text-green-600' : 'text-gray-500'}>Includes a lowercase letter</li>
                    <li className={passwordValidation.number ? 'text-green-600' : 'text-gray-500'}>Includes a number</li>
                    <li className={passwordValidation.specialChar ? 'text-green-600' : 'text-gray-500'}>Includes a special character</li>
                  </ul>
                </div>

                {/* Error Message */}
                {error && <p className="text-red-500 text-sm">{error}</p>}

                <button type="submit" className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700">
                  Sign Up
                </button>
                <div className="mt-4 text-sm">
                  <Link to={'/'} className="font-semibold text-indigo-600 hover:text-indigo-500">Back to homepage</Link>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
  );
}