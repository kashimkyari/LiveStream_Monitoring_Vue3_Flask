<template>
  <div 
    class="sidebar" 
    v-if="!isMobile" 
    ref="sidebarRef"
  >
    <div class="sidebar-header" ref="headerRef">
      <div class="logo">
        <img src="../assets/logo.png" alt="Agency Logo" />
      </div>
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
          class="nav-button"
          :ref="el => { if (el) navButtons[index] = el }"
          :title="tab.label"
        >
          <span class="nav-icon">
            <font-awesome-icon :icon="tab.icon" />
          </span>
          <span 
            v-if="tab.id === 'messages' && messageUnreadCount > 0" 
            class="notification-badge"
          >
            {{ messageUnreadCount }}
          </span>
        </button>
      </div>
    </nav>
    
    <div class="sidebar-footer" ref="footerRef">
      <div class="status-indicator">
        <div class="status-dot" :class="{ online: isOnline }" :title="isOnline ? 'Online' : 'Offline'"></div>
      </div>
      <button @click="toggleSettings" class="settings-toggle" ref="settingsToggleRef" title="Settings">
        <font-awesome-icon :icon="['fas', 'cog']" />
      </button>
    </div>
  </div>

  <!-- Settings Popup (Read-only version) -->
  <div class="settings-popup" v-if="showSettings" ref="settingsPopupRef">
    <div class="settings-menu">
      <div class="settings-section-title">Alert Settings</div>
      <div class="settings-item view-item">
        <span>Keywords</span>
        <span class="item-count">{{ chatKeywords.length }} active</span>
        <font-awesome-icon :icon="['fas', 'chevron-right']" class="right-icon" />
      </div>
      <div class="settings-item view-item">
        <span>Object Detection</span>
        <span class="item-count">{{ flaggedObjects.length }} active</span>
        <font-awesome-icon :icon="['fas', 'chevron-right']" class="right-icon" />
      </div>
      <div class="settings-item view-item">
        <span>Telegram Recipients</span>
        <span class="item-count">{{ telegramRecipients.length }} active</span>
        <font-awesome-icon :icon="['fas', 'chevron-right']" class="right-icon" />
      </div>
     
      <button class="settings-item preferences">
        <span>Change Password</span>
        <font-awesome-icon :icon="['fas', 'key']" class="right-icon" />
      </button>
      
      <button class="settings-item logout" @click="logout">
        <span>Log out</span>
      </button>
    </div>
  </div>

  <!-- Mobile Bottom Navigation -->
  <div class="mobile-nav" v-if="isMobile" ref="mobileNavRef">
    <button 
      v-for="(tab, index) in tabs" 
      :key="tab.id"
      :class="{ active: activeTab === tab.id }"
      @click="changeTab(tab.id, $event)"
      class="mobile-nav-button"
      :ref="el => { if (el) mobileNavButtons[index] = el }"
      :title="tab.label"
    >
      <span class="nav-icon">
        <font-awesome-icon :icon="tab.icon" />
      </span>
      <span v-if="tab.id === 'messages' && messageUnreadCount > 0" class="mobile-notification-badge">
        {{ messageUnreadCount }}
      </span>
    </button>
  </div>
  
  <!-- Toast Notification -->
  <div class="toast-notification" v-if="showToast" :class="toastType" ref="toastRef">
    <font-awesome-icon :icon="toastIcon" class="toast-icon" />
    <span class="toast-message">{{ toastMessage }}</span>
  </div>
  
  <!-- Logout Overlay -->
  <div class="logout-overlay" v-if="showLogoutOverlay" ref="logoutOverlayRef">
    <div class="logout-spinner" ref="logoutSpinnerRef">
      <svg class="spinner-circle" viewBox="0 0 50 50" ref="spinnerCircleRef">
        <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle>
      </svg>
      <span class="logout-text">Logging out...</span>
    </div>
  </div>
  
  <!-- Content Tabs -->
  <div class="content-tabs" v-if="activeTab === 'streams'">
    <!-- Keep existing content -->
  </div>
</template>

<script>
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import anime from 'animejs/lib/anime.es.js'
import axios from 'axios'
import { 
  faTachometerAlt, 
  faVideo, 
  faClipboardList,
  faBell, 
  faCog,
  faComments,
  faChevronRight,
  faKey,
  faExclamationCircle,
  faCheckCircle,
  faInfoCircle,
  faSpinner
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faTachometerAlt, 
  faVideo, 
  faClipboardList, 
  faBell, 
  faCog,
  faComments,
  faChevronRight,
  faKey,
  faExclamationCircle,
  faCheckCircle,
  faInfoCircle,
  faSpinner
)

