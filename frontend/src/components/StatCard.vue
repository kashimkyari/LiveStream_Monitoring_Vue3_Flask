<template>
  <div 
    class="stat-card" 
    ref="statCard" 
    @mouseenter="handleMouseEnter" 
    @mouseleave="handleMouseLeave"
    @mousemove="handleMouseMove"
  >
    <!-- Mouse follower glow -->
    <div class="mouse-glow" ref="mouseGlow"></div>
    <div class="mouse-glow-secondary" ref="mouseGlowSecondary"></div>
    
    <!-- Spotlight effect -->
    <div class="spotlight" ref="spotlight"></div>
    
    <!-- Content -->
    <div class="stat-icon" ref="statIcon">
      <font-awesome-icon :icon="icon" />
    </div>
    <div class="stat-content">
      <div class="stat-value" ref="statValue">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
    
    <!-- Background effects -->
    <div class="stat-wave" ref="statWave"></div>
    <div class="ambient-glow" ref="ambientGlow"></div>
    
    <!-- Particle effects -->
    <div class="particles" ref="particles">
      <div class="particle" v-for="i in 8" :key="i" :ref="el => particles[i-1] = el"></div>
    </div>
  </div>
</template>

<script>
import anime from 'animejs/lib/anime.es.js'
import { ref, onMounted, watch, onUnmounted, reactive } from 'vue'

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
    const ambientGlow = ref(null)
    const mouseGlow = ref(null)
    const mouseGlowSecondary = ref(null)
    const spotlight = ref(null)
    const particles = reactive([])
    
    // Animation state management
    const animationState = ref({
      isHovered: false,
      mousePosition: { x: 0, y: 0, rawX: 0, rawY: 0 },
      cardRect: null,
      rafId: null,
      animations: new Set()
    })

    // Smooth mouse position interpolation
    const smoothMouse = ref({ x: 0, y: 0 })
    let mouseRaf = null

    const interpolateMousePosition = () => {
      const lerp = (start, end, factor) => start + (end - start) * factor
      
      smoothMouse.value.x = lerp(smoothMouse.value.x, animationState.value.mousePosition.x, 0.1)
      smoothMouse.value.y = lerp(smoothMouse.value.y, animationState.value.mousePosition.y, 0.1)
      
      if (animationState.value.isHovered) {
        updateMouseEffects()
        mouseRaf = requestAnimationFrame(interpolateMousePosition)
      }
    }

    // Cleanup function for animations
    const cleanupAnimations = () => {
      animationState.value.animations.forEach(animation => {
        if (animation && animation.pause) animation.pause()
      })
      animationState.value.animations.clear()
      
      if (animationState.value.rafId) {
        cancelAnimationFrame(animationState.value.rafId)
      }
      if (mouseRaf) {
        cancelAnimationFrame(mouseRaf)
      }
    }

    // Add animation to tracking set
    const trackAnimation = (animation) => {
      animationState.value.animations.add(animation)
      return animation
    }

    // Update mouse-following effects
    const updateMouseEffects = () => {
      const { x, y } = smoothMouse.value
      const { rawX, rawY } = animationState.value.mousePosition
      
      // Main mouse glow
      if (mouseGlow.value) {
        anime({
          targets: mouseGlow.value,
          translateX: rawX - 50,
          translateY: rawY - 50,
          duration: 0,
          easing: 'linear'
        })
      }

      // Secondary glow with slight delay
      if (mouseGlowSecondary.value) {
        anime({
          targets: mouseGlowSecondary.value,
          translateX: x - 40,
          translateY: y - 40,
          duration: 100,
          easing: 'easeOutQuad'
        })
      }

      // Spotlight effect
      if (spotlight.value) {
        anime({
          targets: spotlight.value,
          background: `radial-gradient(circle at ${rawX}px ${rawY}px, rgba(255,255,255,0.1) 0%, transparent 60%)`,
          duration: 200,
          easing: 'easeOutQuad'
        })
      }

      // Animate particles towards mouse
      particles.forEach((particle, index) => {
        if (particle) {
          const delay = index * 20
          const distance = 30 + (index * 15)
          const angle = (index / particles.length) * Math.PI * 2
          const targetX = rawX + Math.cos(angle) * distance
          const targetY = rawY + Math.sin(angle) * distance
          
          anime({
            targets: particle,
            translateX: targetX - 4,
            translateY: targetY - 4,
            opacity: 0.6,
            scale: 1 + (index * 0.1),
            duration: 300 + delay,
            easing: 'easeOutQuad'
          })
        }
      })
    }

    // Entrance animation
    onMounted(() => {
      // Card entrance
      if (statCard.value) {
        trackAnimation(anime({
          targets: statCard.value,
          translateY: [50, 0],
          opacity: [0, 1],
          scale: [0.9, 1],
          easing: 'spring(1, 80, 10, 0)',
          duration: 800,
          delay: 100 + (props.index * 80)
        }))
      }

      // Icon entrance
      if (statIcon.value) {
        trackAnimation(anime({
          targets: statIcon.value,
          rotateY: [90, 0],
          opacity: [0, 0.2],
          easing: 'easeOutElastic(1, .8)',
          duration: 1200,
          delay: 300 + (props.index * 80)
        }))
      }

      // Value entrance
      if (statValue.value) {
        trackAnimation(anime({
          targets: statValue.value,
          scale: [0, 1],
          opacity: [0, 1],
          easing: 'easeOutExpo',
          duration: 1000,
          delay: 200 + (props.index * 80)
        }))
      }

      // Initialize particles
      particles.forEach((particle) => {
        if (particle) {
          anime.set(particle, {
            opacity: 0,
            scale: 0.5,
            translateX: Math.random() * 200,
            translateY: Math.random() * 100
          })
        }
      })
    })

    // Value change animation
    let valueChangeTimeout = null
    watch(() => props.value, (newValue, oldValue) => {
      if (statValue.value && newValue !== oldValue) {
        if (valueChangeTimeout) clearTimeout(valueChangeTimeout)
        
        valueChangeTimeout = setTimeout(() => {
          trackAnimation(anime({
            targets: statValue.value,
            scale: [1, 1.2, 1],
            color: ['currentColor', '#00ff88', 'currentColor'],
            duration: 700,
            easing: 'easeOutElastic(1, .6)'
          }))

          // Value change particle burst
          particles.forEach((particle, index) => {
            if (particle) {
              trackAnimation(anime({
                targets: particle,
                translateX: Math.random() * 300 - 150,
                translateY: Math.random() * 200 - 100,
                opacity: [0, 0.8, 0],
                scale: [0.5, 1.5, 0],
                duration: 1000,
                delay: index * 50,
                easing: 'easeOutQuart'
              }))
            }
          })
        }, 50)
      }
    })

    // Mouse move handler
    const handleMouseMove = (e) => {
      if (!statCard.value) return
      
      const rect = statCard.value.getBoundingClientRect()
      const rawX = e.clientX - rect.left
      const rawY = e.clientY - rect.top
      
      // Normalized coordinates for 3D effects
      const normalizedX = (rawX / rect.width) * 2 - 1
      const normalizedY = (rawY / rect.height) * 2 - 1
      
      animationState.value.mousePosition = { 
        x: normalizedX * rect.width * 0.5, 
        y: normalizedY * rect.height * 0.5,
        rawX, 
        rawY 
      }
      animationState.value.cardRect = rect

      // 3D tilt effect
      anime({
        targets: statCard.value,
        rotateX: normalizedY * -8,
        rotateY: normalizedX * 8,
        duration: 200,
        easing: 'easeOutQuad'
      })
    }

    // Mouse enter
    const handleMouseEnter = () => {
      animationState.value.isHovered = true
      
      // Start mouse interpolation
      mouseRaf = requestAnimationFrame(interpolateMousePosition)

      // Card hover animation
      if (statCard.value) {
        trackAnimation(anime({
          targets: statCard.value,
          translateY: -12,
          scale: 1.05,
          boxShadow: [
            '0 4px 12px rgba(0, 0, 0, 0.08)',
            '0 25px 50px rgba(0, 0, 0, 0.2)'
          ],
          duration: 500,
          easing: 'easeOutCubic'
        }))
      }

      // Icon animation
      if (statIcon.value) {
        trackAnimation(anime({
          targets: statIcon.value,
          rotate: '15deg',
          opacity: 0.7,
          scale: 1.2,
          duration: 400,
          easing: 'easeOutBack(1.2)'
        }))
      }

      // Wave effect
      if (statWave.value) {
        trackAnimation(anime({
          targets: statWave.value,
          height: ['0%', '120%'],
          opacity: [0, 0.15],
          duration: 700,
          easing: 'easeOutQuart'
        }))
      }

      // Ambient glow
      if (ambientGlow.value) {
        trackAnimation(anime({
          targets: ambientGlow.value,
          opacity: [0, 0.4],
          scale: [0.8, 1.3],
          duration: 600,
          easing: 'easeOutQuart'
        }))
      }

      // Mouse glows
      if (mouseGlow.value) {
        trackAnimation(anime({
          targets: mouseGlow.value,
          opacity: [0, 0.8],
          scale: [0.5, 1],
          duration: 400,
          easing: 'easeOutQuart'
        }))
      }

      if (mouseGlowSecondary.value) {
        trackAnimation(anime({
          targets: mouseGlowSecondary.value,
          opacity: [0, 0.4],
          scale: [0.3, 1.2],
          duration: 500,
          easing: 'easeOutQuart'
        }))
      }

      // Spotlight
      if (spotlight.value) {
        trackAnimation(anime({
          targets: spotlight.value,
          opacity: [0, 1],
          duration: 400,
          easing: 'easeOutQuad'
        }))
      }

      // Particles entrance
      particles.forEach((particle, index) => {
        if (particle) {
          trackAnimation(anime({
            targets: particle,
            opacity: [0, 0.3],
            scale: [0, 0.8],
            duration: 400,
            delay: index * 30,
            easing: 'easeOutQuart'
          }))
        }
      })
    }

    // Mouse leave
    const handleMouseLeave = () => {
      animationState.value.isHovered = false
      
      // Stop mouse interpolation
      if (mouseRaf) {
        cancelAnimationFrame(mouseRaf)
        mouseRaf = null
      }

      // Reset card
      if (statCard.value) {
        trackAnimation(anime({
          targets: statCard.value,
          translateY: 0,
          scale: 1,
          rotateX: 0,
          rotateY: 0,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
          duration: 500,
          easing: 'easeOutQuad'
        }))
      }

      // Reset icon
      if (statIcon.value) {
        trackAnimation(anime({
          targets: statIcon.value,
          rotate: '0deg',
          opacity: 0.2,
          scale: 1,
          duration: 400,
          easing: 'easeOutQuad'
        }))
      }

      // Hide effects
      const hideTargets = [statWave.value, ambientGlow.value, mouseGlow.value, mouseGlowSecondary.value, spotlight.value]
      hideTargets.forEach(target => {
        if (target) {
          trackAnimation(anime({
            targets: target,
            opacity: 0,
            scale: target === statWave.value ? 1 : 0.8,
            height: target === statWave.value ? '0%' : undefined,
            duration: 400,
            easing: 'easeOutQuad'
          }))
        }
      })

      // Hide particles
      particles.forEach((particle, index) => {
        if (particle) {
          trackAnimation(anime({
            targets: particle,
            opacity: 0,
            scale: 0,
            duration: 300,
            delay: index * 20,
            easing: 'easeOutQuad'
          }))
        }
      })
    }

    // Cleanup on unmount
    onUnmounted(() => {
      cleanupAnimations()
      if (valueChangeTimeout) clearTimeout(valueChangeTimeout)
    })

    return {
      statCard,
      statIcon,
      statValue,
      statWave,
      ambientGlow,
      mouseGlow,
      mouseGlowSecondary,
      spotlight,
      particles,
      handleMouseEnter,
      handleMouseLeave,
      handleMouseMove
    }
  }
}
</script>

