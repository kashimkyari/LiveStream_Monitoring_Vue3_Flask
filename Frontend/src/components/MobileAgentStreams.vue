<template>
  <div class="stream-player-container">
    <!-- View Toggle Controls -->
    <div class="view-controls">
      <h2>My Assigned Streams</h2>
      <div class="controls-right">
        <div class="view-toggle">
          <button 
            class="toggle-btn" 
            :class="{ active: viewMode === 'grid' }"
            @click="viewMode = 'grid'"
          >
            <font-awesome-icon icon="th-large" />
          </button>
          <button 
            class="toggle-btn" 
            :class="{ active: viewMode === 'list' }"
            @click="viewMode = 'list'"
          >
            <font-awesome-icon icon="list" />
          </button>
        </div>
        <div class="refresh-button" @click="loadAssignments">
          <font-awesome-icon icon="sync" :class="{ 'fa-spin': isLoadingAssignments }" />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoadingAssignments" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading your streams...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="assignments.length === 0" class="empty-state">
      <font-awesome-icon icon="video-slash" size="2x" />
      <p>You don't have any assigned streams.</p>
      <button class="refresh-btn" @click="loadAssignments">
        Refresh
      </button>
    </div>

    <!-- Grid View -->
   <div v-else-if="viewMode === 'grid'" class="stream-grid">
      <div 
        v-for="stream in assignments" 
        :key="stream.id" 
        class="stream-grid-item"
        @click="selectStream(stream)"
      >
        <div class="video-thumbnail" :class="{ 'selected': selectedStream?.id === stream.id }">
          <div class="player-overlay">
            <font-awesome-icon icon="play" size="2x" />
          </div>
          <div v-if="stream.stream_status === 'online'" class="mini-player">
            <video 
              class="mini-video-player" 
              :id="`mini-player-${stream.id}`"
              muted
              autoplay
              playsinline
            ></video>
          </div>
          <div v-else-if="stream.stream_status === 'checking'" class="offline-placeholder checking">
            <span class="checking-text">CHECKING...</span>
            <div class="loading-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
          <div v-else class="offline-placeholder">
            <span class="offline-text">OFFLINE</span>
          </div>
          <div class="stream-badges">
            <div class="live-badge" v-if="stream.stream_status === 'online'">
              <span class="live-dot"></span>LIVE
            </div>
            <div class="detection-badge" v-if="stream.detection_status">
              {{ stream.detection_status }}
            </div>
          </div>
          <div class="stream-duration">
            {{ formatStreamTime(stream.stream_start_time) }}
          </div>
        </div>
        <div class="stream-info">
          <div class="stream-title-row">
            <h3 class="stream-title">{{ stream.streamer_username }}</h3>
            <div class="stream-platform" :class="stream.platform.toLowerCase()">
              {{ stream.platform }}
            </div>
          </div>
          <div class="stream-details">
            <span class="stream-viewers">
              <font-awesome-icon icon="eye" /> 
              {{ formatNumber(stream.viewer_count || 0) }}
            </span>
          </div>
          <div class="stream-controls">
            <button 
              class="control-btn detection-btn" 
              :class="{ 'active': stream.detection_active }"
              @click.stop="toggleDetection(stream)"
            >
              <font-awesome-icon :icon="stream.detection_active ? 'stop' : 'play'" />
              {{ stream.detection_active ? 'Stop Detection' : 'Start Detection' }}
            </button>
            <button class="control-btn refresh-btn" @click.stop="refreshStreamUrl(stream)">
              <font-awesome-icon icon="sync" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- List View -->
    <div v-else class="stream-list">
      <div 
        v-for="stream in assignments" 
        :key="stream.id" 
        class="stream-list-item"
        :class="{ 'selected': selectedStream?.id === stream.id, 'offline': stream.stream_status === 'offline' }"
        @click="selectStream(stream)"
      >
        <div class="list-thumbnail">
          <div class="status-indicator" :class="stream.stream_status">
            <div v-if="stream.stream_status === 'online'" class="status-pulse"></div>
          </div>
          <div v-if="stream.stream_status === 'online'" class="list-live-badge">LIVE</div>
        </div>
        <div class="list-info">
          <div class="list-title-row">
            <h3 title="{{ stream.streamer_username }}">{{ stream.streamer_username }}</h3>
            <div class="stream-platform" :class="stream.platform.toLowerCase()">
              {{ stream.platform }}
            </div>
          </div>
          <div class="list-details">
            <span class="list-detail-item viewers">
              <font-awesome-icon icon="eye" /> 
              <span>{{ formatNumber(stream.viewer_count || 0) }}</span>
            </span>
            <span class="list-detail-item duration">
              <font-awesome-icon icon="clock" /> 
              <span>{{ formatStreamTime(stream.stream_start_time) }}</span>
            </span>
            <span class="list-detail-item detection-status" v-if="stream.detection_status">
              <font-awesome-icon icon="chart-bar" /> 
              <span>{{ stream.detection_status }}</span>
            </span>
          </div>
        </div>
        <div class="list-actions">
          <button class="play-btn" title="Play stream">
            <font-awesome-icon icon="play" />
          </button>
          <button 
            class="detection-toggle-btn" 
            :class="{ 'active': stream.detection_active }"
            @click.stop="toggleDetection(stream)"
            :title="stream.detection_active ? 'Stop detection' : 'Start detection'"
          >
            <font-awesome-icon :icon="stream.detection_active ? 'binoculars' : 'binoculars'" />
          </button>
          <button 
            class="refresh-stream-btn" 
            @click.stop="refreshStreamUrl(stream)"
            title="Refresh stream"
          >
            <font-awesome-icon icon="sync" />
          </button>
        </div>
      </div>
    </div>

    <!-- Video Player Modal (displays when a stream is selected) -->
    <div v-if="selectedStream" class="video-player-modal">
      <div class="modal-content">
        <div class="modal-header">
          <div class="modal-title">
            <h3>{{ selectedStream.streamer_username }}</h3>
            <div class="stream-platform" :class="selectedStream.platform.toLowerCase()">
              {{ selectedStream.platform }}
            </div>
            <div class="stream-status-badge" :class="selectedStream.stream_status">
              {{ selectedStream.stream_status === 'online' ? 'LIVE' : selectedStream.stream_status === 'checking' ? 'CHECKING' : 'OFFLINE' }}
            </div>
          </div>
          <button class="close-btn" @click="closePlayer">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <div class="video-container">
          <div class="video-player">
            <div v-if="selectedStream.stream_status === 'online'" class="full-player">
      <video 
        ref="videoPlayer"
        class="full-video-player" 
        id="main-video-player"
        playsinline
        muted
      ></video>
      <button 
        v-if="!isPlaying" 
        class="play-overlay-btn"
        @click="startPlayback"
      >
        <font-awesome-icon icon="play" size="3x" />
      </button>
    </div>
            <div v-else-if="selectedStream.stream_status === 'checking'" class="checking-message">
              <div class="loading-spinner"></div>
              <p>Checking stream status...</p>
            </div>
            <div v-else class="offline-message">
              <font-awesome-icon icon="video-slash" size="4x" />
              <p>Stream is currently offline</p>
            </div>
          </div>
        </div>
        <div class="stream-metadata">
          <div class="meta-row">
            <div class="platform-badge" :class="selectedStream.platform.toLowerCase()">
              {{ selectedStream.platform }}
            </div>
            <div class="viewer-count">
              <font-awesome-icon icon="eye" /> {{ formatNumber(selectedStream.viewer_count || 0) }} viewers
            </div>
          </div>
          <div class="meta-row">
            <div class="stream-time">
              <font-awesome-icon icon="clock" /> 
              Streaming {{ formatStreamTime(selectedStream.stream_start_time) }}
            </div>
            <div class="status-group">
              <div v-if="selectedStream.stream_status === 'online'" class="live-status">
                <span class="live-dot"></span> LIVE
              </div>
              <div v-else-if="selectedStream.stream_status === 'checking'" class="checking-status">
                CHECKING
              </div>
              <div v-else class="offline-status">
                OFFLINE
              </div>
              <div v-if="selectedStream.detection_status" class="detection-status">
                {{ selectedStream.detection_status }}
              </div>
            </div>
          </div>
          <div class="detection-controls">
            <button 
              class="detection-trigger-btn" 
              :class="{ 'active': selectedStream.detection_active }"
              @click="toggleDetection(selectedStream)"
            >
              <font-awesome-icon :icon="selectedStream.detection_active ? 'stop' : 'play'" />
              {{ selectedStream.detection_active ? 'Stop Detection' : 'Start Detection' }}
            </button>
            <button class="refresh-stream-btn" @click="refreshStreamUrl(selectedStream)">
              <font-awesome-icon icon="sync" />
              Refresh Stream
            </button>
          </div>
          <div class="stream-url">
            <p><strong>Room URL:</strong> <a :href="selectedStream.room_url" target="_blank">{{ selectedStream.room_url }}</a></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { formatDistance } from 'date-fns'
