<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-close-wrapper">
        <button class="modal-close" @click="$emit('close')" v-wave>
          <font-awesome-icon icon="times" />
        </button>
      </div>
      
      <div class="modal-header">
        <font-awesome-icon icon="stream" class="header-icon" />
        <h3>Add New Stream</h3>
      </div>
      
      <div class="connection-status-container" v-if="isCreating">
        <div class="connection-status">
          <div class="status-indicator" :class="connectionStatus">
            {{ connectionStatus === 'sse' ? 'Real-Time' : 'Polling' }}
          </div>
          <div class="status-latency" v-if="latency">{{ latency }}ms</div>
        </div>
      </div>
      
      <div class="modal-body">
        <form @submit.prevent="submitForm">
          <!-- Platform Selection -->
          <div class="form-group" v-show="!isCreating">
            <label for="platform">
              <font-awesome-icon icon="broadcast-tower" class="field-icon" />
              Platform
            </label>
            <div class="platform-selector">
              <div 
                class="platform-option" 
                :class="{ active: form.platform === 'Chaturbate' }"
                @click="selectPlatform('Chaturbate')"
              >
                <div class="platform-icon">CB</div>
                <span>Chaturbate</span>
              </div>
              <div 
                class="platform-option" 
                :class="{ active: form.platform === 'Stripchat' }"
                @click="selectPlatform('Stripchat')"
              >
                <div class="platform-icon">SC</div>
                <span>Stripchat</span>
              </div>
            </div>
            <input type="hidden" v-model="form.platform" required>
          </div>
          
          <!-- Room URL -->
          <div class="form-group" v-show="!isCreating">
            <label for="room_url">
              <font-awesome-icon icon="link" class="field-icon" />
              Room URL
            </label>
            <div class="input-wrapper">
              <input 
                id="room_url" 
                v-model="form.room_url" 
                type="url" 
                placeholder="https://chaturbate.com/username" 
                required
                @input="detectPlatform"
                :class="{ 'has-platform': form.platform, 'has-error': urlError }"
              />
              <div v-if="form.platform" class="platform-badge">
                {{ form.platform }}
              </div>
            </div>
            <div v-if="urlError" class="field-error">
              {{ urlError }}
            </div>
            <div v-else class="form-hint">
              Enter the full URL including https://
            </div>
          </div>
          
          <!-- Agent Assignment -->
          <div class="form-group" v-show="!isCreating">
            <label for="stream_agent">
              <font-awesome-icon icon="user-secret" class="field-icon" />
              Assign Agent (Optional)
              <span class="tooltip" v-tooltip="'Select an agent to monitor this stream'">?</span>
            </label>
            <div class="select-wrapper">
              <select id="stream_agent" v-model="form.agent_id">
                <option value="">Unassigned</option>
                <option v-for="agent in agents" :key="agent.id" :value="agent.id">
                  {{ agent.username }}
                </option>
              </select>
              <font-awesome-icon icon="chevron-down" class="select-arrow" />
            </div>
          </div>
          
          <!-- Assignment Notes -->
          <div class="form-group" v-show="!isCreating">
            <label for="notes">
              <font-awesome-icon icon="sticky-note" class="field-icon" />
              Assignment Notes (Optional)
              <span class="tooltip" v-tooltip="'Add notes for the assigned agent (max 500 characters)'">?</span>
            </label>
            <textarea
              id="notes"
              v-model="form.notes"
              placeholder="Enter any special instructions for the agent..."
              :class="{ 'has-error': notesError }"
              maxlength="500"
              @input="validateNotes"
            ></textarea>
            <div v-if="notesError" class="field-error">
              {{ notesError }}
            </div>
            <div class="form-hint">
              {{ form.notes ? form.notes.length : 0 }}/500 characters
            </div>
          </div>
          
          <!-- Priority Selection -->
          <div class="form-group" v-show="!isCreating">
            <label for="priority">
              <font-awesome-icon icon="exclamation-circle" class="field-icon" />
              Priority
              <span class="tooltip" v-tooltip="'Set the urgency of this stream assignment'">?</span>
            </label>
            <div class="select-wrapper">
              <select id="priority" v-model="form.priority">
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
              </select>
              <font-awesome-icon icon="chevron-down" class="select-arrow" />
            </div>
          </div>
          
          <!-- Progress Section -->
          <div v-if="isCreating" class="progress-container">
            <div class="progress-header">
              <div class="platform-icon-animated" :class="form.platform.toLowerCase()">
                {{ form.platform ? form.platform.substring(0, 2).toUpperCase() : 'ST' }}
              </div>
              <h4>Creating Stream for {{ extractUsername(form.room_url) }}</h4>
            </div>
            
            <div class="progress-stage">
              <div class="stage-icon">
                <font-awesome-icon :icon="currentStageIcon" />
              </div>
              <div class="stage-details">
                <div class="stage-title">{{ progressStage }}</div>
                <div class="stage-description">{{ progressMessage }}</div>
              </div>
            </div>
            
            <div class="progress-tracker">
              <div class="progress-bar-container" ref="progressBarContainer">
                <div class="progress-bar" ref="progressBar" :style="{ width: `${progressPercentage}%` }"></div>
                <div class="progress-particles" ref="progressParticles"></div>
              </div>
              <div class="progress-stats">
                <div class="progress-percentage">{{ progressPercentage }}%</div>
                <div v-if="estimatedTime" class="estimated-time">
                  <font-awesome-icon icon="clock" /> {{ estimatedTime }}s
                </div>
              </div>
            </div>
            
            <div class="progress-steps">
              <div 
                v-for="(step, index) in progressSteps" 
                :key="index"
                class="progress-step"
                :class="{ 
                  'completed': progressPercentage >= step.threshold,
                  'current': currentStepIndex === index
                }"
              >
                <div class="step-indicator">
                  <font-awesome-icon :icon="progressPercentage >= step.threshold ? 'check-circle' : 'circle'" />
                </div>
                <div class="step-label">{{ step.label }}</div>
              </div>
            </div>
            
            <!-- Assignment Details on Completion -->
            <div v-if="progressPercentage >= 100 && assignmentDetails" class="assignment-details">
              <h5>Assignment Details</h5>
              <p><strong>Agent:</strong> {{ assignmentDetails.agent?.username || 'Unassigned' }}</p>
              <p><strong>Priority:</strong> {{ assignmentDetails.priority }}</p>
              <p v-if="assignmentDetails.notes"><strong>Notes:</strong> {{ assignmentDetails.notes }}</p>
            </div>
          </div>
          
          <!-- Error Message -->
          <div v-if="error" class="error-message">
            <font-awesome-icon icon="exclamation-circle" class="error-icon" />
            <span>{{ error }}</span>
            <button @click="retryCreation" class="retry-button" v-if="submitError">
              <font-awesome-icon icon="redo" /> Retry
            </button>
          </div>
          
          <div class="form-actions" v-show="!isCreating || error">
            <button type="button" @click="$emit('close')" class="cancel-button" v-wave :disabled="isCreating && !error">
              <font-awesome-icon icon="times" /> Cancel
            </button>
            <button type="submit" class="submit-button" v-wave :disabled="isCreating || !formValid">
              <font-awesome-icon :icon="isCreating ? 'spinner' : 'plus'" :class="{ 'fa-spin': isCreating }" />
              {{ isCreating ? 'Creating...' : 'Create Stream' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'
import { useToast } from 'vue-toastification'
import anime from 'animejs/lib/anime.es.js'
import axios from 'axios'

export default {
  name: 'CreateStreamModal',
  props: {
    agents: Array,
    error: {
      type: String,
      default: ''
    },
    submitError: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'submit', 'retry', 'streamCreated'],
  setup(props, { emit }) {
    const toast = useToast()
    
    // Form state
    const form = ref({
      platform: '',
      room_url: '',
      agent_id: '',
      notes: '',
      priority: 'normal'
    })
    
    // Progress state
    const isCreating = ref(false)
    const progressPercentage = ref(0)
    const progressMessage = ref('Initializing...')
    const estimatedTime = ref('')
    const urlError = ref('')
    const notesError = ref('')
    const jobId = ref('')
    const connectionStatus = ref('none')
    const latency = ref(null)
    const assignmentDetails = ref(null)
    
    // DOM refs
    const progressBarContainer = ref(null)
    const progressBar = ref(null)
    const progressParticles = ref(null)
    
    // Animation state
    let progressAnimation = null
    let particleAnimations = []
    let particleCleanupInterval = null
    
    // Stream event source
    let eventSource = null
    let pollingInterval = null
    let lastPollTime = 0
    let reconnectAttempts = 0
    const maxReconnectAttempts = 5
    const baseReconnectDelay = 1000
    
    // Progress steps (aligned with backend phases)
    const progressSteps = [
      { threshold: 0, label: 'Initialization' },
      { threshold: 10, label: 'Validating' },
      { threshold: 55, label: 'Scraping' },
      { threshold: 75, label: 'Database' },
      { threshold: 90, label: 'Assignment' },
      { threshold: 100, label: 'Finalizing' }
    ]
    
    const currentStepIndex = computed(() => {
      for (let i = progressSteps.length - 1; i >= 0; i--) {
        if (progressPercentage.value >= progressSteps[i].threshold) {
          return i
        }
      }
      return 0
    })
    
    const progressStage = computed(() => progressSteps[currentStepIndex.value].label)
    
    const currentStageIcon = computed(() => {
      const icons = ['rocket', 'check-circle', 'download', 'database', 'user-secret', 'flag-checkered']
      return icons[currentStepIndex.value] || 'circle-notch'
    })
    
    // Form validation
    const formValid = computed(() => {
      return form.value.platform && 
             form.value.room_url && 
             isValidUrl(form.value.room_url) &&
             validateUrlForPlatform(form.value.room_url, form.value.platform) &&
             !urlError.value &&
             !notesError.value
    })
    
    // Progress animation methods
    const animateProgress = (newValue, oldValue = 0) => {
      if (!progressBar.value) return
      
      particleAnimations.forEach(anim => anim.pause())
      particleAnimations = []
      
      requestAnimationFrame(() => {
        progressAnimation = anime({
          targets: progressBar.value,
          width: `${newValue}%`,
          elasticity: 300,
          duration: 1500,
          easing: 'easeOutElastic(1, .5)',
          update: function() {
            progressSteps.forEach(step => {
              if (newValue >= step.threshold && oldValue < step.threshold) {
                createParticles(newValue)
              }
            })
          }
        })
      })
    }
    
    const createParticles = (position) => {
      if (!progressParticles.value || !progressBarContainer.value) return
      
      const containerWidth = progressBarContainer.value.offsetWidth
      const posX = (containerWidth * position) / 100
      
      for (let i = 0; i < 10; i++) {
        const particle = document.createElement('div')
        particle.className = 'particle'
        const size = Math.floor(Math.random() * 8) + 4
        const color = getRandomColor()
        
        particle.style.width = `${size}px`
        particle.style.height = `${size}px`
        particle.style.backgroundColor = color
        particle.style.left = `${posX}px`
        
        progressParticles.value.appendChild(particle)
        
        const particleAnim = anime({
          targets: particle,
          translateX: {
            value: anime.random(-40, 40),
            easing: 'easeOutQuad'
          },
          translateY: {
            value: anime.random(-60, -20),
            easing: 'easeInQuad'
          },
          opacity: [{ value: 0.9 }, { value: 0 }],
          scale: [
            { value: 1.2, duration: 200 },
            { value: 0.5, duration: 800 }
          ],
          duration: anime.random(1000, 1500),
          complete: () => {
            if (progressParticles.value?.contains(particle)) {
              progressParticles.value.removeChild(particle)
            }
          }
        })
        
        particleAnimations.push(particleAnim)
      }
    }
    
    const getRandomColor = () => {
      const colors = ['#4CAF50', '#2196F3', '#FFC107', '#E91E63', '#9C27B0', '#3F51B5']
      return colors[Math.floor(Math.random() * colors.length)]
    }
    
    // Validation methods
    const isValidUrl = (url) => {
      try {
        new URL(url)
        return true
      } catch (e) {
        urlError.value = 'Please enter a valid URL'
        return false
      }
    }

    const validateUrlForPlatform = (url, platform) => {
      if (!url || !platform) return false
      
      const patterns = {
        Chaturbate: /https?:\/\/(www\.)?chaturbate\.com\/[\w-]+\/?$/i,
        Stripchat: /https?:\/\/(www\.)?stripchat\.com\/[\w-]+\/?$/i
      }
      
      const isValid = patterns[platform]?.test(url.toLowerCase()) || false
      urlError.value = isValid ? '' : `This URL doesn't match the ${platform} format`
      return isValid
    }
    
    const validateNotes = () => {
      if (form.value.notes.length > 500) {
        notesError.value = 'Notes cannot exceed 500 characters'
      } else {
        notesError.value = ''
      }
    }
    
    const selectPlatform = (platform) => {
      form.value.platform = platform
      if (form.value.room_url) validateUrlForPlatform(form.value.room_url, platform)
    }

    const detectPlatform = () => {
      const url = form.value.room_url.toLowerCase()
      const newPlatform = url.includes('stripchat.com') ? 'Stripchat' :
                         url.includes('chaturbate.com') ? 'Chaturbate' : ''
      
      if (form.value.platform !== newPlatform) {
        form.value.platform = newPlatform
      }
      
      if (form.value.room_url && form.value.platform) {
        validateUrlForPlatform(form.value.room_url, form.value.platform)
      } else {
        urlError.value = ''
      }
    }
    
    const extractUsername = (url) => {
      if (!url) return 'Stream'
      try {
        const cleanUrl = url.endsWith('/') ? url.slice(0, -1) : url
        const segments = cleanUrl.split('/')
        return segments[segments.length - 1] || 'Stream'
      } catch (e) {
        return 'Stream'
      }
    }
    
    // SSE Implementation
    const setupSSEConnection = () => {
      cleanupConnections()
      if (reconnectAttempts >= maxReconnectAttempts) {
        console.warn('Max SSE reconnect attempts reached, switching to polling')
        connectionStatus.value = 'polling'
        setupPolling()
        return
      }
      
      try {
        const url = ` https://monitor-backend.jetcamstudio.com:5000/api/streams/interactive/sse?job_id=${jobId.value}`
        eventSource = new EventSource(url)
        connectionStatus.value = 'sse'
        const startTime = Date.now()
        
        eventSource.onopen = () => {
          console.log(`SSE connection established for job ${jobId.value}`)
          reconnectAttempts = 0
          latency.value = Date.now() - startTime
        }
        
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('SSE message received:', data)
            
            if (data.progress !== undefined) {
              progressPercentage.value = Math.min(data.progress, 100)
              animateProgress(data.progress, progressPercentage.value)
            }
            
            if (data.message) {
              progressMessage.value = data.message
            }
            
            if (data.estimated_time) {
              estimatedTime.value = Math.round(data.estimated_time)
            }
            
            if (data.error) {
              console.error('SSE error event:', data.error)
              emit('error', data.error)
              toast.error(`Stream creation failed: ${data.error}`)
              cleanupConnections()
              isCreating.value = false
            }
            
            if (event.event === 'completed' || (data.stream && data.progress >= 100)) {
              console.log('SSE completion event:', data)
              assignmentDetails.value = data.assignment
              emit('streamCreated', data.stream)
              toast.success('Stream created successfully!')
              cleanupConnections()
              isCreating.value = false
            }
          } catch (e) {
            console.error('Error parsing SSE message:', e, event.data)
          }
        }
        
        eventSource.onerror = () => {
          console.warn(`SSE connection failed for job ${jobId.value}, attempt ${reconnectAttempts + 1}`)
          eventSource.close()
          eventSource = null
          reconnectAttempts++
          const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts)
          setTimeout(setupSSEConnection, delay)
        }
      } catch (e) {
        console.warn('SSE not supported or failed to initialize, falling back to polling:', e)
        connectionStatus.value = 'polling'
        setupPolling()
      }
    }
    
    // Fallback polling method
    const setupPolling = () => {
      if (pollingInterval) return

      pollingInterval = setInterval(async () => {
        try {
          const now = Date.now()
          if (now - lastPollTime < 1000) return
          lastPollTime = now

          const startTime = Date.now()
          const response = await axios.get(` https://monitor-backend.jetcamstudio.com:5000/api/streams/interactive/status?job_id=${jobId.value}`)
          
          console.log('Polling response:', response.data)
          latency.value = Date.now() - startTime

          if (!response.data) return

          if (response.data.progress !== undefined) {
            progressPercentage.value = Math.min(response.data.progress, 100)
            animateProgress(response.data.progress, progressPercentage.value)
          }

          if (response.data.message) {
            progressMessage.value = response.data.message
          }

          if (response.data.estimated_time) {
            estimatedTime.value = Math.round(response.data.estimated_time)
          }

          if (response.data.error) {
            console.error('Polling error:', response.data.error)
            emit('error', response.data.error)
            toast.error(`Stream creation failed: ${response.data.error}`)
            cleanupConnections()
            isCreating.value = false
          }

          if (response.data.stream && response.data.progress >= 100) {
            console.log('Polling completion:', response.data)
            assignmentDetails.value = response.data.assignment
            emit('streamCreated', response.data.stream)
            toast.success('Stream created successfully!')
            cleanupConnections()
            isCreating.value = false
          }
        } catch (e) {
          console.error('Polling error:', e)
          if (e.response?.status === 404) {
            console.error('Job not found, stopping polling')
            emit('error', 'Stream creation job not found')
            toast.error('Stream creation job not found')
            cleanupConnections()
            isCreating.value = false
          }
        }
      }, 1000)
    }
    
    // Cleanup connections
    const cleanupConnections = () => {
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
      
      if (pollingInterval) {
        clearInterval(pollingInterval)
        pollingInterval = null
      }
      connectionStatus.value = 'none'
      latency.value = null
    }
    
    // Form submission
    const submitForm = async () => {
      if (!formValid.value) return
      
      const streamData = {
        room_url: form.value.room_url.trim(),
        platform: form.value.platform,
        agent_id: form.value.agent_id || null,
        notes: form.value.notes.trim() || null,
        priority: form.value.priority
      }
      
      try {
        isCreating.value = true
        progressPercentage.value = 0
        progressMessage.value = 'Initializing stream creation...'
        assignmentDetails.value = null
        reconnectAttempts = 0
        
        const response = await axios.post(' https://monitor-backend.jetcamstudio.com:5000/api/streams/interactive', streamData)
        
        if (response.data && response.data.job_id) {
          jobId.value = response.data.job_id
          console.log('Starting SSE for job:', jobId.value)
          setupSSEConnection()
          toast.info(`Creating ${form.value.platform} stream...`, {
            timeout: 3000
          })
          emit('submit', streamData)
        } else {
          throw new Error('No job ID returned from server')
        }
      } catch (error) {
        isCreating.value = false
        let errorMessage = 'Failed to create stream'
        if (error.response?.status === 429) {
          errorMessage = 'Another stream creation is in progress. Please wait.'
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message
          if (error.response.data.error === 'duplicate_stream') {
            errorMessage += ` (Stream ID: ${error.response.data.existing_id})`
          }
        }
        console.error('Submit error:', errorMessage)
        emit('error', errorMessage)
        toast.error(errorMessage)
      }
    }
    
    // Retry creation
    const retryCreation = () => {
      emit('retry', form.value)
      submitForm()
    }
    
    // Lifecycle hooks
    onMounted(() => {
      particleCleanupInterval = setInterval(() => {
        particleAnimations = particleAnimations.filter(anim => !anim.completed)
      }, 1000)
    })
    
    onBeforeUnmount(() => {
      cleanupConnections()
      if (progressAnimation) progressAnimation.pause()
      particleAnimations.forEach(anim => anim.pause())
      clearInterval(particleCleanupInterval)
    })
    
    return {
      form,
      isCreating,
      progressPercentage,
      progressMessage,
      estimatedTime,
      urlError,
      notesError,
      connectionStatus,
      latency,
      progressBarContainer,
      progressBar,
      progressParticles,
      progressSteps,
      currentStepIndex,
      progressStage,
      currentStageIcon,
      submitForm,
      detectPlatform,
      selectPlatform,
      formValid,
      extractUsername,
      retryCreation,
      assignmentDetails,
      validateNotes
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
  background-color: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  background-color: var(--card-bg);
  border-radius: 16px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
  position: relative;
  border: 1px solid var(--card-border);
  color: var(--text-color);
}

.modal-close-wrapper {
  position: absolute;
  top: 15px;
  right: 15px;
  z-index: 5;
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--hover-bg);
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1rem;
  opacity: 0.8;
  transition: all 0.2s ease;
  border-radius: 50%;
  padding: 0;
  min-height: 36px;
}

