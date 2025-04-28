<template>
  <div class="agent-streams" :class="{ 'dark-theme': isDarkTheme }">
    <!-- Simple header with stream count -->
    <div class="stream-dashboard-header" ref="streamHeader">
      <div class="stream-status-summary">
        <div class="status-pill" 
             :class="{ 'active': liveStreams.length > 0 }"
             ref="livePill">
          <span class="status-indicator"></span>
          <span>{{ liveStreams.length }} Live</span>
        </div>
        <div class="status-pill" 
             :class="{ 'active': offlineStreams.length > 0 }"
             ref="offlinePill">
          <span class="status-indicator offline"></span>
          <span>{{ offlineStreams.length }} Offline</span>
        </div>
      </div>
      <div class="header-actions" ref="headerActions">
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

    <!-- Stream sections container -->
    <div class="streams-content" ref="streamsContent" :class="{'list-view': viewMode === 'list'}">
      <!-- Active Streams Section -->
      <div 
        class="stream-section live-streams" 
        v-if="liveStreams.length > 0"
        ref="liveStreamSection"
      >
       
        
        <div 
          class="streams-grid" 
          ref="liveStreamsGrid"
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
            :data-index="index"
            :class="{ 'list-item': viewMode === 'list' }"
            ref="liveStreamCards"
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
      <div 
        class="stream-section offline-streams" 
        v-if="offlineStreams.length > 0"
        ref="offlineStreamSection"
      >
        <div class="section-header">
          <div class="status-indicator offline">
            <span class="status-dot"></span>
            <h3>Offline Streams</h3>
          </div>
        </div>
        
        <div 
          class="streams-grid" 
          ref="offlineStreamsGrid"
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
            :data-index="index"
            :class="{ 'list-item': viewMode === 'list' }"
            ref="offlineStreamCards"
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
      
      <!-- Empty State with animation -->
      <div 
        class="empty-state" 
        v-if="streams.length === 0 && !isLoading" 
        ref="emptyState"
      >
        <font-awesome-icon :icon="['fas', 'video-slash']" class="empty-icon" />
        <div class="empty-title">No streams assigned</div>
        <div class="empty-description">Streams assigned to you will appear here</div>
      </div>
    </div>
    
    <!-- Loading overlay with animated spinner -->
    <transition name="fade">
      <div class="loading-overlay" v-if="isLoading">
        <div class="loader-container" ref="loaderContainer">
          <div class="loader-circle"></div>
          <div class="loader-text">Checking stream status...</div>
        </div>
      </div>
    </transition>
    
    <!-- Error message with animated entrance -->
    <transition name="slide-up">
      <div class="error-message" v-if="error && !isLoading" ref="errorMessage">
        <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="error-icon" />
        <div class="error-text">{{ error }}</div>
        <button class="retry-button" @click="fetchAssignedStreams">
          <font-awesome-icon :icon="['fas', 'sync']" />
          <span>Retry</span>
        </button>
      </div>
    </transition>

    <!-- Stream Details Modal with enhanced animations -->
    <transition name="modal">
      <StreamDetailsModal
        v-if="showModal && selectedStream"
        :stream="enhanceStreamWithUsername(selectedStream)"
        :detections="selectedStreamDetections"
        :isRefreshing="isRefreshingStream"
        @close="closeModal"
        @refresh="handleStreamRefresh"
      />
    </transition>
  </div>
</template>

<script>
  /* eslint-disable */ 
