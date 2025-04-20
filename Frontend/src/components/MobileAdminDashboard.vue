<template>
  <div class="mobile-admin-dashboard" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <!-- Header section -->
    <div class="mobile-header">
      <div class="header-title">
        <h1>Admin Dashboard</h1>
        <span class="mobile-tag">Mobile</span>
      </div>
      <div class="header-actions">
        <button class="refresh-button" @click="refreshData" :disabled="refreshing">
          <font-awesome-icon icon="sync" :class="{ 'fa-spin': refreshing }" />
        </button>
      </div>
    </div>

    <!-- Stats section -->
    <div class="stats-container">
      <div class="stat-card" v-for="(stat, index) in displayStats" :key="index">
        <div class="stat-icon">
          <font-awesome-icon :icon="stat.icon" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <!-- Tabs navigation -->
    <div class="mobile-tabs">
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
        <span class="tab-label">{{ tab.label }}</span>
      </div>
    </div>

    <!-- Tab content -->
    <div class="tab-content">
      <!-- Home Tab -->
      <div v-if="activeTab === 0" class="home-tab">
        <MobileHome
          :user="user"
          :stats="{
            streams: dashboardStats.ongoing_streams || 0,
            agents: dashboardStats.active_agents || 0,
            detections: dashboardStats.total_detections || 0,
            notifications: unreadCount || 0
          }"
          :recent-detections="recentDetections"
          :recent-notifications="notifications"
          :is-dark-theme="isDarkTheme"
          @refresh-data="refreshData"
          @add-stream="openAddStreamModal"
          @add-agent="openAddAgentModal"
        />
      </div>
      
      <!-- Streams Tab -->
      <div v-if="activeTab === 1" class="streams-tab">
        <div class="tab-header">
          <h2>Active Streams</h2>
          <div class="filter-actions">
            <select 
              v-model="platformFilter" 
              class="platform-filter"
              @change="applyFilters"
            >
              <option value="">All Platforms</option>
              <option value="chaturbate">Chaturbate</option>
              <option value="stripchat">Stripchat</option>
            </select>
            <div class="search-container">
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="Search streamer..."
                @input="applyFiltersDebounced"
                class="search-input"
              />
              <font-awesome-icon icon="search" class="search-icon" />
            </div>
          </div>
        </div>

        <!-- Stream list -->
        <div class="stream-list" v-if="!loading">
          <p v-if="filteredStreams.length === 0" class="empty-message">
            No streams match your filters
          </p>
          <mobile-stream-card
            v-for="stream in filteredStreams"
            :key="stream.id"
            :stream="stream"
            :is-refreshing="refreshingStreams[stream.id]"
            @click="openStreamDetails(stream)"
            @refresh="refreshStream(stream)"
          />
        </div>
        <div v-else class="loading-container">
          <mobile-loading-spinner :size="40" text="Loading streams..." />
        </div>

        <!-- Add stream button -->
        <div class="floating-action-button" @click="openAddStreamModal">
          <font-awesome-icon icon="plus" />
        </div>
      </div>

      <!-- Agents Tab -->
      <div v-if="activeTab === 2" class="agents-tab">
        <div class="tab-header">
          <h2>Agents</h2>
          <div class="filter-actions">
            <div class="search-container">
              <input 
                type="text" 
                v-model="agentSearchQuery" 
                placeholder="Search agent..."
                @input="filterAgents"
                class="search-input"
              />
              <font-awesome-icon icon="search" class="search-icon" />
            </div>
          </div>
        </div>

        <!-- Agent list -->
        <div class="agent-list" v-if="!loading">
          <p v-if="filteredAgents.length === 0" class="empty-message">
            No agents match your search
          </p>
          <div 
            v-for="agent in filteredAgents" 
            :key="agent.id" 
            class="agent-card"
            @click="openAgentDetails(agent)"
          >
            <div class="agent-status" :class="{ online: agent.online }"></div>
            <div class="agent-info">
              <div class="agent-name">{{ agent.username }}</div>
              <div class="agent-assignment-count">
                {{ agent.assignments ? agent.assignments.length : 0 }} stream(s) assigned
              </div>
            </div>
            <div class="agent-actions">
              <font-awesome-icon icon="chevron-right" />
            </div>
          </div>
        </div>
        <div v-else class="loading-container">
          <mobile-loading-spinner :size="40" text="Loading agents..." />
        </div>

        <!-- Add agent button -->
        <div class="floating-action-button" @click="openAddAgentModal">
          <font-awesome-icon icon="user-plus" />
        </div>
      </div>

      <!-- Detection Tab -->
      <div v-if="activeTab === 3" class="detections-tab">
        <div class="tab-header">
          <h2>Recent Detections</h2>
        </div>

        <!-- Detection list -->
        <div class="detection-list" v-if="!loading">
          <p v-if="recentDetections.length === 0" class="empty-message">
            No recent detections
          </p>
          <div 
            v-for="detection in recentDetections" 
            :key="detection.id" 
            class="detection-card"
          >
            <div class="detection-time">
              {{ formatTimeAgo(detection.timestamp) }}
            </div>
            <div class="detection-content">
              <div class="detection-title">
                {{ formatDetectionTitle(detection) }}
              </div>
              <div class="detection-details">
                {{ formatDetectionDetails(detection) }}
              </div>
              <div class="detection-stream" v-if="detection.room_url">
                {{ getStreamUsername(detection.room_url) }}
              </div>
            </div>
          </div>
        </div>
        <div v-else class="loading-container">
          <mobile-loading-spinner :size="40" text="Loading detections..." />
        </div>
      </div>

      <!-- Notifications Tab -->
      <div v-if="activeTab === 4" class="notifications-tab">
        <div class="tab-header">
          <h2>Notifications</h2>
          <div class="notification-actions">
            <div class="notification-filters">
              <button 
                class="filter-button" 
                :class="{ active: isGroupedByType }"
                @click="toggleGroupByType"
              >
                <font-awesome-icon icon="layer-group" class="filter-icon" />
                Group by Type
              </button>
              <button 
                class="filter-button" 
                :class="{ active: isGroupedByStream }"
                @click="toggleGroupByStream"
              >
                <font-awesome-icon icon="users" class="filter-icon" />
                Group by Stream
              </button>
            </div>
            <button 
              class="mark-all-read" 
              @click="markAllAsRead" 
              v-if="unreadCount > 0"
            >
              Mark All Read
            </button>
          </div>
        </div>

        <!-- Notification list -->
        <div class="notification-list" v-if="!notificationsLoading">
          <p v-if="notifications.length === 0" class="empty-message">
            No notifications
          </p>
          
          <!-- Group view -->
          <template v-if="isGroupedByType || isGroupedByStream">
            <div v-for="(group, groupName) in groupedNotifications" :key="groupName" class="notification-group">
              <div class="group-header">
                <h3 class="group-title">{{ groupName }}</h3>
                <span class="group-count">{{ group.length }}</span>
              </div>
              <div 
                v-for="notification in group" 
                :key="notification.id" 
                class="notification-card"
                :class="{ 'unread': !notification.read }"
                @click="markAsRead(notification.id)"
              >
                <div class="notification-icon" :style="{ color: getNotificationColor(notification) }">
                  <font-awesome-icon :icon="getNotificationIcon(notification)" />
                </div>
                <div class="notification-content">
                  <div class="notification-title">
                    {{ getNotificationTitle(notification) }}
                  </div>
                  <div class="notification-time">
                    {{ formatNotificationTimeAgo(notification.timestamp) }}
                  </div>
                </div>
              </div>
            </div>
          </template>
          
          <!-- Regular list view -->
          <template v-else>
            <div 
              v-for="notification in notifications" 
              :key="notification.id" 
              class="notification-card"
              :class="{ 'unread': !notification.read }"
              @click="markAsRead(notification.id)"
            >
              <div class="notification-icon" :style="{ color: getNotificationColor(notification) }">
                <font-awesome-icon :icon="getNotificationIcon(notification)" />
              </div>
              <div class="notification-content">
                <div class="notification-title">
                  {{ getNotificationTitle(notification) }}
                </div>
                <div class="notification-time">
                  {{ formatNotificationTimeAgo(notification.timestamp) }}
                </div>
              </div>
            </div>
          </template>
        </div>
        <div v-else class="loading-container">
          <mobile-loading-spinner :size="40" text="Loading notifications..." />
        </div>
      </div>

      <!-- Settings Tab -->
      <div v-if="activeTab === 5" class="settings-tab">
        <div class="tab-header">
          <h2>Settings</h2>
        </div>

        <div class="settings-list">
          <div class="settings-section">
            <h3>Display Settings</h3>
            <div class="setting-item">
              <label class="switch">
                <input type="checkbox" v-model="isDarkTheme">
                <span class="slider round"></span>
              </label>
              <span class="setting-label">Dark Mode</span>
            </div>
          </div>

          <div class="settings-section">
            <h3>Data Settings</h3>
            <div class="setting-item">
              <label class="switch">
                <input type="checkbox" v-model="settings.enableBackgroundRefresh">
                <span class="slider round"></span>
              </label>
              <span class="setting-label">Background Refresh</span>
            </div>
            <div class="refresh-interval-setting">
              <span class="setting-label">Refresh Interval</span>
              <select v-model="refreshIntervalMinutes" class="interval-select">
                <option value="1">1 minute</option>
                <option value="5">5 minutes</option>
                <option value="10">10 minutes</option>
                <option value="30">30 minutes</option>
              </select>
            </div>
          </div>

          <div class="settings-section">
            <h3>Notification Settings</h3>
            <div class="setting-item">
              <label class="switch">
                <input type="checkbox" v-model="isGroupedByType">
                <span class="slider round"></span>
              </label>
              <span class="setting-label">Group by Event Type</span>
            </div>
            <div class="setting-item">
              <label class="switch">
                <input type="checkbox" v-model="isGroupedByStream">
                <span class="slider round"></span>
              </label>
              <span class="setting-label">Group by Stream</span>
            </div>
            <div class="setting-item notification-action" @click="markAllAsRead" v-if="unreadCount > 0">
              <font-awesome-icon icon="check-double" class="setting-icon" />
              <span class="setting-label">Mark All as Read ({{ unreadCount }})</span>
            </div>
          </div>

          <div class="settings-section">
            <h3>Account</h3>
            <div class="setting-item" @click="logout">
              <font-awesome-icon icon="sign-out-alt" class="setting-icon" />
              <span class="setting-label">Logout</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stream Details Modal -->
    <mobile-stream-details-modal
      v-if="showStreamDetailsModal"
      :stream="selectedStream"
      :agents="agents"
      @close="showStreamDetailsModal = false"
      @stream-updated="handleStreamUpdated"
      @stream-deleted="handleStreamDeleted"
    />

    <!-- Add Stream Modal -->
    <mobile-add-stream-modal
      v-if="showAddStreamModal"
      @close="showAddStreamModal = false"
      @stream-created="handleStreamCreated"
    />

    <!-- Agent Details Modal -->
    <mobile-agent-details-modal
      v-if="showAgentDetailsModal"
      :agent="selectedAgent"
      @close="showAgentDetailsModal = false"
      @agent-updated="handleAgentUpdated"
      @agent-deleted="handleAgentDeleted"
    />

    <!-- Add Agent Modal -->
    <mobile-add-agent-modal
      v-if="showAddAgentModal"
      @close="showAddAgentModal = false"
      @agent-created="handleAgentCreated"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import axios from 'axios'
