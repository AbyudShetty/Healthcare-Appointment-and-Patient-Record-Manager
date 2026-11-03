import { useEffect, useState } from 'react'
import { Alert, Box, Card, CardContent, Grid, Typography } from '@mui/material'
import axiosInstance from '../../api/axios'

const AdminDashboard = () => {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    Promise.all([axiosInstance.get('/admin/users/'), axiosInstance.get('/appointments/')])
      .then(([users, appointments]) => setStats({
        users: users.data.count ?? users.data.length,
        appointments: appointments.data.count ?? appointments.data.length,
      }))
      .catch(() => setError(true))
  }, [])

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Admin Dashboard</Typography>
      {error && <Alert severity="error">Unable to load dashboard totals.</Alert>}
      {stats && <Grid container spacing={3} sx={{ mt: 2 }}>
        {[['Total Users', stats.users], ['Total Appointments', stats.appointments]].map(([title, value]) => (
          <Grid item xs={12} sm={6} key={title}>
            <Card><CardContent><Typography color="textSecondary">{title}</Typography><Typography variant="h4">{value}</Typography></CardContent></Card>
          </Grid>
        ))}
      </Grid>}
    </Box>
  )
}

export default AdminDashboard
