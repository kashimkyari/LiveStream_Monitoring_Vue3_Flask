<template>
  <div class="stream-player-container">
    <!-- View Toggle Controls -->
    <div class="view-controls">
      <h2>All Streams</h2>
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
    <div v-else-if="streams.length === 0" class="empty-state">
      <font-awesome-icon icon="video-slash" size="2x" />
      <p>No streams available.</p>
      <button class="refresh-btn" @click="loadStreams">
        Refresh
      </button>
    </div>

    <!-- Grid View -->
    <div v-else-if="viewMode === 'grid'" class="stream-grid">
      <!-- Online Streams -->
      <div class="section-header" @click="toggleOnlineCollapse">
        <h3>Online Streams</h3>
        <span class="stream-count">{{ onlineStreams.length }} streams</span>
        <font-awesome-icon :icon="isOnlineCollapsed ? 'chevron-down' : 'chevron-up'" class="collapse-icon" />
      </div>
      <div v-if="!isOnlineCollapsed" class="stream-grid">
        <div 
          v-for="stream in onlineStreams" 
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
      
      <!-- Offline Streams -->
      <div class="section-header offline-section" @click="toggleOfflineCollapse">
        <h3>Offline Streams</h3>
        <span class="stream-count">{{ offlineStreams.length }} streams</span>
        <font-awesome-icon :icon="isOfflineCollapsed ? 'chevron-down' : 'chevron-up'" class="collapse-icon" />
      </div>
      <div v-if="!isOfflineCollapsed" class="stream-grid">
        <div 
          v-for="stream in offlineStreams" 
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
              <div class="live-badge offline">
                <span class="live-dot offline"></span>OFFLINE
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
    </div>

    <!-- List View -->
    <div v-else class="stream-list">
      <!-- Online Streams -->
      <div class="section-header" @click="toggleOnlineCollapse">
        <h3>Online Streams</h3>
        <span class="stream-count">{{ onlineStreams.length }} streams</span>
        <font-awesome-icon :icon="isOnlineCollapsed ? 'chevron-down' : 'chevron-up'" class="collapse-icon" />
      </div>
      <div v-if="!isOnlineCollapsed" class="stream-list">
        <div 
          v-for="stream in onlineStreams" 
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
            <h3 :title="stream.streamer_username">{{ stream.streamer_username }}</h3>
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
      
      <!-- Offline Streams -->
      <div class="section-header offline-section" @click="toggleOfflineCollapse">
        <h3>Offline Streams</h3>
        <span class="stream-count">{{ offlineStreams.length }} streams</span>
        <font-awesome-icon :icon="isOfflineCollapsed ? 'chevron-down' : 'chevron-up'" class="collapse-icon" />
      </div>
      <div v-if="!isOfflineCollapsed" class="stream-list">
        <div 
          v-for="stream in offlineStreams" 
          :key="stream.id" 
          class="stream-list-item offline"
          :class="{ 'selected': selectedStream?.id === stream.id }"
          @click="selectStream(stream)"
        >
          <div class="list-thumbnail">
            <div class="status-indicator offline">
            </div>
            <div class="list-live-badge offline">OFFLINE</div>
          </div>
          <div class="list-info">
            <div class="list-title-row">
              <h3 :title="stream.streamer_username">{{ stream.streamer_username }}</h3>
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
    </div>

    <!-- Video Player Modal -->
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
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue';
import { formatDistance } from 'date-fns';
import axios from 'axios';
import Hls from 'hls.js';
import { useToast } from 'vue-toastification';
import VideoPlayerModal from './VideoPlayerModal.vue';

const toast = useToast();

// State variables
const viewMode = ref('grid'); // 'grid' or 'list'
const selectedStream = ref(null);
const streams = ref([]);
const isLoading = ref(false);
const hlsInstances = ref({});
const isOnlineCollapsed = ref(false);
const isOfflineCollapsed = ref(true);

// Computed properties for online and offline streams
const onlineStreams = computed(() => {
  return streams.value.filter(stream => stream.status === 'online');
});

const offlineStreams = computed(() => {
  return streams.value.filter(stream => stream.status !== 'online');
});

const toggleOnlineCollapse = () => {
  isOnlineCollapsed.value = !isOnlineCollapsed.value;
};

const toggleOfflineCollapse = () => {
  isOfflineCollapsed.value = !isOfflineCollapsed.value;
};

onMounted(() => {
  loadStreams();
  
  // Set up auto-refresh interval (every 5 minutes)
  const refreshInterval = setInterval(() => {
    if (!isLoading.value) {
      loadStreams();
    }
  }, 300000); // 5 minutes
  
  // Clean up interval on unmount
  onUnmounted(() => {
    clearInterval(refreshInterval);
    destroyAllHlsInstances();
  });
});