import axios from 'axios'
import Hls from 'hls.js'
import { useToast } from 'vue-toastification'
import io from 'socket.io-client'

const toast = useToast()

// State variables
const viewMode = ref('list') // 'grid' or 'list'
const selectedStream = ref(null)
const assignments = ref([])
const isLoadingAssignments = ref(false)
const currentAgentId = ref(null)
const videoPlayer = ref(null)
const hlsInstances = ref({})
const socket = ref(null)
const loadingAttempts = ref({}) // Track loading attempts per stream

// Constants
const MAX_RETRY_ATTEMPTS = 3
const RETRY_DELAY = 5000 // 2 seconds between retries

onMounted(() => {
  loadAssignments()
  initSocketConnection()
  
  // Set up auto-refresh interval (every 5 minutes)
  const refreshInterval = setInterval(() => {
    if (!isLoadingAssignments.value) {
      refreshAllStreams()
    }
  }, 300000) // 5 minutes
  
  // Clean up interval on unmount
  onUnmounted(() => {
    clearInterval(refreshInterval)
  })
})

onUnmounted(() => {
  // Clean up resources
  destroyAllHlsInstances()
  
  if (socket.value) {
    socket.value.disconnect()
  }
})

const destroyAllHlsInstances = () => {
  // Destroy all HLS instances
  Object.values(hlsInstances.value).forEach(hls => {
    if (hls) {
      hls.destroy()
    }
  })
  hlsInstances.value = {}
}