<style scoped>
.stat-card {
  background-color: var(--input-bg);
  border-radius: 20px;
  padding: 30px;
  text-align: left;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  height: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  z-index: 1;
  transform-style: preserve-3d;
  perspective: 1000px;
  backdrop-filter: blur(10px);
}

.stat-content {
  z-index: 10;
  position: relative;
  pointer-events: none;
}

.stat-icon {
  font-size: 3.5rem;
  color: var(--primary-color);
  opacity: 0.2;
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 8;
  pointer-events: none;
  transform-origin: center;
  filter: drop-shadow(0 0 10px rgba(var(--primary-rgb), 0.3));
}

.stat-value {
  font-size: 2.8rem;
  font-weight: 800;
  color: var(--primary-color);
  margin-bottom: 12px;
  display: block;
  line-height: 1;
  transform-origin: left center;
  text-shadow: 0 0 20px rgba(var(--primary-rgb), 0.3);
}

.stat-label {
  font-size: 1.1rem;
  color: var(--text-color);
  opacity: 0.9;
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* Mouse following glow effects */
.mouse-glow {
  position: absolute;
  width: 100px;
  height: 100px;
  background: radial-gradient(circle, var(--primary-color) 0%, rgba(var(--primary-rgb), 0.4) 40%, transparent 70%);
  border-radius: 50%;
  opacity: 0;
  z-index: 2;
  pointer-events: none;
  filter: blur(15px);
  mix-blend-mode: overlay;
}

.mouse-glow-secondary {
  position: absolute;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, #ffffff 0%, rgba(255, 255, 255, 0.2) 50%, transparent 70%);
  border-radius: 50%;
  opacity: 0;
  z-index: 3;
  pointer-events: none;
  filter: blur(20px);
  mix-blend-mode: soft-light;
}

.spotlight {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  z-index: 1;
  pointer-events: none;
  border-radius: 20px;
}

.stat-wave {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 0;
  background: linear-gradient(45deg, 
    var(--primary-color) 0%, 
    rgba(var(--primary-rgb), 0.8) 50%, 
    rgba(var(--primary-rgb), 0.4) 100%);
  opacity: 0;
  z-index: 1;
  border-radius: 50% 50% 0 0;
  pointer-events: none;
  animation: wave 3s ease-in-out infinite;
}

.ambient-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 150px;
  height: 150px;
  background: radial-gradient(circle, var(--primary-color) 0%, transparent 60%);
  opacity: 0;
  z-index: 1;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  filter: blur(30px);
  mix-blend-mode: multiply;
}

