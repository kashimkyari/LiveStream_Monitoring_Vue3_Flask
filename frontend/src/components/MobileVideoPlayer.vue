<template>
  <div class="mobile-video-player" :class="{ 'is-loading': loading, 'has-error': error, 'is-fullscreen': isFullscreen }">
    <!-- Video Container -->
    <div ref="videoContainer" class="video-container">
      <video
        ref="videoElement"
        class="video-element"
        playsinline
        @click="togglePlay"
      ></video>
      
      <!-- Loading Spinner -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">Loading stream...</div>
      </div>

      <!-- Error Overlay -->
      <div v-if="error" class="error-overlay">
        <div class="error-icon">
          <font-awesome-icon icon="exclamation-triangle" />
        </div>
        <div class="error-message">{{ error }}</div>
        <button @click="refresh" class="retry-button">
          <font-awesome-icon icon="sync" :class="{ 'rotating': refreshing }" />
          Retry
        </button>
      </div>
      
      <!-- Play Button Overlay -->
      <div v-if="!loading && !isPlaying && !error" class="play-overlay" @click="play">
        <div class="play-button">
          <font-awesome-icon icon="play" />
        </div>
      </div>
      
      <!-- Controls Overlay -->
      <div class="controls-overlay" @click.stop>
        <div class="top-controls">
          <div class="stream-info">
            <div class="stream-title">{{ streamTitle }}</div>
            <div class="stream-platform">{{ streamPlatform }}</div>
          </div>
          
          <div class="control-buttons">
            <button v-if="isFullscreen" @click="exitFullscreen" class="control-button">
              <font-awesome-icon icon="compress" />
            </button>
            <button v-else @click="enterFullscreen" class="control-button">
              <font-awesome-icon icon="expand" />
            </button>
            <button @click="refresh" class="control-button">
              <font-awesome-icon icon="sync" :class="{ 'rotating': refreshing }" />
            </button>
            <button @click="close" class="control-button">
              <font-awesome-icon icon="times" />
            </button>
          </div>
        </div>
        
        <div class="bottom-controls">
          <button @click="togglePlay" class="control-button play-button">
            <font-awesome-icon :icon="isPlaying ? 'pause' : 'play'" />
          </button>
          
          <div class="stream-time">
            <div class="live-indicator" :class="{ 'is-live': isLive }">
              <span class="live-dot"></span>
              LIVE
            </div>
          </div>
          
          <div class="volume-control">
            <button @click="toggleMute" class="control-button">
              <font-awesome-icon :icon="isMuted ? 'volume-mute' : 'volume-up'" />
            </button>
          </div>
        </div>
      </div>
      
      
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import Hls from 'hls.js';

