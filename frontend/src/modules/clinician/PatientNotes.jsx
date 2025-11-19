import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Divider,
} from '@mui/material'
import axiosInstance from '../../api/axios'
import { formatDate } from '../../utils/formatDate'

const PatientNotes = () => {
  const { patientId } = useParams()
  const [records, setRecords] = useState([])
  const [newNote, setNewNote] = useState('')
  const [selectedRecordId, setSelectedRecordId] = useState(null)

  useEffect(() => {
    fetchPatientRecords()
  }, [patientId])

  const fetchPatientRecords = async () => {
    try {
      const response = await axiosInstance.get(`/records/${patientId}/history/`)
      setRecords(response.data)
      if (response.data.length > 0) {
        setSelectedRecordId(response.data[0].id)
      }
    } catch (error) {
      console.error('Failed to fetch records:', error)
    }
  }

  const handleAddNote = async () => {
    if (!newNote.trim() || !selectedRecordId) return

    try {
      await axiosInstance.post('/records/notes/add/', {
        record_id: selectedRecordId,
        note_content: newNote,
      })
      setNewNote('')
      fetchPatientRecords()
    } catch (error) {
      console.error('Failed to add note:', error)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Patient Clinical Notes
      </Typography>
      <Typography variant="subtitle1" color="textSecondary" gutterBottom>
        Patient ID: {patientId}
      </Typography>

      <Card sx={{ mb: 3, mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Add New Clinical Note
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            placeholder="Enter clinical note..."
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Button variant="contained" onClick={handleAddNote}>
            Add Note
          </Button>
        </CardContent>
      </Card>

      {records.map((record) => (
        <Card key={record.id} sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Record Date: {formatDate(record.created_at)}
            </Typography>
            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" color="primary" gutterBottom>
              Medical History
            </Typography>
            <Typography paragraph>{record.medical_history}</Typography>

            <Typography variant="subtitle1" color="primary" gutterBottom>
              Diagnoses
            </Typography>
            <Typography paragraph>{record.diagnoses}</Typography>

            {record.clinical_notes?.length > 0 && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" color="primary" gutterBottom>
                  Clinical Notes
                </Typography>
                {record.clinical_notes.map((note) => (
                  <Box
                    key={note.id}
                    sx={{
                      mb: 2,
                      p: 2,
                      backgroundColor: '#f5f5f5',
                      borderRadius: 1,
                    }}
                  >
                    <Typography variant="body2" color="textSecondary" gutterBottom>
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

export default PatientNotes