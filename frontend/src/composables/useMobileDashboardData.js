import { ref } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import { useRouter } from 'vue-router'
import io from 'socket.io-client'

export function useMobileDashboardData() {
  const router = useRouter()
  const toast = useToast()
  const loading = ref(false)
  const refreshing = ref(false)
  const user = ref(null)
  const dashboardStats = ref({})
  const allStreams = ref([])
  const agents = ref([])
  const detections = ref({})
  const refreshingStreams = ref(false)
  const settings = {
    enableBackgroundRefresh: true,
    baseRefreshInterval: 5 * 60 * 1000 // 5 minutes
  }

  axios.interceptors.response.use(
    response => response,
    error => {
      if (error.response?.status === 401) {
        toast.error('Session expired. Please log in again.')
        router.push('/')
      }
      return Promise.reject(error)
    }
  )

  const fetchDashboardData = async (showLoading = true) => {
    if (showLoading) loading.value = true
    refreshing.value = true
    try {
      const [userRes, statsRes, streamsRes, agentsRes] = await Promise.all([
        axios.get('/api/session'),
        axios.get('/api/dashboard'),
        axios.get('/api/streams'),
        axios.get('/api/agents')
      ])
      user.value = userRes.data || {}
      dashboardStats.value = statsRes.data || {}
      allStreams.value = (streamsRes.data || []).map(stream => ({
        id: stream.id,
        name: stream.streamer_username || 'Unknown',
        status: stream.status || 'unknown',
        ...stream
      }))
      agents.value = (agentsRes.data || []).map(agent => ({
        id: agent.id,
        name: agent.username || 'Unknown',
        status: agent.online ? 'active' : 'inactive',
        ...agent
      }))
      detections.value = {} // Detections are handled via notifications
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      loading.value = false
      refreshing.value = false
    }
  }

  const refreshStream = async (streamId) => {
    refreshingStreams.value = true
    try {
      const response = await axios.get(`/api/streams/${streamId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      const index = allStreams.value.findIndex(s => s.id === streamId)
      if (index !== -1) {
        allStreams.value[index] = {
          id: response.data.id,
          name: response.data.streamer_username || 'Unknown',
          status: response.data.status || 'unknown',
          ...response.data
        }
      }
      toast.success('Stream refreshed')
    } catch (error) {
      console.error('Error refreshing stream:', error)
      toast.error('Failed to refresh stream')
    } finally {
      refreshingStreams.value = false
    }
  }

  const registerUserActivity = () => {
    // Emit user activity via Socket.IO
    const socket = io('wss://monitor-backend.jetcamstudio.com:5000', {
          path: '/ws',
          transports: ['websocket', 'polling'],
          reconnection: true,
          reconnectionAttempts: 5,
          reconnectionDelay: 1000,
          withCredentials: true,
          autoConnect: true
        })
    socket.emit('user_activity')
  }

  return {
    loading,
    refreshing,
    user,
    dashboardStats,
    allStreams,
    agents,
    detections,
    refreshingStreams,
    fetchDashboardData,
    refreshStream,
    registerUserActivity,
    settings
  }
}