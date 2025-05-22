<template>
  <div :class="[
    'stream-card',
    { 'compact-view': isCompactView },
    { 'dark-theme': isDarkTheme },
    { 'online': isOnline },
    { 'offline': !isOnline },
    { 'detecting': isDetecting },
    { 'disabled': !isOnline }
  ]" @click="handleCardClick" @mouseenter="isOnline && canToggleDetection ? addHoverAnimation() : null"
    @mouseleave="isOnline && canToggleDetection ? removeHoverAnimation() : null" ref="streamCard">
    <div class="video-container">
      <video ref="videoPlayer" class="video-player"></video>
      <DetectionBadge v-if="detectionCount > 0" :count="detectionCount" />

      <div v-if="isStripchatStream" class="viewer-count-overlay">
        <span class="viewer-count">
          <font-awesome-icon icon="eye" />
          {{ viewers }}
        </span>
      </div>

      <div class="stream-overlay" ref="streamOverlay">
        <button class="view-details-btn" :disabled="!isOnline">
          <font-awesome-icon icon="eye" />
          <span class="btn-text">View Details</span>
        </button>
      </div>

      <div v-if="!isOnline" class="offline-watermark">
        <span>OFFLINE</span>
      </div>

      <div class="detection-controls">
        <button class="detection-toggle" :class="{
          'active': isDetecting,
          'loading': isDetectionLoading,
          'error': detectionError
        }" @click.stop="toggleDetection" :title="getDetectionButtonTooltip"
          :disabled="!isOnline || isDetectionLoading">
          <span class="detection-icon">
            <font-awesome-icon v-if="isDetectionLoading" icon="spinner" spin />
            <font-awesome-icon v-else-if="detectionError" icon="exclamation-circle" />
            <font-awesome-icon v-else :icon="isDetecting ? 'stop-circle' : 'play-circle'" />
          </span>
          <span class="detection-label">{{ getDetectionButtonText }}</span>
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
        <div class="agent-badge" :class="{ 'unassigned': !hasAssignedAgents }">
          <font-awesome-icon :icon="hasAssignedAgents ? 'user-check' : 'user-clock'" />
          <span>{{ assignedAgentNames || 'Unassigned' }}</span>
        </div>
      </div>
      <div class="stream-stats" ref="streamStats">
        <div class="stat-item">
          <font-awesome-icon icon="clock" />
          <span>{{ getStreamTime() }}</span>
        </div>
        <div class="stat-item alert-stat" :class="{ 'has-alerts': detectionCount > 0 }">
          <font-awesome-icon icon="bell" />
          <span>{{ detectionCount }} {{ detectionCount === 1 ? 'alert' : 'alerts' }}</span>
        </div>
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
    <div class="quick-actions">
    </div>
  </div>
</template>

