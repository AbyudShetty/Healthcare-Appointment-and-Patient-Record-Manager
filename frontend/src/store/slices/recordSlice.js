import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import axiosInstance from '../../api/axios'
import { fetchAllPages } from '../../api/pagination'

export const fetchRecords = createAsyncThunk(
  'records/fetchAll',
  async (patientId, { rejectWithValue }) => {
    try {
      return await fetchAllPages(`/records/${patientId}/history/`)
    } catch (error) {
      return rejectWithValue(error.response?.data)
    }
  }
)

export const addClinicalNote = createAsyncThunk(
  'records/addNote',
  async ({ recordId, noteContent }, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/records/notes/add/', {
        record_id: recordId,
        note_content: noteContent,
      })
      return response.data
    } catch (error) {
      return rejectWithValue(error.response?.data)
    }
  }
)

const recordSlice = createSlice({
  name: 'records',
  initialState: {
    records: [],  // Initialize as empty array
    loading: false,
    error: null,
  },
  reducers: {
    clearRecordError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRecords.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchRecords.fulfilled, (state, action) => {
        state.loading = false
        // Handle both array and object responses
        if (Array.isArray(action.payload)) {
          state.records = action.payload
        } else if (action.payload.results) {
          state.records = action.payload.results
        } else {
          state.records = []
        }
      })
      .addCase(fetchRecords.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
        state.records = []  // Set to empty array on error
      })
  },
})

export const { clearRecordError } = recordSlice.actions
export default recordSlice.reducer
