import React from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import moment from 'moment';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function LineChart({ users }) {
  // Filter users from the last 5 weeks (35 days) and group them by day
  const days = [];
  const userCounts = [];
  
  // Loop through the last 28 days (4 weeks * 7 days)
  for (let i = 28; i >= 0; i--) {
    const day = moment().subtract(i, 'days').startOf('day');
    const dayLabel = day.format('MMM D');  // Format as "MMM D" (e.g., "Oct 14")
    
    const usersInDay = users.filter(user =>
      moment(user.date_joined).isSame(day, 'day')
    ).length;
    
    days.push(dayLabel);
    userCounts.push(usersInDay);
  }
  
  // Data for Chart.js
  const data = {
    labels: days,  // X-axis labels (days)
    datasets: [
      {
        label: 'New Users',
        data: userCounts,  // Y-axis data (user count per day)
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        fill: true,
        tension: 0.4,  // Add some curve to the line
      }
    ]
  };
  
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    aspectRatio: 2,  // Adjust aspect ratio to control the height of the chart
    plugins: {
      legend: {
        display: true,
        position: 'top'
      },
      title: {
        display: true,
        text: 'New Users Over the Last 4 Weeks (Daily)'
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Days',
        },
      },
      y: {
        title: {
          display: true,
          text: 'New Users',
        },
        ticks: {
          beginAtZero: true,
        }
      }
    }
  };
  
  return (
    <div className="bg-white shadow-md rounded-lg p-0 h-[250px]"> {/* Set container height */}
      <Line data={data} options={options} />
    </div>
  );
}
