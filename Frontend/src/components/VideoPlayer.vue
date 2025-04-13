<template>
  <div class="video-container">
    <!-- Loading State -->
    <div v-if="loading" class="loading-message">
      <div class="loading-spinner"></div>
      <span>Loading stream...</span>
    </div>
    
    <!-- Offline State -->
    <div v-else-if="!loading && !isOnline" class="error-message">
      <div class="error-icon">⚠️</div>
      <div>{{ platform }} stream is offline.</div>
      <button class="retry-button" @click="refreshStream">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="16" height="16">
          <path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
        </svg>
        Retry
      </button>
    </div>
    
    <!-- Thumbnail View (optional) -->
    <div 
      v-else-if="!loading && isOnline && thumbnail && !isModalOpen" 
      class="thumbnail-wrapper"
      @click="toggleModal"
    >
      <img
        :src="thumbnail"
        alt="Live stream thumbnail"
        class="thumbnail-image"
        @error="handleThumbnailError"
      />
      <div class="thumbnail-live-indicator">
        <div class="red-dot"></div>
        <span>LIVE</span>
      </div>
    </div>
    
    <!-- Inline Player -->
    <template v-else-if="!loading && isOnline && !isModalOpen">
      <hls-player
        v-if="m3u8Url"
        :m3u8-url="m3u8Url"
        :poster-url="posterUrl"
        :platform="platform"
        :streamer-name="streamerName"
        :is-modal-open="false"
        @refresh-stream="refreshStream"
        class="inline-player"
      />
      <div v-else class="error-message">No valid stream URL for {{ platform }}.</div>
    </template>

    <!-- Modal Player -->
    <teleport to="body">
      <div v-if="isModalOpen" class="modal-overlay" @click="toggleModal">
        <div class="modal-content" @click.stop>
          <hls-player
            v-if="m3u8Url"
            :m3u8-url="m3u8Url"
            :poster-url="posterUrl"
            :platform="platform"
            :streamer-name="streamerName"
            :is-modal-open="true"
            @refresh-stream="refreshStream"
          />
          <button class="close-modal" @click="toggleModal">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="24" height="24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script>
