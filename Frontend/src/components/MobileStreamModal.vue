<template>
  <div class="stream-modal-container" :class="{ 'is-open': isVisible }">
    <div v-if="isVisible" class="modal-backdrop" @click="closeModal"></div>
    
    <div class="stream-modal" :class="{ 'is-open': isVisible }">
      <div class="modal-header">
        <h3 v-if="stream">
          {{ stream.streamer_username || 'Live Stream' }} 
          <span class="platform-badge">{{ stream.platform }}</span>
        </h3>
        <button class="close-button" @click="closeModal">
          <font-awesome-icon icon="times" />
        </button>
      </div>
      
      <div class="modal-body">
        <div v-if="loading" class="loading-container">
          <div class="spinner">
            <font-awesome-icon icon="spinner" spin />
          </div>
          <p>Loading stream...</p>
        </div>
        
        <div v-else-if="error" class="error-container">
          <font-awesome-icon icon="exclamation-circle" class="error-icon" />
          <p>{{ error }}</p>
          <button class="retry-button" @click="loadStream">Retry</button>
        </div>
        
        <div v-else-if="!stream" class="no-stream-container">
          <font-awesome-icon icon="video-slash" class="no-stream-icon" />
          <p>No stream selected</p>
        </div>
        
        <div v-else class="stream-container">
          <div class="video-container">
            <video ref="videoPlayer" class="video-player" controls playsinline></video>
          </div>
          
          <div class="stream-info">
            <div class="stream-details">
              <div class="detail-item">
                <span class="detail-label">Streamer:</span>
                <span class="detail-value">{{ stream.streamer_username }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Platform:</span>
                <span class="detail-value">{{ stream.platform }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">URL:</span>
                <a :href="stream.room_url" target="_blank" rel="noopener noreferrer" class="detail-value link">
                  {{ formatUrl(stream.room_url) }}
                </a>
              </div>
            </div>
            
            <div class="action-buttons">
              <button class="action-button detection-button" @click="triggerDetection">
                <font-awesome-icon icon="magnifying-glass" />
                <span>Run Detection</span>
              </button>
              
              <button class="action-button refresh-button" @click="loadStream">
                <font-awesome-icon icon="sync-alt" />
                <span>Refresh Stream</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, onBeforeUnmount, inject } from 'vue';
import { useToast } from 'vue-toastification';
import mobileStreamService from '../services/MobileStreamService';

export default {
  name: 'MobileStreamModal',
  props: {
    isVisible: {
      type: Boolean,
      default: false
    },
    streamId: {
      type: Number,
      default: null
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    // State
    const videoPlayer = ref(null);
    const stream = ref(null);
    const loading = ref(false);
    const error = ref(null);
    const detectionInProgress = ref(false);
    
    // Toast for notifications
    const toast = useToast();
    
    // Get context help function from global context
    const analyzeContext = inject('analyzeContext', null);
    
    // Methods
    const closeModal = () => {
      // Stop playback when modal is closed
      stopPlayback();
      emit('close');
    };
    
    const loadStream = async () => {
      if (!props.streamId) {
        stream.value = null;
        return;
      }
      
      loading.value = true;
      error.value = null;
      
      try {
        // Use MobileStreamService to fetch and select the stream
        await mobileStreamService.selectStream(props.streamId);
        stream.value = mobileStreamService.currentStream.value;
        
        // Wait for DOM to update
        setTimeout(() => {
          if (videoPlayer.value && stream.value) {
            startPlayback();
          }
        }, 100);
      } catch (err) {
        console.error('Failed to load stream:', err);
        const errorMsg = 'Failed to load stream. Please try again.';
        error.value = errorMsg;
        
        // Show help bubble for stream loading error
        if (analyzeContext) {
          analyzeContext({
            screen: 'stream_modal',
            action: 'error',
            error: {
              type: 'load_error',
              message: errorMsg,
              details: err.message || 'Connection error'
            },
            streamId: props.streamId
          });
        }
      } finally {
        loading.value = false;
      }
    };
    
    const startPlayback = () => {
      if (!videoPlayer.value || !stream.value) return;
      
      try {
        mobileStreamService.startPlayback(videoPlayer.value);
        
        // Show help about playback controls if it's the first time
        if (analyzeContext && !localStorage.getItem('playback_help_shown')) {
          analyzeContext({
            screen: 'stream_modal',
            action: 'playback_started',
            isFirstTime: true,
            streamData: {
              platform: stream.value.platform || 'unknown'
            }
          });
          
          // Mark that playback help has been shown
          localStorage.setItem('playback_help_shown', 'true');
        }
      } catch (err) {
        console.error('Failed to start playback:', err);
        const errorMsg = 'Failed to start playback. Please try again.';
        error.value = errorMsg;
        
        // Show help bubble for playback error
        if (analyzeContext) {
          analyzeContext({
            screen: 'stream_modal',
            action: 'error',
            error: {
              type: 'playback_error',
              message: errorMsg,
              details: err.message || 'Playback initialization error'
            },
            streamData: {
              id: props.streamId,
              platform: stream.value ? stream.value.platform : 'unknown'
            }
          });
        }
      }
    };
    
    const stopPlayback = () => {
      mobileStreamService.stopPlayback();
      
      // Clear video source
      if (videoPlayer.value) {
        videoPlayer.value.src = '';
        videoPlayer.value.load();
      }
    };
    
    const triggerDetection = async () => {
      if (detectionInProgress.value) {
        toast.info('Detection already in progress...');
        return;
      }
      
      detectionInProgress.value = true;
      
      try {
        const result = await mobileStreamService.triggerDetection();
        
        if (result.success) {
          toast.success('Detection started successfully');
          
          // Show help about detection process if it's the first time
          if (analyzeContext && !localStorage.getItem('detection_help_shown')) {
            analyzeContext({
              screen: 'stream_modal',
              action: 'detection_started',
              isFirstTime: true,
              streamData: {
                platform: stream.value.platform || 'unknown'
              }
            });
            
            // Mark that detection help has been shown
            localStorage.setItem('detection_help_shown', 'true');
          }
        } else {
          const errorMsg = result.message || 'Failed to start detection';
          toast.error(errorMsg);
          
          // Show help bubble for detection error
          if (analyzeContext) {
            analyzeContext({
              screen: 'stream_modal',
              action: 'error',
              error: {
                type: 'detection_error',
                message: errorMsg
              },
              streamData: {
                id: props.streamId,
                platform: stream.value ? stream.value.platform : 'unknown'
              }
            });
          }
        }
      } catch (err) {
        console.error('Detection error:', err);
        const errorMsg = 'Failed to run detection. Please try again.';
        toast.error(errorMsg);
        
        // Show help bubble for detection error
        if (analyzeContext) {
          analyzeContext({
            screen: 'stream_modal',
            action: 'error',
            error: {
              type: 'detection_error',
              message: errorMsg,
              details: err.message || 'API connection error'
            },
            streamData: {
              id: props.streamId,
              platform: stream.value ? stream.value.platform : 'unknown'
            }
          });
        }
      } finally {
        detectionInProgress.value = false;
      }
    };
    
    const formatUrl = (url) => {
      if (!url) return '';
      
      try {
        const urlObj = new URL(url);
        // Return just the hostname + pathname for cleaner display
        return `${urlObj.hostname}${urlObj.pathname}`;
      } catch (e) {
        return url;
      }
    };
    
    // Watchers
    watch(() => props.streamId, (newStreamId) => {
      if (newStreamId && props.isVisible) {
        loadStream();
      } else if (!newStreamId) {
        stream.value = null;
      }
    });
    
    watch(() => props.isVisible, (isVisible) => {
      if (isVisible && props.streamId) {
        loadStream();
        
        // Show context help when modal is opened
        if (analyzeContext) {
          // Check if this is first time viewing a stream
          const isFirstTimeViewingStream = !localStorage.getItem('stream_modal_viewed');
          
          analyzeContext({
            screen: 'stream_modal',
            action: 'view',
            isFirstTime: isFirstTimeViewingStream,
            streamData: {
              id: props.streamId
            }
          });
          
          // Mark that stream modal has been viewed
          localStorage.setItem('stream_modal_viewed', 'true');
        }
      } else if (!isVisible) {
        stopPlayback();
      }
    });
    
    // Lifecycle hooks
    onMounted(() => {
      if (props.isVisible && props.streamId) {
        loadStream();
      }
    });
    
    onBeforeUnmount(() => {
      stopPlayback();
    });
    
    return {
      videoPlayer,
      stream,
      loading,
      error,
      detectionInProgress,
      closeModal,
      loadStream,
      triggerDetection,
      formatUrl
    };
  }
};
</script>

<style scoped>
.stream-modal-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stream-modal-container.is-open {
  opacity: 1;
  pointer-events: auto;
}

.modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(2px);
  z-index: 1;
}

.stream-modal {
  position: relative;
  z-index: 2;
  width: 96%;
  max-width: 500px;
  max-height: 90vh;
  background-color: var(--bs-body-bg);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transform: translateY(20px);
  opacity: 0;
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.stream-modal.is-open {
  transform: translateY(0);
  opacity: 1;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--bs-border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.platform-badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 0.8rem;
  background-color: var(--bs-primary);
  color: white;
  border-radius: 12px;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: var(--bs-secondary);
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  transition: background-color 0.2s;
}

.close-button:hover {
  background-color: var(--bs-secondary-bg);
  color: var(--bs-primary);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-container,
.error-container,
.no-stream-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
  gap: 16px;
}

.spinner {
  font-size: 2rem;
  color: var(--bs-primary);
}

.error-icon,
.no-stream-icon {
  font-size: 2.5rem;
  color: var(--bs-danger);
  margin-bottom: 8px;
}

.no-stream-icon {
  color: var(--bs-secondary);
}

.retry-button {
  background-color: var(--bs-primary);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.retry-button:hover {
  filter: brightness(0.9);
}

.stream-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.video-container {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 aspect ratio */
}

.video-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: #000;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.stream-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stream-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background-color: var(--bs-tertiary-bg);
  border-radius: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
}

.detail-label {
  font-weight: 600;
  min-width: 80px;
}

.detail-value {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-value.link {
  color: var(--bs-primary);
  text-decoration: none;
}

.detail-value.link:hover {
  text-decoration: underline;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.action-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.detection-button {
  background-color: var(--bs-primary);
  color: white;
}

.detection-button:hover {
  filter: brightness(0.9);
}

.refresh-button {
  background-color: var(--bs-secondary-bg);
  color: var(--bs-body-color);
}

.refresh-button:hover {
  filter: brightness(0.95);
}

/* Fix for iOS Safari to show proper video controls */
@media not all and (min-resolution:.001dpcm) { 
  @supports (-webkit-appearance:none) {
    .video-player {
      -webkit-appearance: none;
    }
  }
}
</style>