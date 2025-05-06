<template>
  <div
    :class="[
      'mobile-stream-card',
      { 'online': isOnline },
      { 'offline': !isOnline },
      { 'detecting': isDetecting },
      { 'disabled': !isOnline }
    ]"
    @click="handleCardClick"
    @mouseenter="isOnline && canToggleDetection ? addHoverAnimation() : null"
    @mouseleave="isOnline && canToggleDetection ? removeHoverAnimation() : null"
    ref="streamCard"
  >
    <div class="video-container">
      <video ref="videoPlayer" class="video-player"></video>
      <div v-if="detectionCount > 0" class="detection-badge">
        <span>{{ detectionCount }}</span>
      </div>
      <!-- Viewer count overlay for Stripchat streams only -->
      <div v-if="isStripchatStream" class="viewer-count-overlay">
        <span class="viewer-count">
          <font-awesome-icon icon="eye" />
          {{ viewers }}
        </span>
      </div>
      <div class="stream-overlay">
        <button class="view-details-btn">
          <font-awesome-icon icon="eye" />
        </button>
      </div>
      <!-- Offline watermark -->
      <div v-if="!isOnline" class="offline-watermark">
        <span>OFFLINE</span>
      </div>
      <div class="detection-controls">
        <button
          class="detection-toggle"
          :class="{ 'active': isDetecting, 'loading': !canToggleDetection }"
          @click.stop="toggleDetection"
          :title="isDetecting ? 'Stop detection' : 'Start detection'"
          :disabled="!isOnline || !canToggleDetection"
        >
          <span class="detection-icon">
            <font-awesome-icon v-if="!canToggleDetection" icon="spinner" spin />
            <font-awesome-icon v-else :icon="isDetecting ? 'stop-circle' : 'play-circle'" />
          </span>
          <span class="detection-label">{{ isDetecting ? 'Detecting' : 'Start' }}</span>
        </button>
      </div>
    </div>
    <div class="stream-info">
      <div class="info-top-row">
        <h3 class="stream-title" :title="stream.streamer_username">{{ stream.streamer_username }}</h3>
        <span class="platform-tag" :class="stream.platform.toLowerCase()">
          {{ stream.platform }}
        </span>
      </div>
      <div class="stream-meta">
        <div class="agent-badge" :class="{'unassigned': !hasAssignedAgents}">
          <font-awesome-icon :icon="hasAssignedAgents ? 'user-check' : 'user-clock'" />
          <span>{{ assignedAgentNames || 'Unassigned' }}</span>
        </div>
      </div>
      <div class="stream-stats">
        <div class="stat-item">
          <font-awesome-icon icon="clock" />
          <span>{{ getStreamTime() }}</span>
        </div>
        <div class="stat-item alert-stat" :class="{'has-alerts': detectionCount > 0}">
          <font-awesome-icon icon="bell" />
          <span>{{ detectionCount }} {{ detectionCount === 1 ? 'alert' : 'alerts' }}</span>
        </div>
        <!-- Add viewer count stat item for Stripchat streams -->
        <div v-if="isStripchatStream" class="stat-item viewer-stat">
          <font-awesome-icon icon="eye" />
          <span>{{ viewers }} viewers</span>
        </div>
        <div v-if="isDetecting" class="stat-item monitor-stat">
          <font-awesome-icon icon="eye" />
          <span>Monitoring</span>
        </div>
      </div>
    </div>
    <div class="card-footer">
      <button
        class="detection-btn"
        :disabled="!canToggleDetection"
        @click.stop="toggleDetection"
      >
        {{ getDetectionButtonText() }}
      </button>
      <span v-if="isDetecting" class="detecting-indicator">Detecting</span>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import axios from 'axios'
import anime from 'animejs/lib/anime.es.js'
import Hls from 'hls.js'
import { inject } from 'vue'
import { useToast } from 'vue-toastification'

