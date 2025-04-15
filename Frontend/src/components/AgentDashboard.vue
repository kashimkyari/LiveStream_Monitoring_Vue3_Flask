<template>
  <div class="agent-dashboard">
    <div class="dashboard-header">
      <h1>Agent Dashboard</h1>
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

    <div class="dashboard-content">
      <div class="dashboard-grid">
        <!-- Stats Overview -->
        <div class="dashboard-card stats-card">
          <div class="card-header">
            <h2>Monitoring Stats</h2>
            <span class="card-period">Last 24 hours</span>
          </div>
          <div class="stats-container">
            <div class="stat-item">
              <div class="stat-value">{{ stats.activeStreams }}</div>
              <div class="stat-label">Active Streams</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.flaggedEvents }}</div>
              <div class="stat-label">Flagged Events</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.pendingTasks }}</div>
              <div class="stat-label">Pending Tasks</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ stats.unreadMessages }}</div>
              <div class="stat-label">Unread Messages</div>
            </div>
          </div>
        </div>

        <!-- Recent Alerts -->
        <div class="dashboard-card alerts-card">
          <div class="card-header">
            <h2>Recent Alerts</h2>
            <span class="view-all">View All</span>
          </div>
          <div v-if="recentAlerts.length > 0">
            <div v-for="(alert, index) in recentAlerts" :key="index" class="alert-item">
              <div class="alert-icon" :class="alert.level">
                <font-awesome-icon :icon="getAlertIcon(alert.level)" />
              </div>
              <div class="alert-content">
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-description">{{ alert.description }}</div>
                <div class="alert-time">{{ alert.time }}</div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <font-awesome-icon :icon="['fas', 'bell-slash']" class="empty-icon" />
            <div class="empty-message">No recent alerts</div>
          </div>
        </div>

        <!-- Active Streams -->
        <div class="dashboard-card streams-card">
          <div class="card-header">
            <h2>Active Streams</h2>
            <span class="view-all">View All</span>
          </div>
          <div v-if="activeStreams.length > 0">
            <div v-for="(stream, index) in activeStreams" :key="index" class="stream-item">
              <div class="stream-preview">
                <div class="stream-status-indicator" :class="{ live: stream.isLive }"></div>
                <div class="stream-thumbnail"></div>
              </div>
              <div class="stream-content">
                <div class="stream-name">{{ stream.name }}</div>
                <div class="stream-location">{{ stream.location }}</div>
                <div class="stream-duration">Active for {{ stream.duration }}</div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <font-awesome-icon :icon="['fas', 'video-slash']" class="empty-icon" />
            <div class="empty-message">No active streams</div>
          </div>
        </div>

        <!-- Keywords Detection -->
        <div class="dashboard-card keywords-card">
          <div class="card-header">
            <h2>Keywords Detection</h2>
            <span class="card-count">{{ chatKeywords.length }} active</span>
          </div>
          <div class="keywords-container">
            <div v-for="(keyword, index) in chatKeywords" :key="index" class="keyword-item">
              <div class="keyword-name">{{ keyword.text }}</div>
              <div class="keyword-badge" :class="keyword.priority">
                {{ keyword.priority }}
              </div>
            </div>
          </div>
        </div>

        <!-- Flagged Objects -->
        <div class="dashboard-card objects-card">
          <div class="card-header">
            <h2>Object Detection</h2>
            <span class="card-count">{{ flaggedObjects.length }} active</span>
          </div>
          <div class="objects-container">
            <div v-for="(object, index) in flaggedObjects" :key="index" class="object-item">
              <div class="object-icon">
                <font-awesome-icon :icon="getObjectIcon(object.type)" />
              </div>
              <div class="object-name">{{ object.name }}</div>
              <div class="object-badge" :class="object.confidence">
                {{ object.confidence }}%
              </div>
            </div>
          </div>
        </div>

        <!-- Telegram Recipients -->
        <div class="dashboard-card telegram-card">
          <div class="card-header">
            <h2>Telegram Recipients</h2>
            <span class="card-count">{{ telegramRecipients.length }} active</span>
          </div>
          <div class="recipients-container">
            <div v-for="(recipient, index) in telegramRecipients" :key="index" class="recipient-item">
              <div class="recipient-avatar"></div>
              <div class="recipient-name">{{ recipient.name }}</div>
              <div class="recipient-status" :class="recipient.status">
                {{ recipient.status }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
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
  faFire
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
  faFire
)