/* Particles */
.particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 4;
}

.particle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: radial-gradient(circle, var(--primary-color) 0%, transparent 70%);
  border-radius: 50%;
  opacity: 0;
  filter: blur(1px);
  box-shadow: 0 0 10px var(--primary-color);
}

/* Animations */
@keyframes wave {
  0%, 100% { transform: translateX(0) scaleX(1); }
  50% { transform: translateX(-5px) scaleX(1.02); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.05); }
}

/* Color variants */
.stat-card.primary .mouse-glow,
.stat-card.primary .ambient-glow,
.stat-card.primary .stat-wave,
.stat-card.primary .particle {
  background: radial-gradient(circle, var(--primary-color) 0%, rgba(var(--primary-rgb), 0.4) 40%, transparent 70%);
}

.stat-card.success .mouse-glow,
.stat-card.success .ambient-glow,
.stat-card.success .stat-wave,
.stat-card.success .particle {
  background: radial-gradient(circle, var(--success-color) 0%, rgba(var(--success-rgb), 0.4) 40%, transparent 70%);
}

.stat-card.warning .mouse-glow,
.stat-card.warning .ambient-glow,
.stat-card.warning .stat-wave,
.stat-card.warning .particle {
  background: radial-gradient(circle, var(--warning-color) 0%, rgba(var(--warning-rgb), 0.4) 40%, transparent 70%);
}