const destroyAllHlsInstances = () => {
  // Destroy all HLS instances
  Object.values(hlsInstances.value).forEach(hls => {
    if (hls) {
      hls.destroy();
    }
  });
  hlsInstances.value = {};
};

const loadStreams = async () => {
  isLoading.value = true;
  
  try {
    // Get all streams
    const streamsResponse = await axios.get('/api/streams');
    
    // Map streams to include video_url and detection fields
    streams.value = Object.values(streamsResponse.data)
      .filter(stream => stream.platform === 'Chaturbate' || stream.platform === 'Stripchat')
      .map(stream => ({
        ...stream,
        video_url: stream.platform === 'Chaturbate' 
          ? stream.chaturbate_m3u8_url 
          : stream.stripchat_m3u8_url,
        detection_active: false,
        detection_status: null,
        status: stream.status || 'offline' // Ensure status is set
      }));
    
    // Clean up any existing HLS instances
    destroyAllHlsInstances();
    
    // Initialize mini-players in grid view
    if (viewMode.value === 'grid') {
      await nextTick();
      initializeMiniPlayers();
    }
    
    // Check detection status for each stream
    await Promise.all(streams.value.map(checkDetectionStatus));
    
  } catch (error) {
    toast.error('Failed to load streams');
    console.error('Error loading streams:', error);
  } finally {
    isLoading.value = false;
  }
};

const initializeMiniPlayers = () => {
  // Only setup players for grid view
  if (viewMode.value !== 'grid') return;
  
  streams.value.forEach(stream => {
    // Skip offline streams
    if (stream.status !== 'online') return;
    
    // Existing player initialization logic
    if (!stream.video_url) return;
    
    const videoElement = document.getElementById(`mini-player-${stream.id}`);
    if (!videoElement) return;
    
    if (Hls.isSupported()) {
      const hls = new Hls({
        maxBufferLength: 5,
        maxMaxBufferLength: 10,
        liveSyncDuration: 3,
        liveMaxLatencyDuration: 10,
        debug: false,
        autoplay: true,
        capLevelToPlayerSize: true,

      });
      
      hlsInstances.value[stream.id] = hls;
      
      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        hls.loadSource(stream.video_url);
      });
      
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        // Lower quality for thumbnails
        if (hls.levels.length > 1) {
          hls.currentLevel = hls.levels.length - 1; // Use lowest quality
        }
        
        videoElement.play().catch(() => {
          console.log('Auto-play prevented for mini player');
        });
      });
      
      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          hls.destroy();
          delete hlsInstances.value[stream.id];
        }
      });
      
      hls.attachMedia(videoElement);
    } else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support
      videoElement.src = stream.video_url;
      videoElement.play().catch(() => {
        console.log('Auto-play prevented for native HLS');
      });
    }
  });
};

const checkDetectionStatus = async (stream) => {
  try {
    const response = await axios.get(`/api/detection-status?stream_id=${stream.id}`);
    stream.detection_active = response.data.active;
    stream.detection_status = response.data.status;
  } catch (error) {
    stream.detection_active = false;
    stream.detection_status = null;
  }
};

const toggleDetection = async (stream) => {
  try {
    await axios.post('/api/trigger-detection', {
      stream_id: stream.id,
      stream_url: stream.video_url,
      action: stream.detection_active ? 'stop' : 'start'
    });
    
    // Update stream detection status
    stream.detection_active = !stream.detection_active;
    stream.detection_status = stream.detection_active ? 'Running...' : 'Stopped';
    
    toast.success(`Detection ${stream.detection_active ? 'started' : 'stopped'} for ${stream.streamer_username}`);
  } catch (error) {
    toast.error(`Failed to ${stream.detection_active ? 'stop' : 'start'} detection`);
  }
};