<script>
import Hls from 'hls.js'
import anime from 'animejs/lib/anime.es.js'
import DetectionBadge from './DetectionBadge.vue'
import { ref, computed, onMounted, onBeforeUnmount, watch, inject } from 'vue'
import axios from 'axios'
import { io } from 'socket.io-client'

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
  emits: ['click', 'assign', 'bookmark', 'mute-change', 'fullscreen', 'detection-toggled', 'stream-updated'],
  setup(props, { emit }) {
    const streamCard = ref(null)
    const videoPlayer = ref(null)
    const streamOverlay = ref(null)
    const streamStats = ref(null)
    let hls = null
    const toast = inject('toast', null)
    const isMuted = ref(true)
    const isBookmarked = ref(false)
    const isFullscreen = ref(false)
    const isOnline = ref(props.stream.status === 'online' || props.stream.status === 'monitoring')
    const isLoading = ref(true)
    const streamStatus = ref(props.stream.status || 'offline')

    const isDetecting = ref(props.stream.is_monitored)
    const isDetectionLoading = ref(false)
    const detectionError = ref(null)

    const viewers = ref(0)
    const eventBus = inject('eventBus', null)
    const isDarkTheme = inject('theme', ref(true))
    const isPlaying = ref(false)

    const agentCache = ref({})
    const allAgentsFetched = ref(false)
    const socket = io({ autoConnect: false })
    let statusCheckInterval = null

    const isCompactView = computed(() => {
      return props.totalStreams > 5
    })

    const canToggleDetection = computed(() => {
      return isOnline.value && !isDetectionLoading.value
    })

    watch(() => props.stream.status, (newStatus) => {
      isOnline.value = newStatus === 'online' || newStatus === 'monitoring'
      streamStatus.value = newStatus || 'offline'
    })

    watch(() => props.stream.is_monitored, (newMonitored) => {
      isDetecting.value = newMonitored
    })

    const streamUrl = computed(() => {
      if (!props.stream) return null
      if (props.stream.platform?.toLowerCase() === 'chaturbate' && props.stream.chaturbate_m3u8_url) {
        return props.stream.chaturbate_m3u8_url
      } else if (props.stream.platform?.toLowerCase() === 'stripchat' && props.stream.stripchat_m3u8_url) {
        return props.stream.stripchat_m3u8_url
      }
      return props.stream.room_url
    })

    const isStripchatStream = computed(() => {
      return props.stream?.platform?.toLowerCase() === 'stripchat'
    })

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

    const getDetectionButtonText = computed(() => {
      if (isDetectionLoading.value) return 'Loading...'
      if (detectionError.value) return 'Error'
      return isDetecting.value ? 'Stop' : 'Monitor'
    })

    const getDetectionButtonTooltip = computed(() => {
      if (isDetectionLoading.value) return 'Processing detection request...'
      if (detectionError.value) return `Detection error: ${detectionError.value}`
      return isDetecting.value ? 'Stop detection' : 'Start detection'
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

    watch(() => props.stream.assignments, () => {
      if (!allAgentsFetched.value) {
        fetchAllAgents()
      }
    }, { deep: true })

    const initializeVideo = () => {
      let m3u8Url = streamUrl.value
      if (!m3u8Url) {
        console.error('No HLS URL available for this stream')
        isOnline.value = false
        streamStatus.value = 'offline'
        isLoading.value = false
        return
      }

      if (Hls.isSupported() && videoPlayer.value) {
        destroyHls()
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
          isOnline.value = true
          streamStatus.value = 'online'
          isLoading.value = false
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
                break
            }
          }
        })
      } else if (videoPlayer.value && videoPlayer.value.canPlayType('application/vnd.apple.mpegurl')) {
        videoPlayer.value.src = m3u8Url
        videoPlayer.value.addEventListener('loadedmetadata', () => {
          videoPlayer.value.muted = isMuted.value
          videoPlayer.value.play().catch(e => {
            console.warn('Autoplay prevented:', e)
          })
          isOnline.value = true
          streamStatus.value = 'online'
          isLoading.value = false
        })
        videoPlayer.value.addEventListener('error', () => {
          isOnline.value = false
          streamStatus.value = 'offline'
          isLoading.value = false
        })
      }
    }

    const destroyHls = () => {
      if (hls) {
        hls.destroy()
        hls = null
      }
    }

    const checkDetectionStatus = async () => {
      try {
        const response = await axios.get(`/api/detection-status/${props.stream.id}`)
        isDetecting.value = response.data.isDetecting
        isDetectionLoading.value = response.data.isDetectionLoading
        detectionError.value = response.data.detectionError
        streamStatus.value = response.data.status || 'offline'
        isOnline.value = streamStatus.value === 'online' || streamStatus.value === 'monitoring'
      } catch (error) {
        console.error('Error checking detection status:', error)
        detectionError.value = error.response?.data?.error || error.message
      }
    }

    const toggleDetection = async () => {
      if (isDetectionLoading.value) return

      // Check status before toggling to avoid 409 Conflict
      try {
        const statusResponse = await axios.get(`/api/detection-status/${props.stream.id}`)
        if (statusResponse.data.isDetecting === isDetecting.value) {
          // Status matches, proceed with toggle
          isDetectionLoading.value = true
          detectionError.value = null
          try {
            const response = await axios.post('/api/trigger-detection', {
              stream_id: props.stream.id,
              stop: isDetecting.value
            })

            isDetecting.value = response.data.isDetecting
            isDetectionLoading.value = response.data.isDetectionLoading
            detectionError.value = response.data.detectionError

            toast.success(
              isDetecting.value
                ? `Detection started for ${props.stream.streamer_username}`
                : `Detection stopped for ${props.stream.streamer_username}`
            )
            emit('detection-toggled', { streamId: props.stream.id, isDetecting: isDetecting.value })
          } catch (error) {
            console.error('Error toggling detection:', error)
            detectionError.value = error.response?.data?.error || error.message
            toast.error(`Error toggling detection: ${detectionError.value}`)
          } finally {
            isDetectionLoading.value = false
          }
        } else {
          // Status mismatch, update local state
          isDetecting.value = statusResponse.data.isDetecting
          isDetectionLoading.value = statusResponse.data.isDetectionLoading
          detectionError.value = statusResponse.data.detectionError
          toast.info(`Detection state updated for ${props.stream.streamer_username}`)
        }
      } catch (error) {
        console.error('Error checking detection status before toggle:', error)
        detectionError.value = error.response?.data?.error || error.message
        toast.error(`Error checking detection status: ${detectionError.value}`)
      }
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
          delay: 100 + (props.index * 120)
        })
      }
      if (streamStats.value) {
        anime({
          targets: streamStats.value.querySelectorAll('.stat-item'),
          translateY: [20, 0],
          opacity: [0, 1],
          delay: anime.stagger(100, { start: 600 + (props.index * 120) }),
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

    watch(() => props.totalStreams, (newCount) => {
      if (newCount > 8 && !isCompactView.value) {
        anime({
          targets: streamCard.value,
          scale: [1, 0.95, 1],
          duration: 400,
          easing: 'easeOutQuad'
        })
      } else if (newCount <= 8 && isCompactView.value) {
        anime({
          targets: streamCard.value,
          scale: [0.95, 1.05, 1],
          duration: 400,
          easing: 'easeOutQuad'
        })
      }
    })

    const handleVideoPlayback = () => {
      const videoElement = videoPlayer.value
      if (videoElement) {
        videoElement.onplay = () => {
          isPlaying.value = true
          isOnline.value = true
          streamStatus.value = 'online'
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
        }
      }
    }

    const handleStreamUpdate = (data) => {
      if (data.id === props.stream.id || data.room_url === props.stream.room_url) {
        isDetecting.value = data.status === 'monitoring' || data.is_monitored
        isDetectionLoading.value = false
        detectionError.value = null
        streamStatus.value = data.status || 'offline'
        isOnline.value = streamStatus.value === 'online' || streamStatus.value === 'monitoring'
        if (data.viewers !== undefined) {
          viewers.value = data.viewers
          anime({
            targets: '.viewer-count',
            scale: [1, 1.1, 1],
            duration: 300,
            easing: 'easeOutQuad'
          })
        }
        toast.info(`Stream ${props.stream.streamer_username} is now ${streamStatus.value}`)
        emit('stream-updated', {
          streamId: props.stream.id,
          status: streamStatus.value,
          is_monitored: isDetecting.value,
          viewers: data.viewers
        })
      }
    }

    onMounted(() => {
      socket.connect()
      socket.on('connect', () => {
        console.log('Connected to SocketIO server')
      })
      socket.on('notification', (data) => {
        if (data.room_url === props.stream.room_url) {
          handleStreamUpdate(data)
        }
      })
      socket.on('stream-update', handleStreamUpdate)

      initializeVideo()
      addEntranceAnimation()
      fetchAllAgents()
      if (eventBus) {
        eventBus.$on('muteAllStreams', (exceptId) => {
          if (props.stream.id !== exceptId) {
            isMuted.value = true
            if (videoPlayer.value) videoPlayer.value.muted = true
          }
        })
        eventBus.$on('stream-update', handleStreamUpdate)
      }
      handleVideoPlayback()
      // Start periodic status check
      statusCheckInterval = setInterval(checkDetectionStatus, 45000)
      // Initial status check
      checkDetectionStatus()
    })

    onBeforeUnmount(() => {
      socket.off('notification')
      socket.off('stream-update')
      socket.disconnect()
      destroyHls()
      if (eventBus) {
        eventBus.$off('muteAllStreams')
        eventBus.$off('stream-update')
      }
      // Clean up status check interval
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval)
        statusCheckInterval = null
      }
    })

    watch(() => props.stream.platform, () => {
      viewers.value = 0
    })

    const handleCardClick = () => {
      if (!isOnline.value) {
        const userConfirmed = confirm('Stream is offline. Do you want to view details or refresh the stream?')
        if (userConfirmed) {
          toast.warning('Opening stream details or refreshing...', 'info')
          emit('click')
        }
      } else {
        emit('click')
      }
    }

    return {
      streamCard,
      videoPlayer,
      streamOverlay,
      streamStats,
      isMuted,
      isBookmarked,
      isCompactView,
      isDarkTheme,
      isDetecting,
      isDetectionLoading,
      detectionError,
      isOnline,
      viewers,
      isStripchatStream,
      addHoverAnimation,
      removeHoverAnimation,
      getStreamTime,
      toggleMute,
      toggleBookmark,
      toggleFullscreen,
      toggleDetection,
      getDetectionButtonText,
      getDetectionButtonTooltip,
      hasAssignedAgents,
      assignedAgentNames,
      handleCardClick,
      canToggleDetection
    }
  }
}
</script>

