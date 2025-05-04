<template>
  <div class="mobile-stream-card" :class="platformClass">
    <div class="stream-preview" v-if="stream.is_online">
      <mobile-video-player
        :streamUrl="stream.m3u8_url"
        :streamTitle="stream.streamer_username || 'Live Stream'"
        :streamPlatform="stream.platform || 'Unknown'"
        :autoplay="false"
        :muted="true"
        @refresh-request="$emit('refresh')"
        @close="openStreamDetails"
      />
    </div>
    
    <div class="stream-card-content-wrapper">
      <div class="stream-card-content" @click="$emit('click')">
        <div class="stream-header">
          <h3 class="stream-title">{{ stream.streamer_username }}</h3>
          <div class="stream-badge">{{ streamType }}</div>
        </div>
        
        <div class="stream-details">
          <!-- Stream URL -->
          <div class="detail-item">
            <font-awesome-icon icon="link" class="detail-icon" />
            <div class="detail-text url-text" @click.stop="openStreamUrl">
              {{ formatRoomUrl(stream.room_url) }}
            </div>
          </div>
          
          <!-- Assignments -->
          <div class="detail-item">
            <font-awesome-icon icon="users" class="detail-icon" />
            <div class="detail-text">
              {{ assignmentsText }}
            </div>
          </div>
          
          <!-- Stream Status -->
          <div class="detail-item">
            <font-awesome-icon :icon="statusIcon" class="detail-icon" :class="statusClass" />
            <div class="detail-text" :class="statusClass">
              {{ statusText }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="stream-actions">
        <button 
          class="refresh-button" 
          @click.stop="$emit('refresh')"
          :disabled="isRefreshing"
          :class="{ 'refreshing': isRefreshing }"
        >
          <font-awesome-icon icon="sync" :class="{ 'fa-spin': isRefreshing }" />
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
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
    const isStreamActive = computed(() => {
      return props.stream.m3u8_url ? true : false
    })
    
    const statusText = computed(() => {
      return isStreamActive.value ? 'Online' : 'Offline'
    })
    
    const statusIcon = computed(() => {
      return isStreamActive.value ? 'circle' : 'times-circle'
    })
    
    const statusClass = computed(() => {
      return isStreamActive.value ? 'status-online' : 'status-offline'
    })
    
    // Open stream details modal (for video player)
    const openStreamDetails = () => {
      emit('click');
    }
    
    const isDetecting = ref(false)

    const checkDetectionStatus = async () => {
      try {
        const response = await axios.get(`/api/detection-status/${props.stream.id}`);
        isDetecting.value = response.data.active;
        // Ensure detection toggle remains in detecting state if active
        if (response.data.active) {
          isDetecting.value = true;
        }
      } catch (error) {
        console.error('Error checking detection status:', error);
      }
    };

    const toggleDetection = async () => {
      if (isDetecting.value) {
        try {
          await axios.post(`/api/stop-detection/${props.stream.id}`);
          isDetecting.value = false;
          emit('detectionToggled', { streamId: props.stream.id, active: false });
        } catch (error) {
          console.error('Error stopping detection:', error);
          showNotification('Failed to stop detection', 'error');
        }
      } else {
        try {
          const response = await axios.get(`/api/detection-status/${props.stream.id}`);
          if (response.data.active) {
            showNotification('Detection is already active for this stream', 'info');
            isDetecting.value = true;
            return;
          }
          await axios.post(`/api/start-detection/${props.stream.id}`);
          isDetecting.value = true;
          emit('detectionToggled', { streamId: props.stream.id, active: true });
        } catch (error) {
          console.error('Error starting detection:', error);
          showNotification('Failed to start detection', 'error');
        }
      }
    };
    
    return {
      streamType,
      platformClass,
      formatRoomUrl,
      openStreamUrl,
      openStreamDetails,
      assignmentsText,
      statusText,
      statusIcon,
      statusClass,
      isDetecting,
      checkDetectionStatus,
      toggleDetection
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

.stream-preview {
  width: 100%;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

[data-theme='dark'] .stream-preview {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.stream-card-content-wrapper {
  display: flex;
  width: 100%;
}

.stream-card-content {
  flex: 1;
  padding: 15px;
}

.stream-header {
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

.stream-badge {
  font-size: 0.7rem;
  padding: 3px 8px;
  border-radius: 12px;
  background-color: var(--light-secondary);
  color: white;
}

[data-theme='dark'] .stream-badge {
  background-color: var(--dark-secondary);
}

/* Platform-specific styling */
.platform-chaturbate .stream-badge {
  background-color: #f90;
}

.platform-stripchat .stream-badge {
  background-color: #ff0066;
}

.stream-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-rendering: optimizeSpeed; /* Optimize for performance over aesthetics */
}

.detail-item {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  transform: translateZ(0); /* Create a new stacking context for better text rendering */
}

.detail-icon {
  width: 16px;
  margin-right: 10px;
  color: var(--light-text-secondary);
  flex-shrink: 0; /* Prevent icon from shrinking */
}

[data-theme='dark'] .detail-icon {
  color: var(--dark-text-secondary);
}

.detail-text {
  color: var(--light-text-secondary);
  white-space: nowrap; /* Prevent text wrapping for better performance */
  overflow: hidden;
  text-overflow: ellipsis; /* Add ellipsis for overflowing text */
  max-width: 100%; /* Limit text width */
}

[data-theme='dark'] .detail-text {
  color: var(--dark-text-secondary);
}

.url-text {
  color: var(--light-primary);
  cursor: pointer;
}

[data-theme='dark'] .url-text {
  color: var(--dark-primary);
}

.url-text:active {
  opacity: 0.7;
}

/* Status styles */
.status-online {
  color: var(--light-success) !important;
}

[data-theme='dark'] .status-online {
  color: var(--dark-success) !important;
}

.status-offline {
  color: var(--light-danger) !important;
}

[data-theme='dark'] .status-offline {
  color: var(--dark-danger) !important;
}

/* Stream actions */
.stream-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 15px;
  background-color: rgba(0, 0, 0, 0.03);
}

[data-theme='dark'] .stream-actions {
  background-color: rgba(255, 255, 255, 0.03);
}

.refresh-button {
  background: none;
  border: none;
  height: 40px;
  width: 40px;
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

[data-theme='dark'] .refresh-button {
  color: var(--dark-text-secondary);
}

.refresh-button:active {
  background-color: rgba(0, 0, 0, 0.1);
  transform: scale(0.95); /* Slight scale down effect on press */
}

[data-theme='dark'] .refresh-button:active {
  background-color: rgba(255, 255, 255, 0.1);
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important; /* Prevent transform when disabled */
}

.refresh-button.refreshing {
  color: var(--light-primary);
}

[data-theme='dark'] .refresh-button.refreshing {
  color: var(--dark-primary);
}

/* Optimized spin animation for the refresh icon */
@keyframes optimized-spin {
  to { transform: rotate(360deg); }
}

.refresh-button .fa-spin {
  animation: optimized-spin 1s linear infinite;
}
</style>