import {createContext, useCallback, useContext, useEffect, useState} from "react";
import {useNavigate} from 'react-router-dom';
import axiosInstance from "./routes/axiosInstance"; // Import the Axios instance

// Create AuthContext
const AuthContext = createContext();

// Provider component to wrap the app and manage authentication state
export const AuthProvider = ({ children }) => {
  const [isAuth, setIsAuth] = useState(localStorage.getItem('authToken') !== null);
  const [userDetails, setUserDetails] = useState({
    first_name: '',
    last_name: '',
    email: '',
    is_active: false,
    is_superuser: false,
  });
  const [users, setUsers] = useState([]);  // Ensure users is initialized as an empty array
  const [invitationLink, setInvitationLink] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const navigate = useNavigate();
  const token = localStorage.getItem('authToken');
  
  // Function to log in
  const login = (token) => {
    localStorage.setItem('authToken', token);
    setIsAuth(true);
    navigate("/dashboard");
  };
  
  // Function to log out
  const logout = () => {
    localStorage.removeItem('authToken');
    setIsAuth(false);
    navigate("/");
  };
  
  // Function to fetch users from the API
  const fetchUsers = useCallback( async () => {
    const token = localStorage.getItem('authToken'); // Get the token from localStorage
    console.log('Token:', token);
    axiosInstance.get('/user/list', {
        headers: {
          Authorization: `Bearer ${token}`,  // Pass the token in the Authorization header
        },
      })
      .then((response) => {
        console.log('Users fetched:', response.data.data);
        setUsers(response.data.data);  // Set the users data
      })
      .catch((error) => {
        console.error('Error fetching users:', error);
      });
  }, []);
  
  // Fetch user details
  const fetchUserDetails = async () => {
    try {
      const response = await axiosInstance.get('/user/user-detail', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
      });
      setUserDetails(response.data);
    } catch (error) {
      console.error('Error fetching user details:', error);
    }
  };
  
  // Function to send invite
  const sendInvite = async (email) => {
    axiosInstance.post('/user/register-invite', { email }, {
        headers: {
          Authorization: `Bearer ${token}`,  // Pass the token in the Authorization header
        },
      })
      .then((response) => {
        setInvitationLink(response.data.link);
        setSuccessMessage('Invitation sent successfully.');
      })
      .catch((error) => {
        if (undefined === error.response.data.error) {
          setErrorMessage('Error sending invitation. Please try again.');
        } else {
          setErrorMessage(error.response.data.error);
        }
      });
  };
  
  
  const clearInvitationLink = () => {
    setInvitationLink('');
  };
  // Function to clear messages
  const clearMessages = () => {
    setErrorMessage('');
    setSuccessMessage('');
  };
  useEffect(() => {
    if (isAuth) {
      fetchUsers().then().catch();  // Fetch users when authenticated
    }
  }, [isAuth]);
  
  // Group all the context values into a single object
  const authContextValue = {
    isAuth,
    login,
    logout,
    fetchUsers,
    users,
    sendInvite,
    invitationLink,
    clearInvitationLink,
    errorMessage,
    successMessage,
    clearMessages,
    userDetails,
    fetchUserDetails
  };
  
  return (
    <AuthContext.Provider value={authContextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to access AuthContext
export const useAuth = () => useContext(AuthContext);
