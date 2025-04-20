<template>
  <div 
    class="stream-card" 
    :class="{ 'compact-view': isCompactView }"
    @click="$emit('click', $event)" 
    @mouseenter="addHoverAnimation" 
    @mouseleave="removeHoverAnimation" 
    ref="streamCard"
  >
    <div class="video-container">
      <video ref="videoPlayer" class="video-player"></video>
      <DetectionBadge v-if="detectionCount > 0" :count="detectionCount" />
      
      <!-- Add viewer count overlay for Stripchat -->
      <div v-if="stream.platform?.toLowerCase() === 'stripchat'" class="viewer-count-overlay">
        <span class="viewer-count">
          <font-awesome-icon icon="eye" />
          {{ viewers }}
        </span>
      </div>
      
      <div class="stream-overlay" ref="streamOverlay">
        <button class="view-details-btn">
          <font-awesome-icon icon="eye" />
          <span class="btn-text">View Details</span>
        </button>
      </div>
      
      <!-- Add detection toggle button -->
      <div class="detection-controls">
        <button 
          class="detection-toggle" 
          :class="{ 'active': isDetectionActive, 'loading': isDetectionLoading }"
          @click.stop="toggleDetection"
          :title="isDetectionActive ? 'Stop monitoring' : 'Start monitoring'"
        >
          <span class="detection-icon">
            <font-awesome-icon v-if="isDetectionLoading" icon="spinner" spin />
            <font-awesome-icon v-else :icon="isDetectionActive ? 'stop-circle' : 'play-circle'" />
          </span>
          <span class="detection-label">{{ getDetectionButtonText() }}</span>
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
      <div class="stream-stats" ref="streamStats">
        <div class="stat-item">
          <font-awesome-icon icon="clock" />
          <span>{{ getStreamTime() }}</span>
        </div>
        <div class="stat-item alert-stat" :class="{'has-alerts': detectionCount > 0}">
          <font-awesome-icon icon="bell" />
          <span>{{ detectionCount }} {{ detectionCount === 1 ? 'alert' : 'alerts' }}</span>
        </div>
        <!-- Add detection status display -->
        <div v-if="isDetectionActive" class="stat-item monitor-stat">
          <font-awesome-icon icon="eye" />
          <span>Monitoring</span>
        </div>
      </div>
    </div>
    <div class="quick-actions">
      <button class="action-btn assign-btn" @click.stop="$emit('assign')" v-if="!stream.agent?.username">
        <font-awesome-icon icon="user-plus" />
      </button>
    </div>
  </div>
</template>

<script>
import Hls from 'hls.js'
import anime from 'animejs/lib/anime.es.js'
import DetectionBadge from './DetectionBadge.vue'
import { ref, computed, onMounted, onBeforeUnmount, watch, inject } from 'vue'
import axios from 'axios'

