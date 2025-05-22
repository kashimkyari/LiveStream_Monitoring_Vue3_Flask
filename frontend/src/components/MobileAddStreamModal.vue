<template>
  <transition name="sheet-slide">
    <div v-if="isVisible" class="bottom-sheet-overlay" @click="$emit('close')">
      <div class="bottom-sheet-container" @click.stop>
        <div class="bottom-sheet-handle"></div>
        <div class="sheet-content">
          <div class="sheet-header">
            <font-awesome-icon icon="plus" class="sheet-icon" />
            <h3>Add New Stream</h3>
          </div>
          <div v-if="isProcessing" class="progress-section">
            <div class="progress-bar-container" :class="{ 'error': hasError }">
              <div class="progress-bar" :style="progressBarStyle" :title="`Progress: ${progress}%`"
                @mouseenter="showTooltip = true" @mouseleave="showTooltip = false">
                <div class="progress-bar-inner"></div>
              </div>
              <span v-if="showTooltip" class="progress-tooltip">{{ progress }}%</span>
            </div>
            <p class="progress-message" :class="{ 'error-message': hasError, 'fade-in': messageChanged }"
              @animationend="messageChanged = false">
              {{ progressMessage }}
            </p>
            <div v-if="hasError" class="error-details">
              <font-awesome-icon icon="exclamation-triangle" />
              <span>{{ errorDetails }}</span>
            </div>
            <transition name="confetti">
              <div v-if="isComplete" class="confetti-container">
                <font-awesome-icon icon="check-circle" class="completion-icon" />
                <span>Stream Created!</span>
              </div>
            </transition>
          </div>
          <form v-else @submit.prevent="handleSubmit" class="stream-form">
            <div class="form-group">
              <label for="platform">Platform</label>
              <select id="platform" v-model="form.platform" required class="form-control" :disabled="isSubmitting">
                <option value="" disabled>Select Platform</option>
                <option value="chaturbate">Chaturbate</option>
                <option value="stripchat">Stripchat</option>
              </select>
            </div>
            <div class="form-group">
              <label for="room_url">Room URL</label>
              <input id="room_url" v-model="form.room_url" type="url" placeholder="https://example.com/username"
                required class="form-control" :disabled="isSubmitting" />
            </div>
            <div class="form-group">
              <label for="agent_id">Assign Agent (Optional)</label>
              <select id="agent_id" v-model="form.agent_id" class="form-control"
                :disabled="isSubmitting || loadingAgents">
                <option value="">Unassigned</option>
                <option v-for="agent in agentsList" :key="agent.id" :value="agent.id">
                  {{ agent.username }}
                </option>
              </select>
              <div v-if="loadingAgents" class="loading-indicator">
                <font-awesome-icon icon="spinner" spin />
                <span>Loading agents...</span>
              </div>
              <div v-if="errorLoadingAgents" class="error-indicator">
                <font-awesome-icon icon="exclamation-triangle" />
                <span>{{ errorMessage }} <a href="#" @click.prevent="retryFetchAgents">Retry</a></span>
              </div>
            </div>
            <div class="sheet-actions">
              <button type="submit" class="btn btn-primary" :disabled="isSubmitting || loadingAgents">
                <font-awesome-icon :icon="isSubmitting ? 'spinner' : 'plus'" :spin="isSubmitting" class="icon-left" />
                {{ isSubmitting ? 'Submitting...' : 'Add Stream' }}
              </button>
              <button type="button" class="btn btn-outline-secondary" @click="$emit('close')" :disabled="isSubmitting">
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faPlus, faSpinner, faExclamationTriangle, faCheckCircle } from '@fortawesome/free-solid-svg-icons'
import { library } from '@fortawesome/fontawesome-svg-core'
import { useToast } from 'vue-toastification'
import axios from 'axios'

library.add(faPlus, faSpinner, faExclamationTriangle, faCheckCircle)