export default {
  name: 'AgentSidebar',
  components: {
    FontAwesomeIcon
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
  emits: ['tab-change', 'update:theme', 'settings', 'logout'],
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
    
    // Refs for logout animation
    const showLogoutOverlay = ref(false)
    const logoutOverlayRef = ref(null)
    const logoutSpinnerRef = ref(null)
    const spinnerCircleRef = ref(null)
    
    // Toast notification
    const toastRef = ref(null)
    const showToast = ref(false)
    const toastMessage = ref('')
    const toastType = ref('success')
    const toastTimeout = ref(null)
    
    // Read-only data for settings
    const chatKeywords = ref([])
    const flaggedObjects = ref([])
    const telegramRecipients = ref([])

    const checkMobile = () => {
      windowWidth.value = window.innerWidth
      isMobile.value = windowWidth.value <= 768
    }

    const changeTab = (tabId, event) => {
      anime({
        targets: event.currentTarget,
        scale: [1, 0.95, 1],
        duration: 300,
        easing: 'easeInOutBack'
      })

      setTimeout(() => {
        emit('tab-change', tabId)
      }, 150)
    }

    const toggleSettings = () => {
      showSettings.value = !showSettings.value
      
      if (showSettings.value) {
        // Position the popup relative to the gear icon
        nextTick(() => {
          if (settingsToggleRef.value && settingsPopupRef.value) {
            const toggleRect = settingsToggleRef.value.getBoundingClientRect()
            
            if (isMobile.value) {
              // For mobile, position above the bottom navigation
              settingsPopupRef.value.style.bottom = '70px'
              settingsPopupRef.value.style.left = '16px'
              settingsPopupRef.value.style.right = '16px'
            } else {
              const sidebarRect = sidebarRef.value.getBoundingClientRect()
              
              // Position to the right of the sidebar
              settingsPopupRef.value.style.left = `${sidebarRect.width + 10}px`
              // Align with gear icon vertically
              settingsPopupRef.value.style.bottom = `${window.innerHeight - toggleRect.bottom}px`
            }
            
            // Animate popup entrance
            anime({
              targets: settingsPopupRef.value,
              translateX: ['-20px', '0px'],
              opacity: [0, 1],
              duration: 300,
              easing: 'easeOutCubic'
            })
          }
        })
        
        anime({
          targets: settingsToggleRef.value,
          rotate: '+=90',
          duration: 400,
          easing: 'easeInOutQuad'
        })
      } else {
        // Animate popup exit
        if (settingsPopupRef.value) {
          anime({
            targets: settingsPopupRef.value,
            translateX: ['0px', '-20px'],
            opacity: [1, 0],
            duration: 250,
            easing: 'easeInQuad',
            complete: () => {
              // Reset styles after animation completes
              if (settingsPopupRef.value) {
                settingsPopupRef.value.style.transform = ''
              }
            }
          })
        }
        
        anime({
          targets: settingsToggleRef.value,
          rotate: '-=90',
          duration: 400,
          easing: 'easeInOutQuad'
        })
      }
    }

    // Logout function with animation
    const logout = async (callApi = true) => {
      // First close the settings popup if it's open
      if (showSettings.value) {
        anime({
          targets: settingsPopupRef.value,
          translateX: ['0px', '-20px'],
          opacity: [1, 0],
          duration: 250,
          easing: 'easeInQuad'
        })
        
        anime({
          targets: settingsToggleRef.value,
          rotate: '-=90',
          duration: 400,
          easing: 'easeInOutQuad'
        })
        
        showSettings.value = false
      }
      
      // Show the logout overlay
      showLogoutOverlay.value = true
      
      // Fade in the overlay
      nextTick(() => {
        if (logoutOverlayRef.value) {
          anime({
            targets: logoutOverlayRef.value,
            opacity: [0, 1],
            duration: 400,
            easing: 'easeInOutQuad'
          })
        }
        
        // Animate spinner container
        if (logoutSpinnerRef.value) {
          anime({
            targets: logoutSpinnerRef.value,
            scale: [0.8, 1],
            opacity: [0, 1],
            duration: 600,
            easing: 'easeOutElastic(1, .6)'
          })
        }
        
        // Animate spinner circle rotation
        if (spinnerCircleRef.value) {
          anime({
            targets: spinnerCircleRef.value,
            rotate: '360deg',
            duration: 1500,
            easing: 'linear',
            loop: true
          })
          
          // Animate the circle stroke dash
          anime({
            targets: '.path',
            strokeDashoffset: [anime.setDashoffset, 0],
            easing: 'easeInOutSine',
            duration: 1500,
            delay: function(el, i) { return i * 250 },
            direction: 'alternate',
            loop: true
          })
        }
      })
      
      // Also animate sidebar elements out
      const tl = anime.timeline({
        easing: 'easeInOutSine',
        duration: 300
      })
      
      // Animate out the header, nav items, and footer
      tl.add({
        targets: [headerRef.value, footerRef.value],
        opacity: [1, 0],
        translateY: [0, -10],
        duration: 200
      })
      .add({
        targets: navButtons.value,
        opacity: [1, 0],
        translateX: [0, -20],
        delay: anime.stagger(50),
        duration: 200
      }, '-=100')
      
      // Make the actual API call to logout
      if (callApi) {
        try {
          await axios.post('/api/agent/logout')
        } catch (error) {
          console.error('Logout failed:', error)
        }
      }
      
      // Continue the animation and check session status
      setTimeout(async () => {
        try {
          const response = await axios.get('/api/agent/session')
          
          // Complete the logout animation
          if (logoutOverlayRef.value) {
            // Create a completion circle animation
            anime({
              targets: logoutSpinnerRef.value,
              scale: [1, 1.2, 0],
              opacity: [1, 0],
              duration: 800,
              easing: 'easeInOutBack',
              complete: () => {
                // Fade out the overlay
                anime({
                  targets: logoutOverlayRef.value,
                  opacity: [1, 0],
                  duration: 400,
                  easing: 'easeInOutQuad',
                  complete: () => {
                    showLogoutOverlay.value = false
                    
                    // Perform redirection if logged out successfully
                    if (!response.data.logged_in) {
                      // Reset state and redirect
                      showSettings.value = false
                      emit('logout')
                    } else {
                      // Show error toast
                      showToastNotification('Logout failed. Please try again.', 'error')
                    }
                  }
                })
              }
            })
          }
        } catch (error) {
          console.error('Session check failed:', error)
          // Assume logout succeeded if session check fails
          showLogoutOverlay.value = false
          emit('logout')
        }
      }, 1500) // Delay for animation effect
    }
    
    // Toast notification functions
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
          anime({
            targets: toastRef.value,
            translateY: ['100%', '0%'],
            opacity: [0, 1],
            duration: 500,
            easing: 'easeOutElastic(1, .6)'
          })
        }
      })

      toastTimeout.value = setTimeout(() => {
        if (toastRef.value) {
          anime({
            targets: toastRef.value,
            translateY: ['0%', '100%'],
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInBack',
            complete: () => {
              showToast.value = false
            }
          })
        }
      }, 3000)
    }

    // Read-only data fetching functions
    const fetchKeywords = async () => {
      try {
        const response = await axios.get('/api/agent/keywords')
        chatKeywords.value = response.data
      } catch (error) {
        console.error('Error fetching keywords:', error)
        showToastNotification('Unable to load keywords', 'error')
      }
    }
    
    const fetchObjects = async () => {
      try {
        const response = await axios.get('/api/agent/objects')
        flaggedObjects.value = response.data
      } catch (error) {
        console.error('Error fetching objects:', error)
        showToastNotification('Unable to load objects', 'error')
      }
    }
    
    const fetchTelegramRecipients = async () => {
      try {
        const response = await axios.get('/api/agent/telegram_recipients')
        telegramRecipients.value = response.data
      } catch (error) {
        console.error('Error fetching telegram recipients:', error)
        showToastNotification('Unable to load telegram recipients', 'error')
      }
    }

    // Modified tab for agent users
    const tabs = [
      { id: 'dashboard', label: 'Dashboard', icon: ['fas', 'tachometer-alt'] },
      { id: 'streams', label: 'Streams', icon: ['fas', 'video'] },
      { id: 'tasks', label: 'Tasks', icon: ['fas', 'clipboard-list'] },
      { id: 'messages', label: 'Messages', icon: ['fas', 'comments'] },
      { id: 'notifications', label: 'Notifications', icon: ['fas', 'bell'] }
    ]
    
    onMounted(() => {
      checkMobile()
      window.addEventListener('resize', checkMobile)
      fetchKeywords()
      fetchObjects()
      fetchTelegramRecipients()
    })
    
    onUnmounted(() => {
      window.removeEventListener('resize', checkMobile)
    })
    
    // Animation for toast icon based on type
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
      changeTab,
      toggleSettings,
      logout,
      
      // Data for read-only display
      chatKeywords,
      flaggedObjects,
      telegramRecipients,
      
      // Logout animation states and refs
      showLogoutOverlay,
      logoutOverlayRef,
      logoutSpinnerRef,
      spinnerCircleRef,
      
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
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 72px;
  background-color: var(--bg-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
  border-right: 1px solid var(--input-border);
}