import { ref, onMounted, defineComponent, watch, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { useToast } from 'vue-toastification';

// HLS Player Component
const HlsPlayer = defineComponent({
  name: 'HlsPlayer',
  props: {
    m3u8Url: { type: String, required: true },
    isModalOpen: { type: Boolean, default: false },
    posterUrl: { type: String, default: null },
    platform: { type: String, required: true },
    streamerName: { type: String, required: true }
  },
  emits: ['refresh-stream'],
  setup(props, { emit }) {
    const videoRef = ref(null);
    const isStreamLoaded = ref(false);
    const isLoading = ref(true);
    const hasError = ref(false);
    const errorMessage = ref("");
    const isMuted = ref(true);
    const volume = ref(0.5);
    const retryAttempts = ref(0);
    const MAX_RETRIES = 3;
    let hls = null;
    
    // Initialize HLS.js player
    const initializePlayer = () => {
      const videoElement = videoRef.value;
      if (!videoElement || !props.m3u8Url) {
        isLoading.value = false;
        hasError.value = true;
        errorMessage.value = !props.m3u8Url ? "Invalid stream URL" : "Video element not ready";
        return null;
      }
      
      destroyPlayer(); // Clean up any existing player
      
      // Check if HLS.js is supported
      if (window.Hls && window.Hls.isSupported()) {
        hls = new window.Hls({ 
          autoStartLoad: true,
          startLevel: -1,
          maxBufferLength: 30,
          maxMaxBufferLength: 60,
          maxBufferSize: 60 * 1000 * 1000,
          debug: false
        });
        
        hls.loadSource(props.m3u8Url);
        hls.attachMedia(videoElement);
        
        hls.on(window.Hls.Events.MANIFEST_PARSED, () => {
          isLoading.value = false;
          isStreamLoaded.value = true;
          retryAttempts.value = 0;
          
          videoElement.muted = isMuted.value;
          videoElement.volume = volume.value;
          videoElement.play().catch(err => console.warn("Autoplay prevented:", err));
        });
        
        // Error handling
        hls.on(window.Hls.Events.ERROR, (event, data) => {
          if (data.fatal) {
            switch(data.type) {
              case window.Hls.ErrorTypes.NETWORK_ERROR:
                if (retryAttempts.value < MAX_RETRIES) {
                  retryAttempts.value++;
                  console.log(`Network error, retrying (${retryAttempts.value}/${MAX_RETRIES})...`);
                  hls.startLoad();
                } else {
                  hasError.value = true;
                  isLoading.value = false;
                  errorMessage.value = "Network error";
                }
                break;
              case window.Hls.ErrorTypes.MEDIA_ERROR:
                if (retryAttempts.value < MAX_RETRIES) {
                  retryAttempts.value++;
                  console.log(`Media error, retrying (${retryAttempts.value}/${MAX_RETRIES})...`);
                  hls.recoverMediaError();
                } else {
                  hasError.value = true;
                  isLoading.value = false;
                  errorMessage.value = "Media error";
                }
                break;
              default:
                hasError.value = true;
                isLoading.value = false;
                errorMessage.value = "Fatal playback error";
                break;
            }
          }
        });
      } else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
        // For Safari with native HLS support
        videoElement.src = props.m3u8Url;
        
        videoElement.addEventListener('loadedmetadata', () => {
          isLoading.value = false;
          isStreamLoaded.value = true;
          videoElement.muted = isMuted.value;
          videoElement.volume = volume.value;
          videoElement.play().catch(console.error);
        });
        
        videoElement.addEventListener('error', () => {
          if (retryAttempts.value < MAX_RETRIES) {
            retryAttempts.value++;
            setTimeout(() => videoElement.load(), 1000);
          } else {
            hasError.value = true;
            isLoading.value = false;
            errorMessage.value = "Playback error";
          }
        });
      } else {
        hasError.value = true;
        isLoading.value = false;
        errorMessage.value = "HLS not supported in your browser";
      }
    };
    
    // Clean up HLS instance
    const destroyPlayer = () => {
      if (hls) {
        hls.destroy();
        hls = null;
      }
    };
    
    // Toggle mute state
    const toggleMute = () => {
      isMuted.value = !isMuted.value;
      if (videoRef.value) {
        videoRef.value.muted = isMuted.value;
        if (!isMuted.value && volume.value === 0) {
          volume.value = 0.5;
          videoRef.value.volume = volume.value;
        }
      }
    };
    
    // Handle volume change
    const handleVolumeChange = (newVolume) => {
      volume.value = newVolume;
      if (videoRef.value) {
        videoRef.value.volume = newVolume;
        isMuted.value = newVolume === 0;
        videoRef.value.muted = isMuted.value;
      }
    };
    
    // Track stream view for analytics
    const trackStreamView = () => {
      if (isStreamLoaded.value && props.m3u8Url) {
        fetch('/api/trigger-detection', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stream_url: props.m3u8Url,
            timestamp: new Date().toISOString(),
            platform: props.platform,
            streamer_name: props.streamerName
          }),
        }).catch(error => console.error("Analytics error:", error));
      }
    };
    
    // Handle refresh request
    const handleRefresh = () => {
      emit('refresh-stream');
    };
    
    // Watch for stream loaded state to trigger analytics
    watch(isStreamLoaded, newValue => {
      if (newValue) {
        trackStreamView();
      }
    });
    
    // Initialize player when component mounts or URL changes
    watch(() => props.m3u8Url, () => {
      hasError.value = false;
      isLoading.value = true;
      errorMessage.value = "";
      
      // Use nextTick to ensure DOM is updated
      requestAnimationFrame(initializePlayer);
    }, { immediate: true });
    
    // Clean up on component unmount
    onBeforeUnmount(destroyPlayer);
    
    return {
      videoRef,
      isStreamLoaded,
      isLoading,
      hasError,
      errorMessage,
      isMuted,
      volume,
      toggleMute,
      handleVolumeChange,
      handleRefresh
    };
  },
  template: `
    <div class="hls-player-container">
      <!-- Live Indicator -->
      <div v-if="isStreamLoaded && !hasError" class="live-indicator">
        <div class="red-dot"></div>
        <span class="live-text">LIVE</span>
      </div>
      
      <!-- Loading Indicator -->
      <div v-if="isLoading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">Loading stream...</div>
      </div>
      
      <!-- Error Display -->
      <div v-if="hasError" class="error-overlay">
        <div class="error-icon">⚠️</div>
        <div class="error-text">Stream unavailable</div>
        <button v-if="errorMessage.includes('Network') || errorMessage.includes('manifest')" 
                class="retry-button" 
                @click="handleRefresh">
          Refresh Stream
        </button>
      </div>
      
      <!-- Video Element -->
      <video
        ref="videoRef"
        muted
        autoplay
        playsinline
        :poster="posterUrl"
        class="video-element"
      ></video>
      
      <!-- Controls (shown based on modal state) -->
      <div v-if="isModalOpen" class="video-controls">
        <button class="mute-button control-button" @click="toggleMute">
          <svg v-if="isMuted" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="20" height="20">
            <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="20" height="20">
            <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
          </svg>
        </button>
        
        <input
          type="range"
          class="volume-slider"
          min="0"
          max="1"
          step="0.05"
          :value="volume"
          @input="e => handleVolumeChange(parseFloat(e.target.value))"
        />
        
        <button 
          class="fullscreen-button control-button"
          @click="videoRef && videoRef.requestFullscreen()"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="20" height="20">
            <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
          </svg>
        </button>
      </div>
      
      <!-- Play button for autoplay blocked situations -->
      <div 
        v-if="isStreamLoaded && !hasError && videoRef && videoRef.paused" 
        class="play-overlay" 
        @click="videoRef.play()"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="48" height="48">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </div>
    </div>
  `
});

