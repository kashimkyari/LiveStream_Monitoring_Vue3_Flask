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
          <font-awesome-icon icon="sync" :class="{ 'fa-spin': isLoading }" />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="skeleton-loading">
      <div v-if="viewMode === 'grid'" class="stream-grid">
        <div v-for="i in 6" :key="i" class="skeleton-grid-item">
          <div class="skeleton-thumbnail"></div>
          <div class="skeleton-info">
            <div class="skeleton-title"></div>
            <div class="skeleton-details"></div>
          </div>
        </div>
      </div>
      <div v-else class="stream-list">
        <div v-for="i in 6" :key="i" class="skeleton-list-item">
          <div class="skeleton-list-thumbnail"></div>
          <div class="skeleton-list-info">
            <div class="skeleton-list-title"></div>
            <div class="skeleton-list-details"></div>
          </div>
        </div>
      </div>
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
          <div class="mini-player">
            <video 
              class="mini-video-player" 
              :id="`mini-player-${stream.id}`"
              muted
              autoplay
              playsinline
            ></video>
          </div>
          <div class="stream-badges">
            <div class="live-badge">
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
        :class="{ 'selected': selectedStream?.id === stream.id }"
        @click="selectStream(stream)"
      >
        <div class="list-thumbnail">
          <div class="status-indicator">
            <div class="status-pulse"></div>
          </div>
          <div class="list-live-badge">LIVE</div>
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

    <!-- Video Player Modal using the VideoPlayerModal component -->
    <VideoPlayerModal
      :show="!!selectedStream"
      :stream="selectedStream || {}"
      @close="closePlayer"
      @toggle-detection="toggleDetection"
      @refresh-stream="refreshStreamUrl"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { formatDistance } from 'date-fns'
import axios from 'axios'
import Hls from 'hls.js'
import { useToast } from 'vue-toastification'
import VideoPlayerModal from './VideoPlayerModal.vue'

const toast = useToast()

// State variables
const viewMode = ref('list') // 'grid' or 'list'
const selectedStream = ref(null)
const assignments = ref([])
const isLoading = ref(false)
const currentAgentId = ref(null)
const hlsInstances = ref({})

onMounted(() => {
  loadAssignments()
  
  // Set up auto-refresh interval (every 5 minutes)
  const refreshInterval = setInterval(() => {
    if (!isLoading.value) {
      loadAssignments()
    }
  }, 300000) // 5 minutes
  
  // Clean up interval on unmount
  onUnmounted(() => {
    clearInterval(refreshInterval)
    destroyAllHlsInstances()
  })
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

const loadAssignments = async () => {
  isLoading.value = true
  
  try {
    // Get current agent ID
    const sessionResponse = await axios.get('/api/session')
    currentAgentId.value = sessionResponse.data.user.id
    
    // Get streams
    const streamsResponse = await axios.get('/api/streams')
    
    // Filter for assigned streams
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
        detection_active: false,
        detection_status: null
      }))
    
    // Clean up any existing HLS instances
    destroyAllHlsInstances()
    
    // Initialize mini-players in grid view
    if (viewMode.value === 'grid') {
      await nextTick()
      initializeMiniPlayers()
    }
    
    // Check detection status for each stream
    await Promise.all(assignments.value.map(checkDetectionStatus))
    
  } catch (error) {
    toast.error('Failed to load assignments')
    console.error('Error loading assignments:', error)
  } finally {
    isLoading.value = false
  }
}

const initializeMiniPlayers = () => {
  // Only setup players for grid view
  if (viewMode.value !== 'grid') return
  
  assignments.value.forEach(stream => {
    if (!stream.video_url) return
    
    const videoElement = document.getElementById(`mini-player-${stream.id}`)
    if (!videoElement) return
    
    if (Hls.isSupported()) {
      const hls = new Hls({
        maxBufferLength: 5,
        maxMaxBufferLength: 10,
        liveSyncDuration: 3,
        liveMaxLatencyDuration: 10,
        debug: false,
        autoplay: true
      })
      
      hlsInstances.value[stream.id] = hls
      
      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        hls.loadSource(stream.video_url)
      })
      
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        // Lower quality for thumbnails
        if (hls.levels.length > 1) {
          hls.currentLevel = hls.levels.length - 1 // Use lowest quality
        }
        
        videoElement.play().catch(() => {
          console.log('Auto-play prevented for mini player')
        })
      })
      
      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          hls.destroy()
          delete hlsInstances.value[stream.id]
        }
      })
      
      hls.attachMedia(videoElement)
    } else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support
      videoElement.src = stream.video_url
      videoElement.play().catch(() => {
        console.log('Auto-play prevented for native HLS')
      })
    }
  })
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
    stream.detection_active = !stream.detection_active
    stream.detection_status = stream.detection_active ? 'Running...' : 'Stopped'
    
    toast.success(`Detection ${stream.detection_active ? 'started' : 'stopped'} for ${stream.streamer_username}`)
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
      stream.video_url = response.data.m3u8_url
      
      if (stream.platform === 'Chaturbate') {
        stream.chaturbate_m3u8_url = response.data.m3u8_url
      } else {
        stream.stripchat_m3u8_url = response.data.m3u8_url
      }
      
      // Reinitialize player if in grid view
      if (viewMode.value === 'grid') {
        // Clean up existing HLS instance if any
        if (hlsInstances.value[stream.id]) {
          hlsInstances.value[stream.id].destroy()
          delete hlsInstances.value[stream.id]
        }
        
        await nextTick()
        
        // Initialize single mini player
        const videoElement = document.getElementById(`mini-player-${stream.id}`)
        if (videoElement && Hls.isSupported()) {
          const hls = new Hls({
            maxBufferLength: 5,
            maxMaxBufferLength: 10,
          })
          
          hlsInstances.value[stream.id] = hls
          
          hls.on(Hls.Events.MEDIA_ATTACHED, () => {
            hls.loadSource(stream.video_url)
          })
          
          hls.on(Hls.Events.MANIFEST_PARSED, () => {
            if (hls.levels.length > 1) {
              hls.currentLevel = hls.levels.length - 1 // Use lowest quality
            }
            videoElement.play().catch(() => {})
          })
          
          hls.attachMedia(videoElement)
        }
      }
      
      toast.success(`Stream refreshed for ${stream.streamer_username}`)
    } else {
      toast.error(`Failed to refresh stream for ${stream.streamer_username}`)
    }
  } catch (error) {
    toast.error(`Error refreshing stream: ${error.message}`)
  }
}

const selectStream = (stream) => {
  selectedStream.value = stream
}

const closePlayer = () => {
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

// Watch for view mode changes to initialize mini players when switching to grid
watch(viewMode, (newMode) => {
  if (newMode === 'grid') {
    nextTick(() => {
      initializeMiniPlayers()
    })
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

.mini-video-player {
  width: 100%;
  height: 100%;
  object-fit: fill;
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