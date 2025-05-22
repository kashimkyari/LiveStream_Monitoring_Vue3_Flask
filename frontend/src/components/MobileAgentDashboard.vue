<template>
  <div class="mobile-agent-dashboard" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="page-header">
      <h1>Agent Dashboard <span class="mobile-badge">Mobile</span></h1>
    </div>

    <div class="dashboard-tabs">
      <div v-for="(tab, index) in tabs" :key="index" class="tab-item" :class="{ active: activeTab === index }"
        @click="activeTab = index">
        <div class="tab-icon-container">
          <font-awesome-icon :icon="tab.icon" class="tab-icon" />
          <span v-if="tab.icon === 'bell' && unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' :
            unreadCount }}</span>
        </div>
        <span class="tab-text">{{ tab.name }}</span>
      </div>
    </div>

    <div class="tab-content">
      <MobileAgentStreams v-if="activeTab === 0" :assignments="assignments" :is-loading="isLoadingAssignments"
        @refresh="loadAssignments" @open-stream="openStreamDetails" />

      <MobileAgentAnalytics v-else-if="activeTab === 1" :stats="stats" />

      <MobileAgentMessages v-else-if="activeTab === 2" :conversations="conversations"
        :selected-conversation="selectedConversation" :messages="activeConversationMessages" :new-message="newMessage"
        :is-loading="isLoadingMessages" :is-sending="isSendingMessage" @load-conversations="loadConversations"
        @open-conversation="openConversation" @close-conversation="closeConversation" @send-message="sendMessage" />

      <MobileAgentNotifications v-else-if="activeTab === 3" :notifications="notifications.items"
        :unread-count="unreadCount" @mark-read="markAsRead" @mark-all-read="markAllAsRead" />

      <MobileAgentSettings v-else-if="activeTab === 4" :settings="settings" :is-dark-theme="isDarkTheme"
        @toggle-setting="toggleSetting" @set-theme="setTheme" @save-settings="saveSettings" />
    </div>
  </div>
</template>

