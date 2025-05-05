<template>
  <div v-if="show" class="video-player-modal">
    <div v-if="stream" class="modal-overlay" @click="closeModal"></div>
    <div class="modal-content">
      <div v-if="stream">
        <!-- Modal Header -->
        <div class="modal-header">
          <div class="modal-title">
            <h3>{{ stream.streamer_username }}</h3>
            <div class="stream-platform" :class="stream.platform?.toLowerCase()">
              {{ stream.platform }}
            </div>
            <div class="stream-status-badge">
              <span :class="isOnline ? 'live-dot' : 'offline-dot'"></span>
              {{ isOnline ? 'LIVE' : 'OFFLINE' }}
            </div>
          </div>
          <button class="close-btn" @click="closeModal">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        
        <!-- Video Player -->
        <div class="video-container">
          <div v-if="isOnline" class="video-player">
            <div class="full-player">
              <video 
                ref="videoPlayer" 
                class="full-video-player" 
                playsinline
                autoplay
              ></video>
              <button 
                v-if="!isPlaying" 
                class="play-overlay-btn"
                @click="startPlayback"
              >
                <font-awesome-icon icon="play" size="3x" />
              </button>
            </div>
          </div>
          <div v-else class="offline-overlay">
            <div class="offline-content">
              <font-awesome-icon icon="satellite-dish" class="offline-icon" />
              <h3>Stream Offline</h3>
              <p>This stream is currently not broadcasting</p>
            </div>
          </div>
        </div>
        
        <!-- Stream Metadata -->
        <div class="stream-metadata">
          <div class="meta-row">
            <div class="platform-badge" :class="stream.platform?.toLowerCase()">
              {{ stream.platform }}
            </div>
            <div class="viewer-count">
              <font-awesome-icon icon="eye" /> {{ formatNumber(stream.viewer_count || 0) }} viewers
            </div>
          </div>
          <div class="meta-row">
            <div class="stream-time">
              <font-awesome-icon icon="clock" /> 
              Streaming {{ formatStreamTime(stream.stream_start_time) }}
            </div>
            <div class="status-group">
              <div class="live-status">
                <span :class="isOnline ? 'live-dot' : 'offline-dot'"></span>
                {{ isOnline ? 'LIVE' : 'OFFLINE' }}
              </div>
              <div v-if="stream.detection_status" class="detection-status">
                {{ stream.detection_status }}
              </div>
            </div>
          </div>
          <div class="detection-controls">
            <button 
              class="detection-trigger-btn" 
              :class="{ 'active': stream.detection_active }"
              @click="toggleDetection"
              :disabled="!isOnline"
            >
              <font-awesome-icon :icon="stream.detection_active ? 'stop' : 'play'" />
              {{ stream.detection_active ? 'Stop Detection' : isOnline ? 'Start Detection' : 'Stream Offline' }}
            </button>
            <button class="refresh-stream-btn" @click="refreshStream" :disabled="!isOnline">
              <font-awesome-icon icon="sync" />
              Refresh Stream
            </button>
          </div>
          <div class="stream-url">
            <p><strong>Room URL:</strong> <a :href="stream.room_url" target="_blank">{{ stream.room_url }}</a></p>
          </div>
        </div>
      </div>
      <div v-else>
        <p>No stream selected</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, watch, defineEmits, defineProps, computed } from 'vue';
import { formatDistance } from 'date-fns';
import Hls from 'hls.js';
import { useToast } from 'vue-toastification';
import axios from 'axios';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  stream: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits([
  'close', 
  'toggle-detection', 
  'refresh-stream'
]);

const videoPlayer = ref(null);
const isPlaying = ref(false);
const hlsInstance = ref(null);

const toast = useToast();

// Add computed property for online status
const isOnline = computed(() => props.stream?.status === 'online');