const initSocketConnection = () => {
  socket.value = io()
  
  // Listen for stream updates
  socket.value.on('stream_update', (data) => {
    const streamIndex = assignments.value.findIndex(s => s.id === data.id)
    if (streamIndex !== -1) {
      const updatedStream = { ...assignments.value[streamIndex], ...data }
      assignments.value[streamIndex] = updatedStream
      
      // Update selected stream if it's the one being updated
      if (selectedStream.value && selectedStream.value.id === data.id) {
        selectedStream.value = updatedStream
      }
      
      // Show toast notification for detection status changes
      if (data.detection_status) {
        toast.info(`${updatedStream.streamer_username}: ${data.detection_status}`)
      }
    }
  })
  
  // Listen for detection status updates
  socket.value.on('detection_status', (data) => {
    const streamIndex = assignments.value.findIndex(s => s.id === data.stream_id)
    if (streamIndex !== -1) {
      assignments.value[streamIndex].detection_active = data.active
      assignments.value[streamIndex].detection_status = data.status
      
      // Update selected stream if it's the one being updated
      if (selectedStream.value && selectedStream.value.id === data.stream_id) {
        selectedStream.value.detection_active = data.active
        selectedStream.value.detection_status = data.status
      }
    }
  })
}

const loadAssignments = async () => {
  isLoadingAssignments.value = true
  try {
    // Get current agent ID
    const sessionResponse = await axios.get('/api/session')
    currentAgentId.value = sessionResponse.data.user.id
    
    // Get streams
    const streamsResponse = await axios.get('/api/streams')
    
    // Filter for assigned streams and set up stream properties
    assignments.value = Object.values(streamsResponse.data)
      .filter(stream => {
        return stream.assignments?.some(a => a.agent_id === currentAgentId.value) && 
               (stream.platform === 'Chaturbate' || stream.platform === 'Stripchat')
      })
      .map(stream => ({
        ...stream,
        video_url: stream.platform === 'Chaturbate' 
          ? stream.chaturbate_m3u8_url 
          : stream.stripchat_m3u8_url,
        stream_status: 'checking',
        detection_active: false,
        detection_status: null
      }))
    
    // Clean up any existing HLS instances
    destroyAllHlsInstances()
    
    // Reset loading attempts
    loadingAttempts.value = {}
    
    // Check stream status for each stream in parallel
    await Promise.all(assignments.value.map(stream => {
      loadingAttempts.value[stream.id] = 0
      return checkStreamStatusWithHls(stream)
    }))
    
    // Check detection status for each stream in parallel
    await Promise.all(assignments.value.map(checkDetectionStatus))
    
    // If there's a selected stream, make sure its info is updated
    if (selectedStream.value) {
      const updatedStream = assignments.value.find(s => s.id === selectedStream.value.id)
      if (updatedStream) {
        selectedStream.value = { ...updatedStream }
      }
    }
    
    // Auto-play the first online stream if no stream is selected
    if (!selectedStream.value && assignments.value.length > 0) {
      const onlineStream = assignments.value.find(s => s.stream_status === 'online')
      if (onlineStream) {
        selectStream(onlineStream)
      }
    }
  } catch (error) {
    toast.error('Failed to load assignments')
    console.error('Error loading assignments:', error)
  } finally {
    isLoadingAssignments.value = false
  }
}