<script>
/* eslint-disable */
import { ref, inject, onMounted, watch, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import AuthService from '../services/AuthService'
import MessageService from '../services/MessageService'
import { formatDistance, format } from 'date-fns'
import { useMobileNotifications } from '../composables/useMobileNotifications'
import anime from 'animejs/lib/anime.es'
import io from 'socket.io-client'
import axios from 'axios'

// Components
import MobileAgentStreams from './MobileAgentStreams.vue'
import MobileAgentAnalytics from './MobileAgentAnalytics.vue'
import MobileAgentMessages from './MobileAgentMessages.vue'
import MobileAgentNotifications from './MobileAgentNotifications.vue'
import MobileAgentSettings from './MobileAgentSettings.vue'

export default {
  name: 'MobileAgentDashboard',
  components: {
    MobileAgentStreams,
    MobileAgentAnalytics,
    MobileAgentMessages,
    MobileAgentNotifications,
    MobileAgentSettings
  },
  setup() {
    const isDarkTheme = ref(localStorage.getItem('themePreference') === 'dark')
    const updateAppTheme = inject('updateTheme', null)
    const currentAgentId = ref(null)
    const toast = useToast()

    // Settings - Added missing settings object
    const settings = ref({
      enableNotifications: true,
      enableSound: true,
      autoRefresh: true,
      refreshInterval: 30,
      showOfflineStreams: false
    })

    // Missing methods for settings
    const toggleSetting = (setting) => {
      settings.value[setting] = !settings.value[setting]
    }

    const saveSettings = async () => {
      try {
        // Mock save settings to localStorage for now
        localStorage.setItem('agentSettings', JSON.stringify(settings.value))
        toast.success('Settings saved successfully')
      } catch (error) {
        toast.error('Failed to save settings')
      }
    }

    // Tabs
    const tabs = [
      { name: 'Streams', icon: 'video' },
      { name: 'Analytics', icon: 'chart-line' },
      { name: 'Messages', icon: 'comment' },
      { name: 'Alerts', icon: 'bell' },
      { name: 'Settings', icon: 'cog' }
    ]
    const activeTab = ref(0)

    // Streams
    const assignments = ref([])
    const isLoadingAssignments = ref(false)
    const stats = ref({
      totalAssignments: 0,
      activeStreams: 0,
      completedToday: 0
    })

    // Missing method for opening stream details
    const openStreamDetails = (streamId) => {
      // Implementation would go here
      console.log('Opening stream details for stream ID:', streamId)
    }

    // Notifications
    const {
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      formatTimeAgo: formatNotificationTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle
    } = useMobileNotifications()

    // Messages
    const conversations = ref([])
    const isLoadingMessages = ref(false)
    const selectedConversation = ref(null)
    const activeConversationMessages = ref([])
    const newMessage = ref('')
    const isSendingMessage = ref(false)
    const currentUserId = parseInt(localStorage.getItem('userId')) || null
    let socket = null

    // Missing message methods
    const loadConversations = async () => {
      isLoadingMessages.value = true
      try {
        // Implementation would go here
        console.log('Loading conversations')
      } catch (error) {
        toast.error('Failed to load conversations')
      } finally {
        isLoadingMessages.value = false
      }
    }

    const openConversation = (conversation) => {
      selectedConversation.value = conversation
      // Load messages for this conversation
      console.log('Opening conversation', conversation)
    }

    const closeConversation = () => {
      selectedConversation.value = null
      activeConversationMessages.value = []
    }

    const sendMessage = async (content) => {
      if (!content.trim() || !selectedConversation.value) return

      isSendingMessage.value = true
      try {
        // Implementation would go here
        console.log('Sending message:', content)
        newMessage.value = ''
      } catch (error) {
        toast.error('Failed to send message')
      } finally {
        isSendingMessage.value = false
      }
    }

    // Core Functions
    const loadAssignments = async () => {
      isLoadingAssignments.value = true
      try {
        const sessionResponse = await axios.get('/api/session')
        currentAgentId.value = sessionResponse.data.user.id
        const streamsResponse = await axios.get('/api/streams')

        assignments.value = Object.values(streamsResponse.data)
          .filter(stream => stream.assignments?.some(a => a.agent_id === currentAgentId.value))
          .map(stream => ({
            ...stream,
            video_url: stream.platform === 'Chaturbate'
              ? stream.chaturbate_m3u8_url
              : stream.stripchat_m3u8_url
          }))

        calculateStats()
      } catch (error) {
        toast.error('Failed to load assignments')
      } finally {
        isLoadingAssignments.value = false
      }
    }

    const calculateStats = () => {
      stats.value = {
        totalAssignments: assignments.value.length,
        activeStreams: assignments.value.filter(a => a.stream_status === 'live').length,
        completedToday: assignments.value.filter(a =>
          a.completed && new Date(a.completed_at).toDateString() === new Date().toDateString()
        ).length
      }
    }

    // Theme
    const setTheme = (isDark) => {
      isDarkTheme.value = isDark
      localStorage.setItem('themePreference', isDark ? 'dark' : 'light')
      if (updateAppTheme) updateAppTheme(isDark)
    }

    // Messages
    const initializeSocketConnection = () => {
      socket = io('https://monitor-backend.jetcamstudio.com:5000', {
        path: '/ws',
        transports: ['websocket'],
        query: { userId: currentUserId }
      })

      socket.on('new_message', (message) => {
        if (selectedConversation.value?.userId === message.sender_id) {
          activeConversationMessages.value.push(message)
          scrollToBottom()
        }
      })
    }

    const scrollToBottom = () => {
      nextTick(() => {
        const container = document.querySelector('.messages-container')
        if (container) container.scrollTop = container.scrollHeight
      })
    }

    onMounted(() => {
      loadAssignments()
      if (currentUserId) initializeSocketConnection()

      // Load settings from localStorage if available
      const savedSettings = localStorage.getItem('agentSettings')
      if (savedSettings) {
        settings.value = JSON.parse(savedSettings)
      }
    })

    return {
      // State
      tabs,
      activeTab,
      isDarkTheme,
      settings,
      assignments,
      isLoadingAssignments,
      stats,
      notifications,
      unreadCount,
      conversations,
      isLoadingMessages,
      selectedConversation,
      activeConversationMessages,
      newMessage,
      isSendingMessage,

      // Methods
      loadAssignments,
      openStreamDetails,
      setTheme,
      markAsRead,
      markAllAsRead,
      toggleSetting,
      saveSettings,
      loadConversations,
      openConversation,
      closeConversation,
      sendMessage,
      scrollToBottom,
      formatNumber: num => num >= 1000 ? `${(num / 1000).toFixed(1)}K` : num,
      formatStreamTime: ts => ts ? formatDistance(new Date(ts), new Date(), { addSuffix: true }) : 'Unknown'
    }
  }
}
</script>


<style scoped>
.mobile-agent-dashboard {
  padding: 1rem;
  max-width: 100%;
  min-height: 100vh;
  background-color: var(--body-bg);
  color: var(--text-color);
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h1 {
  font-size: 1.5rem;
  display: flex;
  align-items: center;
}

.mobile-badge {
  font-size: 0.7rem;
  background-color: var(--primary-color);
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  margin-left: 0.5rem;
  vertical-align: middle;
}

.dashboard-tabs {
  display: flex;
  background-color: var(--input-bg);
  border-radius: 8px;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 10;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 0.8rem 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 2px solid transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.tab-item.active {
  border-bottom-color: var(--primary-color);
  color: var(--primary-color);
}

.tab-icon-container {
  position: relative;
  display: inline-block;
}

.tab-icon {
  font-size: 1.2rem;
  margin-bottom: 0.3rem;
}

.notification-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background-color: var(--danger-color, #dc3545);
  color: white;
  border-radius: 10px;
  font-size: 0.6rem;
  min-width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.tab-text {
  font-size: 0.8rem;
  font-weight: 500;
}

/* Stream Cards */
.stream-card {
  padding: 1rem;
  background-color: var(--input-bg);
  border-radius: 8px;
  margin-bottom: 1rem;
  transition: transform 0.2s;
}

.stream-card:hover {
  transform: translateY(-2px);
}

.stream-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.8rem;
}

.stream-platform {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-transform: capitalize;
}

.stream-platform.chaturbate {
  background-color: #f5a623;
  color: white;
}

.stream-platform.stripchat {
  background-color: #7e57c2;
  color: white;
}

.stream-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--text-light);
}

/* Notifications */
.notification-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  background-color: var(--input-bg);
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.notification-item.unread {
  border-left: 3px solid var(--primary-color);
}

.notification-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
}

.notification-content {
  flex: 1;
}

/* Messages */
.conversation-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  background-color: var(--input-bg);
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--secondary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
}

.online-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #28a745;
  position: absolute;
  bottom: 0;
  right: 0;
}

.message-bubble {
  max-width: 80%;
  padding: 0.8rem;
  border-radius: 12px;
  margin-bottom: 0.5rem;
}

.message-bubble.outgoing {
  background-color: var(--primary-color);
  color: white;
  margin-left: auto;
}

.message-bubble.incoming {
  background-color: var(--input-bg);
}

/* Settings */
.toggle-switch {
  width: 48px;
  height: 24px;
  border-radius: 12px;
  background-color: var(--border-color);
  position: relative;
  cursor: pointer;
  transition: background-color 0.2s;
}

.toggle-switch.active {
  background-color: var(--primary-color);
}

.toggle-switch-handle {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: white;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.theme-option {
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.theme-option.selected {
  background-color: var(--primary-color);
  color: white;
}

/* Utilities */
.loading-container {
  display: flex;
  justify-content: center;
  padding: 2rem 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-color);
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-light);
}

.refresh-button {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: var(--text-color);
}

.card {
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
</style>