.modal-close:hover {
  opacity: 1;
  background: var(--input-border);
  transform: rotate(90deg);
}

.modal-header {
  padding: 25px 30px 20px;
  border-bottom: 1px solid var(--card-border);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.header-icon {
  font-size: 1.5rem;
  color: var(--primary-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 600;
}

.connection-status-container {
  padding: 0 30px;
  display: flex;
  justify-content: center;
  margin-top: -5px;
  margin-bottom: 10px;
  border-bottom: 1px solid var(--card-border);
  padding-bottom: 10px;
}

.connection-status {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
}

.status-indicator {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--input-border);
}

.status-indicator.sse {
  color: #4CAF50;
  border-color: #4CAF50;
}

.status-indicator.polling {
  color: #FFC107;
  border-color: #FFC107;
}

.status-latency {
  font-size: 0.7rem;
  opacity: 0.7;
}

.modal-body {
  padding: 25px 30px 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 1rem;
  font-weight: 500;
  gap: 6px;
}

.field-icon {
  color: var(--primary-color);
  font-size: 0.9rem;
}

.form-hint {
  margin-top: 6px;
  font-size: 0.8rem;
  color: var(--text-color);
  opacity: 0.7;
}

.field-error {
  margin-top: 6px;
  font-size: 0.85rem;
  color: var(--danger-color);
}

.platform-selector {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.platform-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px 10px;
  border: 2px solid var(--input-border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--input-bg);
}

.platform-option:hover {
  border-color: var(--primary-color);
  background: var(--hover-bg);
}

.platform-option.active {
  border-color: var(--primary-color);
  background: rgba(var(--primary-color-rgb, 0, 123, 255), 0.1);
}

.platform-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.platform-option.active .platform-icon {
  transform: scale(1.1);
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  padding: 12px 15px;
  border: 2px solid var(--input-border);
  border-radius: 10px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 1rem;
  transition: all 0.2s ease;
  padding-right: 100px;
}

.input-wrapper input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb, 0, 123, 255), 0.1);
  outline: none;
}

