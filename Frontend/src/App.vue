<template>
  <SpeedInsights/>
  <div id="app" :data-theme="isDarkTheme ? 'dark' : 'light'" ref="appContainer">
    <!-- Theme toggle -->
    <div class="header-controls">
      <div ref="themeToggle" class="theme-toggle" @click="toggleTheme">
        <font-awesome-icon :icon="isDarkTheme ? 'moon' : 'sun'" />
      </div>
    </div>
    
    <!-- Loading spinner while checking authentication -->
    <div v-if="isCheckingAuth" class="loading-overlay">
      <div class="spinner-container" ref="spinnerContainer">
        <div class="spinner">
          <div class="spinner-circle" v-for="n in 12" :key="n" :style="`--i: ${n}`"></div>
        </div>
        <div class="spinner-text">Verifying session...</div>
      </div>
    </div>
    
    <transition name="page-transition" mode="out-in">
      <LoginComponent 
        v-if="!isCheckingAuth && !isLoggedIn" 
        @login-success="handleLoginSuccess" 
        key="login"
      />
      
      <div v-else-if="!isCheckingAuth && isLoggedIn" class="dashboard" key="dashboard" ref="dashboardContainer">
        <div class="content-area">
          <!-- Debug info to help troubleshoot -->
          <div class="debug-info" v-if="showDebugInfo">
            <p>User Role: {{ userRole }}</p>
            <p>Is Admin: {{ userRole === 'admin' }}</p>
            <p>Is Agent: {{ userRole === 'agent' }}</p>
          </div>
          
          <AdminDashboard v-if="userRole === 'admin'" key="admin" />
          <AgentDashboard v-else-if="userRole === 'agent'" key="agent" />
          
          <!-- Fallback content if role doesn't match -->
          <div v-else class="role-error">
            <h2>Dashboard Error</h2>
            <p>Unable to load the appropriate dashboard for role: "{{ userRole }}"</p>
            <button @click="logout(true)" class="logout-button mt-4">
              <font-awesome-icon icon="sign-out-alt" class="mr-2" />
              Logout and Try Again
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch, provide } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import { 
  faMoon, faSun, faSignOutAlt, faBroadcastTower,
  faTachometerAlt, faVideo, faExclamationTriangle, faChartLine, faCog, faUserLock, faUser, faLock
} from '@fortawesome/free-solid-svg-icons'
import axios from 'axios'
import anime from 'animejs/lib/anime.es.js'
import LoginComponent from './components/Login.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import AgentDashboard from './components/AgentDashboard.vue'
import { SpeedInsights } from "@vercel/speed-insights/vue"
import { useToast } from "vue-toastification";
import "vue-toastification/dist/index.css";

// Add all required icons
library.add(
  faMoon, faSun, faSignOutAlt, faBroadcastTower,
  faTachometerAlt, faVideo, faExclamationTriangle, faChartLine, faCog,
  faUserLock, faUser, faLock
)

