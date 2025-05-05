<template>
  <transition name="modal-fade">
    <div v-if="show" class="mobile-stream-modal-overlay" @click="closeModal">
      <div class="mobile-stream-modal" @click.stop>
        <div class="mobile-stream-modal-header">
          <h2>{{ stream.streamer_username }}</h2>
          <div class="close-button" @click="closeModal">×</div>
        </div>
        
        <div class="mobile-stream-modal-body">
          <div class="stream-info-section">
            <div class="stream-badge" :class="stream.platform">
              {{ stream.platform }}
            </div>
            
            <div class="stream-stats">
              <div class="stat-item">
                <font-awesome-icon icon="eye" />
                <span>{{ formatNumber(stream.viewer_count || 0) }} viewers</span>
              </div>
              <div class="stat-item">
                <font-awesome-icon icon="clock" />
                <span>{{ formatStreamTime(stream.stream_start_time) }}</span>
              </div>
            </div>
            
            <div class="stream-url">
              <div class="field-label">Stream URL:</div>
              <div class="url-display">
                <a :href="stream.room_url" target="_blank" rel="noopener noreferrer" class="truncate-text">
                  {{ stream.room_url }}
                </a>
                <button class="copy-button" @click="copyToClipboard(stream.room_url)">
                  <font-awesome-icon icon="copy" />
                </button>
              </div>
            </div>
          </div>
          
          <div class="stream-preview">
            <div class="field-label">Stream:</div>
            <div class="video-container">
              <mobile-video-player
                v-if="isOnline && stream.m3u8_url"
                :streamUrl="stream.m3u8_url"
                :streamTitle="stream.streamer_username || 'Live Stream'"
                :streamPlatform="stream.platform || 'Unknown'"
                :autoplay="true"
                @refresh-request="refreshStream"
              />
              <div v-else class="offline-preview">
                <font-awesome-icon icon="satellite-dish" class="offline-icon" />
                <p>Stream is currently offline</p>
                <button 
                  class="btn btn-secondary"
                  @click="refreshStream"
                  :disabled="detectionLoading"
                >
                  <font-awesome-icon icon="sync" />
                  Try to Reconnect
                </button>
              </div>
            </div>
          </div>
          
          <div class="agent-assignments">
            <div class="field-label">Assigned Agents:</div>
            <div v-if="isLoadingAgents" class="loading-spinner"></div>
            <div v-else-if="!assignedAgents.length" class="no-agents">
              No agents assigned
            </div>
            <div v-else class="agent-list">
              <div v-for="agent in assignedAgents" :key="agent.id" class="agent-item">
                <div class="agent-name">{{ agent.name || agent.username }}</div>
                <div class="agent-id">ID: {{ agent.id }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="mobile-stream-modal-footer">
          <button class="btn btn-secondary" @click="closeModal">Close</button>
          <button v-if="canAssign" class="btn btn-primary" @click="toggleAssign">
            <span v-if="isAssignedToCurrentAgent">Unassign Me</span>
            <span v-else>Assign to Me</span>
          </button>
          <button 
            class="btn" 
            :class="isDetecting ? 'btn-danger' : 'btn-primary'"
            @click="toggleDetection"
            :disabled="!isOnline || detectionLoading"
          >
            <font-awesome-icon 
              :icon="detectionLoading ? 'spinner' : (isDetecting ? 'stop' : 'play')" 
              :spin="detectionLoading" 
            />
            {{ isDetecting ? 'Stop Detection' : isOnline ? 'Start Detection' : 'Stream Offline' }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { ref, computed, watchEffect, inject, watch, onBeforeUnmount } from 'vue'
import { useToast } from 'vue-toastification'
import { formatDistance } from 'date-fns'
import MobileVideoPlayer from './MobileVideoPlayer.vue'
import axios from 'axios'

export default {
  name: 'MobileStreamDetailsModal',
  
  components: {
    MobileVideoPlayer
  },
  
  props: {
    show: {
      type: Boolean,
      default: false
    },
    stream: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['close', 'assign-toggled', 'stream-refresh'],
  setup(props, { emit }) {
    const toast = useToast()
    const isDarkTheme = inject('theme')
    const isDetecting = ref(false)
    const detectionLoading = ref(false)
    const isOnline = ref(props.stream.status === 'online')
    
    // Agent data
    const assignedAgents = ref([])
    const isLoadingAgents = ref(false)
    const currentAgentId = ref(localStorage.getItem('userId') || null)
    
    // Computed properties
    const isAssignedToCurrentAgent = computed(() => {
      if (!currentAgentId.value) return false
      return assignedAgents.value.some(agent => agent.id === currentAgentId.value)
    })
    
    const canAssign = computed(() => {
      return currentAgentId.value !== null
    })
    
    let detectionInterval = null

    const checkDetectionStatus = async () => {
      if (!isOnline.value) return
      try {
        const response = await axios.get(`/api/detection-status/${props.stream.id}`)
        isDetecting.value = response.data.active
        isOnline.value = response.data.status === 'online'
      } catch (error) {
        console.error('Detection status check failed:', error)
        isOnline.value = false
      }
    }

    const startDetectionInterval = () => {
      if (isOnline.value && !detectionInterval) {
        detectionInterval = setInterval(checkDetectionStatus, 10000)
        checkDetectionStatus() // Initial check
      }
    }

    const stopDetectionInterval = () => {
      if (detectionInterval) {
        clearInterval(detectionInterval)
        detectionInterval = null
      }
    }

    watch(isOnline, (newVal) => {
      if (newVal) {
        startDetectionInterval()
      } else {
        stopDetectionInterval()
        isDetecting.value = false
      }
    })

    watchEffect(() => {
      if (props.show && isOnline.value) {
        startDetectionInterval()
      } else {
        stopDetectionInterval()
      }
    })

    onBeforeUnmount(() => {
      stopDetectionInterval()
    })
    
    // Load assigned agents whenever the stream changes
    watchEffect(() => {
      if (props.show && props.stream && props.stream.id) {
        loadAssignedAgents()
      }
    })

    // Watch for stream changes
    watch(() => props.stream, (newStream) => {
      isOnline.value = newStream.status === 'online'
    })
    
    // Methods
    const loadAssignedAgents = async () => {
      if (!props.stream.id) return
      
      try {
        isLoadingAgents.value = true
        // This would be an API call in a real app
        // const response = await StreamService.getStreamAssignments(props.stream.id)
        // assignedAgents.value = response.data
        
        // Example data for now
        setTimeout(() => {
          assignedAgents.value = [
            { id: '1', name: 'Agent Smith', username: 'asmith' },
            { id: '2', name: 'Agent Johnson', username: 'ajohnson' }
          ]
          isLoadingAgents.value = false
        }, 500)
      } catch (error) {
        console.error('Failed to load agent assignments:', error)
        toast.error('Could not load agent assignments')
        isLoadingAgents.value = false
      }
    }
    
    const toggleAssign = async () => {
      if (!canAssign.value) return
      
      try {
        // This would be an API call in a real app
        // if (isAssignedToCurrentAgent.value) {
        //   await StreamService.removeAssignment(props.stream.id, currentAgentId.value)
        // } else {
        //   await StreamService.createAssignment({ streamId: props.stream.id, agentId: currentAgentId.value })
        // }
        
        // For demo, just toggle the state
        if (isAssignedToCurrentAgent.value) {
          assignedAgents.value = assignedAgents.value.filter(a => a.id !== currentAgentId.value)
          toast.success('Unassigned from stream')
        } else {
          assignedAgents.value.push({ 
            id: currentAgentId.value, 
            name: 'Current Agent', 
            username: 'current_agent' 
          })
          toast.success('Assigned to stream')
        }
        
        // Emit event for parent component
        emit('assign-toggled', {
          streamId: props.stream.id,
          isAssigned: !isAssignedToCurrentAgent.value
        })
      } catch (error) {
        console.error('Failed to toggle assignment:', error)
        toast.error('Could not update assignment')
      }
    }
    
    const closeModal = () => {
      emit('close')
    }
    
    const copyToClipboard = (text) => {
      navigator.clipboard.writeText(text)
        .then(() => {
          toast.success('URL copied to clipboard')
        })
        .catch((err) => {
          console.error('Failed to copy:', err)
          toast.error('Could not copy to clipboard')
        })
    }
    
    // Format number for display (e.g. 1000 -> 1K)
    const formatNumber = (num) => {
      if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K'
      }
      return num
    }
    
    // Format stream time as relative time
    const formatStreamTime = (timestamp) => {
      if (!timestamp) return 'Unknown'
      
      try {
        const date = new Date(timestamp)
        return formatDistance(date, new Date(), { addSuffix: true })
      } catch (e) {
        console.error('Error formatting date:', e)
        return 'Unknown'
      }
    }
    
    // Refresh stream
    const refreshStream = () => {
      emit('stream-refresh', props.stream.id);
      toast.info('Refreshing stream...');
    }

    const toggleDetection = async () => {
      detectionLoading.value = true
      try {
        if (isDetecting.value) {
          await axios.post('/api/trigger-detection', {
            stream_id: props.stream.id,
            stop: true
          })
          toast.success(`Detection stopped for ${props.stream.streamer_username}`)
        } else {
          await axios.post('/api/trigger-detection', {
            stream_id: props.stream.id
          })
          toast.success(`Detection started for ${props.stream.streamer_username}`)
        }
        isDetecting.value = !isDetecting.value
      } catch (error) {
        console.error('Detection toggle failed:', error)
        toast.error(`Failed to toggle detection: ${error.response?.data?.error || error.message}`)
      } finally {
        detectionLoading.value = false
      }
    }
    
    return {
      isDarkTheme,
      assignedAgents,
      isLoadingAgents,
      isAssignedToCurrentAgent,
      canAssign,
      toggleAssign,
      closeModal,
      copyToClipboard,
      formatNumber,
      formatStreamTime,
      refreshStream,
      isDetecting,
      detectionLoading,
      toggleDetection,
      isOnline
    }
  }
}
</script>

<style scoped>
.mobile-stream-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.mobile-stream-modal {
  width: 95%;
  max-width: 480px;
  max-height: 90vh;
  background-color: var(--input-bg);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.mobile-stream-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.mobile-stream-modal-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 85%;
}

.close-button {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  cursor: pointer;
  border-radius: 50%;
  background-color: var(--hover-bg);
}

.mobile-stream-modal-body {
  padding: 1rem;
  overflow-y: auto;
  flex-grow: 1;
}

.stream-info-section {
  margin-bottom: 1.5rem;
}

.stream-badge {
  display: inline-block;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  text-transform: capitalize;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 1rem;
}

.stream-badge.chaturbate {
  background-color: #f5a623;
  color: white;
}

.stream-badge.stripchat {
  background-color: #7e57c2;
  color: white;
}

.stream-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-light);
  font-size: 0.9rem;
}

