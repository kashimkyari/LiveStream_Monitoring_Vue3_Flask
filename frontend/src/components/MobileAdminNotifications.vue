<template>
  <div class="mobile-admin-notifications" :data-theme="theme">
    <div class="header">
      <h2>Notifications</h2>
      <div class="header-actions">
        <button @click="refreshNotifications" :disabled="notificationsLoading" class="refresh-btn">
          <font-awesome-icon :icon="['fas', 'sync-alt']" :class="{ 'spinning': notificationsLoading }" />
        </button>
        <button @click="markAllAsRead" :disabled="unreadCount === 0" class="mark-all-read-btn">
          Mark All Read
        </button>
      </div>
    </div>

    <div class="filter-section">
      <label>
        <input type="checkbox" v-model="groupByType" @change="toggleGroupByType" />
        Group by Type
      </label>
      <label>
        <input type="checkbox" v-model="groupByStream" @change="toggleGroupByStream" />
        Group by Streamer
      </label>
    </div>

    <div v-if="notificationsLoading" class="loading">
      Loading notifications...
    </div>
    <div v-else-if="notifications.length === 0" class="no-notifications">
      No notifications available.
    </div>
    <div v-else class="notifications-list">
      <template v-if="groupByType || groupByStream">
        <div v-for="(group, key) in groupedNotifications" :key="key" class="notification-group">
          <h3>
            {{
              groupByType
                ? key.replace('_', ' ').toUpperCase()
                : group[0].details.streamer_name || 'Unknown Streamer'
            }}
          </h3>
          <div v-for="notification in group" :key="notification.id" class="notification-item"
            :class="{ 'unread': !notification.read }" @click="openModal(notification)">
            <div class="notification-content">
              <div class="notification-header">
                <span class="type" :class="getTypeClass(notification.event_type)">
                  {{ notification.event_type.replace('_', ' ') }}
                </span>
                <span class="time">{{ formatTime(notification.timestamp) }}</span>
              </div>
              <div class="notification-details">
                <p>
                  <strong>Streamer:</strong>
                  {{ notification.details.streamer_name || 'Unknown' }}
                </p>
                <p>
                  <strong>Platform:</strong>
                  {{ notification.details.platform || 'Unknown' }}
                </p>
                <p v-if="notification.event_type === 'object_detection'">
                  <strong>Objects:</strong>
                  {{ formatObjects(notification.details.detections) }}
                </p>
                <p v-if="notification.event_type === 'audio_detection'">
                  <strong>Keyword:</strong>
                  {{ notification.details.keyword || 'N/A' }}<br />
                  <strong>Transcript:</strong>
                  {{
                    notification.details.transcript?.slice(0, 100) +
                    (notification.details.transcript?.length > 100 ? '...' : '')
                  }}
                </p>
                <p v-if="
                  notification.event_type === 'chat_detection' ||
                  notification.event_type === 'chat_sentiment_detection'
                ">
                  <strong>Sender:</strong>
                  {{ notification.details.detections?.[0]?.sender || 'Unknown' }}<br />
                  <strong>Message:</strong>
                  {{
                    notification.details.detections?.[0]?.message?.slice(0, 100) +
                    (notification.details.detections?.[0]?.message?.length > 100
                      ? '...'
                      : '')
                  }}
                </p>
                <p>
                  <strong>Assigned Agent:</strong>
                  {{ notification.details.assigned_agent || 'Unassigned' }}
                </p>
              </div>
              <button v-if="!notification.read" @click.stop="markAsRead(notification.id)" class="mark-read-btn">
                Mark as Read
              </button>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <div v-for="notification in notifications" :key="notification.id" class="notification-item"
          :class="{ 'unread': !notification.read }" @click="openModal(notification)">
          <div class="notification-content">
            <div class="notification-header">
              <span class="type" :class="getTypeClass(notification.event_type)">
                {{ notification.event_type.replace('_', ' ') }}
              </span>
              <span class="time">{{ formatTime(notification.timestamp) }}</span>
            </div>
            <div class="notification-details">
              <p>
                <strong>Streamer:</strong>
                {{ notification.details.streamer_name || 'Unknown' }}
              </p>
              <p>
                <strong>Platform:</strong>
                {{ notification.details.platform || 'Unknown' }}
              </p>
              <p v-if="notification.event_type === 'object_detection'">
                <strong>Objects:</strong>
                {{ formatObjects(notification.details.detections) }}
              </p>
              <p v-if="notification.event_type === 'audio_detection'">
                <strong>Keyword:</strong>
                {{ notification.details.keyword || 'N/A' }}<br />
                <strong>Transcript:</strong>
                {{
                  notification.details.transcript?.slice(0, 100) +
                  (notification.details.transcript?.length > 100 ? '...' : '')
                }}
              </p>
              <p v-if="
                notification.event_type === 'chat_detection' ||
                notification.event_type === 'chat_sentiment_detection'
              ">
                <strong>Sender:</strong>
                {{ notification.details.detections?.[0]?.sender || 'Unknown' }}<br />
                <strong>Message:</strong>
                {{
                  notification.details.detections?.[0]?.message?.slice(0, 100) +
                  (notification.details.detections?.[0]?.message?.length > 100
                    ? '...'
                    : '')
                }}
              </p>
              <p>
                <strong>Assigned Agent:</strong>
                {{ notification.details.assigned_agent || 'Unassigned' }}
              </p>
            </div>
            <button v-if="!notification.read" @click.stop="markAsRead(notification.id)" class="mark-read-btn">
              Mark as Read
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- Modal for Notification Details -->
    <transition name="modal">
      <div v-if="selectedNotification" class="modal-overlay" @click="closeModal">
        <div class="modal" @click.stop>
          <div class="modal-header">
            <h3>{{ selectedNotification.event_type.replace('_', ' ') }}</h3>
            <button class="close-btn small-btn" @click="closeModal">
              <font-awesome-icon icon="times" />
            </button>
          </div>
          <div class="modal-body">
            <div class="modal-section">
              <p><strong>ID:</strong> {{ selectedNotification.id }}</p>
              <p><strong>Streamer:</strong> {{ selectedNotification.details.streamer_name || 'Unknown' }}</p>
              <p><strong>Platform:</strong> {{ selectedNotification.details.platform || 'Unknown' }}</p>
              <p><strong>Timestamp:</strong> {{ formatTime(selectedNotification.timestamp) }}</p>
              <p><strong>Status:</strong> {{ selectedNotification.read ? 'Read' : 'Unread' }}</p>
              <p><strong>Assigned Agent:</strong> {{ selectedNotification.details.assigned_agent || 'Unassigned' }}</p>
            </div>
            <div class="modal-section" v-if="selectedNotification.event_type === 'object_detection'">
              <p><strong>Detected Objects:</strong> {{ formatObjects(selectedNotification.details.detections) }}</p>
              <div v-if="selectedNotification.details.annotated_image" class="image-container" @click="toggleImageZoom">
                <img :src="selectedNotification.details.annotated_image" alt="Annotated Image"
                  class="annotated-image" />
              </div>
            </div>
            <div class="modal-section" v-if="selectedNotification.event_type === 'audio_detection'">
              <p><strong>Keyword:</strong> {{ selectedNotification.details.keyword || 'N/A' }}</p>
              <p><strong>Transcript:</strong> {{ selectedNotification.details.transcript || 'N/A' }}</p>
            </div>
            <div class="modal-section"
              v-if="selectedNotification.event_type === 'chat_detection' || selectedNotification.event_type === 'chat_sentiment_detection'">
              <p><strong>Sender:</strong> {{ selectedNotification.details.detections?.[0]?.sender || 'Unknown' }}</p>
              <p><strong>Message:</strong> {{ selectedNotification.details.detections?.[0]?.message || 'N/A' }}</p>
            </div>
          </div>
          <div class="modal-footer">
            <button v-if="!selectedNotification.read" class="mark-read-btn small-btn"
              @click="markAsRead(selectedNotification.id)">
              Mark as Read
            </button>
            <button class="close-btn small-btn" @click="closeModal">Close</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Full-screen Image Viewer -->
    <transition name="image-zoom">
      <div v-if="isImageZoomed" class="image-zoom-overlay" @click="toggleImageZoom">
        <img :src="selectedNotification?.details?.annotated_image" alt="Zoomed Annotated Image" class="zoomed-image" />
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'
import { io } from 'socket.io-client'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faSyncAlt, faTimes } from '@fortawesome/free-solid-svg-icons'
import { library } from '@fortawesome/fontawesome-svg-core'

