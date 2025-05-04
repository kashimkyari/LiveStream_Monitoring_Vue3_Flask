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
    <SettingsModals 
      :darkMode="isDarkTheme"
      @notification="handleNotification" 
      @update:keywords="fetchKeywords"
      @update:objects="fetchObjects"
      @update:telegramRecipients="fetchTelegramRecipients"
      @modal-closed="handleModalClosed"
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
import SettingsModals from './SettingsModals.vue'
import AdminNotificationsPage from './AdminNotificationsPage.vue'
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
    SettingsModals,
    FontAwesomeIcon,
    AdminNotificationsPage
  },
  methods: {
    async loadStreams() {
      try {
        const response = await axios.get('/api/streams');
        this.streams = response.data;
      } catch (error) {
        console.error('Error loading streams:', error);
      }
    },
    
    handleStreamCreated() {
      // Reload streams to get fresh data
      this.loadStreams();
    },
    
    handleStreamUpdated(updatedStream) {
      if (!this.streams) return; // Guard against null streams
      
      // Find and update the stream in our list
      const index = this.streams.findIndex(s => s.id === updatedStream.id);
      if (index !== -1) {
        // Create a new array to trigger reactivity
        const newStreams = [...this.streams];
        newStreams[index] = updatedStream;
        this.streams = newStreams;
      }
    },
    
    handleStreamDeleted(streamId) {
      if (!this.streams) return; // Guard against null streams
      
      // Remove the deleted stream from our list
      this.streams = this.streams.filter(s => s.id !== streamId);
    },

    // Handle notification from settings modal
    handleNotification(notification) {
      // Implementation for handling notifications
      console.log('Notification received:', notification);
    },

    // Handle modal closed event
    handleModalClosed() {
      // Implementation for when a modal is closed
      console.log('Modal closed');
    },

    // Placeholder methods for API fetches
    fetchKeywords() {
      console.log('Fetching keywords');
      // Implementation
    },

    fetchObjects() {
      console.log('Fetching objects');
      // Implementation
    },

    fetchTelegramRecipients() {
      console.log('Fetching telegram recipients');
      // Implementation
    }
    
    // Add the missing enhanceStreamWithUsername function
    
  },
  setup() {
    const router = useRouter()
    const toast = useToast()
    const mainContent = ref(null)
    const animeInstances = ref([]);  // Track animation instances
    
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

    // Add the enhanceStreamWithUsername function in setup
    const enhanceStreamWithUsername = (stream) => {
      if (!stream || !agents.value) return stream;
      
      // Find the agent assigned to this stream
      const assignedAgent = agents.value.find(agent => agent.id === stream.assigned_agent_id);
      
      // Return enhanced stream with username info
      return {
        ...stream,
        agent_username: assignedAgent ? assignedAgent.username : 'Unassigned',
        agent_status: assignedAgent ? assignedAgent.status : 'inactive'
      };
    };

    // Computed property for enhanced streams
    const enhancedStreams = computed(() => {
      if (!streams.value) return [];
      return streams.value.map(stream => enhanceStreamWithUsername(stream));
    });

    // Safely animate elements
    const safeAnimate = (targets, animation) => {
      if (!targets) return null;
      
      try {
        const instance = anime({
          targets,
          ...animation
        });
        
        // Store animation instance for cleanup
        animeInstances.value.push(instance);
        return instance;
      } catch (error) {
        console.error('Animation error:', error);
        return null;
      }
    }

    // Enhanced sidebar toggle handler with animations
    const handleSidebarToggle = (isMinimized) => {
      // First call the original handler from the composable
      originalHandleSidebarToggle(isMinimized)
      
      // Wait for the DOM to update before animating
      nextTick(() => {
        // Make sure mainContent ref exists
        if (mainContent.value) {
          // Animate the main content margin
          safeAnimate(mainContent.value, {
            marginLeft: isMinimized 
              ? (window.innerWidth <= 768 ? '0' : 'var(--sidebar-width-collapsed)')
              : (window.innerWidth <= 768 ? '0' : 'var(--sidebar-width-expanded)'),
            duration: 300,
            easing: 'easeOutQuad'
          });

          // Find the content div with proper null check
          const contentDiv = mainContent.value.querySelector(':scope > div');
          if (contentDiv) {
            safeAnimate(contentDiv, {
              opacity: [0.9, 1],
              translateX: [isMinimized ? '-10px' : '10px', '0'],
              duration: 350,
              easing: 'spring(1, 80, 12, 0)'
            });
          }
        }
      })
    }

    // Watch for tab changes to ensure proper rendering
    watch(activeTab, (newTab, oldTab) => {
      if (newTab !== oldTab) {
        // Allow the DOM to update before any animations
        nextTick(() => {
          // Any animations or DOM operations after tab change can go here
        });
      }
    });

    // Clean up function to prevent unmount errors
    const cleanupAnimations = () => {
      // Stop all animations
      animeInstances.value.forEach(instance => {
        if (instance && typeof instance.pause === 'function') {
          instance.pause();
        }
      });
      animeInstances.value = [];
    };

    // Lifecycle hooks
    onMounted(() => {
      // Set up online/offline event listeners
      const onlineHandler = () => { isOnline.value = true };
      const offlineHandler = () => { isOnline.value = false };
      
      window.addEventListener('online', onlineHandler);
      window.addEventListener('offline', offlineHandler);
      
      // Fetch initial data safely
      try {
        fetchDashboardData()
          .then(() => {
            // Only animate after data is loaded and if component is still mounted
            nextTick(() => {
              if (mainContent.value) {
                safeAnimate(mainContent.value, {
                  opacity: [0, 1],
                  translateY: ['20px', '0'],
                  duration: 600,
                  easing: 'spring(1, 80, 10, 0)'
                });
              }
            });
          })
          .catch(error => console.error('Error fetching dashboard data:', error));
        
        fetchMessages()
          .catch(error => console.error('Error fetching messages:', error));
      } catch (e) {
        console.error('Error in onMounted:', e);
      }

      // Clean up event listeners on component unmount
      onBeforeUnmount(() => {
        window.removeEventListener('online', onlineHandler);
        window.removeEventListener('offline', offlineHandler);
        cleanupAnimations();
      });
    })

    // Add computed properties for filtering streams
    const onlineStreams = computed(() => {
      return allStreams.value.filter(stream => stream.status === 'online');
    });

    const offlineStreams = computed(() => {
      return allStreams.value.filter(stream => stream.status === 'offline');
    });

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
      enhancedStreams, // Add the computed property
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
      handleSidebarToggle,
      enhanceStreamWithUsername, // Export the function so it's available in templates

      // Computed properties
      onlineStreams,
      offlineStreams
    }
  }
}
</script>

