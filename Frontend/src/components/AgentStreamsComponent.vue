<template>
  <div class="agent-streams" :class="{ 'dark-theme': isDarkTheme }">
    <!-- Dashboard-style header with animated entrance -->
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
        <div class="last-checked" v-if="lastRefreshed" ref="timestampEl">
          Last checked: {{ formattedLastRefresh }}
        </div>
      </div>
      <div class="header-actions" ref="headerActions">
        <button class="view-toggle-btn" @click="toggleViewMode" ref="viewToggleBtn">
          <font-awesome-icon :icon="['fas', viewMode === 'grid' ? 'list' : 'th']" />
          <span>{{ viewMode === 'grid' ? 'List' : 'Grid' }}</span>
        </button>
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
        <div class="section-header">
          <div class="status-indicator">
            <span class="status-pulse"></span>
            <h3>Live Streams</h3>
          </div>
          <div class="stream-counter">{{ liveStreams.length }} {{ liveStreams.length === 1 ? 'stream' : 'streams' }}</div>
        </div>
        
        <div 
          class="streams-grid" 
          ref="liveStreamsGrid"
          :class="{'list-layout': viewMode === 'list'}"
        >
          <div 
            v-for="(stream, index) in liveStreams" 
            :key="stream.id || 'live-' + index"
            class="stream-card-wrapper"
            @mouseenter="animateStreamHover($event, true)"
            @mouseleave="animateStreamHover($event, false)"
            @click="openStreamDetails(stream)"
            :data-index="index"
            ref="liveStreamCards"
          >
            <StreamCard 
              :stream="stream" 
              :index="index"
              :isLive="true"
              :detectionCount="getDetectionCount(stream)"
              :playVideo="true"
              class="stream-card"
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
          <div class="stream-counter">{{ offlineStreams.length }} {{ offlineStreams.length === 1 ? 'stream' : 'streams' }}</div>
        </div>
        
        <div 
          class="streams-grid" 
          ref="offlineStreamsGrid"
          :class="{'list-layout': viewMode === 'list'}"
        >
          <div 
            v-for="(stream, index) in offlineStreams" 
            :key="stream.id || 'offline-' + index"
            class="stream-card-wrapper"
            @mouseenter="animateStreamHover($event, true)"
            @mouseleave="animateStreamHover($event, false)"
            @click="openStreamDetails(stream)"
            :data-index="index"
            ref="offlineStreamCards"
          >
            <StreamCard 
              :stream="stream" 
              :index="index"
              :isLive="false"
              :detectionCount="getDetectionCount(stream)"
              :playVideo="false"
              class="stream-card"
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
        <button class="empty-action-btn" @click="fetchAssignedStreams">
          <font-awesome-icon :icon="['fas', 'sync']" />
          <span>Check for streams</span>
        </button>
      </div>
    </div>
    
    <!-- Loading overlay with animated spinner -->
    <transition name="fade">
      <div class="loading-overlay" v-if="isLoading">
        <div class="loader-container" ref="loaderContainer">
          <div class="loader-circle"></div>
          <div class="loader-text">Checking stream status...</div>
          <div class="loader-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
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
    
    <!-- Refresh button with interactive animation -->
    <div 
      class="refresh-control" 
      @click="handleRefreshClick"
      v-if="!isLoading && streams.length > 0"
      ref="refreshBtn"
    >
      <font-awesome-icon :icon="['fas', 'sync']" :class="{'spinning': isRefreshing}" />
    </div>

    <!-- Animated filter controls -->
    <div class="filter-controls" v-if="streams.length > 0" ref="filterControls">
      <div class="filter-toggle" @click="showFilters = !showFilters">
        <font-awesome-icon :icon="['fas', 'filter']" />
        <span>Filter</span>
        <font-awesome-icon 
          :icon="['fas', showFilters ? 'chevron-up' : 'chevron-down']" 
          class="toggle-icon"
        />
      </div>
      <transition name="slide-down">
        <div class="filter-options" v-if="showFilters">
          <div class="filter-option">
            <input type="checkbox" id="showLive" v-model="filterOptions.showLive">
            <label for="showLive">Show Live</label>
          </div>
          <div class="filter-option">
            <input type="checkbox" id="showOffline" v-model="filterOptions.showOffline">
            <label for="showOffline">Show Offline</label>
          </div>
          <div class="filter-option">
            <input type="checkbox" id="showDetections" v-model="filterOptions.showDetections">
            <label for="showDetections">Only With Detections</label>
          </div>
        </div>
      </transition>
    </div>

    <!-- Stream Details Modal with enhanced animations -->
    <transition name="modal">
      <StreamDetailsModal
        v-if="showModal && selectedStream"
        :stream="selectedStream"
        :detections="selectedStreamDetections"
        :isRefreshing="isRefreshingStream"
        @close="closeModal"
        @refresh="handleStreamRefresh"
      />
    </transition>
    
    <!-- Quick action tooltip -->
    <transition name="fade">
      <div class="action-tooltip" v-if="showTooltip" ref="tooltip" :style="tooltipStyle">
        {{ tooltipText }}
      </div>
    </transition>
  </div>