export default {
  name: 'MobileAddStreamModal',
  components: { FontAwesomeIcon },
  props: {
    isVisible: { type: Boolean, default: false },
    isDarkTheme: { type: Boolean, default: false }
  },
  emits: ['close', 'stream-created'],
  setup(props, { emit }) {
    const form = ref({ platform: '', room_url: '', agent_id: '' })
    const isSubmitting = ref(false)
    const isProcessing = ref(false)
    const progress = ref(0)
    const progressMessage = ref('Initializing...')
    const eventSource = ref(null)
    const toast = useToast()
    const agentsList = ref([])
    const loadingAgents = ref(false)
    const errorLoadingAgents = ref(false)
    const errorMessage = ref('')
    const retryCount = ref(0)
    const maxRetries = 3
    const showTooltip = ref(false)
    const hasError = ref(false)
    const errorDetails = ref('')
    const isComplete = ref(false)
    const messageChanged = ref(false)
    const lastMessage = ref('')

    const fetchAgents = async () => {
      if (retryCount.value >= maxRetries) {
        console.error('Max retries reached for fetching agents')
        errorLoadingAgents.value = true
        errorMessage.value = 'Unable to load agents after multiple attempts.'
        loadingAgents.value = false
        return
      }

      loadingAgents.value = true
      errorLoadingAgents.value = false
      errorMessage.value = ''
      try {
        console.debug('Fetching agents from     https://monitor-backend.jetcamstudio.com:5000api/agents')
        const response = await axios.get('     https://monitor-backend.jetcamstudio.com:5000api/agents', {
          headers: {
            'Accept': 'application/json'
          },
          withCredentials: true,
          timeout: 10000
        })
        console.debug('API response:', response.data)
        let agentsData = response.data
        if (!Array.isArray(agentsData)) {
          agentsData = Object.values(agentsData || {})
        }
        agentsList.value = agentsData.map(agent => ({
          id: agent.id,
          username: agent.username || 'Unknown',
          email: agent.email || '',
          role: agent.role || ''
        }))
        retryCount.value = 0
        if (agentsList.value.length === 0) {
          console.warn('No agents returned from API')
          toast.warning('No agents available')
        }
      } catch (error) {
        console.error('Error fetching agents:', error)
        errorLoadingAgents.value = true
        retryCount.value += 1
        if (error.code === 'ECONNABORTED') {
          errorMessage.value = 'Request timed out. Please check your network.'
        } else if (error.response) {
          const status = error.response.status
          const message = error.response.data?.message || 'Unknown error'
          errorMessage.value = `Failed to load agents: ${message} (Status: ${status})`
        } else if (error.request) {
          errorMessage.value = 'No response from server. Check if the server is running.'
        } else {
          errorMessage.value = `Error: ${error.message}`
        }
        console.error('Retry count:', retryCount.value)
        toast.error(errorMessage.value)
      } finally {
        loadingAgents.value = false
      }
    }

    const retryFetchAgents = async () => {
      console.debug('Retrying fetch agents, attempt:', retryCount.value + 1)
      const delay = Math.pow(2, retryCount.value) * 1000
      await new Promise(resolve => setTimeout(resolve, delay))
      fetchAgents()
    }

    const connectSSE = (jobId) => {
      if (eventSource.value) eventSource.value.close()
      const sseUrl = `     https://monitor-backend.jetcamstudio.com:5000api/streams/interactive/sse?job_id=${jobId}`
      eventSource.value = new EventSource(sseUrl, { withCredentials: true })

      eventSource.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.debug('SSE message:', data)
          progress.value = data.progress || 0
          if (data.message && data.message !== lastMessage.value) {
            lastMessage.value = data.message
            progressMessage.value = data.message
            messageChanged.value = true
          }
          if (data.error) {
            hasError.value = true
            errorDetails.value = data.error
            progressMessage.value = 'Error occurred'
            toast.error(data.error)
            setTimeout(resetState, 3000)
          }
        } catch (error) {
          console.error('SSE message parse error:', error)
          hasError.value = true
          errorDetails.value = 'Error processing stream creation updates'
          toast.error('Error processing stream creation updates')
        }
      }

      eventSource.value.addEventListener('error', () => {
        console.error('SSE connection error for job:', jobId)
        hasError.value = true
        errorDetails.value = 'Lost connection to stream creation server'
        toast.error('Lost connection to stream creation server')
        setTimeout(resetState, 3000)
      })

      eventSource.value.addEventListener('completed', (event) => {
        try {
          const streamData = JSON.parse(event.data)
          console.debug('SSE completed:', streamData)
          isComplete.value = true
          toast.success('Stream created successfully')
          setTimeout(() => {
            emit('stream-created', streamData)
            resetState()
          }, 2000)
        } catch (error) {
          console.error('SSE completed event parse error:', error)
          hasError.value = true
          errorDetails.value = 'Error processing stream creation completion'
          toast.error('Error processing stream creation completion')
          setTimeout(resetState, 3000)
        }
      })
    }

    const resetState = () => {
      if (eventSource.value) {
        eventSource.value.close()
        eventSource.value = null
      }
      progress.value = 0
      progressMessage.value = 'Initializing...'
      lastMessage.value = ''
      isSubmitting.value = false
      isProcessing.value = false
      hasError.value = false
      errorDetails.value = ''
      isComplete.value = false
      messageChanged.value = false
      showTooltip.value = false
      form.value = { platform: '', room_url: '', agent_id: '' }
      errorLoadingAgents.value = false
      errorMessage.value = ''
    }

    const handleSubmit = async () => {
      if (isSubmitting.value) return
      isSubmitting.value = true
      try {
        console.debug('Submitting stream creation:', form.value)
        const response = await axios.post('     https://monitor-backend.jetcamstudio.com:5000api/streams/interactive', form.value, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          withCredentials: true,
          timeout: 10000
        })
        console.debug('Stream creation response:', response.data)
        isSubmitting.value = false
        isProcessing.value = true
        connectSSE(response.data.job_id)
      } catch (error) {
        console.error('Error starting stream creation:', error)
        isSubmitting.value = false
        let message = 'Failed to start stream creation'
        if (error.response) {
          message = error.response.data?.message || `Error: ${error.response.status}`
        } else if (error.request) {
          message = 'No response from server. Check if the server is running.'
        } else {
          message = error.message
        }
        toast.error(message)
      }
    }

    const progressBarStyle = computed(() => {
      let backgroundColor = '#4361ee' // Default blue
      if (hasError.value) {
        backgroundColor = '#e5383b' // Red for errors
      } else if (progress.value < 30) {
        backgroundColor = '#f4a261' // Yellow for early progress
      } else if (progress.value >= 100) {
        backgroundColor = '#2a9d8f' // Green for completion
      }
      return {
        width: `${progress.value}%`,
        backgroundColor
      }
    })

    // Add platform detection logic
    const detectPlatformFromUrl = (url) => {
      if (!url) return ''
      try {
        const parsedUrl = new URL(url.toLowerCase())
        if (parsedUrl.hostname.includes('chaturbate')) return 'chaturbate'
        if (parsedUrl.hostname.includes('stripchat')) return 'stripchat'
      } catch {
        if (url.toLowerCase().includes('chaturbate')) return 'chaturbate'
        if (url.toLowerCase().includes('stripchat')) return 'stripchat'
      }
      return ''
    }

    // Add watcher for URL changes
    watch(
      () => form.value.room_url,
      (newUrl) => {
        const detectedPlatform = detectPlatformFromUrl(newUrl)
        if (detectedPlatform) {
          form.value.platform = detectedPlatform
        }
      }
    )

    watch(() => props.isVisible, (newVisible) => {
      if (newVisible) {
        retryCount.value = 0
        fetchAgents()
      } else {
        resetState()
      }
    })

    onMounted(() => {
      if (props.isVisible) fetchAgents()
    })

    onUnmounted(() => {
      if (eventSource.value) {
        eventSource.value.close()
        eventSource.value = null
      }
    })

    return {
      form,
      isSubmitting,
      isProcessing,
      progress,
      progressMessage,
      handleSubmit,
      agentsList,
      loadingAgents,
      errorLoadingAgents,
      errorMessage,
      retryFetchAgents,
      showTooltip,
      hasError,
      errorDetails,
      isComplete,
      messageChanged,
      progressBarStyle
    }
  }
}
</script>