const refreshStreamUrl = async (stream) => {
  try {
    // Skip refresh if stream is offline
    if (stream.status !== 'online') {
      toast.warning(`Cannot refresh offline stream: ${stream.streamer_username}`);
      return;
    }
    
    toast.info(`Refreshing stream for ${stream.streamer_username}...`);
    
    // Determine the API endpoint and payload based on platform
    const endpoint = `/api/refresh/${stream.platform.toLowerCase()}`;
    const payload = stream.platform === 'Chaturbate'
      ? { room_slug: stream.streamer_username }
      : { room_url: stream.room_url };
    
    const response = await axios.post(endpoint, payload);
    
    if (response.data.m3u8_url) {
      // Update the stream URL
      stream.video_url = response.data.m3u8_url;
      
      if (stream.platform === 'Chaturbate') {
        stream.chaturbate_m3u8_url = response.data.m3u8_url;
      } else {
        stream.stripchat_m3u8_url = response.data.m3u8_url;
      }
      
      // Reinitialize player if in grid view
      if (viewMode.value === 'grid') {
        // Clean up existing HLS instance if any
        if (hlsInstances.value[stream.id]) {
          hlsInstances.value[stream.id].destroy();
          delete hlsInstances.value[stream.id];
        }
        
        await nextTick();
        
        // Initialize single mini player
        const videoElement = document.getElementById(`mini-player-${stream.id}`);
        if (videoElement && Hls.isSupported()) {
          const hls = new Hls({
            maxBufferLength: 5,
            maxMaxBufferLength: 10,

          });
          
          hlsInstances.value[stream.id] = hls;
          
          hls.on(Hls.Events.MEDIA_ATTACHED, () => {
            hls.loadSource(stream.video_url);
          });
          
          hls.on(Hls.Events.MANIFEST_PARSED, () => {
            if (hls.levels.length > 1) {
              hls.currentLevel = hls.levels.length - 1; // Use lowest quality
            }
            videoElement.play().catch(() => {});
          });
          
          hls.attachMedia(videoElement);
        }
      }
      
      toast.success(`Stream refreshed for ${stream.streamer_username}`);
    } else {
      toast.error(`Failed to refresh stream for ${stream.streamer_username}`);
    }
  } catch (error) {
    toast.error(`Error refreshing stream: ${error.message}`);
  }
};

const selectStream = (stream) => {
  selectedStream.value = stream;
};

const closePlayer = () => {
  selectedStream.value = null;
};

const formatNumber = (num) => {
  if (num >= 1000000) return `${(num/1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num/1000).toFixed(1)}K`;
  return num;
};

const formatStreamTime = (timestamp) => {
  if (!timestamp) return 'Unknown';
  try {
    return formatDistance(new Date(timestamp), new Date(), { addSuffix: true });
  } catch {
    return 'Unknown';
  }
};

// Watch for view mode changes to initialize mini players when switching to grid
watch(viewMode, (newMode) => {
  if (newMode === 'grid') {
    nextTick(() => {
      initializeMiniPlayers();
    });
  }
});
</script>

<style scoped>
.stream-player-container {
  width: 100%;
  position: relative;
  top: 1rem;
  padding: 0 1rem;
  box-sizing: border-box;
}

/* View Controls */
.view-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.view-controls h2 {
  font-size: 1.5rem;
  margin: 0;
  color: var(--text-color);
}

