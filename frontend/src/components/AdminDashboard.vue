<template>
  <div class="admin-container" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <AdminSidebar
      :active-tab="activeTab"
      :user="user"
      :is-online="isOnline"
      :notifications="notifications"
      :messages="messages"
      :message-unread-count="messageUnreadCount"
      @tab-change="activeTab = $event"
      @sidebar-toggle="handleSidebarToggle"
    />

    <main 
      class="main-content" 
      :class="{ 'sidebar-minimized': sidebarMinimized }"
      ref="mainContent"
    >
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading...</p>
      </div>

      <div v-else-if="hasError" class="error-state">
        <h3>Something went wrong</h3>
        <p>{{ errorMessage }}</p>
        <button @click="fetchDashboardData" class="refresh-button">
          <font-awesome-icon icon="sync" class="icon" /> Retry
        </button>
      </div>

      <template v-else>
        <DashboardTab
          v-show="activeTab === 'dashboard'"
          :dashboard-stats="dashboardStats"
          :streams="streams"
          :detections="detections"
          :agents="agents"  
          @open-stream="openStreamDetails"
        />

        <StreamsTab
          v-show="activeTab === 'streams'"
          :streams="allStreams"
          :agents="agents"
          @create="showCreateStreamModal = true"
          @edit="editStream"
          @delete="confirmDeleteStream"
          @view="openStreamDetails"
          @refresh="refreshStream"
          @stream-updated="handleStreamUpdated"
          @stream-created="handleStreamCreated"
          @stream-deleted="handleStreamDeleted"
        />

        <AgentsTab
          v-show="activeTab === 'agents'"
          :agents="agents"
          @create="showCreateAgentModal = true"
          @edit="editAgent"
          @delete="confirmDeleteAgent"
        />

        <AdminMessageComponent
          v-show="activeTab === 'messages'"
          :user="user"
        />
        <AdminNotificationsPage
          v-show="activeTab === 'notifications'"
          :user="user"
        />

        <AdminSettingsPage
          v-show="activeTab === 'settings'"
          :user="user"
        />
      </template>
    </main>

    <!-- Modals -->
    <StreamDetailsModal
      v-if="selectedStream"
      :stream="selectedStream"
      :detections="getStreamDetections(selectedStream.room_url)"
      @close="closeModal"
      @assign="assignAgent"
      @refresh="refreshStream"
    />

    <CreateStreamModal
      v-if="showCreateStreamModal"
      :agents="agents"
      :creation-state="streamCreationState"
      @close="showCreateStreamModal = false"
      @submit="createStream"
    />

    <CreateAgentModal
      v-if="showCreateAgentModal"
      @close="showCreateAgentModal = false"
      @submit="createAgent"
    />

    <ConfirmationModal
      v-if="confirmationModal.show"
      :title="confirmationModal.title"
      :message="confirmationModal.message"
      :action-text="confirmationModal.actionText"
      @close="confirmationModal.show = false"
      @confirm="confirmAction"
    />
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useAdminDashboard } from '@/composables/useAdminDashboard'
import { useDashboardData } from '@/composables/useDashboardData'
import { useModalActions } from '@/composables/useModalActions'
import { useMessageData } from '@/composables/useMessageData'
import anime from 'animejs/lib/anime.es.js'

// Components
import AdminSidebar from './AdminSidebar.vue'
import DashboardTab from './DashboardTab.vue'
import StreamsTab from './StreamsTab.vue'
import AgentsTab from './AgentsTab.vue'
import AdminMessageComponent from './AdminMessageComponent.vue'
import StreamDetailsModal from './StreamDetailsModal.vue'
import CreateStreamModal from './CreateStreamModal.vue'
import CreateAgentModal from './CreateAgentModal.vue'
import ConfirmationModal from './ConfirmationModal.vue'
import AdminNotificationsPage from './AdminNotificationsPage.vue'
import AdminSettingsPage from './AdminSettingsPage.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import axios from 'axios'