export default {
  name: 'MobileVideoPlayer',
  
  props: {
    streamUrl: {
      type: String,
      required: true
    },
    streamTitle: {
      type: String,
      default: 'Live Stream'
    },
    streamPlatform: {
      type: String,
      default: 'Unknown'
    },
    autoplay: {
      type: Boolean,
      default: false
    },
    muted: {
      type: Boolean,
      default: true
    }
  },
  
  emits: ['close', 'error', 'refresh-request'],
  
  setup(props, { emit }) {
    const videoElement = ref(null);
    const videoContainer = ref(null);
    const hls = ref(null);
    const loading = ref(true);
    const error = ref(null);
    const isPlaying = ref(false);
    const isMuted = ref(props.muted);
    const isFullscreen = ref(false);
    const isLive = ref(true);
    const refreshing = ref(false);
    
    // Initialize HLS.js player
    const initPlayer = () => {
      if (!videoElement.value) return;
      
      loading.value = true;
      error.value = null;
      
      // Destroy existing HLS instance if it exists
      if (hls.value) {
        hls.value.destroy();
      }
      
      // Check if the browser natively supports HLS
      if (videoElement.value.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (Safari)
        videoElement.value.src = props.streamUrl;
        videoElement.value.addEventListener('loadedmetadata', onVideoLoaded);
        videoElement.value.addEventListener('error', onVideoError);
      } else if (Hls.isSupported()) {
        // Use HLS.js
        hls.value = new Hls({
          debug: false,
          startLevel: 0,
          capLevelToPlayerSize: true,
          maxBufferLength: 30,
          maxMaxBufferLength: 60
        });
        
        hls.value.attachMedia(videoElement.value);
        
        hls.value.on(Hls.Events.MEDIA_ATTACHED, () => {
          hls.value.loadSource(props.streamUrl);
        });
        
        hls.value.on(Hls.Events.MANIFEST_PARSED, () => {
          onVideoLoaded();
        });
        
        hls.value.on(Hls.Events.ERROR, (event, data) => {
          if (data.fatal) {
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                // Try to recover network error
                hls.value.startLoad();
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                // Try to recover media error
                hls.value.recoverMediaError();
                break;
              default:
                // Cannot recover
                onVideoError(data);
                break;
            }
          }
        });
      } else {
        // HLS not supported
        onVideoError('HLS playback is not supported in this browser.');
      }
      
      // Set initial muted state
      videoElement.value.muted = isMuted.value;
    };
    
    // Video loaded handler
    const onVideoLoaded = () => {
      loading.value = false;
      
      if (props.autoplay) {
        play();
      }
    };
    
    // Video error handler
    const onVideoError = (e) => {
      loading.value = false;
      console.error('Video playback error:', e);
      
      if (typeof e === 'string') {
        error.value = e;
      } else {
        error.value = 'Error loading stream. Please try again.';
      }
      
      emit('error', error.value);
    };
    
    // Play the video
    const play = () => {
      if (!videoElement.value || loading.value || error.value) return;
      
      const playPromise = videoElement.value.play();
      
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            isPlaying.value = true;
          })
          .catch(e => {
            console.error('Play was prevented:', e);
            
            // If autoplay with sound is blocked, try again with mute
            if (!isMuted.value) {
              isMuted.value = true;
              videoElement.value.muted = true;
              play();
            }
          });
      }
    };
    
    // Pause the video
    const pause = () => {
      if (!videoElement.value || loading.value) return;
      
      videoElement.value.pause();
      isPlaying.value = false;
    };
    
    // Toggle play/pause
    const togglePlay = () => {
      if (isPlaying.value) {
        pause();
      } else {
        play();
      }
    };
    
    // Toggle mute
    const toggleMute = () => {
      if (!videoElement.value) return;
      
      isMuted.value = !isMuted.value;
      videoElement.value.muted = isMuted.value;
    };
    
    // Enter fullscreen
    const enterFullscreen = () => {
      if (!videoContainer.value) return;
      
      try {
        if (videoContainer.value.requestFullscreen) {
          videoContainer.value.requestFullscreen();
        } else if (videoContainer.value.webkitRequestFullscreen) {
          videoContainer.value.webkitRequestFullscreen();
        } else if (videoContainer.value.msRequestFullscreen) {
          videoContainer.value.msRequestFullscreen();
        }
      } catch (e) {
        console.error('Fullscreen API error:', e);
      }
    };
    
    // Exit fullscreen
    const exitFullscreen = () => {
      try {
        if (document.exitFullscreen) {
          document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
          document.msExitFullscreen();
        }
      } catch (e) {
        console.error('Fullscreen API error:', e);
      }
    };
    
    // Handle fullscreen change event
    const handleFullscreenChange = () => {
      isFullscreen.value = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.msFullscreenElement
      );
    };
    
    // Refresh the stream
    const refresh = () => {
      refreshing.value = true;
      emit('refresh-request');
      
      // Re-initialize player with the current streamUrl
      initPlayer();
      
      // Reset refreshing state after a delay
      setTimeout(() => {
        refreshing.value = false;
      }, 1000);
    };
    
    // Retry on error
    const retry = () => {
      initPlayer();
    };
    
    // Close the player
    const close = () => {
      pause();
      emit('close');
    };
    
    // Clean up player on component unmount
    const cleanup = () => {
      if (videoElement.value) {
        videoElement.value.removeEventListener('loadedmetadata', onVideoLoaded);
        videoElement.value.removeEventListener('error', onVideoError);
      }
      
      if (hls.value) {
        hls.value.destroy();
        hls.value = null;
      }
      
      // Remove fullscreen event listeners
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('msfullscreenchange', handleFullscreenChange);
    };
    
    // Initialize component
    onMounted(() => {
      // Add fullscreen event listeners
      document.addEventListener('fullscreenchange', handleFullscreenChange);
      document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.addEventListener('msfullscreenchange', handleFullscreenChange);
      
      // Initialize player
      initPlayer();
    });
    
    // Clean up on unmount
    onBeforeUnmount(cleanup);
    
    // Watch for changes to streamUrl
    watch(() => props.streamUrl, (newUrl, oldUrl) => {
      if (newUrl !== oldUrl) {
        initPlayer();
      }
    });
    
    // Return public methods and state
    return {
      videoElement,
      videoContainer,
      loading,
      error,
      isPlaying,
      isMuted,
      isFullscreen,
      isLive,
      refreshing,
      play,
      pause,
      togglePlay,
      toggleMute,
      enterFullscreen,
      exitFullscreen,
      refresh,
      retry,
      close
    };
  }
};
</script>

