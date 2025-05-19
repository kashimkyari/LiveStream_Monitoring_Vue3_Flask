<template>
  <div class="mobile-admin-dashboard" :data-theme="isDarkTheme ? 'dark' : 'light'">
    

    <div class="mobile-tabs">
      <div
        v-for="(tab, index) in tabs"
        :key="index"
        class="tab-item"
        :class="{ active: activeTab === index }"
        @click="activeTab = index"
      >
        <div class="tab-icon-container">
          <font-awesome-icon :icon="tab.icon" class="tab-icon" />
          <span v-if="tab.icon === 'bell' && unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </div>
        <span class="tab-label">{{ tab.label }}</span>
      </div>
    </div>

    <div class="tab-content">
      <MobileAdminHome
        v-if="activeTab === 0"
        :user="user"
        :stats="{
          streams: dashboardStats.ongoing_streams || 0,
          agents: dashboardStats.active_agents || 0,
          detections: dashboardStats.total_detections || 0,
          notifications: unreadCount || 0
        }"
        :recent-detections="recentDetections"
        :recent-notifications="notifications"
        :is-dark-theme="isDarkTheme"
        @refresh-data="refreshData"
        @add-stream="openAddStreamModal"
        @add-agent="openAddAgentModal"
      />
      <MobileAdminStreams
        v-else-if="activeTab === 1"
        :loading="loading"
        :refreshing-streams="refreshingStreams"
        :all-streams="allStreams"
        :agents="agents"
        :is-dark-theme="isDarkTheme"
        @refresh="refreshStream"
        @stream-selected="openStreamDetails"
        @add-stream="openAddStreamModal"
      />
      <MobileAdminAgents
        v-else-if="activeTab === 2"
        :is-dark-theme="isDarkTheme"
        @agent-selected="openAgentDetails"
      />
      <MobileAdminNotifications
        v-else-if="activeTab === 3"
        :notifications="notifications"
        :notifications-loading="notificationsLoading"
        :unread-count="unreadCount"
        :grouped-notifications="groupedNotifications"
        :is-grouped-by-type="isGroupedByType"
        :is-grouped-by-stream="isGroupedByStream"
        @mark-as-read="markAsRead"
        @mark-all-read="markAllAsRead"
        @toggle-group-by-type="toggleGroupByType"
        @toggle-group-by-stream="toggleGroupByStream"
        @refresh="fetchDashboardData"
      />
      <MobileAdminSettings
        v-else-if="activeTab === 4"
        :is-dark-theme="isDarkTheme"
        :enable-background-refresh="settings.enableBackgroundRefresh"
        :refresh-interval-minutes="refreshIntervalMinutes"
        :is-grouped-by-type="isGroupedByType"
        :is-grouped-by-stream="isGroupedByStream"
        :unread-count="unreadCount"
        @update:is-dark-theme="handleDarkThemeChange"
        @update:enable-background-refresh="handleBackgroundRefreshChange"
        @update:refresh-interval-minutes="handleRefreshIntervalChange"
        @update:is-grouped-by-type="handleGroupByTypeChange"
        @update:is-grouped-by-stream="handleGroupByStreamChange"
        @mark-all-read="markAllAsRead"
        @logout="logout"
      />
    </div>

    <MobileStreamDetailsModal
      v-if="showStreamDetailsModal"
      :stream="selectedStream"
      :agents="agents"
      @close="showStreamDetailsModal = false"
      @stream-updated="handleStreamUpdated"
      @stream-deleted="handleStreamDeleted"
    />
    <MobileAddStreamModal
      v-if="showAddStreamModal"
      :is-visible="showAddStreamModal"
      :is-dark-theme="isDarkTheme"
      :job-id="jobId"
      @close="showAddStreamModal = false"
      @start-stream-creation="handleStartStreamCreation"
      @stream-created="handleStreamCreated"
    />
    <MobileAgentDetailsModal
      v-if="showAgentDetailsModal"
      :agent="selectedAgent"
      @close="showAgentDetailsModal = false"
      @agent-updated="handleAgentUpdated"
      @agent-deleted="handleAgentDeleted"
    />
    <!-- Add Agent Bottom Sheet -->
    <div class="bottom-sheet" :class="{ active: showAddAgentModal }" :data-theme="isDarkTheme ? 'dark' : 'light'">
      <div class="bottom-sheet-content">
        <div class="modal-header">
          <h3>Add New Agent</h3>
          <button class="close-btn" @click="showAddAgentModal = false">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <form @submit.prevent="handleAgentCreated">
          <div class="form-group">
            <label for="username">Username</label>
            <input
              id="username"
              v-model="newAgent.username"
              type="text"
              placeholder="Enter username"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label for="email">Email</label>
            <input
              id="email"
              v-model="newAgent.email"
              type="email"
              placeholder="Enter email"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <input
              id="password"
              v-model="newAgent.password"
              type="password"
              placeholder="Enter password"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="newAgent.receiveUpdates" />
              Receive Updates
            </label>
          </div>
          <div class="form-actions">
            <button type="button" class="cancel-btn" @click="showAddAgentModal = false">Cancel</button>
            <button type="submit" class="submit-btn" :disabled="addingAgent">Add Agent</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import axios from 'axios'
