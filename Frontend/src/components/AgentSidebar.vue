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
        v-for="(tab, index) in agentTabs" 
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

  <!-- Settings Popup -->
  <div class="settings-popup" v-if="showSettings" ref="settingsPopupRef">
    <div class="settings-menu">
      <div class="settings-section-title">Detection</div>
      <button 
        class="settings-item flag-item" 
        @click="openAddKeywordModal"
        ref="keywordButtonRef"
      >
        <span>Add Keyword</span>
        <font-awesome-icon :icon="['fas', 'plus']" class="right-icon" />
      </button>
      <button 
        class="settings-item flag-item" 
        @click="openAddObjectModal"
        ref="objectButtonRef"
      >
        <span>Add Object Detection</span>
        <font-awesome-icon :icon="['fas', 'plus']" class="right-icon" />
      </button>
      <button 
        class="settings-item flag-item" 
        @click="openAddTelegramModal"
        ref="telegramButtonRef"
      >
        <span>Add Telegram Recipient</span>
        <font-awesome-icon :icon="['fas', 'plus']" class="right-icon" />
      </button>
     
      <button class="settings-item logout" @click="logout">
        <span>Log out</span>
      </button>
    </div>
  </div>

  <!-- Mobile Bottom Navigation -->
  <div class="mobile-nav" v-if="isMobile" ref="mobileNavRef" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <!-- Regular navigation buttons first -->
    <button 
      v-for="(tab, index) in agentTabs" 
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
    
    <!-- Hamburger menu button (positioned last - position 5) -->
    <button 
      class="mobile-nav-button hamburger-button"
      @click="toggleHamburgerMenu"
      ref="hamburgerButtonRef"
      title="Menu"
    >
      <span class="nav-icon">
        <font-awesome-icon :icon="['fas', 'bars']" />
      </span>
    </button>
  </div>
  
  <!-- Hamburger Menu Popup -->
  <div class="hamburger-popup" v-if="showHamburgerMenu && isMobile" ref="hamburgerPopupRef" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="settings-menu">
      <div class="settings-section-title">Quick Actions</div>
      <button 
        class="settings-item" 
        @click="refreshDashboard"
        ref="refreshButtonRef"
      >
        <span>Refresh Dashboard</span>
        <font-awesome-icon :icon="['fas', 'sync']" class="right-icon" />
      </button>
      
      <div class="settings-section-title">Navigation</div>
      <button 
        v-for="tab in agentTabs" 
        :key="`menu-${tab.id}`"
        class="settings-item"
        :class="{ 'active-menu-item': activeTab === tab.id }"
        @click="changeTabFromMenu(tab.id)"
      >
        <font-awesome-icon :icon="tab.icon" class="left-icon" />
        <span>{{ tab.label }}</span>
        <font-awesome-icon v-if="activeTab === tab.id" :icon="['fas', 'check']" class="right-icon" />
      </button>
      
      <div class="settings-section-title">Alert Settings</div>
      <button 
        class="settings-item flag-item" 
        @click="openHamburgerKeywordModal"
      >
        <span>Add Keyword</span>
        <font-awesome-icon :icon="['fas', 'plus']" class="right-icon" />
      </button>
      <button 
        class="settings-item flag-item" 
        @click="openHamburgerObjectModal"
      >
        <span>Add Object Detection</span>
        <font-awesome-icon :icon="['fas', 'plus']" class="right-icon" />
      </button>
      <button 
        class="settings-item flag-item" 
        @click="openHamburgerTelegramModal"
      >
        <span>Add Telegram Recipient</span>
        <font-awesome-icon :icon="['fas', 'plus']" class="right-icon" />
      </button>
      
      <button class="settings-item logout" @click="logout">
        <span>Log out</span>
        <font-awesome-icon :icon="['fas', 'sign-out-alt']" class="right-icon" />
      </button>
    </div>
  </div>
  
  <!-- Toast Notification -->
  <div class="toast-notification" v-if="showToast" :class="toastType" ref="toastRef" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <font-awesome-icon :icon="toastIcon" class="toast-icon" />
    <span class="toast-message">{{ toastMessage }}</span>
  </div>
  
  <!-- Logout Overlay -->
  <div class="logout-overlay" v-if="showLogoutOverlay" ref="logoutOverlayRef" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="logout-spinner" ref="logoutSpinnerRef">
      <svg class="spinner-circle" viewBox="0 0 50 50" ref="spinnerCircleRef">
        <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle>
      </svg>
      <span class="logout-text">Logging out...</span>
    </div>
  </div>
  
  <!-- Modal Components -->
  <SettingsModals
    ref="modalsRef"
    @notification="showToastNotification"
    @update:keywords="fetchKeywords"
    @update:objects="fetchObjects"
    @update:telegramRecipients="fetchTelegramRecipients"
    :isMobile="isMobile"
    :isDarkTheme="isDarkTheme"
  />