<style scoped>
.bottom-sheet-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  z-index: 1000;
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
}

.bottom-sheet-container {
  width: 100%;
  background-color: var(--card-bg);
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
  overflow: hidden;
  transform: translateY(0);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
}

.bottom-sheet-handle {
  width: 40px;
  height: 4px;
  border-radius: 2px;
  background-color: var(--border-color);
  margin: 12px auto;
}

.sheet-content {
  padding: 0 20px 24px;
}

.sheet-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.sheet-icon {
  font-size: 1.4rem;
  color: var(--primary-color);
  margin-right: 12px;
}

.sheet-header h3 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-color);
}

.stream-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 6px;
}

.form-control {
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  font-size: 0.95rem;
  color: var(--text-color);
  background-color: var(--card-bg);
}

.form-control::placeholder {
  color: var(--text-light);
}

.loading-indicator,
.error-indicator {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  color: var(--text-light);
  margin-top: 4px;
  gap: 6px;
}

.error-indicator {
  color: var(--danger-color);
}

.error-indicator a {
  color: var(--primary-color);
  text-decoration: underline;
  cursor: pointer;
}

.sheet-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn {
  width: 100%;
  padding: 12px;
  border-radius: var(--border-radius-sm);
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.btn:active {
  transform: scale(0.98);
}

.btn .icon-left {
  margin-right: 8px;
}

.btn-primary {
  background-color: var(--primary-color);
  border: none;
  color: white;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-outline-secondary {
  background-color: transparent;
  border: 1.5px solid var(--border-color);
  color: var(--text-color);
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.progress-bar-container {
  width: 100%;
  height: 12px;
  background-color: var(--border-color);
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-bar-container.error {
  animation: shake 0.5s ease-in-out;
}

.progress-bar {
  height: 100%;
  position: relative;
  transition: width 0.5s ease, background-color 0.3s ease;
  overflow: hidden;
}

.progress-bar-inner {
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg,
      rgba(255, 255, 255, 0.2) 25%,
      transparent 25%,
      transparent 50%,
      rgba(255, 255, 255, 0.2) 50%,
      rgba(255, 255, 255, 0.2) 75%,
      transparent 75%,
      transparent);
  background-size: 30px 30px;
  animation: move-stripes 1s linear infinite;
}

.progress-bar:not(.error) .progress-bar-inner {
  animation: move-stripes 1s linear infinite, pulse 2s ease-in-out infinite;
}

.progress-tooltip {
  position: absolute;
  top: -30px;
  left: 50%;
  transform: translateX(-50%);
  background-color: var(--text-color);
  color: var(--card-bg);
  padding: 4px 8px;
  border-radius: var(--border-radius-sm);
  font-size: 0.8rem;
  white-space: nowrap;
  z-index: 10;
  animation: fade-in 0.3s ease;
}

.progress-message {
  font-size: 0.95rem;
  color: var(--text-color);
  text-align: center;
  margin: 0;
  transition: opacity 0.3s ease;
}

.progress-message.fade-in {
  animation: fade-in 0.5s ease;
}

.progress-message.error-message {
  color: var(--danger-color);
  font-weight: 500;
}

.error-details {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--danger-color);
  font-size: 0.85rem;
  text-align: center;
  margin-top: 8px;
}

.confetti-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--success-color);
  font-size: 1rem;
  font-weight: 600;
  margin-top: 12px;
  animation: bounce 0.5s ease;
}

