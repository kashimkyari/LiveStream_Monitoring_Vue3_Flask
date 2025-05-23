<template>
  <div class="admin-settings-container" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="settings-sidebar">
      <h3 class="sidebar-title">Settings</h3>
      <ul class="settings-menu">
        <li
          v-for="section in sections"
          :key="section.id"
          class="menu-item"
          :class="{ active: activeSection === section.id }"
          @click="setActiveSection(section.id)"
          :title="section.tooltip"
          :aria-expanded="activeSection === section.id && section.id === 'tracking'"
        >
          <div class="menu-item-content">
            <font-awesome-icon :icon="section.icon" class="menu-icon" />
            <span>{{ section.name }}</span>
          </div>
          <ul v-if="activeSection === section.id && section.id === 'tracking'" class="submenu">
            <li
              v-for="sub in ['keywords', 'objects']"
              :key="sub"
              class="submenu-item"
              :class="{ active: subSection === sub }"
              @click="setSubSection(sub)"
            >
              {{ sub.charAt(0).toUpperCase() + sub.slice(1) }}
            </li>
          </ul>
        </li>
      </ul>
    </div>

    <main class="settings-content">
      <div class="action-buttons">
        <button
          class="btn-danger"
          @click="showLogoutConfirmation = true"
          :disabled="isLoggingOut"
        >
          <font-awesome-icon
            :icon="isLoggingOut ? 'spinner' : 'sign-out-alt'"
            :spin="isLoggingOut"
            class="icon-left"
          />
          {{ isLoggingOut ? 'Logging out...' : 'Logout' }}
        </button>
      </div>
      <transition name="modal-fade">
        <div v-if="showLogoutConfirmation" class="modal-overlay" @click="showLogoutConfirmation = false">
          <div class="modal-container" @click.stop>
            <div class="modal-header">
              <font-awesome-icon icon="sign-out-alt" class="modal-icon" />
              <h3>Confirm Logout</h3>
              <button class="close-btn" @click="showLogoutConfirmation = false">
                <font-awesome-icon icon="times" />
              </button>
            </div>
            <p class="modal-message">Are you sure you want to log out of your account?</p>
            <div class="modal-actions">
              <button
                class="btn btn-danger"
                @click="handleLogout(playLogoutAnimation)"
                :disabled="isLoggingOut"
              >
                <font-awesome-icon
                  :icon="isLoggingOut ? 'spinner' : 'sign-out-alt'"
                  :spin="isLoggingOut"
                  class="icon-left"
                />
                {{ isLoggingOut ? 'Logging out...' : 'Logout' }}
              </button>
              <button class="btn btn-outline" @click="showLogoutConfirmation = false">Cancel</button>
            </div>
          </div>
        </div>
      </transition>
      <div v-if="showLogoutAnimation" class="logout-animation-overlay">
        <div class="logout-animation-container" ref="logoutAnimationContainer">
          <font-awesome-icon icon="sign-out-alt" class="logout-icon" ref="logoutIcon" />
          <div class="logout-message" ref="logoutMessage">Logging out...</div>
          <div class="logout-spinner" ref="logoutSpinner">
            <div class="spinner-circle" v-for="n in 12" :key="n" :style="`--i: ${n}`"></div>
          </div>
        </div>
      </div>
      <div class="settings-header">
        <h2>{{ sections.find(s => s.id === activeSection)?.name || 'Settings' }}</h2>
      </div>
      <transition name="section-fade">
        <div class="settings-body" :key="activeSection + subSection">
          <section v-if="activeSection === 'general'" class="settings-section">
            <h3>Notifications</h3>
            <div class="settings-options">
              <div class="option">
                <span title="Receive alerts via email">Email Alerts</span>
                <div
                  class="toggle-switch"
                  :class="{ active: settings.emailNotifications }"
                  @click="toggleEmailNotifications"
                >
                  <div class="toggle-handle"></div>
                </div>
              </div>
              <div class="option">
                <span title="Receive alerts on your device">App Alerts</span>
                <div
                  class="toggle-switch"
                  :class="{ active: settings.pushNotifications }"
                  @click="togglePushNotifications"
                >
                  <div class="toggle-handle"></div>
                </div>
              </div>
              <div class="telegram-status" v-if="settings.pushNotifications">
                <div v-if="telegramConnected" class="status-connected">
                  <font-awesome-icon :icon="['fab', 'telegram']" class="telegram-icon" />
                  <div class="status-details">
                    <span>Connected to Telegram {{ telegramUsername }}</span>
                  </div>
                  <button class="btn-outline" @click="showTelegramModal = true">Change</button>
                </div>
                <div v-else class="status-disconnected" @click="showTelegramModal = true">
                  <font-awesome-icon :icon="['fab', 'telegram']" class="telegram-icon" />
                  <span>Connect to Telegram</span>
                </div>
              </div>
            </div>
            <h3>Appearance</h3>
            <div class="theme-options">
              <div
                class="theme-option"
                :class="{ selected: isDarkTheme }"
                @click="toggleTheme(true)"
                title="Switch to dark mode for better visibility in low light"
              >
                <font-awesome-icon icon="moon" class="theme-icon" />
                <span>Dark Mode</span>
              </div>
              <div
                class="theme-option"
                :class="{ selected: !isDarkTheme }"
                @click="toggleTheme(false)"
                title="Switch to light mode for a brighter interface"
              >
                <font-awesome-icon icon="sun" class="theme-icon" />
                <span>Light Mode</span>
              </div>
            </div>
          </section>
          <section v-if="activeSection === 'agents'" class="settings-section">
            <h3>Manage Agents</h3>
            <div class="form-group">
              <h4>Add New Agent</h4>
              <form @submit.prevent="addAgent">
                <input v-model="newAgent.username" placeholder="Enter Username" required :disabled="isAddingAgent" />
                <input v-model="newAgent.email" placeholder="Enter Email" required :disabled="isAddingAgent" />
                <input v-model="newAgent.password" type="password" placeholder="Enter Password" required :disabled="isAddingAgent" />
                <button type="submit" class="btn-primary" :disabled="isAddingAgent">
                  <font-awesome-icon v-if="isAddingAgent" icon="spinner" spin />
                  Add Agent
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Update Agent</h4>
              <form @submit.prevent="updateAgent">
                <select v-model="updateAgentData.id" required :disabled="isUpdatingAgent" aria-label="Select an agent to update">
                  <option value="" disabled>Select an Agent</option>
                  <option v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.username }}</option>
                </select>
                <input v-model="updateAgentData.password" type="password" placeholder="New Password (optional)" :disabled="isUpdatingAgent" />
                <label>
                  <input v-model="updateAgentData.online" type="checkbox" :disabled="isUpdatingAgent" />
                  Set as Online
                </label>
                <button type="submit" class="btn-primary" :disabled="isUpdatingAgent">
                  <font-awesome-icon v-if="isUpdatingAgent" icon="spinner" spin />
                  Update Agent
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Remove Agent</h4>
              <form @submit.prevent="removeAgent">
                <select v-model="deleteAgentId" required :disabled="isRemovingAgent" aria-label="Select an agent to remove">
                  <option value="" disabled>Select an Agent</option>
                  <option v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.username }}</option>
                </select>
                <button type="submit" class="btn-danger" :disabled="isRemovingAgent">
                  <font-awesome-icon v-if="isRemovingAgent" icon="spinner" spin />
                  Remove Agent
                </button>
              </form>
            </div>
          </section>
          <section v-if="activeSection === 'assignments'" class="settings-section">
            <h3>Manage Assignments</h3>
            <div class="form-group">
              <h4>Assign Agent to Stream</h4>
              <form @submit.prevent="assignAgentToStream">
                <select v-model="newAssignment.agent_id" required :disabled="isAddingAssignment" aria-label="Select an agent to assign">
                  <option value="" disabled>Select an Agent</option>
                  <option v-for="agent in agents" :key="agent.id" :value="agent.id">{{ agent.username }}</option>
                </select>
                <select v-model="newAssignment.stream_id" required :disabled="isAddingAssignment" aria-label="Select a stream to assign">
                  <option value="" disabled>Select a Stream</option>
                  <option v-for="stream in streams" :key="stream.id" :value="stream.id">{{ stream.room_url }}</option>
                </select>
                <button type="submit" class="btn-primary" :disabled="isAddingAssignment">
                  <font-awesome-icon v-if="isAddingAssignment" icon="spinner" spin />
                  Assign
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Remove Assignment</h4>
              <form @submit.prevent="removeAssignment">
                <select v-model="deleteAssignmentId" required :disabled="isRemovingAssignment" aria-label="Select an assignment to remove">
                  <option value="" disabled>Select an Assignment</option>
                  <option v-for="assignment in assignments" :key="assignment.id" :value="assignment.id">
                    {{ assignment.agent_id }} - {{ assignment.stream_id }}
                  </option>
                </select>
                <button type="submit" class="btn-danger" :disabled="isRemovingAssignment">
                  <font-awesome-icon v-if="isRemovingAssignment" icon="spinner" spin />
                  Remove Assignment
                </button>
              </form>
            </div>
          </section>
          <section v-if="activeSection === 'streams'" class="settings-section">
            <h3>Manage Streams</h3>
            <div class="form-group">
              <h4>Add New Stream</h4>
              <form @submit.prevent="addStream">
                <select v-model="newStream.platform" required :disabled="isAddingStream" aria-label="Select a platform">
                  <option value="" disabled>Select Platform</option>
                  <option value="chaturbate">Chaturbate</option>
                  <option value="stripchat">Stripchat</option>
                </select>
                <input v-model="newStream.room_url" placeholder="Enter Stream URL" required :disabled="isAddingStream" />
                <select v-model="newStream.priority" :disabled="isAddingStream" aria-label="Select priority">
                  <option value="normal">Normal Priority</option>
                  <option value="high">High Priority</option>
                  <option value="low">Low Priority</option>
                </select>
                <button type="submit" class="btn-primary" :disabled="isAddingStream">
                  <font-awesome-icon v-if="isAddingStream" icon="spinner" spin />
                  Add Stream
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Update Stream</h4>
              <form @submit.prevent="updateStream">
                <select v-model="updateStreamData.id" required :disabled="isUpdatingStream" aria-label="Select a stream to update">
                  <option value="" disabled>Select a Stream</option>
                  <option v-for="stream in streams" :key="stream.id" :value="stream.id">{{ stream.room_url }}</option>
                </select>
                <input v-model="updateStreamData.room_url" placeholder="New Stream URL (optional)" :disabled="isUpdatingStream" />
                <select v-model="updateStreamData.priority" :disabled="isUpdatingStream" aria-label="Select priority">
                  <option value="normal">Normal Priority</option>
                  <option value="high">High Priority</option>
                  <option value="low">Low Priority</option>
                </select>
                <button type="submit" class="btn-primary" :disabled="isUpdatingStream">
                  <font-awesome-icon v-if="isUpdatingStream" icon="spinner" spin />
                  Update Stream
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Remove Stream</h4>
              <form @submit.prevent="removeStream">
                <select v-model="deleteStreamId" required :disabled="isRemovingStream" aria-label="Select a stream to remove">
                  <option value="" disabled>Select a Stream</option>
                  <option v-for="stream in streams" :key="stream.id" :value="stream.id">{{ stream.room_url }}</option>
                </select>
                <button type="submit" class="btn-danger" :disabled="isRemovingStream">
                  <font-awesome-icon v-if="isRemovingStream" icon="spinner" spin />
                  Remove Stream
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Update Stream Status</h4>
              <form @submit.prevent="updateStreamStatus">
                <select v-model="streamStatus.id" required :disabled="isUpdatingStreamStatus" aria-label="Select a stream to update status">
                  <option value="" disabled>Select a Stream</option>
                  <option v-for="stream in streams" :key="stream.id" :value="stream.id">{{ stream.room_url }}</option>
                </select>
                <select v-model="streamStatus.status" required :disabled="isUpdatingStreamStatus" aria-label="Select status">
                  <option value="online">Online</option>
                  <option value="offline">Offline</option>
                </select>
                <button type="submit" class="btn-primary" :disabled="isUpdatingStreamStatus">
                  <font-awesome-icon v-if="isUpdatingStreamStatus" icon="spinner" spin />
                  Update Status
                </button>
              </form>
            </div>
          </section>
          <section v-if="activeSection === 'notifications'" class="settings-section">
            <h3>Manage Alerts</h3>
            <div class="form-group">
              <h4>Create Alert</h4>
              <form @submit.prevent="createNotification">
                <select v-model="newNotification.event_type" required :disabled="isCreatingNotification" aria-label="Select alert type">
                  <option value="" disabled>Select Alert Type</option>
                  <option value="stream_online">Stream Online</option>
                  <option value="stream_offline">Stream Offline</option>
                  <option value="keyword_detected">Keyword Detected</option>
                </select>
                <select v-model="newNotification.stream_id" required :disabled="isCreatingNotification" aria-label="Select a stream">
                  <option value="" disabled>Select a Stream</option>
                  <option v-for="stream in streams" :key="stream.id" :value="stream.id">{{ stream.room_url }}</option>
                </select>
                <input v-model="newNotification.message" placeholder="Alert Message" required :disabled="isCreatingNotification" />
                <button type="submit" class="btn-primary" :disabled="isCreatingNotification">
                  <font-awesome-icon v-if="isCreatingNotification" icon="spinner" spin />
                  Create Alert
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Mark Alert as Read</h4>
              <form @submit.prevent="markNotificationRead">
                <select v-model="updateNotificationId" required :disabled="isMarkingNotificationRead" aria-label="Select an alert to mark as read">
                  <option value="" disabled>Select an Alert</option>
                  <option v-for="notification in notifications" :key="notification.id" :value="notification.id">
                    {{ notification.message }} ({{ notification.event_type }})
                  </option>
                </select>
                <button type="submit" class="btn-primary" :disabled="isMarkingNotificationRead">
                  <font-awesome-icon v-if="isMarkingNotificationRead" icon="spinner" spin />
                  Mark as Read
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Remove Alert</h4>
              <form @submit.prevent="removeNotification">
                <select v-model="deleteNotificationId" required :disabled="isRemovingNotification" aria-label="Select an alert to remove">
                  <option value="" disabled>Select an Alert</option>
                  <option v-for="notification in notifications" :key="notification.id" :value="notification.id">
                    {{ notification.message }} ({{ notification.event_type }})
                  </option>
                </select>
                <button type="submit" class="btn-danger" :disabled="isRemovingNotification">
                  <font-awesome-icon v-if="isRemovingNotification" icon="spinner" spin />
                  Remove Alert
                </button>
              </form>
            </div>
          </section>
          <section v-if="activeSection === 'tracking' && subSection === 'keywords'" class="settings-section">
            <h3>Manage Keywords</h3>
            <div class="form-group">
              <h4>Add Keyword</h4>
              <form @submit.prevent="addKeyword">
                <input v-model="newKeyword.keyword" placeholder="Enter Keyword" required :disabled="isAddingKeyword" />
                <button type="submit" class="btn-primary" :disabled="isAddingKeyword">
                  <font-awesome-icon v-if="isAddingKeyword" icon="spinner" spin />
                  Add Keyword
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Update Keyword</h4>
              <form @submit.prevent="updateKeyword">
                <select v-model="updateKeywordData.id" required :disabled="isUpdatingKeyword" aria-label="Select a keyword to update">
                  <option value="" disabled>Select a Keyword</option>
                  <option v-for="keyword in keywords" :key="keyword.id" :value="keyword.id">{{ keyword.keyword }}</option>
                </select>
                <input v-model="updateKeywordData.keyword" placeholder="New Keyword" required :disabled="isUpdatingKeyword" />
                <button type="submit" class="btn-primary" :disabled="isUpdatingKeyword">
                  <font-awesome-icon v-if="isUpdatingKeyword" icon="spinner" spin />
                  Update Keyword
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Remove Keyword</h4>
              <form @submit.prevent="removeKeyword">
                <select v-model="deleteKeywordId" required :disabled="isRemovingKeyword" aria-label="Select a keyword to remove">
                  <option value="" disabled>Select a Keyword</option>
                  <option v-for="keyword in keywords" :key="keyword.id" :value="keyword.id">{{ keyword.keyword }}</option>
                </select>
                <button type="submit" class="btn-danger" :disabled="isRemovingKeyword">
                  <font-awesome-icon v-if="isRemovingKeyword" icon="spinner" spin />
                  Remove Keyword
                </button>
              </form>
            </div>
          </section>
          <section v-if="activeSection === 'tracking' && subSection === 'objects'" class="settings-section">
            <h3>Manage Objects</h3>
            <div class="form-group">
              <h4>Add Object</h4>
              <form @submit.prevent="addObject">
                <input v-model="newObject.object_name" placeholder="Enter Object Name" required :disabled="isAddingObject" />
                <button type="submit" class="btn-primary" :disabled="isAddingObject">
                  <font-awesome-icon v-if="isAddingObject" icon="spinner" spin />
                  Add Object
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Update Object</h4>
              <form @submit.prevent="updateObject">
                <select v-model="updateObjectData.id" required :disabled="isUpdatingObject" aria-label="Select an object to update">
                  <option value="" disabled>Select an Object</option>
                  <option v-for="obj in objects" :key="obj.id" :value="obj.id">{{ obj.object_name }}</option>
                </select>
                <input v-model="updateObjectData.object_name" placeholder="New Object Name" required :disabled="isUpdatingObject" />
                <button type="submit" class="btn-primary" :disabled="isUpdatingObject">
                  <font-awesome-icon v-if="isUpdatingObject" icon="spinner" spin />
                  Update Object
                </button>
              </form>
            </div>
            <div class="form-group">
              <h4>Remove Object</h4>
              <form @submit.prevent="removeObject">
                <select v-model="deleteObjectId" required :disabled="isRemovingObject" aria-label="Select an object to remove">
                  <option value="" disabled>Select an Object</option>
                  <option v-for="obj in objects" :key="obj.id" :value="obj.id">{{ obj.object_name }}</option>
                </select>
                <button type="submit" class="btn-danger" :disabled="isRemovingObject">
                  <font-awesome-icon v-if="isRemovingObject" icon="spinner" spin />
                  Remove Object
                </button>
              </form>
            </div>
          </section>
          <section v-if="activeSection === 'detection'" class="settings-section">
            <h3>Manage Detection</h3>
            <div class="form-group">
              <h4>Control Detection</h4>
              <form @submit.prevent="controlDetection">
                <select v-model="detectionData.stream_id" required :disabled="isControllingDetection" aria-label="Select a stream for detection">
                  <option value="" disabled>Select a Stream</option>
                  <option v-for="stream in streams" :key="stream.id" :value="stream.id">{{ stream.room_url }}</option>
                </select>
                <select v-model="detectionData.stop" required :disabled="isControllingDetection" aria-label="Control detection state">
                  <option value="false">Start Detection</option>
                  <option value="true">Stop Detection</option>
                </select>
                <button type="submit" class="btn-primary" :disabled="isControllingDetection">
                  <font-awesome-icon v-if="isControllingDetection" icon="spinner" spin />
                  {{ detectionData.stop === 'true' ? 'Stop Detection' : 'Start Detection' }}
                </button>
              </form>
            </div>
          </section>
        </div>
      </transition>
      <TelegramOnboarding
        :is-visible="showTelegramModal"
        :existing-username="telegramUsername"
        :existing-chat-id="telegramChatId"
        @close="showTelegramModal = false"
        @telegram-connected="handleTelegramConnected"
      />
    </main>
  </div>