.field-label {
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

.url-display {
  display: flex;
  align-items: center;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  overflow: hidden;
}

.url-display a {
  flex: 1;
  padding: 0.6rem;
  color: var(--primary-color);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.copy-button {
  padding: 0.6rem;
  background: none;
  border: none;
  border-left: 1px solid var(--border-color);
  cursor: pointer;
  color: var(--text-light);
}

.stream-preview {
  margin-bottom: 1.5rem;
}

.video-container {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background-color: #000;
}

.preview-image-container {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
}

.preview-image {
  width: 100%;
  display: block;
}

.no-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--hover-bg);
  border-radius: 8px;
  padding: 2rem;
  color: var(--text-light);
}

.no-preview-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.agent-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.agent-item {
  padding: 0.7rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--hover-bg);
}

.agent-name {
  font-weight: 500;
}

.agent-id {
  font-size: 0.8rem;
  color: var(--text-light);
}

.no-agents {
  color: var(--text-light);
  font-style: italic;
  padding: 0.5rem 0;
}

.mobile-stream-modal-footer {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  border-top: 1px solid var(--border-color);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.offline-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  background-color: var(--hover-bg);
  border-radius: 8px;
}

.offline-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: var(--text-light);
  opacity: 0.7;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary:disabled {
  background-color: var(--border-color);
  color: var(--text-light);
}
</style>