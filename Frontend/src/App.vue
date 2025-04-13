<template>
  <div id="app" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <!-- Theme toggle when not logged in, notifications bell when logged in -->
    <div class="header-controls">
      <div ref="themeToggle" class="theme-toggle" @click="toggleTheme">
        <font-awesome-icon :icon="isDarkTheme ? 'moon' : 'sun'" />
      </div>
    </div>
    
    <LoginComponent 
      v-if="!isLoggedIn" 
      @login-success="handleLoginSuccess" 
    />
    
    <div v-else class="dashboard">
      <transition appear @enter="animateEnter">
        <AdminDashboard v-if="userRole === 'admin'" key="admin" ref="dashboard" />
        <AgentDashboard v-else-if="userRole === 'agent'" key="agent" ref="dashboard" />
      </transition>
      
      <button @click="logout" class="logout-button" ref="logoutButton">Logout</button>
    </div>
  </div>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import { faMoon, faSun, faBell } from '@fortawesome/free-solid-svg-icons'
import axios from 'axios'
import anime from 'animejs/lib/anime.es.js'
import LoginComponent from './components/Login.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import AgentDashboard from './components/AgentDashboard.vue'

library.add(faMoon, faSun, faBell)

export default {
  name: 'App',
  components: {
    FontAwesomeIcon,
    LoginComponent,
    AdminDashboard,
    AgentDashboard
  },
  data() {
    return {
      isDarkTheme: true,
      isLoggedIn: false,
      userRole: null,
      showNotificationsPanel: false,
      unreadNotificationCount: 0,
      notificationDropdownPosition: {
        top: '0px',
        left: '0px'
      }
    }
  },
  created() {
    const savedTheme = localStorage.getItem('themePreference')
    this.isDarkTheme = savedTheme ? savedTheme === 'dark' : true
    
    axios.defaults.baseURL = 'http://localhost:5000'
    axios.defaults.withCredentials = true
    
    this.checkAuthentication()

    // Setup event listeners for clicks outside notifications panel
    document.addEventListener('mousedown', this.handleClickOutside)
    
    // Setup notification polling if user is logged in
    if (this.isLoggedIn) {
      this.startNotificationPolling()
    }
  },
  mounted() {
    // Apply initial animations
    this.animateControls()
    
    // Fix for dark mode - ensure html and body have proper background
    document.documentElement.style.backgroundColor = this.isDarkTheme ? '#121212' : '#f8f9fa'
    document.body.style.backgroundColor = this.isDarkTheme ? '#121212' : '#f8f9fa'
  },
  watch: {
    isDarkTheme(newValue) {
      // Update document background color when theme changes
      document.documentElement.style.backgroundColor = newValue ? '#121212' : '#f8f9fa'
      document.body.style.backgroundColor = newValue ? '#121212' : '#f8f9fa'
    }
  },
  beforeUnmount() {
    document.removeEventListener('mousedown', this.handleClickOutside)
    this.stopNotificationPolling()
  },
  methods: {
    toggleTheme() {
      // Determine the new background based on current theme
      const newBackground = this.isDarkTheme ? '#f8f9fa' : '#121212'
      // Create an animation timeline for a fluid transition
      const tl = anime.timeline({
        easing: 'easeInOutSine',
        duration: 500
      })
      tl.add({
        targets: this.$refs.themeToggle,
        rotate: '+=360',
        scale: [1, 1.1],
        duration: 800
      }).add({
        targets: ['html', 'body', '#app'],
        backgroundColor: newBackground,
        duration: 500
      }, '-=300') // Overlap the background animation with the tail of the rotation

      // Toggle theme state and save preference
      this.isDarkTheme = !this.isDarkTheme
      localStorage.setItem('themePreference', this.isDarkTheme ? 'dark' : 'light')
    },
    animateControls() {
      // Animate header controls with a smooth entrance
      anime({
        targets: '.header-controls',
        translateY: ['-50px', '0'],
        opacity: [0, 1],
        duration: 800,
        easing: 'easeOutExpo'
      })
      
      // Animate logout button appearance if available
      if (this.$refs.logoutButton) {
        anime({
          targets: this.$refs.logoutButton,
          translateY: ['20px', '0'],
          opacity: [0, 1],
          delay: 300,
          duration: 600,
          easing: 'easeOutExpo'
        })
      }
    },
    animateEnter(el, done) {
      // Animate dashboard entrance smoothly
      anime({
        targets: el,
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 600,
        easing: 'easeOutExpo',
        complete: done
      })
    },
    async checkAuthentication() {
      try {
        const response = await axios.get('/api/session')
        if (response.data.logged_in) {
          this.isLoggedIn = true
          this.userRole = response.data.user.role
          localStorage.setItem('userRole', response.data.user.role)
          // Fetch notifications and start polling
          this.fetchNotificationCount()
          this.startNotificationPolling()
          
          // Apply animations after login state is confirmed
          this.$nextTick(() => {
            this.animateControls()
          })
        } else {
          this.logout(false)
        }
      } catch (error) {
        console.error('Authentication check failed:', error)
        this.logout(false)
      }
    },
    async fetchNotificationCount() {
      try {
        // In a real implementation, this would fetch the count from your API
        // const response = await axios.get('/api/notifications/count')
        // this.unreadNotificationCount = response.data.unreadCount
        
        // For demo purposes, we'll use a random count between 1-5
        this.unreadNotificationCount = Math.floor(Math.random() * 5) + 1
      } catch (error) {
        console.error('Failed to fetch notification count:', error)
      }
    },
    startNotificationPolling() {
      // Poll for new notifications every 30 seconds
      this.notificationPollInterval = setInterval(() => {
        if (this.isLoggedIn && !this.showNotificationsPanel) {
          this.fetchNotificationCount()
        }
      }, 30000)
    },
    stopNotificationPolling() {
      if (this.notificationPollInterval) {
        clearInterval(this.notificationPollInterval)
      }
    },
    toggleNotifications() {
      if (!this.showNotificationsPanel) {
        // Only update position when opening
        this.calculateDropdownPosition();
      }
      this.showNotificationsPanel = !this.showNotificationsPanel;
      
      if (this.showNotificationsPanel) {
        // Animate notification panel opening
        this.$nextTick(() => {
          const panel = document.querySelector('.notification-dropdown')
          if (panel) {
            anime({
              targets: panel,
              translateY: ['-10px', '0'],
              opacity: [0, 1],
              duration: 300,
              easing: 'easeOutCubic'
            })
          }
        })
      }
    },
    calculateDropdownPosition() {
      if (this.$refs.notificationBell) {
        const bellRect = this.$refs.notificationBell.getBoundingClientRect();
        this.notificationDropdownPosition = {
          top: `${bellRect.bottom + 5}px`,
          left: `${bellRect.left - 260 + bellRect.width}px`
        };
      }
    },
    closeNotifications() {
      if (this.showNotificationsPanel) {
        const panel = document.querySelector('.notification-dropdown')
        if (panel) {
          anime({
            targets: panel,
            translateY: [0, '-10px'],
            opacity: [1, 0],
            duration: 200,
            easing: 'easeInCubic',
            complete: () => {
              this.showNotificationsPanel = false
            }
          })
        } else {
          this.showNotificationsPanel = false
        }
      }
    },
    updateNotificationCount(count) {
      this.unreadNotificationCount = count
    },
    handleClickOutside(event) {
      // Close notifications panel if clicking outside of it
      const notificationBell = this.$refs.notificationBell
      const notificationDropdown = document.querySelector('.notification-dropdown')
      
      if (this.showNotificationsPanel && 
          notificationDropdown && 
          !notificationDropdown.contains(event.target) &&
          notificationBell && 
          !notificationBell.contains(event.target)) {
        this.closeNotifications()
      }
    },
    handleLoginSuccess(role) {
      this.isLoggedIn = true
      this.userRole = role
      localStorage.setItem('userRole', role)
      this.fetchNotificationCount()
      this.startNotificationPolling()
      
      // Animate dashboard appearance after login
      this.$nextTick(() => {
        this.animateControls()
      })
    },
    async logout(callApi = true) {
      if (callApi) {
        try {
          await axios.post('/api/logout')
        } catch (error) {
          console.error('Logout failed:', error)
        }
      }
      
      // Animate dashboard exit if available and then reset state
      if (this.$refs.dashboard) {
        anime({
          targets: this.$refs.dashboard,
          translateY: [0, 20],
          opacity: [1, 0],
          duration: 300,
          easing: 'easeInOutSine',
          complete: () => {
            this.resetUserState()
          }
        })
      } else {
        this.resetUserState()
      }
    },
    resetUserState() {
      // Reset user authentication state and stop polling
      localStorage.removeItem('userRole')
      this.isLoggedIn = false
      this.userRole = null
      this.unreadNotificationCount = 0
      this.showNotificationsPanel = false
      this.stopNotificationPolling()
    }
  }
}
</script>

