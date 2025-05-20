<template>
  <div class="notifications-page" :data-theme="isDarkMode ? 'dark' : 'light'">
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
          <span v-if="tab === 'Unread' && unreadCount > 0" class="badge">{{ unreadCount }}</span>
        </button>
      </div>
      
      <div class="action-buttons">
        <button class="icon-btn refresh-btn" @click="fetchNotifications" title="Refresh">
          <font-awesome-icon icon="sync" class="icon" />
        </button>
        <button class="icon-btn menu-btn" @click="toggleMenu" title="More Actions">
          <font-awesome-icon icon="ellipsis-v" class="icon" />
        </button>
      </div>
      
      <!-- Dropdown menu -->
      <div v-if="isMenuOpen" class="dropdown-menu">
        <button @click="prepareCreateForm">Create Notification</button>
        <button 
          @click="markAllAsRead"
          :disabled="unreadCount === 0 || markingAllRead"
          :class="{ 'disabled': unreadCount === 0 || markingAllRead }"
        >
          <font-awesome-icon v-if="markingAllRead" icon="spinner" spin class="icon" />
          Mark All as Read
        </button>
        <button 
          @click="markAllAsUnread"
          :disabled="notifications.length === 0 || markingAllUnread"
          :class="{ 'disabled': notifications.length === 0 || markingAllUnread }"
        >
          <font-awesome-icon v-if="markingAllUnread" icon="spinner" spin class="icon" />
          Mark All as Unread
        </button>
        <button 
          @click="confirmDeleteAll"
          :disabled="notifications.length === 0 || deletingAll"
          :class="{ 'disabled': notifications.length === 0 || deletingAll }"
        >
          <font-awesome-icon v-if="deletingAll" icon="spinner" spin class="icon" />
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
          <button class="refresh-button" @click="fetchNotifications">
            <font-awesome-icon icon="sync" class="icon" /> Try Again
          </button>
        </div>
        <div v-else-if="filteredNotifications.length === 0" class="empty-state">
          <font-awesome-icon icon="bell-slash" class="empty-icon" />
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
                'selected': selectedNotification?.id === notification.id,
                'new-notification': newNotificationIds.includes(notification.id),
                'low-priority': notification.details?.priority === 'low'
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
                    {{ notification.details?.streamer_name || 'Unknown' }} | 
                    {{ notification.details?.assigned_agent || 'None' }}
                  </span>
                  <span 
                    v-if="notification.event_type === 'object_detection' && notification.details?.detections?.length" 
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
                  <font-awesome-icon icon="check" />
                </button>
                <button 
                  v-if="notification.read" 
                  class="action-btn unread-btn" 
                  @click.stop="markAsUnread(notification.id)"
                  title="Mark as Unread"
                >
                  <font-awesome-icon icon="envelope-open" />
                </button>
                <button 
                  class="action-btn delete-btn" 
                  @click.stop="deleteNotification(notification.id)"
                  title="Delete"
                >
                  <font-awesome-icon icon="trash" />
                </button>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </div>
      
      <!-- Right panel: Notification details -->
      <div class="details-panel" v-if="selectedNotification || isMobile">
        <div v-if="!selectedNotification && isMobile" class="empty-detail">
          <font-awesome-icon icon="clipboard" class="empty-icon" />
          <p>Select a notification to view details</p>
        </div>
        
        <div v-else-if="selectedNotification" class="detail-content">
          <div class="detail-header">
            <button v-if="isMobile" class="back-btn" @click="selectedNotification = null">
              <font-awesome-icon icon="arrow-left" />
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
                v-if="selectedNotification.read" 
                class="action-btn" 
                @click="markAsUnread(selectedNotification.id)"
              >
                Mark as Unread
              </button>
              <button 
                class="action-btn" 
                @click="prepareEditForm"
                v-if="user?.role === 'admin'"
              >
                Edit
              </button>
              <button 
                class="action-btn delete-btn" 
                @click="confirmDelete(selectedNotification.id)"
              >
                Delete
              </button>
              <button 
                v-if="user?.role === 'admin'" 
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
              <label>Priority:</label>
              <span>{{ selectedNotification.details?.priority?.toUpperCase() || 'NORMAL' }}</span>
            </div>
            <div class="detail-field">
              <label>Stream URL:</label>
              <a 
                :href="selectedNotification.room_url" 
                target="_blank" 
                rel="noopener noreferrer"
                class="url-link"
                v-if="selectedNotification.room_url"
              >
                {{ truncateUrl(selectedNotification.room_url) }}
              </a>
              <span v-else>N/A</span>
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
            <div class="detail-field">
              <label>Assigned Agent:</label>
              <span>{{ selectedNotification.details?.assigned_agent || 'None' }}</span>
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
            <div v-if="user?.role === 'admin'" class="raw-json">
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
            <button class="close-btn" @click="isAgentDropdownOpen = false">
              <font-awesome-icon icon="times" />
            </button>
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
            <button class="close-btn" @click="isDeleteModalOpen = false">
              <font-awesome-icon icon="times" />
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete {{ deleteAll ? 'all notifications' : 'this notification' }}?</p>
            <p class="warning">This action cannot be undone.</p>
          </div>
          <div class="modal-footer">
            <button class="cancel-btn" @click="isDeleteModalOpen = false">Cancel</button>
            <button 
              class="confirm-btn" 
              @click="deleteAll ? deleteAllNotifications() : deleteNotification(deleteId)"
              :disabled="deletingAll || deletingSingle"
            >
              <font-awesome-icon v-if="deletingAll || deletingSingle" icon="spinner" spin class="icon" />
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
            <button class="close-btn" @click="isFormModalOpen = false">
              <font-awesome-icon icon="times" />
            </button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitNotificationForm">
              <div class="form-group">
                <label for="event_type">Event Type</label>
                <select id="event_type" v-model="notificationForm.event_type" required>
                  <option value="object_detection">Object Detection</option>
                  <option value="audio_detection">Audio Detection</option>
                  <option value="chat_detection">Chat Detection</option>
                  <option value="stream_status_updated">Stream Status Updated</option>
                  <option value="general">General</option>
                </select>
              </div>
              <div class="form-group" v-if="notificationForm.event_type === 'stream_status_updated'">
                <label for="priority">Priority</label>
                <select id="priority" v-model="notificationForm.details.priority" required>
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                </select>
              </div>
              <div class="form-group">
                <label for="room_url">Stream URL</label>
                <input 
                  type="url" 
                  id="room_url" 
                  v-model="notificationForm.room_url" 
                  placeholder="https://example.com/stream"
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
            <button class="confirm-btn" @click="submitNotificationForm" :disabled="submittingForm">
              <font-awesome-icon v-if="submittingForm" icon="spinner" spin class="icon" />
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
          <button class="close-btn" @click="imageModalSrc = null">
            <font-awesome-icon icon="times" />
          </button>
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
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import { faSync, faEllipsisV, faBellSlash, faClipboard, faArrowLeft, faCheck, faTrash, faTimes, faSpinner, faEnvelopeOpen } from '@fortawesome/free-solid-svg-icons'

