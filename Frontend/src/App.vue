<template>
  <div id="app" :data-theme="isDarkTheme ? 'dark' : 'light'" ref="appContainer">
    <!-- Theme toggle when not logged in, notifications bell when logged in -->
    <div class="header-controls">
      <div ref="themeToggle" class="theme-toggle" @click="toggleTheme">
        <font-awesome-icon :icon="isDarkTheme ? 'moon' : 'sun'" />
      </div>
    </div>
    
    <transition name="page-transition" mode="out-in">
      <LoginComponent 
        v-if="!isLoggedIn" 
        @login-success="handleLoginSuccess" 
        key="login"
      />
      
      <div v-else class="dashboard" key="dashboard" ref="dashboardContainer">
        
        
        <div class="content-area">
          <AdminDashboard v-if="userRole === 'admin'" key="admin" ref="dashboard" />
          <AgentDashboard v-else-if="userRole === 'agent'" key="agent" ref="dashboard" />
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import { 
  faMoon, faSun, faBell, faSignOutAlt, faBroadcastTower,
  faTachometerAlt, faVideo, faExclamationTriangle, faChartLine, faCog
} from '@fortawesome/free-solid-svg-icons'
import axios from 'axios'
import anime from 'animejs/lib/anime.es.js'
import LoginComponent from './components/Login.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import AgentDashboard from './components/AgentDashboard.vue'

library.add(
  faMoon, faSun, faBell, faSignOutAlt, faBroadcastTower,
  faTachometerAlt, faVideo, faExclamationTriangle, faChartLine, faCog
)