</template>

<script>
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
  faBell,
  faArrowDown,
  faFilter,
  faChevronUp,
  faChevronDown
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
  faBell,
  faArrowDown,
  faFilter,
  faChevronUp,
  faChevronDown
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
    // Inject app theme from parent using the same pattern as App.vue
    const appTheme = inject('theme', ref(true))
    
    // Create a computed property for isDarkTheme to match App.vue's naming convention
    const isDarkTheme = computed(() => appTheme.value === true)
    
    // Reactive state
    const showModal = ref(false)
    const selectedStream = ref(null)
    const selectedStreamDetections = ref([])
    const isRefreshingStream = ref(false)
    const isMobile = ref(window.innerWidth <= 768)
    const viewMode = ref(isMobile.value ? 'list' : 'grid')
    const isRefreshing = ref(false)
    const showFilters = ref(false)
    const filterOptions = ref({
      showLive: true,
      showOffline: true,
      showDetections: false
    })
    
    // API related states
    const localStreams = ref([])
    const localIsLoading = ref(false)
    const localError = ref(null)
    const localLastRefreshed = ref(new Date())
    
    // Tooltip state
    const showTooltip = ref(false)
    const tooltipText = ref('')
    const tooltipStyle = ref({})
    const tooltipTimeout = ref(null)
    
    // Animation refs
    const streamHeader = ref(null)
    const streamsContent = ref(null)
    const liveStreamSection = ref(null)
    const offlineStreamSection = ref(null)
    const liveStreamsGrid = ref(null)
    const offlineStreamsGrid = ref(null)
    const emptyState = ref(null)
    const refreshBtn = ref(null)
    const errorMessage = ref(null)
    const livePill = ref(null)
    const offlinePill = ref(null)
    const timestampEl = ref(null)
    const headerActions = ref(null)
    const viewToggleBtn = ref(null)
    const filterControls = ref(null)
    const tooltip = ref(null)
    const loaderContainer = ref(null)
    const liveStreamCards = ref([])
    const offlineStreamCards = ref([])
    
    // API methods
    const fetchAssignedStreams = async () => {
      if (localIsLoading.value) return
      
      localIsLoading.value = true
      localError.value = null
      
      try {
        // Build the query parameters
        const params = {}
        if (props.agentId) {
          params.agent_id = props.agentId
        }
        
        // Make the API call to get assignments
        const assignmentsResponse = await axios.get('/api/assignments', { params })
        
        if (!assignmentsResponse.data || !assignmentsResponse.data.assignments) {
          throw new Error('Invalid response format from server')
        }
        
        // Extract stream IDs from assignments
        const assignments = assignmentsResponse.data.assignments
        
        if (assignments.length === 0) {
          localStreams.value = []
          localIsLoading.value = false
          localLastRefreshed.value = new Date()
          return
        }
        
        // Get details for each stream
        const streamsData = []
        for (const assignment of assignments) {
          if (!assignment.stream_id) continue
          
          try {
            // Fetch streams and any detection logs associated with them
            const streamResponse = await axios.get(`/api/streams/${assignment.stream_id}`)
            if (streamResponse.data) {
              // Add the stream to our collection
              streamsData.push(streamResponse.data)
            }
          } catch (streamError) {
            console.error(`Error fetching stream ${assignment.stream_id}:`, streamError)
          }
        }
        
        // Update local state
        localStreams.value = streamsData
        localLastRefreshed.value = new Date()
      } catch (error) {
        console.error('Error fetching assigned streams:', error)
        localError.value = error.response?.data?.message || 'Failed to fetch assigned streams'
      } finally {
        localIsLoading.value = false
      }
    }
    
    // Get detailed stream info including m3u8 URLs
    const fetchStreamDetails = async (streamId) => {
      try {
        const response = await axios.get(`/api/streams/${streamId}`)
        if (response.data) {
          // Find and update the stream in our local collection
          const index = localStreams.value.findIndex(s => s.id === streamId)
          if (index !== -1) {
            localStreams.value[index] = response.data
          }
          return response.data
        }
      } catch (error) {
        console.error(`Error fetching details for stream ${streamId}:`, error)
        showTooltipMessage(`Failed to refresh stream details`)
        return null
      }
    }
    
    // Method to refresh a specific stream
    const refreshStreamData = async (streamId) => {
      try {
        const stream = localStreams.value.find(s => s.id === streamId)
        if (!stream) return null
        
        let refreshEndpoint = null
        
        // Determine the correct refresh endpoint based on stream type
        if (stream.type === 'chaturbate') {
          refreshEndpoint = '/api/streams/refresh/chaturbate'
          return await axios.post(refreshEndpoint, { room_slug: stream.streamer_username })
        } else if (stream.type === 'stripchat') {
          refreshEndpoint = '/api/streams/refresh/stripchat'
          return await axios.post(refreshEndpoint, { room_url: stream.room_url })
        }
        
        return null
      } catch (error) {
        console.error(`Error refreshing stream ${streamId}:`, error)
        showTooltipMessage(`Failed to refresh stream`)
        return null
      }
    }
    
    // Computed properties
    const streamsToDisplay = computed(() => {
      // Use props.streams if provided, otherwise use local state
      return props.streams.length > 0 ? props.streams : localStreams.value
    })
    
    const liveStreams = computed(() => {
      const streams = streamsToDisplay.value
      const filtered = streams.filter(stream => stream && stream.isLive === true)
      
      // Apply additional filters if needed
      if (filterOptions.value.showDetections) {
        return filtered.filter(stream => getDetectionCount(stream) > 0)
      }
      
      return filtered
    })
    
    const offlineStreams = computed(() => {
      const streams = streamsToDisplay.value
      const filtered = streams.filter(stream => stream && stream.isLive === false)
      
      // Apply additional filters if needed
      if (filterOptions.value.showDetections) {
        return filtered.filter(stream => getDetectionCount(stream) > 0)
      }
      
      return filtered
    })
    
    const currentLoading = computed(() => {
      return props.isLoading || localIsLoading.value
    })
    
    const currentError = computed(() => {
      return props.error || localError.value
    })
    
    const formattedLastRefresh = computed(() => {
      const timestamp = props.lastRefreshed || localLastRefreshed.value
      if (!timestamp) return ''
      return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    
    // Toggle view mode with enhanced animation
    const toggleViewMode = () => {
      const newMode = viewMode.value === 'grid' ? 'list' : 'grid'
      
      // Animate view toggle button
      anime({
        targets: viewToggleBtn.value,
        scale: [1, 1.2, 1],
        rotate: ['0deg', '5deg', '-5deg', '0deg'],
        duration: 500,
        easing: 'easeInOutBack'
      })
      
      // First fade out all cards
      const allCards = [...document.querySelectorAll('.stream-card-wrapper')]
      anime({
        targets: allCards,
        opacity: [1, 0.3],
        scale: [1, 0.95],
        duration: 300,
        easing: 'easeOutQuad',
        complete: () => {
          // Change the view mode
          viewMode.value = newMode
          
          // Then animate them back in with delay
          nextTick(() => {
            anime({
              targets: allCards,
              opacity: [0.3, 1],
              scale: [0.95, 1],
              delay: anime.stagger(30),
              duration: 400,
              easing: 'easeOutQuad'
            })
          })
        }
      })
      
      // Show tooltip
      showTooltipMessage(`Switched to ${newMode} view`)
    }
    
    // Show tooltip message
    const showTooltipMessage = (message, duration = 2000) => {
      // Clear any existing timeout
      if (tooltipTimeout.value) clearTimeout(tooltipTimeout.value)
      
      tooltipText.value = message
      
      // Position near the view toggle button if available, otherwise center
      if (viewToggleBtn.value) {
        const btnRect = viewToggleBtn.value.getBoundingClientRect()
        tooltipStyle.value = {
          top: `${btnRect.bottom + 10}px`,
          left: `${btnRect.left + (btnRect.width / 2)}px`,
          transform: 'translateX(-50%)'
        }
      } else {
        tooltipStyle.value = {
          top: '20%',
          left: '50%',
          transform: 'translateX(-50%)'
        }
      }
      
      showTooltip.value = true
      
      // Animate tooltip
      nextTick(() => {
        if (tooltip.value) {
          anime({
            targets: tooltip.value,
            translateY: ['-10px', '0px'],
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutQuad'
          })
        }
      })
      
      // Hide after duration
      tooltipTimeout.value = setTimeout(() => {
        if (tooltip.value) {
          anime({
            targets: tooltip.value,
            translateY: ['0px', '-10px'],
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInQuad',
            complete: () => {
              showTooltip.value = false
            }
          })
        } else {
          showTooltip.value = false
        }
      }, duration)
    }
    
    // Handle refresh button click with animation
    const handleRefreshClick = () => {
      if (isRefreshing.value) return
      
      isRefreshing.value = true
      
      // Animate the refresh button
      anime({
        targets: refreshBtn.value,
        rotate: '360deg',
        scale: [1, 1.2, 1],
        duration: 800,
        easing: 'easeInOutQuad'
      })
      
      // Either use the provided refresh method or our own
      if (props.streams.length > 0) {
        emit('refresh-streams')
      } else {
        fetchAssignedStreams()
      }
      
      // Show tooltip
      showTooltipMessage('Refreshing streams...')
      
      // Reset after animation completes
      setTimeout(() => {
        isRefreshing.value = false
      }, 1000)
    }
    
    // Animate stream sections and cards with enhanced effects
    const animateStreamSections = () => {
      console.log('Animating stream sections');
      
      // Animate header with staggered children
      if (streamHeader.value) {
        anime({
          targets: streamHeader.value,
          translateY: ['-20px', 0],
          opacity: [0, 1],
          easing: 'easeOutQuad',
          duration: 600
        })
        
        if (livePill.value && offlinePill.value) {
          anime({
            targets: [livePill.value, offlinePill.value, timestampEl.value].filter(Boolean),
            translateY: ['-10px', 0],
            opacity: [0, 1],
            delay: anime.stagger(100, {start: 200}),
            easing: 'easeOutQuad',
            duration: 500
          })
        }
        
        if (headerActions.value) {
          anime({
            targets: headerActions.value,
            translateX: ['20px', 0],
            opacity: [0, 1],
            easing: 'easeOutQuad',
            duration: 600,
            delay: 300
          })
        }
      }
      
      // Animate live streams section
      if (liveStreams.value.length > 0 && liveStreamSection.value) {
        anime({
          targets: liveStreamSection.value,
          translateY: [20, 0],
          opacity: [0, 1],
          easing: 'easeOutQuad',
          duration: 600
        })
        
        // Animate the section header
        const sectionHeader = liveStreamSection.value.querySelector('.section-header')
        if (sectionHeader) {
          anime({
            targets: sectionHeader,
            translateX: ['-20px', 0],
            opacity: [0, 1],
            easing: 'easeOutQuad',
            duration: 600,
            delay: 200
          })
        }
        
        // Safely animate stream cards with more dynamic effects
        const liveCards = document.querySelectorAll('.live-streams .stream-card-wrapper')
        if (liveCards && liveCards.length > 0) {
          anime({
            targets: liveCards,
            scale: [0.85, 1],
            translateY: [20, 0],
            opacity: [0, 1],
            delay: anime.stagger(80, {grid: [Math.min(3, liveCards.length), Math.ceil(liveCards.length/3)], from: 'center'}),
            easing: 'easeOutQuad',
            duration: 600
          })
        }
      }
      
      // Animate offline streams section with delay
      if (offlineStreams.value.length > 0 && offlineStreamSection.value) {
        anime({
          targets: offlineStreamSection.value,
          translateY: [20, 0],
          opacity: [0, 1],
          easing: 'easeOutQuad',
          duration: 600,
          delay: 400
        })
        
        // Animate the section header
        const sectionHeader = offlineStreamSection.value.querySelector('.section-header')
        if (sectionHeader) {
          anime({
            targets: sectionHeader,
            translateX: ['-20px', 0],
            opacity: [0, 1],
            easing: 'easeOutQuad',
            duration: 600,
            delay: 500
          })
        }
        
        // Safely animate stream cards with more dynamic effects
        const offlineCards = document.querySelectorAll('.offline-streams .stream-card-wrapper')
        if (offlineCards && offlineCards.length > 0) {
          anime({
            targets: offlineCards,
            scale: [0.85, 1],
            translateY: [20, 0],
            opacity: [0, 1],
            delay: anime.stagger(60, {grid: [Math.min(3, offlineCards.length), Math.ceil(offlineCards.length/3)], from: 'center'}),
            easing: 'easeOutQuad',
            duration: 600
          })
        }
      }
      
      // Animate empty state if no streams with bouncy effect
      if (streamsToDisplay.value.length === 0 && emptyState.value && !currentLoading.value) {
        anime({
          targets: emptyState.value,
          scale: [0.8, 1],
          opacity: [0, 1],
          easing: 'easeOutElastic(1, 0.5)',
          duration: 1200
        })
        
        const emptyIcon = emptyState.value.querySelector('.empty-icon')
        if (emptyIcon) {
          anime({
            targets: emptyIcon,
            rotate: ['-20deg', '0deg'],
            scale: [0.7, 1.2, 1],
            duration: 1500,
            easing: 'easeOutElastic(1, 0.5)',
            delay: 300
          })
        }
        
        const actionBtn = emptyState.value.querySelector('.empty-action-btn')
        if (actionBtn) {
          anime({
            targets: actionBtn,
            translateY: [20, 0],
            opacity: [0, 1],
            scale: [0.9, 1],
            duration: 800,
            easing: 'easeOutQuad',
            delay: 800
          })
        }
      }
      
      // Animate error message if there's an error
      if (currentError.value && errorMessage.value) {
        anime({
          targets: errorMessage.value,
          translateY: [20, 0],
          opacity: [0, 1],
          duration: 600,
          easing: 'easeOutQuad'
        })
        
        const errorIcon = errorMessage.value.querySelector('.error-icon')
        if (errorIcon) {
          anime({
            targets: errorIcon,
            rotate: ['0deg', '20deg', '-15deg', '10deg', '-5deg', '0deg'],
            duration: 1200,
            easing: 'easeOutElastic(1, 0.5)',
            delay: 300
          })
        }
      }
      
      // Animate refresh button with a spring effect
      if (refreshBtn.value && streamsToDisplay.value.length > 0) {
        anime({
          targets: refreshBtn.value,
          scale: [0, 1.2, 1],
          rotate: ['0deg', '360deg'],
          easing: 'easeOutElastic(1, 0.5)',
          duration: 1200,
          delay: 800
        })
      }
      
      // Animate filter controls entrance
      if (filterControls.value && streamsToDisplay.value.length > 0) {
        anime({
          targets: filterControls.value,
          translateY: [20, 0],
          opacity: [0, 1],
          easing: 'easeOutQuad',
          duration: 600,
          delay: 1000
        })
      }
      
      // Animate loader if loading
      if (currentLoading.value && loaderContainer.value) {
        anime({
          targets: loaderContainer.value.querySelectorAll('.dot'),
          translateY: [0, -10, 0],
          delay: anime.stagger(150),
          loop: true,
          easing: 'easeInOutQuad',
          duration: 600
        })
      }
    }
    
    // Animate hover on stream cards with enhanced effects
    const animateStreamHover = (event, isEnter) => {
      const card = event.currentTarget
      
      if (isEnter) {
        // Mouse enter animation - more dynamic
        anime({
          targets: card,
          translateY: -8,
          boxShadow: '0 14px 28px rgba(0, 0, 0, 0.2)',
          scale: 1.03,
          duration: 400,
          easing: 'easeOutQuad'
        })
        
        // Animate the inner card elements
        const streamTitle = card.querySelector('.stream-title')
        if (streamTitle) {
          anime({
            targets: streamTitle,
            translateX: [0, 5],
            duration: 300,
            easing: 'easeOutQuad'
          })
        }
         
        const actionBtn = emptyState.value.querySelector('.empty-action-btn')
        if (actionBtn) {
          anime({
            targets: actionBtn,
            translateY: [20, 0],
            opacity: [0, 1],
            scale: [0.9, 1],
            duration: 800,
            easing: 'easeOutQuad',
            delay: 800
          })
        }
      }
      
      // Animate error message if there's an error
      if (props.error && errorMessage.value) {
        anime({
          targets: errorMessage.value,
          translateY: [20, 0],
          opacity: [0, 1],
          duration: 600,
          easing: 'easeOutQuad'
        })
        
        const errorIcon = errorMessage.value.querySelector('.error-icon')
        if (errorIcon) {
          anime({
            targets: errorIcon,
            rotate: ['0deg', '20deg', '-15deg', '10deg', '-5deg', '0deg'],
            duration: 1200,
            easing: 'easeOutElastic(1, 0.5)',
            delay: 300
          })
        }
      }
      
      // Animate refresh button with a spring effect
      if (refreshBtn.value && props.streams.length > 0) {
        anime({
          targets: refreshBtn.value,
          scale: [0, 1.2, 1],
          rotate: ['0deg', '360deg'],
          easing: 'easeOutElastic(1, 0.5)',
          duration: 1200,
          delay: 800
        })
      }
      
      // Animate filter controls entrance
      if (filterControls.value && props.streams.length > 0) {
        anime({
          targets: filterControls.value,
          translateY: [20, 0],
          opacity: [0, 1],
          easing: 'easeOutQuad',
          duration: 600,
          delay: 1000
        })
      }
      
      // Animate loader if loading
      if (props.isLoading && loaderContainer.value) {
        anime({
          targets: loaderContainer.value.querySelectorAll('.dot'),
          translateY: [0, -10, 0],
          delay: anime.stagger(150),
          loop: true,
          easing: 'easeInOutQuad',
          duration: 600
        })
      }
    }
    
    // Animate hover on stream cards with enhanced effects
    
    
    // Get detection count for a stream
    const getDetectionCount = (stream) => {
      if (!stream || !stream.detections) return 0
      return stream.detections.length
    }
    
    // Open stream details modal with enhanced animation
    const openStreamDetails = (stream) => {
      selectedStream.value = stream
      selectedStreamDetections.value = stream.detections || []
      
      // Pre-animation setup
      nextTick(() => {
        showModal.value = true
      })
    }
    
    // Close stream details modal with enhanced animation
    const closeModal = () => {
      showModal.value = false
      
      // Clear selected stream after animation completes
      setTimeout(() => {
        selectedStream.value = null
        selectedStreamDetections.value = []
      }, 300)
    }
    
    // Handle stream refresh from details modal
    const handleStreamRefresh = () => {
      if (!selectedStream.value || isRefreshingStream.value) return
      
      isRefreshingStream.value = true
      
      // Emit event to parent component to update the stream
      emit('update-stream', selectedStream.value.id)
      
      // Show tooltip
      showTooltipMessage('Refreshing stream details...')
      
      // Wait a bit for the update to happen
      setTimeout(() => {
        isRefreshingStream.value = false
      }, 1000)
    }
    
    // Handle window resize
    const handleResize = () => {
      isMobile.value = window.innerWidth <= 768
      
      // If mobile and in grid view, switch to list
      if (isMobile.value && viewMode.value === 'grid') {
        viewMode.value = 'list'
      }
    }
    
    // Watch for changes in stream data to trigger animations
    watch(() => props.streams, (newStreams) => {
      console.log(`Stream data changed, count: ${newStreams?.length || 0}`);
      nextTick(() => {
        animateStreamSections()
      })
    }, { immediate: false, deep: true })
    
    // Watch for loading state to trigger animation
    watch(() => props.isLoading, (newValue) => {
      console.log(`Loading state changed: ${newValue}`);
      if (newValue) {
        // Animate loader when loading starts
        nextTick(() => {
          if (loaderContainer.value) {
            anime({
              targets: loaderContainer.value,
              opacity: [0, 1],
              scale: [0.9, 1],
              duration: 400,
              easing: 'easeOutQuad'
            })
            
            anime({
              targets: loaderContainer.value.querySelectorAll('.dot'),
              translateY: [0, -10, 0],
              delay: anime.stagger(150),
              loop: true,
              easing: 'easeInOutQuad',
              duration: 600
            })
          }
        })
      }
    })
    
    // Setup and cleanup
    onMounted(() => {
      console.log('AgentStreamsComponent mounted');
      
      // Initial animations
      nextTick(() => {
        animateStreamSections()
      })
      
      // Set up event listeners
      window.addEventListener('resize', handleResize)
    })
    
    onBeforeUnmount(() => {
      // Cleanup event listeners
      window.removeEventListener('resize', handleResize)
      
      // Clear any timeouts
      if (tooltipTimeout.value) {
        clearTimeout(tooltipTimeout.value)
      }
    })
    
    return {
      // State
      appTheme,
      isDarkTheme,
      liveStreams,
      offlineStreams,
      formattedLastRefresh,
      showModal,
      selectedStream,
      selectedStreamDetections,
      isRefreshingStream,
      isMobile,
      viewMode,
      showFilters,
      filterOptions,
      isRefreshing,
      showTooltip,
      tooltipText,
      tooltipStyle,
      
      // Refs
      streamHeader,
      streamsContent,
      liveStreamSection,
      offlineStreamSection,
      liveStreamsGrid,
      offlineStreamsGrid,
      emptyState,
      refreshBtn,
      errorMessage,
      livePill,
      offlinePill,
      timestampEl,
      headerActions,
      viewToggleBtn,
      filterControls,
      tooltip,
      loaderContainer,
      liveStreamCards,
      offlineStreamCards,
      
      // Methods
      getDetectionCount,
      openStreamDetails,
      closeModal,
      handleStreamRefresh,
      toggleViewMode,
      animateStreamHover,
      showTooltipMessage,
      handleRefreshClick,
      animateStreamSections,
      fetchStreamDetails,
      refreshStreamData
    }
  }
}
</script>