library.add(faSync, faEllipsisV, faBellSlash, faClipboard, faArrowLeft, faCheck, faTrash, faTimes, faSpinner, faEnvelopeOpen)

export default {
  name: 'AdminNotificationsPage',
  components: { FontAwesomeIcon },
  props: {
    user: Object
  },
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
    const deleteAll = ref(false)
    const deleteId = ref(null)
    const isAgentDropdownOpen = ref(false)
    const isFormModalOpen = ref(false)
    const isEditMode = ref(false)
    const submittingForm = ref(false)
    const markingAllRead = ref(false)
    const markingAllUnread = ref(false)
    const deletingAll = ref(false)
    const deletingSingle = ref(false)
    const notificationForm = ref({
      event_type: 'general',
      room_url: '',
      details: {
        streamer_name: '',
        platform: '',
        message: '',
        priority: 'normal'
      }
    })
    const agents = ref([])
    const socket = ref(null)
    const socketInitialized = ref(false)
    const soundEnabled = ref(localStorage.getItem('notificationSound') !== 'false')
    const isDarkMode = ref(localStorage.getItem('darkMode') === 'true' || window.matchMedia('(prefers-color-scheme: dark)').matches)
    const isMobile = ref(window.innerWidth < 768)
    const showRawJson = ref(false)
    const imageModalSrc = ref(null)
    const newNotificationIds = ref([])
    const toasts = ref([])
    let toastCounter = 0
    let reconnectAttempts = 0
    const maxReconnectAttempts = 3
    const reconnectDelayMs = 2000
    let lastReconnectTime = 0
    const minReconnectInterval = 5000

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
      return filtered.sort((a, b) => {
        // Prioritize unread and high-priority notifications
        if (!a.read && b.read) return -1
        if (a.read && !b.read) return 1
        if (a.details?.priority === 'normal' && b.details?.priority === 'low') return -1
        if (a.details?.priority === 'low' && b.details?.priority === 'normal') return 1
        return new Date(b.timestamp) - new Date(a.timestamp)
      })
    })

    const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

    // Socket setup
    const setupSocketConnection = () => {
      const now = Date.now()
      if (now - lastReconnectTime < minReconnectInterval) {
        console.log('Rate limited: Too many connection attempts')
        return
      }
      lastReconnectTime = now

      if (reconnectAttempts >= maxReconnectAttempts) {
        console.log('Max reconnection attempts reached')
        showToast('Unable to connect to notification server', 'error')
        return
      }

      try {
        socket.value = io('https://monitor-backend.jetcamstudio.com:5000/notifications', {
          path: '/ws',
          transports: ['websocket', 'polling'],
          reconnection: false,
          withCredentials: true,
          autoConnect: true
        })

        socket.value.on('connect', () => {
          socketInitialized.value = true
          reconnectAttempts = 0
          console.log('Socket connected')
          showToast('Connected to notification server', 'success')
        })

        socket.value.on('connect_error', (err) => {
          console.error('Connection error:', err)
          reconnectAttempts++
          if (reconnectAttempts < maxReconnectAttempts) {
            const delay = reconnectDelayMs * Math.pow(2, reconnectAttempts - 1)
            setTimeout(setupSocketConnection, delay)
          } else {
            showToast('Failed to connect to notification server', 'error')
          }
        })

        socket.value.on('disconnect', () => {
          console.log('Socket disconnected')
          socketInitialized.value = false
          if (reconnectAttempts < maxReconnectAttempts) {
            const delay = reconnectDelayMs * Math.pow(2, reconnectAttempts)
            setTimeout(setupSocketConnection, delay)
          }
        })

        socket.value.on('notification', handleNewNotification)
        socket.value.on('notification_update', handleNotificationUpdate)
      } catch (err) {
        console.error('Socket initialization failed:', err)
        reconnectAttempts++
        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = reconnectDelayMs * Math.pow(2, reconnectAttempts - 1)
          setTimeout(setupSocketConnection, delay)
        }
      }
    }

    const safeSocketEmit = (event, data) => {
      if (!socket.value || !socket.value.connected) {
        console.warn('Socket not connected, event dropped:', event)
        return false
      }
      try {
        socket.value.emit(event, data)
        return true
      } catch (err) {
        console.error('Socket emit error:', err)
        return false
      }
    }

    const handleNewNotification = (data) => {
      if (!notifications.value.some(n => n.id === data.id)) {
        notifications.value.unshift(data)
        newNotificationIds.value.push(data.id)
        setTimeout(() => {
          newNotificationIds.value = newNotificationIds.value.filter(id => id !== data.id)
        }, 5000)
        if (soundEnabled.value && data.details?.priority !== 'low') {
          playNotificationSound()
        }
        showToast('New notification received', 'info')
      }
    }

    const handleNotificationUpdate = ({ id, type }) => {
      if (type === 'read') {
        const n = notifications.value.find(x => x.id === id)
        if (n) n.read = true
      } else if (type === 'unread') {
        const n = notifications.value.find(x => x.id === id)
        if (n) n.read = false
      } else if (type === 'deleted') {
        notifications.value = notifications.value.filter(x => x.id !== id)
        if (selectedNotification.value?.id === id) selectedNotification.value = null
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

    const handleMainFilterChange = (filter) => {
      mainFilter.value = filter
      if (selectedNotification.value) selectedNotification.value = null
    }

    const getNotificationColor = (n) => {
      if (n.event_type === 'object_detection') return 'rgb(var(--danger-rgb))'
      if (n.event_type === 'audio_detection') return 'rgb(var(--info-rgb))'
      if (n.event_type === 'chat_detection') return 'rgb(var(--warning-rgb))'
      if (n.event_type === 'stream_status_updated') return 'rgb(var(--secondary-rgb))'
      return 'rgb(var(--success-rgb))'
    }

    const getNotificationType = (n) => {
      if (n.event_type === 'object_detection') return 'Visual'
      if (n.event_type === 'audio_detection') return 'Audio'
      if (n.event_type === 'chat_detection') return 'Chat'
      if (n.event_type === 'stream_status_updated') return 'Stream Status'
      return 'General'
    }

    const getNotificationMessage = (n) => {
      const agent = n.details?.assigned_agent || 'None'
      if (n.event_type === 'object_detection') {
        const det = n.details?.detections || []
        return det.length ? `Detected: ${det.map(d => d.class).join(', ')} (Agent: ${agent})` : `Object detected (Agent: ${agent})`
      }
      if (n.event_type === 'audio_detection') {
        return `${n.details?.transcript?.substring(0, 100) || 'Audio detected'} (Agent: ${agent})`
      }
      if (n.event_type === 'chat_detection') {
        return `${n.details?.message?.substring(0, 100) || 'Chat message detected'} (Agent: ${agent})`
      }
      if (n.event_type === 'stream_status_updated') {
        return `${n.details?.message || 'Stream status updated'} (Agent: ${agent})`
      }
      return `${n.details?.message || 'Notification received'} (Agent: ${agent})`
    }

    const getNotificationDetailTitle = () => {
      const n = selectedNotification.value
      if (!n) return ''
      if (n.event_type === 'object_detection') return 'Visual Detection'
      if (n.event_type === 'audio_detection') return 'Audio Detection'
      if (n.event_type === 'chat_detection') return 'Chat Detection'
      if (n.event_type === 'stream_status_updated') return 'Stream Status Update'
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
    const truncateUrl = (u) => u?.length > 40 ? u.slice(0, 37) + '...' : u || 'N/A'

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
        if (n) {
          n.read = true
          safeSocketEmit('notification_update', { id, type: 'read' })
        }
        showToast('Notification marked as read', 'success')
      } catch {
        showToast('Failed to mark as read', 'error')
      }
    }

    const markAsUnread = async (id) => {
      try {
        await axios.put(`/api/notifications/${id}/unread`)
        const n = notifications.value.find(x => x.id === id)
        if (n) {
          n.read = false
          safeSocketEmit('notification_update', { id, type: 'unread' })
        }
        showToast('Notification marked as unread', 'success')
      } catch {
        showToast('Failed to mark as unread', 'error')
      }
    }

    const markAllAsRead = async () => {
      if (markingAllRead.value) return
      markingAllRead.value = true
      try {
        await axios.put('/api/notifications/read-all')
        notifications.value.forEach(n => {
          if (!n.read) {
            n.read = true
            safeSocketEmit('notification_update', { id: n.id, type: 'read' })
          }
        })
        showToast('All notifications marked as read', 'success')
      } catch {
        showToast('Failed to mark all as read', 'error')
      } finally {
        markingAllRead.value = false
      }
    }

    const markAllAsUnread = async () => {
      if (markingAllUnread.value) return
      markingAllUnread.value = true
      try {
        await axios.put('/api/notifications/unread-all')
        notifications.value.forEach(n => {
          if (n.read) {
            n.read = false
            safeSocketEmit('notification_update', { id: n.id, type: 'unread' })
          }
        })
        showToast('All notifications marked as unread', 'success')
      } catch {
        showToast('Failed to mark all as unread', 'error')
      } finally {
        markingAllUnread.value = false
      }
    }

    const confirmDelete = (id) => {
      deleteId.value = id
      deleteAll.value = false
      isDeleteModalOpen.value = true
    }

    const confirmDeleteAll = () => {
      deleteAll.value = true
      isDeleteModalOpen.value = true
    }

    const deleteNotification = async (id) => {
      if (deletingSingle.value) return
      deletingSingle.value = true
      try {
        await axios.delete(`/api/notifications/${id}`)
        notifications.value = notifications.value.filter(x => x.id !== id)
        if (selectedNotification.value?.id === id) selectedNotification.value = null
        safeSocketEmit('notification_update', { id, type: 'deleted' })
        showToast('Notification deleted', 'success')
      } catch {
        showToast('Failed to delete notification', 'error')
      } finally {
        deletingSingle.value = false
        isDeleteModalOpen.value = false
      }
    }

    const deleteAllNotifications = async () => {
      if (deletingAll.value) return
      deletingAll.value = true
      try {
        await axios.delete('/api/notifications/delete-all')
        const deletedIds = notifications.value.map(n => n.id)
        notifications.value = []
        selectedNotification.value = null
        deletedIds.forEach(id => safeSocketEmit('notification_update', { id, type: 'deleted' }))
        showToast('All notifications deleted', 'success')
      } catch {
        showToast('Failed to delete all notifications', 'error')
      } finally {
        deletingAll.value = false
        isDeleteModalOpen.value = false
      }
    }

    const prepareCreateForm = () => {
      isEditMode.value = false
      notificationForm.value = {
        event_type: 'general',
        room_url: '',
        details: { streamer_name: '', platform: '', message: '', priority: 'normal' }
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
        details: { 
          ...selectedNotification.value.details,
          priority: selectedNotification.value.details?.priority || 'normal'
        }
      }
      isFormModalOpen.value = true
    }

    const submitNotificationForm = async () => {
      if (submittingForm.value) return
      submittingForm.value = true
      try {
        if (isEditMode.value) {
          const res = await axios.put(`/api/notifications/${selectedNotification.value.id}`, notificationForm.value)
          const idx = notifications.value.findIndex(x => x.id === selectedNotification.value.id)
          if (idx !== -1) {
            notifications.value[idx] = { ...notifications.value[idx], ...res.data }
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
      } finally {
        submittingForm.value = false
      }
    }

    const forwardNotification = async (agentId) => {
      if (!selectedNotification.value) return
      try {
        await axios.post(`/api/notifications/${selectedNotification.value.id}/assign`, { agent_id: agentId })
        const agent = agents.value.find(a => a.id === agentId)
        selectedNotification.value.details.assigned_agent = agent?.username
        const n = notifications.value.find(x => x.id === selectedNotification.value.id)
        if (n) n.details.assigned_agent = agent?.username
        showToast(`Forwarded to ${agent?.username || 'agent'}`, 'success')
      } catch {
        showToast('Failed to forward notification', 'error')
      } finally {
        isAgentDropdownOpen.value = false
      }
    }

    const toggleSound = () => {
      soundEnabled.value = !soundEnabled.value
      localStorage.setItem('notificationSound', soundEnabled.value)
      showToast(`Sound ${soundEnabled.value ? 'enabled' : 'disabled'}`, 'info')
      isMenuOpen.value = false
    }

    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value
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
      deleteAll,
      deleteId,
      isAgentDropdownOpen,
      isFormModalOpen,
      isEditMode,
      submittingForm,
      markingAllRead,
      markingAllUnread,
      deletingAll,
      deletingSingle,
      notificationForm,
      agents,
      soundEnabled,
      isDarkMode,
      isMobile,
      showRawJson,
      imageModalSrc,
      newNotificationIds,
      toasts,
      fetchNotifications,
      fetchAgents,
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
      markAsUnread,
      markAllAsRead,
      markAllAsUnread,
      confirmDelete,
      confirmDeleteAll,
      deleteNotification,
      deleteAllNotifications,
      prepareCreateForm,
      prepareEditForm,
      submitNotificationForm,
      forwardNotification,
      toggleSound,
      toggleMenu,
      openImageModal,
      showToast,
      safeSocketEmit
    }
  }
}
</script>

