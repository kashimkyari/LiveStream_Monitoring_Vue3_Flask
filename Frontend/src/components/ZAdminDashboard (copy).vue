<template>
  <div class="admin-container" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <!-- Sidebar Navigation -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>Admin Panel</h2>
        <div class="user-info">
          <span>{{ user.username }}</span>
          <span class="user-role">{{ user.role }}</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
          class="nav-button"
        >
          <span class="nav-icon">
            <font-awesome-icon :icon="tab.icon" />
          </span>
          <span class="nav-text">{{ tab.label }}</span>
        </button>
      </nav>
      <div class="sidebar-footer">
        <div class="status-indicator">
          <div class="status-dot" :class="{ online: isOnline }"></div>
          <span>{{ isOnline ? 'Online' : 'Offline' }}</span>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading dashboard data...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="hasError" class="error-state">
        <h3>Something went wrong</h3>
        <p>{{ errorMessage }}</p>
        <button @click="fetchDashboardData" class="refresh-button">
          <font-awesome-icon icon="sync" /> Retry
        </button>
      </div>

      <!-- Content -->
      <template v-else>
        <!-- Dashboard Tab -->
        <section v-if="activeTab === 'dashboard'" class="dashboard-tab">
          <div class="dashboard-header">
            <h2>Stream Monitoring Dashboard</h2>
            <div class="stats-container">
              <div class="stat-card">
                <div class="stat-value">{{ dashboardStats.ongoing_streams }}</div>
                <div class="stat-label">Active Streams</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ dashboardStats.total_detections }}</div>
                <div class="stat-label">Total Detections</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ dashboardStats.active_agents }}</div>
                <div class="stat-label">Active Agents</div>
              </div>
            </div>
          </div>

          <div class="stream-grid">
            <div
              v-for="stream in streams"
              :key="stream.id"
              class="stream-card"
              @click="openStreamDetails(stream)"
            >
              <div class="stream-thumbnail">
                <VideoPlayer
                  :platform="stream.platform.toLowerCase()"
                  :streamer-uid="stream.streamer_uid"
                  :streamer-name="stream.streamer_username"
                  :alerts="getStreamDetections(stream.room_url)"
                  thumbnail-only
                />
                <div v-if="hasDetections(stream)" class="alert-badge">
                  {{ detectionCount(stream) }}
                </div>
              </div>
              <div class="stream-info">
                <h3 class="stream-title">{{ stream.streamer_username }}</h3>
                <div class="stream-meta">
                  <span class="platform-tag" :class="stream.platform.toLowerCase()">
                    {{ stream.platform }}
                  </span>
                  <span class="agent-name">
                    {{ stream.agent?.username || 'Unassigned' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Streams Management Tab -->
        <section v-if="activeTab === 'streams'" class="streams-tab">
          <div class="tab-header">
            <h2>Stream Management</h2>
            <button @click="showCreateStreamModal = true" class="create-button">
              <font-awesome-icon icon="plus" /> Add Stream
            </button>
          </div>
          <div class="streams-table">
            <table>
              <thead>
                <tr>
                  <th>Streamer</th>
                  <th>Platform</th>
                  <th>URL</th>
                  <th>Assigned Agent</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stream in allStreams" :key="stream.id">
                  <td>{{ stream.streamer_username }}</td>
                  <td>
                    <span class="platform-tag" :class="stream.platform.toLowerCase()">
                      {{ stream.platform }}
                    </span>
                  </td>
                  <td>
                    <a :href="stream.room_url" target="_blank" rel="noopener noreferrer">
                      {{ stream.room_url }}
                    </a>
                  </td>
                  <td>{{ stream.agent?.username || 'Unassigned' }}</td>
                  <td>
                    <span class="status-badge" :class="{ active: stream.is_live }">
                      {{ stream.is_live ? 'Live' : 'Offline' }}
                    </span>
                  </td>
                  <td class="actions">
                    <button @click="editStream(stream)" class="icon-button">
                      <font-awesome-icon icon="edit" />
                    </button>
                    <button @click="confirmDeleteStream(stream)" class="icon-button danger">
                      <font-awesome-icon icon="trash" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- Agents Management Tab -->
        <section v-if="activeTab === 'agents'" class="agents-tab">
          <div class="tab-header">
            <h2>Agent Management</h2>
            <button @click="showCreateAgentModal = true" class="create-button">
              <font-awesome-icon icon="plus" /> Add Agent
            </button>
          </div>
          <div class="agents-table">
            <table>
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Assigned Streams</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="agent in agents" :key="agent.id">
                  <td>{{ agent.username }}</td>
                  <td>{{ agent.firstname }} {{ agent.lastname }}</td>
                  <td>{{ agent.email }}</td>
                  <td>{{ agent.phonenumber }}</td>
                  <td>{{ agent.assignments?.length || 0 }}</td>
                  <td>
                    <span class="status-badge" :class="{ online: agent.online }">
                      {{ agent.online ? 'Online' : 'Offline' }}
                    </span>
                  </td>
                  <td class="actions">
                    <button @click="editAgent(agent)" class="icon-button">
                      <font-awesome-icon icon="edit" />
                    </button>
                    <button @click="confirmDeleteAgent(agent)" class="icon-button danger">
                      <font-awesome-icon icon="trash" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- Notifications Tab -->
        <section v-if="activeTab === 'notifications'" class="notifications-tab">
          <div class="tab-header">
            <h2>Detection Notifications</h2>
            <div class="notification-actions">
              <button @click="markAllAsRead" class="action-button">
                <font-awesome-icon icon="envelope-open" /> Mark All as Read
              </button>
              <button @click="fetchNotifications" class="action-button">
                <font-awesome-icon icon="sync" /> Refresh
              </button>
            </div>
          </div>
          <div class="notifications-list">
            <div 
              v-for="notification in notifications" 
              :key="notification.id"
              :class="['notification-item', notification.read ? 'read' : 'unread']"
            >

            <div class="notifications-header">
      <h3>Notifications ({{ notifications.length }})</h3>
      <div class="notifications-actions">
        <button 
          class="mark-all-read"
          @click="markAllAsRead"
          :disabled="!hasUnreadNotifications"
        >
          Mark All as Read
        </button>
        <button 
          class="delete-all"
          @click="deleteAllNotifications"
          :disabled="notifications.length === 0"
        >
          Delete All
        </button>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
    </div>
    
    <div class="filters">
      <button 
        v-for="tab in ['All', 'Unread', 'Detections']" 
        :key="tab"
        :class="['filter-btn', { active: mainFilter === tab }]"
        @click="setMainFilter(tab)"
      >
        {{ tab }}
      </button>
      
      <div class="sub-filters" v-if="mainFilter === 'Detections'">
        <button 
          v-for="subTab in ['Visual', 'Audio', 'Chat']" 
          :key="subTab"
          :class="['sub-filter-btn', { active: detectionSubFilter === subTab }]"
          @click="detectionSubFilter = subTab"
        >
          {{ subTab }}
        </button>
      </div>
    </div>
    
    <div class="loading-container" v-if="loading">
      <div class="loading-spinner"></div>
      <p>Loading notifications...</p>
    </div>
    
    <div class="error-message" v-else-if="error">{{ error }}</div>
    
    <div class="empty-state" v-else-if="notifications.length === 0">
      <div class="empty-icon">🔔</div>
      <p>No notifications to display</p>
    </div>
    
    <div class="notifications-list" v-else>
      <div 
        v-for="notification in notifications" 
        :key="notification.id"
        :class="['notification-item', { 
          'read': notification.read, 
          'unread': !notification.read,
          'selected': selectedNotification && selectedNotification.id === notification.id 
        }]"
        @click="handleNotificationClick(notification)"
      >
        <div 
          class="notification-indicator"
          :style="{ backgroundColor: getNotificationColor(notification) }"
        ></div>
        <div class="notification-content">
          <div class="notification-message">
            {{ getNotificationMessage(notification) }}
          </div>
          <div class="notification-meta">
            <span class="notification-time">
              {{ formatTimestamp(notification.timestamp) }}
            </span>
            <span class="notification-confidence" v-if="notification.event_type === 'object_detection'">
              {{ formatConfidence(getDetectionConfidence(notification)) }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Notification Detail View -->
    <div class="notification-detail-container" v-if="selectedNotification">
      <div class="detail-header">
        <h3>{{ getDetailTitle() }}</h3>
        <div class="detail-actions">
          <button 
            v-if="!selectedNotification.read"
            class="mark-read-btn" 
            @click="markAsRead(selectedNotification.id)"
          >
            Mark as Read
          </button>
          <button class="delete-btn" @click="deleteNotification(selectedNotification.id)">
            Delete
          </button>
        </div>
      </div>
      
      <div class="detail-timestamp">
        Detected at: {{ formatTimestamp(selectedNotification.timestamp) }}
      </div>
      
      <!-- Detection content depends on notification type -->
      <div class="detection-content" v-if="selectedNotification.event_type === 'object_detection'">
        <div class="image-gallery" v-if="hasImages">
          <div class="image-card" v-if="selectedNotification.details.annotated_image">
            <img
              :src="formatImage(selectedNotification.details.annotated_image)"
              alt="Annotated Detection"
              class="detection-image"
            />
            <div class="image-label">Annotated Image</div>
          </div>
          <div class="image-card" v-if="selectedNotification.details.captured_image">
            <img
              :src="selectedNotification.details.captured_image"
              alt="Captured Image"
              class="detection-image"
            />
            <div class="image-label">Captured Image</div>
          </div>
        </div>
        
        <div class="detected-objects" v-if="hasDetections">
          <h4>Detected Objects</h4>
          <div 
            v-for="(detection, index) in selectedNotification.details.detections" 
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
      
      <div class="audio-detection-content" v-else-if="selectedNotification.event_type === 'audio_detection'">
        <p>Detected keywords: <strong>{{ selectedNotification.details.keywords?.join(', ') }}</strong></p>
        <p>Transcript: {{ selectedNotification.details.transcript }}</p>
      </div>
      
      <div class="chat-detection-content" v-else-if="selectedNotification.event_type === 'chat_detection'">
        <p>Detected chat keyword: <strong>{{ selectedNotification.details.keyword }}</strong></p>
        <p class="chat-excerpt">{{ selectedNotification.details.ocr_text }}</p>
      </div>
      
      <div class="stream-created-content" v-else-if="selectedNotification.event_type === 'stream_created'">
        <p>A new stream has been created by <strong>{{ selectedNotification.details.streamer_name || 'Unknown' }}</strong>.</p>
        <p v-if="selectedNotification.details.stream_url">
          Stream URL: <a :href="selectedNotification.details.stream_url" target="_blank" rel="noopener noreferrer">
            {{ selectedNotification.details.stream_url }}
          </a>
        </p>
      </div>
      
      <div v-else>
        <p>{{ selectedNotification.message }}</p>
      </div>
    </div>
              <div class="notification-header">
                <span class="notification-type">{{ formatEventType(notification.event_type) }}</span>
                <span class="notification-time">{{ formatTime(notification.timestamp) }}</span>
                <span v-if="!notification.read" class="unread-badge"></span>
              </div>
              <div class="notification-content">
                <p>{{ getNotificationMessage(notification) }}</p>
                <div v-if="notification.details.detections" class="detection-details">
                  <div 
                    v-for="(detection, idx) in notification.details.detections" 
                    :key="idx"
                    class="detection-item"
                  >
                    <span class="detection-class">{{ detection.class }}</span>
                    <span class="detection-confidence">{{ (detection.confidence * 100).toFixed(1) }}%</span>
                  </div>
                </div>
              </div>
              <div class="notification-actions">
                <button 
                  v-if="!notification.read"
                  @click="markAsRead(notification.id)"
                  class="small-button"
                >
                  Mark as Read
                </button>
                <button 
                  v-if="user.role === 'admin' && notification.details.assigned_agent === 'Unassigned'"
                  @click="showForwardModal(notification)"
                  class="small-button primary"
                >
                  Forward to Agent
                </button>
              </div>
            </div>
          </div>
        </section>
      </template>
    </main>

    <!-- Stream Details Modal -->
    <div v-if="selectedStream" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <button class="modal-close" @click="closeModal">
          <font-awesome-icon icon="times" />
        </button>
        <div class="modal-header">
          <h3>{{ selectedStream.streamer_username }}</h3>
          <div class="stream-tags">
            <span class="tag platform">{{ selectedStream.platform }}</span>
            <span class="tag agent">{{ selectedStream.agent?.username || 'Unassigned' }}</span>
            <span class="tag stream-id">ID: {{ selectedStream.id }}</span>
          </div>
        </div>
        <div class="modal-body">
          <div class="stream-player-container">
            <VideoPlayer 
              :platform="selectedStream.platform.toLowerCase()"
              :streamer-uid="selectedStream.streamer_uid"
              :streamer-name="selectedStream.streamer_username"
              :static-thumbnail="selectedStream.static_thumbnail"
              :alerts="getStreamDetections(selectedStream.room_url)"
            />
          </div>
          <div v-if="hasDetections(selectedStream)" class="detections-section">
            <h4>Recent Detections</h4>
            <div class="detections-grid">
              <div 
                v-for="(alert, index) in getStreamDetections(selectedStream.room_url)" 
                :key="index"
                class="detection-card"
              >
                <img :src="alert.image_url" alt="Detection" class="detection-image" />
                <div class="detection-info">
                  <div class="detection-class">{{ alert.class }}</div>
                  <div class="detection-confidence">
                    {{ (alert.confidence * 100).toFixed(1) }}% confidence
                  </div>
                  <div class="detection-time">{{ formatTime(alert.timestamp) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="assignAgent(selectedStream)" class="action-button">
            Assign Agent
          </button>
          <button @click="refreshStream(selectedStream)" class="action-button">
            Refresh Stream
          </button>
        </div>
      </div>
    </div>

    <!-- Create Stream Modal -->
    <div v-if="showCreateStreamModal" class="modal-overlay" @click.self="showCreateStreamModal = false">
      <div class="modal-content">
        <button class="modal-close" @click="showCreateStreamModal = false">
          <font-awesome-icon icon="times" />
        </button>
        <div class="modal-header">
          <h3>Add New Stream</h3>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createStream">
            <div class="form-group">
              <label for="platform">Platform</label>
              <select id="platform" v-model="newStream.platform" required>
                <option value="">Select Platform</option>
                <option value="Chaturbate">Chaturbate</option>
                <option value="Stripchat">Stripchat</option>
              </select>
            </div>
            <div class="form-group">
              <label for="room_url">Room URL</label>
              <input 
                id="room_url" 
                v-model="newStream.room_url" 
                type="url" 
                placeholder="https://chaturbate.com/username" 
                required
              />
            </div>
            <div class="form-group">
              <label for="stream_agent">Assign Agent (Optional)</label>
              <select id="stream_agent" v-model="newStream.agent_id">
                <option value="">Unassigned</option>
                <option v-for="agent in agents" :key="agent.id" :value="agent.id">
                  {{ agent.username }}
                </option>
              </select>
            </div>
            <div class="form-actions">
              <button type="button" @click="showCreateStreamModal = false" class="cancel-button">
                Cancel
              </button>
              <button type="submit" class="submit-button">
                Create Stream
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Create Agent Modal -->
    <div v-if="showCreateAgentModal" class="modal-overlay" @click.self="showCreateAgentModal = false">
      <div class="modal-content">
        <button class="modal-close" @click="showCreateAgentModal = false">
          <font-awesome-icon icon="times" />
        </button>
        <div class="modal-header">
          <h3>Add New Agent</h3>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createAgent">
            <div class="form-row">
              <div class="form-group">
                <label for="username">Username</label>
                <input id="username" v-model="newAgent.username" required />
              </div>
              <div class="form-group">
                <label for="password">Password</label>
                <input id="password" v-model="newAgent.password" type="password" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="firstname">First Name</label>
                <input id="firstname" v-model="newAgent.firstname" required />
              </div>
              <div class="form-group">
                <label for="lastname">Last Name</label>
                <input id="lastname" v-model="newAgent.lastname" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="email">Email</label>
                <input id="email" v-model="newAgent.email" type="email" required />
              </div>
              <div class="form-group">
                <label for="phonenumber">Phone Number</label>
                <input id="phonenumber" v-model="newAgent.phonenumber" type="tel" required />
              </div>
            </div>
            <div class="form-actions">
              <button type="button" @click="showCreateAgentModal = false" class="cancel-button">
                Cancel
              </button>
              <button type="submit" class="submit-button">
                Create Agent
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Forward Notification Modal -->
    <div v-if="forwardModal.show" class="modal-overlay" @click.self="forwardModal.show = false">
      <div class="modal-content">
        <button class="modal-close" @click="forwardModal.show = false">
          <font-awesome-icon icon="times" />
        </button>
        <div class="modal-header">
          <h3>Forward Notification</h3>
        </div>
        <div class="modal-body">
          <div class="notification-preview">
            <h4>{{ formatEventType(forwardModal.notification.event_type) }}</h4>
            <p>{{ getNotificationMessage(forwardModal.notification) }}</p>
            <div v-if="forwardModal.notification.details.detections" class="detection-preview">
              <div 
                v-for="(detection, idx) in forwardModal.notification.details.detections.slice(0, 3)" 
                :key="idx"
                class="detection-item"
              >
                <span class="detection-class">{{ detection.class }}</span>
                <span class="detection-confidence">{{ (detection.confidence * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label for="forward-agent">Select Agent</label>
            <select 
              id="forward-agent" 
              v-model="forwardModal.agent_id"
              required
            >
              <option value="">Select Agent</option>
              <option 
                v-for="agent in agents" 
                :key="agent.id" 
                :value="agent.id"
              >
                {{ agent.username }} ({{ agent.assignments?.length || 0 }} assignments)
              </option>
            </select>
          </div>
          <div class="form-group">
            <label for="forward-message">Additional Message (Optional)</label>
            <textarea 
              id="forward-message" 
              v-model="forwardModal.message"
              placeholder="Add any additional instructions for the agent..."
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button 
            @click="forwardNotification" 
            class="submit-button"
            :disabled="!forwardModal.agent_id"
          >
            Forward Notification
          </button>
        </div>
      </div>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="confirmationModal.show" class="modal-overlay" @click.self="confirmationModal.show = false">
      <div class="modal-content small">
        <div class="modal-header">
          <h3>{{ confirmationModal.title }}</h3>
        </div>
        <div class="modal-body">
          <p>{{ confirmationModal.message }}</p>
        </div>
        <div class="modal-footer">
          <button @click="confirmationModal.show = false" class="cancel-button">
            Cancel
          </button>
          <button @click="confirmAction" class="submit-button danger">
            {{ confirmationModal.actionText }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import { 
  faTachometerAlt, 
  faStream, 
  faUsers,
  faBell,
  faFlag, 
  faSync, 
  faTimes,
  faPlus,
  faEdit,
  faTrash,
  faEnvelopeOpen,
  faCircle
} from '@fortawesome/free-solid-svg-icons'
import VideoPlayer from './VideoPlayer.vue'

library.add(
  faTachometerAlt, faStream, faUsers, faBell, faFlag, 
  faSync, faTimes, faPlus, faEdit, faTrash, faEnvelopeOpen, faCircle
)

export default {
  name: 'AdminDashboard',
  components: {
    FontAwesomeIcon,
    VideoPlayer
  },
  setup() {
    const router = useRouter()
    
    // State
    const isDarkTheme = ref(true)
    const activeTab = ref('dashboard')
    const loading = ref(true)
    const hasError = ref(false)
    const errorMessage = ref('')
    const isOnline = ref(true)
    const user = ref({})
    
    // Data
    const dashboardStats = ref({
      ongoing_streams: 0,
      total_detections: 0,
      active_agents: 0
    })
    const streams = ref([])
    const allStreams = ref([])
    const agents = ref([])
    const notifications = ref([])
    const detections = ref({})
    
    // Modals
    const selectedStream = ref(null)
    const showCreateStreamModal = ref(false)
    const showCreateAgentModal = ref(false)
    const forwardModal = ref({
      show: false,
      notification: null,
      agent_id: null,
      message: ''
    })
    const confirmationModal = ref({
      show: false,
      title: '',
      message: '',
      action: null,
      actionText: 'Confirm'
    })
    
    // Form data
    const newStream = ref({
      platform: '',
      room_url: '',
      agent_id: null
    })
    const newAgent = ref({
      username: '',
      password: '',
      firstname: '',
      lastname: '',
      email: '',
      phonenumber: ''
    })
    
    // Tabs configuration
    const tabs = ref([
      { id: 'dashboard', label: 'Dashboard', icon: 'tachometer-alt' },
      { id: 'streams', label: 'Streams', icon: 'stream' },
      { id: 'agents', label: 'Agents', icon: 'users' },
      { id: 'notifications', label: 'Notifications', icon: 'bell' }
    ])
    
    // Computed properties
    const unreadNotifications = computed(() => {
      return notifications.value.filter(n => !n.read).length
    })
    
    // Methods
    const fetchDashboardData = async () => {
      try {
        loading.value = true
        hasError.value = false
        
        // Fetch user data
        const userResponse = await axios.get('/api/session')
        if (userResponse.data.logged_in) {
          user.value = userResponse.data.user
        } else {
          router.push('/login')
          return
        }
        
        // Fetch dashboard stats and streams
        const [dashboardResponse, streamsResponse, agentsResponse, notificationsResponse] = await Promise.all([
          axios.get('/api/dashboard'),
          axios.get('/api/streams'),
          axios.get('/api/agents'),
          axios.get('/api/notifications')
        ])
        
        dashboardStats.value = {
          ongoing_streams: dashboardResponse.data.ongoing_streams,
          total_detections: 0, // Will be calculated from notifications
          active_agents: agentsResponse.data.filter(a => a.online).length
        }
        
        streams.value = dashboardResponse.data.streams
        allStreams.value = streamsResponse.data
        agents.value = agentsResponse.data
        notifications.value = notificationsResponse.data
        
        // Calculate total detections from notifications
        dashboardStats.value.total_detections = notifications.value.reduce((total, notification) => {
          if (notification.event_type === 'object_detection') {
            return total + (notification.details.detections?.length || 0)
          }
          return total
        }, 0)
        
        // Process detections
        processDetections()
        
        loading.value = false
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        hasError.value = true
        errorMessage.value = error.response?.data?.message || 'Failed to load dashboard data'
        loading.value = false
      }
    }
    
    const processDetections = () => {
      // Group detections by stream URL
      const groupedDetections = {}
      
      notifications.value.forEach(notification => {
        if (notification.event_type === 'object_detection' && notification.details.detections) {
          const streamUrl = notification.room_url
          if (!groupedDetections[streamUrl]) {
            groupedDetections[streamUrl] = []
          }
          
          notification.details.detections.forEach(detection => {
            groupedDetections[streamUrl].push({
              ...detection,
              timestamp: new Date(notification.timestamp)
            })
          })
        }
      })
      
      detections.value = groupedDetections
    }
    
    const getStreamDetections = (roomUrl) => {
      return detections.value[roomUrl] || []
    }
    
    const hasDetections = (stream) => {
      return getStreamDetections(stream.room_url).length > 0
    }
    
    const detectionCount = (stream) => {
      return getStreamDetections(stream.room_url).length
    }
    
    const openStreamDetails = (stream) => {
      selectedStream.value = stream
    }
    
    const closeModal = () => {
      selectedStream.value = null
    }
    
    const assignAgent = async (stream) => {
      try {
        // In a real implementation, you would show a modal to select an agent
        // and then make an API call to assign them
        const agentId = prompt('Enter agent ID to assign:')
        if (agentId) {
          await axios.post('/api/assign', {
            agent_id: agentId,
            stream_id: stream.id
          })
          fetchDashboardData()
          closeModal()
        }
      } catch (error) {
        console.error('Failed to assign agent:', error)
        alert('Failed to assign agent: ' + (error.response?.data?.message || error.message))
      }
    }
    
    const refreshStream = async (stream) => {
      try {
        let response
        if (stream.platform.toLowerCase() === 'chaturbate') {
          response = await axios.post('/api/streams/refresh/chaturbate', {
            room_slug: stream.room_url.split('/').pop()
          })
        } else if (stream.platform.toLowerCase() === 'stripchat') {
          response = await axios.post('/api/streams/refresh/stripchat', {
            room_url: stream.room_url
          })
        } else {
          alert('Stream refresh not supported for this platform')
          return
        }
        
        if (response.data.m3u8_url) {
          alert('Stream refreshed successfully!')
          fetchDashboardData()
        } else {
          alert('Failed to refresh stream')
        }
      } catch (error) {
        console.error('Failed to refresh stream:', error)
        alert('Failed to refresh stream: ' + (error.response?.data?.message || error.message))
      }
    }
    
    const createStream = async () => {
      try {
        const response = await axios.post('/api/streams', newStream.value)
        if (response.status === 201) {
          showCreateStreamModal.value = false
          newStream.value = { platform: '', room_url: '', agent_id: null }
          fetchDashboardData()
        }
      } catch (error) {
        console.error('Failed to create stream:', error)
        alert('Failed to create stream: ' + (error.response?.data?.message || error.message))
      }
    }
    
    const editStream = (stream) => {
      // Implement your edit stream functionality here
      console.log('Editing stream:', stream) // Added to use the 'stream' variable
      alert('Edit stream functionality would go here')
    }
    
    const confirmDeleteStream = (stream) => {
      confirmationModal.value = {
        show: true,
        title: 'Delete Stream',
        message: `Are you sure you want to delete the stream for ${stream.streamer_username}?`,
        action: () => deleteStream(stream),
        actionText: 'Delete'
      }
    }
    
    const deleteStream = async (stream) => {
      try {
        await axios.delete(`/api/streams/${stream.id}`)
        confirmationModal.value.show = false
        fetchDashboardData()
      } catch (error) {
        console.error('Failed to delete stream:', error)
        alert('Failed to delete stream: ' + (error.response?.data?.message || error.message))
      }
    }
    
    const createAgent = async () => {
      try {
        const response = await axios.post('/api/agents', newAgent.value)
        if (response.status === 201) {
          showCreateAgentModal.value = false
          newAgent.value = {
            username: '',
            password: '',
            firstname: '',
            lastname: '',
            email: '',
            phonenumber: ''
          }
          fetchDashboardData()
        }
      } catch (error) {
        console.error('Failed to create agent:', error)
        alert('Failed to create agent: ' + (error.response?.data?.message || error.message))
      }
    }
    
    const editAgent = (agent) => {
      // Implement your edit agent functionality here
      console.log('Editing agent:', agent) // Added to use the 'agent' variable
      alert('Edit agent functionality would go here')
    }
    
    const confirmDeleteAgent = (agent) => {
      confirmationModal.value = {
        show: true,
        title: 'Delete Agent',
        message: `Are you sure you want to delete agent ${agent.username}?`,
        action: () => deleteAgent(agent),
        actionText: 'Delete'
      }
    }
    
    const deleteAgent = async (agent) => {
      try {
        await axios.delete(`/api/agents/${agent.id}`)
        confirmationModal.value.show = false
        fetchDashboardData()
      } catch (error) {
        console.error('Failed to delete agent:', error)
        alert('Failed to delete agent: ' + (error.response?.data?.message || error.message))
      }
    }
    
    const fetchNotifications = async () => {
      try {
        const response = await axios.get('/api/notifications')
        notifications.value = response.data
        processDetections()
      } catch (error) {
        console.error('Failed to fetch notifications:', error)
      }
    }
    
    const markAsRead = async (notificationId) => {
      try {
        await axios.put(`/api/notifications/${notificationId}/read`)
        fetchNotifications()
      } catch (error) {
        console.error('Failed to mark notification as read:', error)
      }
    }
    
    const markAllAsRead = async () => {
      try {
        await axios.put('/api/notifications/read-all')
        fetchNotifications()
      } catch (error) {
        console.error('Failed to mark all notifications as read:', error)
      }
    }
    
    const showForwardModal = (notification) => {
      forwardModal.value = {
        show: true,
        notification,
        agent_id: null,
        message: ''
      }
    }
    
    const forwardNotification = async () => {
      try {
        await axios.post(`/api/notifications/${forwardModal.value.notification.id}/forward`, {
          agent_id: forwardModal.value.agent_id,
          message: forwardModal.value.message
        })
        forwardModal.value.show = false
        fetchNotifications()
      } catch (error) {
        console.error('Failed to forward notification:', error)
        alert('Failed to forward notification: ' + (error.response?.data?.message || error.message))
      }
    }
    
    const formatEventType = (type) => {
      const types = {
        'object_detection': 'Object Detection',
        'chat_detection': 'Chat Detection',
        'audio_detection': 'Audio Detection',
        'stream_created': 'Stream Created'
      }
      return types[type] || type
    }
    
    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleString()
    }
    
    const getNotificationMessage = (notification) => {
      if (notification.event_type === 'object_detection') {
        const detections = notification.details.detections || []
        const detectionList = detections.map(d => d.class).join(', ')
        return `Detected ${detectionList} in ${notification.details.streamer_name}'s stream`
      } else if (notification.event_type === 'chat_detection') {
        const keywords = notification.details.keywords || []
        return `Detected flagged keywords (${keywords.join(', ')}) in chat`
      } else if (notification.event_type === 'audio_detection') {
        return `Detected flagged audio: ${notification.details.keyword}`
      } else if (notification.event_type === 'stream_created') {
        return `New stream created for ${notification.details.streamer_username}`
      }
      return notification.details.message || 'Notification'
    }
    
    const confirmAction = () => {
      if (confirmationModal.value.action) {
        confirmationModal.value.action()
      }
      confirmationModal.value.show = false
    }
    
    // Lifecycle hooks
    onMounted(() => {
      fetchDashboardData()
      
      // Set up periodic refresh
      const refreshInterval = setInterval(fetchDashboardData, 30000)
      
      // Check online status
      window.addEventListener('online', () => isOnline.value = true)
      window.addEventListener('offline', () => isOnline.value = false)
      isOnline.value = navigator.onLine
      
      return () => {
        clearInterval(refreshInterval)
        window.removeEventListener('online', () => isOnline.value = true)
        window.removeEventListener('offline', () => isOnline.value = false)
      }
    })
    
    // Watch for tab changes
    watch(activeTab, (newTab) => {
      if (newTab === 'notifications') {
        fetchNotifications()
      } else if (newTab === 'streams') {
        // Could fetch fresh stream data here if needed
      } else if (newTab === 'agents') {
        // Could fetch fresh agent data here if needed
      }
    })
    
    return {
      // State
      isDarkTheme,
      activeTab,
      loading,
      hasError,
      errorMessage,
      isOnline,
      user,
      
      // Data
      dashboardStats,
      streams,
      allStreams,
      agents,
      notifications,
      
      // Modals
      selectedStream,
      showCreateStreamModal,
      showCreateAgentModal,
      forwardModal,
      confirmationModal,
      
      // Form data
      newStream,
      newAgent,
      
      // UI
      tabs,
      unreadNotifications,
      
      // Methods
      fetchDashboardData,
      getStreamDetections,
      hasDetections,
      detectionCount,
      openStreamDetails,
      closeModal,
      assignAgent,
      refreshStream,
      createStream,
      editStream,
      confirmDeleteStream,
      deleteStream,
      createAgent,
      editAgent,
      confirmDeleteAgent,
      deleteAgent,
      fetchNotifications,
      markAsRead,
      markAllAsRead,
      showForwardModal,
      forwardNotification,
      formatEventType,
      formatTime,
      getNotificationMessage,
      confirmAction
    }
  }
}
</script>

<style scoped>
.admin-container {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
}

/* Sidebar Styles */
.sidebar {
  width: 280px;
  background-color: var(--hover-bg);
  border-right: 1px solid var(--input-border);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--input-border);
}

.sidebar-header h2 {
  margin: 0 0 10px 0;
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--primary-color);
}

.user-info {
  display: flex;
  flex-direction: column;
  font-size: 0.9rem;
}

.user-role {
  font-size: 0.8rem;
  color: var(--primary-color);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.sidebar-nav {
  flex: 1;
  padding: 15px 0;
  overflow-y: auto;
}

.nav-button {
  width: 100%;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  background: transparent;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.nav-button:hover {
  background-color: rgba(0, 123, 255, 0.1);
}

.nav-button.active {
  background-color: var(--primary-color);
  color: white;
}

.nav-button.active .nav-icon {
  color: white;
}

.nav-icon {
  margin-right: 10px;
  width: 20px;
  color: var(--text-color);
  transition: color 0.2s ease;
}

.nav-text {
  font-size: 0.95rem;
}

.sidebar-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--input-border);
}

.status-indicator {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
  background-color: #6c757d;
}

.status-dot.online {
  background-color: #28a745;
}

/* Main Content Styles */
.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 123, 255, 0.2);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  max-width: 600px;
  margin: 50px auto;
  padding: 30px;
  background-color: var(--error-bg);
  border-radius: 10px;
  border: 1px solid var(--error-border);
  text-align: center;
}

.error-state h3 {
  margin-bottom: 15px;
  color: #dc3545;
}

.refresh-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  margin-top: 20px;
  cursor: pointer;
  transition: opacity 0.3s ease;
  display: inline-flex;
  align-items: center;
}

.refresh-button:hover {
  opacity: 0.9;
}

.refresh-button svg {
  margin-right: 8px;
}

/* Dashboard Tab Styles */
.dashboard-tab {
  animation: fadeIn 0.4s ease;
}

.dashboard-header {
  margin-bottom: 30px;
}

.dashboard-header h2 {
  margin-bottom: 20px;
  font-size: 1.8rem;
  color: var(--text-color);
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background-color: var(--input-bg);
  border-radius: 10px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-color);
  opacity: 0.8;
}

