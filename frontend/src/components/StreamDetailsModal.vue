<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <button class="modal-close" @click="$emit('close')" v-wave>
        <font-awesome-icon icon="times" />
      </button>
      <div class="modal-header">
        <h3>{{ stream.streamer_username }}</h3>
        <div class="stream-tags">
          <span class="tag platform">{{ stream.platform }}</span>
          <!-- Updated agent tags to properly display usernames -->
          <div class="agent-tags">
            <span v-if="!hasAssignments" class="tag agent unassigned">
              Unassigned
            </span>
            <span 
              v-for="assignment in stream.assignments" 
              :key="assignment.id" 
              class="tag agent"
              v-tooltip="'Agent ID: ' + assignment.agent_id"
            >
              {{ getAgentUsername(assignment) }}
            </span>
          </div>
          <span class="tag stream-id">ID: {{ stream.id }}</span>
        </div>
      </div>
      <div class="modal-body">
        <div class="stream-player-container">
          <video ref="videoPlayer" class="video-player"></video>
          <div v-if="isLoading" class="loading-overlay">
            <font-awesome-icon icon="spinner" spin class="loading-icon" />
            <div>Loading stream...</div>
          </div>
        </div>
        <div v-if="detections.length > 0" class="detections-section">
          <h4>Recent Detections</h4>
          <div class="detections-grid">
            <div 
              v-for="(alert, index) in detections" 
              :key="index"
              class="detection-card"
              v-wave
            >
              <img :src="alert.image_url" alt="Detection" class="detection-image" />
              <div class="detection-info">
                <div class="detection-class">{{ alert.class }}</div>
                <div class="detection-confidence">
                  {{ (alert.confidence * 100).toFixed(1) }}% confidence
                </div>
                <div class="detection-time">{{ formatTime(alert.timestamp) }}</div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="refreshError" class="error-banner">
          {{ refreshError }}
        </div>
      </div>
      <div class="modal-footer">
        <button 
          @click="openAssignAgentModal" 
          class="action-button" 
          v-wave
          :disabled="isRefreshing"
        >
          Assign Agent
        </button>
        <button 
          @click="handleRefresh" 
          class="action-button" 
          v-wave
          :disabled="isRefreshing"
        >
          <span v-if="isRefreshing">
            <font-awesome-icon icon="spinner" spin />
            Refreshing...
          </span>
          <span v-else>
            Refresh Stream
          </span>
        </button>
      </div>
    </div>
  </div>
  <!-- Assign Agent Modal -->
  <div v-if="showAssignModal" class="modal-overlay" @click.self="closeAssignAgentModal">
    <div class="assign-modal-content">
      <button class="modal-close" @click="closeAssignAgentModal" v-wave>
        <font-awesome-icon icon="times" />
      </button>
      <div class="modal-header">
        <h3>Assign Agent to {{ stream.streamer_username }}</h3>
      </div>
      <div class="modal-body">
        <div class="agent-selection">
          <label for="agentSelect">Select Agent:</label>
          <select id="agentSelect" v-model="selectedAgentId" class="agent-select">
            <option value="">-- Select an Agent --</option>
            <option v-for="agent in agents" :key="agent.id" :value="agent.id">
              {{ agent.username }} (ID: {{ agent.id }})
            </option>
          </select>
        </div>
        <div v-if="assignmentError" class="error-banner">
          {{ assignmentError }}
        </div>
      </div>
      <div class="modal-footer">
        <button @click="closeAssignAgentModal" class="action-button cancel" v-wave>
          Cancel
        </button>
        <button 
          @click="assignAgent" 
          class="action-button confirm" 
          v-wave
          :disabled="!selectedAgentId || isAssigning"
        >
          <span v-if="isAssigning">
            <font-awesome-icon icon="spinner" spin />
            Assigning...
          </span>
          <span v-else>
            Assign Agent
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import Hls from 'hls.js'
import anime from 'animejs'
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import axios from 'axios'

