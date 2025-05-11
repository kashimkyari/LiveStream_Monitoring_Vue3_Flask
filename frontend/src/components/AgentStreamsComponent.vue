<template>
  <div class="agent-streams" :class="{ 'dark-theme': isDarkTheme }">
    <div class="stream-dashboard-header">
      <div class="stream-status-summary">
        <div class="status-pill" :class="{ 'active': liveStreams.length > 0 }">
          <span class="status-indicator"></span>
          <span>{{ liveStreams.length }} Live</span>
        </div>
        <div class="status-pill" :class="{ 'active': offlineStreams.length > 0 }">
          <span class="status-indicator offline"></span>
          <span>{{ offlineStreams.length }} Offline</span>
        </div>
      </div>
      <div class="header-actions">
        <div class="view-toggle-container">
          <button 
            class="view-mode-btn" 
            :class="{ 'active': viewMode === 'grid' }" 
            @click="setViewMode('grid')"
            title="Grid View"
          >
            <font-awesome-icon :icon="['fas', 'th']" />
          </button>
          <button 
            class="view-mode-btn" 
            :class="{ 'active': viewMode === 'list' }" 
            @click="setViewMode('list')"
            title="List View"
          >
            <font-awesome-icon :icon="['fas', 'list']" />
          </button>
        </div>
      </div>
    </div>

    <div class="streams-content" :class="{'list-view': viewMode === 'list'}">
      <!-- Live Streams Section -->
      <div class="stream-section live-streams" v-if="liveStreams.length > 0">
        <div 
          class="streams-grid" 
          :class="{
            'list-layout': viewMode === 'list', 
            'small': liveStreams.length > 6 && viewMode === 'grid', 
            'medium': liveStreams.length > 3 && liveStreams.length <= 6 && viewMode === 'grid'
          }"
        >
          <div 
            v-for="(stream, index) in liveStreams" 
            :key="stream.id || 'live-' + index"
            class="stream-card-wrapper"
            @click="openStreamDetails(stream)"
            :class="{ 'list-item': viewMode === 'list' }"
          >
            <StreamCard 
              :stream="enhanceStreamWithUsername(stream)" 
              :index="index"
              :isLive="true"
              :detectionCount="getDetectionCount(stream)"
              :playVideo="playVideo"
              :totalStreams="totalStreams"
              class="stream-card"
              @detection-toggled="handleDetectionToggled"
            ></StreamCard>
          </div>
        </div>
      </div>
      
      <!-- Offline Streams Section -->
      <div class="stream-section offline-streams" v-if="offlineStreams.length > 0">
        <div 
          class="streams-grid" 
          :class="{
            'list-layout': viewMode === 'list', 
            'small': offlineStreams.length > 6 && viewMode === 'grid', 
            'medium': offlineStreams.length > 3 && offlineStreams.length <= 6 && viewMode === 'grid'
          }"
        >
          <div 
            v-for="(stream, index) in offlineStreams" 
            :key="stream.id || 'offline-' + index"
            class="stream-card-wrapper"
            @click="openStreamDetails(stream)"
            :class="{ 'list-item': viewMode === 'list' }"
          >
            <StreamCard 
              :stream="enhanceStreamWithUsername(stream)" 
              :index="index"
              :isLive="false"
              :detectionCount="getDetectionCount(stream)"
              :playVideo="playVideo"
              :totalStreams="totalStreams"
              class="stream-card"
              @detection-toggled="handleDetectionToggled"
            ></StreamCard>
          </div>
        </div>
      </div>
      
      <!-- Empty State -->
      <div class="empty-state" v-if="streams.length === 0 && !isLoading">
        <font-awesome-icon :icon="['fas', 'video-slash']" class="empty-icon" />
        <div class="empty-title">No streams assigned</div>
        <div class="empty-description">Streams assigned to you will appear here</div>
      </div>
    </div>
    
    <!-- Loading State -->
    <div class="loading-overlay" v-if="isLoading">
      <div class="loader-container">
        <div class="loader-circle"></div>
        <div class="loader-text">Loading streams...</div>
      </div>
    </div>
    
    <!-- Error Message -->
    <div class="error-message" v-if="error && !isLoading">
      <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="error-icon" />
      <div class="error-text">{{ error }}</div>
      <button class="retry-button" @click="fetchAssignedStreams">
        <font-awesome-icon :icon="['fas', 'sync']" />
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
  </div>