.input-wrapper input.has-platform {
  padding-right: 110px;
}

.input-wrapper input.has-error {
  border-color: var(--danger-color);
}

.platform-badge {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: var(--primary-color);
  color: white;
  padding: 4px 10px;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 500;
}

.select-wrapper {
  position: relative;
}

.select-wrapper select {
  width: 100%;
  padding: 12px 15px;
  border: 2px solid var(--input-border);
  border-radius: 10px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 1rem;
  appearance: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.select-wrapper select:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb, 0, 123, 255), 0.1);
  outline: none;
}

.select-arrow {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: var(--text-color);
  opacity: 0.7;
}

textarea {
  width: 100%;
  padding: 12px 15px;
  border: 2px solid var(--input-border);
  border-radius: 10px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 1rem;
  transition: all 0.2s ease;
  resize: vertical;
  min-height: 80px;
  max-height: 200px;
}

textarea:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb, 0, 123, 255), 0.1);
  outline: none;
}

textarea.has-error {
  border-color: var(--danger-color);
}

.tooltip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-color);
  color: white;
  font-size: 0.7rem;
  margin-left: 6px;
  cursor: help;
}

.progress-container {
  background: var(--card-bg);
  border-radius: 16px;
  padding: 20px;
  margin: 20px 0;
  border: 1px solid var(--card-border);
  animation: fadeIn 0.5s ease;
}

