<template>
  <div class="video-container" :class="{ 'dark-mode': isDarkMode, 'light-mode': !isDarkMode }">
    <!-- Loading State -->
    <div v-if="loading" class="loading-message">
      <div class="loading-spinner"></div>
      <span>Loading stream...</span>
    </div>
    
    <!-- Offline State -->
    <div v-else-if="!loading && !isOnline" class="error-message">
      <div class="error-icon">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <div>{{ platform }} stream is offline.</div>
      <button class="retry-button" @click="refreshStream">
        <i class="fas fa-sync-alt"></i>
        Retry
      </button>
    </div>
    
    <!-- Thumbnail View -->
    <div 
      v-else-if="!loading && isOnline && thumbnail && !isModalOpen" 
      class="thumbnail-wrapper"
      @click="toggleModal"
      ref="thumbnailEl"
    >
      <img
        :src="thumbnail"
        alt="Live stream thumbnail"
        class="thumbnail-image"
        @error="handleThumbnailError"
      />
     
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
        @stream-offline="handleStreamOffline"
        class="inline-player"
      />
      <div v-else class="error-message">No valid stream URL for {{ platform }}.</div>
    </template>

    <!-- Modal Player -->
    <teleport to="body">
      <div v-if="isModalOpen" class="modal-overlay" @click="toggleModal" ref="modalOverlay">
        <div class="modal-content" @click.stop ref="modalContent" :class="{ 'dark-mode': isDarkMode, 'light-mode': !isDarkMode }">
          <hls-player
            v-if="m3u8Url"
            :m3u8-url="m3u8Url"
            :poster-url="posterUrl"
            :platform="platform"
            :streamer-name="streamerName"
            :is-modal-open="true"
            @refresh-stream="refreshStream"
            @stream-offline="handleStreamOffline"
          />
          <button class="close-modal" @click="toggleModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    </teleport>

    <div class="viewer-count" v-if="viewerCount !== null">
      <font-awesome-icon icon="eye" />
      <span>{{ viewerCount }}</span>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, defineComponent, watch, onBeforeUnmount, nextTick, inject } from 'vue';