.sidebar-header {
  width: 100%;
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px 0;
}

.logo {
  width: 40px;
  height: 40px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.logo img {
  width: 100%;
  height: auto;
  object-fit: contain;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 20px 0;
}

.nav-item-wrapper {
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.nav-button {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: transparent;
  border: none;
  cursor: pointer;
  position: relative;
  color: var(--text-color);
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.nav-button:hover {
  background-color: var(--hover-bg);
}

.nav-button.active {
  background-color: var(--primary-color);
  color: white;
}

.nav-icon {
  font-size: 1.2rem;
}

.notification-badge {
  position: absolute;
  top: 5px;
  right: 2px;
  background-color: var(--notification-bg);
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  font-size: 0.7rem;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
}

.sidebar-footer {
  width: 100%;
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 0;
  position: relative;
}

.status-indicator {
  position: absolute;
  left: 16px;
  display: flex;
  align-items: center;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #8e8e8e;
  transition: background-color 0.3s;
}

.status-dot.online {
  background-color: #4caf50;
}

.settings-toggle {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: transparent;
  border: none;
  color: var(--text-color);
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.settings-toggle:hover {
  background-color: var(--hover-bg);
}

/* Settings Popup */
.settings-popup {
  position: absolute;
  right: 16px;
  background-color: var(--bg-color);
  border: 1px solid var(--input-border);
  border-radius: 12px;
  width: 320px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  z-index: 1100;
  overflow: hidden;
}

.settings-menu {
  padding: 8px 0;
}

.settings-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  width: 100%;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-color);
  font-size: 0.9rem;
  position: relative;
  transition: background-color 0.2s;
}

.settings-item:hover {
  background-color: var(--hover-bg);
}

.settings-section-title {
  padding: 16px 16px 8px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #8e8e8e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.right-icon {
  margin-left: auto;
  font-size: 0.8rem;
  opacity: 0.6;
}

/* Read-only view items */
.view-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: default;
}

.view-item:hover {
  background-color: transparent;
}

.item-count {
  margin-left: auto;
  margin-right: 8px;
  font-size: 0.8rem;
  color: #8e8e8e;
}

.settings-item.preferences {
  border-top: 1px solid var(--input-border);
  margin-top: 8px;
}

.settings-item.logout {
  color: #f44336;
}

/* Mobile Bottom Navigation */
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: var(--bg-color);
  display: flex;
  justify-content: space-around;
  align-items: center;
  border-top: 1px solid var(--input-border);
  z-index: 1000;
}

