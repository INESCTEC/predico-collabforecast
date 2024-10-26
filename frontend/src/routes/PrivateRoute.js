import { Navigate, Outlet } from 'react-router-dom';
import {useAuth} from "../AuthContext";

// Private route to protect routes
export default function PrivateRoute() {
  const { isAuth } = useAuth();
  
  if (!isAuth) {
    return <Navigate to="/" />;
  }
  
  return <Outlet />;
}