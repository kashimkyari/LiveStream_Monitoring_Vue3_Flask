<template>
  <div class="mobile-admin-dashboard" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="mobile-home min-h-screen">
      <!-- Welcome Section -->
      <section class="welcome-section mb-lg">
        <h1 class="text-2xl font-bold text-primary">
          Welcome, {{ user?.username || 'User' }}
        </h1>
        <p class="text-xs text-muted">
          {{ currentTime }}
        </p>
      </section>
      
      <!-- Dashboard Stats Cards -->
      <section class="stats-section mb-lg">
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
      <section class="quick-actions-section mb-lg">
        <h2 class="section-title mb-md">
          Quick Actions
        </h2>
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
      <section class="recent-activity-section mb-lg" v-if="recentActivities.length > 0">
        <h2 class="section-title mb-md">
          Recent Activity
        </h2>
        <div class="activity-list card">
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
              <div class="activity-title">
                {{ activity.title }}
              </div>
              <div class="activity-details">
                {{ activity.details }}
              </div>
              <div class="activity-time">
                {{ formatTimeAgo(activity.timestamp) }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="view-all-link" @click="viewAllActivity">
          View All Activity
          <font-awesome-icon icon="arrow-right" class="ml-xs" />
        </div>
      </section>
      
      <!-- Getting Started Guide - for new users -->
      <section class="card getting-started-section" v-if="isNewUser">
        <div class="card-header">
          <h2 class="section-title">
            Getting Started
          </h2>
        </div>
        <div class="card-body">
          <div class="guide-steps">
            <div 
              v-for="(step, index) in gettingStartedSteps" 
              :key="index"
              class="guide-step"
              :class="{ 'completed': step.completed }"
            >
              <div class="step-number">
                {{ index + 1 }}
              </div>
              <div class="step-content">
                <div class="step-title">
                  {{ step.title }}
                </div>
                <div class="step-description">
                  {{ step.description }}
                </div>
              </div>
              <div class="step-status">
                <font-awesome-icon 
                  v-if="step.completed" 
                  icon="check-circle" 
                  class="completed-icon"
                />
                <button 
                  v-else 
                  class="btn btn-primary btn-sm"
                  @click="completeStep(index)"
                >
                  Do This
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
    
    
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { formatDistanceToNow } from 'date-fns'

export default {
  name: 'MobileAdminHome',
  
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
    },
    currentRoute: {
      type: String,
      default: '/'
    }
  },
  
  emits: ['refresh-data', 'add-stream', 'add-agent', 'navigate'],
  
  setup(props, { emit }) {
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
          return 'default-card'
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
    
    // Using emit for navigation instead of router.push()
    const navigateToSection = (route) => {
      if (route && typeof route === 'string') {
        emit('navigate', route)
      }
    }
    
    // Using emit for navigation instead of router.push()
    const viewAllActivity = () => {
      emit('navigate', '/notifications')
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
/* Base Styles using design system variables */
.mobile-admin-dashboard {
  --primary: #3b82f6;
  --primary-light: #60a5fa;
  --primary-dark: #2563eb;
  --secondary: #10b981; 
  --accent: #8b5cf6;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #06b6d4;
  
  /* Light Theme */
  --background: #f9fafb;
  --card-bg: #ffffff;
  --border: #e5e7eb;
  --text: #1f2937;
  --text-muted: #6b7280;
  --text-light: #9ca3af;
  
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Dark Theme */
.mobile-admin-dashboard[data-theme="dark"] {
  --background: #111827;
  --card-bg: #1f2937;
  --border: #374151;
  --text: #f9fafb;
  --text-muted: #9ca3af;
  --text-light: #6b7280;
}

.mobile-home {
  background-color: var(--background);
  color: var(--text);
  padding: var(--spacing-md);
  padding-bottom: 5rem; /* Space for fixed bottom tabs */
}

/* Typography */
.text-2xl {
  font-size: var(--font-size-2xl);
}

.text-lg {
  font-size: var(--font-size-lg);
}

.text-md {
  font-size: var(--font-size-md);
}

.text-sm {
  font-size: var(--font-size-sm);
}

.text-xs {
  font-size: var(--font-size-xs);
}

.font-bold {
  font-weight: 700;
}

.font-semibold {
  font-weight: 600;
}

.font-medium {
  font-weight: 500;
}

/* Spacing */
.mb-xs {
  margin-bottom: var(--spacing-xs);
}

.mb-sm {
  margin-bottom: var(--spacing-sm);
}

.mb-md {
  margin-bottom: var(--spacing-md);
}

.mb-lg {
  margin-bottom: var(--spacing-lg);
}

.ml-xs {
  margin-left: var(--spacing-xs);
}

/* Colors */
.text-primary {
  color: var(--text);
}

.text-muted {
  color: var(--text-muted);
}

/* Section Styles */
.section-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text);
}

/* Card Component */
.card {
  background-color: var(--card-bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  margin-bottom: var(--spacing-md);
}

.card-header {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border);
}

.card-body {
  padding: var(--spacing-md);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-sm);
}