// Watch for changes in the show prop to initialize player when modal opens
watch(() => props.show, (newValue) => {
  if (newValue === true) {
    // Initialize player when modal is shown
    setTimeout(() => {
      initializePlayer();
    }, 100);
  } else {
    // Cleanup when modal is closed
    destroyPlayer();
  }
});

// Watch for changes in the stream's video URL
watch(
  () => props.stream?.video_url,
  (newUrl) => {
    if (newUrl && props.show) {
      // Reinitialize player when stream URL changes
      destroyPlayer();
      initializePlayer();
    }
  }
);

// Add watcher for online status changes
watch(() => props.stream?.status, (newStatus) => {
  if (newStatus !== 'online') {
    destroyPlayer();
  }
});

// Initialize the video player
const initializePlayer = () => {
  if (!isOnline.value) {
    destroyPlayer();
    return;
  }
  
  if (!videoPlayer.value || !props.stream?.video_url) return;

  if (Hls.isSupported()) {
    const hls = new Hls({
      enableWorker: true,
      lowLatencyMode: true,
      maxBufferSize: 30 * 1000, // 30 seconds
    });

    hlsInstance.value = hls;

    hls.on(Hls.Events.ERROR, (event, data) => {
      if (data.fatal) {
        switch(data.type) {
          case Hls.ErrorTypes.NETWORK_ERROR:
            hls.startLoad();
            break;
          case Hls.ErrorTypes.MEDIA_ERROR:
            hls.recoverMediaError();
            break;
          default:
            destroyPlayer();
            initializePlayer();
            break;
        }
      }
    });

    hls.on(Hls.Events.MEDIA_ATTACHED, () => {
      hls.loadSource(props.stream.video_url);
    });

    hls.attachMedia(videoPlayer.value);
  } else if (videoPlayer.value.canPlayType('application/vnd.apple.mpegurl')) {
    // Native HLS support (Safari)
    videoPlayer.value.src = props.stream.video_url;
  }
};

// Destroy HLS instance when component unmounts
const destroyPlayer = () => {
  if (hlsInstance.value) {
    hlsInstance.value.destroy();
    hlsInstance.value = null;
  }
  
  if (videoPlayer.value) {
    videoPlayer.value.pause();
    videoPlayer.value.removeAttribute('src');
    videoPlayer.value.load();
  }
  
  isPlaying.value = false;
};

// Start playback with audio unmuted
const startPlayback = () => {
  if (videoPlayer.value) {
    videoPlayer.value.muted = false;
    videoPlayer.value.controls = true;
    videoPlayer.value.play()
      .then(() => {
        isPlaying.value = true;
      })
      .catch(error => {
        console.error('Playback error:', error);
      });
  }
};

// Close the modal
const closeModal = () => {
  destroyPlayer();
  emit('close');
};

// Toggle detection for stream
const toggleDetection = () => {
  if (!isOnline.value) {
    toast.warning('Cannot toggle detection on offline stream');
    return;
  }
  emit('toggle-detection', props.stream);
};

// Refresh stream URL
const refreshStream = async () => {
  if (!isOnline.value) {
    toast.warning('Cannot refresh offline stream');
    return;
  }

  try {
    toast.info(`Refreshing ${props.stream.platform} stream...`);
    
    // Determine endpoint and payload based on platform
    const platform = props.stream.platform.toLowerCase();
    let endpoint, payload;

    if (platform === 'chaturbate') {
      endpoint = '/api/refresh/chaturbate';
      // Extract room slug from URL (last part of the URL)
      const roomSlug = props.stream.room_url.split('/').filter(Boolean).pop();
      payload = { room_slug: roomSlug };
    } else if (platform === 'stripchat') {
      endpoint = '/api/refresh/stripchat';
      payload = { room_url: props.stream.room_url };
    } else {
      throw new Error('Unsupported platform');
    }

    const response = await axios.post(endpoint, payload);
    
    if (response.data.m3u8_url) {
      // Update the stream URL in parent component
      emit('refresh-stream', {
        ...props.stream,
        video_url: response.data.m3u8_url
      });
      
      // Reinitialize player with new URL
      destroyPlayer();
      initializePlayer();
      
      toast.success('Stream refreshed successfully');
    } else {
      throw new Error('No M3U8 URL returned');
    }
  } catch (error) {
    console.error('Refresh error:', error);
    toast.error(`Failed to refresh stream: ${error.response?.data?.message || error.message}`);
  }
};

