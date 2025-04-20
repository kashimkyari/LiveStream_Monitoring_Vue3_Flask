<template>
  <div class="mobile-home">
    <!-- Welcome Section -->
    <section class="welcome-section">
      <h1 class="welcome-title">Welcome, {{ user?.username || 'User' }}</h1>
      <p class="welcome-subtitle">{{ currentTime }}</p>
    </section>
    
    <!-- Dashboard Stats Cards -->
    <section class="stats-section">
      <div class="stats-grid">
        <div 
          v-for="(stat, index) in displayStats" 
          :key="index" 
          class="stat-card"
          :class="[getCardClass(stat.type)]"
          @click="navigateToSection(stat.route)"
        >
          <div class="stat-icon">
            <font-awesome-icon :icon="stat.icon" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>
    
    <!-- Quick Actions -->
    <section class="quick-actions-section">
      <h2 class="section-title">Quick Actions</h2>
      <div class="actions-grid">
        <button 
          v-for="(action, index) in quickActions" 
          :key="index"
          class="quick-action-button"
          @click="handleQuickAction(action.action)"
        >
          <font-awesome-icon :icon="action.icon" class="action-icon" />
          <span>{{ action.label }}</span>
        </button>
      </div>
    </section>
    
    <!-- Recent Activity -->
    <section class="recent-activity-section" v-if="recentActivities.length > 0">
      <h2 class="section-title">Recent Activity</h2>
      <div class="activity-list">
        <div 
          v-for="(activity, index) in recentActivities" 
          :key="index"
          class="activity-item"
          :class="{ 'unread': !activity.read }"
        >
          <div class="activity-icon">
            <font-awesome-icon :icon="activity.icon" />
          </div>
          <div class="activity-content">
            <div class="activity-title">{{ activity.title }}</div>
            <div class="activity-details">{{ activity.details }}</div>
            <div class="activity-time">{{ formatTimeAgo(activity.timestamp) }}</div>
          </div>
        </div>
      </div>
      
      <div class="view-all-link" @click="viewAllActivity">
        View All Activity
        <font-awesome-icon icon="arrow-right" />
      </div>
    </section>
    
    <!-- Getting Started Guide - for new users -->
    <section class="getting-started-section" v-if="isNewUser">
      <h2 class="section-title">Getting Started</h2>
      <div class="guide-steps">
        <div 
          v-for="(step, index) in gettingStartedSteps" 
          :key="index"
          class="guide-step"
          :class="{ 'completed': step.completed }"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-content">
            <div class="step-title">{{ step.title }}</div>
            <div class="step-description">{{ step.description }}</div>
          </div>
          <div class="step-status">
            <font-awesome-icon v-if="step.completed" icon="check-circle" class="completed-icon" />
            <button v-else class="do-this-button" @click="completeStep(index)">
              Do This
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { useRouter } from 'vue-router'

