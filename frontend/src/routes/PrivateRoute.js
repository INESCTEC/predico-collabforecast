// src/routes/PrivateRoute.js
import { Navigate, Outlet } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { selectAuthToken } from '../slices/authSlice';

const PrivateRoute = () => {
  const token = useSelector(selectAuthToken);
  return token ? <Outlet /> : <Navigate to="/signin" />;
};

export default PrivateRoute;
