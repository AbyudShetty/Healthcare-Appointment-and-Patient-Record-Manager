import { Drawer, List, ListItem, ListItemIcon, ListItemText, Divider } from '@mui/material'
import {
  Dashboard,
  CalendarToday,
  Description,
  People,
  Assessment,
  Settings,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useSelector } from 'react-redux'

const drawerWidth = 240

const Sidebar = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useSelector((state) => state.auth)

  const patientMenuItems = [
    { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
    { text: 'Appointments', icon: <CalendarToday />, path: '/appointments' },
    { text: 'Medical Records', icon: <Description />, path: '/records' },
  ]

  const clinicianMenuItems = [
    { text: 'Dashboard', icon: <Dashboard />, path: '/clinician/dashboard' },
    { text: 'Appointments', icon: <CalendarToday />, path: '/clinician/appointments' },
  ]

  const adminMenuItems = [
    { text: 'Dashboard', icon: <Dashboard />, path: '/admin/dashboard' },
    { text: 'User Management', icon: <People />, path: '/admin/users' },
    { text: 'Reports', icon: <Assessment />, path: '/admin/reports' },
    { text: 'System Logs', icon: <Settings />, path: '/admin/logs' },
  ]

  const getMenuItems = () => {
    const role = user?.role || 'PATIENT'
    if (role === 'CLINICIAN') return clinicianMenuItems
    if (role === 'ADMIN') return adminMenuItems
    return patientMenuItems
  }

  const menuItems = getMenuItems()

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          mt: 8,
        },
      }}
    >
      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            onClick={() => navigate(item.path)}
            selected={location.pathname === item.path}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Drawer>
  )
}

export default Sidebar