library.add(faSyncAlt, faTimes)

export default {
  name: 'MobileAdminNotifications',
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
    'mark-as-read',
    'mark-all-read',
    'toggle-group-by-type',
    'toggle-group-by-stream',
    'refresh'
  ],
  setup(props, { emit }) {
    const toast = useToast()
    const notifications = ref([])
    const notificationsLoading = ref(false)
    const unreadCount = ref(0)
    const groupByType = ref(false)
    const groupByStream = ref(false)
    const selectedNotification = ref(null)
    const isImageZoomed = ref(false)
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
          : notification.details.streamer_name || 'Unknown'
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

    // Get CSS class for notification type
    const getTypeClass = (type) => {
      switch (type) {
        case 'object_detection':
          return 'type-object'
        case 'audio_detection':
          return 'type-audio'
        case 'chat_detection':
        case 'chat_sentiment_detection':
          return 'type-chat'
        default:
          return 'type-default'
      }
    }

    // Open modal with notification details
    const openModal = (notification) => {
      selectedNotification.value = notification
    }

    // Close modal
    const closeModal = () => {
      selectedNotification.value = null
      isImageZoomed.value = false
    }

    // Toggle image zoom
    const toggleImageZoom = () => {
      isImageZoomed.value = !isImageZoomed.value
    }

    // Fetch all notifications
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

    // Refresh notifications
    const refreshNotifications = () => {
      emit('refresh')
      fetchNotifications()
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
          emit('mark-as-read', notificationId)
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
      emit('toggle-group-by-type')
    }

    // Toggle group by stream
    const toggleGroupByStream = () => {
      groupByStream.value = !groupByStream.value
      emit('toggle-group-by-stream')
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
      isImageZoomed,
      formatTime,
      formatObjects,
      getTypeClass,
      openModal,
      closeModal,
      toggleImageZoom,
      refreshNotifications,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream
    }
  }
}
</script>