<style scoped>
/* Use AdminDashboard's CSS variables */
:root {
  --primary-rgb: 96, 165, 250;
  --secondary-rgb: 156, 163, 175;
  --success-rgb: 16, 185, 129;
  --danger-rgb: 239, 68, 68;
  --warning-rgb: 245, 158, 11;
  --info-rgb: 14, 165, 233;
  --bg-color: #f8fafc;
  --text-color: #1e293b;
  --input-bg: #ffffff;
  --input-border: #e2e8f0;
  --hover-bg: #f1f5f9;
  --error-bg: #fef2f2;
  --error-border: #fecaca;
}

[data-theme="dark"] {
  --primary-rgb: 96, 165, 250;
  --secondary-rgb: 156, 163, 175;
  --success-rgb: 34, 197, 94;
  --danger-rgb: 248, 113, 113;
  --warning-rgb: 251, 191, 36;
  --info-rgb: 56, 189, 248;
  --bg-color: #121212;
  --text-color: #f0f0f0;
  --input-bg: #141313;
  --input-border: #333;
  --hover-bg: #333;
  --error-bg: #4c1d24;
  --error-border: #f87171;
}

.notifications-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  margin-left: 50px;
}

/* Top Navigation Bar */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 18px;
  background-color: var(--input-bg);
  border-bottom: 1px solid var(--input-border);
  z-index: 10;
  position: relative;
}