.progress-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  gap: 15px;
}

.platform-icon-animated {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 1.2rem;
  animation: pulse 2s infinite;
}

.platform-icon-animated.chaturbate {
  background: linear-gradient(135deg, #ff7e5f, #feb47b);
}

.platform-icon-animated.stripchat {
  background: linear-gradient(135deg, #6a11cb, #2575fc);
}

.progress-header h4 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.progress-stage {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  border-radius: 12px;
  background: var(--hover-bg);
  border: 1px solid var(--card-border);
}

.stage-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  animation: spin 3s infinite linear;
}

.stage-details {
  flex: 1;
}

.stage-title {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 5px;
}

.stage-description {
  color: var(--text-color);
  opacity: 0.7;
  font-size: 0.9rem;
}

.progress-tracker {
  margin-bottom: 20px;
}

.progress-bar-container {
  height: 14px;
  width: 100%;
  background-color: var(--input-bg);
  border-radius: 7px;
  overflow: hidden;
  position: relative;
  margin-bottom: 10px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-bar {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, var(--primary-color) 0%, #4dabf7 100%);
  border-radius: 7px;
  position: relative;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(var(--primary-color-rgb, 0, 123, 255), 0.5);
}

.progress-bar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.3) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  animation: shine 2s infinite;
}

.progress-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.particle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.8;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-percentage {
  font-weight: 700;
  font-size: 1.2rem;
  color: var(--primary-color);
}

