import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
} from '@mui/material'
import {
  People,
  EventAvailable,
  Description,
  TrendingUp,
} from '@mui/icons-material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import axiosInstance from '../../api/axios'

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalAppointments: 0,
    totalRecords: 0,
  })

  const chartData = [
    { name: 'Mon', appointments: 12 },
    { name: 'Tue', appointments: 19 },
    { name: 'Wed', appointments: 15 },
    { name: 'Thu', appointments: 25 },
    { name: 'Fri', appointments: 22 },
  ]

  const statCards = [
    {
      title: 'Total Users',
      value: stats.totalUsers,
      icon: <People fontSize="large" />,
      color: '#1976d2',
    },
    {
      title: 'Total Appointments',
      value: stats.totalAppointments,
      icon: <EventAvailable fontSize="large" />,
      color: '#2e7d32',
    },
    {
      title: 'Medical Records',
      value: stats.totalRecords,
      icon: <Description fontSize="large" />,
      color: '#ed6c02',
    },
    {
      title: 'System Health',
      value: '98%',
      icon: <TrendingUp fontSize="large" />,
      color: '#9c27b0',
    },
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Admin Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2, mb: 4 }}>
        {statCards.map((stat) => (
          <Grid item xs={12} sm={6} md={3} key={stat.title}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h4">{stat.value}</Typography>
                  </Box>
                  <Box sx={{ color: stat.color }}>{stat.icon}</Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Appointment Trends
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="appointments" stroke="#1976d2" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Box>
  )
}

export default AdminDashboard