.filter-tabs {
  display: flex;
  gap: 8px;
}

.tab-btn {
  padding: 8px 16px;
  border: none;
  background: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  color: var(--text-color);
  transition: all 0.2s ease;
  position: relative;
}

.tab-btn:hover {
  background-color: var(--hover-bg);
  color: rgb(var(--primary-rgb));
}

.tab-btn.active {
  background-color: rgba(var(--primary-rgb), 0.1);
  color: rgb(var(--primary-rgb));
}

.badge {
  position: absolute;
  top: -6px;
  right: -8px;
  background-color: rgb(var(--danger-rgb));
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
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: none;
  background-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-color);
}

.icon-btn:hover {
  background-color: var(--hover-bg);
  color: rgb(var(--primary-rgb));
}

.icon {
  font-size: 18px;
}

.dropdown-menu {
  position: absolute;
  right: 20px;
  top: 60px;
  background-color: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 180px;
  z-index: 20;
}

.dropdown-menu button {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  text-align: left;
  padding: 10px 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-color);
  transition: background-color 0.2s ease;
}

.dropdown-menu button:hover {
  background-color: var(--hover-bg);
}

.dropdown-menu button:disabled, .dropdown-menu button.disabled {
  color: var(--secondary-rgb);
  cursor: not-allowed;
  opacity: 0.6;
}

