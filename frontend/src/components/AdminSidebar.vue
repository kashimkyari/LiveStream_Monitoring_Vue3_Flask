<template>
  <div 
    class="sidebar" 
    v-if="!isMobile" 
    ref="sidebarRef"
  >
    <!-- Particle Mouse Follower -->
    <div class="mouse-follower" ref="mouseFollowerRef">
      <div class="particle" v-for="i in 8" :key="i" :class="`particle-${i}`"></div>
    </div>
    
    <!-- Animated Background Elements -->
    <div class="bg-decoration">
      <div class="floating-orb orb-1"></div>
      <div class="floating-orb orb-2"></div>
      <div class="floating-orb orb-3"></div>
    </div>
    
    <nav class="sidebar-nav">
      <div 
        v-for="(tab, index) in tabs" 
        :key="tab.id"
        class="nav-item-wrapper"
      >
        <button 
          :class="{ active: activeTab === tab.id }"
          @click="changeTab(tab.id, $event)"
          @mouseenter="onButtonHover"
          @mouseleave="onButtonLeave"
          class="nav-button"
          :ref="el => { if (el) navButtons[index] = el }"
          :title="tab.label"
        >
          <div class="button-glow"></div>
          <span class="nav-icon">
            <font-awesome-icon :icon="tab.icon" />
          </span>
          <span 
            v-if="tab.id === 'messages' && messageUnreadCount > 0" 
            class="notification-badge"
          >
            {{ messageUnreadCount }}
            <div class="badge-pulse"></div>
          </span>
          <div class="ripple-container">
            <span class="ripple"></span>
          </div>
        </button>
      </div>
    </nav>
  </div>

  
  <!-- Enhanced Toast Notification -->
  <div class="toast-notification" v-if="showToast" :class="toastType" ref="toastRef">
    <div class="toast-glow"></div>
    <div class="toast-content">
      <font-awesome-icon :icon="toastIcon" class="toast-icon" />
      <span class="toast-message">{{ toastMessage }}</span>
    </div>
    <div class="toast-progress"></div>
  </div>


</template>

<script>
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import anime from 'animejs/lib/anime.es.js'
import { 
  faTachometerAlt, 
  faVideo, 
  faUsers, 
  faBell, 
  faCog,
  faComments,
  faCheck,
  faChevronRight,
  faPlus,
  faExclamationCircle,
  faCheckCircle,
  faInfoCircle,
  faEdit,
  faTrash,
  faSpinner,
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faTachometerAlt, 
  faVideo, 
  faUsers, 
  faBell, 
  faCog,
  faComments,
  faCheck,
  faChevronRight,
  faPlus,
  faExclamationCircle,
  faCheckCircle,
  faInfoCircle,
  faEdit,
  faTrash,
  faSpinner
)

