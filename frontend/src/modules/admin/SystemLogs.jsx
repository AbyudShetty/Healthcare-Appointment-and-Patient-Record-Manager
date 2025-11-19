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
  TextField,
  CircularProgress,
  Alert,
} from '@mui/material'
import axiosInstance from '../../api/axios'
import { formatDate } from '../../utils/formatDate'

const SystemLogs = () => {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchLogs()
  }, [])

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const response = await axiosInstance.get('/admin/logs/')
      const data = Array.isArray(response.data) ? response.data : response.data.results || []
      setLogs(data)
      setError(null)
    } catch (error) {
      console.error('Failed to fetch logs:', error)
      setError('Audit logs feature coming soon!')
      setLogs([])
    } finally {
      setLoading(false)
    }
  }

  const filteredLogs = logs.filter((log) =>
    log.action?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.user?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getActionColor = (action) => {
    if (action?.includes('LOGIN')) return 'info'
    if (action?.includes('CREATE')) return 'success'
    if (action?.includes('DELETE')) return 'error'
    if (action?.includes('UPDATE')) return 'warning'
    return 'default'
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Audit Logs
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField
            fullWidth
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </CardContent>
      </Card>

      {error && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {filteredLogs.length === 0 && !error ? (
        <Alert severity="info">No audit logs found.</Alert>
      ) : (
        <Card>
          <CardContent>
            <TableContainer component={Paper} elevation={0}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>User</TableCell>
                    <TableCell>Action</TableCell>
                    <TableCell>Details</TableCell>
                    <TableCell>IP Address</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>{formatDate(log.timestamp)}</TableCell>
                      <TableCell>{log.user}</TableCell>
                      <TableCell>
                        <Chip
                          label={log.action}
                          size="small"
                          color={getActionColor(log.action)}
                        />
                      </TableCell>
                      <TableCell>{log.details}</TableCell>
                      <TableCell>{log.ip_address}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default SystemLogs