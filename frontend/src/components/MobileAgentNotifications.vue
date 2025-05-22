<template>
  <div class="mobile-agent-notifications" :data-theme="theme">
    <div class="section-header">
      <h2>Notifications</h2>
      <div class="notification-controls">
        <button v-if="unreadCount > 0" class="btn btn-mark-all" @click="markAllAsRead">
          <font-awesome-icon icon="check-double" />
          Mark All Read
        </button>
      </div>
    </div>

    <div class="notification-filters">
      <div class="filter-toggle">
        <span>Group by Type</span>
        <div class="toggle-switch" :class="{ active: groupByType }" @click="toggleGroupByType">
          <div class="toggle-switch-handle"></div>
        </div>
      </div>
      <div class="filter-toggle">
        <span>Group by Stream</span>
        <div class="toggle-switch" :class="{ active: groupByStream }" @click="toggleGroupByStream">
          <div class="toggle-switch-handle"></div>
        </div>
      </div>
    </div>

    <div v-if="notificationsLoading" class="loading">
      Loading notifications...
    </div>
    <div v-else-if="notifications.length === 0" class="empty-state">
      <font-awesome-icon icon="bell-slash" class="empty-icon" />
      <p>No notifications to display</p>
    </div>
    <div v-else class="notification-list">
      <template v-if="groupByType || groupByStream">
        <div v-for="(group, key) in groupedNotifications" :key="key" class="notification-group">
          <h3>
            {{
              groupByType
                ? key.replace('_', ' ').toUpperCase()
                : group[0].streamer || 'Unknown Streamer'
            }}
          </h3>
          <div v-for="notification in group" :key="notification.id" class="notification-item"
            :class="{ unread: !notification.read }" @click="openModal(notification)">
            <div class="notification-icon" :style="{ backgroundColor: getNotificationColor(notification.event_type) }">
              <font-awesome-icon :icon="getNotificationIcon(notification.event_type)" />
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ getNotificationTitle(notification) }}</div>
              <div class="notification-text">{{ notification.details.message || notification.details.transcript ||
                notification.details.detections?.[0]?.message || 'No details available' }}</div>
              <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
            </div>
            <div class="notification-status">
              <div v-if="!notification.read" class="unread-indicator"></div>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <div v-for="notification in notifications" :key="notification.id" class="notification-item"
          :class="{ unread: !notification.read }" @click="openModal(notification)">
          <div class="notification-icon" :style="{ backgroundColor: getNotificationColor(notification.event_type) }">
            <font-awesome-icon :icon="getNotificationIcon(notification.event_type)" />
          </div>
          <div class="notification-content">
            <div class="notification-title">{{ getNotificationTitle(notification) }}</div>
            <div class="notification-text">{{ notification.details.message || notification.details.transcript ||
              notification.details.detections?.[0]?.message || 'No details available' }}</div>
            <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
          </div>
          <div class="notification-status">
            <div v-if="!notification.read" class="unread-indicator"></div>
          </div>
        </div>
      </template>
    </div>

    <!-- Modal for Notification Details -->
    <div v-if="selectedNotification" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>{{ selectedNotification.event_type.replace('_', ' ') }}</h3>
          <button class="close-btn" @click="closeModal">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <div class="modal-body">
          <p><strong>ID:</strong> {{ selectedNotification.id }}</p>
          <p><strong>Streamer:</strong> {{ selectedNotification.streamer || 'Unknown' }}</p>
          <p><strong>Timestamp:</strong> {{ formatTime(selectedNotification.timestamp) }}</p>
          <p><strong>Status:</strong> {{ selectedNotification.read ? 'Read' : 'Unread' }}</p>
          <p v-if="selectedNotification.event_type === 'object_detection'">
            <strong>Detected Objects:</strong>
            {{ formatObjects(selectedNotification.details.detections) }}
          </p>
          <p v-if="selectedNotification.event_type === 'audio_detection'">
            <strong>Keyword:</strong> {{ selectedNotification.details.keyword || 'N/A' }}<br />
            <strong>Transcript:</strong> {{ selectedNotification.details.transcript || 'N/A' }}
          </p>
          <p
            v-if="selectedNotification.event_type === 'chat_detection' || selectedNotification.event_type === 'chat_sentiment_detection'">
            <strong>Sender:</strong> {{ selectedNotification.details.detections?.[0]?.sender || 'Unknown' }}<br />
            <strong>Message:</strong> {{ selectedNotification.details.detections?.[0]?.message || 'N/A' }}
          </p>
        </div>
        <div class="modal-footer">
          <button v-if="!selectedNotification.read" class="mark-read-btn" @click="markAsRead(selectedNotification.id)">
            Mark as Read
          </button>
          <button class="close-btn" @click="closeModal">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'