export default {
  name: 'MobileStreamCard',
  components: {},
  props: {
    stream: {
      type: Object,
      required: true
    },
    detectionCount: {
      type: Number,
      default: 0
    },
    index: {
      type: Number,
      default: 0
    },
    totalStreams: {
      type: Number,
      default: 1
    }
  },
  emits: ['click', 'detection-toggled'],
  setup(props, { emit }) {
    const streamCard = ref(null)
    const videoPlayer = ref(null)
    const isOnline = ref(props.stream.status === 'online')
    const isLoading = ref(true)
    const isDetecting = ref(false)
    const canToggleDetection = ref(true)
    const checkStatusInterval = ref(null)
    const streamStatus = ref(props.stream.status || 'unknown')
    const agentCache = ref({})
    const allAgentsFetched = ref(false)
    const eventBus = inject('eventBus', null)
    const isDarkTheme = inject('theme', ref(true))
    const toast = useToast()
    // Viewer count for Stripchat streams
    const viewers = ref(0)
    const viewersRefreshInterval = ref(null)
    
    let hls = null
    let detectionInterval = null
    let streamStatusCheckInterval = ref(null)
    const isPlaying = ref(false)

    const showToast = (message, type = 'success') => {
      console.log(`[Toast ${type}]: ${message}`)
      alert(`[${type.toUpperCase()}]: ${message}`)
    }

    const hasAssignedAgents = computed(() => {
      return props.stream.assignments && props.stream.assignments.length > 0
    })

    const assignedAgentNames = computed(() => {
      if (!hasAssignedAgents.value) return ''
      const names = props.stream.assignments.map(assignment => {
        if (assignment.agent && assignment.agent.username) {
          return assignment.agent.username
        } else {
          const agentId = assignment.agent_id
          return agentCache.value[agentId] || `Agent ${agentId}`
        }
      })
      return names.join(', ')
    })
    
    // Computed property to check if stream is from Stripchat
    const isStripchatStream = computed(() => {
      return props.stream?.platform?.toLowerCase() === 'stripchat'
    })

    const fetchAllAgents = async () => {
      if (allAgentsFetched.value) return
      try {
        const response = await axios.get('/api/agents')
        const agents = response.data || []
        agents.forEach(agent => {
          agentCache.value[agent.id] = agent.username || `Agent ${agent.id}`
        })
        allAgentsFetched.value = true
      } catch (error) {
        console.error('Error fetching all agents:', error)
        fetchAgentUsernames()
      }
    }

    const fetchAgentUsernames = async () => {
      if (!hasAssignedAgents.value) return
      for (const assignment of props.stream.assignments) {
        if (assignment.agent && assignment.agent.username) {
          agentCache.value[assignment.agent_id] = assignment.agent.username
        } else {
          const agentId = assignment.agent_id
          if (!agentCache.value[agentId]) {
            try {
              const response = await axios.get(`/api/agents/${agentId}`)
              agentCache.value[agentId] = response.data.username || `Agent ${agentId}`
            } catch (error) {
              console.error(`Error fetching username for agent ${agentId}:`, error)
              agentCache.value[agentId] = `Agent ${agentId}`
            }
          }
        }
      }
    }
    
    // Fetch viewer count for Stripchat streams
    const fetchViewerCount = async () => {
      // Only proceed if this is a Stripchat stream
      if (!isStripchatStream.value) return
      
      const username = getStreamerUsername()
      if (!username) return
      
      try {
        const response = await axios.get(`/api/stripchat-viewers/${username}`)
        
        // Extract guest count from response
        if (response.data && response.data.guests !== undefined) {
          // Update viewers with just the guests count for Stripchat
          viewers.value = response.data.guests
          
          // Add animation for viewer count update
          anime({
            targets: '.viewer-count',
            scale: [1, 1.1, 1],
            duration: 300,
            easing: 'easeOutQuad'
          })
        }
      } catch (error) {
        console.error('Error fetching viewer count:', error)
      }
    }
    
    // Get username from stream data
    const getStreamerUsername = () => {
      if (!props.stream || !props.stream.streamer_username) return null
      return props.stream.streamer_username
    }
    
    // Set up viewer count refresh for Stripchat streams
    const setupViewerCountRefresh = () => {
      if (isStripchatStream.value) {
        // Initial fetch
        fetchViewerCount()
        
        // Set up interval for periodic refresh (every 30 seconds)
        viewersRefreshInterval.value = setInterval(fetchViewerCount, 30000)
      }
    }
    
    // Clean up viewer count refresh interval
    const cleanupViewerCountRefresh = () => {
      if (viewersRefreshInterval.value) {
        clearInterval(viewersRefreshInterval.value)
        viewersRefreshInterval.value = null
      }
    }

    watch(() => props.stream.assignments, () => {
      if (!allAgentsFetched.value) {
        fetchAllAgents()
      }
    }, { deep: true })

    const checkStreamStatus = async () => {
      try {
        const response = await axios.get(`/api/detection-status/${props.stream.id}`)
        isDetecting.value = response.data.active
        streamStatus.value = response.data.status || 'unknown'
        isOnline.value = streamStatus.value === 'online'
        isLoading.value = false
        if (isPlaying.value && streamStatus.value !== 'online') {
          await axios.post(`/api/streams/${props.stream.id}/status`, { status: 'online' })
          streamStatus.value = 'online'
          isOnline.value = true
        }
      } catch (error) {
        console.error('Error checking stream status:', error)
        isLoading.value = false
      }
    }

    const toggleDetection = async () => {
      if (!canToggleDetection.value) return
      
      canToggleDetection.value = false
      try {
        if (isDetecting.value) {
          await axios.post('/api/trigger-detection', {
            stream_id: props.stream.id,
            stop: true
          })
          toast.success(`Detection stopped for ${props.stream.streamer_username}`)
        } else {
          await axios.post('/api/trigger-detection', {
            stream_id: props.stream.id
          })
          toast.success(`Detection started for ${props.stream.streamer_username}`)
        }
        isDetecting.value = !isDetecting.value
      } catch (error) {
        console.error('Detection toggle failed:', error)
        toast.error(`Failed to toggle detection: ${error.response?.data?.error || error.message}`)
      } finally {
        canToggleDetection.value = true
      }
    }

    const getDetectionButtonText = () => {
      if (!canToggleDetection.value) return 'Loading...'
      return isDetecting.value ? 'Stop' : 'Monitor'
    }

    const getStreamTime = () => {
      if (!props.stream.creation_time) return 'New'
      
      const createdAt = new Date(props.stream.creation_time)
      const now = new Date()
      const diffMs = now - createdAt
      const diffMins = Math.floor(diffMs / 60000)
      
      if (diffMins < 60) return `${diffMins}m`
      const hours = Math.floor(diffMins / 60)
      const mins = diffMins % 60
      return `${hours}h ${mins}m`
    }

    const addHoverAnimation = () => {
      if (streamCard.value) {
        anime({
          targets: streamCard.value,
          scale: 1.03,
          boxShadow: '0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22)',
          duration: 300,
          easing: 'easeOutQuad'
        })
      }
    }

    const removeHoverAnimation = () => {
      if (streamCard.value) {
        anime({
          targets: streamCard.value,
          scale: 1,
          boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
          duration: 300,
          easing: 'easeOutQuad'
        })
      }
    }

    const handleCardClick = () => {
      if (!isOnline.value) {
        const userConfirmed = confirm('Stream is offline. Do you want to view details or refresh the stream?')
        if (userConfirmed) {
          showToast('Opening stream details or refreshing...', 'info')
          emit('click')
        }
      } else {
        emit('click')
      }
    }

    const initializeVideo = () => {
      const m3u8Url = getStreamUrl()
      if (!m3u8Url) {
        console.error('No HLS URL available for this stream')
        isOnline.value = false
        streamStatus.value = 'offline'
        isLoading.value = false
        return
      }

      if (Hls.isSupported() && videoPlayer.value) {
        hls = new Hls({
          startLevel: 0,
          capLevelToPlayerSize: true,
          maxBufferLength: 30
        })
        hls.loadSource(m3u8Url)
        hls.attachMedia(videoPlayer.value)
        
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          videoPlayer.value.muted = true
          videoPlayer.value.play().catch(e => {
            console.warn('Autoplay prevented:', e)
          })
          isOnline.value = true
          streamStatus.value = 'online'
          isLoading.value = false
          axios.post(`/api/streams/${props.stream.id}/status`, { status: 'online' })
            .then(() => console.log(`Updated stream ${props.stream.id} status to online`))
            .catch(error => console.error('Failed to update stream status:', error))
        })
        
        hls.on(Hls.Events.ERROR, (event, data) => {
          if (data.fatal) {
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                console.error('HLS network error:', data)
                isOnline.value = false
                streamStatus.value = 'offline'
                isLoading.value = false
                hls.stopLoad()
                hls.detachMedia()
                reportStreamOffline(props.stream.id)
                break
              case Hls.ErrorTypes.MEDIA_ERROR:
                console.error('HLS media error:', data)
                hls.recoverMediaError()
                break
              default:
                console.error('Unrecoverable HLS error:', data)
                hls.destroy()
                isOnline.value = false
                streamStatus.value = 'offline'
                isLoading.value = false
                reportStreamOffline(props.stream.id)
                break
            }
          }
        })
      } else if (videoPlayer.value && videoPlayer.value.canPlayType('application/vnd.apple.mpegurl')) {
        videoPlayer.value.src = m3u8Url
        videoPlayer.value.addEventListener('loadedmetadata', () => {
          videoPlayer.value.muted = true
          videoPlayer.value.play().catch(e => {
            console.warn('Autoplay prevented:', e)
          })
          isOnline.value = true
          streamStatus.value = 'online'
          isLoading.value = false
          axios.post(`/api/streams/${props.stream.id}/status`, { status: 'online' })
            .then(() => console.log(`Updated stream ${props.stream.id} status to online`))
            .catch(error => console.error('Failed to update stream status:', error))
        })
        videoPlayer.value.addEventListener('error', () => {
          isOnline.value = false
          streamStatus.value = 'offline'
          isLoading.value = false
          axios.post(`/api/streams/${props.stream.id}/status`, { status: 'offline' })
            .then(() => console.log(`Updated stream ${props.stream.id} status to offline`))
            .catch(error => console.error('Failed to update stream status:', error))
        })
      }
    }

    const getStreamUrl = () => {
      if (props.stream.platform?.toLowerCase() === 'chaturbate') {
        return props.stream.chaturbate_m3u8_url
      }
      if (props.stream.platform?.toLowerCase() === 'stripchat') {
        return props.stream.stripchat_m3u8_url
      }
      return props.stream.room_url
    }

    const handleVideoPlayback = () => {
      const videoElement = videoPlayer.value
      if (videoElement) {
        videoElement.onplay = () => {
          isPlaying.value = true
          isOnline.value = true
          streamStatus.value = 'online'
          axios.post(`/api/streams/${props.stream.id}/status`, { status: 'online' })
            .then(() => console.log(`Updated stream ${props.stream.id} status to online`))
            .catch(error => console.error('Failed to update stream status:', error))
        }
        videoElement.onpause = () => {
          isPlaying.value = false
        }
        videoElement.onended = () => {
          isPlaying.value = false
        }
        videoElement.onerror = () => {
          isOnline.value = false
          streamStatus.value = 'offline'
          isLoading.value = false
          axios.post(`/api/streams/${props.stream.id}/status`, { status: 'offline' })
            .then(() => console.log(`Updated stream ${props.stream.id} status to offline`))
            .catch(error => console.error('Failed to update stream status:', error))
        }
      }
    }

    const reportStreamOffline = async (streamId) => {
      try {
        await axios.post(`/api/streams/${streamId}/status`, { status: 'offline' })
        streamStatus.value = 'offline'
        isOnline.value = false
        console.log(`Reported stream ${streamId} as offline`)
      } catch (error) {
        console.error('Failed to report stream offline:', error)
      }
    }

    const checkDetectionStatus = async () => {
      if (!isOnline.value) return
      try {
        const response = await axios.get(`/api/detection-status/${props.stream.id}`)
        isDetecting.value = response.data.active
        isOnline.value = response.data.status === 'online'
      } catch (error) {
        console.error('Detection status check failed:', error)
        isOnline.value = false
      }
    }

    const startDetectionInterval = () => {
      if (isOnline.value && !detectionInterval) {
        detectionInterval = setInterval(checkDetectionStatus, 10000)
      }
    }

    const stopDetectionInterval = () => {
      if (detectionInterval) {
        clearInterval(detectionInterval)
        detectionInterval = null
      }
    }

    watch(isOnline, (newVal) => {
      if (newVal) {
        startDetectionInterval()
      } else {
        stopDetectionInterval()
        isDetecting.value = false
      }
    })
    
    // Watch for platform changes and set up viewer count refresh accordingly
    watch(() => props.stream.platform, (newPlatform) => {
      // Clean up existing interval if any
      cleanupViewerCountRefresh()
      
      // Reset viewers count when platform changes
      viewers.value = 0
      
      if (newPlatform?.toLowerCase() === 'stripchat') {
        setupViewerCountRefresh()
      }
    })

    onMounted(async () => {
      initializeVideo()
      handleVideoPlayback()
      checkStreamStatus()
      if (isOnline.value) {
        startDetectionInterval()
      }
      streamStatusCheckInterval.value = setInterval(checkStreamStatus, 120000) // Check every 2 minutes
      // Set up viewer count refresh for Stripchat
      setupViewerCountRefresh()
    })

    onBeforeUnmount(() => {
      stopDetectionInterval()
      if (hls) hls.destroy()
      if (streamStatusCheckInterval.value) {
        clearInterval(streamStatusCheckInterval.value)
      }
      if (viewersRefreshInterval.value) {
        clearInterval(viewersRefreshInterval.value)
      }
    })

    watch(() => props.stream.status, (newStatus) => {
      isOnline.value = newStatus === 'online'
      streamStatus.value = newStatus || 'unknown'
    })

    return {
      streamCard,
      videoPlayer,
      isOnline,
      isDetecting,
      canToggleDetection,
      detectionCount: props.detectionCount,
      hasAssignedAgents,
      assignedAgentNames,
      viewers,
      isStripchatStream,
      toggleDetection,
      getDetectionButtonText,
      getStreamTime,
      handleCardClick,
      addHoverAnimation,
      removeHoverAnimation
    }
  }
}
</script>

