<template>
  <div class="mobile-agent-dashboard" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <!-- Existing page header code remains the same -->
    <div class="page-header">
      <h1>Agent Dashboard <span class="mobile-badge">Mobile</span></h1>
    </div>
    
    <!-- Existing dashboard tabs code remains the same -->
    <div class="dashboard-tabs">
      <div 
        v-for="(tab, index) in tabs" 
        :key="index" 
        class="tab-item" 
        :class="{ active: activeTab === index }"
        @click="activeTab = index"
      >
        <div class="tab-icon-container">
          <font-awesome-icon :icon="tab.icon" class="tab-icon" />
          <span v-if="tab.icon === 'bell' && unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </div>
        <span class="tab-text">{{ tab.name }}</span>
      </div>
    </div>
    
    <div class="tab-content">
      <!-- My Streams tab with View Toggle -->
      <div v-if="activeTab === 0" class="tab-pane">
        <div class="section-header">
          <h2>My Assigned Streams</h2>
          <div class="view-controls">
            <div class="view-toggle">
              <button 
                class="view-toggle-btn" 
                :class="{ active: viewMode === 'list' }" 
                @click="viewMode = 'list'"
                title="List View"
              >
                <font-awesome-icon icon="list" />
              </button>
              <button 
                class="view-toggle-btn" 
                :class="{ active: viewMode === 'grid' }" 
                @click="viewMode = 'grid'"
                title="Grid View"
              >
                <font-awesome-icon icon="th" />
              </button>
            </div>
            <div class="refresh-button" @click="loadAssignments">
              <font-awesome-icon icon="sync" :class="{ 'fa-spin': isLoadingAssignments }" />
            </div>
          </div>
        </div>
        
        <div v-if="isLoadingAssignments" class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading your streams...</p>
        </div>
        
        <div v-else-if="assignments.length === 0" class="empty-state">
          <p>You don't have any assigned streams.</p>
        </div>
        
        <!-- List View Mode -->
        <div v-else-if="viewMode === 'list'" class="stream-cards-list">
          <mobile-stream-card
            v-for="assignment in assignments"
            :key="assignment.id"
            :stream="assignment"
            :is-refreshing="refreshingStreamId === assignment.id"
            @click="openStreamDetails(assignment)"
            @refresh="refreshStream(assignment.id)"
          />
        </div>
        
        <!-- Grid View Mode with preview playing -->
        <div v-else class="stream-cards-grid">
          <div 
            v-for="assignment in assignments" 
            :key="assignment.id" 
            class="grid-stream-card"
            @click="openStreamDetails(assignment)"
          >
            <div class="grid-preview-container">
              <!-- Video preview (autoplay in grid view) -->
              <video 
                v-if="assignment.is_online && assignment.video_url" 
                class="grid-video-preview" 
                :src="assignment.video_url" 
                autoplay 
                muted 
                loop
                playsinline
              ></video>
              
              <!-- Static image fallback -->
              <img 
                v-else-if="assignment.preview_url" 
                :src="assignment.preview_url" 
                alt="Stream Preview" 
                class="grid-preview-image"
              />
              
              <!-- No preview fallback -->
              <div v-else class="grid-no-preview">
                <font-awesome-icon icon="video" class="no-preview-icon" />
              </div>
              
              <!-- Status badges -->
              <div class="grid-stream-status" :class="{ 'online': assignment.is_online }">
                {{ assignment.is_online ? 'LIVE' : 'OFFLINE' }}
              </div>
              
              <div class="grid-platform-badge" :class="assignment.platform.toLowerCase()">
                {{ assignment.platform }}
              </div>
              
              <!-- Viewer count -->
              <div class="grid-viewer-count">
                <font-awesome-icon icon="eye" /> {{ formatNumber(assignment.viewer_count || 0) }}
              </div>
            </div>
            
            <div class="grid-stream-info">
              <div class="grid-stream-title">{{ assignment.streamer_username }}</div>
              <div class="grid-stream-duration">
                <font-awesome-icon icon="clock" class="stat-icon" />
                {{ formatDuration(assignment.stream_start_time) }}
              </div>
            </div>
            
            <!-- Refresh button -->
            <button 
              class="grid-refresh-button" 
              @click.stop="refreshStream(assignment.id)"
              :disabled="refreshingStreamId === assignment.id"
              title="Refresh Stream"
            >
              <font-awesome-icon icon="sync" :class="{ 'fa-spin': refreshingStreamId === assignment.id }" />
            </button>
          </div>
        </div>
      </div>
      
      <!-- Rest of the existing tabs remain the same -->
      <!-- Analytics Tab -->
      <div v-else-if="activeTab === 1" class="tab-pane">
        <!-- Analytics tab content remains unchanged -->
      </div>
      
      <!-- Messages Tab -->
      <div v-else-if="activeTab === 2" class="tab-pane">
        <!-- Messages tab content remains unchanged -->
      </div>
      
      <!-- Notifications Tab -->
      <div v-else-if="activeTab === 3" class="tab-pane">
        <!-- Notifications tab content remains unchanged -->
      </div>
      
      <!-- Settings Tab -->
      <div v-else-if="activeTab === 4" class="tab-pane">
        <!-- Settings tab content remains unchanged -->
      </div>
    </div>
    
    <!-- Stream Details Modal -->
    <div v-if="showStreamDetailModal" class="stream-detail-modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ selectedStream.streamer_username }}</h3>
          <button class="close-button" @click="closeStreamModal">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        
        <div class="stream-video-container">
          <!-- Full video player -->
          <video 
            v-if="selectedStream && selectedStream.video_url" 
            ref="videoPlayer"
            class="stream-video-player" 
            :src="selectedStream.video_url" 
            autoplay 
            controls
            playsinline
          ></video>
          
          <!-- Fallback if no video URL -->
          <div v-else class="no-video-message">
            <font-awesome-icon icon="exclamation-triangle" size="2x" />
            <p>Video stream not available</p>
          </div>
        </div>
        
        <div class="stream-details">
          <div class="stream-info-row">
            <div class="info-item">
              <span class="info-label">Platform:</span>
              <span class="info-value platform" :class="selectedStream.platform.toLowerCase()">
                {{ selectedStream.platform }}
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">Status:</span>
              <span class="info-value status" :class="{ 'online': selectedStream.is_online }">
                {{ selectedStream.is_online ? 'LIVE' : 'OFFLINE' }}
              </span>
            </div>
          </div>
          
          <div class="stream-info-row">
            <div class="info-item">
              <span class="info-label">Viewers:</span>
              <span class="info-value">{{ formatNumber(selectedStream.viewer_count || 0) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Stream Duration:</span>
              <span class="info-value">{{ formatDuration(selectedStream.stream_start_time) }}</span>
            </div>
          </div>
          
          <div class="stream-actions-container">
            <button class="action-button refresh" @click="refreshStreamInModal">
              <font-awesome-icon icon="sync" :class="{ 'fa-spin': isRefreshingModal }" />
              Refresh Stream
            </button>
            <button class="action-button mute" @click="toggleMute">
              <font-awesome-icon :icon="isMuted ? 'volume-mute' : 'volume-up'" />
              {{ isMuted ? 'Unmute' : 'Mute' }}
            </button>
            <button class="action-button fullscreen" @click="toggleFullscreen">
              <font-awesome-icon icon="expand" />
              Fullscreen
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject, onMounted, watch, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import AuthService from '../services/AuthService'
import { formatDistance } from 'date-fns'
import { useMobileNotifications } from '../composables/useMobileNotifications'
import anime from 'animejs/lib/anime.es'
import axios from 'axios'
import MobileStreamCard from './MobileStreamCard.vue'

export default {
  name: 'MobileAgentDashboard',
  components: {
    MobileStreamCard
  },
  setup() {
    // Theme state - synced with app-level theme
    const isDarkTheme = ref(localStorage.getItem('themePreference') === 'dark')
    
    // Get theme update method from App.vue
    const updateAppTheme = inject('updateTheme', null)
    
    // If app provides a theme, use that
    const appTheme = inject('isDarkTheme', null)
    if (appTheme !== null) {
      isDarkTheme.value = appTheme.value
    }
    const toast = useToast()
    
    // Use mobile notifications composable
    const { 
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      formatTimeAgo: formatNotificationTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle
    } = useMobileNotifications()
    
    // Tab management
    const tabs = [
      { name: 'Streams', icon: 'video' },
      { name: 'Analytics', icon: 'chart-line' },
      { name: 'Messages', icon: 'comment' },
      { name: 'Notifications', icon: 'bell' },
      { name: 'Settings', icon: 'cog' }
    ]
    const activeTab = ref(0)
    
    // View mode for streams (list or grid)
    const viewMode = ref('list')
    
    // Streams data
    const assignments = ref([])
    const isLoadingAssignments = ref(false)
    const refreshingStreamId = ref(null)
    const currentAgentId = ref(null)
    
    // Analytics data (simplified for mobile)
    const stats = ref({
      totalAssignments: 0,
      activeStreams: 0,
      completedToday: 0
    })
    
    // Settings
    const settings = ref({
      emailNotifications: true,
      pushNotifications: false
    })
    
    // Stream detail modal
    const showStreamDetailModal = ref(false)
    const selectedStream = ref(null)
    const lastRefreshedTime = ref(new Date())
    const isRefreshingModal = ref(false)
    const videoPlayer = ref(null)
    const isMuted = ref(false)
    
    // Load assignments when component mounts
    onMounted(async () => {
      // Get current user session first to ensure we have the agent ID
      try {
        const sessionResponse = await axios.get('/api/session')
        if (sessionResponse.data?.isLoggedIn) {
          currentAgentId.value = sessionResponse.data.user.id
          await loadAssignments()
          calculateStats()
          
          // Initialize socket connection if logged in
          if (currentAgentId.value) {
            initializeSocketConnection()
          }
        } else {
          // Handle not logged in state
          toast.error('Session expired. Please log in again.')
          setTimeout(() => {
            window.location.href = '/'
          }, 3000)
        }
      } catch (err) {
        console.error('Error fetching session:', err)
        toast.error('Unable to authenticate. Please try again.')
      }
    })
    
    // Load agent's assigned streams
    const loadAssignments = async () => {
      if (isLoadingAssignments.value) return
      
      isLoadingAssignments.value = true
      const errorMessage = ref(null)
      
      try {
        // Ensure we have the current agent's ID
        if (!currentAgentId.value) {
          const sessionResponse = await axios.get('/api/session')
          if (!sessionResponse.data?.isLoggedIn) {
            errorMessage.value = 'Unable to authenticate. Please log in again.'
            isLoadingAssignments.value = false
            return
          }
          currentAgentId.value = sessionResponse.data.user.id
        }
        
        // Fetch all streams
        const streamsResponse = await axios.get('/api/streams')
        const allStreams = streamsResponse.data || {}
        
        // Process streams into an array format with enhanced properties
        const processedStreams = Object.keys(allStreams).map(key => {
          const stream = allStreams[key]
          
          // Determine if this stream is assigned to the current agent
          const isAssignedToCurrentAgent = stream.assignments && 
            stream.assignments.some(assignment => assignment.agent_id === currentAgentId.value)
          
          // Enhance stream with additional properties needed for UI
          return {
            ...stream,
            id: stream.id,
            is_online: true, // Assuming all returned streams are live
            viewer_count: Math.floor(Math.random() * 5000) + 500, // Placeholder for viewer count
            stream_start_time: new Date(Date.now() - Math.floor(Math.random() * 10800000)).toISOString(), // Random start time within last 3 hours
            preview_url: stream.preview_url || null,
            is_assigned_to_current_agent: isAssignedToCurrentAgent,
            video_url: stream.platform === 'Chaturbate' ? stream.chaturbate_m3u8_url : stream.stripchat_m3u8_url,
            streamer_username: stream.username || `Streamer_${Math.floor(Math.random() * 1000)}`
          }
        })
        
        // Filter only assigned streams for the current agent
        assignments.value = processedStreams.filter(stream => stream.is_assigned_to_current_agent)
        
        lastRefreshedTime.value = new Date()
        calculateStats()
        
      } catch (err) {
        console.error('Error fetching assignments:', err)
        errorMessage.value = 'Failed to load assignments. Please try again.'
        assignments.value = [] // Reset on error
        
        toast.error('Could not load assignments')
      } finally {
        isLoadingAssignments.value = false
      }
    }
    
    // Refresh a specific stream
    const refreshStream = async (streamId) => {
      if (refreshingStreamId.value === streamId) return
      
      refreshingStreamId.value = streamId
      
      try {
        const response = await axios.get(`/api/streams/${streamId}`)
        const updatedStream = response.data
        
        // Find and update the stream in our assignments list
        const index = assignments.value.findIndex(s => s.id === streamId)
        if (index !== -1) {
          // Update with enhanced properties for UI
          assignments.value[index] = {
            ...updatedStream,
            is_online: true,
            is_assigned_to_current_agent: true,
            video_url: updatedStream.platform === 'Chaturbate' ? 
              updatedStream.chaturbate_m3u8_url : updatedStream.stripchat_m3u8_url,
            streamer_username: updatedStream.username || assignments.value[index].streamer_username
          }
          
          // If this is the currently selected stream, update it too
          if (selectedStream.value && selectedStream.value.id === streamId) {
            selectedStream.value = assignments.value[index]
          }
        }
        
        toast.success('Stream refreshed')
      } catch (err) {
        console.error('Error refreshing stream:', err)
        toast.error('Could not refresh stream')
      } finally {
        refreshingStreamId.value = null
      }
    }
    
    // Refresh stream in modal
    const refreshStreamInModal = async () => {
      if (!selectedStream.value || isRefreshingModal.value) return
      
      isRefreshingModal.value = true
      
      try {
        await refreshStream(selectedStream.value.id)
        
        // If we have a video player, reload it
        if (videoPlayer.value) {
          const currentTime = videoPlayer.value.currentTime
          videoPlayer.value.load()
          videoPlayer.value.currentTime = currentTime
          
          // Maintain mute state
          videoPlayer.value.muted = isMuted.value
          
          // Continue playing
          videoPlayer.value.play().catch(err => {
            console.warn('Failed to autoplay video after refresh:', err)
          })
        }
      } catch (err) {
        console.error('Error refreshing stream in modal:', err)
      } finally {
        isRefreshingModal.value = false
      }
    }
    
    // Calculate analytics stats based on assignments
    const calculateStats = () => {
      stats.value.totalAssignments = assignments.value.length
      
      // Count active streams (simplified logic for example)
      stats.value.activeStreams = assignments.value.filter(a => a.is_online).length
      
      // Count completed today (simplified)
      const today = new Date().toDateString()
      stats.value.completedToday = assignments.value.filter(a => 
        a.completed && new Date(a.completed_at).toDateString() === today
      ).length || Math.floor(Math.random() * 5) // Placeholder value
    }
    
    // Open stream details modal
    const openStreamDetails = (stream) => {
      selectedStream.value = stream
      showStreamDetailModal.value = true
      
      // Reset mute state
      isMuted.value = false
      
      // Wait for the modal to be mounted before interacting with the video player
      nextTick(() => {
        if (videoPlayer.value) {
          videoPlayer.value.muted = false
          videoPlayer.value.play().catch(err => {
            console.warn('Failed to autoplay video:', err)
            // Fallback to muted autoplay if unmuted autoplay fails
            if (videoPlayer.value) {
              videoPlayer.value.muted = true
              isMuted.value = true
              videoPlayer.value.play().catch(e => {
                console.error('Failed to autoplay even with muted video:', e)
              })
            }
          })
        }
      })
    }
    
    // Close stream detail modal
    const closeStreamModal = () => {
      // Pause video if playing
      if (videoPlayer.value) {
        videoPlayer.value.pause()
      }
      
      showStreamDetailModal.value = false
      selectedStream.value = null
    }
    
    // Toggle video mute
    const toggleMute = () => {
      if (!videoPlayer.value) return
      
      isMuted.value = !isMuted.value
      videoPlayer.value.muted = isMuted.value
    }
    
    // Toggle fullscreen mode
    const toggleFullscreen = () => {
      if (!videoPlayer.value) return
      
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(err => {
          console.error('Error exiting fullscreen:', err)
        })
      } else {
        videoPlayer.value.requestFullscreen().catch(err => {
          console.error('Error entering fullscreen:', err)
        })
      }
    }
    
    // Format number for display (e.g. 1000 -> 1K)
    const formatNumber = (num) => {
      if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K'
      }
      return num
    }
    
    // Format stream duration as relative time
    const formatDuration = (timestamp) => {
      if (!timestamp) return 'N/A'
      
      try {
        return formatDistance(new Date(timestamp), new Date(), { addSuffix: false })
      } catch (e) {
        console.error('Error formatting date:', e)
        return 'N/A'
      }
    }
    
    // Toggle a setting value
    const toggleSetting = (settingName) => {
      settings.value[settingName] = !settings.value[settingName]
    }
    
    // Set theme preference with bidirectional syncing
    const setTheme = (isDark) => {
      // Update local theme
      isDarkTheme.value = isDark
      
      // Save to localStorage for persistence
      localStorage.setItem('themePreference', isDark ? 'dark' : 'light')
      
      // Sync with app-level theme if available
      if (updateAppTheme && typeof updateAppTheme === 'function') {
        updateAppTheme(isDark)
      }
    }
    
    // Save settings
    const saveSettings = () => {
      // In a real app, this would save to an API
      toast.success('Settings saved successfully')
    }
    
    // Handle user logout with delay animation for better UX
    const isLoggingOut = ref(false)
    const logout = async () => {
      // Prevent multiple clicks
      if (isLoggingOut.value) return
      
      isLoggingOut.value = true
      toast.info("Logging out in 3 seconds...")
      
      // Animated countdown using animejs timeline
      const timeline = anime.timeline({
        easing: 'easeOutExpo'
      })
      
      // Subtle UI animations during countdown
      timeline.add({
        targets: '.mobile-agent-dashboard',
        opacity: [1, 0.9],
        duration: 3000
      })
      
      // Set a timeout for the actual logout
      setTimeout(async () => {
        try {
          // Call the auth service logout endpoint - don't await to avoid API errors
          AuthService.logout().catch(err => console.warn('Logout API error:', err))
          
          // Notify parent component about logout
          try {
            await axios.post('/api/logout')
            // Redirect to login page
            window.location.href = '/'
          } catch (err) {
            console.warn('Logout endpoint error:', err)
            // Still redirect even if the API call fails
            window.location.href = '/'
          }
        } catch (error) {
          console.error('Logout error in component:', error)
          isLoggingOut.value = false
          
          // Reset opacity if logout fails
          anime({
            targets: '.mobile-agent-dashboard',
            opacity: 1,
            duration: 300
          })
        }
      }, 3000)
    }
    
    // Initialize Socket.IO connection for real-time messaging
    const initializeSocketConnection = () => {
      // Socket connection code remains the same
    }
    
    // Messaging functionality
    const conversations = ref([])
    const isLoadingMessages = ref(false)
    const selectedConversation = ref(null)
    const activeConversationMessages = ref([])
    const isLoadingConversation = ref(false)
    const newMessage = ref('')
    const isSendingMessage = ref(false)
    const messagesContainer = ref(null)
    const messageInput = ref(null)
    const totalUnreadMessageCount = ref(0)
    
    // Load conversations list
    const loadConversations = async () => {
      // Messaging functionality remains the same
    }
    
    // Open a specific conversation
    const openConversation = async (conversation) => {
      // Messaging functionality remains the same
      console.log(conversation);
    }
    
    // Close the current conversation
    const closeConversation = () => {
      // Messaging functionality remains the same
    }
    
    // Send a new message
    const sendMessage = async () => {
      // Messaging functionality remains the same
    }
    
    // Format message time for chat bubbles
    const formatMessageTime = (timestamp) => {
      // Messaging functionality remains the same
      console.log(timestamp);
    }
    
    // Format message time for conversation list (relative time)
    const formatMessageTimeAgo = (timestamp) => {
      // Messaging functionality remains the same
      console.log(timestamp);
    }
    
    // Watch for view mode changes to handle video playback
    watch(viewMode, (newMode, oldMode) => {
      if (newMode === 'grid' && oldMode === 'list') {
        // When switching to grid view, delay slightly to let DOM update
        nextTick(() => {
          // Auto-adjust grid based on screen width
          const container = document.querySelector('.stream-cards-grid')
          if (container) {
            const containerWidth = container.clientWidth
            const columns = Math.max(1, Math.floor(containerWidth / 160))
            container.style.gridTemplateColumns = `repeat(${columns}, 1fr)`
          }
        })
      }
    })
    
    return {
      // Tab management
      tabs,
      activeTab,
      
      // View mode
      viewMode,
      
      // Streams and assignments
      assignments,
      isLoadingAssignments,
      refreshingStreamId,
      currentAgentId,
      stats,
      
      // Settings
      settings,
      showStreamDetailModal,
      selectedStream,
      isDarkTheme,
      
      // Video player refs
      videoPlayer,
      isMuted,
      isRefreshingModal,
      
      // Notifications (from composable)
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      formatNotificationTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle,
      
      // Messaging
      conversations,
      isLoadingMessages,
      selectedConversation,
      activeConversationMessages,
      isLoadingConversation,
      newMessage,
      isSendingMessage,
      messagesContainer,
      messageInput,
      totalUnreadMessageCount,
      
      // Methods
      loadAssignments,
      refreshStream,
      openStreamDetails,
      closeStreamModal,
      toggleMute,
      toggleFullscreen,
      refreshStreamInModal,
      toggleSetting,
      setTheme,
      saveSettings,
      formatNumber,
      formatDuration,
      logout,
      isLoggingOut,
      loadConversations,
      openConversation,
      closeConversation,
      sendMessage,
      formatMessageTime,
      formatMessageTimeAgo
    }
  }
}
</script>

