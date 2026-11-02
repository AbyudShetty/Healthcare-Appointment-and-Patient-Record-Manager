import { Routes, Route, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { ErrorBoundary } from 'react-error-boundary'
import Login from './modules/auth/Login'
import PatientDashboard from './modules/patient/PatientDashboard'
import PatientRecords from './modules/patient/PatientRecords'
import PatientAppointments from './modules/patient/PatientAppointments'
import ClinicianDashboard from './modules/clinician/ClinicianDashboard'
import AppointmentList from './modules/clinician/AppointmentList'
import PatientNotes from './modules/clinician/PatientNotes'
import AdminDashboard from './modules/admin/AdminDashboard'
import UserManagement from './modules/admin/UserManagement'
import Reports from './modules/admin/Reports'
import SystemLogs from './modules/admin/SystemLogs'
import ProtectedRoute from './routes/ProtectedRoute'
import Layout from './components/Layout'

function App() {
  const { isAuthenticated, restoring, user } = useSelector((state) => state.auth)
  const dashboard = user?.role === 'ADMIN' ? '/admin/dashboard' : user?.role === 'CLINICIAN' ? '/clinician/dashboard' : '/dashboard'
  if (restoring) return <div>Loading session...</div>

  return (
    <ErrorBoundary fallback={<div>Something went wrong</div>}>
      <Routes>
        <Route path="/login" element={
          isAuthenticated ? <Navigate to={dashboard} /> : <Login />
        } />
        
        <Route path="/" element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            {/* Patient Routes */}
            <Route path="dashboard" element={<PatientDashboard />} />
            <Route path="records" element={<PatientRecords />} />
            <Route path="appointments" element={<PatientAppointments />} />
            
            {/* Clinician Routes */}
            <Route path="clinician/dashboard" element={<ClinicianDashboard />} />
            <Route path="clinician/appointments" element={<AppointmentList />} />
            <Route path="clinician/notes/:patientId" element={<PatientNotes />} />
            
            {/* Admin Routes */}
            <Route path="admin/dashboard" element={<AdminDashboard />} />
            <Route path="admin/users" element={<UserManagement />} />
            <Route path="admin/reports" element={<Reports />} />
            <Route path="admin/logs" element={<SystemLogs />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </ErrorBoundary>
  )
}

export default App
