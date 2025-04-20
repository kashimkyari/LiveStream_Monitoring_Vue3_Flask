<template>
  <div class="mobile-loading-spinner-container" :class="{ 'full-page': fullPage }">
    <div class="mobile-loading-spinner" :style="spinnerStyle">
      <div 
        class="spinner-circle" 
        v-for="i in circleCount" 
        :key="i" 
        :style="`--i: ${i}`"
      ></div>
    </div>
    <div class="spinner-text" v-if="text">{{ text }}</div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'MobileLoadingSpinner',
  
  props: {
    size: {
      type: Number,
      default: 60
    },
    text: {
      type: String,
      default: ''
    },
    fullPage: {
      type: Boolean,
      default: false
    },
    circleCount: {
      type: Number,
      default: 8
    },
    color: {
      type: String,
      default: null // Will use CSS variables if null
    }
  },
  
  setup(props) {
    // Calculate dynamic styles based on props
    const spinnerStyle = computed(() => {
      return {
        width: `${props.size}px`,
        height: `${props.size}px`,
        ...(props.color ? { '--circle-color': props.color } : {})
      }
    })
    
    return {
      spinnerStyle
    }
  }
}
</script>

<style scoped>
.mobile-loading-spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.mobile-loading-spinner-container.full-page {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--light-bg);
  z-index: 1000;
}

[data-theme='dark'] .mobile-loading-spinner-container.full-page {
  background-color: var(--dark-bg);
}

.mobile-loading-spinner {
  position: relative;
  width: 60px;
  height: 60px;
}

.spinner-circle {
  --circle-color: var(--light-primary);
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--circle-color);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(calc(var(--i) * (360deg / var(--total-circles, 8)))) translateY(calc(-1 * var(--size, 20px)));
  animation: pulse 1.2s ease-in-out infinite;
  animation-delay: calc(var(--i) * 0.15s);
}

[data-theme='dark'] .spinner-circle {
  --circle-color: var(--dark-primary);
}

.spinner-text {
  margin-top: 15px;
  font-size: 0.85rem;
  color: var(--light-text);
}

[data-theme='dark'] .spinner-text {
  color: var(--dark-text);
}

@keyframes pulse {
  0% {
    opacity: 0.3;
    transform: translate(-50%, -50%) rotate(calc(var(--i) * (360deg / var(--total-circles, 8)))) translateY(calc(-1 * var(--size, 20px)));
  }
  50% {
    opacity: 1;
    transform: translate(-50%, -50%) rotate(calc(var(--i) * (360deg / var(--total-circles, 8)))) translateY(calc(-1.2 * var(--size, 20px)));
  }
  100% {
    opacity: 0.3;
    transform: translate(-50%, -50%) rotate(calc(var(--i) * (360deg / var(--total-circles, 8)))) translateY(calc(-1 * var(--size, 20px)));
  }
}

/* Smaller size for mobile devices */
@media (max-width: 768px) {
  .mobile-loading-spinner {
    width: 50px;
    height: 50px;
  }
  
  .spinner-circle {
    width: 6px;
    height: 6px;
  }
  
  .spinner-text {
    font-size: 0.8rem;
  }
}
</style>