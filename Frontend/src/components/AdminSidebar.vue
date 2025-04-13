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
        @mouseenter="handleMouseEnter(index)"
        @mouseleave="handleMouseLeave(index)"
      >
        <button 
          :class="{ active: activeTab === tab.id }"
          @click="changeTab(tab.id, $event)"
          class="nav-button"
          :ref="el => { if (el) navButtons[index] = el }"
        >
          <span class="nav-icon">
            <font-awesome-icon :icon="tab.icon" />
          </span>
          <span 
            v-if="tab.id === 'notifications' && unreadCount > 0" 
            class="notification-badge"
          >
            {{ unreadCount }}
          </span>
          <span 
            v-if="tab.id === 'messages' && messageUnreadCount > 0" 
            class="notification-badge"
          >
            {{ messageUnreadCount }}
          </span>
        </button>
        <div class="hover-pill" :ref="el => { if (el) pillRefs[index] = el }">
          <span class="pill-icon">
            <font-awesome-icon :icon="tab.icon" />
          </span>
          <span class="pill-label">{{ tab.label }}</span>
        </div>
      </div>
    </nav>
    
    <div class="sidebar-footer" ref="footerRef">
      <div class="status-indicator">
        <div class="status-dot" :class="{ online: isOnline }"></div>
      </div>
      <button @click="toggleSettings" class="settings-toggle" ref="settingsToggleRef">
        <font-awesome-icon :icon="['fas', 'cog']" />
      </button>
    </div>
  </div>

  <!-- Settings Popup -->
  <div class="settings-popup" v-if="showSettings" ref="settingsPopupRef">
    <div class="user-info">
      <div class="user-avatar">{{ userInitials }}</div>
      <div class="user-details">
        <div class="user-email">{{ user?.email || 'user@example.com' }}</div>
        <div class="user-plan">
          <span class="plan-name">{{ user?.plan?.name || 'Personal' }}</span>
          <span class="plan-type">{{ user?.plan?.type || 'Free plan' }}</span>
        </div>
      </div>
      <div class="user-check" v-if="user?.plan?.active">
        <font-awesome-icon :icon="['fas', 'check']" />
      </div>
    </div>
    <div class="settings-menu">
      <button class="settings-item" @click="goToSettings">
        <span>Settings</span>
      </button>
      <button class="settings-item" @click="viewPlans">
        <span>View all plans</span>
        <span class="new-tag">New</span>
      </button>
      <button class="settings-item" @click="changeLanguage">
        <span>Language</span>
        <span class="beta-tag">BETA</span>
        <font-awesome-icon :icon="['fas', 'chevron-right']" class="right-icon" />
      </button>
      <button class="settings-item" @click="getHelp">
        <span>Get help</span>
      </button>
      <button class="settings-item" @click="learnMore">
        <span>Learn more</span>
        <font-awesome-icon :icon="['fas', 'chevron-right']" class="right-icon" />
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
    >
      <span class="nav-icon">
        <font-awesome-icon :icon="tab.icon" />
      </span>
      <span v-if="tab.id === 'notifications' && unreadCount > 0" class="mobile-notification-badge">
        {{ unreadCount }}
      </span>
      <span v-if="tab.id === 'messages' && messageUnreadCount > 0" class="mobile-notification-badge">
        {{ messageUnreadCount }}
      </span>
    </button>
  </div>
</template>