<style>
:root {
  --bg-color: #121212;
  --text-color: #f0f0f0;
  --primary-color: #007bff;
  --hover-bg: #1e1e1e;
  --input-bg: #252525;
  --input-border: #383838;
  --error-bg: #2d0000;
  --error-border: #4d0000;
  --notification-bg: #ff3860;
  --dropdown-dark-bg: #252525;
  --dropdown-dark-text: #f0f0f0;
  --dropdown-dark-border: #383838;
  --dropdown-light-bg: #ffffff;
  --dropdown-light-text: #2d3748;
  --dropdown-light-border: #e2e8f0;
}

[data-theme="light"] {
  --bg-color: #f8f9fa;
  --text-color: #2d3748;
  --hover-bg: #e9ecef;
  --input-bg: #ffffff;
  --input-border: #e2e8f0;
  --error-bg: #fff5f5;
  --error-border: #fed7d7;
  --notification-bg: #ff3860;
}

/* Fix for dark mode white area issue */
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
  background-color: var(--bg-color);
  transition: background-color 0.3s ease;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-color);
  background-color: var(--bg-color);
  transition: background-color 0.3s ease, color 0.3s ease;
  position: relative;
  min-height: 100vh;
  overflow-x: hidden;
}

.header-controls {
  position: fixed;
  top: 1rem;
  right: 1rem;
  display: flex;
  gap: 1rem;
  z-index: 1000;
}

