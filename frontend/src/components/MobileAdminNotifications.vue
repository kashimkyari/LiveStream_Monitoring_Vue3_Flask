<template>
  <div class="notifications-tab">
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
                {{ formatTimeAgo(notification.timestamp) }}
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
            <font-awesome-icon 
              :icon="getNotificationIcon(notification)" 
            />
          </div>
          <div class="notification-content">
            <div class="notification-title">
              {{ getNotificationTitle(notification) }}
            </div>
            <div class="notification-time">
              {{ formatTimeAgo(notification.timestamp) }}
            </div>
          </div>
        </div>
      </template>
    </div>
    <div v-else class="loading-container">
      <mobile-loading-spinner :size="40" text="Loading notifications..." />
    </div>
  </div>
</template>

<script>
import { formatDistanceToNow } from 'date-fns'
import MobileLoadingSpinner from './MobileLoadingSpinner.vue'
import axios from 'axios'
import { defineEmits } from 'vue'

export default {
  name: 'MobileAdminNotifications',
  components: {
    MobileLoadingSpinner
  },
  props: {
    notifications: Array,
    notificationsLoading: Boolean,
    unreadCount: Number,
    groupedNotifications: Object,
    isGroupedByType: Boolean,
    isGroupedByStream: Boolean
  },
  setup() {
    // Define emits
    const emit = defineEmits([
      'refresh', 
      'mark-as-read', 
      'mark-all-read', 
      'toggle-group-by-type', 
      'toggle-group-by-stream'
    ])
    
    // Format notification time
    const formatTimeAgo = (timestamp) => {
      if (!timestamp) return ''
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
    }

    // Get notification icon
    const getNotificationIcon = (notification) => {
      switch (notification.event_type) {
        case 'face_detected':
          return 'user-check'
        case 'object_detected':
          return 'cube'
        case 'stream_created':
          return 'video'
        case 'stream_ended':
          return 'video-slash'
        case 'agent_online':
          return 'signal'
        case 'agent_offline':
          return 'signal-slash'
        case 'system_alert':
          return 'exclamation-triangle'
        default:
          return 'bell'
      }
    }

    // Get notification color
    const getNotificationColor = (notification) => {
      switch (notification.event_type) {
        case 'face_detected':
          return '#4361ee' // primary
        case 'object_detected':
          return '#f7931e' // warning
        case 'stream_created':
        case 'stream_ended':
          return '#00c4cc' // info
        case 'agent_online':
          return '#00c853' // success
        case 'agent_offline':
          return '#d50000' // danger
        case 'system_alert':
          return '#ff4081' // pink
        default:
          return '#673ab7' // secondary
      }
    }

    // Get notification title
    const getNotificationTitle = (notification) => {
      switch (notification.event_type) {
        case 'face_detected':
          return `Face detected in ${notification.stream_name}`
        case 'object_detected':
          return `Object detected in ${notification.stream_name}`
        case 'stream_created':
          return `Stream started: ${notification.stream_name}`
        case 'stream_ended':
          return `Stream ended: ${notification.stream_name}`
        case 'agent_online':
          return `Agent online: ${notification.agent_name}`
        case 'agent_offline':
          return `Agent offline: ${notification.agent_name}`
        case 'system_alert':
          return `System Alert: ${notification.title}`
        default:
          return notification.title || notification.event_type
      }
    }

    // Mark notification as read
    const markAsRead = async (notificationId) => {
      try {
        await axios.post(`/api/notifications/${notificationId}/read`)
        emit('refresh')
      } catch (error) {
        console.error('Error marking notification as read:', error)
      }
    }

    // Mark all notifications as read
    const markAllAsRead = async () => {
      try {
        await axios.post('/api/notifications/mark-all-read')
        emit('refresh')
      } catch (error) {
        console.error('Error marking all notifications as read:', error)
      }
    }

    // Toggle grouping by type
    const toggleGroupByType = () => {
      emit('toggle-group-by-type')
    }

    // Toggle grouping by stream
    const toggleGroupByStream = () => {
      emit('toggle-group-by-stream')
    }

    return {
      formatTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream
    }
  }
}
</script>
<style scoped>
.notifications-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tab-header {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fff;
}

.tab-header h2 {
  margin-bottom: 0.5rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.notification-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
}

.notification-filters {
  display: flex;
  gap: 0.5rem;
}

.filter-button {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 0.25rem;
  background: #f5f5f5;
  font-size: 0.875rem;
  cursor: pointer;
}

.filter-button.active {
  background: #4361ee;
  color: white;
  border-color: #4361ee;
}

.filter-icon {
  margin-right: 0.25rem;
}

.mark-all-read {
  padding: 0.5rem;
  border: none;
  border-radius: 0.25rem;
  background: #4361ee;
  color: white;
  font-size: 0.875rem;
  cursor: pointer;
}

.notification-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.empty-message {
  text-align: center;
  padding: 2rem;
  color: #757575;
}

.notification-group {
  margin-bottom: 1rem;
}

.group-header {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  background: #f5f5f5;
  border-radius: 0.25rem;
  margin-bottom: 0.5rem;
}

.group-title {
  flex: 1;
  font-size: 1rem;
  font-weight: 500;
}

.group-count {
  background: #4361ee;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
  font-size: 0.75rem;
}

.notification-card {
  display: flex;
  padding: 0.75rem;
  background: white;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: background-color 0.2s;
}

.notification-card:hover {
  background-color: #f9f9f9;
}

.notification-card.unread {
  background-color: #eef2ff;
}

.notification-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 50%;
  margin-right: 0.75rem;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.notification-time {
  font-size: 0.75rem;
  color: #757575;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}
</style>