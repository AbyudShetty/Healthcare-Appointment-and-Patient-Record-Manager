import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Grid, Card, CardContent, Typography, Box } from '@mui/material'
import { CalendarToday, Description, MedicalServices } from '@mui/icons-material'
import { fetchAppointments } from '../../store/slices/appointmentSlice'

const PatientDashboard = () => {
  const dispatch = useDispatch()
  const { appointments } = useSelector((state) => state.appointments)
  const { user } = useSelector((state) => state.auth)

  useEffect(() => {
    dispatch(fetchAppointments())
  }, [dispatch])

  // Ensure appointments is always an array
  const appointmentsList = Array.isArray(appointments) ? appointments : []

  const upcomingAppointments = appointmentsList.filter(
    (apt) => apt.status === 'SCHEDULED'
  ).length

  const stats = [
    {
      title: 'Upcoming Appointments',
      value: upcomingAppointments,
      icon: <CalendarToday fontSize="large" />,
      color: '#1976d2',
    },
    {
      title: 'Medical Records',
      value: '12',
      icon: <Description fontSize="large" />,
      color: '#2e7d32',
    },
    {
      title: 'Prescriptions',
      value: '5',
      icon: <MedicalServices fontSize="large" />,
      color: '#ed6c02',
    },
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome, {user?.user_name || user?.username || 'Patient'}
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {stats.map((stat) => (
          <Grid item xs={12} sm={6} md={4} key={stat.title}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h3">{stat.value}</Typography>
                  </Box>
                  <Box sx={{ color: stat.color }}>{stat.icon}</Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default PatientDashboard