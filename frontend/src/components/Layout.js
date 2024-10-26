import { useState } from 'react';
import { Outlet } from 'react-router-dom'; // Import Outlet from react-router-dom
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout({ navigation, teams, userNavigation }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  return (
    <div>
      {/* Sidebar component */}
      <Sidebar navigation={navigation} teams={teams} sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      
      {/* Main content */}
      <div className="flex flex-col lg:pl-72">
        {/* Header */}
        <Header setSidebarOpen={setSidebarOpen} userNavigation={userNavigation} />
        
        {/* Main section with padding to accommodate sidebar */}
        <main className="flex-1 py-10">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {/* Use Outlet to render the nested routes */}
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
