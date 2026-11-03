import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material'
import { Add } from '@mui/icons-material'
import { fetchAppointments, bookAppointment, searchClinicians } from '../../store/slices/appointmentSlice'
import { formatDate } from '../../utils/formatDate'
import axiosInstance from '../../api/axios'

const PatientAppointments = () => {
  const dispatch = useDispatch()
  const { appointments, clinicians, loading, error } = useSelector((state) => state.appointments)
  const { user } = useSelector((state) => state.auth)

  const [open, setOpen] = useState(false)
  const [slots, setSlots] = useState([])
  const [slotsError, setSlotsError] = useState('')
  const [formData, setFormData] = useState({
    clinician: '',
    appointment_date: '',
    appointment_time: '',
    reason_for_visit: '',
  })

  useEffect(() => {
    dispatch(fetchAppointments())
  }, [dispatch])

  useEffect(() => {
    let active = true
    setSlots([])
    setSlotsError('')
    if (!formData.clinician || !formData.appointment_date) return () => { active = false }
    axiosInstance.get(`/appointments/availability/${formData.clinician}/`, { params: { date: formData.appointment_date } })
      .then(({ data }) => { if (active) setSlots(Array.isArray(data) ? data : []) })
      .catch(() => { if (active) setSlotsError('Could not load available times.') })
    return () => { active = false }
  }, [formData.clinician, formData.appointment_date])

  const handleOpen = () => {
    dispatch(searchClinicians(''))
    setOpen(true)
  }

  const handleClose = () => {
    setOpen(false)
    setFormData({
      clinician: '',
      appointment_date: '',
      appointment_time: '',
      reason_for_visit: '',
    })
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value,
      ...(['clinician', 'appointment_date'].includes(e.target.name) ? { appointment_time: '' } : {}) })
  }

  const handleSubmit = async () => {
    // Get patient from user data
    const patientId = user?.id || user?.patient_id
    
    if (!patientId) {
      alert('Patient profile not found. Please contact support.')
      return
    }

    const appointmentData = {
      patient: patientId,
      clinician: parseInt(formData.clinician),
      appointment_date: formData.appointment_date,
      appointment_time: formData.appointment_time,
      reason_for_visit: formData.reason_for_visit,
    }

    const result = await dispatch(bookAppointment(appointmentData))
    if (bookAppointment.fulfilled.match(result)) {
      handleClose()
      dispatch(fetchAppointments())
    } else {
      // Show error
      alert('Failed to book appointment. Please check all fields and try again.')
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

  // Ensure appointments is always an array
  const appointmentsList = Array.isArray(appointments) ? appointments : []
  const cliniciansList = Array.isArray(clinicians) ? clinicians : []

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">My Appointments</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={handleOpen}>
          Book Appointment
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load appointments
        </Alert>
      )}

      {appointmentsList.length === 0 ? (
        <Alert severity="info">No appointments found. Book your first appointment!</Alert>
      ) : (
        <Grid container spacing={2}>
          {appointmentsList.map((appointment) => (
            <Grid item xs={12} md={6} key={appointment.appointment_id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                    <Typography variant="h6">
                      Dr. {appointment.clinician_name}
                    </Typography>
                    <Chip
                      label={appointment.status}
                      color={getStatusColor(appointment.status)}
                      size="small"
                    />
                  </Box>
                  <Typography color="textSecondary" gutterBottom>
                    <strong>Date:</strong> {formatDate(appointment.appointment_date)}
                  </Typography>
                  <Typography color="textSecondary" gutterBottom>
                    <strong>Time:</strong> {appointment.appointment_time}
                  </Typography>
                  <Typography color="textSecondary" gutterBottom>
                    <strong>Duration:</strong> {appointment.duration_minutes} minutes
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    <strong>Reason:</strong> {appointment.reason_for_visit}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Book New Appointment</DialogTitle>
        <DialogContent>
          <TextField
            select
            fullWidth
            margin="normal"
            label="Select Clinician"
            name="clinician"
            value={formData.clinician}
            onChange={handleChange}
            SelectProps={{ native: true }}
          >
            <option value="">Choose a clinician</option>
            {cliniciansList.map((clinician) => (
              <option key={clinician.id} value={clinician.id}>
                {clinician.full_name || `${clinician.first_name} ${clinician.last_name}`}
              </option>
            ))}
          </TextField>

          <TextField
            fullWidth
            margin="normal"
            label="Appointment Date"
            name="appointment_date"
            type="date"
            value={formData.appointment_date}
            onChange={handleChange}
            InputLabelProps={{ shrink: true }}
          />

          <TextField
            select
            fullWidth
            margin="normal"
            label="Available Time"
            name="appointment_time"
            value={formData.appointment_time}
            onChange={handleChange}
            SelectProps={{ native: true }}
          >
            <option value="">Choose an available time</option>
            {slots.map((slot) => <option key={slot.id} value={slot.start_time}>{slot.start_time} – {slot.end_time}</option>)}
          </TextField>
          {slotsError && <Alert severity="error">{slotsError}</Alert>}

          <TextField
            fullWidth
            margin="normal"
            label="Reason for Visit"
            name="reason_for_visit"
            multiline
            rows={3}
            value={formData.reason_for_visit}
            onChange={handleChange}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Book Appointment
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default PatientAppointments