<style>
/* Define CSS variables to control sidebar width and mobile height */
/* Add this to your <style> section */
:root {
  /* Existing variables */
  --sidebar-width-expanded: 0px;
  --sidebar-width-collapsed: 50px;
  --sidebar-mobile-height: 65px;
  
  /* New variables for stream sizing */
  --stream-base-width: 480px;
  --stream-base-height: 360px;
  --stream-min-width: 240px;
  --stream-min-height: 180px;
  
  /* Color variables with RGB format for opacity control */
  --primary-rgb: 59, 130, 246; /* blue-500 */
  --secondary-rgb: 156, 163, 175; /* gray-400 */
  --success-rgb: 16, 185, 129; /* green-500 */
  --danger-rgb: 239, 68, 68; /* red-500 */
  --warning-rgb: 245, 158, 11; /* yellow-500 */
  --info-rgb: 14, 165, 233; /* sky-500 */
}

[data-theme="dark"] {
  /* Existing dark theme variables */
  
  /* RGB variables for dark theme */
  --primary-rgb: 96, 165, 250; /* blue-400 */
  --secondary-rgb: 156, 163, 175; /* gray-400 */
  --success-rgb: 34, 197, 94; /* green-400 */
  --danger-rgb: 248, 113, 113; /* red-400 */
  --warning-rgb: 251, 191, 36; /* yellow-400 */
  --info-rgb: 56, 189, 248; /* sky-400 */
}

.admin-container {
  top: 5;
  min-height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow-x: hidden; /* Prevent horizontal scrollbar during animations */
}



.main-content {
  /* Default state is expanded */
  flex: 1;
  padding: 1rem;
  transition: margin-left 0.3s ease;
  height: 90%;
  will-change: margin-left, transform;
  margin-left: 55px;
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
    height: calc(100vh - var(--sidebar-mobile-height));
    transition: margin-top 0.3s ease; /* Transition for top margin on mobile */
  }
}

@media (min-width: 769px) and (max-width: 1023px) {
  .main-content {
    
  }

  .error-state {
    max-width: 600px;
  }
}

@media (min-width: 1024px) {
  .main-content {
    
  }
}


</style>
