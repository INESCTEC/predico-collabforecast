import {BrowserRouter as Router, Route, Routes, useNavigate} from 'react-router-dom';
import Layout from "./components/Layout";
import {HomeIcon, UsersIcon} from '@heroicons/react/24/outline';
import Dashboard from './pages/Dashboard';
import Users from './pages/users/Users';
import Invite from "./pages/users/Invite";
import SignIn from "./pages/authentication/SignIn";
import SignUp from "./pages/authentication/SignUp";
import Welcome from "./pages/authentication/Welcome";
import Settings from "./pages/users/Settings";
import PrivateRoute from "./routes/PrivateRoute";
import ForgotPassword from "./pages/authentication/ForgotPassword";
import SetPassword from "./pages/authentication/SetPassword";
import EmailVerification from "./pages/authentication/EmailVerification";
import Homepage from "./pages/Homepage";
import {useDispatch} from "react-redux";
import {ToastContainer} from 'react-toastify';
import {logout} from './slices/authSlice'; // Import the logout action


export default function App() {
  
  
  // Navigation and other state data
  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, current: true },
    {
      name: 'Users',
      icon: UsersIcon,
      current: false,
      children: [
        { name: 'Invite', href: '/users/invite' },
        { name: 'List users', href: '/users/list-users' },
      ],
    },
  ];
  
  return (
    <Router>
      <AppContent navigation={navigation}/>
      <ToastContainer/>
    </Router>
  );
}

// Create a separate component that can use the Auth context
function AppContent({ navigation }) {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // User navigation with logout functionality
  const userNavigation = [
    {
      name: 'Your profile', href: '#', onClick: () => {
        navigate('/settings')
      }
    },
    {
      name: 'Sign out', href: '#', onClick: () => {
        handleLogout(dispatch, navigate)
      }
    },  // Directly use logout
  ];
  
  // Logout handler
  const handleLogout = (dispatch, navigate) => {
    dispatch(logout());
    navigate('/signin'); // Redirect to the sign-in page after logout
  };
  
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Homepage/>}/>
      <Route path="/signin" element={<SignIn/>}/>
      <Route path="/signup/:token" element={<SignUp/>}/>
      <Route path="/welcome" element={<Welcome/>}/>
      <Route path="/forgot-password" element={<ForgotPassword/>}/> {/* Add ForgotPassword route */}
      <Route path="/set-password/:token" element={<SetPassword/>}/> {/* Add ForgotPassword route */}
      <Route path={"/email-verification/:uidb64/:token"}
             element={<EmailVerification/>}/> {/* Add EmailVerification route */}
      
      {/* Private routes */}
      <Route element={<PrivateRoute/>}>
        <Route element={<Layout navigation={navigation} userNavigation={userNavigation}/>}>
          <Route path="/dashboard" element={<Dashboard/>}/>
          <Route path="/settings" element={<Settings/>}/>
          <Route path="/users/list-users" element={<Users/>}/>
          <Route path="/users/invite" element={<Invite/>}/>
        
        </Route>
      </Route>
    </Routes>
  );
}