import axios from 'axios';
import { useToast } from 'vue-toastification';
import anime from 'animejs/lib/anime.es.js';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

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
  emits: ['refresh-stream', 'stream-offline'],
  setup(props, { emit }) {
    const videoRef = ref(null);
    const controlsRef = ref(null);
    const isStreamLoaded = ref(false);
    const isLoading = ref(true);
    const hasError = ref(false);
    const errorMessage = ref("");
    const isMuted = ref(true);
    const volume = ref(0.5);
    const retryAttempts = ref(0);
    const isPlaying = ref(false);
    const showControls = ref(false);
    const controlsTimeout = ref(null);
    const isDarkMode = inject('isDarkMode', ref(true));
    const MAX_RETRIES = 3;
    let hls = null;
    
    // Initialize HLS.js player with performance optimizations
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
        // Get optimization settings based on device
        const isMobile = window.innerWidth < 768 || 
                        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // Optimized HLS configuration with device-specific settings
        const hlsConfig = {
          autoStartLoad: true,
          startLevel: isMobile ? 0 : -1, // Start with lowest quality on mobile
          abrEwmaDefaultEstimate: isMobile ? 500000 : 1000000, // Lower bandwidth estimate for mobile
          backBufferLength: isMobile ? 30 : 60, // Smaller back buffer on mobile
          maxBufferLength: isMobile ? 15 : 30, // Reduced buffer size on mobile
          maxMaxBufferLength: isMobile ? 30 : 60,
          maxBufferSize: isMobile ? 15 * 1000 * 1000 : 60 * 1000 * 1000, // Smaller buffer on mobile
          maxBufferHole: isMobile ? 0.5 : 0.3,
          lowLatencyMode: !isMobile, // Disable low latency mode on mobile to save battery
          progressive: isMobile, // Progressive loading on mobile
          enableWorker: !isMobile, // Disable web workers on mobile for battery saving
          debug: false,
          testBandwidth: !isMobile, // Skip bandwidth tests on mobile
          fragLoadingMaxRetry: isMobile ? 2 : 4, // Fewer retries on mobile
          manifestLoadingMaxRetry: isMobile ? 2 : 4,
          levelLoadingMaxRetry: isMobile ? 2 : 4
        };
        
        hls = new window.Hls(hlsConfig);
        
        hls.loadSource(props.m3u8Url);
        hls.attachMedia(videoElement);
        
        hls.on(window.Hls.Events.MANIFEST_PARSED, () => {
          isLoading.value = false;
          isStreamLoaded.value = true;
          retryAttempts.value = 0;
          
          videoElement.muted = isMuted.value;
          videoElement.volume = volume.value;
          
          // Optimize animations for mobile
          const isLowPowerDevice = isMobile || (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4);
          
          videoElement.play()
            .then(() => {
              isPlaying.value = true;
              // Update stream status to online when playing
              axios.post(`/api/streams/${props.streamerName}/status`, { status: 'online' })
                .then(() => console.log(`Updated stream ${props.streamerName} status to online`))
                .catch(error => console.error('Failed to update stream status:', error));
              
              // Use simpler animations on low-power devices
              if (!isLowPowerDevice) {
                animatePlayerStart();
              } else {
                // Simple opacity fade for low-power devices
                videoRef.value.style.opacity = '1';
              }
            })
            .catch(err => {
              console.warn("Autoplay prevented:", err);
              // Show big play button when autoplay is prevented
              showControls.value = true;
            });
        });
        
        // Error handling with improved recovery strategies
        hls.on(window.Hls.Events.ERROR, (event, data) => {
          if (data.fatal) {
            console.warn(`HLS fatal error: ${data.type} - ${data.details}`);
            
            switch(data.type) {
              case window.Hls.ErrorTypes.NETWORK_ERROR:
                if (retryAttempts.value < MAX_RETRIES) {
                  retryAttempts.value++;
                  console.log(`Network error, retrying (${retryAttempts.value}/${MAX_RETRIES})...`);
                  // Exponential backoff for retries
                  setTimeout(() => {
                    hls.startLoad();
                  }, 1000 * Math.pow(2, retryAttempts.value - 1));
                } else {
                  hasError.value = true;
                  isLoading.value = false;
                  errorMessage.value = "Network error - check your connection";
                  emit('stream-offline');
                }
                break;
              case window.Hls.ErrorTypes.MEDIA_ERROR:
                if (retryAttempts.value < MAX_RETRIES) {
                  retryAttempts.value++;
                  console.log(`Media error, retrying (${retryAttempts.value}/${MAX_RETRIES})...`);
                  
                  // Try different recovery methods based on retry count
                  if (retryAttempts.value === 1) {
                    hls.recoverMediaError();
                  } else {
                    hls.swapAudioCodec();
                    hls.recoverMediaError();
                  }
                } else {
                  hasError.value = true;
                  isLoading.value = false;
                  errorMessage.value = "Media playback error";
                  emit('stream-offline');
                }
                break;
              default:
                hasError.value = true;
                isLoading.value = false;
                errorMessage.value = data.details || "Fatal playback error";
                emit('stream-offline');
                break;
            }
          } else {
            // Non-fatal errors - just log for debugging
            console.log(`HLS non-fatal error: ${data.type} - ${data.details}`);
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
          videoElement.play()
            .then(() => {
              isPlaying.value = true;
              const isMobile = window.innerWidth < 768;
              if (!isMobile) {
                animatePlayerStart();
              } else {
                // Simple opacity change for mobile Safari
                videoRef.value.style.opacity = '1';
              }
            })
            .catch(err => {
              console.error("Playback error:", err);
              showControls.value = true; // Show play button when autoplay fails
              emit('stream-offline');
            });
        });
        
        videoElement.addEventListener('error', () => {
          if (retryAttempts.value < MAX_RETRIES) {
            retryAttempts.value++;
            // Exponential backoff
            setTimeout(() => videoElement.load(), 1000 * Math.pow(2, retryAttempts.value - 1));
          } else {
            hasError.value = true;
            isLoading.value = false;
            errorMessage.value = "Playback error - try refreshing";
            emit('stream-offline');
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
        
        // Animate mute icon
        anime({
          targets: '.mute-button i',
          scale: [1.2, 1],
          opacity: [0.5, 1],
          easing: 'easeOutElastic(1, .6)',
          duration: 500
        });
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
    
    // Handle play/pause
    const togglePlayPause = () => {
      if (!videoRef.value) return;
      
      if (videoRef.value.paused) {
        videoRef.value.play()
          .then(() => { isPlaying.value = true; })
          .catch(console.error);
      } else {
        videoRef.value.pause();
        isPlaying.value = false;
      }
      
      // Animate play/pause button
      anime({
        targets: '.play-pause-button i',
        rotateZ: '+=360',
        easing: 'easeInOutSine',
        duration: 300
      });
    };
    
    // Show/hide controls
    const handleMouseMove = () => {
      showControls.value = true;
      
      if (controlsTimeout.value) {
        clearTimeout(controlsTimeout.value);
      }
      
      if (isPlaying.value) {
        controlsTimeout.value = setTimeout(() => {
          showControls.value = false;
        }, 3000);
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
      
      // Animate refresh button
      anime({
        targets: '.retry-button i',
        rotateZ: '+=360',
        easing: 'easeInOutQuad',
        duration: 800
      });
    };
    
    // Animation for player start with device optimizations
    const animatePlayerStart = () => {
      // Check if device is mobile or low-power
      const isMobile = window.innerWidth < 768 || 
                      /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      const isLowPowerDevice = isMobile || (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4);
      
      if (isLowPowerDevice) {
        // Simple CSS transition for low-power devices
        if (videoRef.value) {
          videoRef.value.style.opacity = '1';
          videoRef.value.style.transform = 'scale(1)';
        }
        
        const liveIndicator = document.querySelector('.live-indicator');
        if (liveIndicator) {
          liveIndicator.style.opacity = '1';
          liveIndicator.style.transform = 'translateX(0)';
        }
      } else {
        // Full animation for high-power devices
        anime({
          targets: videoRef.value,
          opacity: [0, 1],
          scale: [0.98, 1],
          easing: 'easeOutCubic',
          duration: 400
        });
        
        // Animate live indicator entrance
        anime({
          targets: '.live-indicator',
          translateX: [-20, 0],
          opacity: [0, 1],
          easing: 'easeOutQuad', // Simpler easing
          duration: 400,
          delay: 200
        });
      }
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
      
      requestAnimationFrame(initializePlayer);
    }, { immediate: true });
    
    // Toggle fullscreen
    const toggleFullscreen = () => {
      const container = videoRef.value?.closest('.hls-player-container');
      if (!container) return;
      
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(err => console.error(err));
      } else {
        container.requestFullscreen().catch(err => console.error(err));
      }
      
      // Animate fullscreen button
      anime({
        targets: '.fullscreen-button i',
        scale: [1.2, 1],
        opacity: [0.5, 1],
        easing: 'easeOutElastic(1, .6)',
        duration: 500
      });
    };
    
    // Monitor playback state
    const setUpPlaybackStateMonitor = () => {
      if (!videoRef.value) return;
      
      videoRef.value.addEventListener('play', () => {
        isPlaying.value = true;
      });
      
      videoRef.value.addEventListener('pause', () => {
        isPlaying.value = false;
      });
      
      videoRef.value.addEventListener('ended', () => {
        isPlaying.value = false;
      });
    };
    
    onMounted(() => {
      setUpPlaybackStateMonitor();
      
      // Add hover effects for controls
      if (controlsRef.value) {
        controlsRef.value.addEventListener('mouseenter', () => {
          if (controlsTimeout.value) {
            clearTimeout(controlsTimeout.value);
          }
          showControls.value = true;
        });
      }
    });
    
    // Clean up on component unmount
    onBeforeUnmount(() => {
      destroyPlayer();
      if (controlsTimeout.value) {
        clearTimeout(controlsTimeout.value);
      }
    });
    
    return {
      videoRef,
      controlsRef,
      isStreamLoaded,
      isLoading,
      hasError,
      errorMessage,
      isMuted,
      volume,
      isPlaying,
      showControls,
      isDarkMode,
      toggleMute,
      handleVolumeChange,
      togglePlayPause,
      handleMouseMove,
      toggleFullscreen,
      handleRefresh
    };
  },
  template: `
    <div class="hls-player-container" 
         @mousemove="handleMouseMove" 
         :class="{ 'dark-mode': isDarkMode, 'light-mode': !isDarkMode }">
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
        <div class="error-icon">
          <i class="fas fa-exclamation-triangle"></i>
        </div>
        <div class="error-text">Stream unavailable</div>
        <button v-if="errorMessage.includes('Network') || errorMessage.includes('manifest')" 
                class="retry-button" 
                @click="handleRefresh">
          <i class="fas fa-sync-alt"></i>
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
      
      <!-- Controls -->
      <div v-if="isModalOpen || showControls" 
           class="video-controls" 
           ref="controlsRef"
           :class="{ 'visible': isModalOpen || showControls }">
        <button class="control-button play-pause-button" @click="togglePlayPause">
          <i :class="[isPlaying ? 'fas fa-pause' : 'fas fa-play']"></i>
        </button>
        
        <button class="control-button mute-button" @click="toggleMute">
          <i :class="[isMuted ? 'fas fa-volume-mute' : (volume > 0.5 ? 'fas fa-volume-up' : 'fas fa-volume-down')]"></i>
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
        
        <button class="control-button fullscreen-button" @click="toggleFullscreen">
          <i class="fas fa-expand"></i>
        </button>
      </div>
      
      <!-- Large Play Button for Autoplay Blocked -->
      <div 
        v-if="isStreamLoaded && !hasError && videoRef && videoRef.paused" 
        class="play-overlay" 
        @click="togglePlayPause"
      >
        <i class="fas fa-play fa-3x"></i>
      </div>
    </div>
  `
});

export default defineComponent({
  name: 'VideoPlayer',
  components: {
    HlsPlayer,
    FontAwesomeIcon
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
    streamerUid: {
      type: String,
      default: null
    },
    staticThumbnail: {
      type: String,
      default: null
    },
    onDetection: {
      type: Function,
      default: null
    }
  },
  setup(props) {
    // Get theme mode from parent app or use dark mode as default
    const isDarkMode = inject('isDarkMode', ref(true));
    
    // Initialize toast
    const toast = useToast();
    
    const isOnline = ref(true);
    const isModalOpen = ref(false);
    const loading = ref(true);
    const m3u8Url = ref(null);
    const posterUrl = ref(null);
    const thumbnail = ref(props.staticThumbnail);
    const refreshInProgress = ref(false);
    const fetchedStreamerUsername = ref(null);
    const thumbnailEl = ref(null);
    const modalOverlay = ref(null);
    const modalContent = ref(null);
    const viewerCount = ref(null);
    
    let refreshTimeout = null;
    
    // Toggle modal state with device-optimized animations
    const toggleModal = () => {
      if (!isOnline.value) return;
      
      // Check if device is mobile or low-power
      const isMobile = window.innerWidth < 768 || 
                      /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      const isLowPowerDevice = isMobile || (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4);
      
      if (!isModalOpen.value) {
        isModalOpen.value = true;
        document.body.style.overflow = 'hidden';
        
        // Wait for modal to be in DOM
        nextTick(() => {
          if (isLowPowerDevice) {
            // Simple CSS transitions for low-power devices
            if (modalOverlay.value) {
              modalOverlay.value.style.opacity = '1';
            }
            
            if (modalContent.value) {
              modalContent.value.style.opacity = '1';
              modalContent.value.style.transform = 'scale(1)';
            }
          } else {
            // Full animations for desktop
            anime({
              targets: modalOverlay.value,
              opacity: [0, 1],
              duration: 300,
              easing: 'easeOutQuad'
            });
            
            anime({
              targets: modalContent.value,
              scale: [0.9, 1],
              opacity: [0, 1],
              duration: 400,
              easing: 'easeOutCubic'
            });
          }
        });
      } else {
        if (isLowPowerDevice) {
          // Simple CSS transitions for low-power devices
          if (modalOverlay.value) {
            modalOverlay.value.style.opacity = '0';
          }
          
          if (modalContent.value) {
            modalContent.value.style.opacity = '0';
            modalContent.value.style.transform = 'scale(0.9)';
          }
          
          // Use setTimeout instead of animation callbacks
          setTimeout(() => {
            isModalOpen.value = false;
            document.body.style.overflow = '';
          }, 300);
        } else {
          // Full animations for desktop
          anime({
            targets: modalOverlay.value,
            opacity: 0,
            duration: 300,
            easing: 'easeOutQuad',
            complete: () => {
              isModalOpen.value = false;
              document.body.style.overflow = '';
            }
          });
          
          anime({
            targets: modalContent.value,
            scale: 0.9,
            opacity: 0,
            duration: 300,
            easing: 'easeOutQuad'
          });
        }
      }
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
            fetchedStreamerUsername.value = stream.streamer_username || props.streamerName;
            
            // If no static thumbnail, try to get one
            if (!thumbnail.value) {
              thumbnail.value = posterUrl.value;
            }
            
            isOnline.value = true;
            animateThumbnail();
          } else if (platformLower === 'stripchat' && stream.stripchat_m3u8_url) {
            m3u8Url.value = stream.stripchat_m3u8_url;
            fetchedStreamerUsername.value = stream.streamer_username || props.streamerName;
            
            // If no static thumbnail for Stripchat, could generate one
            if (!thumbnail.value) {
              thumbnail.value = null; // No standard thumbnail URL for Stripchat
            }
            
            isOnline.value = true;
            animateThumbnail();
          } else {
            throw new Error(`No ${platformLower}_m3u8_url found in stream data`);
          }
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

    // Optimized thumbnail entrance animation with device detection
    const animateThumbnail = () => {
      if (!thumbnailEl.value) return;
      
      // Check if device is mobile or low-power
      const isMobile = window.innerWidth < 768 || 
                      /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      const isLowPowerDevice = isMobile || (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4);
      
      if (isLowPowerDevice) {
        // Simple CSS transitions for low-power devices
        if (thumbnailEl.value) {
          thumbnailEl.value.style.opacity = '1';
          thumbnailEl.value.style.transform = 'translateY(0)';
        }
        
        // Simple transition for live indicator
        const liveIndicator = document.querySelector('.thumbnail-live-indicator');
        if (liveIndicator) {
          // Small delay for the indicator
          setTimeout(() => {
            liveIndicator.style.opacity = '1';
            liveIndicator.style.transform = 'translateX(0)';
          }, 150);
        }
      } else {
        // Full animations for desktop
        anime({
          targets: thumbnailEl.value,
          opacity: [0, 1],
          translateY: [20, 0],
          easing: 'easeOutCubic',
          duration: 600
        });
        
        // Animate live indicator
        anime({
          targets: '.thumbnail-live-indicator',
          translateX: [-20, 0],
          opacity: [0, 1],
          easing: 'easeOutBack',
          duration: 600,
          delay: 300
        });
      }
      
      // Preload video if appropriate (for high-bandwidth users)
      if (!isMobile && navigator.connection && navigator.connection.effectiveType === '4g') {
        const preloadLink = document.createElement('link');
        preloadLink.rel = 'preload';
        preloadLink.as = 'video';
        preloadLink.href = m3u8Url.value;
        document.head.appendChild(preloadLink);
      }
    };

    // Refresh stream with toast notifications
    const refreshStream = async () => {
      if (refreshInProgress.value) return;
      
      loading.value = true;
      refreshInProgress.value = true;
      
      // Animate refresh attempt
      anime({
        targets: '.retry-button i',
        rotateZ: '+=360',
        easing: 'easeInOutQuad',
        duration: 800
      });
      
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
            posterUrl.value = `https://roomimg.stream.highwebmedia.com/ri/${encodeURIComponent(props.streamerName)}.jpg?${Date.now()}`;
          } else if (platformLower === 'stripchat' && response.data.stripchat_m3u8_url) {
            newM3u8Url = response.data.stripchat_m3u8_url;
          } else if (response.data.m3u8_url) {
            // Fallback to generic m3u8_url if available
            newM3u8Url = response.data.m3u8_url;
          }
          
          if (newM3u8Url) {
            m3u8Url.value = newM3u8Url;
            isOnline.value = true;
            
            // Success toast with animation
            toast.success(`${props.platform} stream refreshed successfully!`, {
              timeout: 3000,
              position: "top-right",
              icon: "✅"
            });
            
            // If previously not online, animate the new player
            if (!isOnline.value) {
              isOnline.value = true;
              setTimeout(() => animateThumbnail(), 100);
            }
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
        
        // Error toast notification with animation
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
    
    // Setup and cleanup with device-optimized loading animation
    onMounted(() => {
      fetchStreamData();
      window.addEventListener('keydown', handleKeyDown);
      
      // Check if device is mobile or low-power
      const isMobile = window.innerWidth < 768 || 
                       /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      const isLowPowerDevice = isMobile || (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4);
      
      // Use CSS animation for spinner on mobile/low-power devices, anime.js for desktop
      if (isLowPowerDevice) {
        // Let CSS handle the animation via @keyframes for better performance
        const spinners = document.querySelectorAll('.loading-spinner');
        spinners.forEach(spinner => {
          if (spinner) {
            spinner.classList.add('css-spin-animation');
          }
        });
      } else {
        // Use anime.js for desktop
        anime({
          targets: '.loading-spinner',
          rotateZ: '360deg',
          easing: 'linear',
          duration: 1000,
          loop: true
        });
      }
      
      // Preload resources for faster loading when bandwidth allows
      if (!isMobile && navigator.connection && 
          (navigator.connection.effectiveType === '4g' || navigator.connection.effectiveType === 'wifi')) {
        const fontAwesomePreconnect = document.createElement('link');
        fontAwesomePreconnect.rel = 'preconnect';
        fontAwesomePreconnect.href = 'https://use.fontawesome.com';
        document.head.appendChild(fontAwesomePreconnect);
      }
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
    
    const handleStreamOffline = () => {
      isOnline.value = false;
      m3u8Url.value = null;
      toast.warning(`${props.platform} stream went offline`);
    };
    
    return {
      isOnline,
      isModalOpen,
      loading,
      m3u8Url,
      posterUrl,
      thumbnail,
      fetchedStreamerUsername,
      isDarkMode,
      thumbnailEl,
      modalOverlay,
      modalContent,
      toggleModal,
      refreshStream,
      handleThumbnailError,
      viewerCount,
      handleStreamOffline
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
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

/* Theme modes */
.dark-mode {
  background: #121212;
  color: #fff;
}

.light-mode {
  background: #f5f5f5;
  color: #121212;
}

.loading-message, .error-message {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
  gap: 15px;
}

.dark-mode .loading-message, .dark-mode .error-message {
  background: rgba(18, 18, 18, 0.85);
}

.light-mode .loading-message, .light-mode .error-message {
  background: rgba(245, 245, 245, 0.85);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top-color: #ff4d4d;
  border-radius: 50%;
  animation: spin 1s infinite linear;
}

.dark-mode .loading-spinner {
  border-color: rgba(255, 255, 255, 0.1);
  border-top-color: #ff4d4d;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* CSS spinner animation for better performance on mobile */
.css-spin-animation {
  animation: spin 1s infinite linear !important;
}

.error-icon {
  font-size: 24px;
  color: #ff4d4d;
  margin-bottom: 10px;
}

.retry-button {
  background: #ff4d4d;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 15px;
  transition: background 0.2s ease;
}

.retry-button:hover {
  background: #ff3333;
}

.retry-button i {
  font-size: 14px;
}

.thumbnail-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  overflow: hidden;
  border-radius: 8px;
  transition: transform 0.2s ease, opacity 0.4s ease;
  opacity: 0; /* Initially hidden for smooth animation */
  transform: translateY(20px); /* Initial position for animation */
}

.thumbnail-wrapper:hover {
  transform: scale(1.02);
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-live-indicator {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 4px;
  padding: 5px 10px;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: bold;
  color: white;
  /* Add transitions for CSS animation fallback */
  opacity: 0;
  transform: translateX(-20px);
  transition: opacity 0.4s ease, transform 0.4s ease;
}

.red-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ff4d4d;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.inline-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.modal-content {
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  aspect-ratio: 16/9;
}

.close-modal {
  position: absolute;
  top: 15px;
  right: 15px;
  background: rgba(0, 0, 0, 0.7);
  border: none;
  color: white;
  font-size: 20px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  z-index: 100;
  transition: background 0.2s ease;
}

.close-modal:hover {
  background: rgba(0, 0, 0, 0.9);
}

/* HLS Player styles */
.hls-player-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
  overflow: hidden;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.live-indicator {
  position: absolute;
  top: 15px;
  left: 15px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 4px;
  padding: 5px 10px;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: bold;
  color: white;
  z-index: 10;
}

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
  background: rgba(0, 0, 0, 0.7);
  z-index: 20;
  gap: 15px;
}

.loading-text {
  color: white;
  font-size: 14px;
}

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
  background: rgba(0, 0, 0, 0.7);
  z-index: 20;
  color: white;
  gap: 10px;
}

.error-text {
  font-size: 16px;
  margin-bottom: 10px;
}

.video-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  display: flex;
  align-items: center;
  padding: 15px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
  z-index: 15;
  gap: 15px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.video-controls.visible {
  opacity: 1;
}

.control-button {
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 18px;
  width: 32px;
  height: 32px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  transition: background 0.2s ease;
}

.control-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.volume-slider {
  width: 80px;
  height: 4px;
  appearance: none;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  outline: none;
}

.volume-slider::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.4);
  color: white;
  cursor: pointer;
  z-index: 10;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.play-overlay:hover {
  opacity: 1;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .volume-slider {
    width: 60px;
  }
  
  .control-button {
    font-size: 16px;
    width: 28px;
    height: 28px;
  }
  
  .modal-content {
    width: 100%;
    max-width: none;
    max-height: none;
    height: 50vh;
  }
}

@media (max-width: 480px) {
  .volume-slider {
    display: none;
  }
  
  .video-controls {
    padding: 10px;
    gap: 10px;
  }
  
  .control-button {
    font-size: 14px;
    width: 24px;
    height: 24px;
  }
}

.viewer-count {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  padding: 5px 10px;
  border-radius: 15px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 5px;
  z-index: 20;
}

[data-theme='light'] .viewer-count {
  background-color: rgba(255, 255, 255, 0.5);
  color: var(--light-text);
}
</style>