export default {
  name: 'StreamDetailsModal',
  props: {
    stream: {
      type: Object,
      required: true
    },
    detections: {
      type: Array,
      default: () => []
    },
    isRefreshing: {
      type: Boolean,
      default: false
    },
    show: {
      type: Boolean,
      default: false
    },
    agents: {
      type: Array,
      default: () => []
    }
  },
  emits: ['close', 'assign', 'refresh', 'agent-assigned'],
  setup(props, { emit }) {
    const refreshError = ref(null)
    const videoPlayer = ref(null)
    const hls = ref(null)
    const isLoading = ref(true)
    const showAssignModal = ref(false)
    const selectedAgentId = ref('')
    const assignmentError = ref(null)
    const isAssigning = ref(false)
    const agentCache = ref({})
    
    // Computed property to check if there are any assigned agents
    const hasAssignments = computed(() => {
      return props.stream.assignments && props.stream.assignments.length > 0;
    })

    // Helper function to get agent username from assignment or fetch from API
    const getAgentUsername = async (assignment) => {
      if (assignment.agent && assignment.agent.username) {
        return assignment.agent.username;
      }
      const agentId = assignment.agent_id;
      if (agentCache.value[agentId]) {
        return agentCache.value[agentId];
      }
      try {
        const response = await axios.get(`/api/agents/${agentId}`);
        const username = response.data.username || `Agent ${agentId}`;
        agentCache.value[agentId] = username;
        return username;
      } catch (error) {
        console.error(`Error fetching username for agent ${agentId}:`, error);
        return `Agent ${agentId}`;
      }
    }

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }

    const handleRefresh = () => {
      refreshError.value = null
      isLoading.value = true
      destroyHls()
      emit('refresh')
      // Re-initialize the video player after a short delay
      setTimeout(() => {
        initializeVideo()
      }, 1000)
      // Call platform-specific refresh endpoint
      refreshStream();
    }

    const refreshStream = async () => {
      try {
        let response;
        if (props.stream.platform.toLowerCase() === 'chaturbate') {
          response = await axios.post('/api/streams/refresh/chaturbate', {
            room_slug: props.stream.streamer_username
          });
        } else if (props.stream.platform.toLowerCase() === 'stripchat') {
          response = await axios.post('/api/streams/refresh/stripchat', {
            room_url: props.stream.room_url
          });
        }
        if (response?.data) {
          emit('refresh');
          // Show success toast or notification if needed
          console.log(`Stream ${props.stream.streamer_username} refreshed successfully.`);
        }
      } catch (error) {
        console.error('Error refreshing stream:', error);
        refreshError.value = `Could not refresh ${props.stream.streamer_username}. Please try again.`;
      }
    };

    const initializeVideo = () => {
      if (!videoPlayer.value) return
      
      try {
        isLoading.value = true
        
        // Get the correct m3u8 URL directly from the stream object
        let m3u8Url = null
        
        if (props.stream.platform.toLowerCase() === 'chaturbate' && props.stream.chaturbate_m3u8_url) {
          m3u8Url = props.stream.chaturbate_m3u8_url
        } else if (props.stream.platform.toLowerCase() === 'stripchat' && props.stream.stripchat_m3u8_url) {
          m3u8Url = props.stream.stripchat_m3u8_url
        }
        
        if (!m3u8Url) {
          refreshError.value = 'No valid streaming URL available for this stream'
          isLoading.value = false
          return
        }
        
        // Initialize HLS.js if supported
        if (Hls.isSupported()) {
          destroyHls() // Clean up any existing instance
          
          hls.value = new Hls({
            startLevel: 0,
            capLevelToPlayerSize: true,
            maxBufferLength: 30,
            maxMaxBufferLength: 60
          })
          
          hls.value.loadSource(m3u8Url)
          hls.value.attachMedia(videoPlayer.value)
          
          hls.value.on(Hls.Events.MANIFEST_PARSED, () => {
            videoPlayer.value.muted = true // Muted for autoplay
            videoPlayer.value.play().catch(e => {
              console.warn('Autoplay prevented:', e)
            })
            isLoading.value = false
            
            // Add animation for the video player
            anime({
              targets: videoPlayer.value,
              opacity: [0, 1],
              duration: 800,
              easing: 'easeOutSine'
            })
          })
          
          hls.value.on(Hls.Events.ERROR, (event, data) => {
            console.error('HLS error:', data)
            if (data.fatal) {
              switch(data.type) {
                case Hls.ErrorTypes.NETWORK_ERROR:
                  refreshError.value = 'Network error while loading the stream'
                  hls.value.startLoad()
                  break
                case Hls.ErrorTypes.MEDIA_ERROR:
                  refreshError.value = 'Media error while playing the stream'
                  hls.value.recoverMediaError()
                  break
                default:
                  refreshError.value = 'Error loading the stream'
                  destroyHls()
                  break
              }
            }
          })
        } 
        // Fallback for browsers with native HLS support
        else if (videoPlayer.value.canPlayType('application/vnd.apple.mpegurl')) {
          videoPlayer.value.src = m3u8Url
          videoPlayer.value.addEventListener('loadedmetadata', () => {
            videoPlayer.value.muted = true // Muted for autoplay
            videoPlayer.value.play().catch(e => {
              console.warn('Autoplay prevented:', e)
            })
            isLoading.value = false
          })
          
          videoPlayer.value.addEventListener('error', () => {
            refreshError.value = 'Error loading the stream'
            isLoading.value = false
          })
        } else {
          refreshError.value = 'HLS streaming is not supported by your browser'
          isLoading.value = false
        }
      } catch (error) {
        console.error('Error initializing video stream:', error)
        refreshError.value = 'Failed to load stream data'
        isLoading.value = false
      }
    }
    
    const destroyHls = () => {
      if (hls.value) {
        hls.value.destroy()
        hls.value = null
      }
      
      if (videoPlayer.value) {
        videoPlayer.value.pause()
        videoPlayer.value.removeAttribute('src')
        videoPlayer.value.load()
      }
    }
    
    // Assign Agent Modal functions
    const openAssignAgentModal = () => {
      showAssignModal.value = true
      selectedAgentId.value = ''
      assignmentError.value = null
      // Add animation for modal entrance
      anime({
        targets: '.assign-modal-content',
        translateY: [30, 0],
        opacity: [0, 1],
        easing: 'easeOutExpo',
        duration: 600
      })
    }
    
    const closeAssignAgentModal = () => {
      showAssignModal.value = false
      selectedAgentId.value = ''
      assignmentError.value = null
    }
    
    const assignAgent = async () => {
      if (!selectedAgentId.value) return
      
      isAssigning.value = true
      assignmentError.value = null
      
      try {
        const response = await axios.post('/api/assignments', {
          stream_id: props.stream.id,
          agent_id: selectedAgentId.value
        })
        
        if (response.data) {
          emit('agent-assigned', {
            streamId: props.stream.id,
            assignment: response.data
          })
          closeAssignAgentModal()
          // Show success toast or notification if needed
          console.log(`Agent ${selectedAgentId.value} assigned to stream ${props.stream.id}`)
        }
      } catch (error) {
        console.error('Error assigning agent:', error)
        assignmentError.value = 'Failed to assign agent. Please try again.'
      } finally {
        isAssigning.value = false
      }
    }
    
    // Initialize when mounted
    onMounted(() => {
      // Add entrance animation to modal
      anime({
        targets: '.modal-content',
        translateY: [30, 0],
        opacity: [0, 1],
        easing: 'easeOutExpo',
        duration: 600
      })
      
      initializeVideo()
      
      // Add animation to detection cards
      anime({
        targets: '.detection-card',
        scale: [0.9, 1],
        opacity: [0, 1],
        delay: anime.stagger(100),
        easing: 'easeOutElastic(1, .8)',
        duration: 800
      })
    })
    
    // Clean up when unmounting
    onBeforeUnmount(() => {
      destroyHls()
    })
    
    // Watch for stream changes and reinitialize video
    watch(() => props.stream.id, () => {
      destroyHls()
      initializeVideo()
    })

    return {
      formatTime,
      handleRefresh,
      refreshError,
      videoPlayer,
      isLoading,
      hasAssignments,
      getAgentUsername,
      openAssignAgentModal,
      closeAssignAgentModal,
      assignAgent,
      showAssignModal,
      selectedAgentId,
      assignmentError,
      isAssigning
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  background-color: var(--input-bg);
  border-radius: 10px;
  width: 100%;
  max-width: 800px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  position: relative;
}

.assign-modal-content {
  background-color: var(--input-bg);
  border-radius: 10px;
  width: 100%;
  max-width: 500px;
  max-height: 60vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  position: relative;
}

.modal-close {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.7;
  transition: opacity 0.2s ease;
  padding: 8px;
  z-index: 10;
}

.modal-close:hover {
  opacity: 1;
}

.modal-header {
  padding: 25px;
  border-bottom: 1px solid var(--input-border);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--text-color);
}