<style scoped>
/* Base container */
.agent-streams {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--background-color, #f7f9fc);
  color: var(--text-color, #333);
  transition: all 0.3s ease;
}

.agent-streams.dark-theme {
  --background-color: #1f2937;
  --card-bg: #111827;
  --text-color: #e5e7eb;
  --text-muted: #9ca3af;
  --heading-color: #f3f4f6;
  --border-color: rgba(255, 255, 255, 0.1);
  --pill-bg: rgba(156, 163, 175, 0.2);
  --button-bg: #374151;
  --button-hover: #4b5563;
  --button-text: #e5e7eb;
  --active-bg: #2563eb;
  --success-color: #10b981;
  --counter-bg: rgba(255, 255, 255, 0.1);
  --empty-icon: #4b5563;
  --hover-bg: rgba(255, 255, 255, 0.05);
}

/* Dashboard-style header */
.stream-dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: var(--card-bg, #ffffff);
  border-bottom: 1px solid var(--border-color, rgba(0, 0, 0, 0.05));
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stream-status-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  background-color: var(--button-bg, #f0f4f8);
  color: var(--button-text, #3182ce);
  border: none;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-toggle-btn:hover {
  background-color: var(--button-hover, #e2e8f0);
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  background-color: var(--pill-bg, rgba(0, 0, 0, 0.05));
  color: var(--text-muted, #6B7280);
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.status-pill.active {
  background-color: var(--active-bg, #3B82F6);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
}

.status-pill .status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--success-color, #10B981);
}

.status-pill .status-indicator.offline {
  background-color: var(--text-muted, #6B7280);
}

.last-checked {
  font-size: 0.85rem;
  color: var(--text-muted, #6B7280);
  margin-left: auto;
}

/* Streams content area */
.streams-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  transition: all 0.3s ease;
}

.streams-content.list-view {
  padding: 16px 20px;
  gap: 16px;
}

/* Stream sections */
.stream-section {
  background-color: var(--card-bg, #ffffff);
  border-radius: 12px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
  padding: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stream-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  position: relative;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-indicator h3 {
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
  color: var(--heading-color, #111827);
}

.status-pulse {
  width: 10px;
  height: 10px;
  background-color: var(--success-color, #10B981);
  border-radius: 50%;
  position: relative;
  animation: pulse 2s infinite;
}

.status-dot {
  width: 10px;
  height: 10px;
  background-color: var(--text-muted, #9CA3AF);
  border-radius: 50%;
}

.stream-counter {
  font-size: 0.85rem;
  color: var(--text-muted, #6B7280);
  padding: 4px 10px;
  background-color: var(--counter-bg, rgba(0, 0, 0, 0.05));
  border-radius: 16px;
  transition: all 0.3s ease;
}

/* Streams grid layout */
.streams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  transition: all 0.3s ease;
}

.streams-grid.list-layout {
  grid-template-columns: 1fr;
  gap: 12px;
}

/* Stream card wrapper */
.stream-card-wrapper {
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  position: relative;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 24px;
  height: 240px;
  background-color: var(--card-bg, #ffffff);
  border-radius: 12px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.empty-icon {
  font-size: 3.5rem;
  margin-bottom: 20px;
  color: var(--empty-icon, #9CA3AF);
  opacity: 0.8;
}

.empty-title {
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--heading-color, #111827);
}

.empty-description {
  font-size: 1rem;
  color: var(--text-muted, #6B7280);
  max-width: 360px;
  margin-bottom: 20px;
}

.empty-action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: var(--active-bg, #3B82F6);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.empty-action-btn:hover {
  background-color: var(--primary-dark, #2563EB);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* Loading overlay */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--overlay-bg, rgba(255, 255, 255, 0.8));
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loader-circle {
  width: 50px;
  height: 50px;
  border: 3px solid var(--loader-bg, rgba(59, 130, 246, 0.2));
  border-radius: 50%;
  border-top-color: var(--active-bg, #3B82F6);
  animation: spin 1s linear infinite;
}

.loader-text {
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-color, #333);
}

.loader-dots {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.loader-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--active-bg, #3B82F6);
  opacity: 0.7;
}

/* Error message */
.error-message {
  background-color: var(--error-bg, rgba(239, 68, 68, 0.1));
  border-left: 4px solid var(--danger-color, #EF4444);
  padding: 16px;
  margin: 16px 0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
}

.error-icon {
  font-size: 1.8rem;
  color: var(--danger-color, #EF4444);
}

.error-text {
  font-size: 1rem;
  color: var(--text-color, #333);
}

.retry-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  background-color: var(--active-bg, #3B82F6);
  color: white;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.retry-button:hover {
  background-color: var(--primary-dark, #2563EB);
  transform: translateY(-2px);
}

.retry-button:active {
  transform: translateY(0);
}

/* Filter controls */
.filter-controls {
  position: fixed;
  left: 20px;
  bottom: 24px;
  z-index: 50;
  background-color: var(--card-bg, #ffffff);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-color, #333);
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-toggle:hover {
  background-color: var(--hover-bg, rgba(0, 0, 0, 0.05));
}

.toggle-icon {
  font-size: 0.8rem;
  transition: transform 0.3s ease;
}

.filter-options {
  padding: 10px 16px;
  border-top: 1px solid var(--border-color, rgba(0, 0, 0, 0.05));
}

.filter-option {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-option label {
  font-size: 0.9rem;
  color: var(--text-color, #333);
  cursor: pointer;
}

/* Refresh button */
.refresh-control {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: var(--active-bg, #3B82F6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  z-index: 50;
  transform-origin: center;
  transition: all 0.3s ease;
}

.refresh-control:hover {
  transform: scale(1.1);
  background-color: var(--primary-dark, #2563EB);
}

.refresh-control:active {
  transform: scale(0.95);
}

.refresh-control .spinning {
  animation: spin 1s linear infinite;
}

/* Action tooltip */
.action-tooltip {
  position: fixed;
  padding: 8px 12px;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  border-radius: 6px;
  font-size: 0.9rem;
  z-index: 200;
  pointer-events: none;
}

/* Animations */
@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Vue transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  transform: scale(0.9);
  opacity: 0;
}

/* Responsive styles */
@media (max-width: 768px) {
  .streams-content {
    padding: 12px;
    gap: 16px;
  }
  
  .stream-section {
    padding: 16px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .streams-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .status-indicator h3 {
    font-size: 1.1rem;
  }
  
  .empty-title {
    font-size: 1.3rem;
  }
  
  .empty-icon {
    font-size: 3rem;
  }
  
  .stream-dashboard-header {
    padding: 12px 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .stream-status-summary {
    width: 100%;
    justify-content: space-between;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .status-pill {
    padding: 4px 10px;
    font-size: 0.85rem;
  }
  
  .last-checked {
    width: 100%;
    margin-top: 6px;
    text-align: right;
  }
  
  .refresh-control {
    bottom: 16px;
    right: 16px;
    width: 42px;
    height: 42px;
  }
  
  .filter-controls {
    left: 16px;
    bottom: 16px;
  }
}

/* Tablet styles */
@media (min-width: 769px) and (max-width: 1024px) {
  .streams-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  }
}

/* Adjust for sidebar */
@media (min-width: 992px) {
  .agent-streams {
    padding-left: 0;
  }
}
</style>