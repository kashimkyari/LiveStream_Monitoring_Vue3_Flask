<template>
  <div class="mobile-modal-overlay" @click.self="closeModal">
    <div class="mobile-modal-content">
      <div class="mobile-modal-header">
        <h3>Add Stream</h3>
        <button class="mobile-modal-close" @click="closeModal">×</button>
      </div>
      
      <div class="mobile-modal-body">
        <!-- Error/Success Messages -->
        <div v-if="error" class="error-message">
          <span class="error-icon">⚠️</span>
          <span>{{ error }}</span>
        </div>
        
        <div v-if="message && !error" class="success-message">
          <span class="success-icon">✓</span>
          <span>{{ message }}</span>
        </div>
        
        <!-- Form -->
        <form @submit.prevent="submitForm" class="mobile-form">
          <div class="form-group">
            <label for="roomUrl">Stream URL</label>
            <input
              id="roomUrl"
              v-model="formData.room_url"
              type="url"
              class="form-control"
              placeholder="Enter complete URL (e.g., https://chaturbate.com/username)"
              required
              :disabled="isSubmitting || jobStatus === 'processing'"
            />
            <small class="form-hint">Enter the complete URL including https://</small>
          </div>
          
          <div class="form-group">
            <label for="platform">Platform</label>
            <select
              id="platform"
              v-model="formData.platform"
              class="form-control"
              required
              :disabled="isSubmitting || jobStatus === 'processing'"
            >
              <option value="">Select Platform</option>
              <option value="chaturbate">Chaturbate</option>
              <option value="stripchat">Stripchat</option>
            </select>
          </div>
          
          <!-- Job Status Section -->
          <div v-if="jobStatus" class="job-status-section">
            <div class="job-status-header">
              <span class="job-status-title">Stream Creation Status</span>
              <span 
                class="job-status-badge"
                :class="{
                  'status-pending': jobStatus === 'pending',
                  'status-processing': jobStatus === 'processing',
                  'status-completed': jobStatus === 'completed',
                  'status-failed': jobStatus === 'failed'
                }"
              >
                {{ formatJobStatus(jobStatus) }}
              </span>
            </div>
            
            <div v-if="jobStatus === 'processing'" class="progress-container">
              <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
            </div>
            
            <div v-if="jobProgress" class="job-progress-message">
              {{ jobProgress }}
            </div>
          </div>
          
          <div class="form-actions">
            <button
              type="button"
              @click="closeModal"
              class="cancel-button"
              :disabled="isSubmitting || jobStatus === 'processing'"
            >
              Cancel
            </button>
            
            <button
              type="submit"
              class="submit-button"
              :disabled="!formData.room_url || !formData.platform || isSubmitting || jobStatus === 'processing'"
            >
              <span v-if="isSubmitting || jobStatus === 'processing'">
                <strong>Processing...</strong>
              </span>
              <span v-else><strong>Add Stream</strong></span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

export default {
  name: 'MobileAddStreamModal',
  
  emits: ['close', 'stream-created'],
  
  setup(props, { emit }) {
    // Form data
    const formData = ref({
      room_url: '',
      platform: ''
    })
    
    // UI states
    const isSubmitting = ref(false)
    const error = ref('')
    const message = ref('')
    
    // Job tracking
    const jobId = ref(null)
    const jobStatus = ref('')
    const jobProgress = ref('')
    const progress = ref(0)
    const statusCheckInterval = ref(null)
    
    // Submit form handler
    const submitForm = async () => {
      try {
        isSubmitting.value = true
        error.value = ''
        message.value = ''
        
        // Mobile optimization: Add mobile parameter to reduce data usage
        const response = await axios.post('/api/streams', {
          ...formData.value
        })
        
        if (response.data.job_id) {
          // Handle job-based response
          jobId.value = response.data.job_id
          jobStatus.value = 'pending'
          message.value = 'Stream creation started. Please wait while we process your request.'
          startJobStatusCheck()
        } else {
          // Handle immediate response
          message.value = response.data.message || 'Stream added successfully'
          emit('stream-created')
          setTimeout(() => {
            closeModal()
          }, 1500)
        }
      } catch (err) {
        console.error('Error creating stream:', err)
        error.value = err.response?.data?.message || 'Failed to add stream'
        isSubmitting.value = false
      }
    }
    
    // Format job status for display
    const formatJobStatus = (status) => {
      switch (status) {
        case 'pending':
          return 'Pending'
        case 'processing':
          return 'Processing'
        case 'completed':
          return 'Completed'
        case 'failed':
          return 'Failed'
        default:
          return 'Unknown'
      }
    }
    
    // Job status polling
    const startJobStatusCheck = () => {
      // Clear any existing interval
      if (statusCheckInterval.value) {
        clearInterval(statusCheckInterval.value)
      }
      
      // Set progress to initial state
      progress.value = 5
      
      // Check status immediately
      checkJobStatus()
      
      // Then check every 2 seconds
      statusCheckInterval.value = setInterval(checkJobStatus, 2000)
    }
    
    const checkJobStatus = async () => {
      if (!jobId.value) return
      
      try {
        // Mobile optimization: Add mobile parameter to reduce data usage
        const response = await axios.get(`/api/streams/interactive/sse?job_id=${jobId.value}`)
        
        jobStatus.value = response.data.status
        jobProgress.value = response.data.progress_message || ''
        
        // Update progress bar
        if (jobStatus.value === 'pending') {
          progress.value = 5
        } else if (jobStatus.value === 'processing') {
          // Increment progress by 10% each check, max 90%
          progress.value = Math.min(progress.value + 10, 90)
        } else if (jobStatus.value === 'completed') {
          progress.value = 100
          message.value = 'Stream added successfully'
          error.value = ''
          stopJobStatusCheck()
          emit('stream-created')
          setTimeout(() => {
            closeModal()
          }, 1500)
        } else if (jobStatus.value === 'failed') {
          progress.value = 100
          error.value = response.data.error || 'Failed to add stream'
          message.value = ''
          stopJobStatusCheck()
          isSubmitting.value = false
        }
      } catch (err) {
        console.error('Error checking job status:', err)
        error.value = 'Failed to check job status'
        stopJobStatusCheck()
        isSubmitting.value = false
      }
    }
    
    const stopJobStatusCheck = () => {
      if (statusCheckInterval.value) {
        clearInterval(statusCheckInterval.value)
        statusCheckInterval.value = null
      }
    }
    
    const closeModal = () => {
      // Stop any ongoing requests
      stopJobStatusCheck()
      
      // Reset form state
      isSubmitting.value = false
      
      // Emit close event
      emit('close')
    }
    
    // Clean up on unmount
    onBeforeUnmount(() => {
      stopJobStatusCheck()
    })
    
    return {
      formData,
      isSubmitting,
      error,
      message,
      jobStatus,
      jobProgress,
      progress,
      submitForm,
      closeModal,
      formatJobStatus
    }
  }
}
</script>