export default {
  name: 'AdminSidebar',
  components: {
    FontAwesomeIcon,
  },
  props: {
    activeTab: String,
    user: Object,
    isOnline: Boolean,
    messages: Array,
    messageUnreadCount: {
      type: Number,
      default: 0
    }
  },
  emits: ['tab-change', 'update:theme', 'settings'],
  setup(props, { emit }) {
    const isMobile = ref(false)
    const windowWidth = ref(window.innerWidth)
    const navButtons = ref([])
    const mobileNavButtons = ref([])
    const sidebarRef = ref(null)
    const settingsToggleRef = ref(null)
    const settingsPopupRef = ref(null)
    const showSettings = ref(false)
   
    const footerRef = ref(null)
    const headerRef = ref(null)
    const mouseFollowerRef = ref(null)
    
    // Mouse position for particle follower
    const mouseX = ref(0)
    const mouseY = ref(0)
    
    
    
    // Toast notification
    const toastRef = ref(null)
    const showToast = ref(false)
    const toastMessage = ref('')
    const toastType = ref('success')
    const toastTimeout = ref(null)
    


    const checkMobile = () => {
      windowWidth.value = window.innerWidth
      isMobile.value = windowWidth.value <= 768
    }

    // Enhanced mouse follower
    const updateMousePosition = (e) => {
      mouseX.value = e.clientX
      mouseY.value = e.clientY
      
      if (mouseFollowerRef.value) {
        const follower = mouseFollowerRef.value
        const particles = follower.querySelectorAll('.particle')
        
        // Update main follower position
        anime({
          targets: follower,
          left: e.clientX,
          top: e.clientY,
          duration: 0,
          easing: 'linear'
        })
        
        // Animate particles with staggered delay
        particles.forEach((particle, index) => {
          anime({
            targets: particle,
            translateX: Math.sin(Date.now() * 0.01 + index) * 20,
            translateY: Math.cos(Date.now() * 0.01 + index) * 20,
            duration: 1000 + index * 100,
            easing: 'easeOutSine',
            loop: true,
            direction: 'alternate'
          })
        })
      }
    }

    const changeTab = (tabId, event) => {
      // Enhanced ripple effect
      const button = event.currentTarget
      const ripple = button.querySelector('.ripple')
      const rect = button.getBoundingClientRect()
      const size = Math.max(rect.width, rect.height)
      const x = event.clientX - rect.left - size / 2
      const y = event.clientY - rect.top - size / 2
      
      ripple.style.width = ripple.style.height = size + 'px'
      ripple.style.left = x + 'px'
      ripple.style.top = y + 'px'
      
      anime({
        targets: ripple,
        scale: [0, 4],
        opacity: [0.6, 0],
        duration: 600,
        easing: 'easeOutQuart'
      })

      // Enhanced button animation
      anime({
        targets: event.currentTarget,
        scale: [1, 0.92, 1.05, 1],
        duration: 400,
        easing: 'easeInOutBack'
      })

      setTimeout(() => {
        emit('tab-change', tabId)
      }, 150)
    }

    const onButtonHover = (event) => {
      const glow = event.currentTarget.querySelector('.button-glow')
      anime({
        targets: glow,
        opacity: [0, 0.3],
        scale: [0.8, 1.2],
        duration: 300,
        easing: 'easeOutQuart'
      })
    }

    const onButtonLeave = (event) => {
      const glow = event.currentTarget.querySelector('.button-glow')
      anime({
        targets: glow,
        opacity: [0.3, 0],
        scale: [1.2, 0.8],
        duration: 300,
        easing: 'easeOutQuart'
      })
    }

    const toggleSettings = () => {
      showSettings.value = !showSettings.value
      
      if (showSettings.value) {
        nextTick(() => {
          if (settingsToggleRef.value && settingsPopupRef.value) {
            const toggleRect = settingsToggleRef.value.getBoundingClientRect()
            
            if (isMobile.value) {
              settingsPopupRef.value.style.bottom = '70px'
              settingsPopupRef.value.style.left = '16px'
              settingsPopupRef.value.style.right = '16px'
            } else {
              const sidebarRect = sidebarRef.value.getBoundingClientRect()
              settingsPopupRef.value.style.left = `${sidebarRect.width + 10}px`
              settingsPopupRef.value.style.bottom = `${window.innerHeight - toggleRect.bottom}px`
            }
            
            // Enhanced popup entrance
            anime({
              targets: settingsPopupRef.value,
              translateX: ['-30px', '0px'],
              translateY: ['-20px', '0px'],
              opacity: [0, 1],
              scale: [0.9, 1],
              duration: 400,
              easing: 'easeOutBack'
            })
          }
        })
        
        anime({
          targets: settingsToggleRef.value,
          rotate: '+=180',
          duration: 500,
          easing: 'easeInOutBack'
        })
      } else {
        if (settingsPopupRef.value) {
          anime({
            targets: settingsPopupRef.value,
            translateX: ['0px', '-30px'],
            opacity: [1, 0],
            scale: [1, 0.9],
            duration: 300,
            easing: 'easeInBack'
          })
        }
        
        anime({
          targets: settingsToggleRef.value,
          rotate: '-=180',
          duration: 500,
          easing: 'easeInOutBack'
        })
      }
    }
    
    const showToastNotification = (message, type = 'success') => {
      if (toastTimeout.value) {
        clearTimeout(toastTimeout.value)
      }
      
      toastMessage.value = message
      toastType.value = type
      showToast.value = true
      
      nextTick(() => {
        if (toastRef.value) {
          anime.remove(toastRef.value)
          
          // Enhanced toast animation
          anime({
            targets: toastRef.value,
            translateY: ['100%', '0%'],
            opacity: [0, 1],
            scale: [0.9, 1],
            duration: 600,
            easing: 'easeOutElastic(1, .8)'
          })
          
          // Progress bar animation
          const progressBar = toastRef.value.querySelector('.toast-progress')
          if (progressBar) {
            anime({
              targets: progressBar,
              width: ['100%', '0%'],
              duration: 3000,
              easing: 'linear'
            })
          }
        }
      })

      toastTimeout.value = setTimeout(() => {
        if (toastRef.value) {
          anime({
            targets: toastRef.value,
            translateY: ['0%', '100%'],
            opacity: [1, 0],
            scale: [1, 0.9],
            duration: 400,
            easing: 'easeInBack',
            complete: () => {
              showToast.value = false
            }
          })
        }
      }, 3000)
    }

   

    const tabs = [
      { id: 'dashboard', label: 'Dashboard', icon: ['fas', 'tachometer-alt'] },
      { id: 'streams', label: 'Streams', icon: ['fas', 'video'] },
      { id: 'agents', label: 'Agents', icon: ['fas', 'users'] },
      { id: 'messages', label: 'Messages', icon: ['fas', 'comments'] },
      { id: 'notifications', label: 'Notifications', icon: ['fas', 'bell'] },
      { id: 'settings', label: 'Settings', icon: ['fas', 'cog'] }
    ]
    
    onMounted(() => {
      checkMobile()
      window.addEventListener('resize', checkMobile)
      window.addEventListener('mousemove', updateMousePosition)
      
      
      // Initialize floating orbs animation
      nextTick(() => {
        const orbs = document.querySelectorAll('.floating-orb')
        orbs.forEach((orb, index) => {
          anime({
            targets: orb,
            translateY: ['-20px', '20px'],
            translateX: ['-10px', '10px'],
            duration: 3000 + index * 500,
            easing: 'easeInOutSine',
            direction: 'alternate',
            loop: true
          })
        })
      })
    })
    
    onUnmounted(() => {
      window.removeEventListener('resize', checkMobile)
      window.removeEventListener('mousemove', updateMousePosition)
    })
    
    const toastIcon = computed(() => {
      switch (toastType.value) {
        case 'error': return ['fas', 'exclamation-circle']
        case 'success': return ['fas', 'check-circle']
        default: return ['fas', 'info-circle']
      }
    })
    
    return {
      isMobile,
      tabs,
      navButtons,
      mobileNavButtons,
      sidebarRef,
      settingsToggleRef,
      settingsPopupRef,
      showSettings,
      mouseFollowerRef,
      changeTab,
      toggleSettings,
      onButtonHover,
      onButtonLeave,
      
    
  
      
      // Toast notification
      showToast,
      toastMessage,
      toastType,
      toastRef,
      showToastNotification,
      toastIcon,
      
      // Refs
      footerRef,
      headerRef
    }
  }
}
</script>

