<template>
  <div class="agent-app">
    <AgentSidebar 
      :activeTab="currentTab" 
      @tab-change="handleTabChange" 
      :isOnline="isOnline"
      :messageUnreadCount="stats.unreadMessages"
    />
    
    <div class="agent-dashboard" :class="{ 'with-sidebar': !isMobile }">
      <div class="dashboard-header" ref="dashboardHeader">
        <h1>{{ pageTitle }}</h1>
        <div class="status-display">
          <div class="status-badge" :class="{ online: isOnline }">
            {{ isOnline ? 'Online' : 'Offline' }}
          </div>
          <span class="last-refresh">Last updated: {{ formattedLastRefresh }}</span>
          <button @click="refreshDashboard" class="refresh-button" title="Refresh Dashboard">
            <font-awesome-icon :icon="['fas', 'sync']" :class="{ 'rotate': isRefreshing }" />
          </button>
        </div>
      </div>

      <div class="dashboard-content" ref="dashboardContent">
        <div v-if="currentTab === 'dashboard'" class="dashboard-grid" ref="dashboardGrid">
          <!-- Stats Overview -->
          <div class="dashboard-card stats-card" ref="statsCard">
            <div class="card-header">
              <h2>Monitoring Stats</h2>
              <span class="card-period">Last 24 hours</span>
            </div>
            <div class="stats-container">
              <div class="stat-item" v-for="(value, key, index) in stats" :key="key" :ref="el => { if (el) statItems[index] = el }">
                <div class="stat-value">{{ value }}</div>
                <div class="stat-label">{{ formatStatLabel(key) }}</div>
              </div>
            </div>
          </div>

          <!-- Recent Alerts -->
          <div class="dashboard-card alerts-card" ref="alertsCard">
            <div class="card-header">
              <h2>Recent Alerts</h2>
              <span class="view-all" @click="navigateToTab('notifications')">View All</span>
            </div>
            <div v-if="recentAlerts.length > 0">
              <div v-for="(alert, index) in recentAlerts" :key="index" class="alert-item" :ref="el => { if (el) alertItems[index] = el }">
                <div class="alert-icon" :class="alert.level">
                  <font-awesome-icon :icon="getAlertIcon(alert.level)" />
                </div>
                <div class="alert-content">
                  <div class="alert-title">{{ alert.title }}</div>
                  <div class="alert-description">{{ alert.description }}</div>
                  <div class="alert-time">{{ formatTimestamp(alert.timestamp) }}</div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <font-awesome-icon :icon="['fas', 'bell-slash']" class="empty-icon" />
              <div class="empty-message">No recent alerts</div>
            </div>
          </div>

          <!-- Active Streams -->
          <div class="dashboard-card streams-card" ref="streamsCard">
            <div class="card-header">
              <h2>Active Streams</h2>
              <span class="view-all" @click="navigateToTab('streams')">View All</span>
            </div>
            <div v-if="activeStreams.length > 0">
              <div v-for="(stream, index) in activeStreams" :key="index" class="stream-item" :ref="el => { if (el) streamItems[index] = el }">
                <div class="stream-preview">
                  <div class="stream-status-indicator" :class="{ live: stream.isLive }"></div>
                  <div class="stream-thumbnail"></div>
                </div>
                <div class="stream-content">
                  <div class="stream-name">{{ stream.streamer_username || 'Unnamed Stream' }}</div>
                  <div class="stream-location">{{ getPlatformName(stream.type) }}</div>
                  <div class="stream-duration">{{ stream.assigned_agent ? `Agent: ${stream.assigned_agent}` : 'Unassigned' }}</div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <font-awesome-icon :icon="['fas', 'video-slash']" class="empty-icon" />
              <div class="empty-message">No active streams</div>
            </div>
          </div>

          <!-- Keywords Detection -->
          <div class="dashboard-card keywords-card" ref="keywordsCard">
            <div class="card-header">
              <h2>Keywords Detection</h2>
              <span class="card-count">{{ chatKeywords.length }} active</span>
            </div>
            <div class="keywords-container">
              <div v-for="(keyword, index) in chatKeywords" :key="index" class="keyword-item" :ref="el => { if (el) keywordItems[index] = el }">
                <div class="keyword-name">{{ keyword.keyword }}</div>
                <div class="keyword-badge" :class="getPriorityClass(index)">
                  {{ getPriorityLabel(index) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Flagged Objects -->
          <div class="dashboard-card objects-card" ref="objectsCard">
            <div class="card-header">
              <h2>Object Detection</h2>
              <span class="card-count">{{ flaggedObjects.length }} active</span>
            </div>
            <div class="objects-container">
              <div v-for="(object, index) in flaggedObjects" :key="index" class="object-item" :ref="el => { if (el) objectItems[index] = el }">
                <div class="object-icon">
                  <font-awesome-icon :icon="getObjectIcon(object.object_name)" />
                </div>
                <div class="object-name">{{ object.object_name }}</div>
                <div class="object-badge" :class="getRandomConfidence()">
                  {{ getRandomConfidence() }}%
                </div>
              </div>
            </div>
          </div>

          <!-- Telegram Recipients -->
          <div class="dashboard-card telegram-card" ref="telegramCard">
            <div class="card-header">
              <h2>Telegram Recipients</h2>
              <span class="card-count">{{ telegramRecipients.length }} active</span>
            </div>
            <div class="recipients-container">
              <div v-for="(recipient, index) in telegramRecipients" :key="index" class="recipient-item" :ref="el => { if (el) recipientItems[index] = el }">
                <div class="recipient-avatar"></div>
                <div class="recipient-name">{{ recipient.telegram_username }}</div>
                <div class="recipient-status" :class="recipient.active ? 'active' : 'inactive'">
                  {{ recipient.active ? 'active' : 'inactive' }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Other tabs content here -->
        <div v-if="currentTab !== 'dashboard'" class="tab-content">
          <div class="placeholder-content">
            <div class="placeholder-icon">
              <font-awesome-icon :icon="getTabIcon(currentTab)" />
            </div>
            <h2>{{ getTabTitle(currentTab) }}</h2>
            <p>This tab content is under development</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import AgentSidebar from './AgentSidebar.vue'
import anime from 'animejs/lib/anime.es.js'
import axios from 'axios'
import {
  faSync,
  faBellSlash,
  faVideoSlash,
  faExclamationCircle,
  faExclamationTriangle,
  faInfoCircle,
  faCheckCircle,
  faCamera,
  faUser,
  faLock,
  faSkull,
  faExclamation,
  faFlag,
  faFire,
  faTachometerAlt,
  faVideo,
  faClipboardList,
  faBell,
  faComments,
  faBox
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faSync,
  faBellSlash,
  faVideoSlash,
  faExclamationCircle,
  faExclamationTriangle,
  faInfoCircle,
  faCheckCircle,
  faCamera,
  faUser,
  faLock,
  faSkull,
  faExclamation,
  faFlag,
  faFire,
  faTachometerAlt,
  faVideo,
  faClipboardList,
  faBell,
  faComments,
  faBox
)

export default {
  name: 'AgentDashboard',
  components: {
    FontAwesomeIcon,
    AgentSidebar
  },
  props: {
    isOnline: {
      type: Boolean,
      default: true
    }
  },
  setup() {
    // State variables
    const lastRefresh = ref(new Date())
    const isRefreshing = ref(false)
    const currentTab = ref('dashboard')
    const isMobile = ref(window.innerWidth <= 768)
    const refreshInterval = ref(null)
    
    // Data states
    const stats = ref({
      activeStreams: 0,
      flaggedEvents: 0,
      pendingTasks: 0,
      unreadMessages: 0
    })
    
    const recentAlerts = ref([])
    const activeStreams = ref([])
    const chatKeywords = ref([])
    const flaggedObjects = ref([])
    const telegramRecipients = ref([])
    
    // Error handling
    const errors = ref({})
    
    // Refs for animation
    const dashboardHeader = ref(null)
    const dashboardContent = ref(null)
    const dashboardGrid = ref(null)
    const statsCard = ref(null)
    const alertsCard = ref(null)
    const streamsCard = ref(null)
    const keywordsCard = ref(null)
    const objectsCard = ref(null)
    const telegramCard = ref(null)
    const statItems = ref([])
    const alertItems = ref([])
    const streamItems = ref([])
    const keywordItems = ref([])
    const objectItems = ref([])
    const recipientItems = ref([])
    
    // Fetch all the data for dashboard
    const fetchDashboardData = async () => {
      try {
        await Promise.all([
          fetchKeywords(),
          fetchObjects(),
          fetchTelegramRecipients(),
          fetchActiveStreams(),
          fetchRecentLogs()
        ])
        
        // Update stats based on retrieved data
        updateStats()
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      }
    }
    
    // Fetch keywords from API
    const fetchKeywords = async () => {
      try {
        const response = await axios.get('/api/keywords')
        chatKeywords.value = response.data
      } catch (error) {
        console.error('Error fetching keywords:', error)
        errors.value.keywords = 'Failed to fetch keywords'
      }
    }
    
    // Fetch detection objects from API
    const fetchObjects = async () => {
      try {
        const response = await axios.get('/api/objects')
        flaggedObjects.value = response.data
      } catch (error) {
        console.error('Error fetching objects:', error)
        errors.value.objects = 'Failed to fetch flagged objects'
      }
    }
    
    // Fetch telegram recipients from API
    const fetchTelegramRecipients = async () => {
      try {
        const response = await axios.get('/api/telegram_recipients')
        telegramRecipients.value = response.data.map(recipient => ({
          ...recipient,
          active: true // Assuming all recipients in the system are active
        }))
      } catch (error) {
        console.error('Error fetching telegram recipients:', error)
        errors.value.telegram = 'Failed to fetch telegram recipients'
      }
    }
    
    // Fetch active streams
    const fetchActiveStreams = async () => {
      try {
        // This endpoint would need to be created in the backend
        const response = await axios.get('/api/streams/active')
        activeStreams.value = response.data.map(stream => ({
          ...stream,
          isLive: true // Assuming all fetched streams are live
        }))
      } catch (error) {
        console.error('Error fetching active streams:', error)
        errors.value.streams = 'Failed to fetch active streams'
        
        // Fallback - simulate some active streams for display
        activeStreams.value = [
          {
            streamer_username: 'Stream 1',
            type: 'chaturbate',
            isLive: true,
            assigned_agent: 'Agent Smith'
          },
          {
            streamer_username: 'Stream 2',
            type: 'myfreecams',
            isLive: true,
            assigned_agent: 'Agent Johnson'
          }
        ]
      }
    }
    
    // Fetch recent detection logs
    const fetchRecentLogs = async () => {
      try {
        // This endpoint would need to be created in the backend
        const response = await axios.get('/api/logs/recent')
        
        // Transform the logs into alerts format
        recentAlerts.value = response.data.map(log => {
          let level = 'info'
          let title = 'Unknown Event'
          
          if (log.event_type === 'object_detection') {
            level = 'critical'
            title = 'Object Detected'
          } else if (log.event_type === 'audio_detection') {
            level = 'warning'
            title = 'Audio Keyword Detected'
          } else if (log.event_type === 'chat_detection') {
            level = 'warning'
            title = 'Chat Keyword Detected'
          }
          
          return {
            level,
            title,
            description: getLogDescription(log),
            timestamp: log.timestamp || new Date().toISOString()
          }
        })
      } catch (error) {
        console.error('Error fetching recent logs:', error)
        errors.value.logs = 'Failed to fetch recent logs'
        
        // Fallback - create some example alerts
        recentAlerts.value = [
          {
            level: 'critical',
            title: 'Object Detected',
            description: 'Restricted object detected in stream',
            timestamp: new Date().toISOString()
          },
          {
            level: 'warning',
            title: 'Keyword Alert',
            description: 'Flagged keyword detected in chat',
            timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString()
          }
        ]
      }
    }
    
    // Update stats based on fetched data
    const updateStats = () => {
      stats.value = {
        activeStreams: activeStreams.value.length,
        flaggedEvents: recentAlerts.value.length,
        pendingTasks: 0, // This would need to come from a tasks endpoint
        unreadMessages: countUnreadMessages()
      }
    }
    
    // Count unread messages (would need a proper API endpoint)
    const countUnreadMessages = () => {
      // This is a placeholder - in real implementation, fetch from API
      return Math.floor(Math.random() * 10)
    }
    
    // Format log description based on event type
    const getLogDescription = (log) => {
      if (!log || !log.details) return 'No details available'
      
      const details = typeof log.details === 'string' ? JSON.parse(log.details) : log.details
      
      if (log.event_type === 'object_detection' && details.detections) {
        const objects = Array.isArray(details.detections) ? 
          details.detections.map(d => d.name || d.label || 'Unknown').join(', ') : 
          'Unknown object'
        
        return `${objects} detected in ${details.streamer_name || 'stream'}`
      }
      
      if (log.event_type === 'audio_detection' && details.keyword) {
        return `Keyword "${details.keyword}" detected in ${details.streamer_name || 'stream'}`
      }
      
      if (log.event_type === 'chat_detection' && details.detections) {
        const keywords = Array.isArray(details.detections) ? 
          details.detections.map(d => d.keywords?.join(', ') || 'Unknown').join(', ') : 
          'Unknown keywords'
        
        return `Chat keywords (${keywords}) detected in ${details.streamer_name || 'stream'}`
      }
      
      return log.details.message || 'Detection event occurred'
    }
    
    const formattedLastRefresh = computed(() => {
      const now = new Date()
      const diff = now - lastRefresh.value
      
      if (diff < 60000) { // less than a minute
        return 'Just now'
      } else if (diff < 3600000) { // less than an hour
        return `${Math.floor(diff / 60000)} minutes ago`
      } else {
        const hours = lastRefresh.value.getHours().toString().padStart(2, '0')
        const mins = lastRefresh.value.getMinutes().toString().padStart(2, '0')
        return `Today at ${hours}:${mins}`
      }
    })
    
    const getAlertIcon = (level) => {
      switch (level) {
        case 'critical': return ['fas', 'exclamation-circle']
        case 'warning': return ['fas', 'exclamation-triangle']
        case 'info': return ['fas', 'info-circle']
        default: return ['fas', 'check-circle']
      }
    }
    
    const getObjectIcon = (type) => {
      if (type?.toLowerCase().includes('weapon')) return ['fas', 'exclamation']
      if (type?.toLowerCase().includes('mask')) return ['fas', 'user']
      if (type?.toLowerCase().includes('package')) return ['fas', 'box']
      return ['fas', 'flag']
    }
    
    const getTabIcon = (tab) => {
      switch (tab) {
        case 'dashboard': return ['fas', 'tachometer-alt']
        case 'streams': return ['fas', 'video'] 
        case 'tasks': return ['fas', 'clipboard-list']
        case 'messages': return ['fas', 'comments']
        case 'notifications': return ['fas', 'bell']
        default: return ['fas', 'tachometer-alt']
      }
    }
    
    const getTabTitle = (tab) => {
      switch (tab) {
        case 'dashboard': return 'Dashboard'
        case 'streams': return 'Streams'
        case 'tasks': return 'Tasks'
        case 'messages': return 'Messages'
        case 'notifications': return 'Notifications'
        default: return 'Dashboard'
      }
    }
    
    const pageTitle = computed(() => {
      return getTabTitle(currentTab.value)
    })
    
    const formatStatLabel = (key) => {
      // Convert camelCase to Title Case with spaces
      return key
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, function(str) { return str.toUpperCase(); })
    }
    
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'Unknown time'
      
      try {
        const date = new Date(timestamp)
        const now = new Date()
        const diffMs = now - date
        const diffMins = Math.floor(diffMs / 60000)
        
        if (diffMins < 1) return 'Just now'
        if (diffMins < 60) return `${diffMins} minutes ago`
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`
        return `${Math.floor(diffMins / 1440)} days ago`
      } catch (e) {
        return 'Invalid date'
      }
    }
    
    const getPlatformName = (type) => {
      if (!type) return 'Unknown Platform'
      
      const platforms = {
        'chaturbate': 'Chaturbate',
        'myfreecams': 'MyFreeCams',
        'cam4': 'Cam4',
        'bongacams': 'BongaCams',
        'streamate': 'Streamate'
      }
      
      return platforms[type.toLowerCase()] || type
    }
    
    // These methods provide artificial variety in the display
    const getPriorityClass = (index) => {
      const classes = ['high', 'medium', 'low']
      return classes[index % 3]
    }
    
    const getPriorityLabel = (index) => {
      const labels = ['high', 'medium', 'low']
      return labels[index % 3]
    }
    
    const getRandomConfidence = () => {
      const confidences = [95, 88, 75, 82, 91]
      return confidences[Math.floor(Math.random() * confidences.length)]
    }
    
    const refreshDashboard = async () => {
      if (isRefreshing.value) return
      
      isRefreshing.value = true
      
      // Animate the refresh button
      anime({
        targets: '.refresh-button',
        rotate: '360deg',
        duration: 1000,
        easing: 'easeInOutQuad'
      })
      
      try {
        await fetchDashboardData()
        
        // Update refresh time
        lastRefresh.value = new Date()
        
        // Animation for cards to indicate fresh data
        anime({
          targets: [statsCard.value, alertsCard.value, streamsCard.value, keywordsCard.value, objectsCard.value, telegramCard.value],
          boxShadow: [
            '0 2px 8px rgba(0, 0, 0, 0.08)',
            '0 4px 12px rgba(0, 0, 0, 0.15)',
            '0 2px 8px rgba(0, 0, 0, 0.08)'
          ],
          duration: 600,
          easing: 'easeOutQuad'
        })
        
      } catch (error) {
        console.error('Error refreshing dashboard:', error)
      } finally {
        isRefreshing.value = false
      }
    }
    
    const handleTabChange = (tabId) => {
      // First fade out current content
      anime({
        targets: dashboardContent.value,
        opacity: 0,
        translateY: 10,
        duration: 300,
        easing: 'easeInQuad',
        complete: () => {
          currentTab.value = tabId
          
          // Then fade in new content
          nextTick(() => {
            anime({
              targets: dashboardContent.value,
              opacity: 1,
              translateY: [10, 0],
              duration: 500,
              easing: 'easeOutQuad'
            })
            
            // If it's the dashboard tab, animate the cards
            if (tabId === 'dashboard') {
              animateDashboardEntrance()
            }
          })
        }
      })
    }
    
    const navigateToTab = (tabId) => {
      handleTabChange(tabId)
    }
    
    const checkMobile = () => {
      isMobile.value = window.innerWidth <= 768
    }
    
    const animateDashboardEntrance = () => {
      // Animate header
      anime({
        targets: dashboardHeader.value,
        opacity: [0, 1],
        translateY: [-20, 0],
        duration: 800,
        easing: 'easeOutQuad'
      })
      
      // Animate cards with staggered effect
      anime({
        targets: [statsCard.value, alertsCard.value, streamsCard.value, keywordsCard.value, objectsCard.value, telegramCard.value],
        opacity: [0, 1],
        translateY: [20, 0],
        delay: anime.stagger(100),
        duration: 800,
        easing: 'easeOutElastic(1, .6)'
      })
      
      // Animate stat items
      anime({
        targets: statItems.value,
        opacity: [0, 1],
        scale: [0.9, 1],
        delay: anime.stagger(50),
        duration: 1000,
        easing: 'easeOutElastic(1, .6)'
      })
      
      // Animate list items in each card
      const allListItems = [...alertItems.value, ...streamItems.value, ...keywordItems.value, ...objectItems.value, ...recipientItems.value]
      anime({
        targets: allListItems,
        opacity: [0, 1],
        translateX: ['-20px', 0],
        delay: anime.stagger(30, {start: 300}),
        duration: 800,
        easing: 'easeOutQuad'
      })
      
      // Animate stat numbers counting up
      Object.keys(stats.value).forEach((key, index) => {
        anime({
          targets: { value: 0 },
          value: stats.value[key],
          round: 1,
          easing: 'easeInOutQuad',
          duration: 1200,
          delay: 300 + index * 100,
          update: function(anim) {
            const obj = anim.animatables[0].target
            if (statItems.value[index]) {
              statItems.value[index].querySelector('.stat-value').innerHTML = Math.round(obj.value)
            }
          }
        })
      })
      
      // Pulse animation for status indicators
      anime({
        targets: '.stream-status-indicator.live',
        opacity: [0.5, 1],
        scale: [1, 1.2, 1],
        duration: 1500,
        loop: true,
        easing: 'easeInOutQuad'
      })
    }
    
    // Set up auto-refresh interval
    const setupRefreshInterval = () => {
      // Refresh every 60 seconds
      refreshInterval.value = setInterval(() => {
        refreshDashboard()
      }, 60000)
    }
    
    onMounted(() => {
      checkMobile()
      window.addEventListener('resize', checkMobile)
      
      // Initial data fetch
      fetchDashboardData()
      
      // Set up auto-refresh
      setupRefreshInterval()
      
      // Initialize animations
      nextTick(() => {
        animateDashboardEntrance()
      })
    })
    
    onBeforeUnmount(() => {
      window.removeEventListener('resize', checkMobile)
      
      // Clear refresh interval
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
      }
    })
    
    return {
      stats,
      recentAlerts,
      activeStreams,
      chatKeywords,
      flaggedObjects,
      telegramRecipients,
      formattedLastRefresh,
      isRefreshing,
      refreshDashboard,
      getAlertIcon,
      getObjectIcon,
      getTabIcon,
      getTabTitle,
      currentTab,
      handleTabChange,
      navigateToTab,
      isMobile,
      pageTitle,
      formatStatLabel,
      formatTimestamp,
      getPlatformName,
      getPriorityClass,
      getPriorityLabel,
      getRandomConfidence,
      
      // Refs for animation
      dashboardHeader,
      dashboardContent,
      dashboardGrid,
      statsCard,
      alertsCard,
      streamsCard,
      keywordsCard,
      objectsCard,
      telegramCard,
      statItems,
      alertItems,
      streamItems,
      keywordItems,
      objectItems,
      recipientItems
    }
  }
}
</script>

<style scoped>
.agent-app {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-color-light, #f5f7fa);
}

.agent-dashboard {
  flex: 1;
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  transition: all 0.3s ease;
}

.agent-dashboard.with-sidebar {
  margin-left: 72px;
  width: calc(100% - 72px);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dashboard-header h1 {
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
  position: relative;
}

.dashboard-header h1::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 0;
  width: 40px;
  height: 3px;
  background-color: var(--primary-color);
  border-radius: 3px;
}

.status-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  background-color: #8e8e8e;
  color: white;
  display: flex;
  align-items: center;
}

.status-badge.online {
  background-color: #4caf50;
}

.status-badge.online::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: rgba(255, 255, 255, 0.7);
  border-radius: 50%;
  margin-right: 6px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7);
  }
  
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 6px rgba(255, 255, 255, 0);
  }
  
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0);
  }
}

.last-refresh {
  font-size: 0.8rem;
  color: var(--text-color-light);
}

.refresh-button {
  background: none;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.refresh-button:hover {
  background-color: rgba(var(--primary-color-rgb), 0.1);
}

.refresh-button .rotate {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.dashboard-card {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
}

.dashboard-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color-light);
}

.card-header h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-color);
}

.card-period, .card-count {
  font-size: 0.8rem;
  color: var(--text-color-light);
}

.view-all {
  font-size: 0.8rem;
  color: var(--primary-color);
  cursor: pointer;
  font-weight: 500;
}

.view-all:hover {
  text-decoration: underline;
}

/* Stats card */
.stats-card {
  grid-column: span 3;
}

.stats-container {
  display: flex;
  justify-content: space-around;
  padding: 20px;
  gap: 10px;
}

.stat-item {
  text-align: center;
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  background-color: rgba(var(--primary-color-rgb), 0.05);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 8px;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-color-light);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Alerts card */
.alerts-card {
  grid-column: span 2;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color-light);
  transition: background-color 0.2s ease;
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-item:hover {
  background-color: rgba(var(--primary-color-rgb), 0.03);
}

.alert-icon {
  margin-right: 12px;
  font-size: 1.2rem;
}

.alert-icon.critical {
  color: var(--danger-color);
}

.alert-icon.warning {
  color: var(--warning-color);
}

.alert-icon.info {
  color: var(--info-color);
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-color);
}

.alert-description {
  font-size: 0.85rem;
  color: var(--text-color-light);
  margin-bottom: 6px;
}

.alert-time {
  font-size: 0.75rem;
  color: var(--text-color-lighter);
}

/* Streams card */
.streams-card {
  grid-column: span 1;
}

.stream-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color-light);
  transition: background-color 0.2s ease;
}

.stream-item:last-child {
  border-bottom: none;
}

.stream-item:hover {
  background-color: rgba(var(--primary-color-rgb), 0.03);
}

.stream-preview {
  position: relative;
  margin-right: 12px;
}

.stream-status-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #8e8e8e;
  border: 2px solid white;
  z-index: 1;
}

.stream-status-indicator.live {
  background-color: #f44336;
}

.stream-thumbnail {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background-color: var(--bg-color-dark);
  background-image: linear-gradient(45deg, rgba(0, 0, 0, 0.1) 25%, transparent 25%, transparent 50%, rgba(0, 0, 0, 0.1) 50%, rgba(0, 0, 0, 0.1) 75%, transparent 75%, transparent);
  background-size: 8px 8px;
}

.stream-content {
  flex: 1;
}

.stream-name {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 2px;
  color: var(--text-color);
}

.stream-location, .stream-duration {
  font-size: 0.8rem;
  color: var(--text-color-light);
}

/* Keywords card */
.keywords-card {
  grid-column: span 1;
}

.keywords-container {
  padding: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.keyword-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 10px 12px;
  border-radius: 6px;
  background-color: var(--bg-color-light);
  transition: all 0.2s ease;
}

.keyword-item:hover {
  background-color: rgba(var(--primary-color-rgb), 0.05);
}

.keyword-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-color);
}

.keyword-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 12px;
  text-transform: uppercase;
}

.keyword-badge.high {
  background-color: rgba(var(--danger-color-rgb), 0.1);
  color: var(--danger-color);
}

.keyword-badge.medium {
  background-color: rgba(var(--warning-color-rgb), 0.1);
  color: var(--warning-color);
}

.keyword-badge.low {
  background-color: rgba(var(--success-color-rgb), 0.1);
  color: var(--success-color);
}

/* Objects card */
.objects-card {
  grid-column: span 1;
}

.objects-container {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.object-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 6px;
  background-color: var(--bg-color-light);
  transition: all 0.2s ease;
}

.object-item:hover {
  background-color: rgba(var(--primary-color-rgb), 0.05);
}

.object-icon {
  margin-right: 10px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  color: var(--text-color-light);
}

.object-name {
  flex: 1;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-color);
}

.object-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 12px;
}

.object-badge.high {
  background-color: var(--success-color);
  color: white;
}

.object-badge.medium {
  background-color: var(--primary-color);
  color: white;
}

.object-badge.low {
  background-color: var(--text-color-light);
  color: white;
}

/* Telegram card */
.telegram-card {
  grid-column: span 1;
}

.recipients-container {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recipient-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  background-color: var(--bg-color-light);
  transition: all 0.2s ease;
}

.recipient-item:hover {
  background-color: rgba(var(--primary-color-rgb), 0.05);
}

.recipient-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--bg-color-dark);
  margin-right: 12px;
  background-image: linear-gradient(45deg, rgba(0, 0, 0, 0.1) 25%, transparent 25%, transparent 50%, rgba(0, 0, 0, 0.1) 50%, rgba(0, 0, 0, 0.1) 75%, transparent 75%, transparent);
  background-size: 8px 8px;
}

.recipient-name {
  flex: 1;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-color);
}

.recipient-status {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 12px;
  text-transform: uppercase;
}

.recipient-status.active {
  background-color: rgba(var(--success-color-rgb), 0.1);
  color: var(--success-color);
}

.recipient-status.inactive {
  background-color: rgba(var(--text-color-lighter-rgb), 0.1);
  color: var(--text-color-lighter);
}

/* Empty states */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-color-light);
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-message {
  font-size: 0.9rem;
}

/* Tab content placeholder */
.tab-content {
  height: 100%;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.placeholder-icon {
  font-size: 3rem;
  color: var(--primary-color);
  margin-bottom: 24px;
  opacity: 0.7;
}

.placeholder-content h2 {
  font-size: 1.5rem;
  margin-bottom: 16px;
  color: var(--text-color);
}

.placeholder-content p {
  font-size: 1rem;
  color: var(--text-color-light);
}

/* Responsive styles */
@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stats-card {
    grid-column: span 2;
  }
  
  .alerts-card {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .agent-dashboard {
    padding: 16px;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .stats-card, .alerts-card, .streams-card, .keywords-card, .objects-card, .telegram-card {
    grid-column: span 1;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .status-display {
    width: 100%;
    justify-content: space-between;
  }
  
  .stats-container {
    flex-wrap: wrap;
  }
  
  .stat-item {
    min-width: 120px;
    margin-bottom: 10px;
  }
}

/* CSS Variables */
:root {
  --primary-color: #1976d2;
  --primary-color-rgb: 25, 118, 210;
  --danger-color: #f44336;
  --danger-color-rgb: 244, 67, 54;
  --warning-color: #ff9800;
  --warning-color-rgb: 255, 152, 0;
  --success-color: #4caf50;
  --success-color-rgb: 76, 175, 80;
  --info-color: #2196f3;
  --info-color-rgb: 33, 150, 243;
  
  --text-color: #333333;
  --text-color-light: #666666;
  --text-color-lighter: #999999;
  --text-color-lighter-rgb: 153, 153, 153;
  
  --bg-color-light: #f5f7fa;
  --bg-color-dark: #e0e0e0;
  --border-color-light: #eeeeee;
}

</style>