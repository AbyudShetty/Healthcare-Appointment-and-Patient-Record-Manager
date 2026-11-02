import { useEffect, useState } from 'react'
import { Alert, Box, Button, Card, CardContent, TextField, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import axiosInstance from '../../api/axios'

const ClinicianDashboard = () => {
  const [date, setDate] = useState('')
  const [schedule, setSchedule] = useState(null)
  const [error, setError] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    axiosInstance.get('/appointments/dashboard/', { params: date ? { date } : {} })
      .then(({ data }) => { setSchedule(data); setError(false) })
      .catch(() => { setError(true); setSchedule(null) })
  }, [date])

  return <Box>
    <Typography variant="h4" gutterBottom>Daily Schedule</Typography>
    <TextField type="date" label="Date" value={date} onChange={(event) => setDate(event.target.value)} InputLabelProps={{ shrink: true }} />
    {error && <Alert severity="error">Unable to load the schedule.</Alert>}
    {schedule && <>
      <Typography sx={{ my: 2 }}>{schedule.date}: {schedule.total_appointments} appointments</Typography>
      {schedule.appointments.map((appointment) => <Card key={appointment.appointment_id} sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6">{appointment.appointment_time} — {appointment.patient_name}</Typography>
          <Typography>{appointment.reason_for_visit}</Typography>
          <Typography>{appointment.status}</Typography>
          <Button onClick={() => navigate(`/clinician/notes/${appointment.patient_id}`)}>View records</Button>
        </CardContent>
      </Card>)}
    </>}
  </Box>
}

export default ClinicianDashboard
