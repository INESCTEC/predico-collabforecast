import {ChartBarIcon, CheckCircleIcon, UserIcon, UsersIcon} from '@heroicons/react/24/outline';
import {useAuth} from '../AuthContext';
import {useEffect} from 'react';
import moment from 'moment';
import LineChart from "../components/LineChart";

export default function Dashboard() {
  const { users, fetchUsers, fetchUserDetails } = useAuth();
  
  useEffect(() => {
    // Fetch users only when the component mounts
    fetchUsers();
    fetchUserDetails()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // No dependencies, runs only once
  
  // Active Users (users who logged in within the last 48 hours)
  const userRecentActivityCount = users.filter(user =>
    user.last_login !== null && moment().diff(moment(user.last_login), 'hours') <= 48
  ).length;
  
  // const activeUsersCount = users.filter(user => user.is_active).length;
  
  // New Registrations (users who joined within the last 2 weeks)
  const newRegistrationsCount = users.filter(user =>
    moment().diff(moment(user.date_joined), 'weeks') <= 2
  ).length;
  
  // Verified Users
  const verifiedUsersCount = users.filter(user => user.is_verified).length;
  
  // Filter out users with `last_login` null and limit to most recent 10 users
  const recentUsers = users
    .filter(user => user.last_login !== null)
    .sort((a, b) => new Date(b.last_login) - new Date(a.last_login)) // Sort by most recent login
    .slice(0, 10); // Limit to 10 users
  
  return (
    <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Welcome to Your Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">Here you can view insights and manage key aspects of your
          application.</p>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="bg-indigo-50 text-indigo-800 overflow-hidden shadow-sm rounded-lg p-4 sm:p-6">
          <div className="flex items-center">
            <UserIcon className="h-6 w-6 text-indigo-400" aria-hidden="true"/>
            <div className="ml-4">
              <div className="text-sm font-medium">Total Users</div>
              <div className="mt-1 text-3xl font-semibold">{users.length}</div>
            </div>
          </div>
        </div>
        <div className="bg-green-50 text-green-800 overflow-hidden shadow-sm rounded-lg p-4 sm:p-6">
          <div className="flex items-center">
            <UsersIcon className="h-6 w-6 text-green-400" aria-hidden="true"/>
            <div className="ml-4">
              <div className="text-sm font-medium">Active Users</div>
              <div className="mt-1 text-3xl font-semibold">{userRecentActivityCount}</div>
              <div className="text-xs text-gray-500">logged in within the last 48 hours</div> {/* Small note for last 2 weeks */}
            </div>
          </div>
        </div>
        <div className="bg-yellow-50 text-yellow-800 overflow-hidden shadow-sm rounded-lg p-4 sm:p-6">
          <div className="flex items-center">
            <ChartBarIcon className="h-6 w-6 text-yellow-400" aria-hidden="true"/>
            <div className="ml-4">
              <div className="text-sm font-medium">New Registrations</div>
              <div className="mt-1 text-3xl font-semibold">{newRegistrationsCount}</div>
              <div className="text-xs text-gray-500">last 2 weeks</div> {/* Small note for last 2 weeks */}
            </div>
          </div>
        </div>
        <div className="bg-teal-50 text-teal-800 overflow-hidden shadow-sm rounded-lg p-4 sm:p-6">
          <div className="flex items-center">
            <CheckCircleIcon className="h-6 w-6 text-teal-400" aria-hidden="true"/>
            <div className="ml-4">
              <div className="text-sm font-medium">Verified Users</div>
              <div className="mt-1 text-3xl font-semibold">{verifiedUsersCount}</div>
              <div className="text-xs text-gray-500">email confirmed</div> {/* Small note for last 2 weeks */}
            </div>
          </div>
        </div>
      </div>
      
      {/* Chart Section */}
      <div className="bg-white overflow-hidden rounded-lg p-0 mb-8">
        <h2 className="text-lg font-medium text-gray-900 mb-0">New Users Over Time (Last 4 Weeks)</h2>
        <LineChart users={users}/> {/* Pass the users array to the chart */}
      </div>
      
      {/* Recent Activity / Table */}
      <div className="bg-white overflow-hidden shadow-sm rounded-lg p-0 sm:p-0">
        <h2 className="text-lg font-medium text-gray-900">Recent User Activity</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Activity
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
            </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
            {recentUsers.map((user) => (
              <tr key={user.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{user.email}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">Logged In</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">
                    {moment(user.last_login).fromNow()} {/* Display relative time */}
                  </div>
                </td>
              </tr>
            ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
