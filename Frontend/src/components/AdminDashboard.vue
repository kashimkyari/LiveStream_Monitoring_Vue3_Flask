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
      :class="{ 'sidebar-expanded': !sidebarMinimized, 'sidebar-collapsed': sidebarMinimized }"
      ref="mainContent"
    >
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading dashboard data...</p>
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
          v-if="activeTab === 'dashboard'"
          :dashboard-stats="dashboardStats"
          :streams="streams"
          :detections="detections"
          @open-stream="openStreamDetails"
        />

        <StreamsTab
          v-if="activeTab === 'streams'"
          :streams="allStreams"
          :agents="agents"
          @create="showCreateStreamModal = true"
          @edit="editStream"
          @delete="confirmDeleteStream"
        />

        <AgentsTab
          v-if="activeTab === 'agents'"
          :agents="agents"
          @create="showCreateAgentModal = true"
          @edit="editAgent"
          @delete="confirmDeleteAgent"
        />

        <MessageComponent
          v-if="activeTab === 'messages'"
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
import { ref, onMounted, nextTick } from 'vue'
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
import MessageComponent from './MessageComponent.vue'
import StreamDetailsModal from './StreamDetailsModal.vue'
import CreateStreamModal from './CreateStreamModal.vue'
import CreateAgentModal from './CreateAgentModal.vue'
import ConfirmationModal from './ConfirmationModal.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

export default {
  name: 'AdminDashboard',
  components: {
    AdminSidebar,
    DashboardTab,
    StreamsTab,
    AgentsTab,
    MessageComponent,
    StreamDetailsModal,
    CreateStreamModal,
    CreateAgentModal,
    ConfirmationModal,
    FontAwesomeIcon
  },
  setup() {
    const router = useRouter()
    const toast = useToast()
    const mainContent = ref(null)

    // Composable integrations
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

    // Message data - new composable to handle message fetching
    const {
      messages,
      fetchMessages,
      messageUnreadCount
    } = useMessageData(user)

    // Enhanced sidebar toggle handler with animations
    const handleSidebarToggle = (isMinimized) => {
      originalHandleSidebarToggle(isMinimized)
      nextTick(() => {
        if (mainContent.value) {
          // Calculate margin values based on device width using CSS variables
          const expandedMargin = window.innerWidth <= 768 ? '0' : 'var(--sidebar-width-expanded)'
          const collapsedMargin = window.innerWidth <= 768 ? '0' : 'var(--sidebar-width-collapsed)'

          // Animate the main content margin so it starts exactly after the sidebar
          anime({
            targets: mainContent.value,
            marginLeft: isMinimized ? collapsedMargin : expandedMargin,
            duration: 300,
            easing: 'easeOutQuad'
          })

          // Optionally animate other content properties
          anime({
            targets: mainContent.value.querySelector(':scope > div'),
            opacity: [0.9, 1],
            translateX: [isMinimized ? '-10px' : '10px', '0'],
            duration: 350,
            easing: 'spring(1, 80, 12, 0)'
          })
        }
      })
    }

    // Lifecycle hooks
    onMounted(() => {
      fetchDashboardData()
      fetchMessages()

      const refreshInterval = setInterval(() => {
        fetchDashboardData()
        fetchMessages()
      }, 30000)

      window.addEventListener('online', () => isOnline.value = true)
      window.addEventListener('offline', () => isOnline.value = false)
      isOnline.value = navigator.onLine

      // Initial animation for page load
      if (mainContent.value) {
        anime({
          targets: mainContent.value,
          opacity: [0, 1],
          translateY: ['20px', '0'],
          duration: 600,
          easing: 'spring(1, 80, 10, 0)'
        })
      }

      return () => {
        clearInterval(refreshInterval)
        window.removeEventListener('online', () => isOnline.value = true)
        window.removeEventListener('offline', () => isOnline.value = false)
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
      sidebarMinimized,
      notifications,
      streamCreationState,
      mainContent,

      // Data
      dashboardStats,
      streams,
      allStreams,
      agents,
      detections,

      // Message data
      messages,
      messageUnreadCount,

      // Modals
      selectedStream,
      showCreateStreamModal,
      showCreateAgentModal,
      confirmationModal,

      // Methods
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
      handleSidebarToggle
    }
  }
}
</script>

<style>
/* Define CSS variables to control sidebar width and mobile height */
:root {
  --sidebar-width-expanded: 280px;
  --sidebar-width-collapsed: 70px;
  --sidebar-mobile-height: 65px;
}

.admin-container {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow-x: hidden; /* Prevent horizontal scrollbar during animations */
}

/* Main content starts right after the sidebar using CSS variables */
.main-content {
  flex: 1;
  padding: 1rem;
  transition: margin-left 0.3s ease; /* Smooth transition for margin */
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  will-change: margin-left, transform; /* Optimize for animations */
}

.main-content.sidebar-expanded {
  margin-left: var(--sidebar-width-expanded);
}

.main-content.sidebar-collapsed {
  margin-left: var(--sidebar-width-collapsed);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  transition: opacity 0.3s ease; /* Smooth transition for content */
}

.loading-state p {
  margin-top: 1rem;
  font-size: 1rem;
  color: var(--text-color);
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

.loading-spinner {
  width: 3rem;
  height: 3rem;
  border: 0.25rem solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Tab transition animations */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Responsive layouts */
@media (max-width: 768px) {
  .admin-container {
    flex-direction: column;
  }

  .main-content {
    margin-left: 0 !important;
    margin-top: var(--sidebar-mobile-height);
    padding-bottom: 80px;
    height: calc(100vh - var(--sidebar-mobile-height));
    transition: margin-top 0.3s ease; /* Transition for top margin on mobile */
  }
}

@media (min-width: 769px) and (max-width: 1023px) {
  .main-content {
    padding: 1.5rem;
  }

  .error-state {
    max-width: 600px;
  }
}

@media (min-width: 1024px) {
  .main-content {
    padding: 2rem 2.5rem;
  }
}
</style>
