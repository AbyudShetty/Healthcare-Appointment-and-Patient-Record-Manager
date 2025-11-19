import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import appointmentReducer from './slices/appointmentSlice'
import recordReducer from './slices/recordSlice'

const store = configureStore({
  reducer: {
    auth: authReducer,
    appointments: appointmentReducer,
    records: recordReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
})

export default store