.stat-card {
  padding: var(--spacing-md);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: transform var(--transition-speed) var(--transition-function),
              box-shadow var(--transition-speed) var(--transition-function);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  font-size: var(--font-size-xl);
  margin-bottom: var(--spacing-sm);
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  margin-bottom: var(--spacing-xs);
}

.stat-label {
  font-size: var(--font-size-xs);
  font-weight: 500;
}

/* Card Type-Specific Styles */
.stream-card {
  background-color: rgba(59, 130, 246, 0.1);
  color: var(--primary);
}

.agent-card {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--secondary);
}

.detection-card {
  background-color: rgba(245, 158, 11, 0.1);
  color: var(--warning);
}

.notification-card {
  background-color: rgba(139, 92, 246, 0.1);
  color: var(--accent);
}

/* Actions Grid */
.actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-sm);
}

.quick-action-button {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: background-color var(--transition-speed) var(--transition-function);
}

.quick-action-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.action-icon {
  color: var(--primary);
  margin-right: var(--spacing-sm);
}

/* Activity List */
.activity-item {
  display: flex;
  align-items: flex-start;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-item.unread {
  background-color: rgba(59, 130, 246, 0.1);
}

.activity-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  background-color: rgba(59, 130, 246, 0.1);
  border-radius: var(--radius-full);
  margin-right: var(--spacing-md);
  color: var(--primary);
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.activity-details {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-bottom: var(--spacing-xs);
}

.activity-time {
  font-size: var(--font-size-xs);
  color: var(--text-light);
}

.view-all-link {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--primary);
  margin-top: var(--spacing-sm);
  cursor: pointer;
}

/* Getting Started Section */
.guide-step {
  display: flex;
  align-items: center;
  padding-bottom: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--border);
}

.guide-step:last-child {
  padding-bottom: 0;
  margin-bottom: 0;
  border-bottom: none;
}

.guide-step.completed {
  opacity: 0.75;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  background-color: rgba(59, 130, 246, 0.1);
  color: var(--primary);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 700;
  margin-right: var(--spacing-md);
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.step-description {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.step-status {
  margin-left: var(--spacing-md);
}

.completed-icon {
  color: var(--success);
  font-size: var(--font-size-lg);
}

/* Button Styles */
.btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: var(--font-size-sm);
  transition: background-color var(--transition-speed) var(--transition-function);
}

.btn-primary {
  background-color: var(--primary);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-dark);
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-xs);
}

/* Mobile Tabs Navigation */
.mobile-tabs {
  display: flex;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: var(--card-bg);
  box-shadow: var(--shadow-lg);
  border-top: 1px solid var(--border);
  height: 4rem;
  z-index: 100;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: var(--spacing-xs) 0;
  color: var(--text-muted);
  transition: color var(--transition-speed) var(--transition-function);
  cursor: pointer;
}

.tab-item.active {
  color: var(--primary);
}

.tab-icon-container {
  margin-bottom: var(--spacing-xs);
  font-size: var(--font-size-lg);
}

.tab-label {
  font-size: var(--font-size-xs);
  font-weight: 500;
}

/* Animation for loading states */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}
</style>