export default {
  name: 'AdminDashboard',
  components: {
    AdminSidebar,
    DashboardTab,
    StreamsTab,
    AgentsTab,
    AdminMessageComponent,
    StreamDetailsModal,
    CreateStreamModal,
    CreateAgentModal,
    ConfirmationModal,
    FontAwesomeIcon,
    AdminNotificationsPage,
    AdminSettingsPage
  },
  methods: {
    async loadStreams() {
      try {
        const response = await axios.get('/api/streams')
        this.streams = response.data
        this.allStreams = response.data
      } catch (error) {
        console.error('Error loading streams:', error)
        this.hasError = true
        this.errorMessage = 'Failed to load streams'
      }
    },
    
    handleStreamCreated() {
      // Reload streams to get fresh data
      this.loadStreams()
    },
    
    handleStreamUpdated({ streamId, status, is_monitored, viewers }) {
      if (!this.streams || !this.allStreams) return
      
      // Update streams
      const streamIndex = this.streams.findIndex(s => s.id === streamId)
      if (streamIndex !== -1) {
        const updatedStream = {
          ...this.streams[streamIndex],
          status,
          is_monitored,
          viewers: viewers !== undefined ? viewers : this.streams[streamIndex].viewers
        }
        this.streams = [
          ...this.streams.slice(0, streamIndex),
          updatedStream,
          ...this.streams.slice(streamIndex + 1)
        ]
      }

      // Update allStreams
      const allStreamIndex = this.allStreams.findIndex(s => s.id === streamId)
      if (allStreamIndex !== -1) {
        const updatedAllStream = {
          ...this.allStreams[allStreamIndex],
          status,
          is_monitored,
          viewers: viewers !== undefined ? viewers : this.allStreams[allStreamIndex].viewers
        }
        this.allStreams = [
          ...this.allStreams.slice(0, allStreamIndex),
          updatedAllStream,
          ...this.allStreams.slice(allStreamIndex + 1)
        ]
      }
    },
    
    handleStreamDeleted(streamId) {
      if (!this.streams || !this.allStreams) return
      this.streams = this.streams.filter(s => s.id !== streamId)
      this.allStreams = this.allStreams.filter(s => s.id !== streamId)
    },

    handleNotification(notification) {
      console.log('Notification received:', notification)
    },

    handleModalClosed() {
      console.log('Modal closed')
    },

    fetchKeywords() {
      console.log('Fetching keywords')
    },

    fetchObjects() {
      console.log('Fetching objects')
    },

    fetchTelegramRecipients() {
      console.log('Fetching telegram recipients')
    }
  },
  setup() {
    const router = useRouter()
    const toast = useToast()
    const mainContent = ref(null)
    const animeInstances = ref([])

    const {
      isDarkTheme,
      activeTab,
      isOnline,
      sidebarMinimized,
      notifications,
      handleSidebarToggle: originalHandleSidebarToggle
    } = useAdminDashboard()

    const {
      loading,
      hasError,
      errorMessage,
      user,
      dashboardStats,
      streams,
      allStreams,
      agents,
      detections,
      fetchDashboardData,
      getStreamDetections,
      refreshStream
    } = useDashboardData(router, toast)

    const {
      selectedStream,
      showCreateStreamModal,
      showCreateAgentModal,
      confirmationModal,
      streamCreationState,
      openStreamDetails,
      closeModal,
      assignAgent,
      createStream,
      editStream,
      confirmDeleteStream,
      deleteStream,
      createAgent,
      editAgent,
      confirmDeleteAgent,
      deleteAgent,
      confirmAction
    } = useModalActions(toast, fetchDashboardData, agents)

    const {
      messages,
      fetchMessages,
      messageUnreadCount
    } = useMessageData(user)

    const enhanceStreamWithUsername = (stream) => {
      if (!stream || !agents.value) return stream
      const assignedAgent = agents.value.find(agent => agent.id === stream.assigned_agent_id)
      return {
        ...stream,
        agent_username: assignedAgent ? assignedAgent.username : 'Unassigned',
        agent_status: assignedAgent ? assignedAgent.status : 'inactive'
      }
    }

    const enhancedStreams = computed(() => {
      if (!streams.value) return []
      return streams.value.map(stream => enhanceStreamWithUsername(stream))
    })

    const safeAnimate = (targets, animation) => {
      if (!targets) return null
      try {
        const instance = anime({
          targets,
          ...animation
        })
        animeInstances.value.push(instance)
        return instance
      } catch (error) {
        console.error('Animation error:', error)
        return null
      }
    }

    const handleSidebarToggle = (isMinimized) => {
      originalHandleSidebarToggle(isMinimized)
      nextTick(() => {
        if (mainContent.value) {
          safeAnimate(mainContent.value, {
            marginLeft: isMinimized 
              ? (window.innerWidth <= 768 ? '0' : 'var(--sidebar-width-collapsed)')
              : (window.innerWidth <= 768 ? '0' : 'var(--sidebar-width-expanded)'),
            duration: 300,
            easing: 'easeOutQuad'
          })
          const contentDiv = mainContent.value.querySelector(':scope > div')
          if (contentDiv) {
            safeAnimate(contentDiv, {
              opacity: [0.9, 1],
              translateX: [isMinimized ? '-10px' : '10px', '0'],
              duration: 350,
              easing: 'spring(1, 80, 12, 0)'
            })
          }
        }
      })
    }

    watch(activeTab, (newTab, oldTab) => {
      if (newTab !== oldTab) {
        nextTick(() => {})
      }
    })

    const cleanupAnimations = () => {
      animeInstances.value.forEach(instance => {
        if (instance && typeof instance.pause === 'function') {
          instance.pause()
        }
      })
      animeInstances.value = []
    }

    onMounted(() => {
      const onlineHandler = () => { isOnline.value = true }
      const offlineHandler = () => { isOnline.value = false }
      window.addEventListener('online', onlineHandler)
      window.addEventListener('offline', offlineHandler)
      
      try {
        fetchDashboardData()
          .then(() => {
            nextTick(() => {
              if (mainContent.value) {
                safeAnimate(mainContent.value, {
                  opacity: [0, 1],
                  translateY: ['20px', '0'],
                  duration: 600,
                  easing: 'spring(1, 80, 10, 0)'
                })
              }
            })
          })
          .catch(error => console.error('Error fetching dashboard data:', error))
        
        fetchMessages()
          .catch(error => console.error('Error fetching messages:', error))
      } catch (e) {
        console.error('Error in onMounted:', e)
      }

      onBeforeUnmount(() => {
        window.removeEventListener('online', onlineHandler)
        window.removeEventListener('offline', offlineHandler)
        cleanupAnimations()
      })
    })

    const onlineStreams = computed(() => {
      return allStreams.value.filter(stream => stream.status === 'online')
    })

    const offlineStreams = computed(() => {
      return allStreams.value.filter(stream => stream.status === 'offline')
    })

    return {
      isDarkTheme,
      activeTab,
      loading,
      hasError,
      errorMessage,
      isOnline,
      user,
      sidebarMinimized,
      notifications,
      streamCreationState,
      mainContent,
      dashboardStats,
      streams,
      allStreams,
      enhancedStreams,
      agents,
      detections,
      messages,
      messageUnreadCount,
      selectedStream,
      showCreateStreamModal,
      showCreateAgentModal,
      confirmationModal,
      fetchDashboardData,
      getStreamDetections,
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
      confirmAction,
      handleSidebarToggle,
      enhanceStreamWithUsername,
      onlineStreams,
      offlineStreams
    }
  }
}
</script>