export default {
  name: 'StreamCard',
  components: {
    DetectionBadge
  },
  props: {
    stream: Object,
    detectionCount: Number,
    index: {
      type: Number,
      default: 0
    },
    totalStreams: {
      type: Number,
      default: 1
    }
  },
  emits: ['click', 'assign', 'bookmark', 'mute-change', 'fullscreen', 'detection-toggled'],
  setup(props, { emit }) {
    const streamCard = ref(null)
    const videoPlayer = ref(null)
    const streamOverlay = ref(null)
    const streamStats = ref(null)
    let hls = null
    
    const isMuted = ref(true)
    const isBookmarked = ref(false)
    const isFullscreen = ref(false)
    
    // Detection state variables
    const isDetectionActive = ref(false)
    const isDetectionLoading = ref(false)
    const detectionError = ref(null)
    const checkStatusInterval = ref(null)
    
    // Viewer count for Stripchat streams
    const viewers = ref(0)
    const viewersRefreshInterval = ref(null)
    
    // Get the global store or event bus if available
    const eventBus = inject('eventBus', null)
    
    // Get the theme from parent component (App.vue)
    const isDarkTheme = inject('theme', ref(true))
    
    // Computed property to determine if compact view should be used
    const isCompactView = computed(() => {
      return props.totalStreams > 8
    })

    // Computed property to get the stream URL (m3u8)
    const streamUrl = computed(() => {
      if (!props.stream) return null
      
      // Get the m3u8 URL based on platform
      if (props.stream.platform?.toLowerCase() === 'chaturbate' && props.stream.chaturbate_m3u8_url) {
        return props.stream.chaturbate_m3u8_url
      } else if (props.stream.platform?.toLowerCase() === 'stripchat' && props.stream.stripchat_m3u8_url) {
        return props.stream.stripchat_m3u8_url
      }
      
      // Fallback to room URL
      return props.stream.room_url
    })

    // Get username from stream data
    const getStreamerUsername = () => {
      if (!props.stream || !props.stream.streamer_username) return null
      return props.stream.streamer_username
    }

    // Fetch viewer count for Stripchat streams
    const fetchViewerCount = async () => {
      const username = getStreamerUsername()
      if (!username || props.stream.platform?.toLowerCase() !== 'stripchat') return
      
      try {
        const response = await axios.get(`https://stripchat.com/api/front/v2/models/username/${username}/members`)
        
        // Extract viewer count from response
        if (response.data && response.data.guests !== undefined) {
          viewers.value = response.data.guests
          
          // If we also want to include other viewer types
          const totalViewers = (response.data.guests || 0) + 
                              (response.data.members?.length || 0) + 
                              (response.data.spies || 0)
          
          // Choose which viewer count to display
          viewers.value = totalViewers
          
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

    const initializeVideo = () => {
      // Get the correct m3u8 URL directly from the stream object
      let m3u8Url = streamUrl.value
      
      if (!m3u8Url) {
        console.error('No HLS URL available for this stream')
        return
      }
      
      // Initialize HLS.js if supported
      if (Hls.isSupported() && videoPlayer.value) {
        destroyHls() // Clean up any existing instance
        
        hls = new Hls({
          startLevel: 0,
          capLevelToPlayerSize: true,
          maxBufferLength: 30
        })
        
        hls.loadSource(m3u8Url)
        hls.attachMedia(videoPlayer.value)
        
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          videoPlayer.value.muted = isMuted.value
          videoPlayer.value.play().catch(e => {
            console.warn('Autoplay prevented:', e)
          })
        })
        
        hls.on(Hls.Events.ERROR, (event, data) => {
          console.error('HLS error:', data)
          if (data.fatal) {
            switch(data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                hls.startLoad()
                break
              case Hls.ErrorTypes.MEDIA_ERROR:
                hls.recoverMediaError()
                break
              default:
                destroyHls()
                break
            }
          }
        })
      } 
      // Fallback for browsers with native HLS support
      else if (videoPlayer.value && videoPlayer.value.canPlayType('application/vnd.apple.mpegurl')) {
        videoPlayer.value.src = m3u8Url
        videoPlayer.value.addEventListener('loadedmetadata', () => {
          videoPlayer.value.muted = isMuted.value
          videoPlayer.value.play().catch(e => {
            console.warn('Autoplay prevented:', e)
          })
        })
      }
    }

    const destroyHls = () => {
      if (hls) {
        hls.destroy()
        hls = null
      }
    }

    // Detection toggle and status functions
    const toggleDetection = async (event) => {
      // Prevent click from propagating to parent
      if (event) event.stopPropagation()
      
      if (!streamUrl.value) {
        console.error('No stream URL available')
        return
      }
      
      isDetectionLoading.value = true
      
      try {
        const response = await axios.post('/api/trigger-detection', {
          stream_url: streamUrl.value,
          stop: isDetectionActive.value
        })
        
        // Use the response data to set the state
        if (response.data.message.includes('started')) {
          isDetectionActive.value = true
        } else if (response.data.message.includes('stopped')) {
          isDetectionActive.value = false
        } else {
          // Just toggle the state as a fallback
          isDetectionActive.value = !isDetectionActive.value
        }
        
        // Emit event to notify parent component
        emit('detection-toggled', {
          stream: props.stream,
          active: isDetectionActive.value
        })
        
        // Add animation for feedback
        anime({
          targets: '.detection-toggle',
          scale: [1, 1.2, 1],
          duration: 400,
          easing: 'easeOutQuad'
        })
        
      } catch (error) {
        console.error('Error toggling detection:', error)
        detectionError.value = error.response?.data?.error || 'Failed to toggle detection'
      } finally {
        isDetectionLoading.value = false
      }
    }
    
    const checkDetectionStatus = async () => {
      if (!streamUrl.value) return
      
      try {
        const response = await axios.get(`/api/detection-status?stream_url=${encodeURIComponent(streamUrl.value)}`)
        isDetectionActive.value = response.data.active === true
      } catch (error) {
        console.error('Error checking detection status:', error)
      }
    }
    
    const getDetectionButtonText = () => {
      if (isDetectionLoading.value) return 'Loading...'
      return isDetectionActive.value ? 'Stop' : 'Monitor'
    }

    const addEntranceAnimation = () => {
      if (streamCard.value) {
        anime({
          targets: streamCard.value,
          translateY: [60, 0],
          opacity: [0, 1],
          scale: [0.85, 1],
          easing: 'spring(1, 80, 10, 0)',
          duration: 800,
          delay: 100 + (props.index * 120) // Staggered effect
        })
      }

      if (streamStats.value) {
        anime({
          targets: streamStats.value.querySelectorAll('.stat-item'),
          translateY: [20, 0],
          opacity: [0, 1],
          delay: anime.stagger(100, {start: 600 + (props.index * 120)}),
          easing: 'easeOutQuad',
          duration: 500
        })
      }
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

      if (streamOverlay.value) {
        anime({
          targets: streamOverlay.value,
          opacity: [0, 1],
          duration: 250,
          easing: 'easeOutQuad'
        })

        anime({
          targets: streamOverlay.value.querySelector('.view-details-btn'),
          translateY: [20, 0],
          scale: [0.9, 1],
          opacity: [0, 1],
          duration: 350,
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

      if (streamOverlay.value) {
        anime({
          targets: streamOverlay.value,
          opacity: 0,
          duration: 200,
          easing: 'easeOutQuad'
        })
      }
    }

    const getStreamTime = () => {
      // Calculate how long the stream has been active based on creation_time
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

    const toggleMute = () => {
      if (videoPlayer.value) {
        isMuted.value = !isMuted.value
        videoPlayer.value.muted = isMuted.value
        emit('mute-change', isMuted.value)
        
        // Provide haptic feedback through animation
        anime({
          targets: '.mute-btn',
          scale: [1, 1.2, 1],
          duration: 300,
          easing: 'easeOutQuad'
        })
      }
    }

    const toggleBookmark = () => {
      isBookmarked.value = !isBookmarked.value
      emit('bookmark', { stream: props.stream, bookmarked: isBookmarked.value })
      
      // Animate bookmark button
      anime({
        targets: '.bookmark-btn',
        scale: [1, 1.2, 1],
        rotate: ['0deg', '20deg', '0deg'],
        duration: 400,
        easing: 'easeOutQuad'
      })
    }

    const toggleFullscreen = () => {
      emit('fullscreen', props.stream)
      isFullscreen.value = !isFullscreen.value
    }

    // Watch for changes in totalStreams to adjust the layout
    watch(() => props.totalStreams, (newCount) => {
      if (newCount > 8 && !isCompactView.value) {
        // Animate transition to compact view
        anime({
          targets: streamCard.value,
          scale: [1, 0.95, 1],
          duration: 400,
          easing: 'easeOutQuad'
        })
      } else if (newCount <= 8 && isCompactView.value) {
        // Animate transition to standard view
        anime({
          targets: streamCard.value,
          scale: [0.95, 1.05, 1],
          duration: 400,
          easing: 'easeOutQuad'
        })
      }
    })

    // Set up viewer count refresh for Stripchat streams
    const setupViewerCountRefresh = () => {
      if (props.stream.platform?.toLowerCase() === 'stripchat') {
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

    // Listen for global events
    onMounted(() => {
      initializeVideo()
      addEntranceAnimation()
      
      // Check detection status initially
      checkDetectionStatus()
      
      // Set up interval to check detection status
      checkStatusInterval.value = setInterval(checkDetectionStatus, 30000)
      
      // Set up viewer count refresh for Stripchat
      setupViewerCountRefresh()
      
      // Listen for global mute all event if event bus exists
      if (eventBus) {
        eventBus.$on('muteAllStreams', (exceptId) => {
          if (props.stream.id !== exceptId) {
            isMuted.value = true
            if (videoPlayer.value) videoPlayer.value.muted = true
          }
        })
      }
    })

    onBeforeUnmount(() => {
      destroyHls()
      
      // Clear detection status interval
      if (checkStatusInterval.value) {
        clearInterval(checkStatusInterval.value)
      }
      
      // Clear viewer count refresh interval
      cleanupViewerCountRefresh()
      
      // Clean up event listeners
      if (eventBus) {
        eventBus.$off('muteAllStreams')
      }
    })

    // Watch for platform changes and set up viewer count refresh accordingly
    watch(() => props.stream.platform, (newPlatform) => {
      // Clean up existing interval if any
      cleanupViewerCountRefresh()
      
      if (newPlatform?.toLowerCase() === 'stripchat') {
        setupViewerCountRefresh()
      }
    })

    return {
      streamCard,
      videoPlayer,
      streamOverlay,
      streamStats,
      isMuted,
      isBookmarked,
      isCompactView,
      isDarkTheme,
      isDetectionActive,
      isDetectionLoading,
      viewers,  // Export viewers count
      addHoverAnimation,
      removeHoverAnimation,
      getStreamTime,
      toggleMute,
      toggleBookmark,
      toggleFullscreen,
      toggleDetection,
      getDetectionButtonText
    }
  }
}
</script>

<style scoped>
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

.compact-view .viewer-count {
  padding: 3px 8px;
  font-size: 0.75rem;
}

/* Detection controls */
.detection-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}

.detection-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: rgba(5, 0, 0, 0.7);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 6px 12px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.detection-toggle:hover {
  background-color: rgba(0, 0, 0, 0.85);
  transform: translateY(-2px);
}

.detection-toggle.active {
  background-color: rgba(220, 53, 69, 0.85);
}

.detection-toggle.active:hover {
  background-color: rgba(220, 53, 69, 1);
}

.detection-toggle.loading {
  background-color: rgba(255, 193, 7, 0.85);
  pointer-events: none;
}

/* Monitor stat for active detection */
.monitor-stat {
  color: #28a745;
  font-weight: 500;
}

/* Compact view adjustments */
.compact-view .detection-toggle {
  padding: 4px 8px;
  font-size: 0.7rem;
}

.compact-view .detection-label {
  display: none;
}

/* Add these to your existing styles for the rest of the component */
.stream-card {
  background-color: var(--input-bg);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--input-border);
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
  height: 100%;
  display: flex;
  flex-direction: column;
  will-change: transform, box-shadow;
  position: relative;
}


/* Compact view styling */
.stream-card.compact-view {
  border-radius: 12px;
}

.compact-view .stream-title {
  font-size: 1rem;
}

.compact-view .stream-meta {
  margin-bottom: 8px;
}

.compact-view .stream-stats {
  padding-top: 8px;
}

.compact-view .stat-item {
  font-size: 0.7rem;
}

.compact-view .agent-badge {
  font-size: 0.7rem;
}

.compact-view .platform-tag {
  font-size: 0.65rem;
  padding: 2px 6px;
}

.compact-view .view-details-btn .btn-text {
  display: none;
}

.video-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  overflow: hidden;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background-color: #000;
}

.stream-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  pointer-events: none;
  z-index: 2;
}

.view-details-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 30px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  transform: translateY(20px);
  opacity: 0;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.view-details-btn:hover {
  background-color: var(--primary-hover);
  transform: translateY(0) scale(1.05);
}

.stream-controls {
  position: absolute;
  bottom: 10px;
  right: 10px;
  display: flex;
  gap: 8px;
  z-index: 3;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.video-container:hover .stream-controls {
  opacity: 1;
}

.control-btn {
  background-color: rgba(var(--primary-color-rgb), 0.8);
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.control-btn:hover {
  background-color: var(--primary-hover);
  transform: scale(1.1);
  box-shadow: var(--shadow-md);
}

.stream-info {
  padding: 10px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.info-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.stream-title {
  margin: 0;
  font-size: 1.2rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
  max-width: 70%;
}

.stream-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.platform-tag {
  padding: 1px 7px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  white-space: nowrap;
}

.platform-tag.chaturbate {
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.platform-tag.stripchat {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.agent-badge {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  background-color: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  display: flex;
  align-items: center;
  gap: 5px;
}

.agent-badge.unassigned {
  background-color: rgba(158, 158, 158, 0.2);
  color: #9e9e9e;
}

.stream-stats {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid var(--input-border);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: var(--text-color);
  opacity: 0.7;
}

.alert-stat.has-alerts {
  color: #f44336;
  font-weight: 500;
  opacity: 1;
}

.quick-actions {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 8px;
  z-index: 3;
}

.action-btn {
  background-color: rgba(var(--primary-color-rgb), 0.8);
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.action-btn:hover {
  background-color: var(--primary-hover);
  transform: scale(1.1);
  box-shadow: var(--shadow-md);
}

.bookmark-btn {
  color: #ffeb3b;
}

.assign-btn {
  color: white;
}

/* Responsive styles */
@media (max-width: 1400px) {
  .stream-card:not(.compact-view) {
    border-radius: 14px;
  }
  
  .stream-card:not(.compact-view) .stream-title {
    font-size: 1.1rem;
  }
}

@media (max-width: 1200px) {
  .stream-card:not(.compact-view) {
    border-radius: 12px;
  }
  
  .stream-card:not(.compact-view) .stream-title {
    font-size: 1rem;
  }
  
  .stream-card:not(.compact-view) .stat-item {
    font-size: 0.8rem;
  }
}

@media (max-width: 768px) {
  .stream-card {
    border-radius: 10px;
  }
  
  .stream-title {
    font-size: 0.9rem;
  }
  
  .stream-meta {
    margin-bottom: 12px;
  }
  
  .stream-stats {
    padding-top: 12px;
  }
  
  
  .stat-item {
    font-size: 0.75rem;
  }
  
  .control-btn,
  .action-btn {
    width: 28px;
    height: 28px;
  }
  
  .platform-tag,
  .agent-badge {
    font-size: 0.7rem;
    padding: 2px 8px;
  }
  
  .view-details-btn {
    padding: 8px 16px;
    font-size: 0.9rem;
  }
  
  .view-details-btn .btn-text {
    display: none;
  }
}

/* Animation classes */
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.pulse-animation {
  animation: pulse 1s infinite;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.fade-in {
  animation: fadeIn 0.3s forwards;
}
</style>