const checkStreamStatusWithHls = async (stream) => {
  if (!stream.video_url) {
    stream.stream_status = 'offline'
    return
  }
  
  // Wait for the DOM to update
  await nextTick()
  
  // Check if we should retry
  const attemptCount = loadingAttempts.value[stream.id] || 0
  if (attemptCount >= MAX_RETRY_ATTEMPTS) {
    stream.stream_status = 'offline'
    return
  }
  
  // Increment attempt counter
  loadingAttempts.value[stream.id] = attemptCount + 1
  
  try {
    const videoElement = document.getElementById(`mini-player-${stream.id}`)
    
    if (videoElement && Hls.isSupported()) {
      // Create new HLS instance
      const hls = new Hls({
        maxBufferLength: 10,
        maxMaxBufferLength: 15,
        liveSyncDuration: 3,
        liveMaxLatencyDuration: 10,
        liveDurationInfinity: true,
        debug: false,
        xhrSetup: (xhr) => {
          xhr.timeout = 5000 // 5 second timeout for better error handling
        }
      })
      
      // Store the instance for cleanup later
      hlsInstances.value[stream.id] = hls
      
      // Add event listeners
      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        hls.loadSource(stream.video_url)
      })
      
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        stream.stream_status = 'online'
        videoElement.play().catch(() => {
          console.log('Auto-play prevented for stream:', stream.id)
        })
      })
      
      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          switch(data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
            case Hls.ErrorTypes.MEDIA_ERROR:
            default:
              hls.destroy()
              delete hlsInstances.value[stream.id]
              
              // Try again if under max attempts
              if (loadingAttempts.value[stream.id] < MAX_RETRY_ATTEMPTS) {
                console.log(`Retry attempt ${loadingAttempts.value[stream.id]} for stream ${stream.id}`)
                setTimeout(() => {
                  checkStreamStatusWithHls(stream)
                }, RETRY_DELAY)
              } else {
                stream.stream_status = 'offline'
              }
              break
          }
        }
      })
      
      // Attach media
      hls.attachMedia(videoElement)
      
      // Set timeout for stream status check
      setTimeout(() => {
        if (stream.stream_status === 'checking') {
          // Try again if under max attempts
          if (loadingAttempts.value[stream.id] < MAX_RETRY_ATTEMPTS) {
            hls.destroy()
            delete hlsInstances.value[stream.id]
            setTimeout(() => {
              checkStreamStatusWithHls(stream)
            }, RETRY_DELAY)
          } else {
            stream.stream_status = 'offline'
            hls.destroy()
            delete hlsInstances.value[stream.id]
          }
        }
      }, 5000)
    } else {
      // If HLS is not supported or element not found
      await checkStreamStatus(stream)
    }
  } catch (error) {
    console.error('Error checking stream status with HLS:', error)
    
    // Try again if under max attempts
    if (loadingAttempts.value[stream.id] < MAX_RETRY_ATTEMPTS) {
      setTimeout(() => {
        checkStreamStatusWithHls(stream)
      }, RETRY_DELAY)
    } else {
      stream.stream_status = 'offline'
    }
  }
}