export default {
  name: 'App',
  components: {
    FontAwesomeIcon,
    LoginComponent,
    AdminDashboard,
    AgentDashboard
  },
  setup() {
    const isDarkTheme = ref(true)
    const isLoggedIn = ref(false)
    const userRole = ref(null)
    const unreadNotificationCount = ref(0)
    const appContainer = ref(null)
    const themeToggle = ref(null)
    const sidebar = ref(null)
    const logoutButton = ref(null)
    const dashboard = ref(null)
    const dashboardContainer = ref(null)
    const notificationPollInterval = ref(null)
    
    // Initial setup
    onMounted(() => {
      const savedTheme = localStorage.getItem('themePreference')
      isDarkTheme.value = savedTheme ? savedTheme === 'dark' : true
      
      axios.defaults.baseURL = 'http://localhost:5000'
      axios.defaults.withCredentials = true
      
      checkAuthentication()
      animateControls()
      
      // Fix for dark mode - ensure html and body have proper background
      document.documentElement.style.backgroundColor = isDarkTheme.value ? '#121212' : '#f8f9fa'
      document.body.style.backgroundColor = isDarkTheme.value ? '#121212' : '#f8f9fa'
      
      // Add resize event listener for responsive design
      window.addEventListener('resize', handleResize)
      handleResize()
    })
    
    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize)
      stopNotificationPolling()
    })
    
    // Watch for theme changes
    watch(isDarkTheme, (newValue) => {
      // Update document background color when theme changes
      document.documentElement.style.backgroundColor = newValue ? '#121212' : '#f8f9fa'
      document.body.style.backgroundColor = newValue ? '#121212' : '#f8f9fa'
    })
    
    // Methods
    const toggleTheme = () => {
      // Determine the new background based on current theme
      const newBackground = isDarkTheme.value ? '#f8f9fa' : '#121212'
      const newTextColor = isDarkTheme.value ? '#2d3748' : '#f0f0f0'
      
      // Create an animation timeline for a fluid transition
      const tl = anime.timeline({
        easing: 'easeInOutSine',
        duration: 500
      })
      
      tl.add({
        targets: themeToggle.value,
        rotate: '+=360',
        scale: [1, 1.2, 1],
        duration: 800
      }).add({
        targets: ['html', 'body', '#app'],
        backgroundColor: newBackground,
        color: newTextColor,
        duration: 500
      }, '-=400')
      
      // Add ripple effect animation
      const ripple = document.createElement('div')
      ripple.className = 'theme-toggle-ripple'
      ripple.style.position = 'fixed'
      ripple.style.borderRadius = '50%'
      ripple.style.backgroundColor = isDarkTheme.value ? '#f8f9fa' : '#121212'
      ripple.style.opacity = '0.3'
      ripple.style.transform = 'scale(0)'
      ripple.style.top = '1rem'
      ripple.style.right = '1rem'
      ripple.style.width = '1px'
      ripple.style.height = '1px'
      ripple.style.zIndex = '-1'
      document.body.appendChild(ripple)
      
      anime({
        targets: ripple,
        scale: [0, 30],
        opacity: [0.5, 0],
        duration: 800,
        easing: 'easeOutExpo',
        complete: () => {
          document.body.removeChild(ripple)
        }
      })

      // Toggle theme state and save preference
      isDarkTheme.value = !isDarkTheme.value
      localStorage.setItem('themePreference', isDarkTheme.value ? 'dark' : 'light')
    }
    
    const animateControls = () => {
      // Animate header controls with a smooth entrance
      anime({
        targets: '.header-controls',
        translateY: ['-50px', '0'],
        opacity: [0, 1],
        duration: 800,
        easing: 'easeOutExpo'
      })
      
      // Animate sidebar if available
      if (sidebar.value && isLoggedIn.value) {
        anime({
          targets: sidebar.value,
          translateX: ['-100%', '0'],
          opacity: [0, 1],
          duration: 800,
          easing: 'easeOutExpo',
          delay: 200
        })
        
        // Animate sidebar items
        anime({
          targets: sidebar.value.querySelectorAll('.sidebar-item'),
          translateX: ['-30px', '0'],
          opacity: [0, 1],
          delay: anime.stagger(80, {start: 600}),
          duration: 600,
          easing: 'easeOutCubic'
        })
      }
      
      // Animate logout button appearance if available
      if (logoutButton.value) {
        anime({
          targets: logoutButton.value,
          translateY: ['20px', '0'],
          opacity: [0, 1],
          delay: 1200,
          duration: 600,
          easing: 'easeOutExpo'
        })
      }
    }
    
    const checkAuthentication = async () => {
      try {
        const response = await axios.get('/api/session')
        if (response.data.logged_in) {
          isLoggedIn.value = true
          userRole.value = response.data.user.role
          localStorage.setItem('userRole', response.data.user.role)
          
          // Fetch notifications and start polling
          fetchNotificationCount()
          startNotificationPolling()
          
          // Apply animations after login state is confirmed
          setTimeout(() => {
            animateControls()
          }, 100)
        } else {
          logout(false)
        }
      } catch (error) {
        console.error('Authentication check failed:', error)
        logout(false)
      }
    }
    
    const fetchNotificationCount = async () => {
      try {
        // In a real implementation, this would fetch the count from your API
        // const response = await axios.get('/api/notifications/count')
        // unreadNotificationCount.value = response.data.unreadCount
        
        // For demo purposes, we'll use a random count between 1-5
        unreadNotificationCount.value = Math.floor(Math.random() * 5) + 1
      } catch (error) {
        console.error('Failed to fetch notification count:', error)
      }
    }
    
    const startNotificationPolling = () => {
      // Poll for new notifications every 30 seconds
      notificationPollInterval.value = setInterval(() => {
        if (isLoggedIn.value) {
          fetchNotificationCount()
        }
      }, 30000)
    }
    
    const stopNotificationPolling = () => {
      if (notificationPollInterval.value) {
        clearInterval(notificationPollInterval.value)
      }
    }
    
    const handleLoginSuccess = (role) => {
      isLoggedIn.value = true
      userRole.value = role
      localStorage.setItem('userRole', role)
      
      // Animate content appearance
      anime({
        targets: appContainer.value,
        opacity: [0.8, 1],
        scale: [0.98, 1],
        duration: 600,
        easing: 'easeOutQuad'
      })
      
      fetchNotificationCount()
      startNotificationPolling()
      
      // Animate dashboard appearance after login
      setTimeout(() => {
        animateControls()
      }, 100)
    }
    
    const logout = async (callApi = true) => {
      if (callApi) {
        try {
          await axios.post('/api/logout')
        } catch (error) {
          console.error('Logout failed:', error)
        }
      }
      
      // Animate dashboard exit
      if (dashboardContainer.value) {
        anime({
          targets: dashboardContainer.value,
          translateY: [0, 20],
          opacity: [1, 0],
          duration: 400,
          easing: 'easeInOutSine',
          complete: () => {
            resetUserState()
          }
        })
      } else {
        resetUserState()
      }
    }
    
    const resetUserState = () => {
      // Reset user authentication state and stop polling
      localStorage.removeItem('userRole')
      isLoggedIn.value = false
      userRole.value = null
      unreadNotificationCount.value = 0
      stopNotificationPolling()
    }
    
    const handleResize = () => {
      // Adjust sidebar based on screen size
      if (sidebar.value) {
        if (window.innerWidth < 768) {
          sidebar.value.classList.add('sidebar-collapse')
        } else {
          sidebar.value.classList.remove('sidebar-collapse')
        }
      }
    }
    
    return {
      isDarkTheme,
      isLoggedIn,
      userRole,
      unreadNotificationCount,
      appContainer,
      themeToggle,
      sidebar,
      logoutButton,
      dashboard,
      dashboardContainer,
      toggleTheme,
      animateControls,
      checkAuthentication,
      fetchNotificationCount,
      startNotificationPolling,
      stopNotificationPolling,
      handleLoginSuccess,
      logout,
      resetUserState,
      handleResize
    }
  }
}
</script>

