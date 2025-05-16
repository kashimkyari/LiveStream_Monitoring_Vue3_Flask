<template>
  <section class="agent-streams" :class="{ 'dark-theme': isDarkTheme }">
    <div class="dashboard-header">
      <h2>Agent Streams</h2>
    </div>

    <!-- Stats section -->
    <div class="stats-section">
      <StatCard 
        v-for="stat in stats"
        :key="stat.label"
        :value="stat.value"
        :label="stat.label"
        :icon="stat.icon"
      />
    </div>

    <!-- Search and Controls -->
    <div class="controls-section">
      <div class="search-box">
        <font-awesome-icon icon="search" class="search-icon" />
        <input v-model="searchQuery" placeholder="Search assigned streams..." class="search-input" />
      </div>
      <div class="view-controls" style="display: flex; gap: 1rem;">
        <button 
          class="view-toggle-btn" 
          :class="{ 'active': viewMode === 'grid' }" 
          @click="setViewMode('grid')"
          title="Grid View"
        >
          <font-awesome-icon icon="th" />
        </button>
        <button 
          class="view-toggle-btn" 
          :class="{ 'active': viewMode === 'list' }" 
          @click="setViewMode('list')"
          title="List View"
        >
          <font-awesome-icon icon="list" />
        </button>
        <button @click="refreshStreams" class="view-toggle-btn refresh-btn">
          <font-awesome-icon icon="sync-alt" />
          Refresh All
        </button>
      </div>
    </div>

    <!-- Stream sections -->
    <div class="streams-section">
      <!-- Live Streams -->
      <div class="section-header" @click="toggleLiveCollapse">
        <h3>Live Streams ({{ liveStreams.length }})</h3>
        <font-awesome-icon :icon="isLiveCollapsed ? 'chevron-down' : 'chevron-up'" />
      </div>
      <div v-show="!isLiveCollapsed" :class="['stream-container', viewMode]">
        <StreamCard 
          v-for="(stream, index) in filteredLiveStreams" 
          :key="stream.id || 'live-' + index"
          :stream="enhanceStreamWithUsername(stream)" 
          :index="index"
          :isLive="true"
          :detectionCount="getDetectionCount(stream)"
          :totalStreams="liveStreams.length"
          @click="openStreamDetails(stream)"
          @detection-toggled="handleDetectionToggled"
          @status-change="handleStreamStatusChange"
        />
      </div>
      
      <!-- Offline Streams -->
      <div class="section-header offline-section" @click="toggleOfflineCollapse">
        <h3>Offline Streams ({{ offlineStreams.length }})</h3>
        <font-awesome-icon :icon="isOfflineCollapsed ? 'chevron-down' : 'chevron-up'" />
      </div>
      <div v-show="!isOfflineCollapsed" :class="['stream-container', viewMode]">
        <StreamCard 
          v-for="(stream, index) in filteredOfflineStreams" 
          :key="stream.id || 'offline-' + index"
          :stream="enhanceStreamWithUsername(stream)" 
          :index="index"
          :isLive="false"
          :detectionCount="getDetectionCount(stream)"
          :totalStreams="offlineStreams.length"
          @click="openStreamDetails(stream)"
          @detection-toggled="handleDetectionToggled"
          @status-change="handleStreamStatusChange"
        />
      </div>
      
      <!-- Empty State -->
      <div class="empty-state" v-if="localStreams.length === 0 && !localIsLoading">
        <font-awesome-icon icon="video-slash" class="empty-icon" />
        <div class="empty-title">No streams assigned</div>
        <div class="empty-description">Streams assigned to you will appear here</div>
      </div>
    </div>

    <!-- Loading State -->
    <div class="loading-overlay" v-if="localIsLoading">
      <div class="loader-container">
        <div class="loader-circle"></div>
        <div class="loader-text">Loading streams...</div>
      </div>
    </div>
    
    <!-- Error Message -->
    <div class="error-message" v-if="localError && !localIsLoading">
      <font-awesome-icon icon="exclamation-triangle" class="error-icon" />
      <div class="error-text">{{ localError }}</div>
      <button class="retry-button" @click="fetchAssignedStreams">
        <font-awesome-icon icon="sync" />
        <span>Retry</span>
      </button>
    </div>

    <!-- Stream Details Modal -->
    <StreamDetailsModal
      v-if="showModal && selectedStream"
      :stream="enhanceStreamWithUsername(selectedStream)"
      :detections="selectedStreamDetections"
      :isRefreshing="isRefreshingStream"
      @close="closeModal"
      @refresh="handleStreamRefresh"
    />
  </section>
