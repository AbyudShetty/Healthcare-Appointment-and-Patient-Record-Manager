import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import axiosInstance from '../../api/axios'
import { fetchAllPages } from '../../api/pagination'

export const fetchAppointments = createAsyncThunk(
  'appointments/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      return await fetchAllPages('/appointments/')
    } catch (error) {
      return rejectWithValue(error.response?.data)
    }
  }
)

export const bookAppointment = createAsyncThunk(
  'appointments/book',
  async (appointmentData, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/appointments/book/', appointmentData)
      return response.data
    } catch (error) {
      return rejectWithValue(error.response?.data)
    }
  }
)

export const searchClinicians = createAsyncThunk(
  'appointments/searchClinicians',
  async (query, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.get(`/appointments/search/?q=${query}`)
      return response.data
    } catch (error) {
      return rejectWithValue(error.response?.data)
    }
  }
)

const appointmentSlice = createSlice({
  name: 'appointments',
  initialState: {
    appointments: [],  // Initialize as empty array
    clinicians: [],
    loading: false,
    error: null,
  },
  reducers: {
    clearAppointmentError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAppointments.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchAppointments.fulfilled, (state, action) => {
        state.loading = false
        // Handle both array and paginated responses
        if (Array.isArray(action.payload)) {
          state.appointments = action.payload
        } else if (action.payload.results) {
          state.appointments = action.payload.results
        } else {
          state.appointments = []
        }
      })
      .addCase(fetchAppointments.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
        state.appointments = []  // Set to empty array on error
      })
      .addCase(bookAppointment.fulfilled, (state, action) => {
        state.appointments.push(action.payload)
      })
      .addCase(searchClinicians.fulfilled, (state, action) => {
        // Handle both array and object responses
        if (Array.isArray(action.payload)) {
          state.clinicians = action.payload
        } else if (action.payload.results) {
          state.clinicians = action.payload.results
        } else {
          state.clinicians = []
        }
      })
  },
})

export const { clearAppointmentError } = appointmentSlice.actions
export default appointmentSlice.reducer
