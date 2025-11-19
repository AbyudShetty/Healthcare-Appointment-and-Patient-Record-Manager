import { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material'
import { CalendarToday, People, CheckCircle } from '@mui/icons-material'
import axiosInstance from '../../api/axios'
import { formatDate } from '../../utils/formatDate'

const ClinicianDashboard = () => {
  const { user } = useSelector((state) => state.auth)
  const [dashboard, setDashboard] = useState({
    date: new Date().toISOString().split('T')[0],
    total_appointments: 0,
    appointments: [],
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const today = new Date().toISOString().split('T')[0]
        const response = await axiosInstance.get(`/appointments/dashboard/?date=${today}`)
        setDashboard(response.data)
      } catch (error) {
        console.error('Failed to fetch dashboard:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [])

  const stats = [
    {
      title: "Today's Appointments",
      value: dashboard.total_appointments,
      icon: <CalendarToday fontSize="large" />,
      color: '#1976d2',
    },
    {
      title: 'Total Patients',
      value: '45',
      icon: <People fontSize="large" />,
      color: '#2e7d32',
    },
    {
      title: 'Completed Today',
      value: dashboard.appointments.filter((a) => a.status === 'COMPLETED').length,
      icon: <CheckCircle fontSize="large" />,
      color: '#ed6c02',
    },
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Clinician Dashboard
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Welcome, Dr. {user?.last_name || 'Clinician'}
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2, mb: 4 }}>
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

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Today's Schedule
          </Typography>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Patient</TableCell>
                  <TableCell>Patient ID</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {dashboard.appointments.map((appointment) => (
                  <TableRow key={appointment.appointment_id}>
                    <TableCell>{appointment.appointment_time}</TableCell>
                    <TableCell>{appointment.patient_name}</TableCell>
                    <TableCell>{appointment.patient_id}</TableCell>
                    <TableCell>{appointment.reason_for_visit}</TableCell>
                    <TableCell>
                      <Chip
                        label={appointment.status}
                        size="small"
                        color={appointment.status === 'COMPLETED' ? 'success' : 'primary'}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  )
}

export default ClinicianDashboard