<template>
  <div class="detection-controls">
    <button 
      class="detection-toggle"
      :class="{
        'active': isDetecting,
        'online': isOnline,
        'loading': isLoading
      }"
      :disabled="!isOnline || !canToggleDetection"
      @click="toggleDetection"
    >
      <span class="detection-icon">
        <font-awesome-icon 
          :icon="isLoading ? 'spinner' : isDetecting ? 'eye' : 'eye-slash'"
          :spin="isLoading"
        />
      </span>
      <span class="detection-label">
        {{ buttonLabel }}
      </span>
    </button>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

export default {
  name: 'DetectionControls',
  props: {
    streamId: {
      type: Number,
      required: true
    },
    streamUrl: {
      type: String,
      required: true
    },
    isOnline: {
      type: Boolean,
      required: true
    }
  },
  setup(props, { emit }) {
    const toast = useToast()
    const isDetecting = ref(false)
    const isLoading = ref(false)
    const canToggleDetection = ref(true)

    const buttonLabel = computed(() => {
      if (isLoading.value) return 'Processing...'
      if (isDetecting.value) return 'Stop Monitoring'
      return 'Start Monitoring'
    })

    const checkDetectionStatus = async () => {
      try {
        const response = await axios.get(`/api/detection-status/${props.streamId}`)
        isDetecting.value = response.data.active
      } catch (error) {
        console.error('Error checking detection status:', error)
      }
    }

    const toggleDetection = async () => {
      if (!canToggleDetection.value || !props.isOnline) return

      isLoading.value = true
      canToggleDetection.value = false

      try {
        const response = await axios.post('/api/trigger-detection', {
          stream_url: props.streamUrl,
          stream_id: props.streamId,
          stop: isDetecting.value
        })

        if (response.status === 200) {
          isDetecting.value = !isDetecting.value
          toast.success(isDetecting.value ? 'Monitoring started' : 'Monitoring stopped')
          emit('detection-toggled', isDetecting.value)
        }
      } catch (error) {
        console.error('Error toggling detection:', error)
        toast.error('Failed to toggle monitoring')
      } finally {
        isLoading.value = false
        // Add a small delay before allowing toggling again
        setTimeout(() => {
          canToggleDetection.value = true
        }, 1000)
      }
    }

    // Check initial detection status
    checkDetectionStatus()

    return {
      isDetecting,
      isLoading,
      canToggleDetection,
      buttonLabel,
      toggleDetection
    }
  }
}
</script>

<style scoped>
.detection-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}

.detection-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
  backdrop-filter: blur(4px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  background-color: rgba(108, 117, 125, 0.9);
  color: white;
}

.detection-toggle.online {
  background-color: rgba(40, 167, 69, 0.9);
}

.detection-toggle.active {
  background-color: rgba(255, 193, 7, 0.9);
}

.detection-toggle.active:hover:not(:disabled) {
  background-color: rgba(220, 53, 69, 0.9);
}

.detection-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: rgba(108, 117, 125, 0.9);
}

.detection-toggle:hover:not(:disabled) {
  transform: translateY(-2px);
}

.detection-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}

@media (max-width: 768px) {
  .detection-toggle {
    padding: 6px 10px;
    font-size: 0.8rem;
  }

  .detection-label {
    display: none;
  }
}
</style>