export default {
  name: 'App',
  components: {
    FontAwesomeIcon,
    LoginComponent,
    AdminDashboard,
    AgentDashboard,
    SpeedInsights
  },
  setup() {
    const toast = useToast();
    const isDarkTheme = ref(true)
    const isLoggedIn = ref(false)
    const isCheckingAuth = ref(true)
    const userRole = ref(null)
    const appContainer = ref(null)
    const themeToggle = ref(null)
    const sidebar = ref(null)
    const logoutButton = ref(null)
    const dashboardContainer = ref(null)
    const spinnerContainer = ref(null)
    const showDebugInfo = ref(false) // Set to true to show debug info
    
    // Provide theme to child components
    provide('theme', isDarkTheme)
    
    // Initial setup
    onMounted(() => {
      console.log("App component mounted")
      
      // Load theme preference
      const savedTheme = localStorage.getItem('themePreference')
      isDarkTheme.value = savedTheme ? savedTheme === 'dark' : true
      
      // Set up axios defaults
      axios.defaults.baseURL = "https://54.86.99.85:5000"
      axios.defaults.withCredentials = true
      
      // Apply theme to document
      document.documentElement.style.backgroundColor = isDarkTheme.value ? '#121212' : '#f8f9fa'
      document.body.style.backgroundColor = isDarkTheme.value ? '#121212' : '#f8f9fa'
      
      // Listen for window resize events
      window.addEventListener('resize', handleResize)
      handleResize()
      
      // Initialize spinner animation
      initSpinnerAnimation();
      
      // Check user authentication status with a small delay for spinner to show
      setTimeout(() => {
        checkAuthentication()
      }, 200)
    })
    
    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize)
    })
    
    // Watch for theme changes
    watch(isDarkTheme, (newValue) => {
      // Update document background color when theme changes
      document.documentElement.style.backgroundColor = newValue ? '#121212' : '#f8f9fa'
      document.body.style.backgroundColor = newValue ? '#121212' : '#f8f9fa'
    })
    
    // Initialize loading spinner animation
    const initSpinnerAnimation = () => {
      if (!spinnerContainer.value) return;
      
      // Animate the spinner container
      anime({
        targets: spinnerContainer.value,
        opacity: [0, 1],
        translateY: ['-20px', '0px'],
        duration: 800,
        easing: 'easeOutExpo'
      });
      
      // Animate the spinner circles
      anime({
        targets: '.spinner-circle',
        scale: [0, 1],
        opacity: [0, 1],
        delay: anime.stagger(100, {start: 300}),
        easing: 'easeOutExpo'
      });
      
      // Pulsing animation for the text
      anime({
        targets: '.spinner-text',
        opacity: [0.6, 1],
        duration: 800,
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine'
      });
      
      // Continuous rotation animation
      anime({
        targets: '.spinner',
        rotate: '360deg',
        duration: 2000,
        loop: true,
        easing: 'linear'
      });
      
      // Interactive hover effect setup
      const spinnerEl = document.querySelector('.spinner-container');
      if (spinnerEl) {
        spinnerEl.addEventListener('mouseenter', () => {
          anime({
            targets: '.spinner-circle',
            scale: 1.2,
            duration: 300,
            easing: 'easeOutElastic(1, .5)'
          });
        });
        
        spinnerEl.addEventListener('mouseleave', () => {
          anime({
            targets: '.spinner-circle',
            scale: 1,
            duration: 500,
            easing: 'easeOutElastic(1, .5)'
          });
        });
      }
    };
    
    // Methods
    const toggleTheme = () => {
      // Create a circular overlay element for the animation
      const overlay = document.createElement('div')
      overlay.className = 'theme-overlay'
      overlay.style.position = 'fixed'
      overlay.style.zIndex = '-1'
      overlay.style.borderRadius = '50%'
      overlay.style.transform = 'scale(0)'
      
      // Get the toggle button position to make the animation start from there
      const toggleRect = themeToggle.value.getBoundingClientRect()
      const centerX = toggleRect.left + toggleRect.width / 2
      const centerY = toggleRect.top + toggleRect.height / 2
      
      overlay.style.top = `${centerY}px`
      overlay.style.left = `${centerX}px`
      
      // Set the color for the opposite theme
      overlay.style.backgroundColor = isDarkTheme.value ? '#f8f9fa' : '#121212'
      
      // Add to DOM
      document.body.appendChild(overlay)
      
      // Animate the toggle icon
      anime({
        targets: themeToggle.value,
        rotate: '+=360',
        scale: [1, 1.2, 1],
        duration: 800,
        easing: 'easeInOutBack'
      })
      
      // Calculate the maximum dimension to ensure the circle covers the entire screen
      const maxDim = Math.max(
        window.innerWidth * 2,
        window.innerHeight * 2
      )
      
      // Animate the overlay
      anime({
        targets: overlay,
        scale: [0, Math.ceil(maxDim / 100)],
        opacity: [0.8, 1],
        duration: 700,
        easing: 'easeOutQuad',
        complete: () => {
          // Change theme state
          isDarkTheme.value = !isDarkTheme.value
          localStorage.setItem('themePreference', isDarkTheme.value ? 'dark' : 'light')
          
          // Update text color for elements
          const newTextColor = isDarkTheme.value ? '#f0f0f0' : '#2d3748'
          anime({
            targets: ['body', '#app'],
            color: newTextColor,
            duration: 300,
            easing: 'easeOutQuad'
          })
          
          // Fade out and remove the overlay
          anime({
            targets: overlay,
            opacity: 0,
            duration: 400,
            easing: 'easeInQuad',
            delay: 200,
            complete: () => {
              document.body.removeChild(overlay)
            }
          })
          
          // Apply subtle fade animation to all content
          anime({
            targets: '.content-area, .sidebar, .header-controls',
            opacity: [0.85, 1],
            duration: 500,
            easing: 'easeOutExpo'
          })
        }
      })
    }
    
    const animateControls = () => {
      console.log("Animating controls")
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
        console.log("Checking authentication status...")
        const response = await axios.get('/api/session');
        
        if (response.data.isLoggedIn) {
          console.log("User is logged in as:", response.data.user.role)
          isLoggedIn.value = true;
          userRole.value = response.data.user.role;
          localStorage.setItem('userRole', response.data.user.role);
          
          // Animate loading spinner exit
          anime({
            targets: spinnerContainer.value,
            translateY: [0, '-20px'],
            opacity: [1, 0],
            duration: 600,
            easing: 'easeInOutExpo',
            complete: () => {
              // Set checking state to false only after animation completes
              isCheckingAuth.value = false;
              
              // Apply animations after login state is confirmed
              setTimeout(() => {
                animateControls();
              }, 100);
            }
          });
        } else {
          console.log("User is not logged in")
          
          // Animate loading spinner exit
          anime({
            targets: spinnerContainer.value,
            translateY: [0, '-20px'],
            opacity: [1, 0],
            duration: 600,
            easing: 'easeInOutExpo',
            complete: () => {
              logout(false);
              isCheckingAuth.value = false;
            }
          });
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
        
        // More specific error handling
        if (error.response && error.response.status === 401) {
          // Session expired or invalid
          toast.warning("Your session has expired. Please log in again.");
        } else {
          // Network error or server error
          toast.error("Could not verify login status. Please check your connection.");
        }
        
        // Animate loading spinner exit
        anime({
          targets: spinnerContainer.value,
          translateY: [0, '-20px'],
          opacity: [1, 0],
          duration: 600,
          easing: 'easeInOutExpo',
          complete: () => {
            logout(false);
            isCheckingAuth.value = false;
          }
        });
      }
    };
    
    const handleLoginSuccess = (role) => {
      console.log("Login successful with role:", role)
      
      isLoggedIn.value = true
      userRole.value = role
      localStorage.setItem('userRole', role)
      
      // Ensure role is properly set
      console.log("Set user role to:", userRole.value)
      
      // Animate content appearance with slight delay to ensure state is updated
      setTimeout(() => {
        anime({
          targets: appContainer.value,
          opacity: [0.8, 1],
          scale: [0.98, 1],
          duration: 600,
          easing: 'easeOutQuad'
        })
        
        // Animate dashboard appearance after login
        setTimeout(() => {
          animateControls()
        }, 100)
      }, 50)
    }
    
    const logout = async (callApi = true) => {
      console.log("Logging out, callApi:", callApi)
      
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
      // Reset user authentication state
      console.log("Resetting user state")
      localStorage.removeItem('userRole')
      isLoggedIn.value = false
      userRole.value = null
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
      isCheckingAuth,
      userRole,
      appContainer,
      themeToggle,
      sidebar,
      logoutButton,
      dashboardContainer,
      spinnerContainer,
      showDebugInfo,
      toggleTheme,
      animateControls,
      checkAuthentication,
      handleLoginSuccess,
      logout,
      resetUserState,
      handleResize,
      initSpinnerAnimation
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
  --primary-color-rgb: 0, 128, 255;
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
  --primary-color-rgb: 0, 128, 255;
}