<style scoped>
.mobile-admin-notifications {
  font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --primary-color: #4361ee;
  --primary-light: #4361ee20;
  --secondary-color: #3f37c9;
  --text-color: #333333;
  --text-light: #777777;
  --background-color: #f8f9fa;
  --card-bg: #ffffff;
  --border-color: #e0e0e0;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  --border-radius: 12px;
  background-color: var(--background-color);
  color: var(--text-color);
  padding: 12px;
  max-width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.mobile-admin-notifications[data-theme="dark"] {
  --primary-color: #4cc9f0;
  --primary-light: #4cc9f020;
  --secondary-color: #4895ef;
  --text-color: #f8f9fa;
  --text-light: #b0b0b0;
  --background-color: #121212;
  --card-bg: #1e1e1e;
  --border-color: #333333;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
}

.header {
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

.header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-color);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.refresh-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
  min-width: 2rem;
  min-height: 2rem;
}

.mark-all-read-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
  min-width: 2rem;
  min-height: 2rem;
}

.mark-all-read-btn:hover,
.refresh-btn:hover {
  background-color: var(--secondary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.mark-all-read-btn:disabled,
.refresh-btn:disabled {
  background-color: var(--border-color);
  cursor: not-allowed;
}

.filter-section {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background-color: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
}

.filter-section label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-color);
  user-select: none;
}

.loading,
.no-notifications {
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

.notifications-list {
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
  background-color: var(--background-color);
  padding: 0.5rem 0;
  z-index: 5;
}

.notification-item {
  background-color: var(--card-bg);
  border-radius: var(--border-radius);
  margin-bottom: 0.5rem;
  margin-top: 6px;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
  overflow: hidden;
  animation: slideIn 0.3s ease;
  border: 1px solid var(--border-color);
}

.notification-item.unread {
  border-left: 4px solid var(--primary-color);
}

.notification-item:hover {
  transform: scale(1.01);
  box-shadow: var(--shadow-md);
}

.notification-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.75rem;
  border-radius: var(--border-radius);
  color: white;
}

.type-object {
  background-color: #4CAF50;
}

.type-audio {
  background-color: #2196F3;
}

.type-chat {
  background-color: #FFC107;
}

.type-default {
  background-color: var(--text-light);
}

.time {
  font-size: 0.75rem;
  color: var(--text-light);
}

.notification-details p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
  color: var(--text-color);
  line-height: 1.5;
}

.notification-details p strong {
  font-weight: 600;
}

.mark-read-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  align-self: flex-end;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.mark-read-btn:hover {
  background-color: var(--secondary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background-color: var(--card-bg);
  border-radius: var(--border-radius);
  max-width: 90%;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: var(--shadow-md);
  animation: slideUp 0.3s ease;
  padding: 0.5rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--card-bg);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-color);
}

.modal-body {
  padding: 1.5rem;
}

.modal-section {
  margin-bottom: 1rem;
  padding: 1rem;
  background: var(--card-bg);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.modal-section p {
  margin: 0.5rem 0;
  font-size: 0.875rem;
  color: var(--text-color);
  line-height: 1.6;
}

.modal-section p strong {
  font-weight: 600;
  color: var(--primary-color);
}

.image-container {
  margin-top: 1rem;
  cursor: pointer;
  overflow: hidden;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s ease;
  border: 1px solid var(--border-color);
}

.image-container:hover {
  transform: scale(1.02);
}

.annotated-image {
  width: 100%;
  height: auto;
  display: block;
  border-radius: var(--border-radius);
  object-fit: contain;
  transition: opacity 0.3s ease;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
  background: var(--card-bg);
}

.small-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.75rem;
  border-radius: var(--border-radius);
  min-width: 4rem;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.mark-read-btn.small-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
}

.mark-read-btn.small-btn:hover {
  background-color: var(--secondary-color);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.close-btn.small-btn {
  background-color: var(--border-color);
  color: var(--text-color);
  border: none;
}

.close-btn.small-btn:hover {
  background-color: var(--text-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.image-zoom-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  cursor: zoom-out;
}

.zoomed-image {
  max-width: 90%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-md);
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

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: translateY(20px);
  opacity: 0;
}

.image-zoom-enter-active,
.image-zoom-leave-active {
  transition: opacity 0.3s ease;
}

.image-zoom-enter-from,
.image-zoom-leave-to {
  opacity: 0;
}

.image-zoom-enter-active .zoomed-image,
.image-zoom-leave-active .zoomed-image {
  transition: transform 0.3s ease;
}

.image-zoom-enter-from .zoomed-image,
.image-zoom-leave-to .zoomed-image {
  transform: scale(0.8);
}
</style>