import MobileAdminHome from './MobileAdminHome.vue'
import MobileAdminStreams from './MobileAdminStreams.vue'
import MobileAdminAgents from './MobileAdminAgents.vue'
import MobileAdminNotifications from './MobileAdminNotifications.vue'
import MobileAdminSettings from './MobileAdminSettings.vue'
import MobileStreamDetailsModal from './MobileStreamDetailsModal.vue'
import MobileAddStreamModal from './MobileAddStreamModal.vue'
import MobileAgentDetailsModal from './MobileAgentDetailsModal.vue'
import { useMobileDashboardData } from '../composables/useMobileDashboardData'
import { useMobileNotifications } from '../composables/useMobileNotifications'

export default {
  name: 'MobileAdminDashboard',
  components: {
    MobileAdminHome,
    MobileAdminStreams,
    MobileAdminAgents,
    MobileAdminNotifications,
    MobileAdminSettings,
    MobileStreamDetailsModal,
    MobileAddStreamModal,
    MobileAgentDetailsModal
  },
  setup() {
    const router = useRouter()
    const toast = useToast()
    const isDarkTheme = ref(localStorage.getItem('themePreference') === 'dark' || false)
    const { notifications, loading: notificationsLoading, unreadCount, groupedNotifications, isGroupedByType, isGroupedByStream, markAsRead, markAllAsRead, toggleGroupByType, toggleGroupByStream, fetchNotifications } = useMobileNotifications()
    const { loading, refreshing, user, dashboardStats, allStreams, agents, detections, refreshingStreams, fetchDashboardData, refreshStream, registerUserActivity, settings } = useMobileDashboardData()
    const activeTab = ref(0)
    const showStreamDetailsModal = ref(false)
    const showAddStreamModal = ref(false)
    const showAgentDetailsModal = ref(false)
    const showAddAgentModal = ref(false)
    const selectedStream = ref(null)
    const selectedAgent = ref(null)
    const jobId = ref(null)
    const addingAgent = ref(false)
    const refreshIntervalMinutes = ref(Math.round(settings.baseRefreshInterval / (60 * 1000)))

    const newAgent = ref({
      username: '',
      email: '',
      password: '',
      receiveUpdates: false
    })

    const tabs = [
      { label: 'Home', icon: 'house' },
      { label: 'Streams', icon: 'video' },
      { label: 'Agents', icon: 'users' },
      { label: 'Notifications', icon: 'bell' },
      { label: 'Settings', icon: 'cog' }
    ]

    const openAddStreamModal = () => {
      showAddStreamModal.value = true
      registerUserActivity()
    }
    const openAddAgentModal = () => {
      showAddAgentModal.value = true
      registerUserActivity()
    }

    const displayStats = computed(() => [
      { label: 'Active Streams', value: dashboardStats.value.ongoing_streams || 0, icon: 'video' },
      { label: 'Active Agents', value: agents.value.length || 0, icon: 'users' },
      { label: 'Detections', value: notifications.value.length || 0, icon: 'eye' }
    ])

    const recentDetections = computed(() => {
      return notifications.value
        .filter(n => n.event_type === 'object_detection')
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 20)
    })

    const handleDarkThemeChange = (value) => {
      isDarkTheme.value = value
      localStorage.setItem('themePreference', value ? 'dark' : 'light')
    }

    const handleBackgroundRefreshChange = (value) => {
      settings.enableBackgroundRefresh = value
    }

    const handleRefreshIntervalChange = (value) => {
      refreshIntervalMinutes.value = value
      settings.baseRefreshInterval = parseInt(value) * 60 * 1000
    }

    const openStreamDetails = (stream) => {
      selectedStream.value = stream
      showStreamDetailsModal.value = true
      registerUserActivity()
    }

    const handleStartStreamCreation = async ({ platform, room_url, agent_id }) => {
      try {
        const token = localStorage.getItem('token')
        if (!token) throw new Error('No authentication token found')
        const payload = { platform, room_url, agent_id: agent_id || null }
        const response = await axios.post('/api/streams/interactive', payload, {
          headers: { Authorization: `Bearer ${token}` }
        })
        jobId.value = response.data.job_id
      } catch (error) {
        console.error('Error starting stream creation:', error)
        const message = error.response?.data?.message || 'Failed to start stream creation'
        if (error.response?.status === 400) {
          toast.error(`Invalid input: ${message}`)
        } else if (error.response?.status === 401) {
          toast.error('Unauthorized: Please log in again')
          router.push('/')
        } else if (error.response?.status === 409) {
          toast.error('Stream already exists')
        } else {
          toast.error('Server error. Please try again.')
        }
        showAddStreamModal.value = false
      }
    }

    const handleStreamCreated = () => {
      fetchDashboardData(false)
      showAddStreamModal.value = false
      jobId.value = null
      toast.success('Stream created')
    }

    const handleStreamUpdated = () => {
      fetchDashboardData(false)
      showStreamDetailsModal.value = false
      toast.success('Stream updated')
    }

    const handleStreamDeleted = () => {
      fetchDashboardData(false)
      showStreamDetailsModal.value = false
      toast.success('Stream deleted')
    }

    const openAgentDetails = (agent) => {
      selectedAgent.value = agent
      showAgentDetailsModal.value = true
      registerUserActivity()
    }

    const handleAgentUpdated = () => {
      fetchDashboardData(false)
      showAgentDetailsModal.value = false
      toast.success('Agent updated')
    }

    const handleAgentDeleted = () => {
      fetchDashboardData(false)
      showAgentDetailsModal.value = false
      toast.success('Agent deleted')
    }

    const handleAgentCreated = async () => {
      addingAgent.value = true
      try {
        const response = await axios.post('/api/register', {
          username: newAgent.value.username,
          email: newAgent.value.email,
          password: newAgent.value.password,
          receiveUpdates: newAgent.value.receiveUpdates
        })
        agents.value = [...agents.value, response.data.user]
        fetchDashboardData(false)
        showAddAgentModal.value = false
        newAgent.value = { username: '', email: '', password: '', receiveUpdates: false }
        toast.success('Agent created')
      } catch (error) {
        const message = error.response?.data?.message || 'Failed to create agent'
        toast.error(message)
      } finally {
        addingAgent.value = false
      }
    }

    const logout = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) throw new Error('No authentication token found')
        await axios.post('/api/logout', {}, {
          headers: { Authorization: `Bearer ${token}` }
        })
        localStorage.removeItem('token')
        toast.info('Logged out successfully')
        router.push('/')
      } catch (error) {
        console.error('Logout failed:', error)
        toast.error(error.response?.data?.message || 'Logout failed')
      }
    }

    onMounted(() => {
      // Remove auto-fetch
      document.addEventListener('click', registerUserActivity)
      document.addEventListener('touchstart', registerUserActivity)
    })

    watch(refreshIntervalMinutes, (newValue) => {
      settings.baseRefreshInterval = parseInt(newValue) * 60 * 1000
    })

    return {
      activeTab,
      tabs,
      isDarkTheme,
      showStreamDetailsModal,
      showAddStreamModal,
      showAgentDetailsModal,
      showAddAgentModal,
      selectedStream,
      selectedAgent,
      refreshIntervalMinutes,
      jobId,
      loading,
      refreshing,
      user,
      dashboardStats,
      allStreams,
      agents,
      detections,
      refreshingStreams,
      notifications,
      notificationsLoading,
      unreadCount,
      groupedNotifications,
      isGroupedByType,
      isGroupedByStream,
      settings,
      displayStats,
      recentDetections,
      newAgent,
      addingAgent,
      refreshData: fetchDashboardData,
      refreshStream,
      openStreamDetails,
      openAgentDetails,
      openAddStreamModal,
      openAddAgentModal,
      handleStartStreamCreation,
      handleStreamCreated,
      handleStreamUpdated,
      handleStreamDeleted,
      handleAgentUpdated,
      handleAgentDeleted,
      handleAgentCreated,
      logout,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      handleDarkThemeChange,
      handleBackgroundRefreshChange,
      handleRefreshIntervalChange,
      fetchNotifications
    }
  }
}
</script>