import { io } from 'socket.io-client'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faCheckDouble, faBellSlash, faEye, faMicrophone, faComment, faBell, faTimes } from '@fortawesome/free-solid-svg-icons'
import { library } from '@fortawesome/fontawesome-svg-core'

library.add(faCheckDouble, faBellSlash, faEye, faMicrophone, faComment, faBell, faTimes)

export default {
  name: 'MobileAgentNotifications',
  components: {
    FontAwesomeIcon
  },
  props: {
    isDarkTheme: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'mark-read',
    'mark-all-read',
    'toggle-group-type',
    'toggle-group-stream'
  ],
  setup(props, { emit }) {
    const toast = useToast()
    const notifications = ref([])
    const notificationsLoading = ref(false)
    const unreadCount = ref(0)
    const groupByType = ref(false)
    const groupByStream = ref(false)
    const selectedNotification = ref(null)
    let socket = null

    // Determine theme based on prop or system preference
    const theme = computed(() => {
      if (props.isDarkTheme) return 'dark'
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    })

    // Listen for system theme changes
    const updateSystemTheme = () => {
      if (!props.isDarkTheme) {
        const isSystemDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        theme.value = isSystemDark ? 'dark' : 'light'
      }
    }

    // Computed property for grouped notifications
    const groupedNotifications = computed(() => {
      if (!groupByType.value && !groupByStream.value) return {}
      const grouped = {}
      notifications.value.forEach((notification) => {
        const key = groupByType.value
          ? notification.event_type
          : notification.streamer || 'Unknown'
        if (!grouped[key]) grouped[key] = []
        grouped[key].push(notification)
      })
      return grouped
    })

    // Format timestamp
    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }

    // Format object detections
    const formatObjects = (detections) => {
      if (!detections || !Array.isArray(detections)) return 'None'
      return detections
        .map((d) => `${d.class} (${(d.confidence * 100).toFixed(1)}%)`)
        .join(', ')
    }

    // Get notification icon
    const getNotificationIcon = (type) => {
      switch (type) {
        case 'object_detection':
          return 'eye'
        case 'audio_detection':
          return 'microphone'
        case 'chat_detection':
        case 'chat_sentiment_detection':
          return 'comment'
        default:
          return 'bell'
      }
    }

    // Get notification color
    const getNotificationColor = (type) => {
      switch (type) {
        case 'object_detection':
          return '#f5a623'
        case 'audio_detection':
          return '#28a745'
        case 'chat_detection':
        case 'chat_sentiment_detection':
          return '#7e57c2'
        default:
          return '#6c757d'
      }
    }

    // Get notification title
    const getNotificationTitle = (notification) => {
      return `${notification.event_type.replace('_', ' ').toUpperCase()} - ${notification.streamer || 'Unknown'}`
    }

    // Open modal with notification details
    const openModal = (notification) => {
      selectedNotification.value = notification
    }

    // Close modal
    const closeModal = () => {
      selectedNotification.value = null
    }

    // Fetch notifications
    const fetchNotifications = async () => {
      notificationsLoading.value = true
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/notifications', {
          headers: { Authorization: `Bearer ${token}` }
        })
        notifications.value = response.data
        unreadCount.value = notifications.value.filter(n => !n.read).length
      } catch (error) {
        console.error('Error fetching notifications:', error)
        toast.error(error.response?.data?.message || 'Failed to load notifications')
        if (error.response?.status === 401) {
          localStorage.removeItem('token')
          window.location.href = '/'
        }
      } finally {
        notificationsLoading.value = false
      }
    }

    // Mark a single notification as read
    const markAsRead = async (notificationId) => {
      try {
        const token = localStorage.getItem('token')
        await axios.put(`/api/notifications/${notificationId}/read`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
        const notification = notifications.value.find(n => n.id === notificationId)
        if (notification) {
          notification.read = true
          unreadCount.value = notifications.value.filter(n => !n.read).length
          emit('mark-read', notificationId)
        }
        if (selectedNotification.value && selectedNotification.value.id === notificationId) {
          selectedNotification.value.read = true
        }
        toast.success('Notification marked as read')
      } catch (error) {
        console.error('Error marking notification as read:', error)
        toast.error(error.response?.data?.message || 'Failed to mark as read')
      }
    }

    // Mark all notifications as read
    const markAllAsRead = async () => {
      try {
        const token = localStorage.getItem('token')
        await axios.put('/api/notifications/read-all', {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
        notifications.value.forEach(n => { n.read = true })
        unreadCount.value = 0
        if (selectedNotification.value) {
          selectedNotification.value.read = true
        }
        emit('mark-all-read')
        toast.success('All notifications marked as read')
      } catch (error) {
        console.error('Error marking all notifications as read:', error)
        toast.error(error.response?.data?.message || 'Failed to mark all as read')
      }
    }

    // Toggle group by type
    const toggleGroupByType = () => {
      groupByType.value = !groupByType.value
      emit('toggle-group-type')
    }

    // Toggle group by stream
    const toggleGroupByStream = () => {
      groupByStream.value = !groupByStream.value
      emit('toggle-group-stream')
    }

    // Initialize Socket.IO
    const initializeSocket = () => {
      socket = io('https://monitor-backend.jetcamstudio.com:5000/notifications', {
        path: '/ws',
        transports: ['websocket'],
        query: { token: localStorage.getItem('token') }
      })

      socket.on('connect', () => {
        console.log('Connected to Socket.IO notifications namespace')
      })

      socket.on('notification', (data) => {
        notifications.value.unshift(data)
        if (!data.read) unreadCount.value += 1
        toast.info(`New ${data.event_type.replace('_', ' ')} notification`)
      })

      socket.on('notification_update', (data) => {
        if (data.type === 'read') {
          const notification = notifications.value.find(n => n.id === data.id)
          if (notification) {
            notification.read = true
            unreadCount.value = notifications.value.filter(n => !n.read).length
          }
          if (selectedNotification.value && selectedNotification.value.id === data.id) {
            selectedNotification.value.read = true
          }
        } else if (data.type === 'deleted') {
          notifications.value = notifications.value.filter(n => n.id !== data.id)
          unreadCount.value = notifications.value.filter(n => !n.read).length
          if (selectedNotification.value && selectedNotification.value.id === data.id) {
            closeModal()
          }
        } else if (data.type === 'updated' || data.type === 'forwarded') {
          fetchNotifications()
        }
      })

      socket.on('disconnect', () => {
        console.log('Disconnected from Socket.IO notifications namespace')
      })
    }

    onMounted(() => {
      fetchNotifications()
      initializeSocket()
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateSystemTheme)
    })

    onUnmounted(() => {
      if (socket) socket.disconnect()
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', updateSystemTheme)
    })

    return {
      notifications,
      notificationsLoading,
      unreadCount,
      groupByType,
      groupByStream,
      groupedNotifications,
      theme,
      selectedNotification,
      formatTime,
      formatObjects,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle,
      openModal,
      closeModal,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream
    }
  }
}
</script>

