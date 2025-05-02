<template>
  <div class="notifications-page" :class="{ 'dark-mode': isDarkMode }">
    <!-- Top navigation bar with filters and actions -->
    <div class="top-bar">
      <div class="filter-tabs">
        <button 
          v-for="tab in ['All', 'Unread', 'Detections']" 
          :key="tab"
          class="tab-btn"
          :class="{ 'active': mainFilter === tab }"
          @click="handleMainFilterChange(tab)"
        >
          {{ tab }}
          <span v-if="tab === 'Unread'" class="badge">{{ unreadCount }}</span>
        </button>
      </div>
      
      <div class="action-buttons">
        <button class="icon-btn refresh-btn" @click="fetchNotifications" title="Refresh">
          <span class="icon">↻</span>
        </button>
        <button class="icon-btn" @click="toggleDarkMode" :title="isDarkMode ? 'Light Mode' : 'Dark Mode'">
          <span class="icon">{{ isDarkMode ? '☀️' : '🌙' }}</span>
        </button>
        <button class="icon-btn menu-btn" @click="isMenuOpen = !isMenuOpen" title="More Actions">
          <span class="icon">⋮</span>
        </button>
      </div>
      
      <!-- Dropdown menu -->
      <div v-if="isMenuOpen" class="dropdown-menu">
        <button @click="prepareCreateForm">Create Notification</button>
        <button 
          @click="markAllAsRead"
          :disabled="filteredNotifications.filter(n => !n.read).length === 0"
        >
          Mark All as Read
        </button>
        <button 
          @click="isDeleteModalOpen = true"
          :disabled="notifications.length === 0"
        >
          Delete All
        </button>
        <button @click="toggleSound">
          {{ soundEnabled ? 'Disable Sound' : 'Enable Sound' }}
        </button>
      </div>
    </div>
    
    <!-- Sub-filters for detection types -->
    <div v-if="mainFilter === 'Detections'" class="sub-filters">
      <button 
        v-for="subTab in ['Visual', 'Audio', 'Chat']" 
        :key="subTab"
        class="sub-filter-btn"
        :class="{ active: detectionSubFilter === subTab }"
        @click="detectionSubFilter = subTab"
      >
        {{ subTab }}
      </button>
    </div>
    
    <!-- Main content area -->
    <div class="content-area">
      <!-- Left panel: Notifications list -->
      <div class="notifications-panel">
        <div class="panel-header">
          <h2>Notifications <span class="count">({{ filteredNotifications.length }})</span></h2>
        </div>
        
        <!-- Loading, error, or empty states -->
        <div v-if="loading" class="state-container">
          <div class="loading-spinner"></div>
          <p>Loading notifications...</p>
        </div>
        <div v-else-if="error" class="error-state">
          <p>{{ error }}</p>
          <button @click="fetchNotifications">Try Again</button>
        </div>
        <div v-else-if="filteredNotifications.length === 0" class="empty-state">
          <div class="empty-icon">🔔</div>
          <p>No notifications to display</p>
        </div>
        
        <!-- Notifications list -->
        <div v-else class="notification-list">
          <TransitionGroup name="list" tag="div">
            <div 
              v-for="notification in filteredNotifications" 
              :key="notification.id"
              class="notification-card"
              :class="{ 
                'read': notification.read, 
                'unread': !notification.read, 
                'selected': selectedNotification && selectedNotification.id === notification.id,
                'new-notification': newNotificationIds.includes(notification.id)
              }"
              @click="handleNotificationClick(notification)"
            >
              <div 
                class="notification-indicator"
                :style="{ backgroundColor: getNotificationColor(notification) }"
              ></div>
              
              <div class="notification-content">
                <div class="notification-header">
                  <span class="notification-type">{{ getNotificationType(notification) }}</span>
                  <span class="notification-time">{{ formatTimestamp(notification.timestamp) }}</span>
                </div>
                
                <div class="notification-message">
                  {{ getNotificationMessage(notification) }}
                </div>
                
                <div class="notification-meta">
                  <span class="notification-source">
                    {{ notification.details?.platform || 'System' }} | 
                    {{ notification.details?.streamer_name || 'Unknown' }}
                  </span>
                  <span 
                    v-if="notification.event_type === 'object_detection' && 
                         notification.details?.detections?.length" 
                    class="notification-confidence"
                  >
                    {{ formatConfidence(notification.details.detections[0].confidence) }}
                  </span>
                </div>
              </div>
              
              <div class="notification-actions">
                <button 
                  v-if="!notification.read" 
                  class="action-btn read-btn" 
                  @click.stop="markAsRead(notification.id)"
                  title="Mark as Read"
                >
                  ✓
                </button>
                <button 
                  class="action-btn delete-btn" 
                  @click.stop="deleteNotification(notification.id)"
                  title="Delete"
                >
                  ×
                </button>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </div>
      
      <!-- Right panel: Notification details -->
      <div class="details-panel" v-if="selectedNotification || isMobile">
        <div v-if="!selectedNotification && isMobile" class="empty-detail">
          <div class="empty-icon">📋</div>
          <p>Select a notification to view details</p>
        </div>
        
        <div v-else-if="selectedNotification" class="detail-content">
          <div class="detail-header">
            <button v-if="isMobile" class="back-btn" @click="selectedNotification = null">
              &larr; Back
            </button>
            <h2>{{ getNotificationDetailTitle() }}</h2>
            
            <div class="detail-actions">
              <button 
                v-if="!selectedNotification.read" 
                class="action-btn" 
                @click="markAsRead(selectedNotification.id)"
              >
                Mark as Read
              </button>
              <button 
                class="action-btn" 
                @click="prepareEditForm"
              >
                Edit
              </button>
              <button 
                class="action-btn delete-btn" 
                @click="isDeleteModalOpen = true"
              >
                Delete
              </button>
              
              <button 
                v-if="user && user.role === 'admin'" 
                class="action-btn forward-btn" 
                @click="isAgentDropdownOpen = true"
              >
                Forward
              </button>
            </div>
          </div>
          
          <!-- Notification details content -->
          <div class="detail-body">
            <div class="detail-field">
              <label>Type:</label>
              <span>{{ selectedNotification.event_type }}</span>
            </div>
            <div class="detail-field">
              <label>Stream URL:</label>
              <a 
                :href="selectedNotification.room_url" 
                target="_blank" 
                rel="noopener noreferrer"
                class="url-link"
              >
                {{ truncateUrl(selectedNotification.room_url) }}
              </a>
            </div>
            <div class="detail-field">
              <label>Timestamp:</label>
              <span>{{ formatTimestamp(selectedNotification.timestamp, true) }}</span>
            </div>
            <div class="detail-field">
              <label>Platform:</label>
              <span>{{ selectedNotification.details?.platform || 'Unknown' }}</span>
            </div>
            <div class="detail-field">
              <label>Streamer:</label>
              <span>{{ selectedNotification.details?.streamer_name || 'Unknown' }}</span>
            </div>
            <div v-if="selectedNotification.assigned_agent" class="detail-field">
              <label>Assigned Agent:</label>
              <span>{{ selectedNotification.assigned_agent }}</span>
            </div>
            
            <!-- Specific details based on notification type -->
            <div v-if="selectedNotification.event_type === 'object_detection'" class="type-details detection-details">
              <h3>Detection Details</h3>
              <div 
                v-if="selectedNotification.details?.detections?.length" 
                class="detections-grid"
              >
                <div 
                  v-for="(detection, index) in selectedNotification.details.detections" 
                  :key="index"
                  class="detection-item"
                >
                  <span class="detection-class">{{ detection.class }}</span>
                  <span class="detection-confidence">
                    {{ formatConfidence(detection.confidence) }}
                  </span>
                </div>
              </div>
              <div 
                v-if="selectedNotification.details?.annotated_image"
                class="detection-image"
              >
                <img 
                  :src="`data:image/png;base64,${selectedNotification.details.annotated_image}`"
                  alt="Detection Image"
                  @click="openImageModal(selectedNotification.details.annotated_image)"
                />
              </div>
            </div>
            
            <div v-if="selectedNotification.event_type === 'chat_detection'" class="type-details chat-details">
              <h3>Chat Details</h3>
              <div class="chat-message">
                <p>{{ selectedNotification.details?.message || 'No message content' }}</p>
              </div>
              <div 
                v-if="selectedNotification.details?.keywords?.length"
                class="keywords-list"
              >
                <h4>Flagged Keywords:</h4>
                <div class="keywords">
                  <span 
                    v-for="(keyword, index) in selectedNotification.details.keywords" 
                    :key="index"
                    class="keyword-tag"
                  >
                    {{ keyword }}
                  </span>
                </div>
              </div>
            </div>
            
            <div v-if="selectedNotification.event_type === 'audio_detection'" class="type-details audio-details">
              <h3>Audio Details</h3>
              <div class="audio-transcript">
                <h4>Transcript:</h4>
                <p>{{ selectedNotification.details?.transcript || 'No transcript available' }}</p>
              </div>
              <div v-if="selectedNotification.details?.keyword" class="keyword">
                <h4>Flagged Keyword:</h4>
                <span class="keyword-tag">{{ selectedNotification.details.keyword }}</span>
              </div>
            </div>
            
            <!-- Raw JSON (admin only) -->
            <div v-if="user && user.role === 'admin'" class="raw-json">
              <h3>Raw Data</h3>
              <div class="json-toggle" @click="showRawJson = !showRawJson">
                {{ showRawJson ? 'Hide' : 'Show' }} Raw JSON
              </div>
              <pre v-if="showRawJson">{{ JSON.stringify(selectedNotification.details, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Forward to agent modal -->
    <Teleport to="body">
      <div v-if="isAgentDropdownOpen" class="modal-overlay" @click="isAgentDropdownOpen = false">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3>Forward to Agent</h3>
            <button class="close-btn" @click="isAgentDropdownOpen = false">&times;</button>
          </div>
          <div class="modal-body">
            <div class="agent-list">
              <div 
                v-for="agent in agents" 
                :key="agent.id" 
                class="agent-item"
                @click="forwardNotification(agent.id)"
              >
                <div :class="['status-indicator', agent.online ? 'online' : 'offline']"></div>
                <div class="agent-info">
                  <div class="agent-name">{{ agent.username }}</div>
                  <div class="agent-email">{{ agent.email || 'No email' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
    
    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <div v-if="isDeleteModalOpen" class="modal-overlay" @click="isDeleteModalOpen = false">
        <div class="modal-container delete-modal" @click.stop>
          <div class="modal-header">
            <h3>Confirm Deletion</h3>
            <button class="close-btn" @click="isDeleteModalOpen = false">&times;</button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete {{ selectedNotification ? 'this notification' : 'all notifications' }}?</p>
            <p class="warning">This action cannot be undone.</p>
          </div>
          <div class="modal-footer">
            <button class="cancel-btn" @click="isDeleteModalOpen = false">Cancel</button>
            <button 
              class="confirm-btn" 
              @click="selectedNotification ? deleteNotification(selectedNotification.id) : deleteAllNotifications()"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </Teleport>
    
    <!-- Create/Edit notification modal -->
    <Teleport to="body">
      <div v-if="isFormModalOpen" class="modal-overlay" @click="isFormModalOpen = false">
        <div class="modal-container form-modal" @click.stop>
          <div class="modal-header">
            <h3>{{ isEditMode ? 'Edit' : 'Create' }} Notification</h3>
            <button class="close-btn" @click="isFormModalOpen = false">&times;</button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitNotificationForm">
              <div class="form-group">
                <label for="event_type">Event Type</label>
                <select id="event_type" v-model="notificationForm.event_type" required>
                  <option value="object_detection">Object Detection</option>
                  <option value="audio_detection">Audio Detection</option>
                  <option value="chat_detection">Chat Detection</option>
                  <option value="general">General</option>
                </select>
              </div>
              
              <div class="form-group">
                <label for="room_url">Stream URL</label>
                <input 
                  type="text" 
                  id="room_url" 
                  v-model="notificationForm.room_url" 
                  placeholder="https://example.com/stream"
                  required
                />
              </div>
              
              <div class="form-group">
                <label for="streamer_name">Streamer Name</label>
                <input 
                  type="text" 
                  id="streamer_name" 
                  v-model="notificationForm.details.streamer_name" 
                  placeholder="Streamer name"
                />
              </div>
              
              <div class="form-group">
                <label for="platform">Platform</label>
                <input 
                  type="text" 
                  id="platform" 
                  v-model="notificationForm.details.platform" 
                  placeholder="Platform name"
                />
              </div>
              
              <div class="form-group">
                <label for="message">Message</label>
                <textarea 
                  id="message" 
                  v-model="notificationForm.details.message" 
                  placeholder="Notification message"
                  rows="3"
                ></textarea>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button class="cancel-btn" @click="isFormModalOpen = false">Cancel</button>
            <button class="confirm-btn" @click="submitNotificationForm">
              {{ isEditMode ? 'Update' : 'Create' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
    
    <!-- Image viewer modal -->
    <Teleport to="body">
      <div v-if="imageModalSrc" class="modal-overlay" @click="imageModalSrc = null">
        <div class="image-modal" @click.stop>
          <button class="close-btn" @click="imageModalSrc = null">&times;</button>
          <img :src="`data:image/png;base64,${imageModalSrc}`" alt="Full size image" />
        </div>
      </div>
    </Teleport>
    
    <!-- Toast notifications -->
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div 
          v-for="toast in toasts" 
          :key="toast.id"
          class="toast"
          :class="toast.type"
        >
          {{ toast.message }}
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import axios from 'axios'
import { io } from 'socket.io-client'
import { formatDistanceToNow, parseISO } from 'date-fns'

export default {
  name: 'AdminNotificationsPage',
  setup() {
    // State
    const notifications = ref([])
    const selectedNotification = ref(null)
    const mainFilter = ref('All')
    const detectionSubFilter = ref('Visual')
    const loading = ref(true)
    const error = ref(null)
    const isMenuOpen = ref(false)
    const isDeleteModalOpen = ref(false)
    const isAgentDropdownOpen = ref(false)
    const isFormModalOpen = ref(false)
    const isEditMode = ref(false)
    const notificationForm = ref({
      event_type: 'general',
      room_url: '',
      details: {
        streamer_name: '',
        platform: '',
        message: ''
      }
    })
    const agents = ref([])
    const user = ref(null)
    const socket = ref(null)
    const socketInitialized = ref(false)
    const soundEnabled = ref(localStorage.getItem('notificationSound') !== 'false')
    const isDarkMode = ref(localStorage.getItem('darkMode') === 'true')
    const isMobile = ref(window.innerWidth < 768)
    const showRawJson = ref(false)
    const imageModalSrc = ref(null)
    const newNotificationIds = ref([])
    const toasts = ref([])
    let toastCounter = 0

    // Computed
    const filteredNotifications = computed(() => {
      let filtered = [...notifications.value]
      if (mainFilter.value === 'Unread') {
        filtered = filtered.filter(n => !n.read)
      } else if (mainFilter.value === 'Detections') {
        filtered = filtered.filter(n => {
          if (detectionSubFilter.value === 'Visual') return n.event_type === 'object_detection'
          if (detectionSubFilter.value === 'Audio') return n.event_type === 'audio_detection'
          if (detectionSubFilter.value === 'Chat') return n.event_type === 'chat_detection'
          return false
        })
      }
      return filtered
    })

    const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

    // Socket setup and handlers
    const setupSocketConnection = () => {
      try {
        socket.value = io('https://monitor-backend.jetcamstudio.com:5000/notifications', {
          path: '/ws',
          transports: ['websocket', 'polling'],
          reconnection: true,
          reconnectionAttempts: 5,
          reconnectionDelay: 1000,
          withCredentials: true,
          autoConnect: true
        })

        socket.value.on('connect', () => {
          socketInitialized.value = true
          console.log('Socket connected')
          showToast('Connected to notification server', 'success')
        })

        socket.value.on('connect_error', (err) => {
          console.error('Connection error:', err)
          setTimeout(setupSocketConnection, 5000)
        })

        socket.value.on('disconnect', () => {
          console.log('Socket disconnected')
        })

        socket.value.on('notification', handleNewNotification)
        socket.value.on('notification_update', handleNotificationUpdate)
      } catch (err) {
        console.error('Socket initialization failed:', err)
        setTimeout(setupSocketConnection, 5000)
      }
    }

    const handleNewNotification = (data) => {
      if (!notifications.value.some(n => n.id === data.id)) {
        notifications.value.unshift(data)
        newNotificationIds.value.push(data.id)
        setTimeout(() => {
          newNotificationIds.value = newNotificationIds.value.filter(id => id !== data.id)
        }, 5000)
        if (soundEnabled.value) playNotificationSound()
        showToast('New notification received', 'info')
      }
    }

    const handleNotificationUpdate = ({ id, type }) => {
      if (type === 'read') {
        const n = notifications.value.find(x => x.id === id)
        if (n) n.read = true
      } else if (type === 'deleted') {
        notifications.value = notifications.value.filter(x => x.id !== id)
        if (selectedNotification.value?.id === id) selectedNotification.value = null
      }
    }

    const safeSocketEmit = (event, data) => {
      if (socket.value?.connected) {
        socket.value.emit(event, data)
      } else {
        console.warn('Socket not connected, event queued:', event)
        // Optionally implement queue logic here
      }
    }

    // Core methods
    const fetchNotifications = async () => {
      loading.value = true
      error.value = null
      try {
        const res = await axios.get('/api/notifications')
        notifications.value = res.data
      } catch (err) {
        console.error('Error fetching notifications:', err)
        error.value = 'Failed to load notifications. Please try again.'
      } finally {
        loading.value = false
      }
    }

    const fetchAgents = async () => {
      try {
        const res = await axios.get('/api/agents')
        agents.value = res.data
      } catch {
        showToast('Failed to load agents', 'error')
      }
    }

    const fetchCurrentUser = async () => {
      try {
        const res = await axios.get('/api/session')
        user.value = res.data
      } catch {
        /* ignore */
      }
    }

    const handleMainFilterChange = (filter) => {
      mainFilter.value = filter
      if (selectedNotification.value) selectedNotification.value = null
    }

    const getNotificationColor = (n) => {
      if (n.event_type === 'object_detection') return '#e74c3c'
      if (n.event_type === 'audio_detection') return '#3498db'
      if (n.event_type === 'chat_detection') return '#f39c12'
      return '#2ecc71'
    }

    const getNotificationType = (n) => {
      if (n.event_type === 'object_detection') return 'Visual'
      if (n.event_type === 'audio_detection') return 'Audio'
      if (n.event_type === 'chat_detection') return 'Chat'
      return 'General'
    }

    const getNotificationMessage = (n) => {
      if (n.event_type === 'object_detection') {
        const det = n.details?.detections || []
        return det.length ? `Detected: ${det.map(d => d.class).join(', ')}` : 'Object detected'
      }
      if (n.event_type === 'audio_detection') {
        return n.details?.transcript?.substring(0,100) || 'Audio detected'
      }
      if (n.event_type === 'chat_detection') {
        return n.details?.message?.substring(0,100) || 'Chat message detected'
      }
      return n.details?.message || 'Notification received'
    }

    const getNotificationDetailTitle = () => {
      const n = selectedNotification.value
      if (!n) return ''
      if (n.event_type === 'object_detection') return 'Visual Detection'
      if (n.event_type === 'audio_detection') return 'Audio Detection'
      if (n.event_type === 'chat_detection') return 'Chat Detection'
      return 'Notification Details'
    }

    const formatTimestamp = (ts, detailed = false) => {
      if (!ts) return 'Unknown'
      try {
        const date = parseISO(ts)
        if (detailed) {
          return new Intl.DateTimeFormat('en-US', {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit', second: '2-digit'
          }).format(date)
        }
        return formatDistanceToNow(date, { addSuffix: true })
      } catch {
        return 'Invalid date'
      }
    }

    const formatConfidence = (c) => typeof c === 'number' ? `${Math.round(c * 100)}%` : 'N/A'
    const truncateUrl = (u) => u?.length > 40 ? u.slice(0,37) + '...' : u || ''

    const handleNotificationClick = (n) => {
      selectedNotification.value = n
      if (isMobile.value) {
        nextTick(() => {
          const el = document.querySelector('.details-panel')
          if (el) el.scrollIntoView({ behavior: 'smooth' })
        })
      }
    }

    const markAsRead = async (id) => {
      try {
        await axios.put(`/api/notifications/${id}/read`)
        const n = notifications.value.find(x => x.id === id)
        if (n) n.read = true
        showToast('Notification marked as read', 'success')
      } catch {
        showToast('Failed to mark as read', 'error')
      }
    }

    const markAllAsRead = async () => {
      try {
        await axios.put('/api/notifications/read-all')
        notifications.value.forEach(x => x.read = true)
        showToast('All notifications marked as read', 'success')
      } catch {
        showToast('Failed to mark all as read', 'error')
      }
    }

    const deleteNotification = async (id) => {
      try {
        await axios.delete(`/api/notifications/${id}`)
        notifications.value = notifications.value.filter(x => x.id !== id)
        if (selectedNotification.value?.id === id) selectedNotification.value = null
        isDeleteModalOpen.value = false
        showToast('Notification deleted', 'success')
      } catch {
        isDeleteModalOpen.value = false
        showToast('Failed to delete notification', 'error')
      }
    }

    const deleteAllNotifications = async () => {
      try {
        await axios.delete('/api/notifications')
        notifications.value = []
        selectedNotification.value = null
        isDeleteModalOpen.value = false
        showToast('All notifications deleted', 'success')
      } catch {
        isDeleteModalOpen.value = false
        showToast('Failed to delete all notifications', 'error')
      }
    }

    const prepareCreateForm = () => {
      isEditMode.value = false
      notificationForm.value = {
        event_type: 'general',
        room_url: '',
        details: { streamer_name: '', platform: '', message: '' }
      }
      isFormModalOpen.value = true
      isMenuOpen.value = false
    }

    const prepareEditForm = () => {
      if (!selectedNotification.value) return
      isEditMode.value = true
      notificationForm.value = {
        event_type: selectedNotification.value.event_type,
        room_url: selectedNotification.value.room_url,
        details: { ...selectedNotification.value.details }
      }
      isFormModalOpen.value = true
    }

    const submitNotificationForm = async () => {
      try {
        if (isEditMode.value) {
          await axios.put(`/api/notifications/${selectedNotification.value.id}`, notificationForm.value)
          const idx = notifications.value.findIndex(x => x.id === selectedNotification.value.id)
          if (idx !== -1) {
            notifications.value[idx] = { ...notifications.value[idx], ...notificationForm.value }
            selectedNotification.value = notifications.value[idx]
          }
          showToast('Notification updated', 'success')
        } else {
          const res = await axios.post('/api/notifications', notificationForm.value)
          notifications.value.unshift(res.data.notification)
          showToast('Notification created', 'success')
        }
        isFormModalOpen.value = false
      } catch {
        showToast('Failed to save notification', 'error')
      }
    }

    const forwardNotification = async (agentId) => {
      if (!selectedNotification.value) return
      try {
        await axios.post(`/api/notifications/${selectedNotification.value.id}/assign`, { agent_id: agentId })
        const agent = agents.value.find(a => a.id === agentId)
        selectedNotification.value.assigned_agent = agent?.username
        const n = notifications.value.find(x => x.id === selectedNotification.value.id)
        if (n) n.assigned_agent = agent?.username
        isAgentDropdownOpen.value = false
        showToast(`Forwarded to ${agent?.username || 'agent'}`, 'success')
      } catch {
        isAgentDropdownOpen.value = false
        showToast('Failed to forward notification', 'error')
      }
    }

    const toggleSound = () => {
      soundEnabled.value = !soundEnabled.value
      localStorage.setItem('notificationSound', soundEnabled.value)
      showToast(`Sound ${soundEnabled.value ? 'enabled' : 'disabled'}`, 'info')
      isMenuOpen.value = false
    }

    const toggleDarkMode = () => {
      isDarkMode.value = !isDarkMode.value
      localStorage.setItem('darkMode', isDarkMode.value)
    }

    const openImageModal = (src) => {
      imageModalSrc.value = src
    }

    const playNotificationSound = () => {
      const audio = new Audio('/notification.mp3')
      audio.play().catch(() => {})
    }

    const showToast = (msg, type = 'info') => {
      const id = toastCounter++
      toasts.value.push({ id, message: msg, type })
      setTimeout(() => {
        toasts.value = toasts.value.filter(t => t.id !== id)
      }, 3000)
    }

    const handleResize = () => {
      isMobile.value = window.innerWidth < 768
    }

    // Lifecycle
    onMounted(() => {
      fetchNotifications()
      fetchAgents()
      fetchCurrentUser()
      setupSocketConnection()
      window.addEventListener('resize', handleResize)
      window.addEventListener('online', setupSocketConnection)
    })

    onBeforeUnmount(() => {
      if (socket.value) {
        socket.value.off('notification', handleNewNotification)
        socket.value.off('notification_update', handleNotificationUpdate)
        socket.value.disconnect()
      }
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('online', setupSocketConnection)
    })

    return {
      notifications,
      selectedNotification,
      mainFilter,
      detectionSubFilter,
      loading,
      error,
      filteredNotifications,
      unreadCount,
      isMenuOpen,
      isDeleteModalOpen,
      isAgentDropdownOpen,
      isFormModalOpen,
      isEditMode,
      notificationForm,
      agents,
      user,
      soundEnabled,
      isDarkMode,
      isMobile,
      showRawJson,
      imageModalSrc,
      newNotificationIds,
      toasts,
      fetchNotifications,
      handleMainFilterChange,
      getNotificationColor,
      getNotificationType,
      getNotificationMessage,
      getNotificationDetailTitle,
      formatTimestamp,
      formatConfidence,
      truncateUrl,
      handleNotificationClick,
      markAsRead,
      markAllAsRead,
      deleteNotification,
      deleteAllNotifications,
      prepareCreateForm,
      prepareEditForm,
      submitNotificationForm,
      forwardNotification,
      toggleSound,
      toggleDarkMode,
      openImageModal,
      showToast,
      safeSocketEmit
    }
  }
}
</script>


<style scoped>
.notifications-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f8f9fa;
  color: #333;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Dark Mode */
.dark-mode {
  background-color: #121212;
  color: #e4e4e4;
}

.dark-mode .top-bar,
.dark-mode .sub-filters,
.dark-mode .notifications-panel,
.dark-mode .details-panel,
.dark-mode .modal-container {
  background-color: #1e1e1e;
  border-color: #333;
}

.dark-mode .dropdown-menu {
  background-color: #2a2a2a;
  border-color: #444;
}

.dark-mode .notification-card {
  background-color: #2a2a2a;
  border-color: #444;
}

.dark-mode .notification-card.selected {
  background-color: #333;
}

.dark-mode .notification-card.unread {
  background-color: #252835;
}

.dark-mode .notification-card:hover {
  background-color: #333;
}

.dark-mode .empty-state,
.dark-mode .empty-detail,
.dark-mode .error-state,
.dark-mode .state-container {
  background-color: #2a2a2a;
  color: #ccc;
}

.dark-mode .detection-item,
.dark-mode .keyword-tag {
  background-color: #333;
}

.dark-mode a {
  color: #4dabf7;
}

.dark-mode .modal-overlay {
  background-color: rgba(0, 0, 0, 0.7);
}

/* Top Navigation Bar */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background-color: #fff;
  border-bottom: 1px solid #e1e4e8;
  z-index: 10;
  position: relative;
}

.filter-tabs {
  display: flex;
  gap: 8px;
}

.tab-btn {
  padding: 6px 12px;
  border: none;
  background: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: #555;
  transition: all 0.2s ease;
  position: relative;
}

.tab-btn:hover {
  background-color: #f0f0f0;
}

.tab-btn.active {
  background-color: #ebf5fe;
  color: #0366d6;
}

.dark-mode .tab-btn:hover {
  background-color: #333;
}

.dark-mode .tab-btn.active {
  background-color: #1a365d;
  color: #4dabf7;
}

.badge {
  position: absolute;
  top: -6px;
  right: -8px;
  background-color: #e74c3c;
  color: white;
  border-radius: 12px;
  padding: 0 6px;
  font-size: 12px;
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background-color: #f0f0f0;
}

.dark-mode .icon-btn:hover {
  background-color: #333;
}

.icon {
  font-size: 18px;
}

.dropdown-menu {
  position: absolute;
  right: 20px;
  top: 60px;
  background-color: white;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 180px;
  z-index: 20;
}

.dropdown-menu button {
  display: block;
  width: 100%;
  text-align: left;
  padding: 10px 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

.dropdown-menu button:hover {
  background-color: #f6f8fa;
}

.dropdown-menu button:disabled {
  color: #a0a0a0;
  cursor: not-allowed;
}

.dark-mode .dropdown-menu button:hover {
  background-color: #333;
}

/* Sub-filters */
.sub-filters {
  display: flex;
  padding: 8px 20px;
  background-color: #fff;
  border-bottom: 1px solid #e1e4e8;
  gap: 8px;
}

.sub-filter-btn {
  padding: 4px 10px;
  border: 1px solid #e1e4e8;
  background: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sub-filter-btn:hover {
  background-color: #f6f8fa;
}

.sub-filter-btn.active {
  background-color: #0366d6;
  color: white;
  border-color: #0366d6;
}

.dark-mode .sub-filter-btn {
  border-color: #444;
}

.dark-mode .sub-filter-btn:hover {
  background-color: #333;
}

.dark-mode .sub-filter-btn.active {
  background-color: #1a365d;
  border-color: #1a365d;
}

/* Content Area */
.content-area {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.notifications-panel {
  width: 40%;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e1e4e8;
  background-color: #fff;
  position: relative;
}

.details-panel {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #fff;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e1e4e8;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.panel-header .count {
  color: #888;
  margin-left: 4px;
  font-weight: normal;
}

/* Notifications List */
.notification-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.notification-card {
  display: flex;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background-color: #fff;
  border: 1px solid #e1e4e8;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.notification-card:hover {
  background-color: #f6f8fa;
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.notification-card.selected {
  background-color: #f0f6ff;
  border-color: #79b8ff;
}

.notification-card.unread {
  background-color: #f0f7ff;
  border-left-width: 3px;
}

.notification-card.read {
  opacity: 0.8;
}

.dark-mode .notification-card.selected {
  background-color: #1a365d;
  border-color: #4dabf7;
}

.notification-indicator {
  width: 4px;
  border-radius: 2px;
  margin-right: 12px;
  background-color: #0366d6;
}

.notification-content {
  flex: 1;
  min-width: 0; /* For proper text truncation */
}

.notification-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.notification-type {
  font-size: 12px;
  font-weight: 600;
  color: #0366d6;
}

.notification-time {
  font-size: 12px;
  color: #888;
}

.notification-message {
  font-size: 14px;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notification-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #888;
}

.notification-source {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-confidence {
  color: #2ecc71;
  font-weight: 500;
}

.notification-actions {
  display: none;
  position: absolute;
  right: 8px;
  top: 8px;
}

.notification-card:hover .notification-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: none;
  background-color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background-color: #f0f0f0;
}

.action-btn.read-btn:hover {
  background-color: #d4edda;
  color: #28a745;
}

.action-btn.delete-btn:hover {
  background-color: #f8d7da;
  color: #dc3545;
}

.dark-mode .action-btn {
  background-color: rgba(30, 30, 30, 0.8);
}

.dark-mode .action-btn:hover {
  background-color: #333;
}

.dark-mode .action-btn.read-btn:hover {
  background-color: #1e4620;
  color: #4ade80;
}

.dark-mode .action-btn.delete-btn:hover {
  background-color: #4c1d24;
  color: #f87171;
}

/* New notification animation */
.notification-card.new-notification {
  animation: pulse 2s ease-in-out;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(66, 153, 225, 0.5); }
  70% { box-shadow: 0 0 0 10px rgba(66, 153, 225, 0); }
  100% { box-shadow: 0 0 0 0 rgba(66, 153, 225, 0); }
}

/* Empty/Error States */
.state-container,
.empty-state,
.empty-detail,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  height: 100%;
  color: #888;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.error-state {
  color: #dc3545;
}

.error-state button {
  margin-top: 12px;
  padding: 6px 12px;
  background-color: #f8d7da;
  color: #dc3545;
  border: 1px solid #dc3545;
  border-radius: 4px;
  cursor: pointer;
}

.dark-mode .error-state button {
  background-color: #4c1d24;
  color: #f87171;
  border-color: #f87171;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: #0366d6;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 12px;
}

.dark-mode .loading-spinner {
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #4dabf7;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Detail Section */
.detail-content {
  padding: 20px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #e1e4e8;
  padding-bottom: 12px;
}

.detail-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.detail-header .back-btn {
  padding: 6px 12px;
  background: none;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-right: 12px;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.detail-actions button {
  padding: 6px 12px;
  background: none;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.detail-actions button:hover {
  background-color: #f6f8fa;
}

.detail-actions .delete-btn {
  color: #dc3545;
  border-color: #dc3545;
}

.detail-actions .delete-btn:hover {
  background-color: #f8d7da;
}

.detail-actions .forward-btn {
  color: #0366d6;
  border-color: #0366d6;
}

.detail-actions .forward-btn:hover {
  background-color: #f0f7ff;
}

.dark-mode .detail-header .back-btn,
.dark-mode .detail-actions button {
  border-color: #444;
}

.dark-mode .detail-actions button:hover {
  background-color: #333;
}

.dark-mode .detail-actions .delete-btn {
  color: #f87171;
  border-color: #f87171;
}

.dark-mode .detail-actions .delete-btn:hover {
  background-color: #4c1d24;
}

.dark-mode .detail-actions .forward-btn {
  color: #4dabf7;
  border-color: #4dabf7;
}

.dark-mode .detail-actions .forward-btn:hover {
  background-color: #1a365d;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-field {
  display: flex;
  margin-bottom: 8px;
}

.detail-field label {
  width: 100px;
  font-weight: 500;
  color: #666;
}

.dark-mode .detail-field label {
  color: #aaa;
}

.url-link {
  color: #0366d6;
  text-decoration: none;
}

.url-link:hover {
  text-decoration: underline;
}

.type-details {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e1e4e8;
}

.type-details h3 {
  font-size: 16px;
  font-weight: 600;
  margin-top: 0;
  margin-bottom: 12px;
}

.type-details h4 {
  font-size: 14px;
  font-weight: 500;
  margin-top: 12px;
  margin-bottom: 8px;
  color: #666;
}

.dark-mode .type-details h4 {
  color: #aaa;
}

.detections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}

.detection-item {
  padding: 8px;
  border-radius: 4px;
  background-color: #f6f8fa;
  font-size: 13px;
  display: flex;
  flex-direction: column;
}

.detection-class {
  font-weight: 500;
}

.detection-confidence {
  color: #2ecc71;
  font-size: 12px;
  margin-top: 4px;
}

.detection-image {
  margin-top: 12px;
  max-width: 100%;
  border-radius: 4px;
  overflow: hidden;
}

.detection-image img {
  max-width: 100%;
  height: auto;
  cursor: zoom-in;
  transition: transform 0.2s ease;
}

.detection-image img:hover {
  transform: scale(1.02);
}

.audio-transcript p,
.chat-message p {
  background-color: #f6f8fa;
  padding: 12px;
  border-radius: 4px;
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
}

.dark-mode .audio-transcript p,
.dark-mode .chat-message p {
  background-color: #2a2a2a;
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.keyword-tag {
  background-color: #e1e4e8;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  display: inline-block;
}

.raw-json {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e1e4e8;
}

.raw-json h3 {
  font-size: 16px;
  font-weight: 600;
  margin-top: 0;
  margin-bottom: 12px;
}

.json-toggle {
  display: inline-block;
  padding: 4px 8px;
  background-color: #f6f8fa;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  margin-bottom: 8px;
}

.dark-mode .json-toggle {
  background-color: #2a2a2a;
  border-color: #444;
}

.raw-json pre {
  background-color: #f6f8fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
}

.dark-mode .raw-json pre {
  background-color: #2a2a2a;
}

/* Modals */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  width: 400px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e1e4e8;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e1e4e8;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
}

.cancel-btn,
.confirm-btn {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  border: 1px solid #e1e4e8;
}

.cancel-btn {
  background-color: white;
}

.confirm-btn {
  background-color: #0366d6;
  color: white;
  border-color: #0366d6;
}

.delete-modal .confirm-btn {
  background-color: #dc3545;
  border-color: #dc3545;
}

.warning {
  color: #dc3545;
  font-weight: 500;
}

.dark-mode .modal-container {
  background-color: #1e1e1e;
}

.dark-mode .cancel-btn {
  background-color: #2a2a2a;
}

.dark-mode .confirm-btn {
  background-color: #0f4c81;
}

.dark-mode .delete-modal .confirm-btn {
  background-color: #a02f3e;
}

/* Form styling */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 14px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  font-size: 14px;
}

.dark-mode .form-group input,
.dark-mode .form-group select,
.dark-mode .form-group textarea {
  background-color: #2a2a2a;
  color: #e4e4e4;
  border-color: #444;
}

/* Agent list in forward modal */
.agent-list {
  max-height: 300px;
  overflow-y: auto;
}

.agent-item {
  display: flex;
  align-items: center;
  padding: 10px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-radius: 4px;
}

.agent-item:hover {
  background-color: #f6f8fa;
}

.dark-mode .agent-item:hover {
  background-color: #333;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 10px;
  background-color: #ccc;
}

.status-indicator.online {
  background-color: #2ecc71;
}

.status-indicator.offline {
  background-color: #e74c3c;
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-weight: 500;
  font-size: 14px;
}

.agent-email {
  font-size: 12px;
  color: #888;
}

/* Image modal */
.image-modal {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-modal img {
  max-width: 100%;
  max-height: 90vh;
  border-radius: 4px;
}

.image-modal .close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Toast notifications */
.toast-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toast {
  padding: 12px 16px;
  border-radius: 4px;
  color: white;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  min-width: 250px;
}

.toast.success {
  background-color: #2ecc71;
}

.toast.error {
  background-color: #e74c3c;
}

.toast.info {
  background-color: #3498db;
}

.toast.warning {
  background-color: #f39c12;
}

/* Animations */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(50px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(50px);
}

/* Responsive Design */
@media (max-width: 768px) {
  .content-area {
    flex-direction: column;
  }
  
  .notifications-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e1e4e8;
    max-height: 50vh;
  }
  
  .detail-actions {
    flex-wrap: wrap;
  }
  
  .top-bar {
    flex-wrap: wrap;
  }
  
  .filter-tabs {
    width: 100%;
    margin-bottom: 8px;
    justify-content: space-between;
  }
  
  .action-buttons {
    margin-left: auto;
  }
  
  .notification-card {
    padding: 8px;
  }
  
  .notification-message {
    font-size: 13px;
  }
  
  .notification-meta,
  .notification-time {
    font-size: 11px;
  }
}
</style>