export default {
  name: 'AgentDashboard',
  components: {
    FontAwesomeIcon
  },
  props: {
    isOnline: {
      type: Boolean,
      default: true
    }
  },
  setup() {
    const lastRefresh = ref(new Date())
    const isRefreshing = ref(false)
    
    // Sample data - would be fetched from API in real implementation
    const stats = ref({
      activeStreams: 4,
      flaggedEvents: 12,
      pendingTasks: 3,
      unreadMessages: 7
    })
    
    const recentAlerts = ref([
      {
        level: 'critical',
        title: 'Restricted Object Detected',
        description: 'Weapon detected in Stream #4 (Downtown Camera)',
        time: '10 minutes ago'
      },
      {
        level: 'warning',
        title: 'Keyword Alert',
        description: 'High priority keyword "emergency" detected in audio',
        time: '25 minutes ago'
      },
      {
        level: 'info',
        title: 'New Task Assigned',
        description: 'Review footage from South Entrance (12:00-14:00)',
        time: '1 hour ago'
      }
    ])
    
    const activeStreams = ref([
      {
        isLive: true,
        name: 'Downtown Camera',
        location: 'Main Street & 5th Ave',
        duration: '4h 12m'
      },
      {
        isLive: true,
        name: 'South Entrance',
        location: 'Building A',
        duration: '6h 45m'
      },
      {
        isLive: false,
        name: 'Parking Lot East',
        location: 'Parking Structure',
        duration: '2h 30m'
      },
      {
        isLive: true,
        name: 'Plaza Camera',
        location: 'Central Plaza',
        duration: '5h 05m'
      }
    ])
    
    const chatKeywords = ref([
      { text: 'emergency', priority: 'high' },
      { text: 'help', priority: 'medium' },
      { text: 'fire', priority: 'high' },
      { text: 'suspicious', priority: 'medium' },
      { text: 'injured', priority: 'high' },
      { text: 'security', priority: 'low' }
    ])
    
    const flaggedObjects = ref([
      { name: 'Weapon', type: 'weapon', confidence: 95 },
      { name: 'Mask', type: 'mask', confidence: 88 },
      { name: 'Suspicious Package', type: 'package', confidence: 75 }
    ])
    
    const telegramRecipients = ref([
      { name: 'Security Team', status: 'active' },
      { name: 'John Smith', status: 'active' },
      { name: 'Emergency Response', status: 'inactive' }
    ])
    
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
      switch (type) {
        case 'weapon': return ['fas', 'exclamation']
        case 'mask': return ['fas', 'user']
        case 'package': return ['fas', 'box']
        default: return ['fas', 'flag']
      }
    }
    
    const refreshDashboard = async () => {
      if (isRefreshing.value) return
      
      isRefreshing.value = true
      
      try {
        // In a real implementation, these would be actual API calls
        // const statsResponse = await axios.get('/api/agent/stats')
        // stats.value = statsResponse.data
        
        // const alertsResponse = await axios.get('/api/agent/alerts')
        // recentAlerts.value = alertsResponse.data
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // Update refresh time
        lastRefresh.value = new Date()
      } catch (error) {
        console.error('Error refreshing dashboard:', error)
      } finally {
        isRefreshing.value = false
      }
    }
    
    onMounted(() => {
      refreshDashboard()
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
      getObjectIcon
    }
  }
}
</script>

<style scoped>
.agent-dashboard {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
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
}

.status-badge.online {
  background-color: #4caf50;
}

.last-refresh {
  font-size: 0.85rem;
  color: #8e8e8e;
}

