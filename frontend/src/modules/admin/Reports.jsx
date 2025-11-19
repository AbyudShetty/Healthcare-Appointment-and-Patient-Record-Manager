import { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material'
import { Download } from '@mui/icons-material'
import axiosInstance from '../../api/axios'

const Reports = () => {
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0])
  const [reportData, setReportData] = useState(null)

  const generateReport = async () => {
    try {
      const response = await axiosInstance.post('/reports/patient-volume/', {
        date: reportDate,
      })
      setReportData(response.data)
    } catch (error) {
      console.error('Failed to generate report:', error)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Patient Volume Reports
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="date"
                label="Report Date"
                value={reportDate}
                onChange={(e) => setReportDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Button
                fullWidth
                variant="contained"
                onClick={generateReport}
                startIcon={<Download />}
              >
                Generate Report
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {reportData && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Report for {reportData.report_date}
            </Typography>
            <TableContainer component={Paper} elevation={0}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Metric</TableCell>
                    <TableCell align="right">Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Total Appointments</TableCell>
                    <TableCell align="right">{reportData.total_appointments}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Completed</TableCell>
                    <TableCell align="right">{reportData.completed_appointments}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Cancelled</TableCell>
                    <TableCell align="right">{reportData.cancelled_appointments}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>No Show</TableCell>
                    <TableCell align="right">{reportData.no_show_appointments}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default Reports