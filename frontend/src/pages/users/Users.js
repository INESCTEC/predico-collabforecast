import DataTable from 'react-data-table-component';
import {useState, useEffect} from 'react';
import {useAuth} from '../../AuthContext'; // Import the useAuth hook to get users
import moment from 'moment';

export default function Users() {
  const { users, fetchUsers } = useAuth();  // Use the users from authContext
  const [filteredUsers, setFilteredUsers] = useState([]);
  
  // Fetch users on component mount
  useEffect(() => {
    fetchUsers();  // This will fetch users when the component mounts
  }, [fetchUsers]);  // Empty dependency array ensures fetchUsers runs only once
  
  // Update filteredUsers when users are updated
  useEffect(() => {
    if (users) {
      setFilteredUsers(users);  // Set filteredUsers when users are available
    }
  }, [users]);  // This useEffect depends on `users` to update `filteredUsers`
  
  // Define columns for the DataTable
  const columns = [
    {
      name: 'Name',
      selector: row => `${row.first_name} ${row.last_name}`,  // Combine first and last names
      sortable: true,
      grow: 2, // Adjusting width of the name column
    },
    {
      name: 'Email',
      selector: row => row.email,
      sortable: true,
    },
    {
      name: 'Role',
      selector: row => row.is_superuser ? 'Admin' : 'User',  // Display "Admin" if is_superuser is true
      sortable: true,
    },
    {
      name: 'Date Joined',
      selector: row => moment(row.date_joined).format('MMMM D, YYYY'),  // Format date_joined
      sortable: true,
    },
    {
      name: 'Active',
      selector: row => (
        row.is_active ?
          <span className="text-green-600">✔</span> :
          <span className="text-red-600">✘</span>
      ),  // Display green checkmark if verified, red cross if not
      sortable: true,
    },
    {
      name: 'Verified',
      selector: row => (
        row.is_verified ?
          <span className="text-green-600">✔</span> :
          <span className="text-red-600">✘</span>
      ),  // Display green checkmark if verified, red cross if not
      sortable: true,  // Enable sorting for the verified status if needed
      center: true,  // Align center for better appearance
    },
  ];
  
  // Custom styles for DataTable
  const customStyles = {
    table: {
      style: {
        borderRadius: '8px',
        border: '1px solid #E5E7EB', // Light gray border
        overflow: 'hidden', // To ensure rounded corners are visible
      },
    },
    headRow: {
      style: {
        backgroundColor: '#F9FAFB', // Light background for header
        fontWeight: 'bold',
      },
    },
    headCells: {
      style: {
        paddingLeft: '16px',
        paddingRight: '16px',
        fontSize: '0.875rem',
        color: '#4B5563', // Darker gray for text
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
      },
    },
    rows: {
      style: {
        minHeight: '56px', // Slightly larger row height for comfort
        borderBottom: '1px solid #E5E7EB', // Light border between rows
      },
      highlightOnHoverStyle: {
        backgroundColor: '#F3F4F6', // Light gray hover effect
        borderBottomColor: '#E5E7EB',
        borderRadius: '8px',
        transition: 'background-color 0.15s ease',
      },
    },
    pagination: {
      style: {
        borderTop: 'none', // Remove top border
        paddingTop: '12px',
      },
    },
  };
  
  return (
    <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <h1 className="text-3xl font-bold text-gray-900">List of Users</h1>
      <p className="mt-2 text-sm text-gray-600">
        Roles, email addresses, and other details of all users.
      </p>
      
      {/* Horizontal layout: Form and Table */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Table section (full width) */}
        <div className="lg:col-span-3">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Users List </h2>
          
          {/* DataTable */}
          <DataTable
            columns={columns}
            data={filteredUsers}
            pagination
            paginationTotalRows={filteredUsers.length} // Displays total rows in pagination
            highlightOnHover
            defaultSortFieldId={1}
            customStyles={customStyles}
          />
        </div>
      </div>
    </div>
  );
}