.refresh-button {
  background: transparent;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: background-color 0.2s;
}

.refresh-button:hover {
  background-color: var(--hover-bg);
}

.rotate {
  animation: rotating 1s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.dashboard-card {
  background-color: var(--bg-color);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: 1px solid var(--input-border);
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--input-border);
}

.card-header h2 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-color);
}

.card-period, .card-count {
  font-size: 0.85rem;
  color: #8e8e8e;
}

.view-all {
  font-size: 0.85rem;
  color: var(--primary-color);
  cursor: pointer;
}

.view-all:hover {
  text-decoration: underline;
}

/* Stats card specific styles */
.stats-card {
  grid-column: span 3;
}

.stats-container {
  display: flex;
  justify-content: space-between;
  padding: 20px;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
  flex: 1;
  min-width: 120px;
  padding: 16px;
}

.stat-value {
  font-size: 2.4rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 8px;
}

.stat-label {
  font-size: 0.9rem;
  color: #8e8e8e;
}

/* Alerts card specific styles */
.alerts-card {
  grid-column: span 2;
  grid-row: span 2;
}

.alert-item {
  display: flex;
  padding: 16px 20px;
  border-bottom: 1px solid var(--input-border);
}

.alert-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 16px;
  flex-shrink: 0;
}

.alert-icon.critical {
  background-color: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

.alert-icon.warning {
  background-color: rgba(255, 152, 0, 0.1);
  color: #ff9800;
}

.alert-icon.info {
  background-color: rgba(33, 150, 243, 0.1);
  color: #2196f3;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.alert-description {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 8px;
}

.alert-time {
  font-size: 0.8rem;
  color: #8e8e8e;
}

/* Streams card */
.streams-card {
  grid-row: span 2;
}

.stream-item {
  display: flex;
  padding: 12px 20px;
  border-bottom: 1px solid var(--input-border);
}

.stream-preview {
  width: 80px;
  height: 48px;
  background-color: #eee;
  border-radius: 6px;
  margin-right: 16px;
  position: relative;
  flex-shrink: 0;
}

.stream-status-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #8e8e8e;
}

.stream-status-indicator.live {
  background-color: #f44336;
}

.stream-thumbnail {
  width: 100%;
  height: 100%;
  border-radius: 6px;
  background-color: #333;
}

.stream-content {
  flex: 1;
}

.stream-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.stream-location {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 4px;
}

.stream-duration {
  font-size: 0.8rem;
  color: #8e8e8e;
}

/* Keywords card */
.keywords-container, .objects-container, .recipients-container {
  padding: 12px 20px;
}

.keyword-item, .object-item, .recipient-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--input-border);
}

.keyword-item:last-child, .object-item:last-child, .recipient-item:last-child {
  border-bottom: none;
}

.keyword-name, .object-name, .recipient-name {
  flex: 1;
  font-size: 0.9rem;
}

.keyword-badge, .object-badge, .recipient-status {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.keyword-badge.high {
  background-color: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

.keyword-badge.medium {
  background-color: rgba(255, 152, 0, 0.1);
  color: #ff9800;
}

.keyword-badge.low {
  background-color: rgba(33, 150, 243, 0.1);
  color: #2196f3;
}

/* Objects card */
.object-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 12px;
  background-color: rgba(0, 0, 0, 0.05);
  color: #666;
}

.object-badge {
  background-color: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

/* Telegram recipients */
.recipient-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #eee;
  margin-right: 12px;
}

.recipient-status.active {
  background-color: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

.recipient-status.inactive {
  background-color: rgba(158, 158, 158, 0.1);
  color: #9e9e9e;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #8e8e8e;
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-message {
  font-size: 0.9rem;
}

/* Responsive adjustments */
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
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-card, .alerts-card, .streams-card {
    grid-column: 1;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .status-display {
    width: 100%;
    justify-content: space-between;
  }
  
  .stat-item {
    min-width: 100px;
  }
}
</style>