</template>

<script>
import { ref, computed, onMounted, inject } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import StreamCard from './StreamCard.vue'
import StreamDetailsModal from './StreamDetailsModal.vue'
import axios from 'axios'
import {
  faSync,
  faVideoSlash,
  faExclamationTriangle,
  faTh,
  faList
} from '@fortawesome/free-solid-svg-icons'

library.add(faSync, faVideoSlash, faExclamationTriangle, faTh, faList)

export default {
  name: 'AgentStreamsComponent',
  components: {
    FontAwesomeIcon,
    StreamCard,
    StreamDetailsModal
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
    }
  },
  emits: ['refresh-streams', 'update-stream'],
  setup() {
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

    // Computed properties
    const liveStreams = computed(() => {
      return localStreams.value.filter(stream => isStreamLive(stream))
    })
    
    const offlineStreams = computed(() => {
      return localStreams.value.filter(stream => !isStreamLive(stream))
    })

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
            assignment.agent_id === currentAgentId.value
          )
        )
      } catch (error) {
        console.error('Error fetching streams:', error)
        localError.value = 'Failed to load streams. Please try again.'
      } finally {
        localIsLoading.value = false
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
      selectedStreamDetections.value = []
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
          }
        }
      } catch (error) {
        console.error('Error refreshing stream:', error)
      } finally {
        isRefreshingStream.value = false
      }
    }

    const handleDetectionToggled = (data) => {
      console.log(`Detection ${data.active ? 'started' : 'stopped'} for ${data.stream.streamer_username}`)
    }

    onMounted(async () => {
      const savedViewMode = localStorage.getItem('streamViewMode')
      if (savedViewMode && ['grid', 'list'].includes(savedViewMode)) {
        viewMode.value = savedViewMode
      }
      
      await fetchAssignedStreams()
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
      fetchAssignedStreams,
      setViewMode,
      openStreamDetails,
      closeModal,
      handleStreamRefresh,
      enhanceStreamWithUsername,
      handleDetectionToggled,
      
    }
  }
}
</script>

<style scoped>
.agent-streams {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 300px;
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

.stream-dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-color, #dee2e6);
}

.stream-status-summary {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  background-color: rgba(0, 0, 0, 0.05);
  font-size: 0.9rem;
  font-weight: 500;
}

.dark-theme .status-pill {
  background-color: rgba(255, 255, 255, 0.07);
}

.status-pill.active {
  background-color: rgba(31, 157, 85, 0.15);
}

.dark-theme .status-pill.active {
  background-color: rgba(31, 157, 85, 0.25);
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #1F9D55;
}

.status-indicator.offline {
  background-color: #718096;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.view-toggle-container {
  display: flex;
  background-color: var(--hover-color, rgba(0, 0, 0, 0.05));
  border-radius: 6px;
  padding: 2px;
  overflow: hidden;
}

.view-mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  color: var(--text-color, rgba(33, 37, 41, 0.7));
  cursor: pointer;
  border-radius: 4px;
}

.view-mode-btn.active {
  background-color: var(--accent-color, #9147FF);
  color: white;
}

.view-mode-btn:hover:not(.active) {
  background-color: var(--hover-color, rgba(0, 0, 0, 0.1));
}

.streams-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.stream-section {
  width: 100%;
}

.streams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.streams-grid.medium {
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
}

.streams-grid.small {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

.list-layout {
  grid-template-columns: 1fr;
  gap: 10px;
}

.stream-card-wrapper {
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.stream-card-wrapper:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.18);
}

.stream-card-wrapper.list-item {
  height: 100px;
}

.stream-card-wrapper:not(.list-item) {
  height: 240px;
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
  
  .stream-dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .streams-grid {
    grid-template-columns: 1fr;
  }
}
</style>