import { useState } from 'react'
import { Alert, Box, Button, TextField, Typography } from '@mui/material'
import axiosInstance from '../../api/axios'

export default function MFASettings() {
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [enrollment, setEnrollment] = useState(null)
  const [recovery, setRecovery] = useState([])
  const [message, setMessage] = useState('')

  const start = async () => {
    try {
      const { data } = await axiosInstance.post('/auth/mfa/enroll/', { password })
      setEnrollment(data); setMessage(''); setRecovery([])
    } catch (error) { setMessage(error.response?.data?.detail || 'Unable to start enrollment.') }
  }
  const confirm = async () => {
    try {
      const { data } = await axiosInstance.post('/auth/mfa/confirm/', { code })
      setRecovery(data.recovery_codes); setEnrollment(null); setPassword(''); setCode(''); setMessage('MFA enabled.')
    } catch (error) { setMessage(error.response?.data?.detail || 'Unable to enable MFA.') }
  }
  const disable = async () => {
    try {
      await axiosInstance.post('/auth/mfa/disable/', { password, code })
      setEnrollment(null); setRecovery([]); setPassword(''); setCode(''); setMessage('MFA disabled.')
    } catch (error) { setMessage(error.response?.data?.detail || 'Unable to disable MFA.') }
  }

  return <Box>
    <Typography variant="h4" gutterBottom>Authenticator security</Typography>
    {message && <Alert sx={{ my: 2 }}>{message}</Alert>}
    <TextField label="Current password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} fullWidth margin="normal" />
    <Button onClick={start}>Set up authenticator</Button>
    {enrollment && <Box sx={{ my: 2 }}>
      <Typography>Scan this QR code in your authenticator app, or enter the setup key manually. It expires in 10 minutes.</Typography>
      <img alt="Authenticator setup QR code" width="220" src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(enrollment.qr_svg)}`} />
      <Typography>Setup key: {enrollment.secret}</Typography>
    </Box>}
    <TextField label="Authenticator or recovery code" value={code} onChange={(event) => setCode(event.target.value)} fullWidth margin="normal" />
    {enrollment && <Button variant="contained" onClick={confirm}>Confirm setup</Button>}
    <Button color="error" onClick={disable}>Disable MFA</Button>
    {recovery.length > 0 && <Box sx={{ mt: 3 }}><Alert severity="warning">Save these one-use recovery codes securely. They will not be shown again.</Alert>
      {recovery.map((item) => <Typography key={item}><code>{item}</code></Typography>)}
    </Box>}
  </Box>
}