/* Sub-filters */
.sub-filters {
  display: flex;
  padding: 8px 20px;
  background-color: var(--input-bg);
  border-bottom: 1px solid var(--input-border);
  gap: 8px;
}

.sub-filter-btn {
  padding: 4px 10px;
  border: 1px solid var(--input-border);
  background: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  color: var(--text-color);
  transition: all 0.2s ease;
}

.sub-filter-btn:hover {
  background-color: var(--hover-bg);
}

.sub-filter-btn.active {
  background-color: rgb(var(--primary-rgb));
  color: white;
  border-color: rgb(var(--primary-rgb));
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
  border-right: 1px solid var(--input-border);
  background-color: var(--input-bg);
}

.details-panel {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--input-bg);
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--input-border);
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.panel-header .count {
  color: rgb(var(--secondary-rgb));
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
  background-color: var(--input-bg);
  border: 1px solid var(--input-border);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.notification-card:hover {
  background-color: var(--hover-bg);
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.notification-card.selected {
  background-color: rgba(var(--primary-rgb), 0.1);
  border-color: rgb(var(--primary-rgb));
}

.notification-card.unread {
  background-color: rgba(var(--primary-rgb), 0.05);
  border-left: 3px solid rgb(var(--primary-rgb));
}

.notification-card.read {
  opacity: 0.85;
}

.notification-card.low-priority {
  opacity: 0.7;
  font-style: italic;
}

.notification-card.low-priority .notification-message {
  color: rgb(var(--secondary-rgb));
}

.notification-indicator {
  width: 4px;
  border-radius: 2px;
  margin-right: 12px;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.notification-type {
  font-size: 13px;
  font-weight: 600;
  color: rgb(var(--primary-rgb));
}

.notification-time {
  font-size: 13px;
  color: rgb(var(--secondary-rgb));
}

.notification-message {
  font-size: 15px;
  margin-bottom: 4px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-color);
}

.notification-meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: rgb(var(--secondary-rgb));
}

.notification-source {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-confidence {
  color: rgb(var(--success-rgb));
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
  width: auto;
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
  background-color: var(--hover-bg);
}

.action-btn.read-btn:hover {
  background-color: rgba(var(--success-rgb), 0.1);
  color: rgb(var(--success-rgb));
}

.action-btn.delete-btn:hover {
  background-color: rgba(var(--danger-rgb), 0.1);
  color: rgb(var(--danger-rgb));
}

[data-theme="dark"] .action-btn {
  background-color: rgba(30, 30, 30, 0.8);
}

/* New notification animation */
.notification-card.new-notification {
  animation: pulse 2s ease-in-out;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(var(--primary-rgb), 0.5); }
  70% { box-shadow: 0 0 0 10px rgba(var(--primary-rgb), 0); }
  100% { box-shadow: 0 0 0 0 rgba(var(--primary-rgb), 0); }
}

/* States */
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
  color: rgb(var(--secondary-rgb));
  font-size: 15px;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.error-state {
  background-color: var(--error-bg);
  border: 1px solid var(--error-border);
  border-radius: 8px;
}

.error-state p {
  color: rgb(var(--danger-rgb));
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  background-color: rgb(var(--primary-rgb));
  color: white;
  font-weight: 500;
  cursor: pointer;
  border: none;
  font-size: 14px;
  transition: all 0.2s ease;
}

.refresh-button:hover {
  opacity: 0.9;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(var(--primary-rgb), 0.1);
  border-radius: 50%;
  border-top-color: rgb(var(--primary-rgb));
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 12px;
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
  border-bottom: 1px solid var(--input-border);
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
  border: 1px solid var(--input-border);
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-color);
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.detail-actions button {
  padding: 6px 12px;
  background: none;
  border: 1px solid var(--input-border);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  color: var(--text-color);
  transition: all 0.2s ease;
  width: max-content;
}

.detail-actions button:hover {
  background-color: var(--hover-bg);
}

.detail-actions .delete-btn {
  color: rgb(var(--danger-rgb));
  border-color: rgb(var(--danger-rgb));
  width: max-content;
}

.detail-actions .delete-btn:hover {
  background-color: rgba(var(--danger-rgb), 0.1);
}

.detail-actions .forward-btn {
  color: rgb(var(--primary-rgb));
  border-color: rgb(var(--primary-rgb));
  width: max-content;
}

.detail-actions .forward-btn:hover {
  background-color: rgba(var(--primary-rgb), 0.1);
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
  color: rgb(var(--secondary-rgb));
  font-size: 15px;
}

.url-link {
  color: rgb(var(--primary-rgb));
  text-decoration: none;
  font-size: 15px;
}

.url-link:hover {
  text-decoration: underline;
}

.type-details {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--input-border);
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
  color: rgb(var(--secondary-rgb));
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
  background-color: var(--hover-bg);
  font-size: 14px;
  display: flex;
  flex-direction: column;
}