<style scoped>
.mobile-agent-dashboard {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--bg-color);
  color: var(--text-color);
}

/* Page header */
.page-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mobile-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.4rem;
  background-color: var(--accent-color);
  color: white;
  border-radius: 4px;
  margin-left: 0.5rem;
  vertical-align: middle;
}

/* Dashboard tabs */
.dashboard-tabs {
  display: flex;
  background-color: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.tab-item {
  flex: 1;
  min-width: 70px;
  padding: 0.8rem 0;
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-light);
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
}

.tab-item.active {
  color: var(--primary-color);
  border-bottom: 2px solid var(--primary-color);
}

.tab-icon-container {
  position: relative;
  display: inline-block;
  margin-bottom: 0.3rem;
}

.tab-icon {
  font-size: 1.2rem;
  margin-bottom: 0.2rem;
}

.notification-badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: var(--danger-color);
  color: white;
  border-radius: 50%;
  padding: 0.1rem 0.3rem;
  font-size: 0.6rem;
  min-width: 1rem;
  text-align: center;
}

/* Tab content */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.tab-pane {
  animation: fadeIn 0.3s ease;
}

/* Section headers */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

h2 {
  font-size: 1.2rem;
  margin: 0;
}

.refresh-button {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--hover-bg);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

.refresh-button:hover {
  background-color: var(--hover-bg-dark);
}