<style scoped>
.mobile-admin-dashboard {
  font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-x: hidden;
  --primary-color: #4361ee;
  --primary-light: #4361ee20;
  --secondary-color: #3f37c9;
  --danger-color: #e5383b;
  --success-color: #38b000;
  --warning-color: #ffb700;
  --text-color: #333333;
  --text-light: #777777;
  --background-color: #f8f9fa;
  --card-bg: #ffffff;
  --border-color: #e0e0e0;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  --border-radius: 12px;
  --border-radius-sm: 8px;
  background-color: var(--background-color);
  color: var(--text-color);
  padding-bottom: 80px;
}

.mobile-admin-dashboard[data-theme="dark"] {
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

.mobile-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 10;
  transition: var(--transition);
}

.header-title { display: flex; align-items: center; gap: 10px; }
.header-title h1 { font-size: 1.5rem; font-weight: 600; margin: 0; color: var(--text-color); }
.mobile-tag { background-color: var(--primary-light); color: var(--primary-color); font-size: 0.7rem; font-weight: 500; padding: 2px 8px; border-radius: 12px; text-transform: uppercase; }
.refresh-button { background-color: var(--primary-color); color: white; border: none; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: var(--transition); box-shadow: var(--shadow-sm); }
.refresh-button:hover { background-color: var(--secondary-color); }
.refresh-button:disabled { background-color: var(--text-light); cursor: not-allowed; }