const checkStreamStatus = async (stream) => {
  if (!stream.video_url) {
    stream.stream_status = 'offline'
    return
  }
  
  // Check if we should retry
  const attemptCount = loadingAttempts.value[stream.id] || 0
  if (attemptCount >= MAX_RETRY_ATTEMPTS) {
    stream.stream_status = 'offline'
    return
  }
  
  // Increment attempt counter
  loadingAttempts.value[stream.id] = attemptCount + 1
  
  try {
    // Use a HEAD request with timeout to check if stream is available
    await axios.head(stream.video_url, { timeout: 15000 })
    stream.stream_status = 'online'
  } catch (error) {
    // Try again if under max attempts
    if (loadingAttempts.value[stream.id] < MAX_RETRY_ATTEMPTS) {
      setTimeout(() => {
        checkStreamStatus(stream)
      }, RETRY_DELAY)
    } else {
      stream.stream_status = 'offline'
    }
  }
}

const checkDetectionStatus = async (stream) => {
  try {
    const response = await axios.get(`/api/detection-status?stream_id=${stream.id}`)
    stream.detection_active = response.data.active
    stream.detection_status = response.data.status
  } catch (error) {
    stream.detection_active = false
    stream.detection_status = null
  }
}

const toggleDetection = async (stream) => {
  try {
    await axios.post('/api/trigger-detection', {
      stream_id: stream.id,
      stream_url: stream.video_url,
      action: stream.detection_active ? 'stop' : 'start'
    })
    
    // Update stream detection status
    const streamIndex = assignments.value.findIndex(s => s.id === stream.id)
    if (streamIndex !== -1) {
      assignments.value[streamIndex].detection_active = !stream.detection_active
      assignments.value[streamIndex].detection_status = stream.detection_active ? 'Stopped' : 'Starting...'
      
      // Update selected stream if it's the current stream
      if (selectedStream.value && selectedStream.value.id === stream.id) {
        selectedStream.value.detection_active = !stream.detection_active
        selectedStream.value.detection_status = stream.detection_active ? 'Stopped' : 'Starting...'
      }
    }
    
    toast.success(`Detection ${stream.detection_active ? 'stopped' : 'started'} for ${stream.streamer_username}`)
  } catch (error) {
    toast.error(`Failed to ${stream.detection_active ? 'stop' : 'start'} detection`)
  }
}

const refreshStreamUrl = async (stream) => {
  try {
    toast.info(`Refreshing stream for ${stream.streamer_username}...`)
    
    // Determine the API endpoint and payload based on platform
    const endpoint = `/api/refresh/${stream.platform.toLowerCase()}`
    const payload = stream.platform === 'Chaturbate'
      ? { room_slug: stream.streamer_username }
      : { room_url: stream.room_url }
    
    const response = await axios.post(endpoint, payload)
    
    if (response.data.m3u8_url) {
      // Update the stream URL
      const streamIndex = assignments.value.findIndex(s => s.id === stream.id)
      if (streamIndex !== -1) {
        assignments.value[streamIndex].video_url = response.data.m3u8_url
        
        if (stream.platform === 'Chaturbate') {
          assignments.value[streamIndex].chaturbate_m3u8_url = response.data.m3u8_url
        } else {
          assignments.value[streamIndex].stripchat_m3u8_url = response.data.m3u8_url
        }
        
        // Reset stream status to checking
        assignments.value[streamIndex].stream_status = 'checking'
        
        // Clean up existing HLS instance if any
        if (hlsInstances.value[stream.id]) {
          hlsInstances.value[stream.id].destroy()
          delete hlsInstances.value[stream.id]
        }
        
        // Reset loading attempts for this stream
        loadingAttempts.value[stream.id] = 0
        
        // Check if stream is online with HLS
        await checkStreamStatusWithHls(assignments.value[streamIndex])
        
        // If this is the selected stream, update video player
        if (selectedStream.value && selectedStream.value.id === stream.id) {
          selectedStream.value = { ...assignments.value[streamIndex] }
          
          // Re-initialize video player
          if (hlsInstances.value['main-player']) {
            hlsInstances.value['main-player'].destroy()
            delete hlsInstances.value['main-player']
            await nextTick()
            initializeHlsPlayer()
          }
        }
        
        toast.success(`Stream refreshed for ${stream.streamer_username}`)
      }
    } else {
      toast.error(`Failed to refresh stream for ${stream.streamer_username}`)
    }
  } catch (error) {
    toast.error(`Error refreshing stream: ${error.message}`)
  }
}