.stream-tags {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.agent-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: capitalize;
}

.tag.platform {
  background-color: rgba(0, 123, 255, 0.2);
  color: var(--primary-color);
}

.tag.agent {
  background-color: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.tag.agent.unassigned {
  background-color: rgba(108, 117, 125, 0.2);
  color: #6c757d;
}

.tag.stream-id {
  background-color: rgba(108, 117, 125, 0.2);
  color: #6c757d;
}

.modal-body {
  padding: 20px;
}

.stream-player-container {
  width: 100%;
  height: 300px;
  background-color: black;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
  position: relative;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  z-index: 5;
}

.loading-icon {
  font-size: 2rem;
  margin-bottom: 10px;
  animation: spin 1s linear infinite;
}

.detections-section h4 {
  margin: 20px 0 15px 0;
  font-size: 1.2rem;
  color: var(--text-color);
}

.detections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
}

.detection-card {
  background-color: var(--hover-bg);
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.detection-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.detection-image {
  width: 100%;
  height: 100px;
  object-fit: cover;
  background-color: var(--input-bg);
}

.detection-info {
  padding: 10px;
}

.detection-class {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 3px;
  color: var(--text-color);
}

.detection-confidence {
  font-size: 0.8rem;
  opacity: 0.8;
  color: var(--text-secondary);
}

.detection-time {
  font-size: 0.7rem;
  opacity: 0.6;
  margin-top: 5px;
  color: var(--text-secondary);
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--input-border);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.action-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-button:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.action-button:active:not(:disabled) {
  transform: translateY(1px);
}

.action-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  background-color: var(--disabled-bg);
}

.action-button.cancel {
  background-color: var(--hover-bg);
  color: var(--text-color);
}

.action-button.cancel:hover:not(:disabled) {
  background-color: var(--disabled-bg);
}

.action-button.confirm {
  background-color: var(--primary-color);
  color: white;
}

.action-button.confirm:hover:not(:disabled) {
  background-color: var(--primary-hover);
}

.agent-selection {
  margin-bottom: 20px;
}

.agent-selection label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-secondary);
}

.agent-select {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 5px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.agent-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
}

.error-banner {
  background-color: #ffebee;
  color: #b71c1c;
  padding: 12px;
  border-radius: 4px;
  margin-top: 20px;
  border: 1px solid #ffcdd2;
  font-size: 0.9rem;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 576px) {
  .modal-content {
    max-height: 85vh;
  }
  
  .stream-player-container {
    height: 250px;
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .action-button {
    width: 100%;
    justify-content: center;
  }
  
  .detections-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 400px) {
  .modal-header h3 {
    font-size: 1.2rem;
  }
  
  .stream-tags {
    gap: 6px;
  }
  
  .tag {
    font-size: 0.7rem;
  }
}
</style>