// Format number for display (e.g., 1000 -> 1K)
const formatNumber = (num) => {
  if (num >= 1000000) return `${(num/1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num/1000).toFixed(1)}K`;
  return num;
};

// Format stream time as relative time
const formatStreamTime = (timestamp) => {
  if (!timestamp) return 'Unknown';
  try {
    return formatDistance(new Date(timestamp), new Date(), { addSuffix: true });
  } catch {
    return 'Unknown';
  }
};

// Cleanup on component unmount
onUnmounted(() => {
  destroyPlayer();
});
</script>

<style scoped>
.video-player-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(5px);
}

.modal-content {
  position: relative;
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  background-color: #1a1a1a;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: modal-in 0.3s ease-out;
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background-color: #232323;
  border-bottom: 1px solid #333;
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-title h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #fff;
  font-weight: 600;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stream-platform {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #fff;
}

.stream-platform.chaturbate {
  background-color: #f47321;
}

.stream-platform.stripchat {
  background-color: #16a0d6;
}

.stream-status-badge {
  display: flex;
  align-items: center;
  padding: 4px 10px;
  background-color: v-bind('isOnline ? "#dc2626" : "#6b7280"');
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
}

.live-dot {
  width: 8px;
  height: 8px;
  background-color: #dc2626;
  border-radius: 50%;
  margin-right: 5px;
  animation: pulse 1.5s infinite;
}

.offline-dot {
  background-color: #6b7280;
  animation: none;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

.close-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 1.25rem;
  cursor: pointer;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.video-container {
  position: relative;
  width: 100%;
  background-color: #000;
  aspect-ratio: 16 / 9;
}

.video-player {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.full-player {
  position: relative;
  width: 100%;
  height: 100%;
}

.full-video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background-color: #000;
}

.play-overlay-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.6);
  color: #fff;
  border: none;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.play-overlay-btn:hover {
  background-color: rgba(220, 38, 38, 0.8);
  transform: translate(-50%, -50%) scale(1.1);
}

.stream-metadata {
  padding: 16px 20px;
  background-color: #232323;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  align-items: center;
}

.platform-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #fff;
}

.viewer-count {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: #e5e5e5;
}

.stream-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: #e5e5e5;
}

.status-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.live-status {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
}

.detection-status {
  padding: 3px 8px;
  background-color: #2563eb;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #fff;
}

.detection-controls {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  margin-bottom: 16px;
}

.detection-trigger-btn,
.refresh-stream-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  }

.detection-trigger-btn {
  background-color: #2563eb;
  color: #fff;
}

.detection-trigger-btn:hover {
  background-color: #1d4ed8;
}

.detection-trigger-btn.active {
  background-color: #dc2626;
}

.detection-trigger-btn.active:hover {
  background-color: #b91c1c;
}

.refresh-stream-btn {
  background-color: #374151;
  color: #fff;
}

.refresh-stream-btn:hover {
  background-color: #4b5563;
}

.stream-url {
  margin-top: 12px;
  color: #a3a3a3;
  font-size: 0.9rem;
}

.stream-url a {
  color: #60a5fa;
  text-decoration: none;
}

.stream-url a:hover {
  text-decoration: underline;
}

.offline-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  text-align: center;
  z-index: 2;
}

.offline-content {
  padding: 2rem;
  max-width: 300px;
}

.offline-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.7;
}

.detection-trigger-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #6b7280 !important;
}

@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 95vh;
  }
  
  .modal-title {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .detection-controls {
    flex-direction: column;
  }
}
</style>