.stat-card.danger .mouse-glow,
.stat-card.danger .ambient-glow,
.stat-card.danger .stat-wave,
.stat-card.danger .particle {
  background: radial-gradient(circle, var(--danger-color) 0%, rgba(var(--danger-rgb), 0.4) 40%, transparent 70%);
}

.stat-card.info .mouse-glow,
.stat-card.info .ambient-glow,
.stat-card.info .stat-wave,
.stat-card.info .particle {
  background: radial-gradient(circle, var(--info-color) 0%, rgba(var(--info-rgb), 0.4) 40%, transparent 70%);
}

@media (max-width: 768px) {
  .stat-card {
    padding: 25px;
  }
  
  .stat-value {
    font-size: 2.2rem;
  }
  
  .stat-icon {
    font-size: 2.8rem;
  }
  
  .mouse-glow {
    width: 80px;
    height: 80px;
  }
  
  .mouse-glow-secondary {
    width: 60px;
    height: 60px;
  }
  
  .particle {
    width: 6px;
    height: 6px;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .stat-card,
  .stat-icon,
  .stat-wave,
  .mouse-glow,
  .mouse-glow-secondary,
  .spotlight,
  .particle {
    animation: none !important;
    transform: none !important;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .stat-card {
    border: 2px solid var(--primary-color);
  }
  
  .mouse-glow,
  .mouse-glow-secondary,
  .ambient-glow {
    filter: none;
    mix-blend-mode: normal;
  }
}
</style>