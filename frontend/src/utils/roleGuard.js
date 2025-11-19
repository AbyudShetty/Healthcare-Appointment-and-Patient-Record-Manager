import { ROLES } from './constants'

export const hasRole = (user, allowedRoles) => {
  if (!user || !user.role) return false
  return allowedRoles.includes(user.role)
}

export const isPatient = (user) => hasRole(user, [ROLES.PATIENT])

export const isClinician = (user) => hasRole(user, [ROLES.CLINICIAN])

export const isAdmin = (user) => hasRole(user, [ROLES.ADMIN])

export const canAccessRoute = (user, requiredRoles) => {
  if (!requiredRoles || requiredRoles.length === 0) return true
  return hasRole(user, requiredRoles)
}

export const getDefaultRoute = (user) => {
  if (!user) return '/login'
  
  switch (user.role) {
    case ROLES.ADMIN:
      return '/admin/dashboard'
    case ROLES.CLINICIAN:
      return '/clinician/dashboard'
    case ROLES.PATIENT:
    default:
      return '/dashboard'
  }
}