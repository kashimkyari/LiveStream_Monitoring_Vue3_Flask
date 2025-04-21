<template>
  <transition name="help-fade">
    <div
      v-if="visible"
      :class="['help-bubble', `help-bubble--${type}`, `help-bubble--${position}`]"
      ref="helpBubble"
    >
      <div class="help-bubble__content">
        <div class="help-bubble__icon">
          <font-awesome-icon :icon="bubbleIcon" />
        </div>
        <div class="help-bubble__text">
          <h4 v-if="title" class="help-bubble__title">{{ title }}</h4>
          <p class="help-bubble__message">{{ message }}</p>
        </div>
        <div class="help-bubble__close" @click="onDismiss">
          <font-awesome-icon icon="times" />
        </div>
      </div>
      <div v-if="actionButtons && actionButtons.length" class="help-bubble__actions">
        <button
          v-for="(button, index) in actionButtons"
          :key="index"
          :class="[
            'help-bubble__action',
            { 'help-bubble__action--primary': button.primary }
          ]"
          @click="button.action"
        >
          {{ button.label }}
        </button>
      </div>
      <div class="help-bubble__arrow"></div>
    </div>
  </transition>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

export default {
  name: 'HelpBubble',
  components: {
    FontAwesomeIcon
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: ''
    },
    message: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['info', 'tip', 'warning'].includes(value)
    },
    position: {
      type: String,
      default: 'bottom',
      validator: (value) => ['top', 'right', 'bottom', 'left'].includes(value)
    },
    actionButtons: {
      type: Array,
      default: () => []
    },
    anchorElement: {
      type: [HTMLElement, String],
      default: null
    }
  },
  emits: ['dismiss'],
  setup(props, { emit }) {
    const helpBubble = ref(null);
    
    const bubbleIcon = computed(() => {
      switch (props.type) {
        case 'info':
          return 'info-circle';
        case 'tip':
          return 'lightbulb';
        case 'warning':
          return 'exclamation-triangle';
        default:
          return 'info-circle';
      }
    });
    
    // Handle dismissal
    const onDismiss = () => {
      emit('dismiss');
    };
    
    // Position the bubble relative to the anchor element if provided
    const positionBubble = () => {
      const anchorElement = props.anchorElement;
      if (!anchorElement || !helpBubble.value) return;
      
      let anchorEl;
      if (typeof anchorElement === 'string') {
        anchorEl = document.querySelector(anchorElement);
      } else {
        anchorEl = anchorElement;
      }
      
      if (!anchorEl) return;
      
      const anchorRect = anchorEl.getBoundingClientRect();
      const bubbleRect = helpBubble.value.getBoundingClientRect();
      
      let left, top;
      
      // Position based on the position prop
      switch (props.position) {
        case 'top':
          left = anchorRect.left + (anchorRect.width / 2) - (bubbleRect.width / 2);
          top = anchorRect.top - bubbleRect.height - 10;
          break;
        case 'right':
          left = anchorRect.right + 10;
          top = anchorRect.top + (anchorRect.height / 2) - (bubbleRect.height / 2);
          break;
        case 'bottom':
          left = anchorRect.left + (anchorRect.width / 2) - (bubbleRect.width / 2);
          top = anchorRect.bottom + 10;
          break;
        case 'left':
          left = anchorRect.left - bubbleRect.width - 10;
          top = anchorRect.top + (anchorRect.height / 2) - (bubbleRect.height / 2);
          break;
      }
      
      // Ensure the bubble stays within the viewport
      if (left < 10) left = 10;
      if (top < 10) top = 10;
      if (left + bubbleRect.width > window.innerWidth - 10) {
        left = window.innerWidth - bubbleRect.width - 10;
      }
      if (top + bubbleRect.height > window.innerHeight - 10) {
        top = window.innerHeight - bubbleRect.height - 10;
      }
      
      // Apply position
      helpBubble.value.style.position = 'fixed';
      helpBubble.value.style.left = `${left}px`;
      helpBubble.value.style.top = `${top}px`;
    };
    
    // Reposition when visibility changes
    watch(() => props.visible, (isVisible) => {
      if (isVisible && props.anchorElement) {
        // Need to wait for the DOM to update
        setTimeout(positionBubble, 0);
      }
    });
    
    // Reposition on window resize if visible
    onMounted(() => {
      if (props.visible && props.anchorElement) {
        positionBubble();
      }
      
      window.addEventListener('resize', () => {
        if (props.visible && props.anchorElement) {
          positionBubble();
        }
      });
    });
    
    return {
      helpBubble,
      bubbleIcon,
      onDismiss
    };
  }
};
</script>