const refreshAllStreams = async () => {
  toast.info('Refreshing all streams...')
  
  for (const stream of assignments.value) {
    stream.stream_status = 'checking'
    
    // Clean up existing HLS instance if any
    if (hlsInstances.value[stream.id]) {
      hlsInstances.value[stream.id].destroy()
      delete hlsInstances.value[stream.id]
    }
    
    // Reset loading attempts for this stream
    loadingAttempts.value[stream.id] = 0
  }
  
  // Check status for all streams
  await Promise.all(assignments.value.map(checkStreamStatusWithHls))
  
  toast.success('All streams refreshed')
}

const selectStream = async (stream) => {
  destroyHlsInstance('main-player')
  selectedStream.value = stream
  await nextTick()
  initializeHlsPlayer()
}

const initializeHlsPlayer = () => {
  if (!selectedStream.value) return

  // Clear existing instance first
  if (hlsInstances.value['main-player']) {
    hlsInstances.value['main-player'].destroy()
    delete hlsInstances.value['main-player']
  }

  if (selectedStream.value.stream_status === 'online' && videoPlayer.value) {
    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true, // Enable separate thread for parsing
        lowLatencyMode: true,
        backBufferLength: 30,
        maxBufferSize: 60 * 1000, // 60 seconds
        maxLoadingDelay: 4,
        liveSyncDuration: 3,
        liveMaxLatencyDuration: 10,
        fragLoadingTimeOut: 20000,
        manifestLoadingTimeOut: 20000,
        levelLoadingTimeOut: 20000
      })

      hlsInstances.value['main-player'] = hls

      // Improved error handling
      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS Error:', data)
        if (data.fatal) {
          switch(data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              hls.startLoad()
              break
            case Hls.ErrorTypes.MEDIA_ERROR:
              hls.recoverMediaError()
              break
            default:
              destroyHlsInstance('main-player')
              initializeHlsPlayer()
              break
          }
        }
      })

      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        hls.loadSource(selectedStream.value.video_url)
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          // Add play button for user interaction
          videoPlayer.value.controls = true
          videoPlayer.value.muted = false
          videoPlayer.value.play().catch(error => {
            console.log(error,'User interaction required for playback')
          })
        })
      })

      hls.attachMedia(videoPlayer.value)
    } else if (videoPlayer.value.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support
      videoPlayer.value.src = selectedStream.value.video_url
      videoPlayer.value.addEventListener('loadedmetadata', () => {
        videoPlayer.value.controls = true
        videoPlayer.value.play().catch(error => {
          console.log('Native HLS play failed:', error)
        })
      })
    }
  }
}

const destroyHlsInstance = (key) => {
  if (hlsInstances.value[key]) {
    hlsInstances.value[key].destroy()
    delete hlsInstances.value[key]
  }
}

const closePlayer = () => {
  destroyHlsInstance('main-player')
  selectedStream.value = null
}

const formatNumber = (num) => {
  if (num >= 1000000) return `${(num/1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num/1000).toFixed(1)}K`
  return num
}

const formatStreamTime = (timestamp) => {
  if (!timestamp) return 'Unknown'
  try {
    return formatDistance(new Date(timestamp), new Date(), { addSuffix: true })
  } catch {
    return 'Unknown'
  }
}

// Watch for changes to selectedStream and refresh its status
watch(selectedStream, async (newStream) => {
  if (newStream) {
    await checkStreamStatus(newStream)
    await checkDetectionStatus(newStream)
  }
})
</script>

<style scoped>
.stream-player-container {
  width: 100%;
  position: relative;
}

/* View Controls */
.view-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.view-controls h2 {
  font-size: 1.3rem;
  margin: 0;
}

.controls-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.view-toggle {
  display: flex;
  background-color: var(--input-bg);
  border-radius: 6px;
  overflow: hidden;
}

.toggle-btn {
  border: none;
  background: transparent;
  padding: 0.5rem 0.8rem;
  cursor: pointer;
  color: var(--text-light);
  transition: all 0.2s ease;
}

.toggle-btn.active {
  background-color: var(--primary-color);
  color: white;
}