<style scoped>
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
  background-color: rgba(40, 167, 69, 0.85);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 6px 12px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.detection-toggle:hover:not(:disabled) {
  background-color: rgb(103, 124, 108);
  transform: translateY(-2px);
}

.detection-toggle.active {
  background-color: rgba(220, 53, 69, 0.85);
}

.detection-toggle.active:hover:not(:disabled) {
  background-color: rgba(200, 33, 49, 0.85);
  transform: translateY(-2px);
}

.detection-toggle.loading {
  background-color: rgba(255, 193, 7, 0.85);
  pointer-events: none;
}

.detection-toggle.error {
  background-color: rgba(220, 53, 69, 0.85);
  animation: shake 0.3s;
}

.detection-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.monitor-stat {
  color: #28a745;
  font-weight: 500;
}

.compact-view .detection-toggle {
  padding: 4px 8px;
  font-size: 0.7rem;
}

.compact-view .detection-label {
  display: none;
}

.stream-card {
  background-color: var(--input-bg);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--input-border);
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  height: 100%;
  display: flex;
  flex-direction: column;
  will-change: transform, box-shadow;
  position: relative;
}

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

@keyframes pulse {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.05);
  }

  100% {
    transform: scale(1);
  }
}

@keyframes shake {
  0% {
    transform: translateX(0);
  }

  25% {
    transform: translateX(-2px);
  }

  50% {
    transform: translateX(2px);
  }

  75% {
    transform: translateX(-2px);
  }

  100% {
    transform: translateX(0);
  }
}

