import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  CircularProgress,
  Alert,
} from '@mui/material'
import axiosInstance from '../../api/axios'

const AppointmentList = () => {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedAppointment, setSelectedAppointment] = useState(null)
  const [statusDialogOpen, setStatusDialogOpen] = useState(false)
  const [newStatus, setNewStatus] = useState('')

  useEffect(() => {
    fetchAppointments()
  }, [])

  const fetchAppointments = async () => {
    try {
      setLoading(true)
      const response = await axiosInstance.get('/appointments/')
      // Handle both array and object responses
      const data = Array.isArray(response.data) ? response.data : response.data.results || []
      setAppointments(data)
      setError(null)
    } catch (error) {
      console.error('Failed to fetch appointments:', error)
      setError('Failed to load appointments')
      setAppointments([])
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = (appointment) => {
    setSelectedAppointment(appointment)
    setNewStatus(appointment.status)
    setStatusDialogOpen(true)
  }

  const handleStatusUpdate = async () => {
    try {
      await axiosInstance.patch(`/appointments/status/${selectedAppointment.appointment_id}/`, {
        status: newStatus,
      })
      setStatusDialogOpen(false)
      fetchAppointments()
    } catch (error) {
      console.error('Failed to update status:', error)
      alert('Failed to update appointment status')
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      SCHEDULED: 'primary',
      COMPLETED: 'success',
      CANCELLED: 'error',
      NO_SHOW: 'warning',
    }
    return colors[status] || 'default'
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Appointment Management
        </Typography>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Appointment Management
      </Typography>

      {appointments.length === 0 ? (
        <Alert severity="info">No appointments found.</Alert>
      ) : (
        <Card>
          <CardContent>
            <TableContainer component={Paper} elevation={0}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Appointment ID</TableCell>
                    <TableCell>Patient</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Time</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {appointments.map((appointment) => (
                    <TableRow key={appointment.appointment_id}>
                      <TableCell>{appointment.appointment_id}</TableCell>
                      <TableCell>{appointment.patient_name}</TableCell>
                      <TableCell>{appointment.appointment_date}</TableCell>
                      <TableCell>{appointment.appointment_time}</TableCell>
                      <TableCell>
                        <Chip
                          label={appointment.status}
                          size="small"
                          color={getStatusColor(appointment.status)}
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleStatusChange(appointment)}
                        >
                          Update Status
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      <Dialog open={statusDialogOpen} onClose={() => setStatusDialogOpen(false)}>
        <DialogTitle>Update Appointment Status</DialogTitle>
        <DialogContent>
          <TextField
            select
            fullWidth
            margin="normal"
            label="Status"
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
          >
            <MenuItem value="SCHEDULED">Scheduled</MenuItem>
            <MenuItem value="COMPLETED">Completed</MenuItem>
            <MenuItem value="CANCELLED">Cancelled</MenuItem>
            <MenuItem value="NO_SHOW">No Show</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStatusDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleStatusUpdate} variant="contained">
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AppointmentList