.estimated-time {
  font-size: 0.85rem;
  color: var(--text-color);
  opacity: 0.8;
  display: flex;
  align-items: center;
  gap: 5px;
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
  position: relative;
}

.progress-steps::before {
  content: '';
  position: absolute;
  top: 15px;
  left: 25px;
  right: 25px;
  height: 2px;
  background-color: var(--input-border);
  z-index: 1;
}

.progress-step {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.step-indicator {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--card-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--input-border);
  margin-bottom: 8px;
  color: var(--text-color);
  transition: all 0.3s ease;
}

.progress-step.completed .step-indicator {
  border-color: var(--primary-color);
  background: var(--primary-color);
  color: white;
}

.progress-step.current .step-indicator {
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: scale(1.2);
  box-shadow: 0 0 0 5px rgba(var(--primary-color-rgb, 0, 123, 255), 0.1);
}

.step-label {
  font-size: 0.75rem;
  text-align: center;
  max-width: 80px;
  opacity: 0.7;
  transition: all 0.3s ease;
}

.progress-step.current .step-label {
  opacity: 1;
  font-weight: 600;
}

.assignment-details {
  margin-top: 20px;
  padding: 15px;
  background: var(--hover-bg);
  border-radius: 8px;
  border: 1px solid var(--card-border);
}