.stats-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; padding: 16px; margin-bottom: 16px; }
.stat-card { background-color: var(--card-bg); border-radius: var(--border-radius); padding: 14px; display: flex; flex-direction: column; align-items: center; box-shadow: var(--shadow-sm); transition: var(--transition); border: 1px solid var(--border-color); }
.stat-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.stat-icon { background-color: var(--primary-light); color: var(--primary-color); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; font-size: 1.2rem; }
.stat-content { text-align: center; }
.stat-value { font-weight: 700; font-size: 1.4rem; margin-bottom: 2px; color: var(--text-color); }
.stat-label { font-size: 0.75rem; color: var(--text-light); white-space: nowrap; }

.mobile-tabs { display: flex; justify-content: space-between; align-items: center; position: fixed; bottom: 0; left: 0; right: 0; background-color: var(--card-bg); padding: 6px 12px; box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1); z-index: 20; border-top: 1px solid var(--border-color); transition: var(--transition); }
.tab-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 8px 0; cursor: pointer; transition: var(--transition); position: relative; color: var(--text-light); }
.tab-item.active { color: var(--primary-color); }
.tab-item:hover { color: var(--secondary-color); }
.tab-icon-container { position: relative; margin-bottom: 4px; }
.tab-icon { font-size: 1.2rem; }
.notification-badge { position: absolute; top: -8px; right: -8px; background-color: var(--danger-color); color: white; font-size: 0.6rem; font-weight: 600; min-width: 18px; height: 18px; border-radius: 9px; display: flex; align-items: center; justify-content: center; padding: 0 4px; }
.tab-label { font-size: 0.7rem; font-weight: 500; }

.tab-content { flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch; }

/* Bottom Sheet */
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: var(--card-bg);
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  box-shadow: var(--shadow-md);
  transform: translateY(100%);
  transition: transform 0.3s ease-in-out;
  z-index: 1000;
  max-height: 90vh;
  overflow-y: auto;
}

.bottom-sheet.active {
  transform: translateY(0);
}

.bottom-sheet-content {
  padding: 16px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-color);
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--border-radius-sm);
  border: none;
  background-color: var(--border-color);
  color: var(--text-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition);
}

.close-btn:hover {
  background-color: var(--primary-light);
}

/* Form Styles */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: var(--text-color);
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  background-color: var(--background-color);
  color: var(--text-color);
  font-size: 0.875rem;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.form-input::placeholder {
  color: var(--text-light);
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.cancel-btn,
.submit-btn {
  flex: 1;
  padding: 12px;
  border-radius: var(--border-radius-sm);
  border: none;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
}

.cancel-btn {
  background-color: var(--border-color);
  color: var(--text-color);
}

.cancel-btn:hover {
  background-color: #d1d5db;
}

.submit-btn {
  background-color: var(--primary-color);
  color: white;
}

.submit-btn:hover {
  background-color: var(--secondary-color);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 340px) {
  .stats-container { grid-template-columns: repeat(1, 1fr); }
  .tab-label { font-size: 0.65rem; }
}

@media (min-width: 341px) and (max-width: 480px) {
  .stats-container { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .stat-icon { width: 30px; height: 30px; font-size: 1rem; }
  .stat-value { font-size: 1.2rem; }
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideIn { from { transform: translateY(10px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.tab-content > * { animation: fadeIn 0.3s ease; }
.stat-card { animation: slideIn 0.3s ease; animation-fill-mode: both; }
.stat-card:nth-child(1) { animation-delay: 0.1s; }
.stat-card:nth-child(2) { animation-delay: 0.2s; }
.stat-card:nth-child(3) { animation-delay: 0.3s; }
</style>