.detection-class {
  font-weight: 500;
  color: var(--text-color);
}

.detection-confidence {
  color: rgb(var(--success-rgb));
  font-size: 13px;
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
  background-color: var(--hover-bg);
  padding: 12px;
  border-radius: 4px;
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-color);
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.keyword-tag {
  background-color: rgba(var(--warning-rgb), 0.2);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 13px;
  color: rgb(var(--warning-rgb));
}

.raw-json {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--input-border);
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
  background-color: var(--hover-bg);
  border: 1px solid var(--input-border);
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  margin-bottom: 8px;
  color: var(--text-color);
}

.raw-json pre {
  background-color: var(--hover-bg);
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
  max-height: 300px;
  color: var(--text-color);
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
  background-color: var(--input-bg);
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
  border-bottom: 1px solid var(--input-border);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--input-border);
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: rgb(var(--secondary-rgb));
}

.cancel-btn,
.confirm-btn {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  border: 1px solid var(--input-border);
}

.cancel-btn {
  background-color: var(--input-bg);
  color: var(--text-color);
}

.cancel-btn:hover {
  background-color: var(--hover-bg);
}

.confirm-btn {
  background-color: rgb(var(--primary-rgb));
  color: white;
  border-color: rgb(var(--primary-rgb));
}

.confirm-btn:hover {
  opacity: 0.9;
}

