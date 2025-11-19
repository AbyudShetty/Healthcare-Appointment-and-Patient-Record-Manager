import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Alert,
} from '@mui/material'
import { fetchRecords } from '../../store/slices/recordSlice'
import { formatDate } from '../../utils/formatDate'

const PatientRecords = () => {
  const dispatch = useDispatch()
  const { records, loading, error } = useSelector((state) => state.records)
  const { user } = useSelector((state) => state.auth)

  useEffect(() => {
    if (user?.patient_id) {
      dispatch(fetchRecords(user.patient_id))
    }
  }, [dispatch, user])

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
          Medical Records
        </Typography>
        <Alert severity="error">Failed to load records. Please try again later.</Alert>
      </Box>
    )
  }

  // Ensure records is always an array
  const recordsList = Array.isArray(records) ? records : []

  if (recordsList.length === 0) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Medical Records
        </Typography>
        <Alert severity="info">No medical records found.</Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Medical Records
      </Typography>

      {recordsList.map((record) => (
        <Card key={record.id} sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Record Date: {formatDate(record.created_at)}
            </Typography>
            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" color="primary" gutterBottom>
              Medical History
            </Typography>
            <Typography paragraph>{record.medical_history || 'N/A'}</Typography>

            <Typography variant="subtitle1" color="primary" gutterBottom>
              Diagnoses
            </Typography>
            <Typography paragraph>{record.diagnoses || 'N/A'}</Typography>

            <Typography variant="subtitle1" color="primary" gutterBottom>
              Medications
            </Typography>
            <Typography paragraph>{record.medications || 'N/A'}</Typography>

            {record.clinical_notes && record.clinical_notes.length > 0 && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" color="primary" gutterBottom>
                  Clinical Notes
                </Typography>
                {record.clinical_notes.map((note) => (
                  <Box key={note.id} sx={{ mb: 2, pl: 2, borderLeft: '3px solid #1976d2' }}>
                    <Typography variant="body2" color="textSecondary">
                      {note.clinician} - {formatDate(note.created_at)}
                    </Typography>
                    <Typography>{note.decrypted_note}</Typography>
                  </Box>
                ))}
              </>
            )}
          </CardContent>
        </Card>
      ))}
    </Box>
  )
}

export default PatientRecords