</template>

<script>
import { computed, ref, onMounted, onUnmounted, nextTick, inject } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import anime from 'animejs/lib/anime.es.js'
import axios from 'axios'
import SettingsModals from './SettingsModals.vue'
import { 
  faTachometerAlt, 
  faVideo, 
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
  faBars,
  faSync,
  faSignOutAlt,
  faClipboardList,
  faSave
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faTachometerAlt, 
  faVideo,
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
  faBars,
  faSync,
  faSignOutAlt,
  faClipboardList,
  faSave
)

export default {
  name: 'AgentSidebar',
  components: {
    FontAwesomeIcon,
    SettingsModals
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
  emits: ['tab-change', 'update:theme', 'settings', 'logout', 'refresh'],
  setup(props, { emit }) {
    // Inject app theme from parent using the same pattern as App.vue
    const appTheme = inject('theme', ref(true))
    
    // Create a computed property for isDarkTheme to match App.vue's naming convention
    const isDarkTheme = computed(() => appTheme.value === true)
    
    const isMobile = ref(false)
    const windowWidth = ref(window.innerWidth)
    const navButtons = ref([])
    const mobileNavButtons = ref([])
    const sidebarRef = ref(null)
    const settingsToggleRef = ref(null)
    const settingsPopupRef = ref(null)
    const showSettings = ref(false)
    const modalsRef = ref(null)
    const footerRef = ref(null)
    const headerRef = ref(null)
    const mobileNavRef = ref(null)
    
    // Agent-specific settings
    const agentSettings = ref({
      notificationSound: true,
      refreshInterval: 300, // 5 minutes in seconds
      objectDetection: true,
      chatKeywords: true,
      audioDetection: false
    })
    
    // New refs for hamburger menu
    const hamburgerButtonRef = ref(null)
    const hamburgerPopupRef = ref(null)
    const showHamburgerMenu = ref(false)
    const refreshButtonRef = ref(null)
    
    // Refs for logout animation
    const showLogoutOverlay = ref(false)
    const logoutOverlayRef = ref(null)
    const logoutSpinnerRef = ref(null)
    const spinnerCircleRef = ref(null)
    
    // Refs for modal buttons
    const keywordButtonRef = ref(null)
    const objectButtonRef = ref(null)
    const telegramButtonRef = ref(null)
    
    // Toast notification
    const toastRef = ref(null)
    const showToast = ref(false)
    const toastMessage = ref('')
    const toastType = ref('success')
    const toastTimeout = ref(null)
    
    // Data for settings
    const chatKeywords = ref([])
    const flaggedObjects = ref([])
    const telegramRecipients = ref([])

    // Agent tabs
    const agentTabs = computed(() => [
      {
        id: 'dashboard',
        label: 'Dashboard',
        icon: ['fas', 'tachometer-alt']
      },
      {
        id: 'streams',
        label: 'Streams',
        icon: ['fas', 'video']
      },
      {
        id: 'tasks',
        label: 'Tasks',
        icon: ['fas', 'clipboard-list']
      },
      {
        id: 'notifications',
        label: 'Notifications',
        icon: ['fas', 'bell']
      },
      {
        id: 'messages',
        label: 'Messages',
        icon: ['fas', 'comments']
      }
    ])

    const checkMobile = () => {
      windowWidth.value = window.innerWidth
      isMobile.value = windowWidth.value <= 768
      
      // Close hamburger menu when switching to desktop
      if (!isMobile.value && showHamburgerMenu.value) {
        showHamburgerMenu.value = false
      }
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
      // Close hamburger menu if it's open
      if (showHamburgerMenu.value) {
        toggleHamburgerMenu()
      }
      
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
    
    // Removed custom gear icon animation as we're now using font-awesome icon

    // New methods for hamburger menu
    const toggleHamburgerMenu = () => {
      // Close settings popup if it's open
      if (showSettings.value) {
        toggleSettings()
      }
      
      showHamburgerMenu.value = !showHamburgerMenu.value
      
      if (showHamburgerMenu.value) {
        // Position hamburger popup relative to button
        nextTick(() => {
          if (hamburgerButtonRef.value && hamburgerPopupRef.value) {
            // Animate entrance
            anime({
              targets: hamburgerPopupRef.value,
              translateY: ['20px', '0px'],
              opacity: [0, 1],
              duration: 300,
              easing: 'easeOutCubic'
            })
            
            // Animate hamburger button
            anime({
              targets: hamburgerButtonRef.value,
              rotate: '90deg',
              scale: [1, 1.1, 1],
              duration: 500,
              easing: 'easeOutElastic(1, 0.5)'
            })
          }
        })
      } else {
        // Animate exit
        if (hamburgerPopupRef.value) {
          anime({
            targets: hamburgerPopupRef.value,
            translateY: ['0px', '20px'],
            opacity: [1, 0],
            duration: 250,
            easing: 'easeInQuad'
          })
          
          // Animate hamburger button
          anime({
            targets: hamburgerButtonRef.value,
            rotate: '0deg',
            scale: [1, 0.9, 1],
            duration: 500,
            easing: 'easeOutElastic(1, 0.5)'
          })
        }
      }
    }
    
    // Changed tab from menu
    const changeTabFromMenu = (tabId) => {
      emit('tab-change', tabId)
      toggleHamburgerMenu()
    }
    
    // Refresh dashboard from menu
    const refreshDashboard = () => {
      emit('refresh')
      toggleHamburgerMenu()
      
      // Show toast feedback
      showToastNotification('Refreshing dashboard...', 'info')
    }
    
    // Show toast notification
    const showToastNotification = (message, type = 'success') => {
      // Clear any existing timeout
      if (toastTimeout.value) {
        clearTimeout(toastTimeout.value)
      }
      
      // Set toast properties
      toastMessage.value = message
      toastType.value = type
      showToast.value = true
      
      // Animate toast entrance
      nextTick(() => {
        if (toastRef.value) {
          anime({
            targets: toastRef.value,
            translateY: ['20px', '0px'],
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutQuad'
          })
        }
      })
      
      // Auto-hide after delay
      toastTimeout.value = setTimeout(() => {
        if (toastRef.value) {
          anime({
            targets: toastRef.value,
            translateY: ['0px', '20px'],
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInQuad',
            complete: () => {
              showToast.value = false
            }
          })
        } else {
          showToast.value = false
        }
      }, 3000)
    }
    
    // Compute toast icon based on type
    const toastIcon = computed(() => {
      switch (toastType.value) {
        case 'success':
          return ['fas', 'check-circle']
        case 'error':
          return ['fas', 'exclamation-circle']
        case 'info':
          return ['fas', 'info-circle']
        case 'warning':
          return ['fas', 'exclamation-triangle']
        default:
          return ['fas', 'info-circle']
      }
    })
    
    // Modal methods
    const openAddKeywordModal = () => {
      if (modalsRef.value) {
        modalsRef.value.openKeywordModal()
      }
      toggleSettings()
    }
    
    const openAddObjectModal = () => {
      if (modalsRef.value) {
        modalsRef.value.openObjectModal()
      }
      toggleSettings()
    }
    
    const openAddTelegramModal = () => {
      if (modalsRef.value) {
        modalsRef.value.openTelegramModal()
      }
      toggleSettings()
    }
    
    // Mobile modal methods
    const openHamburgerKeywordModal = () => {
      if (modalsRef.value) {
        modalsRef.value.openKeywordModal()
      }
      toggleHamburgerMenu()
    }
    
    const openHamburgerObjectModal = () => {
      if (modalsRef.value) {
        modalsRef.value.openObjectModal()
      }
      toggleHamburgerMenu()
    }
    
    const openHamburgerTelegramModal = () => {
      if (modalsRef.value) {
        modalsRef.value.openTelegramModal()
      }
      toggleHamburgerMenu()
    }

    // Logout with animation and redirect to App.vue
    const logout = async () => {
      showLogoutOverlay.value = true
      
      // Animate logout spinner
      nextTick(() => {
        if (logoutSpinnerRef.value) {
          anime({
            targets: logoutSpinnerRef.value,
            opacity: [0, 1],
            scale: [0.8, 1],
            duration: 600,
            easing: 'easeOutQuad'
          })
          
          // Animate spinner rotation
          anime({
            targets: spinnerCircleRef.value,
            strokeDashoffset: [anime.setDashoffset, 0],
            duration: 1500,
            easing: 'easeInOutSine',
            loop: true
          })
        }
      })
      
      try {
        // Call the logout API endpoint
        await axios.post('/api/logout')
        console.log('Logout successful')
      } catch (error) {
        console.error('Logout API call failed:', error)
        // Continue with local logout even if API call fails
      }
      
      // Clear local storage and reset state
      localStorage.removeItem('userRole')
      
      // Delay before redirecting to allow animation to complete
      setTimeout(() => {
        // Emit logout event for parent components
        emit('logout')
        
        // Refresh the page to return to App.vue login screen
        window.location.href = '/'
      }, 1200)
    }
    
    // Save agent settings
    const saveSettings = () => {
      // In a real implementation, you would send these settings to the server
      // For now, we'll just show a success notification
      
      // Close settings popup
      toggleSettings()
      
      // Show success notification
      showToastNotification('Settings saved successfully', 'success')
    }
    
    // Fetch settings data
    const fetchKeywords = async () => {
      try {
        const response = await axios.get('/api/agent/keywords')
        chatKeywords.value = response.data || []
      } catch (error) {
        console.error('Error fetching keywords:', error)
        showToastNotification('Failed to fetch keywords', 'error')
      }
    }
    
    const fetchObjects = async () => {
      try {
        const response = await axios.get('/api/agent/objects')
        flaggedObjects.value = response.data || []
      } catch (error) {
        console.error('Error fetching objects:', error)
        showToastNotification('Failed to fetch objects', 'error')
      }
    }
    
    const fetchTelegramRecipients = async () => {
      try {
        const response = await axios.get('/api/agent/telegram_recipients')
        telegramRecipients.value = response.data || []
      } catch (error) {
        console.error('Error fetching telegram recipients:', error)
        showToastNotification('Failed to fetch telegram recipients', 'error')
      }
    }

    // Animate sidebar elements on mount
    const animateSidebar = () => {
      // Animate logo first
      if (headerRef.value) {
        anime({
          targets: headerRef.value,
          translateY: ['-30px', '0px'],
          opacity: [0, 1],
          easing: 'easeOutQuad',
          duration: 600
        })
      }
      
      // Animate nav buttons with delay
      if (navButtons.value.length) {
        anime({
          targets: navButtons.value,
          translateY: ['-10px', '0px'],
          opacity: [0, 1],
          delay: anime.stagger(80, {start: 300}),
          easing: 'easeOutQuad',
          duration: 500
        })
      }
      
      // Animate footer elements
      if (footerRef.value) {
        anime({
          targets: footerRef.value,
          translateY: ['10px', '0px'],
          opacity: [0, 1],
          easing: 'easeOutQuad',
          duration: 600,
          delay: 600
        })
      }
      
      // Animate settings toggle icon
      if (settingsToggleRef.value) {
        anime({
          targets: settingsToggleRef.value,
          rotate: '360deg',
          duration: 1500,
          easing: 'easeInOutQuad',
          delay: 800
        })
      }
    }
    
    // Watch for tab changes to update active state
    const updateActiveTab = () => {
      // Highlight the active tab
      navButtons.value.forEach((button, index) => {
        const tabId = agentTabs.value[index].id
        if (button && tabId === props.activeTab) {
          anime({
            targets: button,
            scale: [1, 1.2, 1],
            duration: 500,
            easing: 'easeOutElastic(1, 0.5)'
          })
        }
      })
    }
    
    // Lifecycle hooks
    onMounted(() => {
      // Initial mobile check
      checkMobile()
      
      // Add resize listener
      window.addEventListener('resize', checkMobile)
      
      // Animate sidebar elements
      nextTick(() => {
        animateSidebar()
        updateActiveTab()
      })
      
      // Fetch initial data
      fetchKeywords()
      fetchObjects()
      fetchTelegramRecipients()
      
      // Setup occasional settings icon rotation animation
      setInterval(() => {
        if (!showSettings.value && settingsToggleRef.value) {
          anime({
            targets: settingsToggleRef.value,
            rotate: '+=45deg',
            duration: 3000,
            easing: 'easeInOutQuad'
          })
        }
      }, 10000) // Every 10 seconds
    })
    
    onUnmounted(() => {
      // Remove event listeners
      window.removeEventListener('resize', checkMobile)
      
      // Clear any timeouts
      if (toastTimeout.value) {
        clearTimeout(toastTimeout.value)
      }
    })
    
    return {
      appTheme,
      isDarkTheme,
      isMobile,
      windowWidth,
      navButtons,
      mobileNavButtons,
      sidebarRef,
      settingsToggleRef,
      settingsPopupRef,
      showSettings,
      modalsRef,
      footerRef,
      headerRef,
      mobileNavRef,
      hamburgerButtonRef,
      hamburgerPopupRef,
      showHamburgerMenu,
      refreshButtonRef,
      showLogoutOverlay,
      logoutOverlayRef,
      logoutSpinnerRef,
      spinnerCircleRef,
      keywordButtonRef,
      objectButtonRef,
      telegramButtonRef,
      toastRef,
      showToast,
      toastMessage,
      toastType,
      toastIcon,
      chatKeywords,
      flaggedObjects,
      telegramRecipients,
      agentTabs,
      agentSettings,
      changeTab,
      toggleSettings,
      toggleHamburgerMenu,
      changeTabFromMenu,
      refreshDashboard,
      showToastNotification,
      openAddKeywordModal,
      openAddObjectModal,
      openAddTelegramModal,
      openHamburgerKeywordModal,
      openHamburgerObjectModal,
      openHamburgerTelegramModal,
      logout,
      saveSettings
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
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.status-indicator {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
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

.settings-section-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 8px 16px;
}

.settings-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  width: 100%;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-color);
  font-size: 14px;
  text-align: left;
  transition: background-color 0.2s;
}

.settings-item:hover {
  background-color: var(--hover-bg);
}

.settings-item.flag-item {
  color: var(--primary-color);
}

.settings-item.logout {
  color: var(--danger-color);
  border-top: 1px solid var(--input-border);
  margin-top: 4px;
  padding-top: 12px;
}

.left-icon, .right-icon {
  flex-shrink: 0;
}

.right-icon {
  margin-left: auto;
}

/* Mobile navigation */
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background-color: var(--bg-color);
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0 16px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
  border-top: 1px solid var(--input-border);
  transition: background-color 0.3s ease;
}

.mobile-nav-button {
  height: 48px;
  flex: 1;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  color: var(--text-color);
  border: none;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
}

.mobile-nav-button:hover {
  background-color: var(--hover-bg);
}

.mobile-nav-button.active {
  color: var(--primary-color);
  font-weight: 500;
  background-color: var(--primary-bg-subtle);
}

.hamburger-button {
  max-width: 48px;
}

.mobile-notification-badge {
  position: absolute;
  top: 6px;
  right: 50%;
  transform: translateX(12px);
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  background-color: var(--danger-color, #EF4444);
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  box-shadow: 0 2px 5px rgba(239, 68, 68, 0.3);
  animation: notify-bounce 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* Hamburger menu */
.hamburger-popup {
  position: fixed;
  bottom: 70px;
  left: 8px;
  right: 8px;
  background-color: var(--bg-color);
  border-radius: 12px;
  border: 1px solid var(--input-border);
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.15);
  z-index: 200;
  max-height: 80vh;
  overflow-y: auto;
  /* Add animation */
  animation: popup-fade-in 0.3s ease-out;
}

/* Toast notification */
.toast-notification {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 16px;
  border-radius: 8px;
  background-color: var(--bg-color);
  color: var(--text-color);
  font-size: 0.9rem;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 1000;
  min-width: 200px;
  max-width: 90%;
  animation: slideUp 0.3s forwards;
  border: 1px solid var(--input-border);
}

.toast-notification.success {
  border-left: 4px solid var(--success-color, #10B981);
}

.toast-notification.error {
  border-left: 4px solid var(--danger-color, #EF4444);
}

.toast-notification.info {
  border-left: 4px solid var(--primary-color, #3B82F6);
}

.toast-icon {
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
}

/* Logout overlay */
.logout-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.logout-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spinner-circle {
  width: 50px;
  height: 50px;
  animation: rotate 2s linear infinite;
}

.spinner-circle .path {
  stroke: var(--primary-color, #3B82F6);
  stroke-linecap: round;
  animation: dash 1.5s ease-in-out infinite;
}

.logout-text {
  color: white;
  font-size: 1rem;
}

/* Animations */
@keyframes rotate {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes dash {
  0% {
    stroke-dasharray: 1, 150;
    stroke-dashoffset: 0;
  }
  50% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -35;
  }
  100% {
    stroke-dasharray: 90, 150;
    stroke-dashoffset: -124;
  }
}

@keyframes slideUp {
  0% {
    transform: translate(-50%, 20px);
    opacity: 0;
  }
  100% {
    transform: translate(-50%, 0);
    opacity: 1;
  }
}

@keyframes popup-fade-in {
  0% {
    transform: translateY(20px) scale(0.95);
    opacity: 0;
  }
  100% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

@keyframes notify-bounce {
  0% { 
    transform: translateX(12px) scale(0.8); 
    opacity: 0; 
  }
  50% { 
    transform: translateX(12px) scale(1.15); 
    opacity: 1; 
  }
  70% { 
    transform: translateX(12px) scale(0.95); 
    opacity: 1; 
  }
  100% { 
    transform: translateX(12px) scale(1); 
    opacity: 1; 
  }
}

/* Settings icon animations are now handled inline with anime.js */
</style>