<style scoped>
.mobile-agent-notifications {
  padding: 0;
  max-width: 100%;
  min-height: 100vh;
  background-color: var(--body-bg);
  color: var(--text-color);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.section-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--card-bg);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 10;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-color);
}

.notification-controls {
  display: flex;
  gap: 0.5rem;
}

.btn-mark-all {
  background-color: var(--primary-color);
  color: var(--text-white);
  border: none;
  border-radius: 1rem;
  padding: 0.75rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.btn-mark-all::after {
  content: '';
  position: absolute;
  background: rgba(255, 255, 255, 0.3);
  width: 0;
  height: 0;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.3s ease, height 0.3s ease;
}

.btn-mark-all:active::after {
  width: 200%;
  height: 200%;
}

.notification-filters {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background-color: var(--input-bg);
  border-bottom: 1px solid var(--border-color);
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-color);
  user-select: none;
}

.toggle-switch {
  width: 2.5rem;
  height: 1.5rem;
  border-radius: 0.75rem;
  background-color: var(--border-color);
  position: relative;
  cursor: pointer;
  transition: var(--transition);
}

.toggle-switch.active {
  background-color: var(--primary-color);
}

.toggle-switch-handle {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  background-color: var(--text-white);
  position: absolute;
  top: 0.125rem;
  left: 0.125rem;
  transition: transform 0.2s;
}

.toggle-switch.active .toggle-switch-handle {
  transform: translateX(1rem);
}