.pulse-animation {
  animation: pulse 1s infinite;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

.fade-in {
  animation: fadeIn 0.3s forwards;
}

.stream-card.disabled {
  opacity: 0.6;
  pointer-events: auto;
  cursor: not-allowed;
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

.list-view .stream-card {
  flex-direction: row;
  height: auto;
  min-height: 60px;
  border-radius: 8px;
}

.list-view .video-container {
  width: 80px;
  min-width: 80px;
  height: 45px;
  margin-right: 0.75rem;
  aspect-ratio: 16/9;
}

.list-view .stream-info {
  flex-grow: 1;
  padding: 0.5rem 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.list-view .info-top-row {
  margin-bottom: 0.25rem;
}

.list-view .stream-title {
  font-size: 0.9rem;
  margin: 0;
  max-width: 100%;
}

.list-view .platform-tag {
  font-size: 0.6rem;
  padding: 1px 4px;
}

.list-view .stream-meta {
  margin-bottom: 0.25rem;
}

.list-view .agent-badge {
  font-size: 0.65rem;
  padding: 2px 6px;
}

.list-view .stream-stats {
  padding-top: 0;
  justify-content: flex-start;
  gap: 0.75rem;
}

.list-view .stat-item {
  font-size: 0.65rem;
  gap: 0.25rem;
}

.list-view .detection-controls {
  top: 50%;
  right: 0.5rem;
  transform: translateY(-50%);
}

.list-view .detection-toggle {
  padding: 3px 8px;
  font-size: 0.7rem;
}

.list-view .detection-label {
  display: none;
}

.list-view .quick-actions {
  top: 50%;
  right: 3rem;
  transform: translateY(-50%);
}

.list-view .action-btn {
  width: 24px;
  height: 24px;
}

.list-view .offline-watermark {
  font-size: 0.8rem;
  padding: 3px 6px;
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

  .list-view .video-container {
    width: 70px;
    min-width: 70px;
    height: 40px;
  }

  .list-view .stream-title {
    font-size: 0.85rem;
  }

  .list-view .detection-controls {
    right: 0.25rem;
  }

  .list-view .quick-actions {
    right: 2.5rem;
  }
}
</style>