.theme-toggle, .notification-bell {
  cursor: pointer;
  padding: 0.8rem;
  border-radius: 50%;
  background: var(--hover-bg);
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.theme-toggle:hover, .notification-bell:hover {
  background: var(--input-bg);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.notification-bell {
  position: relative;
}

.notification-badge {
  position: absolute;
  top: 0;
  right: 0;
  background-color: var(--notification-bg);
  color: white;
  border-radius: 50%;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  border: 2px solid var(--bg-color);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  animation: pulse 2s infinite;
  pointer-events: none;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 56, 96, 0.7);
  }
  70% {
    transform: scale(1.1);
    box-shadow: 0 0 0 10px rgba(255, 56, 96, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 56, 96, 0);
  }
}

.logout-button {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  padding: 0.8rem 1.5rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.logout-button:hover {
  opacity: 0.9;
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
}

/* Add new animations */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Notification dropdown animation */
.notification-dropdown {
  transform-origin: top right;
  backface-visibility: hidden;
  will-change: transform, opacity;
}

@media (max-width: 768px) {
  .header-controls {
    top: 0.5rem;
    right: 0.5rem;
    gap: 0.5rem;
  }
  
  .theme-toggle, .notification-bell {
    width: 2.5rem;
    height: 2.5rem;
    padding: 0.6rem;
  }
  
  .notification-badge {
    width: 1.2rem;
    height: 1.2rem;
    font-size: 0.7rem;
  }
  
  .dashboard {
    padding: 1rem;
  }
  
  .logout-button {
    bottom: 1rem;
    right: 1rem;
    padding: 0.6rem 1rem;
  }

  .notification-dropdown {
    width: 290px;
    left: auto !important;
    right: 10px !important;
  }
}
</style>