.controls-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.view-toggle {
  display: flex;
  background-color: var(--input-bg);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle-btn {
  border: none;
  background: transparent;
  padding: 0.6rem 1rem;
  cursor: pointer;
  color: var(--text-light);
  transition: all 0.2s ease;
  font-size: 1rem;
}

.toggle-btn.active {
  background-color: var(--primary-color);
  color: white;
}

.refresh-button {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 50%;
  background-color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  color: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.refresh-button:hover {
  transform: rotate(360deg);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Grid View */
.stream-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.stream-grid-item {
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border-radius: 12px;
  overflow: hidden;
  background-color: var(--card-bg);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
}

.stream-grid-item:hover {
  transform: translateY(-6px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.video-thumbnail {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 aspect ratio */
  overflow: hidden;
  background-color: #000;
}

.player-overlay {
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
  transition: opacity 0.3s ease;
  color: white;
  z-index: 2;
}

.video-thumbnail:hover .player-overlay {
  opacity: 1;
}

.stream-badges {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  z-index: 3;
}

.live-badge {
  background-color: #f44336;
  color: white;
  font-size: 0.75rem;
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
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
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

.detection-badge {
  background-color: #2196F3;
  color: white;
  font-size: 0.75rem;
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.stream-duration {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 0.8rem;
  padding: 3px 8px;
  border-radius: 6px;
  z-index: 3;
}

.stream-info {
  padding: 1.2rem;
}

.stream-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.6rem;
}

.stream-title {
  font-size: 1.1rem;
  margin: 0;
  font-weight: 600;
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-color);
}

.stream-platform {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
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
  font-size: 0.85rem;
  color: var(--text-light);
  margin-bottom: 0.9rem;
}

.stream-controls {
  display: flex;
  gap: 0.6rem;
}

.control-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  border-radius: 6px;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.control-btn:hover {
  filter: brightness(1.1);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
}

/* List View */
.stream-list {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.stream-list-item {
  display: flex;
  align-items: center;
  padding: 1.2rem;
  border-radius: 10px;
  background-color: var(--card-bg);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.stream-list-item:hover {
  background-color: var(--card-bg-hover);
  transform: translateX(5px);
  box-shadow: 0 5px 12px rgba(0, 0, 0, 0.1);
}

.stream-list-item.selected {
  border-left: 5px solid var(--primary-color);
  padding-left: calc(1.2rem - 4px);
  background-color: var(--card-bg-hover);
}

.list-thumbnail {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 50px;
  position: relative;
}

.status-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  position: relative;
}

.status-indicator {
  background-color: #4CAF50;
  box-shadow: 0 0 8px #4CAF50;
}

.status-pulse {
  position: absolute;
  top: -5px;
  left: -5px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background-color: rgba(76, 175, 80, 0.3);
  animation: pulse-ring 2s ease-out infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 0.8; }
  80%, 100% { transform: scale(1.6); opacity: 0; }
}

.list-live-badge {
  position: absolute;
  top: -20px;
  left: 22px;
  font-size: 0.7rem;
  font-weight: bold;
  color: #fff;
  background-color: #f44336;
  padding: 2px 8px;
  border-radius: 4px;
}

.list-info {
  flex-grow: 1;
  margin-left: 1.2rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.list-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.list-title-row h3 {
  margin: 0;
  font-size: 1.05rem;
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
  gap: 1.2rem;
  font-size: 0.85rem;
  color: var(--text-light);
}

.list-detail-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.list-detail-item svg {
  color: var(--primary-color);
  opacity: 0.8;
}

.list-actions {
  margin-left: 1.2rem;
  display: flex;
  gap: 12px;
  align-items: center;
}

.play-btn, .detection-toggle-btn, .refresh-stream-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
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
  transform: scale(1.08);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

/* Light/dark mode specific adjustments */
@media (prefers-color-scheme: dark) {
  .play-btn, .detection-toggle-btn, .refresh-stream-btn {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
  
  .list-detail-item svg {
    color: var(--primary-color);
    opacity: 0.9;
  }
  
  .stream-list-item {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  }
}

@media (prefers-color-scheme: light) {
  .status-indicator {
    box-shadow: 0 0 10px rgba(76, 175, 80, 0.6);
  }
  
  .list-detail-item svg {
    color: var(--primary-color);
    opacity: 0.7;
  }
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
  background-color: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.empty-state svg {
  margin-bottom: 1.5rem;
  font-size: 2.5rem;
  color: var(--text-light);
}

.empty-state p {
  margin-bottom: 1.5rem;
  font-size: 1rem;
}

.empty-state .refresh-btn {
  width: auto;
  height: auto;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  background-color: var(--primary-color);
  color: white;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.empty-state .refresh-btn:hover {
  filter: brightness(1.1);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .stream-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1.2rem;
  }
  
  .list-details {
    gap: 10px;
    flex-wrap: wrap;
  }
  
  .stream-list-item {
    padding: 1rem;
  }
}

@media (max-width: 640px) {
  .list-actions {
    margin-left: 0.8rem;
    gap: 8px;
  }
  
  .play-btn, .detection-toggle-btn, .refresh-stream-btn {
    width: 34px;
    height: 34px;
  }
  
  .list-info {
    margin-left: 0.9rem;
  }
  
  .list-title-row h3 {
    font-size: 0.95rem;
  }
}

@media (max-width: 480px) {
  .view-controls h2 {
    font-size: 1.2rem;
  }
  
  .stream-grid {
    grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
    gap: 1rem;
  }
  
  .stream-list-item {
    flex-direction: column;
    align-items: flex-start;
    padding: 0.9rem;
  }
  
  .list-info {
    width: 100%;
    margin-left: 0;
    margin-top: 0.6rem;
  }
  
  .list-actions {
    margin-top: 0.9rem;
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
    margin-right: 0.6rem;
  }
  
  .list-live-badge {
    position: static;
    margin-left: 0.6rem;
  }
  
  .list-title-row {
    margin-top: 0.6rem;
  }
  
  .list-details {
    margin-top: 0.5rem;
  }
}

/* Mini player styling */
.mini-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  object-fit: fill;
}

/* Streams section styling */
.streams-section {
  padding-top: 0.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  cursor: pointer;
}

.section-header.offline-section {
  margin-top: 2rem;
}

.section-header h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.stream-count {
  background-color: var(--primary-color, #3B82F6);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.collapse-icon {
  margin-left: 0.5rem;
  transition: transform 0.3s ease;
}

.stream-container {
  margin-bottom: 2rem;
}

.live-badge.offline {
  background-color: #757575;
}

.live-dot.offline {
  background-color: #BDBDBD;
  animation: none;
}

.status-indicator.offline {
  background-color: #757575;
}
</style>
