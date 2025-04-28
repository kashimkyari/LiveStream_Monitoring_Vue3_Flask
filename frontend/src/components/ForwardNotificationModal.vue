<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <button class="modal-close" @click="$emit('close')" v-wave>
        <font-awesome-icon icon="times" />
      </button>
      <div class="modal-header">
        <h3>Forward Notification</h3>
      </div>
      <div class="modal-body">
        <div class="notification-preview">
          <h4>{{ formatEventType(notification.event_type) }}</h4>
          <p>{{ getNotificationMessage(notification) }}</p>
          <div v-if="notification.details.detections" class="detection-preview">
            <div 
              v-for="(detection, idx) in notification.details.detections.slice(0, 3)" 
              :key="idx"
              class="detection-item"
            >
              <span class="detection-class">{{ detection.class }}</span>
              <span class="detection-confidence">{{ (detection.confidence * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
        <div class="form-group">
          <label for="forward-agent">Select Agent</label>
          <select 
            id="forward-agent" 
            v-model="form.agent_id"
            required
          >
            <option value="">Select Agent</option>
            <option 
              v-for="agent in agents" 
              :key="agent.id" 
              :value="agent.id"
            >
              {{ agent.username }} ({{ agent.assignments?.length || 0 }} assignments)
            </option>
          </select>
        </div>
        <div class="form-group">
          <label for="forward-message">Additional Message (Optional)</label>
          <textarea 
            id="forward-message" 
            v-model="form.message"
            placeholder="Add any additional instructions for the agent..."
          ></textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button 
          @click="submitForm" 
          class="submit-button"
          :disabled="!form.agent_id"
          v-wave
        >
          Forward Notification
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ForwardNotificationModal',
  props: {
    notification: Object,
    agents: Array
  },
  emits: ['close', 'submit'],
  setup(props, { emit }) {
    const form = ref({
      agent_id: null,
      message: ''
    })
    
    const formatEventType = (type) => {
      const types = {
        'object_detection': 'Object Detection',
        'chat_detection': 'Chat Detection',
        'audio_detection': 'Audio Detection',
        'stream_created': 'Stream Created'
      }
      return types[type] || type
    }
    
    const getNotificationMessage = (notification) => {
      if (notification.event_type === 'object_detection') {
        const detections = notification.details.detections || []
        const detectionList = detections.map(d => d.class).join(', ')
        return `Detected ${detectionList} in ${notification.details.streamer_name}'s stream`
      } else if (notification.event_type === 'chat_detection') {
        const keywords = notification.details.keywords || []
        return `Detected flagged keywords (${keywords.join(', ')}) in chat`
      } else if (notification.event_type === 'audio_detection') {
        return `Detected flagged audio: ${notification.details.keyword}`
      } else if (notification.event_type === 'stream_created') {
        return `New stream created for ${notification.details.streamer_username}`
      }
      return notification.details.message || 'Notification'
    }
    
    const submitForm = () => {
      emit('submit', {
        notification: props.notification,
        agent_id: form.value.agent_id,
        message: form.value.message
      })
      form.value = {
        agent_id: null,
        message: ''
      }
    }
    
    return {
      form,
      formatEventType,
      getNotificationMessage,
      submitForm
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
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
  position: relative;
}

.modal-close {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.modal-close:hover {
  opacity: 1;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid var(--input-border);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.modal-body {
  padding: 20px;
}

.notification-preview {
  background-color: var(--hover-bg);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.notification-preview h4 {
  margin: 0 0 10px 0;
  font-size: 1.1rem;
}

.detection-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.detection-item {
  background-color: var(--hover-bg);
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
}

.detection-class {
  font-weight: 600;
  margin-right: 5px;
}

.detection-confidence {
  opacity: 0.7;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 0.9rem;
  font-weight: 500;
}

.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 5px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 0.9rem;
}

.form-group textarea {
  min-height: 100px;
  resize: vertical;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--input-border);
  display: flex;
  justify-content: flex-end;
}

.submit-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.submit-button:hover {
  opacity: 0.9;
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Responsive styles */
@media (max-width: 576px) {
  .modal-footer {
    flex-direction: column;
  }
  
  .submit-button {
    width: 100%;
  }
}
</style>