<script>
import { computed, ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import anime from 'animejs/lib/anime.es.js'
import axios from 'axios'
import { 
  faTachometerAlt, 
  faVideo, 
  faUsers, 
  faBell, 
  faCog,
  faComments,
  faCheck,
  faChevronRight
} from '@fortawesome/free-solid-svg-icons'

library.add(
  faTachometerAlt, 
  faVideo, 
  faUsers, 
  faBell, 
  faCog,
  faComments,
  faCheck,
  faChevronRight
)

export default {
  name: 'AdminSidebar',
  components: {
    FontAwesomeIcon
  },
  props: {
    activeTab: String,
    user: Object,
    isOnline: Boolean,
    notifications: Array,
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
    const pillRefs = ref([])
    const mobileNavButtons = ref([])
    const sidebarRef = ref(null)
    const settingsToggleRef = ref(null)
    const settingsPopupRef = ref(null)
    const animationInProgress = ref(false)
    const activeAnimationIndex = ref(null)
    const showSettings = ref(false)

    const checkMobile = () => {
      windowWidth.value = window.innerWidth
      isMobile.value = windowWidth.value <= 768
    }

    const handleMouseEnter = (index) => {
      const pill = pillRefs.value[index]
      if (!pill || (animationInProgress.value && activeAnimationIndex.value !== index)) return
      
      activeAnimationIndex.value = index
      animationInProgress.value = true
      
      anime.remove(pill)
      anime({
        targets: pill,
        width: ['70px', '200px'],
        opacity: [0, 1],
        easing: 'easeOutQuad',
        duration: 300,
        begin: () => {
          pill.style.display = 'flex'
        },
        complete: () => {
          animationInProgress.value = false
        }
      })
    }

    const handleMouseLeave = (index) => {
      const pill = pillRefs.value[index]
      if (!pill) return
      
      anime.remove(pill)
      anime({
        targets: pill,
        width: ['200px', '70px'],
        opacity: [1, 0],
        easing: 'easeOutQuad',
        duration: 200,
        complete: () => {
          pill.style.display = 'none'
          animationInProgress.value = false
          activeAnimationIndex.value = null
        }
      })
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
        // Position the popup to align with gear icon
        nextTick(() => {
          if (settingsToggleRef.value && settingsPopupRef.value) {
            const toggleRect = settingsToggleRef.value.getBoundingClientRect()
            settingsPopupRef.value.style.bottom = `${window.innerHeight - toggleRect.top}px`
          }
        })
        
        anime({
          targets: settingsToggleRef.value,
          rotate: '+=90',
          duration: 400,
          easing: 'easeInOutQuad'
        })
      } else {
        anime({
          targets: settingsToggleRef.value,
          rotate: '-=90',
          duration: 400,
          easing: 'easeInOutQuad'
        })
      }
    }
    
    const closeSettingsOnOutsideClick = (event) => {
      if (showSettings.value && 
          settingsPopupRef.value && 
          !settingsPopupRef.value.contains(event.target) &&
          settingsToggleRef.value && 
          !settingsToggleRef.value.contains(event.target)) {
        showSettings.value = false
      }
    }
    
    const goToSettings = () => {
      emit('settings', 'general')
      showSettings.value = false
    }
    
    const viewPlans = () => {
      emit('settings', 'plans')
      showSettings.value = false
    }
    
    const changeLanguage = () => {
      emit('settings', 'language')
      showSettings.value = false
    }
    
    const getHelp = () => {
      emit('settings', 'help')
      showSettings.value = false
    }
    
    const learnMore = () => {
      emit('settings', 'learn')
      showSettings.value = false
    }
    
    const logout = async (callApi = true) => {
      if (callApi) {
        try {
          await axios.post('/api/logout')
        } catch (error) {
          console.error('Logout failed:', error)
        }
      }
      emit('logout')
      showSettings.value = false
    }

    onMounted(() => {
      checkMobile()
      window.addEventListener('resize', checkMobile)
      document.addEventListener('click', closeSettingsOnOutsideClick)
      
      // Initialize pills to be hidden
      pillRefs.value.forEach(pill => {
        if (pill) {
          pill.style.opacity = 0
          pill.style.display = 'none'
          pill.style.width = '70px'
        }
      })
    })
    
    onUnmounted(() => {
      window.removeEventListener('resize', checkMobile)
      document.removeEventListener('click', closeSettingsOnOutsideClick)
    })

    const tabs = [
      { id: 'dashboard', label: 'Dashboard', icon: ['fas', 'tachometer-alt'] },
      { id: 'streams', label: 'Streams', icon: ['fas', 'video'] },
      { id: 'agents', label: 'Agents', icon: ['fas', 'users'] },
      { id: 'messages', label: 'Messages', icon: ['fas', 'comments'] },
      { id: 'notifications', label: 'Notifications', icon: ['fas', 'bell'] }
    ]
    
    const unreadCount = computed(() => {
      return props.notifications?.filter(n => !n.read).length || 0
    })
    
    const userInitials = computed(() => {
      if (!props.user || !props.user.name) return 'KM'
      
      const names = props.user.name.split(' ')
      if (names.length >= 2) {
        return (names[0][0] + names[1][0]).toUpperCase()
      }
      return names[0].substring(0, 2).toUpperCase()
    })
    
    watch(() => showSettings.value, (newValue) => {
      if (newValue) {
        anime({
          targets: settingsPopupRef.value,
          opacity: [0, 1],
          translateY: ['-10px', '0px'],
          duration: 200,
          easing: 'easeOutQuad'
        })
      }
    })
    
    return {
      tabs,
      unreadCount,
      toggleSettings,
      isMobile,
      windowWidth,
      changeTab,
      navButtons,
      mobileNavButtons,
      sidebarRef,
      settingsToggleRef,
      handleMouseEnter,
      handleMouseLeave,
      pillRefs,
      showSettings,
      settingsPopupRef,
      userInitials,
      goToSettings,
      viewPlans,
      changeLanguage,
      getHelp,
      learnMore,
      logout
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: 70px;
  height: 100vh;
  background-color: var(--hover-bg);
  border-right: 1px solid var(--input-border);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1100;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.sidebar-header {
  padding: 25px 0;
  display: flex;
  justify-content: center;
}

.logo img {
  width: 40px;
  height: 40px;
  object-fit: contain;
}

.sidebar-nav {
  flex: 1;
  padding: 15px 0;
  overflow: visible;
}

.nav-item-wrapper {
  position: relative;
  margin: 5px 0;
  overflow: visible;
  height: 50px;
}

.nav-button {
  width: 100%;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  position: relative;
}

.nav-button.active {
  background-color: var(--primary-color);
  color: white;
}

.nav-button.active .nav-icon {
  color: white;
}

.nav-icon {
  font-size: 20px;
}

.hover-pill {
  position: absolute;
  top: 0;
  left: 0;
  height: 50px;
  width: 70px;
  background-color: var(--primary-color);
  color: white;
  border-radius: 0 25px 25px 0;
  font-size: 0.9rem;
  white-space: nowrap;
  opacity: 0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  pointer-events: none;
  z-index: 1101;
  display: none;
  align-items: center;
  overflow: hidden;
}

.pill-icon {
  width: 70px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 20px;
}

.pill-label {
  padding-right: 20px;
  font-weight: 500;
}

.notification-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background-color: #dc3545;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: bold;
  z-index: 1102;
}

.sidebar-footer {
  padding: 15px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #6c757d;
}

.status-dot.online {
  background-color: #28a745;
}

.settings-toggle {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.settings-toggle:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

/* Settings Popup Styles */
.settings-popup {
  position: fixed;
  left: 70px;
  width: 280px;
  background-color: var(--bg-color, #ffffff);
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
  z-index: 1200;
  overflow: hidden;
  opacity: 1;
  transform: translateY(0);
  display: flex;
  flex-direction: column;
}

.user-info {
  padding: 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--input-border, #e0e0e0);
}

.user-avatar {
  width: 36px;
  height: 36px;
  background-color: #333;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 12px;
  font-size: 0.9rem;
}

.user-details {
  flex: 1;
}

.user-email {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-color, #333);
  margin-bottom: 2px;
}

.user-plan {
  display: flex;
  flex-direction: column;
}

.plan-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-color, #333);
}

.plan-type {
  font-size: 0.8rem;
  color: var(--text-secondary, #666);
}

.user-check {
  color: #0088ff;
  font-size: 1.2rem;
  margin-left: 8px;
}

.settings-menu {
  display: flex;
  flex-direction: column;
}

.settings-item {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: none;
  border: none;
  text-align: left;
  font-size: 0.9rem;
  color: var(--text-color, #333);
  cursor: pointer;
  transition: background-color 0.2s;
}

.settings-item:hover {
  background-color: var(--hover-bg, #f5f5f5);
}

.settings-item.logout {
  border-top: 1px solid var(--input-border, #e0e0e0);
  margin-top: 4px;
}

.new-tag {
  font-size: 0.75rem;
  color: #0088ff;
  font-weight: 500;
}

.beta-tag {
  font-size: 0.7rem;
  background-color: rgba(0, 0, 0, 0.1);
  color: var(--text-secondary, #666);
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 8px;
}

.right-icon {
  font-size: 0.8rem;
  color: var(--text-secondary, #666);
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
  
  .settings-popup {
    left: 16px;
  }
  
  .mobile-nav {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 65px;
    background-color: var(--hover-bg);
    border-top: 1px solid var(--input-border);
    justify-content: space-around;
    align-items: center;
  }
  
  .mobile-nav-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: transparent;
    border: none;
    color: var(--text-color);
    height: 65px;
    width: 100%;
    position: relative;
  }
  
  .mobile-nav-button.active {
    color: var(--primary-color);
  }
  
  .mobile-notification-badge {
    position: absolute;
    top: 8px;
    right: calc(50% - 15px);
    background-color: #dc3545;
    color: white;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    font-size: 0.75rem;
  }
}

:root[data-theme="dark"] .sidebar,
:root[data-theme="dark"] .mobile-nav {
  background-color: #1e1e2d;
}

:root[data-theme="light"] .sidebar,
:root[data-theme="light"] .mobile-nav {
  background-color: #ffffff;
}

:root[data-theme="dark"] .settings-popup {
  background-color: #1e1e2d;
  border: 1px solid #2d2d3f;
}

:root[data-theme="dark"] .settings-item:hover {
  background-color: #2d2d3f;
}

:root[data-theme="dark"] .user-info {
  border-bottom-color: #2d2d3f;
}

:root[data-theme="dark"] .settings-item.logout {
  border-top-color: #2d2d3f;
}
</style>