export default {
  name: 'MobileHome',
  
  props: {
    user: {
      type: Object,
      default: () => ({})
    },
    stats: {
      type: Object,
      default: () => ({
        streams: 0,
        agents: 0,
        detections: 0,
        notifications: 0
      })
    },
    recentDetections: {
      type: Array,
      default: () => []
    },
    recentNotifications: {
      type: Array,
      default: () => []
    },
    isDarkTheme: {
      type: Boolean,
      default: true
    }
  },
  
  emits: ['refresh-data', 'add-stream', 'add-agent'],
  
  setup(props, { emit }) {
    const router = useRouter()
    const isNewUser = ref(false)
    
    // Check if user is new (based on join date or completed steps)
    onMounted(() => {
      if (props.user?.created_at) {
        // If user account was created less than 7 days ago, show getting started guide
        const joinDate = new Date(props.user.created_at)
        const daysSinceJoin = Math.floor((Date.now() - joinDate) / (1000 * 60 * 60 * 24))
        isNewUser.value = daysSinceJoin < 7
      }
      
      // Check for completed steps in localStorage
      const completedSteps = JSON.parse(localStorage.getItem('gettingStartedSteps') || '[]')
      
      // Update steps with completed status
      gettingStartedSteps.value = gettingStartedSteps.value.map((step, index) => {
        return {
          ...step,
          completed: completedSteps.includes(index)
        }
      })
      
      // If all steps are completed, don't show the guide even for new users
      if (gettingStartedSteps.value.every(step => step.completed)) {
        isNewUser.value = false
      }
    })
    
    const currentTime = computed(() => {
      const now = new Date()
      const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric'
      }
      return now.toLocaleDateString(undefined, options)
    })
    
    const displayStats = computed(() => [
      {
        label: 'Active Streams',
        value: props.stats.streams || 0,
        icon: 'video',
        type: 'stream',
        route: '/streams'
      },
      {
        label: 'Active Agents',
        value: props.stats.agents || 0,
        icon: 'users',
        type: 'agent',
        route: '/agents'
      },
      {
        label: 'Detections',
        value: props.stats.detections || 0,
        icon: 'eye',
        type: 'detection',
        route: '/detections'
      },
      {
        label: 'Notifications',
        value: props.stats.notifications || 0,
        icon: 'bell',
        type: 'notification',
        route: '/notifications'
      }
    ])
    
    const quickActions = ref([
      {
        label: 'Add Stream',
        icon: 'plus-circle',
        action: 'add-stream'
      },
      {
        label: 'Add Agent',
        icon: 'user-plus',
        action: 'add-agent'
      },
      {
        label: 'Refresh Data',
        icon: 'sync',
        action: 'refresh-data'
      },
      {
        label: 'Settings',
        icon: 'cog',
        action: 'navigate-settings'
      }
    ])
    
    // Combine recent detections and notifications for activity feed
    const recentActivities = computed(() => {
      // Process detections
      const detectionActivities = (props.recentDetections || []).map(detection => {
        return {
          id: detection.id,
          type: 'detection',
          title: getDetectionTitle(detection),
          details: getDetectionDetails(detection),
          timestamp: detection.timestamp,
          icon: getDetectionIcon(detection),
          read: detection.read || false,
          original: detection
        }
      })
      
      // Process notifications
      const notificationActivities = (props.recentNotifications || []).map(notification => {
        return {
          id: notification.id,
          type: 'notification',
          title: notification.title || 'Notification',
          details: notification.message || '',
          timestamp: notification.timestamp,
          icon: 'bell',
          read: notification.read || false,
          original: notification
        }
      })
      
      // Combine and sort by timestamp (newest first)
      return [...detectionActivities, ...notificationActivities]
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 5) // Limit to 5 most recent
    })
    
    const gettingStartedSteps = ref([
      {
        title: 'Monitor Your First Stream',
        description: 'Add a stream to begin monitoring for detections.',
        completed: false,
        action: 'add-stream'
      },
      {
        title: 'Configure Detection Parameters',
        description: 'Set up keywords and objects you want to detect.',
        completed: false,
        action: 'navigate-settings'
      },
      {
        title: 'Assign Agents',
        description: 'Add and assign agents to monitor streams.',
        completed: false,
        action: 'add-agent'
      },
      {
        title: 'Set Up Notifications',
        description: 'Configure how you want to be notified of detections.',
        completed: false,
        action: 'navigate-notifications'
      }
    ])
    
    // Helper methods
    const getDetectionTitle = (detection) => {
      const type = detection.event_type || ''
      
      switch (type.toLowerCase()) {
        case 'face_detected':
          return 'Face Detected'
        case 'object_detected':
          return 'Object Detected'
        case 'keyword_detected':
          return 'Keyword Detected'
        case 'stream_created':
          return 'Stream Started'
        case 'stream_ended':
          return 'Stream Ended'
        default:
          return type.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
          ).join(' ')
      }
    }
    
    const getDetectionDetails = (detection) => {
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
      
      if (detection.event_type === 'keyword_detected') {
        return `"${details.keyword || 'Keyword'}" found in chat`
      }
      
      return JSON.stringify(details)
    }
    
    const getDetectionIcon = (detection) => {
      const type = (detection.event_type || '').toLowerCase()
      
      if (type.includes('face')) return 'user'
      if (type.includes('object')) return 'cube'
      if (type.includes('keyword')) return 'comment'
      if (type.includes('created') || type.includes('started')) return 'play-circle'
      if (type.includes('ended')) return 'stop-circle'
      
      return 'bell'
    }
    
    const formatTimeAgo = (timestamp) => {
      if (!timestamp) return ''
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
    }
    
    const getCardClass = (type) => {
      switch (type) {
        case 'stream':
          return 'stream-card'
        case 'agent':
          return 'agent-card'
        case 'detection':
          return 'detection-card'
        case 'notification':
          return 'notification-card'
        default:
          return ''
      }
    }
    
    // Action handlers
    const handleQuickAction = (action) => {
      switch (action) {
        case 'add-stream':
          emit('add-stream')
          break
        case 'add-agent':
          emit('add-agent')
          break
        case 'refresh-data':
          emit('refresh-data')
          break
        case 'navigate-settings':
          navigateToSection('/settings')
          break
        default:
          console.log('Unhandled action:', action)
      }
    }
    
    const navigateToSection = (route) => {
      if (route.startsWith('/')) {
        router.push(route)
      }
    }
    
    const viewAllActivity = () => {
      router.push('/notifications')
    }
    
    const completeStep = (index) => {
      // Mark step as completed
      gettingStartedSteps.value[index].completed = true
      
      // Store completed steps in localStorage
      const completedSteps = gettingStartedSteps.value
        .map((step, i) => step.completed ? i : null)
        .filter(i => i !== null)
      
      localStorage.setItem('gettingStartedSteps', JSON.stringify(completedSteps))
      
      // Perform the associated action
      const action = gettingStartedSteps.value[index].action
      if (action) {
        handleQuickAction(action)
      }
    }
    
    return {
      currentTime,
      displayStats,
      quickActions,
      recentActivities,
      isNewUser,
      gettingStartedSteps,
      formatTimeAgo,
      getCardClass,
      handleQuickAction,
      navigateToSection,
      viewAllActivity,
      completeStep
    }
  }
}
</script>