<style scoped>
.help-bubble {
  max-width: 320px;
  background-color: var(--bs-body-bg);
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 1000;
  position: relative;
  margin: 10px;
}

/* Position specific styles for arrow */
.help-bubble--top .help-bubble__arrow {
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
}

.help-bubble--right .help-bubble__arrow {
  left: -6px;
  top: 50%;
  transform: translateY(-50%) rotate(45deg);
}

.help-bubble--bottom .help-bubble__arrow {
  top: -6px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
}

.help-bubble--left .help-bubble__arrow {
  right: -6px;
  top: 50%;
  transform: translateY(-50%) rotate(45deg);
}

/* Type-specific styles */
.help-bubble--info {
  border-left: 4px solid var(--bs-info);
}

.help-bubble--tip {
  border-left: 4px solid var(--bs-success);
}

.help-bubble--warning {
  border-left: 4px solid var(--bs-warning);
}

.help-bubble__content {
  display: flex;
  padding: 16px;
  position: relative;
}

.help-bubble__icon {
  margin-right: 12px;
  font-size: 20px;
  height: 24px;
  width: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.help-bubble--info .help-bubble__icon {
  color: var(--bs-info);
}

.help-bubble--tip .help-bubble__icon {
  color: var(--bs-success);
}

.help-bubble--warning .help-bubble__icon {
  color: var(--bs-warning);
}

.help-bubble__text {
  flex: 1;
  font-size: 14px;
}

.help-bubble__title {
  font-weight: 600;
  margin: 0 0 4px 0;
  font-size: 16px;
  color: var(--bs-body-color);
}

.help-bubble__message {
  margin: 0;
  line-height: 1.5;
  color: var(--bs-body-color);
}

.help-bubble__close {
  position: absolute;
  top: 8px;
  right: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--bs-secondary);
  padding: 4px;
  transition: color 0.2s;
}

.help-bubble__close:hover {
  color: var(--bs-primary);
}

.help-bubble__actions {
  display: flex;
  justify-content: flex-end;
  padding: 8px 16px 16px;
  gap: 8px;
}

.help-bubble__action {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  background-color: var(--bs-tertiary-bg);
  color: var(--bs-body-color);
  transition: background-color 0.2s;
}

.help-bubble__action:hover {
  background-color: var(--bs-tertiary-bg-hover);
}

.help-bubble__action--primary {
  background-color: var(--bs-primary);
  color: #fff;
}

.help-bubble__action--primary:hover {
  background-color: var(--bs-primary-dark, var(--bs-primary));
  filter: brightness(0.9);
}

.help-bubble__arrow {
  position: absolute;
  width: 12px;
  height: 12px;
  background-color: var(--bs-body-bg);
  box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.1);
}

/* Animation */
.help-fade-enter-active,
.help-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.help-fade-enter-from,
.help-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Mobile Adjustments */
@media (max-width: 576px) {
  .help-bubble {
    max-width: calc(100vw - 40px);
    margin: 10px auto;
  }
  
  /* On mobile, always position at bottom center if no anchor */
  .help-bubble:not([style]) {
    position: fixed;
    bottom: 80px;
    left: 20px;
    right: 20px;
    margin: 0 auto;
  }
}
</style>