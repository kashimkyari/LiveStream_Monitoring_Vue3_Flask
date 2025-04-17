// src/composables/useDashboardData.js
import { ref } from 'vue'
import axios from 'axios'

export function useDashboardData(router, toast) {
  // State
  const loading = ref(true)
  const hasError = ref(false)
  const errorMessage = ref('')
  const user = ref({})
  const refreshingStreams = ref({}) // Track ongoing refresh operations
  
  // Data
  const dashboardStats = ref({
    ongoing_streams: 0,
    total_detections: 0,
    active_agents: 0
  })
  const streams = ref([])
  const allStreams = ref([])
  const agents = ref([])
  const detections = ref({})
  
  // Methods
  const fetchDashboardData = async () => {
    try {
      loading.value = true
      hasError.value = false
      
      const userResponse = await axios.get('/api/session')
      if (userResponse.data.isLoggedIn) {
        user.value = userResponse.data.user
      } else {
        router.push('/login')
        return
      }
      
      const [dashboardResponse, streamsResponse, agentsResponse] = await Promise.all([
        axios.get('/api/dashboard'),
        axios.get('/api/streams'),
        axios.get('/api/agents')
      ])
      
      dashboardStats.value = {
        ongoing_streams: dashboardResponse.data.ongoing_streams,
        total_detections: 0,
        active_agents: agentsResponse.data.filter(a => a.online).length
      }
      
      streams.value = dashboardResponse.data.streams
      allStreams.value = streamsResponse.data
      agents.value = agentsResponse.data
      
      // Process detections data
      const groupedDetections = {}
      // Process detection data without relying on notifications
      // You might need to adapt this method to get detection data 
      // from a different API endpoint
      
      detections.value = groupedDetections
      loading.value = false
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      hasError.value = true
      errorMessage.value = error.response?.data?.message || 'Failed to load dashboard data'
      loading.value = false
      toast.error('Failed to load dashboard data')
    }
  }
  
  const getStreamDetections = (roomUrl) => {
    return detections.value[roomUrl] || []
  }
  
  const refreshStream = async (stream) => {
    const streamId = stream.id
    try {
      // Prevent duplicate refresh requests
      if (refreshingStreams.value[streamId]) return
      refreshingStreams.value[streamId] = true

      let response, payload
      const platform = stream.platform.toLowerCase()

      // Prepare platform-specific payload and ensure proper URL construction
      if (platform === 'chaturbate') {
        // Extract username from existing URL or construct it if needed
        let username
        if (stream.room_url && stream.room_url.includes('chaturbate.com/')) {
          username = stream.room_url.split('/').filter(Boolean).pop()
        } else {
          // If we only have the username, ensure it's clean
          username = (stream.username || stream.room_url || '').replace(/[^a-zA-Z0-9_-]/g, '')
        }
        
        // Construct the full URL if needed
        const fullRoomUrl = username ? `https://chaturbate.com/${username}` : ''
        
        // Set the payload with the username
        payload = { 
          room_slug: username,
          room_url: fullRoomUrl 
        }
      } else if (platform === 'stripchat') {
        // Extract username from existing URL or construct it if needed
        let username
        if (stream.room_url && stream.room_url.includes('stripchat.com/')) {
          username = stream.room_url.split('/').filter(Boolean).pop()
        } else {
          // If we only have the username, ensure it's clean
          username = (stream.username || stream.room_url || '').replace(/[^a-zA-Z0-9_-]/g, '')
        }
        
        // Construct the full URL if needed
        const fullRoomUrl = username ? `https://stripchat.com/${username}` : ''
        
        payload = { room_url: fullRoomUrl }
      } else {
        toast.error('Stream refresh not supported for this platform')
        return
      }

      // Make refresh request
      response = await axios.post(
        `/api/streams/refresh/${platform}`,
        payload
      )

      if (response.data.m3u8_url) {
        // Update local state without full reload
        const updateFn = s => s.id === streamId ? 
          { ...s, m3u8_url: response.data.m3u8_url } : s
        
        streams.value = streams.value.map(updateFn)
        allStreams.value = allStreams.value.map(updateFn)
        
        toast.success('Stream refreshed successfully!')
      } else {
        toast.error('Failed to refresh stream - no valid URL received')
      }
    } catch (error) {
      console.error('Failed to refresh stream:', error)
      const errorMsg = error.response?.data?.message ||
        error.message ||
        'Failed to refresh stream'
      
      toast.error(errorMsg)
    } finally {
      refreshingStreams.value[streamId] = false
    }
  }
  
  return {
    loading,
    hasError,
    errorMessage,
    user,
    dashboardStats,
    streams,
    allStreams,
    agents,
    detections,
    refreshingStreams,
    fetchDashboardData,
    getStreamDetections,
    refreshStream
  }
}