import { format, parseISO } from 'date-fns'

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString
    return format(date, 'MMM dd, yyyy hh:mm a')
  } catch {
    return dateString
  }
}

export const formatDateShort = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString
    return format(date, 'MMM dd, yyyy')
  } catch {
    return dateString
  }
}

export const formatTime = (timeString) => {
  if (!timeString) return 'N/A'
  
  try {
    const [hours, minutes] = timeString.split(':')
    const date = new Date()
    date.setHours(parseInt(hours), parseInt(minutes))
    return format(date, 'hh:mm a')
  } catch {
    return timeString
  }
}