<template>
  <div class="stat-card" ref="statCard" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
    <div class="stat-icon" ref="statIcon">
      <font-awesome-icon :icon="icon" />
    </div>
    <div class="stat-content">
      <div class="stat-value" ref="statValue">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
    <div class="stat-wave" ref="statWave"></div>
  </div>
</template>

<script>
import anime from 'animejs/lib/anime.es.js'
import { ref, onMounted, watch } from 'vue'

export default {
  name: 'StatCard',
  props: {
    value: [Number, String],
    label: String,
    icon: String,
    color: {
      type: String,
      default: null
    },
    index: {
      type: Number,
      default: 0
    }
  },
  setup(props) {
    const statCard = ref(null)
    const statIcon = ref(null)
    const statValue = ref(null)
    const statWave = ref(null)

    // Entrance animation
    onMounted(() => {
      if (statCard.value) {
        anime({
          targets: statCard.value,
          translateY: [50, 0],
          opacity: [0, 1],
          scale: [0.9, 1],
          easing: 'spring(1, 80, 10, 0)',
          duration: 800,
          delay: 100 + (props.index * 100) // Staggered entrance based on index
        })
      }

      if (statIcon.value) {
        anime({
          targets: statIcon.value,
          rotateY: [90, 0],
          opacity: [0, 0.2],
          easing: 'easeOutElastic(1, .8)',
          duration: 1200,
          delay: 300 + (props.index * 100)
        })
      }

      if (statValue.value) {
        anime({
          targets: statValue.value,
          scale: [0, 1],
          opacity: [0, 1],
          easing: 'easeOutExpo',
          duration: 1000,
          delay: 200 + (props.index * 100)
        })
      }
    })

    // Watch for changes in value to animate updates
    watch(() => props.value, (newValue, oldValue) => {
      if (statValue.value && newValue !== oldValue) {
        anime({
          targets: statValue.value,
          scale: [1, 1.2, 1],
          color: ['#000', '#4caf50', '#000'],
          duration: 500,
          easing: 'easeInOutQuad'
        })
      }
    })

    // Hover animations
    const handleMouseEnter = () => {
      if (statCard.value) {
        anime({
          targets: statCard.value,
          translateY: -8,
          scale: 1.03,
          boxShadow: '0 15px 25px rgba(0, 0, 0, 0.15)',
          duration: 400,
          easing: 'easeOutQuad'
        })
      }

      if (statIcon.value) {
        anime({
          targets: statIcon.value,
          rotate: ['0deg', '15deg', '-15deg', '0deg'],
          opacity: 0.5,
          scale: 1.2,
          duration: 500,
          easing: 'easeInOutSine'
        })
      }

      if (statWave.value) {
        anime({
          targets: statWave.value,
          height: '120%',
          opacity: [0, 0.2],
          duration: 800,
          easing: 'easeOutQuart'
        })
      }
    }

    const handleMouseLeave = () => {
      if (statCard.value) {
        anime({
          targets: statCard.value,
          translateY: 0,
          scale: 1,
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          duration: 400,
          easing: 'easeOutQuad'
        })
      }

      if (statIcon.value) {
        anime({
          targets: statIcon.value,
          rotate: '0deg',
          opacity: 0.2,
          scale: 1,
          duration: 400,
          easing: 'easeOutQuad'
        })
      }

      if (statWave.value) {
        anime({
          targets: statWave.value,
          height: '0%',
          opacity: 0,
          duration: 400,
          easing: 'easeOutQuad'
        })
      }
    }

    return {
      statCard,
      statIcon,
      statValue,
      statWave,
      handleMouseEnter,
      handleMouseLeave
    }
  }
}
</script>

<style scoped>
.stat-card {
  background-color: var(--input-bg);
  border-radius: 16px;
  padding: 25px;
  text-align: left;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  height: 100%;
  border: 1px solid rgba(0, 0, 0, 0.05);
  cursor: pointer;
  z-index: 1;
}

.stat-content {
  z-index: 2;
  position: relative;
}

.stat-icon {
  font-size: 3rem;
  color: var(--primary-color);
  opacity: 0.2;
  position: absolute;
  top: 15px;
  right: 15px;
  z-index: 1;
  transition: all 0.3s ease;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 10px;
  display: block;
  line-height: 1;
}

.stat-label {
  font-size: 1rem;
  color: var(--text-color);
  opacity: 0.8;
  font-weight: 500;
}

.stat-wave {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 0;
  background: var(--primary-color);
  opacity: 0;
  transition: all 0.5s ease;
  z-index: 0;
  border-radius: 50% 50% 0 0;
}

/* Optional custom colors */
.stat-card.primary {
  background-color: rgba(var(--primary-rgb), 0.05);
}

.stat-card.success {
  background-color: rgba(var(--success-rgb), 0.05);
}

.stat-card.warning {
  background-color: rgba(var(--warning-rgb), 0.05);
}

.stat-card.danger {
  background-color: rgba(var(--danger-rgb), 0.05);
}

.stat-card.info {
  background-color: rgba(var(--info-rgb), 0.05);
}

@media (max-width: 768px) {
  .stat-card {
    padding: 20px;
  }
  
  .stat-value {
    font-size: 2rem;
  }
  
  .stat-icon {
    font-size: 2.5rem;
  }
}
</style>