<style scoped>
:root {
  --sidebar-width-expanded: 0px;
  --sidebar-width-collapsed: 50px;
  --sidebar-mobile-height: 65px;
  --stream-base-width: 480px;
  --stream-base-height: 360px;
  --stream-min-width: 240px;
  --stream-min-height: 180px;
  --primary-rgb: 59, 130, 246;
  --secondary-rgb: 156, 163, 175;
  --success-rgb: 16, 185, 129;
  --danger-rgb: 239, 68, 68;
  --warning-rgb: 245, 158, 11;
  --info-rgb: 14, 165, 233;
}

[data-theme="dark"] {
  --primary-rgb: 96, 165, 250;
  --secondary-rgb: 156, 163, 175;
  --success-rgb: 34, 197, 94;
  --danger-rgb: 248, 113, 113;
  --warning-rgb: 251, 191, 36;
  --info-rgb: 56, 189, 248;
}

.admin-container {
  min-height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow-x: hidden;
  
}

.main-content {
  flex: 1;
  padding: 2rem;
  transition: margin-left 0.3s ease;
  height: 90%;
  will-change: margin-left, transform;
}

.error-state {
  max-width: 100%;
  margin: 1rem auto;
  padding: 1.5rem;
  text-align: center;
  background-color: var(--error-bg);
  border: 1px solid var(--error-border);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.error-state h3 {
  margin-bottom: 0.5rem;
  color: var(--text-color);
  font-size: 1.25rem;
}

.error-state p {
  margin-bottom: 1rem;
  color: var(--text-color);
  font-size: 1rem;
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  background-color: var(--primary-color);
  color: white;
  font-weight: 500;
  cursor: pointer;
  border: none;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.refresh-button:hover {
  opacity: 0.9;
}

.icon {
  font-size: 1rem;
  display: inline-block;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  gap: 1rem;
}

.loading-spinner {
  width: 3rem;
  height: 3rem;
  border: 0.25rem solid rgba(var(--primary-rgb), 0.1);
  border-radius: 50%;
  border-top-color: rgb(var(--primary-rgb));
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .admin-container {
    flex-direction: column;
  }

  .main-content {
    margin-left: 0 !important;
    height: calc(100vh - var(--sidebar-mobile-height));
    transition: margin-top 0.3s ease;
  }
}

@media (min-width: 769px) and (max-width: 1023px) {
  .error-state {
    max-width: 600px;
  }
}
</style>