</template>
<script setup>
import { defineProps, defineEmits, ref, onMounted, nextTick, watch } from 'vue'
import anime from 'animejs/lib/anime.es.js'
import TelegramOnboarding from './TelegramOnboarding.vue'
import { useSettings } from '../composables/useSettings'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()

defineProps({
  isDarkTheme: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['set-theme', 'logout'])

const {
  settings,
  telegramConnected,
  telegramUsername,
  telegramChatId,
  showTelegramModal,
  isLoggingOut,
  showLogoutConfirmation,
  toggleEmailNotifications,
  togglePushNotifications,
  handleTelegramConnected,
  handleLogout
} = useSettings()

const activeSection = ref('general')
const subSection = ref('keywords')
const sections = [
  { id: 'general', name: 'General Settings', icon: 'cog', tooltip: 'Manage notifications and appearance' },
  { id: 'agents', name: 'Agents', icon: 'user-shield', tooltip: 'Add, update, or remove team members' },
  { id: 'assignments', name: 'Assignments', icon: 'tasks', tooltip: 'Assign agents to streams' },
  { id: 'streams', name: 'Streams', icon: 'video', tooltip: 'Manage live streams' },
  { id: 'notifications', name: 'Alerts', icon: 'bell', tooltip: 'Create or manage alerts' },
  { id: 'tracking', name: 'Tracking', icon: 'tags', tooltip: 'Set up keywords and objects to track' },
  { id: 'detection', name: 'Detection', icon: 'search', tooltip: 'Control stream detection' }
]

const setActiveSection = (sectionId) => {
  activeSection.value = sectionId
  if (sectionId === 'tracking' && !subSection.value) {
    subSection.value = 'keywords'
  }
}

const setSubSection = (sub) => {
  subSection.value = sub
}

const isDarkTheme = ref(localStorage.getItem('theme') === 'dark')

const toggleTheme = (dark) => {
  isDarkTheme.value = dark
  localStorage.setItem('theme', dark ? 'dark' : 'light')
  emit('set-theme', dark)
}

watch(isDarkTheme, (newValue) => {
  document.documentElement.setAttribute('data-theme', newValue ? 'dark' : 'light')
})

onMounted(() => {
  document.documentElement.setAttribute('data-theme', isDarkTheme.value ? 'dark' : 'light')
})

const agents = ref([])
const streams = ref([])
const assignments = ref([])
const notifications = ref([])
const keywords = ref([])
const objects = ref([])

const isAddingAgent = ref(false)
const isUpdatingAgent = ref(false)
const isRemovingAgent = ref(false)
const isAddingAssignment = ref(false)
const isRemovingAssignment = ref(false)
const isAddingStream = ref(false)
const isUpdatingStream = ref(false)
const isRemovingStream = ref(false)
const isUpdatingStreamStatus = ref(false)
const isCreatingNotification = ref(false)
const isMarkingNotificationRead = ref(false)
const isRemovingNotification = ref(false)
const isAddingKeyword = ref(false)
const isUpdatingKeyword = ref(false)
const isRemovingKeyword = ref(false)
const isAddingObject = ref(false)
const isUpdatingObject = ref(false)
const isRemovingObject = ref(false)
const isControllingDetection = ref(false)

const newAgent = ref({ username: '', email: '', password: '' })
const updateAgentData = ref({ id: '', password: '', online: false })
const deleteAgentId = ref('')
const newAssignment = ref({ agent_id: '', stream_id: '' })
const deleteAssignmentId = ref('')
const newStream = ref({ platform: '', room_url: '', priority: 'normal' })
const updateStreamData = ref({ id: '', room_url: '', priority: 'normal' })
const deleteStreamId = ref('')
const streamStatus = ref({ id: '', status: 'online' })
const newNotification = ref({ event_type: '', stream_id: '', message: '' })
const updateNotificationId = ref('')
const deleteNotificationId = ref('')
const newKeyword = ref({ keyword: '' })
const updateKeywordData = ref({ id: '', keyword: '' })
const deleteKeywordId = ref('')
const newObject = ref({ object_name: '' })
const updateObjectData = ref({ id: '', object_name: '' })
const deleteObjectId = ref('')
const detectionData = ref({ stream_id: '', stop: 'false' })

const apiCall = async (method, url, data = null, loadingState = null, showSuccessToast = true) => {
  if (loadingState) loadingState.value = true
  try {
    const response = await axios({
      method,
      url: `${url}`,
      data,
      withCredentials: true
    })
    if (showSuccessToast && response.data.message) {
      toast.success(response.data.message)
    }
    return response.data
  } catch (error) {
    const message = error.response?.data?.message || 'Something went wrong'
    toast.error(message)
    throw error
  } finally {
    if (loadingState) loadingState.value = false
  }
}

const fetchAgents = async () => {
  try {
    const response = await apiCall('get', '/api/agents', null, null, false)
    agents.value = response
  } catch (error) {
    agents.value = []
  }
}

const fetchStreams = async () => {
  try {
    const response = await apiCall('get', '/api/streams', null, null, false)
    streams.value = response
  } catch (error) {
    streams.value = []
  }
}

const fetchAssignments = async () => {
  try {
    const response = await apiCall('get', '/api/assignments', null, null, false)
    assignments.value = response
  } catch (error) {
    assignments.value = []
  }
}

const fetchNotifications = async () => {
  try {
    const response = await apiCall('get', '/api/notifications', null, null, false)
    notifications.value = response
  } catch (error) {
    notifications.value = []
  }
}

const fetchKeywords = async () => {
  try {
    const response = await apiCall('get', '/api/keywords', null, null, false)
    keywords.value = response
  } catch (error) {
    keywords.value = []
  }
}

const fetchObjects = async () => {
  try {
    const response = await apiCall('get', '/api/objects', null, null, false)
    objects.value = response
  } catch (error) {
    objects.value = []
  }
}

const fetchAllData = async () => {
  await Promise.all([
    fetchAgents(),
    fetchStreams(),
    fetchAssignments(),
    fetchNotifications(),
    fetchKeywords(),
    fetchObjects()
  ])
}

onMounted(fetchAllData)

window.addEventListener('beforeunload', () => {
  localStorage.removeItem('agents')
  localStorage.removeItem('streams')
  localStorage.removeItem('assignments')
  localStorage.removeItem('notifications')
  localStorage.removeItem('keywords')
  localStorage.removeItem('objects')
})

const addAgent = async () => {
  if (!newAgent.value.username || !newAgent.value.email || !newAgent.value.password) {
    toast.error('Username, email, and password are required')
    return
  }
  try {
    const response = await apiCall('post', '/api/register', {
      username: newAgent.value.username,
      email: newAgent.value.email,
      password: newAgent.value.password,
      receiveUpdates: false
    }, isAddingAgent, true)
    newAgent.value = { username: '', email: '', password: '' }
    await fetchAgents()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const updateAgent = async () => {
  if (!updateAgentData.value.id) {
    toast.error('Please select an agent to update')
    return
  }
  const data = {
    password: updateAgentData.value.password || undefined,
    online: updateAgentData.value.online
  }
  try {
    const response = await apiCall('put', `/api/agents/${updateAgentData.value.id}`, data, isUpdatingAgent, true)
    updateAgentData.value = { id: '', password: '', online: false }
    await fetchAgents()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const removeAgent = async () => {
  if (!deleteAgentId.value) {
    toast.error('Please select an agent to remove')
    return
  }
  try {
    const response = await apiCall('delete', `/api/agents/${deleteAgentId.value}`, null, isRemovingAgent, true)
    deleteAgentId.value = ''
    await fetchAgents()
    await fetchAssignments()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const assignAgentToStream = async () => {
  if (!newAssignment.value.agent_id || !newAssignment.value.stream_id) {
    toast.error('Please select an agent and a stream')
    return
  }
  try {
    const response = await apiCall('post', '/api/assign', newAssignment.value, isAddingAssignment, true)
    newAssignment.value = { agent_id: '', stream_id: '' }
    await fetchAssignments()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const removeAssignment = async () => {
  if (!deleteAssignmentId.value) {
    toast.error('Please select an assignment to remove')
    return
  }
  try {
    const response = await apiCall('delete', `/api/assignments/${deleteAssignmentId.value}`, null, isRemovingAssignment, true)
    deleteAssignmentId.value = ''
    await fetchAssignments()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const addStream = async () => {
  if (!newStream.value.platform || !newStream.value.room_url) {
    toast.error('Platform and stream URL are required')
    return
  }
  try {
    const response = await apiCall('post', '/api/streams', newStream.value, isAddingStream, true)
    newStream.value = { platform: '', room_url: '', priority: 'normal' }
    await fetchStreams()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const updateStream = async () => {
  if (!updateStreamData.value.id) {
    toast.error('Please select a stream to update')
    return
  }
  const data = {
    room_url: updateStreamData.value.room_url || undefined,
    priority: updateStreamData.value.priority
  }
  try {
    const response = await apiCall('put', `/api/streams/${updateStreamData.value.id}`, data, isUpdatingStream, true)
    updateStreamData.value = { id: '', room_url: '', priority: 'normal' }
    await fetchStreams()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const removeStream = async () => {
  if (!deleteStreamId.value) {
    toast.error('Please select a stream to remove')
    return
  }
  try {
    const response = await apiCall('delete', `/api/streams/${deleteStreamId.value}`, null, isRemovingStream, true)
    deleteStreamId.value = ''
    await fetchStreams()
    await fetchAssignments()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const updateStreamStatus = async () => {
  if (!streamStatus.value.id) {
    toast.error('Please select a stream to update status')
    return
  }
  try {
    const response = await apiCall('post', `/api/streams/${streamStatus.value.id}/status`, { status: streamStatus.value.status }, isUpdatingStreamStatus, true)
    streamStatus.value = { id: '', status: 'online' }
    await fetchStreams()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const createNotification = async () => {
  if (!newNotification.value.event_type || !newNotification.value.stream_id || !newNotification.value.message) {
    toast.error('All notification fields are required')
    return
  }
  const data = {
    event_type: newNotification.value.event_type,
    room_url: streams.value.find(s => s.id === newNotification.value.stream_id)?.room_url || '',
    message: newNotification.value.message
  }
  try {
    const response = await apiCall('post', '/api/notifications', data, isCreatingNotification, true)
    newNotification.value = { event_type: '', stream_id: '', message: '' }
    await fetchNotifications()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const markNotificationRead = async () => {
  if (!updateNotificationId.value) {
    toast.error('Please select a notification to mark as read')
    return
  }
  try {
    const response = await apiCall('put', `/api/notifications/${updateNotificationId.value}/read`, null, isMarkingNotificationRead, true)
    updateNotificationId.value = ''
    await fetchNotifications()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const removeNotification = async () => {
  if (!deleteNotificationId.value) {
    toast.error('Please select a notification to remove')
    return
  }
  try {
    const response = await apiCall('delete', `/api/notifications/${deleteNotificationId.value}`, null, isRemovingNotification, true)
    deleteNotificationId.value = ''
    await fetchNotifications()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const addKeyword = async () => {
  if (!newKeyword.value.keyword) {
    toast.error('Keyword is required')
    return
  }
  try {
    const response = await apiCall('post', '/api/keywords', newKeyword.value, isAddingKeyword, true)
    newKeyword.value = { keyword: '' }
    await fetchKeywords()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const updateKeyword = async () => {
  if (!updateKeywordData.value.id || !updateKeywordData.value.keyword) {
    toast.error('Please select a keyword and provide a new value')
    return
  }
  try {
    const response = await apiCall('put', `/api/keywords/${updateKeywordData.value.id}`, { keyword: updateKeywordData.value.keyword }, isUpdatingKeyword, true)
    updateKeywordData.value = { id: '', keyword: '' }
    await fetchKeywords()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const removeKeyword = async () => {
  if (!deleteKeywordId.value) {
    toast.error('Please select a keyword to remove')
    return
  }
  try {
    const response = await apiCall('delete', `/api/keywords/${deleteKeywordId.value}`, null, isRemovingKeyword, true)
    deleteKeywordId.value = ''
    await fetchKeywords()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const addObject = async () => {
  if (!newObject.value.object_name) {
    toast.error('Object name is required')
    return
  }
  try {
    const response = await apiCall('post', '/api/objects', newObject.value, isAddingObject, true)
    newObject.value = { object_name: '' }
    await fetchObjects()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const updateObject = async () => {
  if (!updateObjectData.value.id || !updateObjectData.value.object_name) {
    toast.error('Please select an object and provide a new name')
    return
  }
  try {
    const response = await apiCall('put', `/api/objects/${updateObjectData.value.id}`, { object_name: updateObjectData.value.object_name }, isUpdatingObject, true)
    updateObjectData.value = { id: '', object_name: '' }
    await fetchObjects()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const removeObject = async () => {
  if (!deleteObjectId.value) {
    toast.error('Please select an object to remove')
    return
  }
  try {
    const response = await apiCall('delete', `/api/objects/${deleteObjectId.value}`, null, isRemovingObject, true)
    deleteObjectId.value = ''
    await fetchObjects()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const controlDetection = async () => {
  if (!detectionData.value.stream_id) {
    toast.error('Please select a stream for detection')
    return
  }
  try {
    const response = await apiCall('post', '/api/trigger-detection', {
      stream_id: detectionData.value.stream_id,
      stop: detectionData.value.stop === 'true'
    }, isControllingDetection, true)
    detectionData.value = { stream_id: '', stop: 'false' }
    await fetchStreams()
    return response
  } catch (error) {
    // Error handled in apiCall
  }
}

const showLogoutAnimation = ref(false)
const logoutAnimationContainer = ref(null)
const logoutIcon = ref(null)
const logoutMessage = ref(null)
const logoutSpinner = ref(null)

const playLogoutAnimation = async () => {
  showLogoutAnimation.value = true
  
  await nextTick()
  
  if (logoutAnimationContainer.value) {
    anime({
      targets: logoutAnimationContainer.value,
      opacity: [0, 1],
      scale: [0.8, 1],
      duration: 600,
      easing: 'easeOutCubic'
    })
  }
  
  if (logoutIcon.value) {
    anime({
      targets: logoutIcon.value,
      scale: [0, 1],
      opacity: [0, 1],
      duration: 500,
      easing: 'easeOutBack'
    })
  }
  
  if (logoutMessage.value) {
    anime({
      targets: logoutMessage.value,
      opacity: [0, 1],
      translateY: [20, 0],
      delay: 200,
      duration: 400,
      easing: 'easeOutQuad'
    })
  }
  
  if (logoutSpinner.value) {
    const spinnerCircles = logoutSpinner.value.querySelectorAll('.spinner-circle')
    anime({
      targets: spinnerCircles,
      scale: [0, 1],
      opacity: [0, 1],
      delay: anime.stagger(50),
      duration: 400,
      easing: 'easeOutExpo',
      complete: () => {
        if (logoutSpinner.value) {
          anime({
            targets: logoutSpinner.value,
            rotate: '360deg',
            duration: 1500,
            loop: true,
            easing: 'linear'
          })
        }
      }
    })
  }
  
  setTimeout(() => {
    completeLogout()
  }, 2000)
}

const completeLogout = async () => {
  try {
    await apiCall('post', '/api/logout', null, null, false)
    anime({
      targets: logoutAnimationContainer.value,
      opacity: 0,
      scale: 0.8,
      duration: 400,
      easing: 'easeInQuad',
      complete: () => {
        showLogoutAnimation.value = false
        emit('logout')
        localStorage.removeItem('userSettings')
        window.location.href = '/dashboard'
      }
    })
  } catch (error) {
    toast.error('Failed to logout. Please try again.')
    showLogoutAnimation.value = false
  }
}
</script>
<style scoped>
@import '../styles/shared.css';

:root {
  --primary-color: #4A90E2;
  --secondary-color: #50C878;
  --danger-color: #E74C3C;
  --bg-color-light: #F4F7FA;
  --bg-color-dark: #2C3E50;
  --sidebar-bg-light: #FFFFFF;
  --sidebar-bg-dark: #34495E;
  --content-bg-light: #FFFFFF;
  --content-bg-dark: #3E5469;
  --text-color-light: #2C3E50;
  --text-color-dark: #ECF0F1;
  --border-color-light: #DDE4E6;
  --border-color-dark: #5E6A7A;
  --toggle-bg-light: #BDC3C7;
  --toggle-bg-dark: #7F8C8D;
}

.admin-settings-container {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
  font-family: 'Inter', sans-serif;
}

[data-theme="light"] {
  --bg-color: var(--bg-color-light);
  --sidebar-bg: var(--sidebar-bg-light);
  --content-bg: var(--content-bg-light);
  --text-color: var(--text-color-light);
  --border-color: var(--border-color-light);
  --toggle-bg: var(--toggle-bg-light);
}

[data-theme="dark"] {
  --bg-color: var(--bg-color-dark);
  --sidebar-bg: var(--sidebar-bg-dark);
  --content-bg: var(--content-bg-dark);
  --text-color: var(--text-color-dark);
  --border-color: var(--border-color-dark);
  --toggle-bg: var(--toggle-bg-dark);
}

.settings-sidebar {
  width: 260px;
  background-color: var(--sidebar-bg);
  box-shadow: 4px 0 12px rgba(0, 0, 0, 0.1);
}

.sidebar-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 2rem;
  color: var(--primary-color);
}

.settings-menu {
  list-style: none;
  padding: 0;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.menu-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0.85rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 0.5rem;
  position: relative;
}

.menu-item-content {
  display: flex;
  align-items: center;
  width: 100%;
}

.menu-item:hover {
  background-color: rgba(var(--primary-color), 0.1);
}

.menu-item.active {
  background-color: var(--primary-color);
  color: white;
}

.menu-icon {
  margin-right: 1rem;
  font-size: 1.2rem;
}

.submenu {
  list-style: none;
  padding-left: 2rem;
  margin-top: 0.5rem;
  width: 100%;
  display: block;
  transition: opacity 0.3s ease;
}

.submenu-item {
  padding: 0.5rem 0.5rem;
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  width: 100%;
}

.submenu-item.active {
  font-weight: 600;
}

.menu-item:not(.active) .submenu {
  display: none;
}

.settings-content {
  flex: 1;
  padding: 2.5rem;
}

.settings-header {
  margin-bottom: 2.5rem;
}

.settings-header h2 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-color);
}

.settings-body {
  background-color: var(--content-bg);
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
}

.settings-section {
  margin-bottom: 3rem;
}

.settings-section h3 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: var(--text-color);
}

.settings-options {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1rem;
}

.toggle-switch {
  width: 54px;
  height: 28px;
  background-color: var(--toggle-bg);
  border-radius: 28px;
  position: relative;
  cursor: pointer;
  transition: background-color 0.3s;
}

.toggle-switch.active {
  background-color: var(--primary-color);
}

.toggle-handle {
  width: 24px;
  height: 24px;
  background-color: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch.active .toggle-handle {
  transform: translateX(26px);
}

.theme-options {
  display: flex;
  gap: 1.5rem;
}

.theme-option {
  flex: 1;
  padding: 1.25rem;
  text-align: center;
  border: 2px solid var(--border-color);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.theme-option:hover {
  border-color: var(--primary-color);
}

.theme-option.selected {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.form-group {
  margin-bottom: 2rem;
}

.form-group h4 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

input, select {
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  background-color: var(--content-bg);
  color: var(--text-color);
  transition: border-color 0.3s, transform 0.2s;
}

input:focus, select:focus {
  border-color: var(--primary-color);
  outline: none;
  transform: scale(1.02);
}

select {
  appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg fill='%232C3E50' height='24' viewBox='0 0 24 24' width='24' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/><path d='M0 0h24v24H0z' fill='none'/></svg>");
  background-repeat: no-repeat;
  background-position-x: 98%;
  background-position-y: 50%;
}

[data-theme="dark"] select {
  background-image: url("data:image/svg+xml;utf8,<svg fill='%23ECF0F1' height='24' viewBox='0 0 24 24' width='24' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/><path d='M0 0h24v24H0z' fill='none'/></svg>");
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
  padding: 0.85rem 1.75rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary:hover {
  background-color: #3A7BC8;
  transform: scale(1.05);
}

.btn-danger {
  background-color: var(--danger-color);
  color: white;
  padding: 0.85rem 1.75rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-danger:hover {
  background-color: #C0392B;
  transform: scale(1.05);
}

.btn-outline {
  background-color: transparent;
  border: 2px solid var(--border-color);
  color: var(--text-color);
  padding: 0.85rem 1.75rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-outline:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
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
  backdrop-filter: blur(4px);
}

.modal-container {
  background-color: var(--input-bg);
  border-radius: 12px;
  width: 100%;
  max-width: 450px;
  padding: 1.5rem;
  position: relative;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  position: relative;
}

.modal-icon {
  font-size: 1.5rem;
  color: var(--danger-color);
  margin-right: 0.75rem;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-color);
}

.close-btn {
  position: absolute;
  top: 0;
  right: 0;
  background: none;
  border: none;
  font-size: 1.2rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.2s ease;
}

.close-btn:hover {
  color: var(--text-color);
}

.modal-message {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.logout-animation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

[data-theme='light'] .logout-animation-overlay {
  background-color: rgba(248, 249, 250, 0.9);
}

[data-theme='dark'] .logout-animation-overlay {
  background-color: rgba(18, 18, 18, 0.9);
}

.logout-animation-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
}

.logout-icon {
  font-size: 4rem;
  color: var(--primary-color);
  margin-bottom: 1.5rem;
  opacity: 0;
}

[data-theme='light'] .logout-icon {
  color: var(--light-primary);
}

[data-theme='dark'] .logout-icon {
  color: var(--dark-primary);
}

.logout-message {
  font-size: 1.3rem;
  color: white;
  text-align: center;
  margin-bottom: 2rem;
  opacity: 0;
}

[data-theme='light'] .logout-message {
  color: var(--light-text);
}

[data-theme='dark'] .logout-message {
  color: var(--dark-text);
}

.logout-spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.spinner-circle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--light-primary);
  transform: translate(-50%, -50%) rotate(calc(var(--i) * 30deg)) translateY(-30px);
  transform-origin: center;
  opacity: calc(1 - (var(--i) * 0.08));
}

[data-theme='dark'] .spinner-circle {
  background-color: var(--dark-primary);
}

.section-fade-enter-active, .section-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.section-fade-enter-from, .section-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

:deep(.Vue-Toastification__toast--success) {
  background-color: var(--primary-color);
  color: white;
}

:deep(.Vue-Toastification__toast--error) {
  background-color: var(--danger-color);
  color: white;
}

:deep(.Vue-Toastification__toast) {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>