.assignment-details h5 {
  margin: 0 0 10px;
  font-size: 1.1rem;
  font-weight: 600;
}

.assignment-details p {
  margin: 5px 0;
  font-size: 0.9rem;
}

.error-message {
  margin: 20px 0;
  padding: 15px;
  background-color: rgba(var(--danger-color-rgb, 220, 53, 69), 0.1);
  border-left: 4px solid var(--danger-color);
  color: var(--danger-color);
  border-radius: 6px;
  animation: fadeIn 0.3s ease;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  position: relative;
}

.error-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

.retry-button {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 5px 10px;
  border-radius: 4px;
  background: var(--danger-color);
  color: white;
  border: none;
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
}

.retry-button:hover {
  background: var(--danger-color-hover, #bb2d3b);
  transform: translateY(-1px);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 30px;
}

.cancel-button, .submit-button {
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  min-width: 120px;
  justify-content: center;
  border: none;
}

.cancel-button {
  background-color: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--input-border);
}

.cancel-button:hover {
  background-color: var(--input-border);
}

.submit-button {
  background-color: var(--primary-color);
  color: white;
}

.submit-button:hover {
  background-color: var(--primary-color-hover, #0069d9);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(var(--primary-color-rgb, 0, 123, 255), 0.3);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes shine {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@media (max-width: 768px) {
  .modal-content {
    max-width: 100%;
    margin: 0 10px;
  }
  
  .progress-steps {
    display: none;
  }
  
  .platform-selector {
    flex-direction: column;
  }
  
  .modal-header h3 {
    font-size: 1.3rem;
  }
  
  .modal-body {
    padding: 20px;
  }
  
  .form-actions {
    flex-direction: column;
    gap: 15px;
  }
  
  .cancel-button, .submit-button {
    width: 100%;
  }
}

@media (prefers-color-scheme: dark) {
  .progress-bar::after {
    background: linear-gradient(
      90deg,
      rgba(255, 255, 255, 0) 0%,
      rgba(255, 255, 255, 0.1) 50%,
      rgba(255, 255, 255, 0) 100%
    );
  }
  
  .platform-option:hover {
    background: rgba(255, 255, 255, 0.05);
  }
}
</style>