<style scoped>
:root {
  --primary-color: #6366f1;
  --primary-light: #818cf8;
  --primary-dark: #4f46e5;
  --bg-color: rgb(96, 165, 250);
  --surface-color: #121212;
  --text-color: #e2e8f0;
  --text-muted: #94a3b8;
  --border-color: #334155;
  --hover-bg: #334155;
  --notification-bg: #ef4444;
  --success-color: #10b981;
  --error-color: #ef4444;
  --warning-color: #f59e0b;
  --glow-color: rgba(99, 102, 241, 0.3);
}

/* Mouse Follower */
.mouse-follower {
  position: fixed;
  pointer-events: none;
  z-index: 9998;
  width: 20px;
  height: 20px;
  transform: translate(-50%, -50%);
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: var(--primary-color);
  border-radius: 50%;
  box-shadow: 0 0 10px var(--primary-color);
  opacity: 0.8;
}

.particle-1 { animation-delay: 0s; }
.particle-2 { animation-delay: 0.1s; }
.particle-3 { animation-delay: 0.2s; }
.particle-4 { animation-delay: 0.3s; }
.particle-5 { animation-delay: 0.4s; }
.particle-6 { animation-delay: 0.5s; }
.particle-7 { animation-delay: 0.6s; }
.particle-8 { animation-delay: 0.7s; }

