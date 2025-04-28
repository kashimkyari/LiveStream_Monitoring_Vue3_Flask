<template>
  <transition name="slide-up">
    <div v-if="show" class="notification-detection" :class="{ 'notification-danger': isDanger }" @click="onClick">
      <div class="notification-content">
        <div class="notification-icon">
          <font-awesome-icon :icon="icon" />
        </div>
        <div class="notification-text">
          <div class="notification-title">{{ title }}</div>
          <div class="notification-details" v-if="details">{{ details }}</div>
          <div class="notification-source" v-if="source">{{ source }}</div>
        </div>
        <div class="notification-actions">
          <button class="action-btn" @click.stop="dismiss">
            <font-awesome-icon icon="times" />
          </button>
        </div>
      </div>
      <div class="notification-progress">
        <div class="progress-bar" :style="progressStyle"></div>
      </div>
    </div>
  </transition>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';

export default {
  name: 'MobileDetectionNotification',
  props: {
    title: {
      type: String,
      default: 'Detection Alert'
    },
    details: {
      type: String,
      default: ''
    },
    source: {
      type: String,
      default: ''
    },
    type: {
      type: String,
      default: 'info' // 'info', 'warning', 'danger'
    },
    autoHide: {
      type: Boolean,
      default: true
    },
    duration: {
      type: Number,
      default: 5000 // 5 seconds
    },
    detection: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['click', 'dismiss'],
  setup(props, { emit }) {
    const show = ref(false);
    const progress = ref(100);
    const progressInterval = ref(null);
    
    // Compute icon based on notification type
    const icon = computed(() => {
      switch (props.type.toLowerCase()) {
        case 'keyword':
        case 'chat':
          return 'comment-dots';
        case 'object':
          return 'eye';
        case 'warning':
          return 'exclamation-triangle';
        case 'danger':
          return 'exclamation-circle';
        default:
          return 'bell';
      }
    });
    
    // Check if it's a high-priority notification
    const isDanger = computed(() => {
      return props.type.toLowerCase() === 'danger' || 
        props.type.toLowerCase() === 'object' ||
        props.type.toLowerCase() === 'keyword';
    });
    
    // Style for the progress bar
    const progressStyle = computed(() => {
      return {
        width: `${progress.value}%`
      };
    });
    
    // Handle click on notification
    const onClick = () => {
      emit('click', props.detection);
      dismiss();
    };
    
    // Dismiss the notification
    const dismiss = () => {
      show.value = false;
      stopProgressTimer();
      emit('dismiss');
    };
    
    // Start the progress timer for auto-hide
    const startProgressTimer = () => {
      if (!props.autoHide) return;
      
      const step = 100 / (props.duration / 100); // decrease by this percentage every 100ms
      
      progressInterval.value = setInterval(() => {
        progress.value = Math.max(0, progress.value - step);
        
        if (progress.value <= 0) {
          dismiss();
        }
      }, 100);
    };
    
    // Stop the progress timer
    const stopProgressTimer = () => {
      if (progressInterval.value) {
        clearInterval(progressInterval.value);
        progressInterval.value = null;
      }
    };
    
    // Show notification after a small delay
    onMounted(() => {
      setTimeout(() => {
        show.value = true;
        startProgressTimer();
      }, 100);
    });
    
    // Clean up on unmount
    onBeforeUnmount(() => {
      stopProgressTimer();
    });
    
    // Watch for changes to the duration prop
    watch(() => props.duration, () => {
      stopProgressTimer();
      progress.value = 100;
      startProgressTimer();
    });
    
    return {
      show,
      icon,
      isDanger,
      progressStyle,
      onClick,
      dismiss
    };
  }
};
</script>

<style scoped>
/* Component is styled in App.vue for consistent theme application */

/* Additional styling specific to this component */
.notification-content {
  display: flex;
  align-items: flex-start;
}

.notification-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  background-color: rgba(66, 153, 225, 0.1);
  color: var(--light-primary);
}

[data-theme='dark'] .notification-icon {
  background-color: rgba(99, 179, 237, 0.1);
  color: var(--dark-primary);
}

.notification-danger .notification-icon {
  background-color: rgba(245, 101, 101, 0.1);
  color: var(--light-danger);
}

[data-theme='dark'] .notification-danger .notification-icon {
  background-color: rgba(252, 129, 129, 0.1);
  color: var(--dark-danger);
}

.notification-text {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  margin-bottom: 2px;
  color: var(--light-text);
}

[data-theme='dark'] .notification-title {
  color: var(--dark-text);
}

.notification-details {
  font-size: 0.85rem;
  margin-bottom: 2px;
  color: var(--light-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

[data-theme='dark'] .notification-details {
  color: var(--dark-text-secondary);
}

.notification-source {
  font-size: 0.75rem;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .notification-source {
  color: var(--dark-text-secondary);
}

.notification-actions {
  flex-shrink: 0;
  margin-left: 8px;
}

.action-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: transparent;
  color: var(--light-text-secondary);
  border: 1px solid var(--light-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme='dark'] .action-btn {
  color: var(--dark-text-secondary);
  border-color: var(--dark-border);
}

.action-btn:hover {
  background-color: var(--light-danger);
  color: white;
  border-color: var(--light-danger);
}

[data-theme='dark'] .action-btn:hover {
  background-color: var(--dark-danger);
  border-color: var(--dark-danger);
}

.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background-color: var(--light-border);
  overflow: hidden;
  border-radius: 0 0 8px 8px;
}

[data-theme='dark'] .notification-progress {
  background-color: var(--dark-border);
}

.progress-bar {
  height: 100%;
  background-color: var(--light-primary);
  transition: width 0.1s linear;
}

[data-theme='dark'] .progress-bar {
  background-color: var(--dark-primary);
}

.notification-danger .progress-bar {
  background-color: var(--light-danger);
}

[data-theme='dark'] .notification-danger .progress-bar {
  background-color: var(--dark-danger);
}

/* Animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(10px);
  opacity: 0;
}
</style>