/* View controls */
.view-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.view-toggle {
  display: flex;}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 0;
}

.empty-state {
  text-align: center;
  padding: 2rem 0;
  color: var(--text-light);
}

.stream-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.stream-card {
  padding: 1rem;
  cursor: pointer;
}

.stream-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.8rem;
}

.stream-card-header h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.stream-platform {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-transform: capitalize;
}

.stream-platform.chaturbate {
  background-color: #f5a623;
  color: white;
}

.stream-platform.stripchat {
  background-color: #7e57c2;
  color: white;
}

.stream-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--text-light);
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.8rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  padding: 1rem;
  text-align: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.3rem;
  color: var(--primary-color);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-light);
}

.performance-chart-container {
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-text {
  color: var(--text-light);
  font-style: italic;
}

.settings-form {
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
}

.toggle-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--border-color);
}

.toggle-option:last-child {
  border-bottom: none;
}

.toggle-switch {
  width: 48px;
  height: 24px;
  border-radius: 12px;
  background-color: var(--border-color);
  position: relative;
  cursor: pointer;
  transition: background-color 0.2s;
}

.toggle-switch.active {
  background-color: var(--primary-color);
}

.toggle-switch-handle {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: white;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.toggle-switch.active .toggle-switch-handle {
  transform: translateX(24px);
}

.theme-options {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  background-color: var(--hover-bg);
  cursor: pointer;
}

.theme-option.selected {
  background-color: var(--primary-color);
  color: white;
}

.save-settings {
  width: 100%;
  margin-top: 1rem;
}

.logout-button {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
}

/* Notification Styles */
.notification-controls {
  display: flex;
  gap: 0.5rem;
}

.notification-filters {
  display: flex;
  justify-content: space-between;
  background-color: var(--hover-bg);
  border-radius: 8px;
  padding: 0.8rem 1rem;
  margin-bottom: 1rem;
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.85rem;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.notification-item {
  display: flex;
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  border-left: 3px solid transparent;
}

.notification-item.unread {
  border-left-color: var(--primary-color);
  background-color: var(--hover-bg);
}

.notification-icon {
  width: 2.5rem;
  height: 2.5rem;
  min-width: 2.5rem;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 600;
  margin-bottom: 0.3rem;
}

.notification-text {
  font-size: 0.85rem;
  color: var(--text-light);
  line-height: 1.4;
  margin-bottom: 0.5rem;
  word-break: break-word;
}

.notification-time {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.notification-status {
  display: flex;
  align-items: center;
}

.unread-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary-color);
}

/* Messages Tab Styles */
.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.conversation-item {
  display: flex;
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  border-left: 3px solid transparent;
}

.conversation-item.unread {
  border-left-color: var(--primary-color);
  background-color: var(--hover-bg);
}

.user-avatar {
  width: 3rem;
  height: 3rem;
  min-width: 3rem;
  border-radius: 50%;
  background-color: var(--secondary-color, #6c757d);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  position: relative;
}

.online-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #28a745;
  border: 2px solid var(--body-bg);
  position: absolute;
  bottom: 0;
  right: 0;
}

.conversation-content {
  flex: 1;
  min-width: 0; /* Prevent text overflow */
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.3rem;
}

.username {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-light);
  white-space: nowrap;
}

