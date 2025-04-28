// src/composables/useMobileDashboardData.js
import { ref, onUnmounted, watchEffect } from 'vue'
import MobileStreamService from '../services/MobileStreamService'
import axios from 'axios'

/**
 * Mobile-optimized composable for dashboard data
 * Key features:
 * - Reduced API calls with caching
 * - Optimized data payload sizes
 * - Automatic background refresh with configurable intervals
 * - Battery and data-conscious refresh policy
 */
export function useMobileDashboardData(router, toast) {
  // State management
  const loading = ref(true)
  const refreshing = ref(false)
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
  
  // Binding to cached reactive props from service
  const bindToCachedData = () => {
    watchEffect(() => {
      allStreams.value = MobileStreamService.streams.value
    })
    
    watchEffect(() => {
      agents.value = MobileStreamService.agents.value
    })
  }
  
  // Background refresh timer
  let refreshTimer = null
  let lastUserInteraction = Date.now()
  
  // Settings
  const settings = {
    // Base refresh interval in ms (5 minutes)
    baseRefreshInterval: 5 * 60 * 1000, 
    // Maximum refresh interval when inactive (30 minutes)
    maxRefreshInterval: 30 * 60 * 1000,
    // Inactive threshold (10 minutes)
    inactiveThreshold: 10 * 60 * 1000,
    // Whether background refresh is enabled
    enableBackgroundRefresh: true
  }
  
  /**
   * Fetch dashboard data optimized for mobile
   * @param {boolean} [showLoadingState=true] - Whether to show loading state
   * @returns {Promise} - Promise resolving when data is loaded
   */
  const fetchDashboardData = async (showLoadingState = true) => {
    try {
      if (showLoadingState) loading.value = true
      else refreshing.value = true
      
      hasError.value = false
      
      // Update last interaction time
      lastUserInteraction = Date.now()
      
      // Fetch user session data
      const userResponse = await axios.get('/api/session')
      if (userResponse.data.isLoggedIn) {
        user.value = userResponse.data.user
      } else {
        router.push('/login')
        return
      }
      
      // Fetch mobile-optimized dashboard data
      const dashboardResponse = await MobileStreamService.getMobileDashboard()
      dashboardStats.value = {
        ongoing_streams: dashboardResponse.ongoing_streams || 0,
        total_detections: dashboardResponse.total_detections || 0,
        active_agents: dashboardResponse.active_agents || 0
      }
      
      // Update streams from dashboard response
      if (dashboardResponse.streams) {
        streams.value = dashboardResponse.streams
      }
      
      // Fetch additional data in parallel to speed up loading
      await Promise.all([
        MobileStreamService.getAllStreams(),
        MobileStreamService.getAllAgents()
      ])
      
      // Process detection data if available in dashboard response
      if (dashboardResponse.detections) {
        const groupedDetections = {}
        for (const detection of dashboardResponse.detections) {
          const roomUrl = detection.room_url
          if (!groupedDetections[roomUrl]) {
            groupedDetections[roomUrl] = []
          }
          groupedDetections[roomUrl].push(detection)
        }
        detections.value = groupedDetections
      }
    } catch (error) {
      console.error('Failed to fetch mobile dashboard data:', error)
      hasError.value = true
      errorMessage.value = error.response?.data?.message || 'Failed to load dashboard data'
      
      // Only show error toast in manual refresh
      if (!showLoadingState) {
        toast.error('Failed to refresh data')
      }
    } finally {
      loading.value = false
      refreshing.value = false
    }
  }
  
  /**
   * Refresh dashboard data in background
   * Adjusts refresh interval based on user activity
   * @returns {Promise} - Promise resolving when refresh is complete
   */
  const backgroundRefresh = async () => {
    if (!settings.enableBackgroundRefresh) return
    
    try {
      // Check if user has interacted recently
      const timeSinceLastInteraction = Date.now() - lastUserInteraction
      if (timeSinceLastInteraction > settings.inactiveThreshold) {
        // Only do lightweight refresh when inactive
        await MobileStreamService.getAllStreams(true)
      } else {
        // Full refresh when active
        await fetchDashboardData(false)
      }
    } catch (error) {
      console.error('Background refresh failed:', error)
    }
    
    // Schedule next refresh with dynamic interval
    scheduleNextRefresh()
  }
  
  /**
   * Schedule next background refresh with dynamic interval
   */
  const scheduleNextRefresh = () => {
    if (refreshTimer) clearTimeout(refreshTimer)
    
    // Calculate interval based on inactivity
    const timeSinceLastInteraction = Date.now() - lastUserInteraction
    let interval = settings.baseRefreshInterval
    
    if (timeSinceLastInteraction > settings.inactiveThreshold) {
      // Gradually increase interval when inactive
      const inactiveTime = timeSinceLastInteraction - settings.inactiveThreshold
      const factor = Math.min(inactiveTime / settings.inactiveThreshold, 5)
      interval = Math.min(settings.baseRefreshInterval * (1 + factor), settings.maxRefreshInterval)
    }
    
    refreshTimer = setTimeout(backgroundRefresh, interval)
  }
  
  /**
   * Reset inactivity timer on user interaction
   */
  const registerUserActivity = () => {
    lastUserInteraction = Date.now()
  }
  
  /**
   * Get detection events for a specific stream
   * @param {string} roomUrl - Room URL to get detections for
   * @returns {Array} - Array of detection events
   */
  const getStreamDetections = (roomUrl) => {
    return detections.value[roomUrl] || []
  }
  
  /**
   * Refresh a specific stream
   * Optimized for mobile with reduced payload
   * @param {Object} stream - Stream to refresh
   * @returns {Promise} - Promise resolving when refresh is complete
   */
  const refreshStream = async (stream) => {
    const streamId = stream.id
    try {
      // Prevent duplicate refresh requests
      if (refreshingStreams.value[streamId]) return
      refreshingStreams.value[streamId] = true
      
      // Register user activity
      registerUserActivity()
      
      // Use the mobile service to refresh
      const response = await MobileStreamService.refreshStream(stream)
      
      if (response.m3u8_url) {
        // Update local state
        const updateFn = s => s.id === streamId ? 
          { ...s, m3u8_url: response.m3u8_url } : s
        
        streams.value = streams.value.map(updateFn)
        toast.success('Stream refreshed!')
      } else {
        toast.error('Failed to refresh stream')
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
  
  // Set up data binding and background refresh
  bindToCachedData()
  
  // Start background refresh
  if (settings.enableBackgroundRefresh) {
    scheduleNextRefresh()
  }
  
  // Clean up on unmount
  onUnmounted(() => {
    if (refreshTimer) clearTimeout(refreshTimer)
  })
  
  return {
    loading,
    refreshing,
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
    refreshStream,
    registerUserActivity,
    settings
  }
}