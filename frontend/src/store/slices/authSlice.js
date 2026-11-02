import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import axiosInstance from '../../api/axios'

export const login = createAsyncThunk(
  'auth/login',
  async ({ username, password }, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/auth/login/', {
        username,
        password,
      })
      
      const { access, refresh } = response.data
      localStorage.setItem('accessToken', access)
      localStorage.setItem('refreshToken', refresh)

      const profileResponse = await axiosInstance.get('/patients/profile/')
      return { user: profileResponse.data }
    } catch (error) {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      return rejectWithValue(error.response?.data || 'Login failed')
    }
  }
)

export const restoreSession = createAsyncThunk('auth/restore', async () => {
  if (!localStorage.getItem('accessToken')) return null
  const response = await axiosInstance.get('/patients/profile/')
  return response.data
})

export const logout = createAsyncThunk('auth/logout', async () => {
  localStorage.removeItem('accessToken')
  localStorage.removeItem('refreshToken')
})

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    isAuthenticated: false,
    loading: false,
    restoring: true,
    error: null,
  },
  reducers: {
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(restoreSession.fulfilled, (state, action) => {
        state.restoring = false
        state.user = action.payload
        state.isAuthenticated = Boolean(action.payload)
      })
      .addCase(restoreSession.rejected, (state) => {
        state.restoring = false
        state.user = null
        state.isAuthenticated = false
      })
      .addCase(login.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false
        state.isAuthenticated = true
        state.user = action.payload.user
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
      .addCase(logout.fulfilled, (state) => {
        state.user = null
        state.isAuthenticated = false
      })
  },
})

export const { clearError } = authSlice.actions
export default authSlice.reducer