.completion-icon {
  font-size: 1.5rem;
}

.confetti-enter-active {
  animation: bounce 0.5s ease;
}

.confetti-leave-active {
  animation: fade-out 0.3s ease;
}

.sheet-slide-enter-active,
.sheet-slide-leave-active {
  transition: opacity 0.3s ease;
}

.sheet-slide-enter-from,
.sheet-slide-leave-to {
  opacity: 0;
}

@keyframes move-stripes {
  0% {
    background-position: 0 0;
  }

  100% {
    background-position: 30px 0;
  }
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.8;
  }
}

@keyframes shake {

  0%,
  100% {
    transform: translateX(0);
  }

  20%,
  60% {
    transform: translateX(-5px);
  }

  40%,
  80% {
    transform: translateX(5px);
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes fade-out {
  from {
    opacity: 1;
  }

  to {
    opacity: 0;
  }
}

@keyframes bounce {

  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-10px);
  }
}

:where([data-theme="light"]) {
  --primary-color: #4361ee;
  --secondary-color: #3f37c9;
  --background-color: #f8f9fa;
  --card-bg: #ffffff;
  --text-color: #333333;
  --text-light: #777777;
  --border-color: #e0e0e0;
  --danger-color: #e5383b;
  --success-color: #2a9d8f;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  --border-radius: 12px;
  --border-radius-sm: 8px;
}

:where([data-theme="dark"]) {
  --primary-color: #4cc9f0;
  --secondary-color: #4895ef;
  --background-color: #121212;
  --card-bg: #1e1e1e;
  --text-color: #f8f9fa;
  --text-light: #b0b0b0;
  --border-color: #333333;
  --danger-color: #e5383b;
  --success-color: #2a9d8f;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
}
</style>
