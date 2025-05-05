<template>
  <div
    :class="[
      'mobile-stream-card',
      { 'online': isOnline },
      { 'offline': !isOnline },
      { 'detecting': isDetecting }
    ]"
    @click="handleCardClick"
  >
    <div class="video-container">
      <video ref="videoPlayer" class="video-player"></video>
      <div v-if="detectionCount > 0" class="detection-badge">
        <span>{{ detectionCount }}</span>
      </div>
      <div class="stream-overlay">
        <button class="view-details-btn">
          <font-awesome-icon icon="eye" />
        </button>
      </div>
      <div class="detection-controls">
        <button
          class="detection-toggle"
          :class="{ 'active': isDetecting, 'loading': !canToggleDetection }"
          @click.stop="toggleDetection"
          :title="isDetecting ? 'Stop monitoring' : 'Start monitoring'"
        >
          <span class="detection-icon">
            <font-awesome-icon v-if="!canToggleDetection" icon="spinner" spin />
            <font-awesome-icon v-else :icon="isDetecting ? 'stop-circle' : 'play-circle'" />
          </span>
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
        <div class="agent-badge" :class="{'unassigned': !stream.agent?.username}">
          <font-awesome-icon :icon="stream.agent?.username ? 'user-check' : 'user-clock'" />
          <span>{{ stream.agent?.username || 'Unassigned' }}</span>
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
import MobileVideoPlayer from './MobileVideoPlayer.vue'
import axios from 'axios'