import { useMobileDashboardData } from '../composables/useMobileDashboardData'
import { useMobileNotifications } from '../composables/useMobileNotifications'
import MobileStreamCard from './MobileStreamCard.vue'
import MobileLoadingSpinner from './MobileLoadingSpinner.vue'
import MobileStreamDetailsModal from './MobileStreamDetailsModal.vue'
import MobileAddStreamModal from './MobileAddStreamModal.vue'
// Directly using MobileStreamService methods in the code instead of importing
// import MobileStreamService from '../services/MobileStreamService'
import MobileAgentDetailsModal from './MobileAgentDetailsModal.vue'
import MobileAddAgentModal from './MobileAddAgentModal.vue'
import MobileHome from './MobileHome.vue'
import { formatDistanceToNow } from 'date-fns'
import debounce from 'lodash/debounce'

export default {
  name: 'MobileAdminDashboard',

  components: {
    MobileStreamCard,
    MobileLoadingSpinner,
    MobileStreamDetailsModal,
    MobileAddStreamModal,
    MobileAgentDetailsModal,
    MobileAddAgentModal,
    MobileHome
  },

  setup() {
    const router = useRouter()
    const toast = useToast()
    
    // Theme state
    const isDarkTheme = ref(localStorage.getItem('themePreference') === 'dark' || false)
    
    // Get theme update method from App.vue
    const updateAppTheme = inject('updateTheme')
    
    // Notification state
    const { 
      notifications,
      loading: notificationsLoading,
      error: notificationsError,
      unreadCount,
      groupedNotifications,
      isGroupedByType,
      isGroupedByStream,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      formatTimeAgo: formatNotificationTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle
    } = useMobileNotifications()
    
    // Tab navigation
    const activeTab = ref(0)
    const tabs = [
      { label: 'Home', icon: 'home' },
      { label: 'Streams', icon: 'video' },
      { label: 'Agents', icon: 'users' },
      { label: 'Detections', icon: 'eye' },
      { label: 'Notifications', icon: 'bell' },
      { label: 'Settings', icon: 'cog' }
    ]
    
    // Dashboard data
    const {
      loading,
      refreshing,
      user,
      dashboardStats,
      streams,
      allStreams,
      agents,
      detections,
      refreshingStreams,
      fetchDashboardData,
      refreshStream,
      registerUserActivity,
      settings
    } = useMobileDashboardData(router, toast)
    
    // Filters
    const platformFilter = ref('')
    const searchQuery = ref('')
    const agentSearchQuery = ref('')
    
    // Modals
    const showStreamDetailsModal = ref(false)
    const showAddStreamModal = ref(false)
    const showAgentDetailsModal = ref(false)
    const showAddAgentModal = ref(false)
    const selectedStream = ref(null)
    const selectedAgent = ref(null)
    
    // Settings
    const refreshIntervalMinutes = ref(
      Math.round(settings.baseRefreshInterval / (60 * 1000))
    )
    
    // Watch for refresh interval changes
    watch(refreshIntervalMinutes, (newValue) => {
      settings.baseRefreshInterval = parseInt(newValue) * 60 * 1000
    })
    
    // Watch for theme changes in this component and sync with App theme
    watch(isDarkTheme, (newValue) => {
      // Update the app theme using the provided method
      if (updateAppTheme) {
        updateAppTheme(newValue)
      }
    })
    
    // Format stats for display
    const displayStats = computed(() => [
      {
        label: 'Active Streams',
        value: dashboardStats.value.ongoing_streams || 0,
        icon: 'video'
      },
      {
        label: 'Active Agents',
        value: dashboardStats.value.active_agents || 0,
        icon: 'users'
      },
      {
        label: 'Detections',
        value: dashboardStats.value.total_detections || 0,
        icon: 'bell'
      }
    ])
    
    // Filter streams based on platform and search query
    const filteredStreams = computed(() => {
      let result = allStreams.value
      
      if (platformFilter.value) {
        result = result.filter(stream => 
          (stream.type || stream.platform || '').toLowerCase() === platformFilter.value.toLowerCase()
        )
      }
      
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(stream => 
          (stream.streamer_username || '').toLowerCase().includes(query)
        )
      }
      
      return result
    })
    
    // Filter agents based on search query
    const filteredAgents = computed(() => {
      if (!agentSearchQuery.value) return agents.value
      
      const query = agentSearchQuery.value.toLowerCase()
      return agents.value.filter(agent => 
        (agent.username || '').toLowerCase().includes(query)
      )
    })
    
    // Get recent detections across all streams
    const recentDetections = computed(() => {
      const allDetections = []
      
      // Gather all detections
      Object.values(detections.value).forEach(streamDetections => {
        allDetections.push(...streamDetections)
      })
      
      // Sort by timestamp (newest first)
      return allDetections
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 20) // Limit to 20 most recent
    })
    
    // Create debounced filter function
    const applyFiltersDebounced = debounce(() => {
      registerUserActivity()
    }, 300)
    
    // Apply filters immediately
    const applyFilters = () => {
      registerUserActivity()
    }
    
    // Filter agents
    const filterAgents = () => {
      registerUserActivity()
    }
    
    // Refresh dashboard data
    const refreshData = async () => {
      await fetchDashboardData(false)
      toast.success('Dashboard refreshed')
    }
    
    // Format time ago
    const formatTimeAgo = (timestamp) => {
      if (!timestamp) return ''
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
    }
    
    // Format detection title
    const formatDetectionTitle = (detection) => {
      const type = detection.event_type || ''
      
      switch (type.toLowerCase()) {
        case 'face_detected':
          return 'Face Detected'
        case 'object_detected':
          return 'Object Detected'
        case 'stream_created':
          return 'Stream Created'
        case 'stream_ended':
          return 'Stream Ended'
        default:
          return type.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
          ).join(' ')
      }
    }
    
    // Format detection details
    const formatDetectionDetails = (detection) => {
      const details = detection.details || {}
      
      if (typeof details === 'string') {
        return details
      }
      
      if (details.message) {
        return details.message
      }
      
      if (detection.event_type === 'face_detected') {
        return `Confidence: ${(details.confidence * 100).toFixed(1)}%`
      }
      
      if (detection.event_type === 'object_detected') {
        return `${details.name || 'Object'} detected (${(details.confidence * 100).toFixed(1)}%)`
      }
      
      return JSON.stringify(details)
    }
    
    // Extract username from room URL
    const getStreamUsername = (roomUrl) => {
      if (!roomUrl) return ''
      
      try {
        const url = new URL(roomUrl)
        return url.pathname.split('/').filter(Boolean).pop() || ''
      } catch (e) {
        return roomUrl.split('/').filter(Boolean).pop() || ''
      }
    }
    
    // We no longer need toggleTheme as we're using the centralized theme from App.vue
    // isDarkTheme state is kept for consistency with the Settings tab checkbox
    
    // Stream details modal
    const openStreamDetails = (stream) => {
      selectedStream.value = stream
      showStreamDetailsModal.value = true
      registerUserActivity()
    }
    
    // Agent details modal
    const openAgentDetails = (agent) => {
      selectedAgent.value = agent
      showAgentDetailsModal.value = true
      registerUserActivity()
    }
    
    // Add stream modal
    const openAddStreamModal = () => {
      showAddStreamModal.value = true
      registerUserActivity()
    }
    
    // Add agent modal
    const openAddAgentModal = () => {
      showAddAgentModal.value = true
      registerUserActivity()
    }
    
    // Stream updated callback
    const handleStreamUpdated = () => {
      fetchDashboardData(false)
      showStreamDetailsModal.value = false
      toast.success('Stream updated')
    }
    
    // Stream deleted callback
    const handleStreamDeleted = () => {
      fetchDashboardData(false)
      showStreamDetailsModal.value = false
      toast.success('Stream deleted')
    }
    
    // Stream created callback
    const handleStreamCreated = () => {
      fetchDashboardData(false)
      showAddStreamModal.value = false
      toast.success('Stream created')
    }
    
    // Agent updated callback
    const handleAgentUpdated = () => {
      fetchDashboardData(false)
      showAgentDetailsModal.value = false
      toast.success('Agent updated')
    }
    
    // Agent deleted callback
    const handleAgentDeleted = () => {
      fetchDashboardData(false)
      showAgentDetailsModal.value = false
      toast.success('Agent deleted')
    }
    
    // Agent created callback
    const handleAgentCreated = () => {
      fetchDashboardData(false)
      showAddAgentModal.value = false
      toast.success('Agent created')
    }
    
    // Logout
    const logout = async () => {
      try {
        await axios.post('/api/logout')
        toast.info('Logged out successfully')
        router.push('/login')
      } catch (error) {
        console.error('Logout failed:', error)
        toast.error('Logout failed')
      }
    }
    
    // Initial data fetch
    onMounted(async () => {
      await fetchDashboardData()
      
      // Register click event for user activity tracking
      document.addEventListener('click', registerUserActivity)
      document.addEventListener('touchstart', registerUserActivity)
    })
    
    return {
      // State
      isDarkTheme,
      activeTab,
      tabs,
      loading,
      refreshing,
      user,
      dashboardStats,
      streams,
      allStreams,
      agents,
      detections,
      refreshingStreams,
      platformFilter,
      searchQuery,
      agentSearchQuery,
      showStreamDetailsModal,
      showAddStreamModal,
      showAgentDetailsModal,
      showAddAgentModal,
      selectedStream,
      selectedAgent,
      settings,
      refreshIntervalMinutes,
      
      // Notification state
      notifications,
      notificationsLoading,
      notificationsError,
      unreadCount,
      groupedNotifications,
      isGroupedByType,
      isGroupedByStream,
      
      // Computed
      displayStats,
      filteredStreams,
      filteredAgents,
      recentDetections,
      
      // Methods
      fetchDashboardData,
      refreshStream,
      refreshData,
      applyFilters,
      applyFiltersDebounced,
      filterAgents,
      formatTimeAgo,
      formatDetectionTitle,
      formatDetectionDetails,
      getStreamUsername,
      openStreamDetails,
      openAgentDetails,
      openAddStreamModal,
      openAddAgentModal,
      handleStreamUpdated,
      handleStreamDeleted,
      handleStreamCreated,
      handleAgentUpdated,
      handleAgentDeleted,
      handleAgentCreated,
      logout,
      
      // Notification methods
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      formatNotificationTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle
    }
  }
}
</script>

