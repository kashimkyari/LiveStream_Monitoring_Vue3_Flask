<template>
  <div class="stream-card" @click="$emit('click', $event)" ref="streamCard">
    <div class="video-container">
      <video ref="videoPlayer" class="video-player"></video>
      <DetectionBadge v-if="detectionCount > 0" :count="detectionCount" />
    </div>
    <div class="stream-info">
      <h3 class="stream-title">{{ stream.streamer_username }}</h3>
      <div class="stream-meta">
        <span class="platform-tag" :class="stream.platform.toLowerCase()">
          {{ stream.platform }}
        </span>
        <span class="agent-name">
          {{ stream.agent?.username || 'Unassigned' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import Hls from 'hls.js'
import anime from 'animejs'
import DetectionBadge from './DetectionBadge.vue'

export default {
  name: 'StreamCard',
  components: {
    DetectionBadge
  },
  props: {
    stream: Object,
    detectionCount: Number
  },
  emits: ['click'],
  data() {
    return {
      hls: null
    }
  },
  mounted() {
    this.initializeVideo()
    this.addEntranceAnimation()
  },
  beforeUnmount() {
    this.destroyHls()
  },
  methods: {
    initializeVideo() {
      // Get the correct m3u8 URL directly from the stream object
      let m3u8Url = null
      
      if (this.stream.platform.toLowerCase() === 'chaturbate' && this.stream.chaturbate_m3u8_url) {
        m3u8Url = this.stream.chaturbate_m3u8_url
      } else if (this.stream.platform.toLowerCase() === 'stripchat' && this.stream.stripchat_m3u8_url) {
        m3u8Url = this.stream.stripchat_m3u8_url
      }
      
      if (!m3u8Url) {
        console.error('No HLS URL available for this stream')
        return
      }
      
      // Initialize HLS.js if supported
      if (Hls.isSupported()) {
        this.destroyHls() // Clean up any existing instance
        
        this.hls = new Hls({
          startLevel: 0,
          capLevelToPlayerSize: true,
          maxBufferLength: 30
        })
        
        this.hls.loadSource(m3u8Url)
        this.hls.attachMedia(this.$refs.videoPlayer)
        
        this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
          this.$refs.videoPlayer.muted = true // Muted for autoplay
          this.$refs.videoPlayer.play().catch(e => {
            console.warn('Autoplay prevented:', e)
          })
        })
        
        this.hls.on(Hls.Events.ERROR, (event, data) => {
          console.error('HLS error:', data)
          if (data.fatal) {
            switch(data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                this.hls.startLoad()
                break
              case Hls.ErrorTypes.MEDIA_ERROR:
                this.hls.recoverMediaError()
                break
              default:
                this.destroyHls()
                break
            }
          }
        })
      } 
      // Fallback for browsers with native HLS support
      else if (this.$refs.videoPlayer.canPlayType('application/vnd.apple.mpegurl')) {
        this.$refs.videoPlayer.src = m3u8Url
        this.$refs.videoPlayer.addEventListener('loadedmetadata', () => {
          this.$refs.videoPlayer.muted = true // Muted for autoplay
          this.$refs.videoPlayer.play().catch(e => {
            console.warn('Autoplay prevented:', e)
          })
        })
      }
    },
    destroyHls() {
      if (this.hls) {
        this.hls.destroy()
        this.hls = null
      }
    },
    addEntranceAnimation() {
      // Add fancy entrance animation with anime.js
      anime({
        targets: this.$refs.streamCard,
        translateY: [20, 0],
        opacity: [0, 1],
        scale: [0.95, 1],
        easing: 'easeOutElastic(1, .8)',
        duration: 800,
        delay: this.stream.id * 100 % 500 // Stagger based on stream ID
      })
    },
    addHoverAnimation() {
      anime({
        targets: this.$refs.streamCard,
        scale: 1.05,
        boxShadow: '0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22)',
        duration: 300,
        easing: 'easeOutQuad'
      })
    },
    removeHoverAnimation() {
      anime({
        targets: this.$refs.streamCard,
        scale: 1,
        boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        duration: 300,
        easing: 'easeOutQuad'
      })
    }
  }
}
</script>

<style scoped>
.stream-card {
  background-color: var(--input-bg);
  border-radius: 10px;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border: 1px solid var(--input-border);
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
}

.stream-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
  border-color: var(--primary-color);
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

.stream-info {
  padding: 15px;
}

.stream-title {
  margin: 0 0 5px 0;
  font-size: 1.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stream-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--text-color);
  opacity: 0.8;
}

.platform-tag {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.platform-tag.chaturbate {
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.platform-tag.stripchat {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.agent-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 50%;
}
</style>