<style>
:root {
  --bg-color: #121212;
  --text-color: #f0f0f0;
  --primary-color: #0080ff;
  --primary-hover: #0070e0;
  --secondary-color: #6c63ff;
  --hover-bg: #1e1e1e;
  --input-bg: #252525;
  --input-border: #383838;
  --card-bg: #1c1c1c;
  --card-border: #333333;
  --error-bg: #2d0000;
  --error-border: #4d0000;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --notification-bg: #ff3860;
  --sidebar-width: 260px;
  --sidebar-collapsed-width: 70px;
  --header-height: 60px;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.5);
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  --transition-fast: 0.2s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;
}

[data-theme="light"] {
  --bg-color: #f8f9fa;
  --text-color: #2d3748;
  --hover-bg: #e9ecef;
  --input-bg: #ffffff;
  --input-border: #e2e8f0;
  --card-bg: #ffffff;
  --card-border: #e2e8f0;
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
  color: var(--text-color);
  transition: background-color 0.5s ease, color 0.5s ease;
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
  transition: background-color 0.5s ease, color 0.5s ease;
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

.theme-toggle {
  cursor: pointer;
  padding: 0.8rem;
  border-radius: 50%;
  background: var(--hover-bg);
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  box-shadow: var(--shadow-md);
}

.theme-toggle:hover {
  background: var(--input-bg);
  transform: translateY(-2px) scale(1.05);
  box-shadow: var(--shadow-lg);
}

/* Dashboard layout */
.dashboard {
  display: flex;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background-color: var(--card-bg);
  border-right: 1px solid var(--card-border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), transform 0.5s ease;
  z-index: 100;
  box-shadow: var(--shadow-sm);
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-collapse {
  width: var(--sidebar-collapsed-width);
}

.sidebar-brand {
  padding: 1.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 1rem;
  border-bottom: 1px solid var(--card-border);
}

.sidebar-menu {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1rem 0;
}

.sidebar-item {
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.sidebar-item:hover {
  background-color: var(--hover-bg);
}

.sidebar-item.active {
  background-color: var(--primary-color);
  color: white;
}

.sidebar-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 4px;
  background-color: var(--secondary-color);
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--card-border);
}

.logout-button {
  padding: 0.8rem 1.5rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: var(--border-radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 500;
  box-shadow: var(--shadow-sm);
}

.logout-button:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.content-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1rem;
  padding-top: calc(var(--header-height) + 1rem);
}

/* Page transitions */
.page-transition-enter-active,
.page-transition-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.page-transition-enter-from,
.page-transition-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* Media queries */
@media (max-width: 992px) {
  .content-area {
    padding-left: var(--sidebar-collapsed-width);
  }
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 1000;
    transform: translateX(-100%);
  }
  
  .sidebar.show {
    transform: translateX(0);
  }
  
  .content-area {
    padding-left: 1rem;
  }
  
  .header-controls {
    top: 0.5rem;
    right: 0.5rem;
  }
  
  .theme-toggle {
    width: 2.5rem;
    height: 2.5rem;
    padding: 0.6rem;
  }
}

@media (max-width: 576px) {
  .content-area {
    padding: 0.5rem;
    padding-top: calc(var(--header-height) + 0.5rem);
  }
}

/* Sidebar collapse transition */
.sidebar-collapse .sidebar-brand span,
.sidebar-collapse .sidebar-item span,
.sidebar-collapse .logout-button span {
  display: none;
}

.sidebar-collapse .sidebar-item {
  display: flex;
  justify-content: center;
  padding: 1rem;
}

.sidebar-collapse .sidebar-footer {
  display: flex;
  justify-content: center;
}

.sidebar-collapse .logout-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>