<style scoped>
.mobile-stream-card {
  display: flex;
  flex-direction: column;
  background-color: var(--light-card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.2s ease, background-color 0.3s ease, box-shadow 0.3s ease;
  position: relative;
  contain: content; /* Improve rendering performance */
  will-change: transform; /* Hint for better performance on scroll/animations */
  backface-visibility: hidden; /* Prevent flickering on some mobile browsers */
  -webkit-font-smoothing: antialiased; /* Better text rendering on Safari */
}

[data-theme='dark'] .mobile-stream-card {
  background-color: var(--dark-card-bg);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.mobile-stream-card:active {
  transform: scale(0.98);
}

.mobile-stream-card.disabled {
  opacity: 0.6;
  pointer-events: auto; /* Allow clicks but visually indicate disabled state */
  cursor: not-allowed;
}

.video-container {
  position: relative;
  width: 100%;
  height: 200px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

[data-theme='dark'] .video-container {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.stream-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.stream-overlay:hover {
  opacity: 1;
}

.view-details-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
}

.stream-info {
  flex: 1;
  padding: 15px;
}

.info-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.stream-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: var(--light-text);
}

[data-theme='dark'] .stream-title {
  color: var(--dark-text);
}

.platform-tag {
  font-size: 0.7rem;
  padding: 3px 8px;
  border-radius: 12px;
  background-color: var(--light-secondary);
  color: white;
}

[data-theme='dark'] .platform-tag {
  background-color: var(--dark-secondary);
}

.platform-tag.chaturbate {
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.platform-tag.stripchat {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.stream-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-rendering: optimizeSpeed; /* Optimize for performance over aesthetics */
}

.agent-badge {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  transform: translateZ(0); /* Create a new stacking context for better text rendering */
  background-color: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  padding: 3px 10px;
  border-radius: 20px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  gap: 5px;
}

.agent-badge.unassigned {
  background-color: rgba(158, 158, 158, 0.2);
  color: #9e9e9e;
}

.stream-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-rendering: optimizeSpeed; /* Optimize for performance over aesthetics */
}

.stat-item {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  transform: translateZ(0); /* Create a new stacking context for better text rendering */
}

.stat-item .fa-icon {
  width: 16px;
  margin-right: 10px;
  color: var(--text-muted, #6c757d);
  flex-shrink: 0; /* Prevent icon from shrinking */
}

.alert-stat.has-alerts {
  color: #f44336;
  font-weight: 500;
  opacity: 1;
}

.monitor-stat {
  color: #28a745;
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
}

.detection-btn {
  background: none;
  border: none;
  padding: 8px 16px;
  border-radius: 12px;
  background-color: var(--primary-color);
  color: white;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

[data-theme='dark'] .detection-btn {
  background-color: var(--dark-primary);
}

.detection-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.detection-toggle {
  background: none;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted, #6c757d);
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease; /* Specific transitions for better performance */
  will-change: transform, color; /* Hint for browser to optimize these properties */
  transform: translateZ(0); /* Force GPU acceleration */
  -webkit-tap-highlight-color: transparent; /* Remove tap highlight on mobile */
  touch-action: manipulation; /* Optimize for touch */
  background-color: rgba(40, 167, 69, 0.85); /* Green for idle state */
}

[data-theme='dark'] .detection-toggle {
  color: var(--dark-text-secondary);
}

.detection-toggle:active {
  background-color: rgba(0, 0, 0, 0.1);
  transform: scale(0.95); /* Slight scale down effect on press */
}

[data-theme='dark'] .detection-toggle:active {
  background-color: rgba(255, 255, 255, 0.1);
}

.detection-toggle.active {
  background-color: rgba(255, 193, 7, 0.85); /* Yellow for running state */
}

[data-theme='dark'] .detection-toggle.active {
  background-color: var(--dark-success);
}

.detection-toggle.loading {
  background-color: rgba(255, 193, 7, 0.85); /* Yellow for loading state */
  pointer-events: none;
}

[data-theme='dark'] .detection-toggle.loading {
  background-color: var(--dark-danger);
}

.detection-toggle:hover:not(:disabled) {
  background-color: rgba(40, 167, 69, 1); /* Darker green on hover for idle state */
  transform: translateY(-2px);
}

.detection-toggle.active:hover:not(:disabled) {
  background-color: rgba(220, 53, 69, 0.85); /* Red on hover for stop state */
  transform: translateY(-2px);
}

.detection-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.detection-toggle .detection-icon {
  font-size: 1.2rem;
}

.detection-toggle.active .detection-icon {
  color: var(--light-success);
}

[data-theme='dark'] .detection-toggle.active .detection-icon {
  color: var(--dark-success);
}

.detection-toggle.loading .detection-icon {
  color: var(--light-danger);
}

[data-theme='dark'] .detection-toggle.loading .detection-icon {
  color: var(--dark-danger);
}

.detecting-indicator {
  font-size: 0.8rem;
  color: var(--text-muted, #6c757d);
}

[data-theme='dark'] .detecting-indicator {
  color: var(--dark-text-secondary);
}

.detection-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: var(--light-danger);
  color: white;
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 12px;
}

[data-theme='dark'] .detection-badge {
  background-color: var(--dark-danger);
}

.offline-watermark {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 10px 20px;
  border-radius: 5px;
  font-size: 1.2rem;
  font-weight: bold;
  z-index: 5;
}

[data-theme='light'] .offline-watermark {
  background-color: rgba(255, 255, 255, 0.7);
  color: black;
}

/* Add viewer count overlay styles */
.viewer-count-overlay {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 10;
}

.viewer-count {
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  border-radius: 20px;
  padding: 4px 10px;
  font-size: 0.85rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(2px);
  transition: all 0.2s ease;
}

.viewer-count:hover {
  background-color: rgba(0, 0, 0, 0.85);
}
</style>