<style scoped>
.mobile-home {
  padding: 16px;
  max-width: 100%;
}

/* Welcome Section */
.welcome-section {
  margin-bottom: 20px;
}

.welcome-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.welcome-subtitle {
  color: var(--bs-secondary);
  font-size: 0.875rem;
}

/* Stats Section */
.stats-section {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-card {
  background-color: var(--bs-card-bg);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:active {
  transform: scale(0.98);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 1.25rem;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--bs-secondary);
}

/* Card color variants */
.stream-card .stat-icon {
  background-color: rgba(66, 153, 225, 0.1);
  color: var(--bs-info);
}

.agent-card .stat-icon {
  background-color: rgba(72, 187, 120, 0.1);
  color: var(--bs-success);
}

.detection-card .stat-icon {
  background-color: rgba(237, 137, 54, 0.1);
  color: var(--bs-warning);
}

.notification-card .stat-icon {
  background-color: rgba(237, 100, 166, 0.1);
  color: var(--bs-danger);
}

/* Quick Actions Section */
.quick-actions-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-action-button {
  background-color: var(--bs-card-bg);
  border: none;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.quick-action-button:active {
  background-color: var(--bs-secondary-bg);
}

.action-icon {
  font-size: 1.5rem;
  margin-bottom: 8px;
  color: var(--bs-primary);
}

/* Recent Activity Section */
.recent-activity-section {
  margin-bottom: 24px;
}

.activity-list {
  background-color: var(--bs-card-bg);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.activity-item {
  padding: 16px;
  display: flex;
  align-items: flex-start;
  border-bottom: 1px solid var(--bs-border-color);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-item.unread {
  border-left: 3px solid var(--bs-primary);
  background-color: var(--bs-primary-bg-subtle);
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--bs-primary-bg-subtle);
  color: var(--bs-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-title {
  font-weight: 600;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-details {
  font-size: 0.875rem;
  color: var(--bs-secondary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-time {
  font-size: 0.75rem;
  color: var(--bs-secondary);
}

.view-all-link {
  text-align: center;
  padding: 12px;
  color: var(--bs-primary);
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* Getting Started Section */
.getting-started-section {
  margin-bottom: 24px;
}

.guide-steps {
  background-color: var(--bs-card-bg);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.guide-step {
  padding: 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--bs-border-color);
}

.guide-step:last-child {
  border-bottom: none;
}

.guide-step.completed {
  background-color: var(--bs-success-bg-subtle);
}

.step-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: var(--bs-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: 16px;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.step-description {
  font-size: 0.875rem;
  color: var(--bs-secondary);
}

.step-status {
  margin-left: 16px;
  flex-shrink: 0;
}

.completed-icon {
  color: var(--bs-success);
  font-size: 1.25rem;
}

.do-this-button {
  background-color: var(--bs-primary);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Dark theme adjustments */
:deep([data-bs-theme="dark"]) .stat-card,
:deep([data-bs-theme="dark"]) .quick-action-button,
:deep([data-bs-theme="dark"]) .activity-list,
:deep([data-bs-theme="dark"]) .guide-steps {
  background-color: var(--bs-dark-bg-subtle);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

:deep([data-bs-theme="dark"]) .activity-item,
:deep([data-bs-theme="dark"]) .guide-step {
  border-color: var(--bs-dark-border-subtle);
}

:deep([data-bs-theme="dark"]) .quick-action-button:active {
  background-color: var(--bs-tertiary-bg);
}

/* Responsive adjustments */
@media (max-width: 360px) {
  .stats-grid,
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>