.confirm-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.delete-modal .confirm-btn {
  background-color: rgb(var(--danger-rgb));
  border-color: rgb(var(--danger-rgb));
}

.delete-modal .confirm-btn:hover {
  opacity: 0.9;
}

.warning {
  color: rgb(var(--danger-rgb));
  font-weight: 500;
  font-size: 14px;
}

/* Form styling */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 15px;
  color: var(--text-color);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--input-border);
  border-radius: 4px;
  font-size: 15px;
  background-color: var(--input-bg);
  color: var(--text-color);
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: rgb(var(--primary-rgb));
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
}

/* Agent list */
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
  background-color: var(--hover-bg);
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 10px;
  background-color: rgb(var(--secondary-rgb));
}

.status-indicator.online {
  background-color: rgb(var(--success-rgb));
}

.status-indicator.offline {
  background-color: rgb(var(--danger-rgb));
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-weight: 500;
  font-size: 15px;
  color: var(--text-color);
}

.agent-email {
  font-size: 13px;
  color: rgb(var(--secondary-rgb));
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
  font-size: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  min-width: 250px;
}

.toast.success {
  background-color: rgb(var(--success-rgb));
}

.toast.error {
  background-color: rgb(var(--danger-rgb));
}

.toast.info {
  background-color: rgb(var(--info-rgb));
}

.toast.warning {
  background-color: rgb(var(--warning-rgb));
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
  .notifications-page {
    margin-left: 0;
  }
  
  .content-area {
    flex-direction: column;
  }
  
  .notifications-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--input-border);
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
    font-size: 14px;
  }
  
  .notification-meta,
  .notification-time {
    font-size: 12px;
  }
}
</style>