.message-preview {
  font-size: 0.85rem;
  color: var(--text-light);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.unread-count {
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  background-color: var(--primary-color);
  color: white;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

/* Individual Conversation View */
.conversation-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 10rem);
  max-height: calc(100vh - 10rem);
}

.conversation-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1rem;
}

.back-button {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-info {
  flex: 1;
}

.user-info h3 {
  margin: 0;
  font-size: 1rem;
}

.online-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-light);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-light);
}

.status-indicator.online {
  background-color: #28a745;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0;
}

.message-bubbles {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message-bubble {
  max-width: 80%;
  padding: 0.8rem 1rem;
  border-radius: 12px;
  position: relative;
}

.message-bubble.outgoing {
  align-self: flex-end;
  background-color: var(--primary-color);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-bubble.incoming {
  align-self: flex-start;
  background-color: var(--input-bg);
  border-bottom-left-radius: 4px;
}

.message-bubble.unread {
  border: 1px solid var(--primary-color);
}

.message-content {
  margin-bottom: 0.5rem;
  word-break: break-word;
  line-height: 1.4;
}

.message-time {
  font-size: 0.7rem;
  text-align: right;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 0.3rem;
}

.message-bubble.outgoing .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.message-bubble.incoming .message-time {
  color: var(--text-light);
}

.read-status {
  font-size: 0.7rem;
}

.read-status.read {
  color: #4FC3F7;
}

.message-input-container {
  display: flex;
  padding: 1rem 0;
  border-top: 1px solid var(--border-color);
  margin-top: auto;
}

.message-input {
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 0.8rem 1rem;
  background-color: var(--input-bg);
  resize: none;
  color: var(--text-color);
  max-height: 100px;
}

.message-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.send-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  border: none;
  margin-left: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.send-button:disabled {
  background-color: var(--text-light);
  cursor: not-allowed;
}

.empty-icon {
  margin-bottom: 1rem;
  color: var(--text-light);
}

/* Message Styles */
.message-list {
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>