<style scoped>
.mobile-admin-dashboard {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding-bottom: 70px; /* Space for tabs */
  background-color: var(--light-bg);
  color: var(--light-text);
}

[data-theme='dark'] .mobile-admin-dashboard {
  background-color: var(--dark-bg);
  color: var(--dark-text);
}

/* Header */
.mobile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: var(--light-card-bg);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

[data-theme='dark'] .mobile-header {
  background-color: var(--dark-card-bg);
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.header-title {
  display: flex;
  align-items: center;
}

.header-title h1 {
  font-size: 1.3rem;
  margin: 0;
  font-weight: 600;
}

.mobile-tag {
  font-size: 0.7rem;
  background-color: var(--light-primary);
  color: white;
  padding: 2px 6px;
  border-radius: 10px;
  margin-left: 8px;
}

[data-theme='dark'] .mobile-tag {
  background-color: var(--dark-primary);
}

.header-actions {
  display: flex;
  gap: 10px;
}

.refresh-button, .theme-toggle {
  background: none;
  border: none;
  font-size: 1.1rem;
  color: var(--light-text);
  cursor: pointer;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

[data-theme='dark'] .refresh-button, 
[data-theme='dark'] .theme-toggle {
  color: var(--dark-text);
}

.refresh-button:active, .theme-toggle:active {
  background-color: var(--light-hover);
}

[data-theme='dark'] .refresh-button:active, 
[data-theme='dark'] .theme-toggle:active {
  background-color: var(--dark-hover);
}

/* Stats */
.stats-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  padding: 15px;
}

.stat-card {
  background-color: var(--light-card-bg);
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

[data-theme='dark'] .stat-card {
  background-color: var(--dark-card-bg);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.stat-icon {
  font-size: 1.2rem;
  margin-bottom: 8px;
  color: var(--light-primary);
}

[data-theme='dark'] .stat-icon {
  color: var(--dark-primary);
}

.stat-value {
  font-size: 1.4rem;
  font-weight: 600;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .stat-label {
  color: var(--dark-text-secondary);
}

/* Tabs */
.mobile-tabs {
  display: flex;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: var(--light-card-bg);
  border-top: 1px solid var(--light-border);
  z-index: 10;
}

[data-theme='dark'] .mobile-tabs {
  background-color: var(--dark-card-bg);
  border-top-color: var(--dark-border);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 0;
  gap: 4px;
  font-size: 0.7rem;
  color: var(--light-text-secondary);
  cursor: pointer;
}

[data-theme='dark'] .tab-item {
  color: var(--dark-text-secondary);
}

.tab-icon-container {
  position: relative;
}

.tab-icon {
  font-size: 1.1rem;
}

.tab-item.active {
  color: var(--light-primary);
}

[data-theme='dark'] .tab-item.active {
  color: var(--dark-primary);
}

.notification-badge {
  position: absolute;
  top: -6px;
  right: -8px;
  font-size: 0.65rem;
  background-color: var(--light-danger);
  color: white;
  border-radius: 10px;
  padding: 1px 4px;
  min-width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  box-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

[data-theme='dark'] .notification-badge {
  background-color: var(--dark-danger);
}

/* Tab content */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 15px 15px;
}

.tab-header {
  margin: 15px 0;
}

.tab-header h2 {
  font-size: 1.1rem;
  margin: 0 0 10px 0;
}

.filter-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.platform-filter {
  flex: 1;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid var(--light-border);
  background-color: var(--light-card-bg);
  color: var(--light-text);
  min-width: 120px;
}

[data-theme='dark'] .platform-filter {
  border-color: var(--dark-border);
  background-color: var(--dark-card-bg);
  color: var(--dark-text);
}

.search-container {
  position: relative;
  flex: 2;
}

.search-input {
  width: 100%;
  padding: 8px 30px 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--light-border);
  background-color: var(--light-card-bg);
  color: var(--light-text);
}

[data-theme='dark'] .search-input {
  border-color: var(--dark-border);
  background-color: var(--dark-card-bg);
  color: var(--dark-text);
}

.search-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--light-text-secondary);
}

[data-theme='dark'] .search-icon {
  color: var(--dark-text-secondary);
}

/* Stream list */
.stream-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Agent list */
.agent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agent-card {
  display: flex;
  align-items: center;
  padding: 15px;
  background-color: var(--light-card-bg);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

[data-theme='dark'] .agent-card {
  background-color: var(--dark-card-bg);
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.agent-status {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--light-danger);
  margin-right: 15px;
}

[data-theme='dark'] .agent-status {
  background-color: var(--dark-danger);
}

.agent-status.online {
  background-color: var(--light-success);
}

[data-theme='dark'] .agent-status.online {
  background-color: var(--dark-success);
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.agent-assignment-count {
  font-size: 0.8rem;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .agent-assignment-count {
  color: var(--dark-text-secondary);
}

.agent-actions {
  color: var(--light-text-secondary);
}

[data-theme='dark'] .agent-actions {
  color: var(--dark-text-secondary);
}

/* Detection list */
.detection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detection-card {
  padding: 15px;
  background-color: var(--light-card-bg);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

[data-theme='dark'] .detection-card {
  background-color: var(--dark-card-bg);
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.detection-time {
  font-size: 0.75rem;
  color: var(--light-text-secondary);
  margin-bottom: 8px;
}

[data-theme='dark'] .detection-time {
  color: var(--dark-text-secondary);
}

.detection-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.detection-details {
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.detection-stream {
  font-size: 0.8rem;
  color: var(--light-primary);
}

[data-theme='dark'] .detection-stream {
  color: var(--dark-primary);
}

/* Notification styles */
.notification-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 15px;
}

.notification-filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-button {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--light-border);
  background-color: var(--light-card-bg);
  color: var(--light-text);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme='dark'] .filter-button {
  border-color: var(--dark-border);
  background-color: var(--dark-card-bg);
  color: var(--dark-text);
}

.filter-button.active {
  background-color: var(--light-primary-soft);
  border-color: var(--light-primary);
  color: var(--light-primary);
}

[data-theme='dark'] .filter-button.active {
  background-color: var(--dark-primary-soft);
  border-color: var(--dark-primary);
  color: var(--dark-primary);
}

.filter-icon {
  font-size: 0.9rem;
}

.mark-all-read {
  align-self: flex-end;
  padding: 6px 12px;
  border-radius: 6px;
  border: none;
  background-color: var(--light-primary);
  color: white;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme='dark'] .mark-all-read {
  background-color: var(--dark-primary);
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-group {
  margin-bottom: 20px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 0 6px;
}

.group-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .group-title {
  color: var(--dark-text-secondary);
}

.group-count {
  font-size: 0.8rem;
  background-color: var(--light-primary-soft);
  color: var(--light-primary);
  padding: 2px 8px;
  border-radius: 12px;
}

[data-theme='dark'] .group-count {
  background-color: var(--dark-primary-soft);
  color: var(--dark-primary);
}

.notification-card {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background-color: var(--light-card-bg);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme='dark'] .notification-card {
  background-color: var(--dark-card-bg);
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.notification-card.unread {
  border-left: 3px solid var(--light-primary);
  background-color: var(--light-card-bg-hover);
}

[data-theme='dark'] .notification-card.unread {
  border-left: 3px solid var(--dark-primary);
  background-color: var(--dark-card-bg-hover);
}

.notification-icon {
  font-size: 1.2rem;
  margin-right: 12px;
  padding-top: 3px;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-time {
  font-size: 0.75rem;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .notification-time {
  color: var(--dark-text-secondary);
}

/* Settings */
.settings-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-section {
  padding: 15px;
  background-color: var(--light-card-bg);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

[data-theme='dark'] .settings-section {
  background-color: var(--dark-card-bg);
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.settings-section h3 {
  font-size: 1rem;
  margin: 0 0 15px 0;
  color: var(--light-text);
}

[data-theme='dark'] .settings-section h3 {
  color: var(--dark-text);
}

.setting-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.setting-label {
  margin-left: 12px;
}

.setting-icon {
  width: 20px;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .setting-icon {
  color: var(--dark-text-secondary);
}

.notification-action {
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.notification-action:hover {
  background-color: var(--light-hover);
}

[data-theme='dark'] .notification-action:hover {
  background-color: var(--dark-hover);
}

.refresh-interval-setting {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.interval-select {
  padding: 6px;
  border-radius: 6px;
  border: 1px solid var(--light-border);
  background-color: var(--light-card-bg);
  color: var(--light-text);
}

[data-theme='dark'] .interval-select {
  border-color: var(--dark-border);
  background-color: var(--dark-card-bg);
  color: var(--dark-text);
}

/* Toggle switch */
.switch {
  position: relative;
  display: inline-block;
  width: 46px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--light-text-secondary);
  transition: .3s;
}

[data-theme='dark'] .slider {
  background-color: var(--dark-text-secondary);
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .3s;
}

input:checked + .slider {
  background-color: var(--light-primary);
}

[data-theme='dark'] input:checked + .slider {
  background-color: var(--dark-primary);
}

input:checked + .slider:before {
  transform: translateX(22px);
}

.slider.round {
  border-radius: 24px;
}

.slider.round:before {
  border-radius: 50%;
}

/* Loading */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

/* Empty state */
.empty-message {
  text-align: center;
  color: var(--light-text-secondary);
  padding: 30px 0;
}

[data-theme='dark'] .empty-message {
  color: var(--dark-text-secondary);
}

/* Floating action button */
.floating-action-button {
  position: fixed;
  right: 20px;
  bottom: 80px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: var(--light-primary, #4361ee);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2), 0 6px 15px rgba(0,0,0,0.2);
  cursor: pointer;
  z-index: 100;
  transition: all 0.3s ease;
  border: none;
  animation: pulse 2s infinite;
  visibility: visible !important;
  opacity: 1 !important;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(67, 97, 238, 0.4);
  }
  70% {
    box-shadow: 0 0 0 15px rgba(67, 97, 238, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(67, 97, 238, 0);
  }
}

[data-theme='dark'] .floating-action-button {
  background-color: var(--dark-primary, #5e72e4);
}

.floating-action-button:active {
  transform: scale(0.95);
  box-shadow: 0 2px 5px rgba(0,0,0,0.2), 0 3px 8px rgba(0,0,0,0.2);
}

.floating-action-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.25), 0 8px 20px rgba(0,0,0,0.2);
}

/* Home tab styles */
.home-tab {
  padding: 0;
  overflow-y: auto;
  height: 100%;
}

/* Remove the stats section from home tab since it's handled by MobileHome */
.home-tab .stats-container {
  display: none;
}

.tab-content > div {
  padding-bottom: 16px;
}
</style>