<template>
  <div class="notifications-page">
    <div class="notifications-controls">
      <div class="main-filter-controls">
        <button 
          v-for="tab in ['All', 'Unread', 'Detections']" 
          :key="tab"
          :class="['filter-btn', { active: mainFilter === tab }]"
          @click="setMainFilter(tab)"
        >
          {{ tab }}
        </button>
      </div>
      <div v-if="mainFilter === 'Detections'" class="sub-filter-controls">
        <button 
          v-for="subTab in ['Visual', 'Audio', 'Chat']" 
          :key="subTab"
          :class="['sub-filter-btn', { active: detectionSubFilter === subTab }]"
          @click="setDetectionSubFilter(subTab)"
        >
          {{ subTab }}
        </button>
      </div>
      <div class="action-controls">
        <button 
          class="mark-all-read"
          @click="markAllAsRead"
          :disabled="unreadCount === 0"
        >
          <font-awesome-icon icon="envelope-open-text" /> Mark All as Read
        </button>
        <button 
          class="delete-all"
          @click="deleteAllNotifications"
          :disabled="notifications.length === 0"
        >
          <font-awesome-icon icon="trash-alt" /> Delete All
        </button>
        <button class="refresh-notifications" @click="fetchNotifications">
          <font-awesome-icon icon="sync-alt" /> Refresh
        </button>
      </div>
    </div>

    <div class="notifications-container">
      <div class="notifications-list-container">
        <h3>Notifications ({{ notifications.length }})</h3>
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading notifications...</p>
        </div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else-if="filteredNotifications.length === 0" class="empty-state">
          <div class="empty-icon">🔔</div>
          <p>No notifications to display</p>
        </div>
        <div v-else class="notifications-list">
          <div 
            v-for="notification in filteredNotifications" 
            :key="notification.id"
            :class="['notification-item', { 
              read: notification.read, 
              unread: !notification.read,
              selected: selectedNotification?.id === notification.id
            }]"
            @click="handleNotificationClick(notification)"
          >
            <div 
              class="notification-indicator"
              :style="{
                backgroundColor: getIndicatorColor(notification)
              }"
            ></div>
            <div class="notification-content">
              <div class="notification-message">
                {{ getNotificationPreview(notification) }}
              </div>
              <div class="notification-meta">
                <span class="notification-time">
                  {{ formatTime(notification.timestamp) }}
                </span>
                <span 
                  v-if="notification.event_type === 'object_detection'" 
                  class="notification-confidence"
                >
                  {{ formatConfidence(notification.details?.detections?.[0]?.confidence) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="notification-detail-container">
        <div v-if="!selectedNotification" class="empty-detail">
          <div class="empty-icon">📋</div>
          <p>Select a notification to view details</p>
        </div>
        <div v-else class="notification-detail">
          <div class="detail-header">
            <h3>{{ getDetailTitle(selectedNotification) }}</h3>
            <div class="detail-actions">
              <button 
                v-if="!selectedNotification.read" 
                class="mark-read-btn" 
                @click="markAsRead(selectedNotification.id)"
              >
                <font-awesome-icon icon="check" /> Mark as Read
              </button>
              <div v-if="user?.role === 'admin'" class="forward-section">
                <button class="forward-btn" @click="showAgentDropdown = true">
                  <font-awesome-icon icon="share" /> Forward to Agent
                </button>
                <div v-if="showAgentDropdown" class="forward-modal-overlay" @click="showAgentDropdown = false">
                  <div class="forward-modal-content" @click.stop>
                    <div class="modal-header">
                      <h3>Select Agent</h3>
                      <button class="modal-close-btn" @click="showAgentDropdown = false">
                        &times;
                      </button>
                    </div>
                    <div class="agent-list">
                      <div 
                        v-for="agent in agents" 
                        :key="agent.id" 
                        class="agent-option"
                        @click="forwardNotification(agent.id)"
                      >
                        <div :class="['agent-status-indicator', { online: agent.online }]"></div>
                        <div class="agent-info">
                          <div class="agent-name">{{ agent.username }}</div>
                          <div class="agent-email">{{ agent.email }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <button class="delete-btn" @click="deleteNotification(selectedNotification.id)">
                <font-awesome-icon icon="trash-alt" /> Delete
              </button>
            </div>
          </div>
          <div class="detail-timestamp">
            Detected at: {{ formatTime(selectedNotification.timestamp) }}
          </div>

          <!-- Visual Detection Details -->
          <div v-if="selectedNotification.event_type === 'object_detection'" class="detection-content">
            <div class="image-gallery">
              <div v-if="selectedNotification.details?.annotated_image" class="image-card">
                <img
                  :src="formatImage(selectedNotification.details.annotated_image)"
                  alt="Annotated Detection"
                  class="detection-image"
                />
                <div class="image-label">Annotated Image</div>
              </div>
              <div v-if="selectedNotification.details?.captured_image" class="image-card">
                <img
                  :src="selectedNotification.details.captured_image"
                  alt="Captured Image"
                  class="detection-image"
                />
                <div class="image-label">Captured Image</div>
              </div>
            </div>
            <div class="streamer-info-card">
              <h4>Streamer Info</h4>
              <div class="info-item">
                <span class="info-label">Streamer:</span>
                <span class="info-value">{{ selectedNotification.details?.streamer_name || 'Unknown' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Assigned Agent:</span>
                <span class="info-value">
                  <span v-if="getAssignedAgentForStream() !== 'Unassigned'">
                    {{ getAssignedAgentForStream() }}
                  </span>
                  <span v-else class="unassigned-badge">⚠️ UNASSIGNED</span>
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">Platform:</span>
                <span class="info-value">{{ selectedNotification.details?.platform || 'Unknown' }}</span>
              </div>
            </div>
            <div class="detected-objects">
              <h4>Detected Objects</h4>
              <div class="detection-items">
                <div 
                  v-for="(detection, index) in selectedNotification.details?.detections" 
                  :key="index" 
                  class="detection-item"
                >
                  <span class="detection-class">{{ detection.class }}</span>
                  <span 
                    class="confidence-badge"
                    :style="{ backgroundColor: getConfidenceColor(detection.confidence) }"
                  >
                    {{ formatConfidence(detection.confidence) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Audio Detection Details -->
          <div v-else-if="selectedNotification.event_type === 'audio_detection'" class="audio-detection-content">
            <p>Detected keywords: <strong>{{ selectedNotification.details?.keywords?.join(', ') }}</strong></p>
            <p>Transcript: {{ selectedNotification.details?.transcript }}</p>
          </div>

          <!-- Chat Detection Details -->
          <div v-else-if="selectedNotification.event_type === 'chat_detection'" class="chat-detection-content">
            <p>Detected chat keyword: <strong>{{ selectedNotification.details?.keyword }}</strong></p>
            <div v-if="selectedNotification.details?.messages" class="chat-messages">
              <div 
                v-for="(msg, idx) in selectedNotification.details.messages" 
                :key="idx" 
                class="chat-message"
              >
                <span class="chat-sender">{{ msg.sender }}:</span>
                <span class="chat-text">{{ msg.message }}</span>
                <div class="chat-keywords">
                  <span 
                    v-for="(kw, kIdx) in msg.keywords" 
                    :key="kIdx" 
                    class="chat-keyword"
                  >
                    {{ kw }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Stream Created Details -->
          <div v-else-if="selectedNotification.event_type === 'stream_created'" class="stream-created-content">
            <p>A new stream has been created by <strong>{{ selectedNotification.details?.streamer_name || 'Unknown' }}</strong>.</p>
            <p v-if="selectedNotification.details?.stream_url">
              Stream URL: 
              <a :href="selectedNotification.details.stream_url" target="_blank" rel="noopener noreferrer">
                {{ selectedNotification.details.stream_url }}
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { io } from 'socket.io-client'

export default {
  name: 'NotificationsTab',
  props: {
    user: Object
  },
  setup(props) {
    const notifications = ref([])
    const loading = ref(true)
    const error = ref(null)
    const mainFilter = ref('All')
    const detectionSubFilter = ref('Visual')
    const selectedNotification = ref(null)
    const agents = ref([])
    const dashboardStreams = ref([])
    const showAgentDropdown = ref(false)
    const socket = ref(null)
    const SOCKET_SERVER_URL = 'https://54.86.99.85:5000'

    const unreadCount = computed(() => {
      return notifications.value.filter(n => !n.read).length
    })

    const filteredNotifications = computed(() => {
      let filtered = notifications.value
      
      if (mainFilter.value === 'Unread') {
        filtered = filtered.filter(n => !n.read)
      } else if (mainFilter.value === 'Detections') {
        const typeMap = {
          Visual: 'object_detection',
          Audio: 'audio_detection',
          Chat: 'chat_detection',
        }
        filtered = filtered.filter(n => n.event_type === typeMap[detectionSubFilter.value])
      }
      
      if (props.user?.role === 'agent') {
        filtered = filtered.filter(n => 
          (n.assigned_agent || "").toLowerCase() === props.user.username.toLowerCase()
        )
      }
      
      return filtered
    })

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleString()
    }

    const formatConfidence = (confidence) => {
      return (typeof confidence === 'number' && confidence > 0)
        ? `${(confidence * 100).toFixed(1)}%`
        : ''
    }

    const getConfidenceColor = (confidence) => {
      const conf = typeof confidence === 'number' ? confidence : 0
      if (conf >= 0.9) return '#ff4444'
      if (conf >= 0.75) return '#ff8c00'
      if (conf >= 0.5) return '#ffcc00'
      return '#28a745'
    }

    const getIndicatorColor = (notification) => {
      if (notification.event_type === 'object_detection') {
        return getConfidenceColor(notification.details?.detections?.[0]?.confidence)
      } else if (notification.event_type === 'audio_detection') {
        return '#007bff'
      } else if (notification.event_type === 'chat_detection') {
        return '#8a2be2'
      } else if (notification.event_type === 'stream_created') {
        return '#28a745'
      }
      return '#28a745'
    }

    const getNotificationPreview = (notification) => {
      if (notification.event_type === 'object_detection') {
        return `Detected ${notification.details?.detections?.length || 0} objects`
      } else if (notification.event_type === 'audio_detection') {
        return `Detected keyword: ${notification.details?.keyword}`
      } else if (notification.event_type === 'chat_detection') {
        return `Chat event: ${notification.details?.keyword}`
      } else if (notification.event_type === 'stream_created') {
        return `New stream created by ${notification.details?.streamer_name || 'Unknown'}`
      }
      return notification.message || 'New notification'
    }

    const getDetailTitle = (notification) => {
      if (notification.event_type === 'audio_detection') return 'Audio Detection Details'
      if (notification.event_type === 'object_detection') return 'Visual Detection Details'
      if (notification.event_type === 'chat_detection') return 'Chat Detection Details'
      if (notification.event_type === 'stream_created') return 'New Stream Created'
      return 'Notification Details'
    }

    const formatImage = (image) => {
      if (image && !image.startsWith("data:")) {
        return "data:image/png;base64," + image
      }
      return image
    }

    const extractStreamInfo = (streamUrl) => {
      let platform = 'Chaturbate'
      let streamer = ''
      if (streamUrl && streamUrl.includes('edge-hls.doppiocdn.live')) {
        platform = 'Stripchat'
      }
      if (streamUrl) {
        const parts = streamUrl.split('/')
        streamer = parts[parts.length - 1].split('?')[0]
      }
      return { platform, streamer }
      
    }
    console.log(extractStreamInfo)
    const getAssignedAgentForStream = () => {
      if (dashboardStreams.value.length > 0 && selectedNotification.value && selectedNotification.value.details) {
        const { platform, streamer } = selectedNotification.value.details.stream || {}
        const matchedStream = dashboardStreams.value.find(s =>
          s.type?.toLowerCase() === platform?.toLowerCase() &&
          s.streamer_username?.toLowerCase() === streamer?.toLowerCase()
        )
        if (matchedStream && matchedStream.assignments && matchedStream.assignments.length > 0 && matchedStream.assignments[0].agent) {
          const agentId = matchedStream.assignments[0].agent.id
          const foundAgent = agents.value.find(a => a.id === agentId)
          if (foundAgent) return foundAgent.username
          return matchedStream.assignments[0].agent.username || "Unassigned"
        }
      }
      return "Unassigned"
    }

    const fetchDashboardStreams = async () => {
      try {
        const res = await axios.get('/api/dashboard')
        if (res.status === 200 && res.data && res.data.streams) {
          dashboardStreams.value = res.data.streams
        }
      } catch (err) {
        console.error('Error fetching dashboard streams:', err)
      }
    }

    const fetchAgents = async () => {
      if (props.user?.role === 'admin') {
        try {
          const res = await axios.get('/api/agents')
          agents.value = res.data
        } catch (err) {
          console.error('Error fetching agents:', err)
        }
      }
    }

    const processNotifications = (data) => {
      return data.map(notification => {
        const assignedAgent = notification.details?.assigned_agent || notification.assigned_agent || "Unassigned"
        const baseNotification = {
          id: notification.id,
          event_type: notification.event_type,
          timestamp: notification.timestamp,
          read: notification.read,
          details: {
            ...notification.details,
            detections: (notification.details?.detections || []).map(d => ({
              class: d.class,
              confidence: d.confidence || d.score || 0,
              bbox: d.bbox || []
            })),
            images: notification.details?.images || {
              annotated: notification.details?.annotated_image,
              original: notification.details?.captured_image
            },
            stream: notification.details?.stream || {
              platform: notification.details?.platform,
              streamer: notification.details?.streamer_name,
              url: notification.room_url
            },
            agent: assignedAgent
          },
          assigned_agent: assignedAgent
        }

        return {
          ...baseNotification,
          displayType: notification.event_type === 'object_detection' ? 'object' : notification.event_type,
          previewText: notification.event_type === 'object_detection'
            ? `${notification.details.detections.length} objects detected`
            : notification.details.message,
          timestamp: notification.timestamp,
          confidence: notification.event_type === 'object_detection'
            ? Math.max(...(notification.details.detections.map(d => d.confidence))) || 0
            : 0
        }
      })
    }

    const fetchNotifications = async () => {
      try {
        loading.value = true
        error.value = null
        const res = await axios.get('/api/notifications', { timeout: 10000 })
        if (res.status === 200 && Array.isArray(res.data)) {
          notifications.value = processNotifications(res.data)
        } else {
          error.value = 'Unexpected response from server.'
        }
      } catch (err) {
        console.error('Error fetching notifications:', err)
        error.value = 'Failed to load notifications.'
      } finally {
        loading.value = false
      }
    }

    const markAsRead = async (notificationId) => {
      try {
        await axios.put(`/api/notifications/${notificationId}/read`)
        notifications.value = notifications.value.map(n => 
          n.id === notificationId ? { ...n, read: true } : n
        )
      } catch (err) {
        console.error('Error marking notification as read:', err)
      }
    }

    const markAllAsRead = async () => {
      try {
        await axios.put('/api/notifications/read-all')
        notifications.value = notifications.value.map(n => ({ ...n, read: true }))
      } catch (err) {
        console.error('Error marking all notifications as read:', err)
      }
    }

    const deleteNotification = async (notificationId) => {
      try {
        await axios.delete(`/api/notifications/${notificationId}`)
        notifications.value = notifications.value.filter(n => n.id !== notificationId)
        if (selectedNotification.value?.id === notificationId) {
          selectedNotification.value = null
        }
      } catch (err) {
        console.error('Error deleting notification:', err)
      }
    }

    const deleteAllNotifications = async () => {
      try {
        await axios.delete('/api/notifications/delete-all')
        notifications.value = []
        selectedNotification.value = null
      } catch (err) {
        console.error('Error deleting all notifications:', err)
      }
    }

    const forwardNotification = async (agentId) => {
      if (!selectedNotification.value) return
      try {
        await axios.post(`/api/notifications/${selectedNotification.value.id}/forward`, { 
          agent_id: agentId 
        })
        showAgentDropdown.value = false
        fetchNotifications()
      } catch (err) {
        console.error('Forward error:', err)
      }
    }

    const handleNotificationClick = (notification) => {
      if (!notification.read) markAsRead(notification.id)
      selectedNotification.value = notification
      
      if (notification.event_type === 'object_detection') {
        fetchDashboardStreams()
      }
    }

    const setMainFilter = (filter) => {
      mainFilter.value = filter
      if (filter === 'Detections') {
        detectionSubFilter.value = 'Visual'
      }
    }

    const setDetectionSubFilter = (subFilter) => {
      detectionSubFilter.value = subFilter
    }

    onMounted(() => {
      socket.value = io(SOCKET_SERVER_URL, { withCredentials: true })
      socket.value.on('notification_forwarded', fetchNotifications)

      fetchAgents()
      fetchNotifications()
      const interval = setInterval(fetchNotifications, 60000)

      onUnmounted(() => {
        clearInterval(interval)
        if (socket.value) socket.value.disconnect()
      })
    })

    return {
      notifications,
      loading,
      error,
      mainFilter,
      detectionSubFilter,
      selectedNotification,
      agents,
      showAgentDropdown,
      unreadCount,
      filteredNotifications,
      formatTime,
      formatConfidence,
      getConfidenceColor,
      getIndicatorColor,
      getNotificationPreview,
      getDetailTitle,
      formatImage,
      getAssignedAgentForStream,
      fetchNotifications,
      markAsRead,
      markAllAsRead,
      deleteNotification,
      deleteAllNotifications,
      forwardNotification,
      handleNotificationClick,
      setMainFilter,
      setDetectionSubFilter
    }
  }
}
</script>

<style scoped>
.notifications-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background-color: #f5f7fa;
  padding: 20px;
  box-sizing: border-box;
}

.notifications-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
  align-items: center;
}

.main-filter-controls, .sub-filter-controls {
  display: flex;
  gap: 8px;
}

.filter-btn, .sub-filter-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background-color: #e0e0e0;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.filter-btn.active, .sub-filter-btn.active {
  background-color: #3f51b5;
  color: white;
}

.action-controls {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.mark-all-read, .delete-all, .refresh-notifications {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.mark-all-read {
  background-color: #4caf50;
  color: white;
}

.mark-all-read:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.delete-all {
  background-color: #f44336;
  color: white;
}

.delete-all:disabled {
  background-color: #ef9a9a;
  cursor: not-allowed;
}

.refresh-notifications {
  background-color: #2196f3;
  color: white;
}

.notifications-container {
  display: flex;
  flex: 1;
  gap: 20px;
  height: calc(100% - 60px);
}

.notifications-list-container {
  flex: 0 0 350px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 15px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.notifications-list-container h3 {
  margin: 0 0 15px 0;
  font-size: 18px;
  color: #333;
}

.notifications-list {
  flex: 1;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #f9f9f9;
}

.notification-item.unread {
  background-color: #e3f2fd;
  border-left: 4px solid #2196f3;
}

.notification-item.selected {
  background-color: #bbdefb;
}

.notification-item:hover {
  background-color: #e3f2fd;
}

.notification-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 8px;
  margin-right: 12px;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
}

.notification-message {
  margin: 0;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.notification-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 12px;
  color: #666;
}

.notification-time {
  color: #757575;
}

.notification-confidence {
  font-weight: 600;
}

.notification-detail-container {
  flex: 1;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 20px;
  overflow-y: auto;
}

.empty-detail, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #757575;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 15px;
  opacity: 0.5;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #3498db;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #f44336;
  padding: 15px;
  text-align: center;
}

.notification-detail {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

.detail-header h3 {
  margin: 0;
  color: #333;
}

.detail-actions {
  display: flex;
  gap: 10px;
}

.mark-read-btn, .forward-btn, .delete-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.mark-read-btn {
  background-color: #4caf50;
  color: white;
}

.forward-btn {
  background-color: #ff9800;
  color: white;
}

.delete-btn {
  background-color: #f44336;
  color: white;
}

.detail-timestamp {
  color: #757575;
  font-size: 14px;
}

.detection-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.image-gallery {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.image-card {
  flex: 1;
  min-width: 250px;
  border: 1px solid #eee;
  border-radius: 6px;
  overflow: hidden;
}

.detection-image {
  width: 100%;
  height: auto;
  display: block;
}

.image-label {
  padding: 8px;
  text-align: center;
  background-color: #f5f5f5;
  font-size: 14px;
  color: #666;
}

.streamer-info-card {
  background-color: #f9f9f9;
  border-radius: 6px;
  padding: 15px;
}

.streamer-info-card h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.info-item {
  display: flex;
  margin-bottom: 8px;
}

.info-label {
  font-weight: 500;
  min-width: 120px;
  color: #666;
}

.info-value {
  color: #333;
}

.unassigned-badge {
  color: #f44336;
  font-weight: 500;
}

.detected-objects h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.detection-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detection-item {
  display: flex;
  align-items: center;
  background-color: #f5f5f5;
  padding: 6px 12px;
  border-radius: 20px;
  gap: 8px;
}

.detection-class {
  font-weight: 500;
}

.confidence-badge {
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}

.forward-section {
  position: relative;
}

.forward-modal-overlay {
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
}

.forward-modal-content {
  background-color: white;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
}

.agent-list {
  padding: 10px;
}

.agent-option {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.agent-option:hover {
  background-color: #f5f5f5;
}

.agent-status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 12px;
  background-color: #ccc;
}

.agent-status-indicator.online {
  background-color: #4caf50;
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-weight: 500;
  color: #333;
}

.agent-email {
  font-size: 12px;
  color: #757575;
}

.audio-detection-content, .chat-detection-content, .stream-created-content {
  background-color: #f9f9f9;
  padding: 15px;
  border-radius: 6px;
}

.chat-messages {
  margin-top: 15px;
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.chat-message {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.chat-sender {
  font-weight: 500;
  color: #3f51b5;
  margin-right: 5px;
}

.chat-text {
  color: #333;
}

.chat-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 5px;
}

.chat-keyword {
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}
</style>