/* Sidebar */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 72px;
  background: linear-gradient(135deg, var(--primary-dark), var(--input-bg));
  backdrop-filter: blur(20px);
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 
    0 0 30px rgba(99, 102, 241, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border-right: 1px solid var(--border-color);
  z-index: 1000;
  overflow: hidden;
  position: relative;
}

.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, #1a1a1a 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, #1a1a1a 0%, transparent 50%);
  pointer-events: none;
}

/* Background Decorations */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}

.floating-orb {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
  filter: blur(1px);
}

.orb-1 {
  width: 40px;
  height: 40px;
  background: var(--primary-color);
  top: 20%;
  left: 20%;
}

.orb-2 {
  width: 25px;
  height: 25px;
  background: var(--primary-light);
  top: 60%;
  right: 15%;
}

.orb-3 {
  width: 30px;
  height: 30px;
  background: var(--primary-dark);
  bottom: 20%;
  left: 30%;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 20px 0;
  position: relative;
  z-index: 2;
}

.nav-item-wrapper {
  position: relative;
  margin: 8px 0;
}

.nav-button {
  position: relative;
  width: 48px;
  height: 48px;
  background: transparent;
  border: none;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  overflow: hidden;
  transform-origin: center;
}

.nav-button:hover {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-dark);
  transform: scale(1.1);
}

.nav-button.active {
  background: #63b3ed85;
  color: white;
  box-shadow: 
    0 8px 32px rgba(99, 102, 241, 0.4),
    0 4px 12px rgba(0, 0, 0, 0.3);
  transform: scale(1.05);
}

.nav-button.active::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -2px;
  width: 4px;
  height: 24px;
  background: var(--primary-light);
  border-radius: 2px;
  transform: translateY(-50%);
  box-shadow: 0 0 12px var(--primary-light);
}

.button-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at center, var(--glow-color), transparent);
  border-radius: 12px;
  opacity: 0;
  pointer-events: none;
}

.nav-icon {
  font-size: 18px;
  position: relative;
  z-index: 1;
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--notification-bg);
  color: white;
  font-size: 10px;
  font-weight: bold;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  z-index: 2;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.5);
}

.badge-pulse {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--notification-bg);
  border-radius: 9px;
  animation: pulse-badge 2s infinite;
}

@keyframes pulse-badge {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
  100% { opacity: 1; transform: scale(1); }
}

.ripple-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 12px;
  overflow: hidden;
  pointer-events: none;
}

.ripple {
  position: absolute;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  transform: scale(0);
  pointer-events: none;
}

/* Settings Popup */
.settings-popup {
  position: fixed;
  min-width: 280px;
  background: linear-gradient(135deg, var(--surface-color), var(--bg-color));
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.4),
    0 8px 16px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  z-index: 2000;
  overflow: hidden;
}

.popup-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at top, rgba(99, 102, 241, 0.1), transparent);
  pointer-events: none;
}

.settings-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-color);
  position: relative;
}

.settings-header h3 {
  margin: 0;
  color: var(--text-color);
  font-size: 18px;
  font-weight: 600;
}

.header-decoration {
  position: absolute;
  bottom: 0;
  left: 24px;
  right: 24px;
  height: 2px;
  background: linear-gradient(90deg, var(--primary-color), transparent);
  border-radius: 1px;
}

.settings-menu {
  padding: 16px;
}

.settings-section-title {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 12px 0;
  padding: 0 8px;
}

.settings-item {
  width: 100%;
  background: transparent;
  border: none;
  padding: 14px 16px;
  border-radius: 12px;
  color: var(--text-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 4px 0;
  transition: all 0.3s ease;
  font-size: 14px;
  font-weight: 500;
}

.settings-item:hover {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-light);
  transform: translateX(4px);
}

.item-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.right-icon {
  margin-left: auto;
  color: var(--text-muted);
  font-size: 12px;
  transition: all 0.3s ease;
}

.settings-item:hover .right-icon {
  color: var(--primary-light);
  transform: translateX(2px);
}

/* Toast Notification */
.toast-notification {
  position: fixed;
  bottom: 24px;
  right: 24px;
  min-width: 320px;
  background: linear-gradient(135deg, var(--surface-color), var(--bg-color));
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px 20px;
  
  }

</style>