.refresh-button {
  width: 1.2rem;
  height: 2rem;
  border-radius: 100%;
  background-color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.refresh-button:hover {
  transform: rotate(360deg);
}

/* Grid View */
.stream-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stream-grid-item {
  cursor: pointer;
  transition: transform 0.2s;
  border-radius: 10px;
  overflow: hidden;
  background-color: var(--card-bg);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.stream-grid-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.video-thumbnail {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 aspect ratio */
  overflow: hidden;
}

.player-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--input-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 30;
  transition: opacity 0.3s;
  color: white;
  z-index: 2;
}

.video-thumbnail:hover .player-overlay {
  opacity: 1;
}

.offline-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.offline-text {
  font-size: 1.2rem;
  font-weight: bold;
  color: #ffffff;
  padding: 5px 15px;
  background-color: rgba(244, 67, 54, 0.7);
  border-radius: 4px;
}

.stream-badges {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  z-index: 3;
}

.live-badge {
  background-color: #f44336;
  color: white;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 4px;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: white;
  display: inline-block;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.detection-badge {
  background-color: #2196F3;
  color: white;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: bold;
}

.stream-duration {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 0.8rem;
  padding: 2px 6px;
  border-radius: 4px;
  z-index: 3;
}

.stream-info {
  padding: 1rem;
}

.stream-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.stream-title {
  font-size: 1rem;
  margin: 0;
  font-weight: 600;
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stream-platform {
  font-size: 0.7rem;
  padding: 0.1rem 0.5rem;
  border-radius: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.stream-platform.chaturbate {
  background-color: #f5a62322;
  color: #f5a623;
  border: 1px solid #f5a62333;
}

.stream-platform.stripchat {
  background-color: #7e57c222;
  color: #7e57c2;
  border: 1px solid #7e57c233;
}

.stream-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--text-light);
  margin-bottom: 0.8rem;
}

.stream-controls {
  display: flex;
  gap: 0.5rem;
}

.control-btn {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.detection-btn {
  background-color: #4CAF50;
  color: white;
  flex-grow: 1;
}

.detection-btn.active {
  background-color: #f44336;
}

.refresh-btn {
  background-color: #2196F3;
  color: white;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.control-btn:hover {
  filter: brightness(1.1);
}

/* List View */
.stream-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.stream-list-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  background-color: var(--card-bg);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--border-color);
  position: relative;
  overflow: hidden;
}

.stream-list-item:hover {
  background-color: var(--card-bg-hover);
  transform: translateX(4px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
}

.stream-list-item.selected {
  border-left: 4px solid var(--primary-color);
  padding-left: calc(1rem - 3px);
  background-color: var(--card-bg-hover);
}

.stream-list-item.offline {
  opacity: 0.85;
}

.list-thumbnail {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  position: relative;
}

.status-indicator {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  position: relative;
}

.status-indicator.online {
  background-color: #4CAF50;
  box-shadow: 0 0 6px #4CAF50;
}

.status-indicator.offline {
  background-color: #757575;
}

.status-pulse {
  position: absolute;
  top: -4px;
  left: -4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background-color: rgba(76, 175, 80, 0.3);
  animation: pulse-ring 2s ease-out infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 0.8; }
  80%, 100% { transform: scale(1.5); opacity: 0; }
}

.list-live-badge {
  position: absolute;
  top: -18px;
  left: 20px;
  font-size: 0.65rem;
  font-weight: bold;
  color: #fff;
  background-color: #f44336;
  padding: 2px 6px;
  border-radius: 3px;
}

.list-info {
  flex-grow: 1;
  margin-left: 1rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.list-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.list-title-row h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
  color: var(--text-color);
}

.list-details {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--text-light);
}

.list-detail-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.list-detail-item svg {
  color: var(--primary-color);
  opacity: 0.8;
}

.list-actions {
  margin-left: 1rem;
  display: flex;
  gap: 10px;
  align-items: center;
}

.play-btn, .detection-toggle-btn, .refresh-stream-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: white;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
}

.play-btn {
  background-color: var(--primary-color);
}

.detection-toggle-btn {
  background-color: #4CAF50;
}

.detection-toggle-btn.active {
  background-color: #f44336;
}

.refresh-stream-btn {
  background-color: #2196F3;
}

.play-btn:hover, .detection-toggle-btn:hover, .refresh-stream-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

/* Light/dark mode specific adjustments */
@media (prefers-color-scheme: dark) {
  .play-btn, .detection-toggle-btn, .refresh-stream-btn {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  }
  
  .list-detail-item svg {
    color: var(--primary-color);
    opacity: 0.9;
  }
  
  .stream-list-item {
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
  }
}