<style scoped>
.mobile-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
  padding: 0 16px;
}

.mobile-modal-content {
  background-color: var(--light-bg, #ffffff);
  border-radius: 12px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  visibility: visible !important;
  opacity: 1 !important;
}

[data-theme='dark'] .mobile-modal-content {
  background-color: var(--dark-bg, #1a1a1a);
  color: var(--dark-text, #f0f0f0);
}

.mobile-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--light-border, rgba(0, 0, 0, 0.1));
}

[data-theme='dark'] .mobile-modal-header {
  border-bottom: 1px solid var(--dark-border, rgba(255, 255, 255, 0.1));
}

.mobile-modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--light-text, #333333);
}

[data-theme='dark'] .mobile-modal-header h3 {
  color: var(--dark-text, #ffffff);
}

.mobile-modal-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 1.2rem;
  padding: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mobile-modal-body {
  padding: 16px;
}

.error-message {
  padding: 12px;
  background-color: rgba(244, 67, 54, 0.1);
  border-left: 3px solid #f44336;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f44336;
}

.error-icon {
  color: #f44336;
}

.success-message {
  padding: 12px;
  background-color: rgba(76, 175, 80, 0.1);
  border-left: 3px solid #4caf50;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #4caf50;
}

.success-icon {
  color: #4caf50;
}

.mobile-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: var(--light-text, #333333);
  font-size: 1rem;
  margin-bottom: 4px;
}

[data-theme='dark'] .form-group label {
  color: var(--dark-text, #ffffff);
}

.form-control {
  padding: 14px;
  border: 1px solid var(--light-border, rgba(0, 0, 0, 0.15));
  border-radius: 8px;
  background-color: var(--light-input-bg, #ffffff);
  color: var(--light-text, #333333);
  font-size: 1rem;
  width: 100%;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

[data-theme='dark'] .form-control {
  background-color: var(--dark-input-bg, #2a2a2a);
  border-color: var(--dark-border, rgba(255, 255, 255, 0.15));
  color: var(--dark-text, #ffffff);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.form-control:focus {
  border-color: var(--primary-color, #4361ee);
  outline: none;
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.15);
}

.form-control:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.form-hint {
  font-size: 0.85rem;
  color: var(--light-text-muted, #666666);
  margin-top: 6px;
}

[data-theme='dark'] .form-hint {
  color: var(--dark-text-muted, #aaaaaa);
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.cancel-button,
.submit-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 15px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 1rem;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.cancel-button {
  background-color: var(--light-button-bg, #f5f5f5);
  border: 1px solid var(--light-border, rgba(0, 0, 0, 0.1));
  color: var(--light-text, #333333);
}

[data-theme='dark'] .cancel-button {
  background-color: var(--dark-button-bg, #2d2d2d);
  border-color: var(--dark-border, rgba(255, 255, 255, 0.1));
  color: var(--dark-text, #ffffff);
}

.cancel-button:hover {
  background-color: var(--light-button-hover-bg, #eeeeee);
}

[data-theme='dark'] .cancel-button:hover {
  background-color: var(--dark-button-hover-bg, #3a3a3a);
}

.submit-button {
  background-color: var(--primary-color, #4361ee);
  border: none;
  color: white;
  position: relative;
  overflow: hidden;
}

.submit-button:hover {
  background-color: var(--primary-hover-color, #3a56e4);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.submit-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.submit-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Job Status Section */
.job-status-section {
  background-color: var(--muted-bg);
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
}

.job-status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.job-status-title {
  font-weight: 600;
  color: var(--text-color);
}

.job-status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-pending {
  background-color: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.status-processing {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.status-completed {
  background-color: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.status-failed {
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.progress-container {
  height: 8px;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-bar {
  height: 100%;
  background-color: var(--primary-color);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.job-progress-message {
  font-size: 0.9rem;
  color: var(--text-muted);
}

/* Improve touch targets for mobile */
@media (max-width: 480px) {
  .cancel-button,
  .submit-button {
    padding: 16px;
  }
  
  .form-control {
    padding: 14px;
  }
}
</style>