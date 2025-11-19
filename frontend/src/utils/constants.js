export const ROLES = {
  PATIENT: 'PATIENT',
  CLINICIAN: 'CLINICIAN',
  ADMIN: 'ADMIN',
}

export const APPOINTMENT_STATUS = {
  SCHEDULED: 'SCHEDULED',
  COMPLETED: 'COMPLETED',
  CANCELLED: 'CANCELLED',
  NO_SHOW: 'NO_SHOW',
}

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login/',
    REFRESH: '/auth/token/refresh/',
  },
  PATIENTS: {
    REGISTER: '/patients/register/',
    PROFILE: '/patients/profile/',
  },
  APPOINTMENTS: {
    LIST: '/appointments/',
    BOOK: '/appointments/book/',
    SEARCH: '/appointments/search/',
    AVAILABILITY: '/appointments/availability/',
    DASHBOARD: '/appointments/dashboard/',
  },
  RECORDS: {
    HISTORY: (patientId) => `/records/${patientId}/history/`,
    QUICK_CREATE: '/records/quick-create/',
    NOTES_ADD: '/records/notes/add/',
  },
  REPORTS: {
    PATIENT_VOLUME: '/reports/patient-volume/',
  },
}

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'accessToken',
  REFRESH_TOKEN: 'refreshToken',
  USER_DATA: 'userData',
}