<style scoped>
.mobile-video-player {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 aspect ratio */
  background-color: #000;
  border-radius: 8px;
  overflow: hidden;
}

.mobile-video-player.is-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  padding-bottom: 0;
  z-index: 9999;
}

.video-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Loading Overlay */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 10;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 3px solid #fff;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

.loading-text {
  color: #fff;
  font-size: 14px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error Overlay */
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 10;
  padding: 20px;
  text-align: center;
}

.error-icon {
  font-size: 36px;
  color: #ff5252;
  margin-bottom: 15px;
}

.error-message {
  color: #fff;
  font-size: 14px;
  margin-bottom: 20px;
  max-width: 80%;
}

.retry-button {
  background-color: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #fff;
  border-radius: 4px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
}

.retry-button:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

/* Animation for the rotating refresh icon */
.rotating {
  animation: spin 1s linear infinite;
}

/* Play Button Overlay */
.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.3);
  z-index: 10;
}

.play-button {
  width: 60px;
  height: 60px;
  background-color: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  color: #fff;
  cursor: pointer;
  transition: transform 0.1s ease-in-out;
}

.play-button:hover {
  transform: scale(1.1);
}

/* Controls Overlay */
.controls-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10px;
  box-sizing: border-box;
  background: linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 70%, rgba(0,0,0,0.7) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 5;
}

.mobile-video-player:hover .controls-overlay,
.mobile-video-player.is-fullscreen .controls-overlay {
  opacity: 1;
}

.top-controls, .bottom-controls {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stream-info {
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.stream-title {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 3px;
}

.stream-platform {
  font-size: 12px;
  opacity: 0.8;
}

.control-buttons {
  display: flex;
}

.control-button {
  background: none;
  border: none;
  color: #fff;
  font-size: 16px;
  padding: 5px 10px;
  cursor: pointer;
  transition: transform 0.1s ease-in-out;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.control-button:hover {
  transform: scale(1.1);
}

.control-button.play-button {
  font-size: 18px;
}

.bottom-controls .control-button {
  width: 40px;
  height: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.stream-time {
  display: flex;
  align-items: center;
  color: #fff;
  font-size: 12px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.live-indicator {
  display: flex;
  align-items: center;
  padding: 3px 8px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 10px;
  font-weight: bold;
}

.live-indicator.is-live {
  background-color: rgba(255, 0, 0, 0.7);
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #ccc;
  margin-right: 5px;
}

.live-indicator.is-live .live-dot {
  background-color: #fff;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

/* Error Overlay */
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.8);
  z-index: 10;
  padding: 20px;
  text-align: center;
  box-sizing: border-box;
}

.error-icon {
  font-size: 36px;
  color: #ff5252;
  margin-bottom: 15px;
}

.error-message {
  color: #fff;
  font-size: 14px;
  margin-bottom: 20px;
  max-width: 80%;
}

.retry-button {
  padding: 8px 16px;
  background-color: #2196f3;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.retry-button svg {
  margin-right: 5px;
}

/* Utility */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Mobile-specific adjustments */
@media (max-width: 768px) {
  .control-button {
    padding: 5px;
  }
  
  .stream-title {
    font-size: 12px;
  }
  
  .stream-platform {
    font-size: 10px;
  }
  
  .error-icon {
    font-size: 30px;
  }
  
  .error-message {
    font-size: 12px;
  }
}
</style>