export default defineComponent({
  name: 'VideoPlayer',
  components: {
    HlsPlayer
  },
  props: {
    platform: {
      type: String,
      default: "stripchat",
      validator: value => ['stripchat', 'chaturbate'].includes(value.toLowerCase())
    },
    streamerName: {
      type: String,
      required: true
    },
    staticThumbnail: {
      type: String,
      default: null
    }
  },
  setup(props) {
    // Initialize toast
    const toast = useToast();
    
    const isOnline = ref(true);
    const isModalOpen = ref(false);
    const loading = ref(true);
    const m3u8Url = ref(null);
    const posterUrl = ref(null);
    const thumbnail = ref(props.staticThumbnail);
    const refreshInProgress = ref(false);
    
    let refreshTimeout = null;
    
    // Toggle modal state
    const toggleModal = () => {
      if (!isOnline.value) return;
      isModalOpen.value = !isModalOpen.value;
      document.body.style.overflow = isModalOpen.value ? 'hidden' : '';
    };
    
    // Handle thumbnail error
    const handleThumbnailError = () => {
      thumbnail.value = null;
    };
    
    // Fetch stream data based on platform
    const fetchStreamData = async () => {
      if (refreshInProgress.value) return;
      
      loading.value = true;
      refreshInProgress.value = true;
      
      try {
        const platformLower = props.platform.toLowerCase();
        const endpoint = `/api/streams?platform=${platformLower}&streamer=${encodeURIComponent(props.streamerName)}`;
        
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        
        const data = await response.json();
        if (data.length > 0) {
          // Set m3u8 URL directly from the API response
          const stream = data[0];
          
          if (platformLower === 'chaturbate' && stream.chaturbate_m3u8_url) {
            m3u8Url.value = stream.chaturbate_m3u8_url;
            posterUrl.value = `https://roomimg.stream.highwebmedia.com/ri/${encodeURIComponent(props.streamerName)}.jpg?${Date.now()}`;
            
            // If no static thumbnail, try to get one
            if (!thumbnail.value) {
              thumbnail.value = posterUrl.value;
            }
          } else if (platformLower === 'stripchat' && stream.stripchat_m3u8_url) {
            m3u8Url.value = stream.stripchat_m3u8_url;
            
            // If no static thumbnail for Stripchat, could generate one
            if (!thumbnail.value) {
              thumbnail.value = null; // No standard thumbnail URL for Stripchat
            }
          } else {
            throw new Error(`No ${platformLower}_m3u8_url found in stream data`);
          }
          
          isOnline.value = true;
        } else {
          isOnline.value = false;
          if (platformLower === 'chaturbate') {
            posterUrl.value = `https://roomimg.stream.highwebmedia.com/ri/${encodeURIComponent(props.streamerName)}.jpg?${Date.now()}`;
          }
          throw new Error("No stream data found");
        }
      } catch (error) {
        console.error(`Error fetching stream data:`, error);
        isOnline.value = false;
      } finally {
        loading.value = false;
        
        // Use setTimeout to prevent immediate re-requests
        if (refreshTimeout) clearTimeout(refreshTimeout);
        refreshTimeout = setTimeout(() => { 
          refreshInProgress.value = false; 
        }, 1000);
      }
    };

    // Refresh stream with toast notifications
    const refreshStream = async () => {
      if (refreshInProgress.value) return;
      
      loading.value = true;
      refreshInProgress.value = true;
      
      // Show toast notification for refresh start
      toast.info(`Refreshing ${props.platform} stream...`, {
        timeout: 3000,
        position: "top-right",
        icon: "🔄"
      });
      
      try {
        const platformLower = props.platform.toLowerCase();
        const endpoint = `/api/streams/refresh/${platformLower}`;
        
        // Properly construct the payload based on platform
        let payload;
        if (platformLower === 'chaturbate') {
          const roomUrl = `https://chaturbate.com/${props.streamerName}`;
          payload = { room_slug: props.streamerName, room_url: roomUrl };
        } else if (platformLower === 'stripchat') {
          const roomUrl = `https://stripchat.com/${props.streamerName}`;
          payload = { room_url: roomUrl };
        }
        
        const response = await axios.post(endpoint, payload);
        
        if (response.data) {
          // Extract the m3u8 URL from the response based on platform
          let newM3u8Url = null;
          if (platformLower === 'chaturbate' && response.data.chaturbate_m3u8_url) {
            newM3u8Url = response.data.chaturbate_m3u8_url;
          } else if (platformLower === 'stripchat' && response.data.stripchat_m3u8_url) {
            newM3u8Url = response.data.stripchat_m3u8_url;
          } else if (response.data.m3u8_url) {
            // Fallback to generic m3u8_url if available
            newM3u8Url = response.data.m3u8_url;
          }
          
          if (newM3u8Url) {
            m3u8Url.value = newM3u8Url;
            isOnline.value = true;
            
            // Success toast notification
            toast.success(`${props.platform} stream refreshed successfully!`, {
              timeout: 3000,
              position: "top-right",
              icon: "✅"
            });
          } else {
            isOnline.value = false;
            
            // Stream offline toast notification
            toast.warning(`${props.platform} stream is offline`, {
              timeout: 4000,
              position: "top-right",
              icon: "⚠️"
            });
          }
        } else {
          isOnline.value = false;
          
          // Error toast notification
          toast.warning(`${props.platform} stream could not be refreshed`, {
            timeout: 4000,
            position: "top-right",
            icon: "⚠️"
          });
        }
      } catch (error) {
        console.error(`Error refreshing stream:`, error);
        isOnline.value = false;
        
        if (props.platform.toLowerCase() === 'chaturbate') {
          posterUrl.value = `https://roomimg.stream.highwebmedia.com/ri/${encodeURIComponent(props.streamerName)}.jpg?${Date.now()}`;
        }
        
        // Error toast notification
        toast.error(`Failed to refresh stream: ${error.message || 'Unknown error'}`, {
          timeout: 5000,
          position: "top-right",
          icon: "❌"
        });
      } finally {
        loading.value = false;
        
        // Prevent rapid refresh attempts
        if (refreshTimeout) clearTimeout(refreshTimeout);
        refreshTimeout = setTimeout(() => { 
          refreshInProgress.value = false; 
        }, 1000);
      }
    };
    
    // Handle keyboard shortcuts
    const handleKeyDown = (event) => {
      if (isModalOpen.value && event.key === 'Escape') {
        toggleModal();
      }
    };
    
    // Setup and cleanup
    onMounted(() => {
      fetchStreamData();
      window.addEventListener('keydown', handleKeyDown);
    });
    
    onBeforeUnmount(() => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
      
      // Clear any pending timeouts
      if (refreshTimeout) clearTimeout(refreshTimeout);
    });
    
    // Watch for prop changes
    watch([() => props.platform, () => props.streamerName], () => {
      if (refreshTimeout) clearTimeout(refreshTimeout);
      refreshTimeout = setTimeout(() => {
        fetchStreamData();
      }, 100);
    });
    
    return {
      isOnline,
      isModalOpen,
      loading,
      m3u8Url,
      posterUrl,
      thumbnail,
      toggleModal,
      refreshStream,
      handleThumbnailError
    };
  }
});
</script>