@media (prefers-color-scheme: light) {
  .status-indicator.online {
    box-shadow: 0 0 8px rgba(76, 175, 80, 0.6);
  }
  
  .list-detail-item svg {
    color: var(--primary-color);
    opacity: 0.7;
  }
}

/* Video Player Modal */
.video-player-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  width: 90%;
  max-width: 900px;
  background-color: var(--card-bg);
  border-radius: 12px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.stream-status-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: bold;
}

.stream-status-badge.online {
  background-color: #4CAF50;
  color: white;
}

.stream-status-badge.offline {
  background-color: #757575;
  color: white;
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: var(--border-color);
  color: var(--text-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: var(--input-bg);
}

.video-container {
  width: 100%;
  position: relative;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 aspect ratio */
  overflow: hidden;
}

.video-player {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
}

.full-player {
  width: 100%;
  height: 100%;
}

.full-player-instance {
  width: 100%;
  height: 100%;
}

.offline-message {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #1a1a1a;
  color: #fff;
}

.offline-message p {
  margin-top: 1rem;
  font-size: 1.2rem;
}

.stream-metadata {
  padding: 1rem;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.8rem;
}

.platform-badge {
  font-size: 0.8rem;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.viewer-count {
  font-size: 0.9rem;
  color: var(--text-light);
  display: flex;
  align-items: center;
  gap: 5px;
}

.stream-time {
  font-size: 0.9rem;
  color: var(--text-light);
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.live-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.8rem;
  font-weight: bold;
  color: #f44336;
}

.offline-status {
  font-size: 0.8rem;
  font-weight: bold;
  color: #757575;
}

.detection-status {
  font-size: 0.8rem;
  font-weight: bold;
  color: #2196F3;
}

.detection-controls {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
}

.detection-trigger-btn, .refresh-stream-btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: none;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.detection-trigger-btn {
  background-color: #4CAF50;
  color: white;
  flex-grow: 1;
}

.detection-trigger-btn.active {
  background-color: #f44336;
}

.refresh-stream-btn {
  background-color: #2196F3;
  color: white;
}

.detection-trigger-btn:hover, .refresh-stream-btn:hover {
  filter: brightness(1.1);
}

.stream-url {
  margin-top: 1rem;
  font-size: 0.9rem;
}

.stream-url a {
  color: var(--primary-color);
  text-decoration: none;
  word-break: break-all;
}

.stream-url a:hover {
  text-decoration: underline;
}

/* Mini player styling */
.mini-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.mini-player-instance {
  width: 100%;
  height: 100%;
}

/* Loading state */
.loading-container {
  width: 100%;
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-light);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Empty state */
.empty-state {
  width: 100%;
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-light);
}

.empty-state svg {
  margin-bottom: 1rem;
}

.empty-state p {
  margin-bottom: 1rem;
}

.empty-state .refresh-btn {
  width: auto;
  height: auto;
  padding: 0.5rem 1rem;
  border-radius: 6px;
}

/* Adding responsiveness to list view */
@media (max-width: 640px) {
  .list-actions {
    margin-left: 0.5rem;
    gap: 6px;
  }
  
  .play-btn, .detection-toggle-btn, .refresh-stream-btn {
    width: 32px;
    height: 32px;
  }
  
  .list-info {
    margin-left: 0.75rem;
  }
  
  .list-title-row h3 {
    font-size: 0.9rem;
  }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .stream-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .modal-content {
    width: 95%;
  }
  
  .detection-controls {
    flex-direction: column;
  }
  
  .list-details {
    gap: 8px;
    flex-wrap: wrap;
  }
  
  .stream-list-item {
    padding: 0.8rem;
  }
}

@media (max-width: 480px) {
  .view-controls h2 {
    font-size: 1.1rem;
  }
  
  .stream-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .stream-list-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .list-info {
    width: 100%;
    margin-left: 0;
    margin-top: 0.5rem;
  }
  
  .list-actions {
    margin-top: 0.8rem;
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }
  
  .list-thumbnail {
    width: 100%;
    justify-content: flex-start;
  }
  
  .status-indicator {
    display: block;
    margin-right: 0.5rem;
  }
  
  .list-live-badge {
    position: static;
    margin-left: 0.5rem;
  }
  
  .list-title-row {
    margin-top: 0.5rem;
  }
  
  .list-details {
    margin-top: 0.4rem;
  }
}
</style>