</template>

<script>
import { ref, computed, onMounted, inject } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import StreamCard from './StreamCard.vue'
import StreamDetailsModal from './StreamDetailsModal.vue'
import StatCard from './StatCard.vue'
import axios from 'axios'
import {
  faSync,
  faVideoSlash,
  faExclamationTriangle,
  faTh,
  faList,
  faSearch,
  faSyncAlt,
  faChevronUp,
  faChevronDown
} from '@fortawesome/free-solid-svg-icons'

library.add(faSync, faVideoSlash, faExclamationTriangle, faTh, faList, faSearch, faSyncAlt, faChevronUp, faChevronDown)

export default {
  name: 'AgentStreamsComponent',
  components: {
    FontAwesomeIcon,
    StreamCard,
    StreamDetailsModal,
    StatCard
  },
  props: {
    agentId: {
      type: [Number, String],
      default: null
    },
    streams: {
      type: Array,
      default: () => []
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    },
    detections: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['refresh-streams', 'update-streams'],
  setup(props, { emit }) {
    const appTheme = inject('theme', ref(true))
    const isDarkTheme = computed(() => appTheme.value === true)
    
    // Core state
    const showModal = ref(false)
    const selectedStream = ref(null)
    const selectedStreamDetections = ref([])
    const isRefreshingStream = ref(false)
    const viewMode = ref(window.innerWidth <= 768 ? 'list' : 'grid')
    const localStreams = ref([])
    const localIsLoading = ref(false)
    const localError = ref(null)
    const currentAgentId = ref(null)
    const agentData = ref(null)
    const agents = ref([])
    const searchQuery = ref('')
    const isLiveCollapsed = ref(false)
    const isOfflineCollapsed = ref(true)
    const notifications = ref([])

    // Computed properties
    const liveStreams = computed(() => {
      return localStreams.value.filter(stream => isStreamLive(stream))
    })
    
    const offlineStreams = computed(() => {
      return localStreams.value.filter(stream => !isStreamLive(stream))
    })

    const filteredLiveStreams = computed(() => 
      liveStreams.value.filter(s => 
        s.streamer_username.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    )

    const filteredOfflineStreams = computed(() => 
      offlineStreams.value.filter(s => 
        s.streamer_username.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    )

    const stats = computed(() => [{
      value: liveStreams.value.length,
      label: 'Assigned Live Streams',
      icon: 'broadcast-tower'
    }, {
      value: offlineStreams.value.length,
      label: 'Assigned Offline Streams',
      icon: 'video-slash'
    }, {
      value: notifications.value.filter(n => 
        ['object_detection', 'audio_detection', 'chat_detection'].includes(n.event_type) &&
        localStreams.value.some(s => s.room_url === n.room_url)
      ).length,
      label: 'Detections in Assigned Streams',
      icon: 'exclamation-triangle'
    }])

    // Core functions
    const fetchCurrentAgent = async () => {
      try {
        const response = await axios.get('/api/session')
        if (response.data?.isLoggedIn) {
          currentAgentId.value = response.data.user.id
          agentData.value = response.data.user
          return response.data.user
        }
        return null
      } catch (error) {
        console.error('Error fetching current agent:', error)
        return null
      }
    }

    const fetchAgents = async () => {
      try {
        const response = await axios.get('/api/agents')
        agents.value = response.data || []
      } catch (error) {
        console.error('Error fetching agents:', error)
      }
    }
    
    const fetchAssignedStreams = async () => {
      if (localIsLoading.value) return
      
      localIsLoading.value = true
      localError.value = null
      
      try {
        if (!currentAgentId.value) {
          const agent = await fetchCurrentAgent()
          if (!agent) {
            localError.value = 'Unable to authenticate. Please log in again.'
            return
          }
        }

        if (agents.value.length === 0) {
          await fetchAgents()
        }
        
        const response = await axios.get('/api/streams')
        localStreams.value = (response.data || []).filter(stream => 
          stream.assignments?.some(assignment => 
            assignment.agent_id === currentAgentId.value && assignment.status === 'active'
          )
        )
      } catch (error) {
        console.error('Error fetching streams:', error)
        localError.value = 'Failed to load streams. Please try again.'
      } finally {
        localIsLoading.value = false
      }
    }

    const fetchNotifications = async () => {
      try {
        const { data } = await axios.get('/api/notifications')
        notifications.value = data
      } catch (error) {
        console.error('Error fetching notifications:', error)
      }
    }

    const enhanceStreamWithUsername = (stream) => {
      if (!stream) return stream
      const enhanced = JSON.parse(JSON.stringify(stream))
      
      if (enhanced.assignments?.length) {
        enhanced.assignments = enhanced.assignments.map(assignment => {
          const username = assignment.agent?.username || 
            agents.value.find(a => a.id === assignment.agent_id)?.username ||
            (assignment.agent_id === currentAgentId.value ? agentData.value?.username : null) ||
            `Agent ${assignment.agent_id}`
            
          return { ...assignment, agent_username: username }
        })
        enhanced.agent = {
          username: enhanced.assignments.find(a => a.agent_id === currentAgentId.value)?.agent_username || 'Unassigned',
          status: enhanced.assignments.find(a => a.agent_id === currentAgentId.value)?.status || 'inactive'
        }
      } else {
        enhanced.agent = { username: 'Unassigned', status: 'inactive' }
      }
      
      return enhanced
    }
    
    const isStreamLive = (stream) => {
      if (!stream) return false
      const platform = stream.platform?.toLowerCase()
      return platform === 'chaturbate' ? !!stream.chaturbate_m3u8_url :
             platform === 'stripchat' ? !!stream.stripchat_m3u8_url :
             false
    }
    
    const setViewMode = (mode) => {
      if (viewMode.value === mode) return
      viewMode.value = mode
      localStorage.setItem('streamViewMode', mode)
    }
    
    const openStreamDetails = (stream) => {
      selectedStream.value = stream
      selectedStreamDetections.value = props.detections[stream.room_url] || []
      showModal.value = true
    }
    
    const closeModal = () => {
      showModal.value = false
      selectedStream.value = null
    }
    
    const handleStreamRefresh = async (streamId) => {
      isRefreshingStream.value = true
      try {
        const response = await axios.put(`/api/streams/${streamId}`, { refresh: true })
        if (response.data?.stream) {
          const streamIndex = localStreams.value.findIndex(s => s.id === streamId)
          if (streamIndex >= 0) {
            localStreams.value[streamIndex] = response.data.stream
            if (selectedStream.value?.id === streamId) {
              selectedStream.value = response.data.stream
            }
            emit('update-streams', localStreams.value)
          }
        }
      } catch (error) {
        console.error('Error refreshing stream:', error)
        localError.value = 'Failed to refresh stream. Please try again.'
      } finally {
        isRefreshingStream.value = false
      }
    }

    const refreshStreams = () => {
      emit('refresh-streams', { all: true })
      fetchAssignedStreams()
    }

    const toggleLiveCollapse = () => {
      isLiveCollapsed.value = !isLiveCollapsed.value
    }

    const toggleOfflineCollapse = () => {
      isOfflineCollapsed.value = !isOfflineCollapsed.value
    }

    const handleDetectionToggled = ({ streamId, active }) => {
      const updatedStreams = localStreams.value.map(s => 
        s.id === streamId ? { ...s, isDetecting: active } : s
      )
      localStreams.value = updatedStreams
      emit('update-streams', updatedStreams)
      console.log(`Detection ${active ? 'started' : 'stopped'} for stream ID ${streamId}`)
    }

    const handleStreamStatusChange = ({ streamId, newStatus }) => {
      const updatedStreams = localStreams.value.map(s => 
        s.id === streamId ? { ...s, status: newStatus } : s
      )
      localStreams.value = updatedStreams
      emit('update-streams', updatedStreams)
    }

    const getDetectionCount = (stream) => 
      props.detections[stream.room_url]?.length || 0

    onMounted(async () => {
      const savedViewMode = localStorage.getItem('streamViewMode')
      if (savedViewMode && ['grid', 'list'].includes(savedViewMode)) {
        viewMode.value = savedViewMode
      }
      
      await fetchAssignedStreams()
      await fetchNotifications()
    })

    return {
      isDarkTheme,
      viewMode,
      showModal,
      selectedStream,
      selectedStreamDetections,
      isRefreshingStream,
      liveStreams,
      offlineStreams,
      filteredLiveStreams,
      filteredOfflineStreams,
      localStreams,
      localIsLoading,
      localError,
      stats,
      searchQuery,
      isLiveCollapsed,
      isOfflineCollapsed,
      fetchAssignedStreams,
      setViewMode,
      openStreamDetails,
      closeModal,
      handleStreamRefresh,
      enhanceStreamWithUsername,
      handleDetectionToggled,
      handleStreamStatusChange,
      getDetectionCount,
      refreshStreams,
      toggleLiveCollapse,
      toggleOfflineCollapse
    }
  }
}
</script>

<style scoped>
.agent-streams {
  width: auto;
  padding: 20px;
  background-color: var(--bg-color, #f8f9fa);
  color: var(--text-color, #212529);
  border-radius: 8px;
}

.dark-theme {
  --bg-color: #18181B;
  --text-color: #EFEFF1;
  --border-color: #3a3a3d;
  --accent-color: #9147FF;
  --active-color: #1F9D55;
  --hover-color: #2c2c35;
}

.dashboard-header h2 {
  margin: 0 0 2rem;
  font-size: 2rem;
  font-weight: 600;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.controls-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.6;
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 35px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--input-bg, #fff);
  color: var(--text-color);
}

.view-toggle-btn, .refresh-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: var(--primary-color, #9147FF);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.view-toggle-btn.active {
  background-color: var(--accent-color, #9147FF);
}

.view-toggle-btn:hover:not(.active) {
  background-color: var(--hover-color, rgba(0, 0, 0, 0.1));
}

.section-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0 1rem;
  cursor: pointer;
}

.section-header h3 {
  margin: 0;
  font-size: 1.25rem;
}

.stream-container {
  display: grid;
  gap: 1rem;
}

.stream-container.grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.stream-container.list {
  grid-template-columns: 1fr;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  background-color: var(--hover-color, rgba(0, 0, 0, 0.02));
  border-radius: 8px;
  margin: 30px 0;
}

.empty-icon {
  font-size: 2.5rem;
  color: var(--border-color, #dee2e6);
  margin-bottom: 15px;
}

.empty-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 10px;
}

.empty-description {
  color: var(--text-color, rgba(33, 37, 41, 0.7));
  margin-bottom: 20px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: var(--bg-color, white);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.19);
}

.loader-circle {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top-color: var(--accent-color, #9147FF);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

.loader-text {
  font-size: 1rem;
  font-weight: 500;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  margin: 20px 0;
  background-color: rgba(220, 53, 69, 0.1);
  border-left: 4px solid #dc3545;
  border-radius: 6px;
}

.error-icon {
  color: #dc3545;
  font-size: 1.2rem;
}

.error-text {
  flex: 1;
}

.retry-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  background-color: var(--accent-color, #9147FF);
  color: white;
  cursor: pointer;
}

.retry-button:hover {
  background-color: var(--accent-color, #7e32e6);
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .agent-streams {
    padding: 15px 10px;
  }
  
  .controls-section {
    flex-direction: column;
  }
  
  .search-box {
    max-width: 100%;
  }
  
  .view-controls {
    width: 100%;
    display: flex;
    gap: 0.5rem;
  }
  
  .view-toggle-btn, .refresh-btn {
    flex: 1;
    justify-content: center;
  }
  
  .stream-container.grid {
    grid-template-columns: 1fr;
  }
}
</style>