export default {
  name: 'MobileStreamCard',
  
  components: {
    MobileVideoPlayer
  },
  
  props: {
    stream: {
      type: Object,
      required: true
    },
    isRefreshing: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['click', 'refresh', 'detectionToggled'],
  
  setup(props, { emit }) {
    // Determine platform/type for styling
    const streamType = computed(() => {
      const type = (props.stream.type || props.stream.platform || '').toLowerCase()
      return type.charAt(0).toUpperCase() + type.slice(1)
    })
    
    const platformClass = computed(() => {
      const type = (props.stream.type || props.stream.platform || '').toLowerCase()
      return `platform-${type}`
    })
    
    // Truncate and format room URL for display
    const formatRoomUrl = (url) => {
      if (!url) return 'No URL'
      
      try {
        const urlObj = new URL(url)
        // Return just the domain and pathname, truncated if needed
        const display = `${urlObj.hostname}${urlObj.pathname}`
        return display.length > 30 ? display.substring(0, 30) + '...' : display
      } catch (e) {
        // If not a valid URL, just return truncated
        return url.length > 30 ? url.substring(0, 30) + '...' : url
      }
    }
    
    // Open stream URL in new tab
    const openStreamUrl = (event) => {
      event.preventDefault()
      event.stopPropagation()
      if (props.stream.room_url) {
        window.open(props.stream.room_url, '_blank')
      }
    }
    
    // Format assignments text
    const assignmentsText = computed(() => {
      const count = (props.stream.assignments || []).length
      return count === 1 ? '1 agent assigned' : `${count} agents assigned`
    })
    
    // Stream status
    const isOnline = ref(false)
    const isLoading = ref(true)
    const isDetecting = ref(false)
    const canToggleDetection = ref(true)
    const checkStatusInterval = ref(null)
    const streamStatus = ref('unknown')

    const showToast = (message, type = 'success') => {
      // This is a placeholder. Replace with your actual toast notification system if available.
      console.log(`[Toast ${type}]: ${message}`)
      alert(`[${type.toUpperCase()}]: ${message}`)
    }

    const checkStreamStatus = async () => {
      try {
        const response = await axios.get(`/api/detection-status/${props.stream.id}`)
        isDetecting.value = response.data.active
        streamStatus.value = response.data.status || 'unknown'
        // Update online status based on stream status
        isOnline.value = streamStatus.value === 'online'
        isLoading.value = false
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
          // Stop detection
          await axios.post('/api/trigger-detection', {
            stream_id: props.stream.id,
            stop: true
          })
          isDetecting.value = false
          streamStatus.value = 'offline'
          isOnline.value = false
          showToast(`Detection stopped for ${props.stream.streamer_username}`, 'info')
        } else {
          // Check if detection is already active before starting
          const statusResponse = await axios.get(`/api/detection-status/${props.stream.id}`)
          if (statusResponse.data.active) {
            isDetecting.value = true
            streamStatus.value = statusResponse.data.status || 'online'
            isOnline.value = streamStatus.value === 'online'
            showToast(`Detection is already active for ${props.stream.streamer_username}`, 'info')
          } else {
            // Start detection using stream_id
            await axios.post('/api/trigger-detection', {
              stream_id: props.stream.id
            })
            isDetecting.value = true
            streamStatus.value = 'online'
            isOnline.value = true
            showToast(`Detection started for ${props.stream.streamer_username}`, 'success')
          }
        }
      } catch (error) {
        console.error('Error toggling detection:', error)
        showToast(`Error toggling detection for ${props.stream.streamer_username}: ${error.message}`, 'error')
      } finally {
        canToggleDetection.value = true
      }
    }

    const getDetectionButtonText = () => {
      if (!canToggleDetection.value) return 'Loading...'
      return isDetecting.value ? 'Stop' : 'Monitor'
    }
    
    // Open stream details modal (for video player)
    const openStreamDetails = () => {
      emit('click');
    }
    
    onMounted(() => {
      checkStreamStatus()
      checkStatusInterval.value = setInterval(checkStreamStatus, 30000)
    })

    onBeforeUnmount(() => {
      if (checkStatusInterval.value) {
        clearInterval(checkStatusInterval.value)
      }
    })
    
    return {
      streamType,
      platformClass,
      formatRoomUrl,
      openStreamUrl,
      openStreamDetails,
      assignmentsText,
      isOnline,
      isLoading,
      isDetecting,
      canToggleDetection,
      checkStreamStatus,
      toggleDetection,
      getDetectionButtonText
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

/* Platform-specific styling */
.platform-chaturbate .platform-tag {
  background-color: #f90;
}

.platform-stripchat .platform-tag {
  background-color: #ff0066;
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
}

.agent-badge .fa-icon {
  width: 16px;
  margin-right: 10px;
  color: var(--light-text-secondary);
  flex-shrink: 0; /* Prevent icon from shrinking */
}

[data-theme='dark'] .agent-badge .fa-icon {
  color: var(--dark-text-secondary);
}

.agent-badge .agent-text {
  color: var(--light-text-secondary);
  white-space: nowrap; /* Prevent text wrapping for better performance */
  overflow: hidden;
  text-overflow: ellipsis; /* Add ellipsis for overflowing text */
  max-width: 100%; /* Limit text width */
}

[data-theme='dark'] .agent-badge .agent-text {
  color: var(--dark-text-secondary);
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
  color: var(--light-text-secondary);
  flex-shrink: 0; /* Prevent icon from shrinking */
}

[data-theme='dark'] .stat-item .fa-icon {
  color: var(--dark-text-secondary);
}

.stat-item .stat-text {
  color: var(--light-text-secondary);
  white-space: nowrap; /* Prevent text wrapping for better performance */
  overflow: hidden;
  text-overflow: ellipsis; /* Add ellipsis for overflowing text */
  max-width: 100%; /* Limit text width */
}

[data-theme='dark'] .stat-item .stat-text {
  color: var(--dark-text-secondary);
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
  background-color: var(--light-primary);
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
  color: var(--light-text-secondary);
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.1s ease; /* Specific transitions for better performance */
  will-change: transform, color; /* Hint for browser to optimize these properties */
  transform: translateZ(0); /* Force GPU acceleration */
  -webkit-tap-highlight-color: transparent; /* Remove tap highlight on mobile */
  touch-action: manipulation; /* Optimize for touch */
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
  background-color: var(--light-success);
}

[data-theme='dark'] .detection-toggle.active {
  background-color: var(--dark-success);
}

.detection-toggle.loading {
  background-color: var(--light-danger);
}

[data-theme='dark'] .detection-toggle.loading {
  background-color: var(--dark-danger);
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
  color: var(--light-text-secondary);
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
</style>