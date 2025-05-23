<template>
  <div class="admin-container" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="dashboard-wrapper">
      <AdminSidebar
        :active-tab="activeTab"
        :user="user"
        :is-online="isOnline"
        :notifications="notifications"
        :messages="messages"
        :message-unread-count="messageUnreadCount"
        @tab-change="activeTab = $event"
        @sidebar-toggle="debouncedHandleSidebarToggle"
      />

      <main 
        class="main-content" 
        :class="{ 'sidebar-minimized': sidebarMinimized }"
        ref="mainContent"
      >
        <div v-if="loading || hasError" class="skeleton-loading">
          <!-- Skeleton for Stats Section -->
          <div class="skeleton-stats-section">
            <div v-for="n in 3" :key="'stat-' + n" class="skeleton-stat-card">
              <div class="skeleton-icon"></div>
              <div class="skeleton-text skeleton-value"></div>
              <div class="skeleton-text skeleton-label"></div>
            </div>
          </div>

          <!-- Skeleton for Streams Section -->
          <div class="skeleton-streams-section">
            <div class="skeleton-section-header">
              <div class="skeleton-text skeleton-header"></div>
            </div>
            <div class="skeleton-stream-container">
              <div v-for="n in 3" :key="'stream-' + n" class="skeleton-stream-card">
                <div class="skeleton-thumbnail"></div>
                <div class="skeleton-content">
                  <div class="skeleton-text skeleton-title"></div>
                  <div class="skeleton-text skeleton-subtitle"></div>
                  <div class="skeleton-text skeleton-details"></div>
                </div>
              </div>
            </div>
          </div>
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
          >
            <button v-if="hasMoreStreams" @click="loadMoreStreams" class="load-more-button">
              Load More
            </button>
          </StreamsTab>

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
    </div>

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
  --sidebar-width-expanded: 250px;
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
  --skeleton-bg: rgba(200, 200, 200, 0.2);
}

[data-theme="dark"] {
  --primary-rgb: 96, 165, 250;
  --secondary-rgb: 156, 163, 175;
  --success-rgb: 34, 197, 94;
  --danger-rgb: 248, 113, 113;
  --warning-rgb: 251, 191, 36;
  --info-rgb: 56, 189, 248;
  --skeleton-bg: rgba(100, 100, 100, 0.2);
}

.admin-container {
  min-height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow-x: hidden;
}

.dashboard-wrapper {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding: 2rem;
  margin-left: var(--sidebar-width-expanded);
  transition: margin-left 0.2s ease;
  will-change: margin-left;
}

.main-content.sidebar-minimized {
  margin-left: var(--sidebar-width-collapsed);
}

.skeleton-loading {
  max-width: 100%;
  margin: 1rem auto;
  padding: 1.5rem;
}

.skeleton-stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.skeleton-stat-card {
  background: var(--skeleton-bg);
  border-radius: 8px;
  padding: 1.5rem;
  height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: pulse 1.5s infinite ease-in-out;
}

.skeleton-icon {
  width: 24px;
  height: 24px;
  background: var(--skeleton-bg);
  border-radius: 50%;
  margin-bottom: 0.5rem;
}

.skeleton-text {
  background: var(--skeleton-bg);
  border-radius: 4px;
}

.skeleton-value {
  width: 60%;
  height: 20px;
  margin-bottom: 0.5rem;
}

.skeleton-label {
  width: 40%;
  height: 16px;
}

.skeleton-streams-section {
  margin-top: 2rem;
}

.skeleton-section-header {
  margin-bottom: 1rem;
}

.skeleton-header {
  width: 200px;
  height: 24px;
  background: var(--skeleton-bg);
  border-radius: 4px;
}

.skeleton-stream-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.skeleton-stream-card {
  background: var(--skeleton-bg);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  gap: 1rem;
  height: 150px;
  animation: pulse 1.5s infinite ease-in-out;
}

.skeleton-thumbnail {
  width: 120px;
  height: 90px;
  background: var(--skeleton-bg);
  border-radius: 4px;
}

.skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-title {
  width: 80%;
  height: 20px;
}

.skeleton-subtitle {
  width: 60%;
  height: 16px;
}

.skeleton-details {
  width: 40%;
  height: 16px;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.load-more-button {
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
  transition: all 0.2s ease;
  margin: 1rem auto;
}

.load-more-button:hover {
  opacity: 0.9;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .dashboard-wrapper {
    flex-direction: column;
  }

  .main-content {
    margin-left: 0;
    height: calc(100vh - var(--sidebar-mobile-height));
    transition: margin-top 0.2s ease;
  }

  .main-content.sidebar-minimized {
    margin-left: 0;
  }

  .skeleton-stats-section {
    grid-template-columns: 1fr;
  }

  .skeleton-stream-container {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 769px) and (max-width: 1023px) {
  .skeleton-loading {
    max-width: 600px;
  }
}
</style>