<style scoped>
.video-container {
  position: relative;
  width: 100%;
  height: 0;
  padding-top: 56.25%; /* 16:9 aspect ratio */
  background: #000;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.loading-message, .error-message {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  background: rgba(0, 0, 0, 0.8);
  gap: 16px;
  z-index: 5;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s infinite linear;
}

.error-icon {
  font-size: 28px;
}

.retry-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 68, 68, 0.8);
  border: none;
  border-radius: 4px;
  color: white;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.retry-button:hover {
  background: rgba(255, 68, 68, 1);
}

.thumbnail-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  overflow: hidden;
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-live-indicator {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.7);
  padding: 5px 10px;
  border-radius: 4px;
  z-index: 2;
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.inline-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  position: relative;
  width: 80%;
  max-width: 1000px;
  height: 0;
  padding-top: 45%; /* More compact ratio for modal */
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.close-modal {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.7);
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100;
  transition: background 0.2s ease;
}

.close-modal:hover {
  background: rgba(255, 68, 68, 0.8);
}

/* HLS Player styles */
.hls-player-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #000;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.live-indicator {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.7);
  padding: 5px 10px;
  border-radius: 4px;
  z-index: 2;
}

.red-dot {
  width: 8px;
  height: 8px;
  background-color: #f00;
  border-radius: 50%;
  animation: blink 1.5s infinite;
}

.live-text {
  color: #fff;
  font-size: 12px;
  font-weight: bold;
}

.loading-overlay, .error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  z-index: 2;
}

.loading-text, .error-text {
  color: white;
  font-size: 14px;
}

.video-controls {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.7);
  padding: 6px 10px;
  border-radius: 4px;
  z-index: 3;
  opacity: 0.5;
  transition: opacity 0.3s ease;
}

.video-controls:hover {
  opacity: 1;
}

.control-button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.control-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.volume-slider {
  width: 70px;
  cursor: pointer;
}


.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  cursor: pointer;
  z-index: 2;
}

@keyframes blink {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* CSS containment for better performance */
.hls-player-container {
  contain: layout paint;
}

/* Reduce paint operations for animated elements */
.loading-spinner, .red-dot {
  will-change: opacity, transform;
}

/* Make video controls visible when hovering over the player */
.hls-player-container:hover .video-controls {
  opacity: 1;
}
</style>