import { ref, computed, onMounted, nextTick, onBeforeUnmount, inject, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import StreamCard from './StreamCard.vue'
import StreamDetailsModal from './StreamDetailsModal.vue'
import anime from 'animejs/lib/anime.es.js'
import axios from 'axios'
import {
  faSync,
  faVideoSlash,
  faPlayCircle,
  faExclamationCircle,
  faExclamationTriangle,
  faEye,
  faThLarge,
  faTh,
  faList,
  faChevronRight,
  faClock,
  faBell
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faSync, 
  faVideoSlash, 
  faPlayCircle, 
  faExclamationCircle,
  faExclamationTriangle,
  faEye, 
  faThLarge, 
  faTh, 
  faList, 
  faChevronRight, 
  faClock, 
  faBell
)

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
    },
    lastRefreshed: {
      type: Date,
      default: () => new Date()
    }
  },
  emits: ['refresh-streams', 'update-stream'],
  setup(props, { emit }) {
    // Inject app theme from parent
    const appTheme = inject('theme', ref(true))
    
    // Create computed property for isDarkTheme
    const isDarkTheme = computed(() => appTheme.value === true)
    
    // Reactive state
    const showModal = ref(false)
    const selectedStream = ref(null)
    const selectedStreamDetections = ref([])
    const isRefreshingStream = ref(false)
    const isMobile = ref(window.innerWidth <= 768)
    const viewMode = ref(isMobile.value ? 'list' : 'grid')
    
    // API related states
    const localStreams = ref([])
    const localIsLoading = ref(false)
    const localError = ref(null)
    const localLastRefreshed = ref(new Date())
    const currentAgentId = ref(null)
    const agentData = ref(null)
    const agents = ref([])
    
    // Animation refs
    const streamHeader = ref(null)
    const streamsContent = ref(null)
    const liveStreamSection = ref(null)
    const offlineStreamSection = ref(null)
    const liveStreamsGrid = ref(null)
    const offlineStreamsGrid = ref(null)
    const emptyState = ref(null)
    const errorMessage = ref(null)
    const livePill = ref(null)
    const offlinePill = ref(null)
    const headerActions = ref(null)
    const viewToggleBtn = ref(null)
    const loaderContainer = ref(null)
    const liveStreamCards = ref([])
    const offlineStreamCards = ref([])

    const handleDetectionToggled = (data) => {
  console.log(`Detection ${data.active ? 'started' : 'stopped'} for ${data.stream.streamer_username}`)
  // You can add additional logic here, like showing a notification
}
    
    // Get current session and agent data
    const fetchCurrentAgent = async () => {
      try {
        const response = await axios.get('/api/session')
        if (response.data && response.data.isLoggedIn) {
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

    // Fetch all agents for username lookup
    const fetchAgents = async () => {
      try {
        const response = await axios.get('/api/agents')
        if (response.data) {
          agents.value = response.data
        }
      } catch (error) {
        console.error('Error fetching agents:', error)
      }
    }
    
    // API methods - Fetch streams with assignments
    const fetchAssignedStreams = async () => {
      if (localIsLoading.value) return
      
      localIsLoading.value = true
      localError.value = null
      
      try {
        // First, get the current agent's ID if not already set
        if (!currentAgentId.value) {
          const agent = await fetchCurrentAgent()
          if (!agent) {
            localError.value = 'Unable to authenticate. Please log in again.'
            localIsLoading.value = false
            return
          }
        }

        // Fetch agents for username mapping if not already loaded
        if (agents.value.length === 0) {
          await fetchAgents()
        }
        
        // Fetch all streams
        const response = await axios.get('/api/streams')
        const allStreams = response.data || []
        
        // Filter streams that are assigned to the current agent
        const agentId = currentAgentId.value
        const assignedStreams = allStreams.filter(stream => {
          // Check if this stream has assignments for the current agent
          return stream.assignments && stream.assignments.some(assignment => 
            assignment.agent_id === agentId
          )
        })
        
        localStreams.value = assignedStreams
        localLastRefreshed.value = new Date()
        localIsLoading.value = false
        
        // Animate elements after data is loaded
        nextTick(() => {
          animateStreamElements()
        })
      } catch (error) {
        console.error('Error fetching streams:', error)
        localError.value = 'Failed to load streams. Please try again.'
        localIsLoading.value = false
      }
    }

    // Helper function to enhance stream with agent username
    const enhanceStreamWithUsername = (stream) => {
      if (!stream) return stream
      
      // Create a deep copy to avoid modifying the original
      const enhancedStream = JSON.parse(JSON.stringify(stream))

      // Process assignments to add usernames
      if (enhancedStream.assignments && enhancedStream.assignments.length > 0) {
        enhancedStream.assignments = enhancedStream.assignments.map(assignment => {
          let agentUsername = null
          
          // First check if we already have the username in the agent object
          if (assignment.agent && assignment.agent.username) {
            agentUsername = assignment.agent.username
          } 
          // Then look up the agent in our agents list
          else if (agents.value.length > 0) {
            const agentObj = agents.value.find(a => a.id === assignment.agent_id)
            if (agentObj) {
              agentUsername = agentObj.username
            }
          }
          // If it's the current agent, use that username
          else if (assignment.agent_id === currentAgentId.value && agentData.value) {
            agentUsername = agentData.value.username
          }
          
          return {
            ...assignment,
            agent_username: agentUsername || `Agent ${assignment.agent_id}`
          }
        })
      }

      // Add agent reference to the stream for StreamCard to use
      if (enhancedStream.assignments && enhancedStream.assignments.length > 0) {
        // Find the assignment for the current agent
        const currentAgentAssignment = enhancedStream.assignments.find(
          a => a.agent_id === currentAgentId.value
        )
        
        if (currentAgentAssignment) {
          enhancedStream.agent = {
            id: currentAgentId.value,
            username: currentAgentAssignment.agent_username
          }
        }
      }
      
      return enhancedStream
    }
    
    // Helper to determine if a stream is live based on m3u8 URLs
    const isStreamLive = (stream) => {
      if (!stream) return false
      
      const platform = stream.platform?.toLowerCase()
      if (platform === 'chaturbate') {
        return !!stream.chaturbate_m3u8_url
      } else if (platform === 'stripchat') {
        return !!stream.stripchat_m3u8_url
      }
      
      return false
    }
    
    // Filtered streams
    const liveStreams = computed(() => {
      return localStreams.value.filter(stream => isStreamLive(stream))
    })
    
    const offlineStreams = computed(() => {
      return localStreams.value.filter(stream => !isStreamLive(stream))
    })
    
    // Get detection count (mock for now, would connect to real data)
    const getDetectionCount = (stream) => {
      // This would integrate with actual detection data
      return 0
    }
    
    // Set view mode with animation
    const setViewMode = (mode) => {
      if (viewMode.value === mode) return
      
      // Store the old mode for animation purposes
      const oldMode = viewMode.value
      viewMode.value = mode
      
      // Save preference in localStorage
      try {
        localStorage.setItem('streamViewMode', mode)
      } catch (e) {
        console.error('Could not save view mode preference')
      }
      
      // Animate the transition
      nextTick(() => {
        const cards = [...document.querySelectorAll('.stream-card-wrapper')]
        
        // Different animation depending on target mode
        if (mode === 'list') {
          // Grid to List animation
          anime.timeline({
            easing: 'easeOutQuad',
            duration: 400
          }).add({
            targets: cards,
            scale: [1, 0.95],
            opacity: [1, 0.7],
            duration: 200
          }).add({
            targets: cards,
            height: '100px',
            width: '100%',
            scale: 1,
            opacity: 1,
            delay: anime.stagger(30),
            duration: 300
          })
        } else {
          // List to Grid animation
          anime.timeline({
            easing: 'easeOutQuad',
            duration: 400
          }).add({
            targets: cards,
            scale: [1, 0.95],
            opacity: [1, 0.7],
            duration: 200
          }).add({
            targets: cards,
            height: '240px',
            width: '100%',
            scale: 1,
            opacity: 1,
            delay: anime.stagger(30),
            duration: 300
          })
        }
      })
    }
    
    // Open stream details modal
    const openStreamDetails = (stream) => {
      selectedStream.value = stream
      
      // Fetch detections for this stream
      // This would be replaced with actual API call to get detections
      selectedStreamDetections.value = []
      
      showModal.value = true
      
      // Animate the modal entrance
      nextTick(() => {
        anime({
          targets: '.modal-content',
          translateY: [50, 0],
          opacity: [0, 1],
          duration: 500,
          easing: 'easeOutQuad'
        })
      })
    }
    
    // Close modal with animation
    const closeModal = () => {
      anime({
        targets: '.modal-content',
        translateY: [0, 50],
        opacity: [1, 0],
        duration: 300,
        easing: 'easeInQuad',
        complete: () => {
          showModal.value = false
          selectedStream.value = null
        }
      })
    }
    
    // Handle stream refresh
    const handleStreamRefresh = async (streamId) => {
      isRefreshingStream.value = true
      
      try {
        // API call to refresh specific stream
        const response = await axios.put(`/api/streams/${streamId}`, { refresh: true })
        
        if (response.data && response.data.stream) {
          // Update the stream in local state
          const updatedStream = response.data.stream
          
          // Update in localStreams
          const streamIndex = localStreams.value.findIndex(s => s.id === streamId)
          if (streamIndex >= 0) {
            localStreams.value[streamIndex] = updatedStream
            
            // If this is the selected stream, update it too
            if (selectedStream.value && selectedStream.value.id === streamId) {
              selectedStream.value = updatedStream
            }
          }
        }
      } catch (error) {
        console.error('Error refreshing stream:', error)
      } finally {
        isRefreshingStream.value = false
      }
    }
    
    // Animation functions
    const animateStreamElements = () => {
      // Skip animations if no data
      if (localStreams.value.length === 0) {
        animateEmptyState()
        return
      }
      
      // Animate header elements
      if (streamHeader.value) {
        anime({
          targets: streamHeader.value,
          translateY: [-30, 0],
          opacity: [0, 1],
          duration: 600,
          easing: 'easeOutQuad'
        })
      }
      
      // Animate status pills
      if (livePill.value) {
        anime({
          targets: livePill.value,
          translateX: [-20, 0],
          opacity: [0, 1],
          delay: 200,
          duration: 500,
          easing: 'easeOutQuad'
        })
      }
      
      if (offlinePill.value) {
        anime({
          targets: offlinePill.value,
          translateX: [-20, 0],
          opacity: [0, 1],
          delay: 300,
          duration: 500,
          easing: 'easeOutQuad'
        })
      }
      
      // Animate section headers
      if (liveStreamSection.value) {
        anime({
          targets: liveStreamSection.value.querySelector('.section-header'),
          translateY: [-20, 0],
          opacity: [0, 1],
          duration: 500,
          easing: 'easeOutQuad'
        })
      }
      
      if (offlineStreamSection.value) {
        anime({
          targets: offlineStreamSection.value.querySelector('.section-header'),
          translateY: [-20, 0],
          opacity: [0, 1],
          delay: 100,
          duration: 500,
          easing: 'easeOutQuad'
        })
      }
      
      // Animate stream cards with staggered effect
      if (liveStreamCards.value.length > 0) {
        anime({
          targets: liveStreamCards.value,
          translateY: [40, 0],
          opacity: [0, 1],
          delay: anime.stagger(100),
          duration: 600,
          easing: 'easeOutQuad'
        })
      }
      
      if (offlineStreamCards.value.length > 0) {
        anime({
          targets: offlineStreamCards.value,
          translateY: [40, 0],
          opacity: [0, 1],
          delay: anime.stagger(100),
          duration: 600,
          easing: 'easeOutQuad'
        })
      }
    }
    
    const animateEmptyState = () => {
      if (emptyState.value) {
        anime({
          targets: emptyState.value,
          translateY: [30, 0],
          opacity: [0, 1],
          duration: 800,
          easing: 'easeOutQuad'
        })
        
        anime({
          targets: emptyState.value.querySelector('.empty-icon'),
          scale: [0.5, 1],
          opacity: [0, 1],
          duration: 1000,
          delay: 300,
          easing: 'easeOutElastic(1, 0.5)'
        })
        
        anime({
          targets: [
            emptyState.value.querySelector('.empty-title'),
            emptyState.value.querySelector('.empty-description')
          ],
          translateY: [20, 0],
          opacity: [0, 1],
          delay: anime.stagger(150, {start: 400}),
          duration: 800,
          easing: 'easeOutQuad'
        })
      }
    }
    
    // Animate error message
    const animateErrorMessage = () => {
      if (errorMessage.value) {
        anime({
          targets: errorMessage.value,
          translateY: [20, 0],
          opacity: [0, 1],
          duration: 500,
          easing: 'easeOutQuad'
        })
        
        anime({
          targets: errorMessage.value.querySelector('.error-icon'),
          rotate: ['15deg', '-15deg', '0deg'],
          duration: 800,
          delay: 200,
          easing: 'easeOutElastic(1, 0.5)'
        })
      }
    }
    
    // Handle window resize
    const handleResize = () => {
      isMobile.value = window.innerWidth <= 768
      
      // Switch to list view automatically on small screens
      if (isMobile.value && viewMode.value === 'grid') {
        setViewMode('list')
      }
    }
    
    // Lifecycle hooks
    onMounted(async () => {
      // Add resize listener
      window.addEventListener('resize', handleResize)
      
      // Check for saved view mode preference
      try {
        const savedViewMode = localStorage.getItem('streamViewMode')
        if (savedViewMode && ['grid', 'list'].includes(savedViewMode)) {
          viewMode.value = savedViewMode
        }
      } catch (e) {
        console.error('Could not retrieve view mode preference')
      }
      
      // Initial fetch of assigned streams
      await fetchAssignedStreams()
      
      // Set up watch for error to animate
      watch(() => localError.value, (newError) => {
        if (newError) {
          nextTick(() => {
            animateErrorMessage()
          })
        }
      })
      
      // Watch for changes in stream counts to adjust grid layout
      watch(
        [() => liveStreams.value.length, () => offlineStreams.value.length],
        () => {
          nextTick(() => {
            // Animate grid layout adjustments
            anime({
              targets: '.streams-grid',
              scale: [0.95, 1],
              duration: 300,
              easing: 'easeOutQuad'
            })
          })
        }
      )
    })
    
    onBeforeUnmount(() => {
      // Remove resize listener
      window.removeEventListener('resize', handleResize)
    })
    
    // Return all the reactive variables and methods
    return {
      // Reactive state
      isDarkTheme,
      isMobile,
      viewMode,
      showModal,
      selectedStream,
      selectedStreamDetections,
      isRefreshingStream,
      
      // Computed properties
      liveStreams,
      offlineStreams,
      
      // Methods
      fetchAssignedStreams,
      getDetectionCount,
      setViewMode,
      openStreamDetails,
      closeModal,
      handleStreamRefresh,
      enhanceStreamWithUsername,
      
      // Refs for animations
      streamHeader,
      streamsContent,
      liveStreamSection,
      offlineStreamSection,
      liveStreamsGrid,
      offlineStreamsGrid,
      emptyState,
      errorMessage,
      livePill,
      offlinePill,
      headerActions,
      viewToggleBtn,
      loaderContainer,
      liveStreamCards,
      offlineStreamCards,
      handleDetectionToggled,
      
      // Use local props for data that needs to be reactive
      streams: localStreams,
      isLoading: localIsLoading,
      error: localError,
      lastRefreshed: localLastRefreshed
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
  overflow: hidden;
  transition: all 0.3s ease-in-out;
}

.dark-theme {
  --bg-color: #18181B;
  --text-color: #EFEFF1;
  --border-color: #3a3a3d;
  --accent-color: #9147FF;
  --active-color: #1F9D55;
  --hover-color: #2c2c35;
}

/* Dashboard Header */
.stream-dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-color, #dee2e6);
  transition: all 0.3s ease-in-out;
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
  transition: all 0.3s ease-in-out;
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
  position: relative;
}

.status-indicator.offline {
  background-color: #718096;
}

.status-indicator .status-pulse {
  position: absolute;
  top: -4px;
  left: -4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background-color: rgba(31, 157, 85, 0.3);
  animation: pulse 2s infinite;
}

.header-actions {
  display: flex;
  gap: 10px;
}

/* Updated view mode toggle */
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
  transition: all 0.2s ease-in-out;
  border-radius: 4px;
}

.view-mode-btn.active {
  background-color: var(--accent-color, #9147FF);
  color: white;
}

.view-mode-btn:hover:not(.active) {
  background-color: var(--hover-color, rgba(0, 0, 0, 0.1));
}

/* Streams Content Container */
.streams-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
  transition: all 0.3s ease-in-out;
}

/* Stream Sections */
.stream-section {
  width: 100%;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header .status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-header h3 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
}

/* Streams Grid Layout */
.streams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  transition: all 0.3s ease-in-out;
}

/* Responsive grid adjustments based on stream count */
.streams-grid.medium {
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
}

.streams-grid.small {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

/* List View */
.list-layout {
  grid-template-columns: 1fr !important;
  gap: 10px !important;
}

.stream-card-wrapper {
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease-in-out;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
}

.stream-card-wrapper:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.stream-card-wrapper.list-item {
  height: 100px;
}

.stream-card-wrapper:not(.list-item) {
  height: 240px;
}

/* Empty State */
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

/* Loading Overlay */
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

/* Error Message */
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
  transition: all 0.2s ease;
}

.retry-button:hover {
  background-color: var(--accent-color, #7e32e6);
}

/* Animations */
@keyframes pulse {
  0% {
    transform: scale(0.9);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.3;
  }
  100% {
    transform: scale(0.9);
    opacity: 0.7;
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s ease-out;
}

.slide-up-enter-from, .slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

.modal-enter-active, .modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

/* Mobile Optimizations */
@media (max-width: 768px) {
  .agent-streams {
    padding: 15px 10px;
  }
  
  .stream-dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .streams-grid {
    grid-template-columns: 1fr !important;
  }
  
  .stream-status-summary {
    width: 100%;
    justify-content: space-between;
  }
}
</style>