.loading,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  color: var(--text-light);
  font-size: 1rem;
  text-align: center;
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  opacity: 0.7;
}

.notification-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 1rem 1rem;
  -webkit-overflow-scrolling: touch;
}

.notification-group h3 {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 1rem 0 0.5rem;
  color: var(--text-color);
  position: sticky;
  top: 4rem;
  background-color: var(--body-bg);
  padding: 0.5rem 0;
  z-index: 5;
}

.notification-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  background-color: var(--input-bg);
  border-radius: 1rem;
  margin-bottom: 0.5rem;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
  overflow: hidden;
  animation: slideIn 0.3s ease;
}

.notification-item.unread {
  border-left: 4px solid var(--primary-color);
}

.notification-item:active {
  transform: scale(0.98);
  box-shadow: var(--shadow-md);
}

.notification-item::after {
  content: '';
  position: absolute;
  background: rgba(0, 0, 0, 0.1);
  width: 0;
  height: 0;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.3s ease, height 0.3s ease;
}

.notification-item:active::after {
  width: 200%;
  height: 200%;
}

.notification-icon {
  width: 2.5rem;
  height: 2.5rem;
  min-width: 2.5rem;
  border-radius: 50%;
  color: var(--text-white);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  margin-right: 1rem;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
  color: var(--text-color);
}

.notification-text {
  font-size: 0.75rem;
  color: var(--text-light);
  line-height: 1.5;
  margin-bottom: 0.25rem;
  word-break: break-word;
}

.notification-time {
  font-size: 0.75rem;
  color: var(--text-light);
}

.notification-status {
  margin-left: 0.5rem;
}

.unread-indicator {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background-color: var(--primary-color);
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

.modal {
  background-color: var(--card-bg);
  border-radius: 1rem;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-md);
  animation: slideUp 0.3s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-color);
}

.modal-body {
  padding: 1rem;
}

.modal-body p {
  margin: 0.5rem 0;
  font-size: 0.875rem;
  color: var(--text-color);
  line-height: 1.5;
}

.modal-body p strong {
  font-weight: 600;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid var(--border-color);
}

.mark-read-btn {
  background-color: var(--primary-color);
  color: var(--text-white);
  border: none;
  border-radius: 1rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.mark-read-btn::after {
  content: '';
  position: absolute;
  background: rgba(255, 255, 255, 0.3);
  width: 0;
  height: 0;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.3s ease, height 0.3s ease;
}

.mark-read-btn:active::after {
  width: 200%;
  height: 200%;
}

.mark-read-btn:hover {
  background-color: var(--secondary-color);
}

.close-btn {
  background-color: var(--border-color);
  color: var(--text-color);
  border: none;
  border-radius: 1rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.close-btn::after {
  content: '';
  position: absolute;
  background: rgba(0, 0, 0, 0.1);
  width: 0;
  height: 0;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.3s ease, height 0.3s ease;
}

.close-btn:active::after {
  width: 200%;
  height: 200%;
}

.close-btn:hover {
  background-color: var(--text-light);
}

/* Animations */
@keyframes slideIn {
  from {
    transform: translateY(10px);
    opacity: 0;
  }

  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }

  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Theme Variables */
.mobile-agent-notifications {
  --primary-color: #6200ea;
  --secondary-color: #3700b3;
  --body-bg: #f5f5f5;
  --card-bg: #ffffff;
  --input-bg: #ffffff;
  --text-color: #212121;
  --text-light: #757575;
  --text-white: #ffffff;
  --border-color: #e0e0e0;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.12);
  --transition: all 0.2s ease;
}

.mobile-agent-notifications[data-theme="dark"] {
  --primary-color: #bb86fc;
  --secondary-color: #3700b3;
  --body-bg: #121212;
  --card-bg: #1e1e1e;
  --input-bg: #1e1e1e;
  --text-color: #e0e0e0;
  --text-light: #9e9e9e;
  --text-white: #ffffff;
  --border-color: #424242;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.3);
}

/* Responsive Adjustments */
@media (max-width: 360px) {
  .section-header h2 {
    font-size: 1.25rem;
  }

  .btn-mark-all {
    padding: 0.5rem 1rem;
    font-size: 0.75rem;
  }

  .notification-item {
    padding: 0.75rem;
  }

  .notification-title {
    font-size: 0.75rem;
  }

  .notification-text {
    font-size: 0.75rem;
  }

  .modal {
    max-width: 95%;
  }
}
</style>