.stream-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.stream-card {
  background-color: var(--input-bg);
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid var(--input-border);
  cursor: pointer;
}

.stream-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
  border-color: var(--primary-color);
}

.stream-thumbnail {
  position: relative;
  width: 100%;
  height: 150px;
  overflow: hidden;
}

.stream-thumbnail::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.5));
  z-index: 1;
}

.alert-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: #dc3545;
  color: white;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
  z-index: 2;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.stream-info {
  padding: 15px;
}

.stream-title {
  margin: 0 0 5px 0;
  font-size: 1.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stream-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--text-color);
  opacity: 0.8;
}

.platform-tag {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.platform-tag.chaturbate {
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.platform-tag.stripchat {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.platform-tag.youtube {
  background-color: rgba(255, 0, 0, 0.2);
  color: #ff0000;
}

.platform-tag.twitch {
  background-color: rgba(100, 65, 164, 0.2);
  color: #6441a4;
}

/* Streams Tab Styles */
.streams-tab, .agents-tab, .notifications-tab {
  animation: fadeIn 0.4s ease;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tab-header h2 {
  margin: 0;
  font-size: 1.8rem;
}

.create-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: opacity 0.3s ease;
  display: inline-flex;
  align-items: center;
  font-size: 0.9rem;
}

.create-button:hover {
  opacity: 0.9;
}

.create-button svg {
  margin-right: 8px;
}

.streams-table, .agents-table {
  background-color: var(--input-bg);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid var(--input-border);
}

th {
  background-color: var(--hover-bg);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.5px;
}

tr:hover {
  background-color: var(--hover-bg);
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.active, .status-badge.online {
  background-color: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.status-badge:not(.active):not(.online) {
  background-color: rgba(108, 117, 125, 0.2);
  color: #6c757d;
}

.actions {
  white-space: nowrap;
}

.icon-button {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  padding: 5px;
  margin: 0 5px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.icon-button:hover {
  opacity: 1;
}

.icon-button.danger {
  color: #dc3545;
}

/* Notifications Tab Styles */
.notifications-tab .tab-header {
  margin-bottom: 15px;
}

.notification-actions {
  display: flex;
  gap: 10px;
}

.action-button {
  background-color: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--input-border);
  padding: 8px 12px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
}

.action-button:hover {
  background-color: var(--input-bg);
}

.action-button svg {
  margin-right: 6px;
}

.action-button.primary {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.action-button.primary:hover {
  opacity: 0.9;
}

.notifications-list {
  background-color: var(--input-bg);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.notification-item {
  padding: 15px;
  border-bottom: 1px solid var(--input-border);
  transition: background-color 0.2s ease;
}

.notification-item.unread {
  background-color: rgba(0, 123, 255, 0.05);
}

.notification-item.read {
  opacity: 0.8;
}

.notification-item:hover {
  background-color: var(--hover-bg);
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.notification-type {
  font-weight: 600;
  font-size: 0.9rem;
}

.notification-time {
  font-size: 0.8rem;
  color: var(--text-color);
  opacity: 0.7;
}

.unread-badge {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary-color);
}

.notification-content p {
  margin: 0 0 10px 0;
  font-size: 0.9rem;
}

.detection-details {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.detection-item {
  background-color: var(--hover-bg);
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
}

.detection-class {
  font-weight: 600;
  margin-right: 5px;
}

.detection-confidence {
  opacity: 0.7;
}

.notification-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.small-button {
  padding: 5px 10px;
  font-size: 0.8rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.small-button:hover {
  opacity: 0.9;
}

.small-button.primary {
  background-color: var(--primary-color);
  color: white;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  background-color: var(--input-bg);
  border-radius: 10px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
  position: relative;
}

.modal-content.small {
  max-width: 500px;
}

.modal-close {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.modal-close:hover {
  opacity: 1;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid var(--input-border);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.stream-tags {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}

.tag.platform {
  background-color: rgba(0, 123, 255, 0.2);
  color: var(--primary-color);
}

.tag.agent {
  background-color: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.tag.stream-id {
  background-color: rgba(108, 117, 125, 0.2);
  color: #6c757d;
}

.modal-body {
  padding: 20px;
}

.stream-player-container {
  width: 100%;
  height: 400px;
  background-color: black;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.detections-section h4 {
  margin: 20px 0 15px 0;
  font-size: 1.2rem;
}

.detections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
}

.detection-card {
  background-color: var(--hover-bg);
  border-radius: 8px;
  overflow: hidden;
}

.detection-image {
  width: 100%;
  height: 100px;
  object-fit: cover;
}

.detection-info {
  padding: 10px;
}

.detection-class {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 3px;
}

.detection-confidence {
  font-size: 0.8rem;
  opacity: 0.8;
}

.detection-time {
  font-size: 0.7rem;
  opacity: 0.6;
  margin-top: 5px;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--input-border);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-button {
  background-color: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--input-border);
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-button:hover {
  background-color: var(--input-bg);
}

.submit-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.submit-button:hover {
  opacity: 0.9;
}

.submit-button.danger {
  background-color: #dc3545;
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Form Styles */
.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 0.9rem;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 5px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 0.9rem;
}

.form-group textarea {
  min-height: 100px;
  resize: vertical;
}

.form-row {
  display: flex;
  gap: 15px;
}

.form-row .form-group {
  flex: 1;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.notification-preview {
  background-color: var(--hover-bg);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.notification-preview h4 {
  margin: 0 0 10px 0;
  font-size: 1.1rem;
}

.detection-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Responsive Styles */
@media (max-width: 992px) {
  .sidebar {
    width: 240px;
  }
}

@media (max-width: 768px) {
  .admin-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--input-border);
  }
  
  .sidebar-nav {
    display: flex;
    overflow-x: auto;
    padding: 0;
  }
  
  .nav-button {
    flex: 1;
    min-width: max-content;
    justify-content: center;
    padding: 12px 15px;
  }
  
  .nav-text {
    display: none;
  }
  
  .main-content {
    padding: 15px;
  }
  
  .stats-container {
    grid-template-columns: 1fr;
  }
  
  .stream-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .tab-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .create-button {
    width: 100%;
  }
  
  table {
    display: block;
    overflow-x: auto;
  }
}

@media (max-width: 576px) {
  .stream-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    max-height: 85vh;
  }
  
  .stream-player-container {
    height: 250px;
  }
  
  .form-row {
    flex-direction: column;
    gap: 0;
  }
}
</style>