.mobile-nav-button {
  width: 48px;
  height: 48px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 10px;
  background: transparent;
  border: none;
  color: var(--text-color);
  position: relative;
  cursor: pointer;
}

.mobile-nav-button.active {
  color: var(--primary-color);
}

.mobile-notification-badge {
  position: absolute;
  top: 5px;
  right: 5px;
  background-color: var(--notification-bg);
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  font-size: 0.7rem;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
}

/* Toast Notification */
.toast-notification {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 20px;
  border-radius: 8px;
  background-color: #4caf50;
  color: white;
  display: flex;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 2000;
  min-width: 280px;
  max-width: 400px;
}

.toast-notification.error {
  background-color: #f44336;
}

.toast-notification.info {
  background-color: #2196f3;
}

.toast-icon {
  margin-right: 12px;
  font-size: 1.2rem;
}

.toast-message {
  font-size: 0.9rem;
  font-weight: 500;
}

/* Content Tabs */
.content-tabs {
  margin-left: 72px;
  padding: 20px;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Logout Animation Styles */
.logout-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  opacity: 0;
}

.logout-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.spinner-circle {
  width: 80px;
  height: 80px;
  transform-origin: center;
  margin-bottom: 16px;
}

.path {
  stroke: var(--primary-color);
  stroke-linecap: round;
  stroke-dasharray: 126;
  stroke-dashoffset: 126;
  animation: dash 1.5s ease-in-out infinite;
}

.logout-text {
  color: white;
  font-size: 1.1rem;
  font-weight: 500;
  text-align: center;
  margin-top: 16px;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes dash {
  0% {
    stroke-dashoffset: 126;
  }
  50% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: 126;
  }
}

@keyframes pulse {
  0% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.6;
  }
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  
  .content-tabs {
    margin-left: 0;
    padding: 16px;
    padding-bottom: 70px;
  }
  
  .settings-popup {
    position: fixed;
    bottom: 70px;
    left: 16px;
    right: 16px;
    width: auto;
  }
  
  .toast-notification {
    left: 16px;
    right: 16px;
    width: calc(100% - 32px);
    transform: none;
    bottom: 70px;
  }
}
</style>