/* Fix for dark mode white area issue */
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
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
}

/* Loading overlay and spinner styles */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2rem;
}

.spinner {
  position: relative;
  width: 150px;
  height: 150px;
  transform-origin: center;
  cursor: pointer;
}

.spinner-circle {
  position: absolute;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: var(--primary-color);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(calc(30deg * var(--i))) translateY(-60px);
  transform-origin: center;
  filter: drop-shadow(0 0 8px rgba(var(--primary-color-rgb), 0.8));
  opacity: calc(1 - (var(--i) - 1) * 0.08);
  will-change: transform, opacity;
}

.spinner-text {
  font-size: 1.2rem;
  font-weight: 500;
  color: var(--text-color);
  text-align: center;
  letter-spacing: 0.8px;
  margin-top: 1rem;
}

/* Header controls */
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

.theme-overlay {
  pointer-events: none;
  transition: transform 0.7s ease-out;
  will-change: transform, opacity;
}

/* Dashboard layout */
.dashboard {
  display: flex;
  height: 100vh;
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
  padding: 1rem;
  overflow-y: auto;
}

/* Debug Info */
.debug-info {
  position: fixed;
  top: 70px;
  right: 10px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 10px;
  border-radius: 5px;
  font-family: monospace;
  z-index: 9999;
}

/* Error display for role mismatch */
.role-error {
  text-align: center;
  padding: 2rem;
  background: var(--error-bg);
  border: 1px solid var(--error-border);
  border-radius: var(--border-radius-lg);
  max-width: 500px;
  margin: 3rem auto;
}

.role-error h2 {
  color: var(--error-border);
  margin-bottom: 1rem;
}

.mt-4 {
  margin-top: 1rem;
}

.mr-2 {
  margin-right: 0.5rem;
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
    /* Responsive adjustments for content area if needed */
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
    
  }
  
  .header-controls {
    top: 0.5rem;
    right: 0.5rem;
  }
  
  .theme-toggle {
    width: 1.5rem;
    height: 1.5rem;
    padding: 0.6rem;
  }
  
  .spinner {
    width: 120px;
    height: 120px;
  }
  
  .spinner-circle {
    width: 12px;
    height: 12px;
    transform: translate(-50%, -50%) rotate(calc(30deg * var(--i))) translateY(-45px);
  }
}

@media (max-width: 576px) {
  .content-area {
    padding: 0.5rem;
  }
  
  .spinner {
    width: 100px;
    height: 100px;
  }
  
  .spinner-circle {
    width: 10px;
    height: 10px;
    transform: translate(-50%, -50%) rotate(calc(30deg * var(--i))) translateY(-35px);
  }
  
  .spinner-text {
    font-size: 1rem;
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