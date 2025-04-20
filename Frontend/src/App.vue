<template>
  <div id="app" :data-theme="isDarkTheme ? 'dark' : 'light'" :class="{'mobile-view': isMobile}" ref="appContainer">
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
      <!-- Use mobile or desktop authentication components based on device type -->
      <template v-if="!isCheckingAuth && !isLoggedIn">
        <!-- Mobile Authentication Flow -->
        <template v-if="isMobile">
          <MobileLoginComponent
            v-if="mobileAuthView === 'login'"
            @login-success="handleLoginSuccess"
            @forgot-password="mobileAuthView = 'forgot-password'"
            @create-account="mobileAuthView = 'create-account'"
            key="mobile-login"
          />
          <MobileForgotPassword
            v-else-if="mobileAuthView === 'forgot-password'"
            @back="mobileAuthView = 'login'"
            key="mobile-forgot-password"
          />
          <MobileCreateAccount
            v-else-if="mobileAuthView === 'create-account'"
            @back="mobileAuthView = 'login'"
            @account-created="handleAccountCreated"
            key="mobile-create-account"
          />
        </template>
        
        <!-- Desktop Authentication Flow -->
        <LoginComponent 
          v-else
          @login-success="handleLoginSuccess" 
          key="desktop-login"
        />
      </template>
      
      <div v-else-if="!isCheckingAuth && isLoggedIn" class="dashboard" key="dashboard" ref="dashboardContainer">
        <div class="content-area theme-container">
          <!-- Debug info to help troubleshoot -->
          <div class="debug-info" v-if="showDebugInfo">
            <p>User Role: {{ userRole }}</p>
            <p>Is Admin: {{ userRole === 'admin' }}</p>
            <p>Is Agent: {{ userRole === 'agent' }}</p>
            <p>Is Mobile: {{ isMobile }}</p>
            <p>Is Dark Theme: {{ isDarkTheme }}</p>
            <p>Unread Notifications: {{ unreadNotificationCount }}</p>
          </div>
          
          <!-- Use appropriate component based on device type -->
          <template v-if="userRole === 'admin'">
            <MobileAdminDashboard 
              v-if="isMobile" 
              key="mobile-admin"
              :theme="isDarkTheme ? 'dark' : 'light'"
              :unread-notifications="unreadNotificationCount"
            />
            <AdminDashboard v-else key="admin" />
          </template>
          
          <!-- Agent dashboard with mobile support -->
          <template v-else-if="userRole === 'agent'">
            <MobileAgentDashboard 
              v-if="isMobile" 
              key="mobile-agent"
              :theme="isDarkTheme ? 'dark' : 'light'"
              :unread-notifications="unreadNotificationCount"
            />
            <AgentDashboard v-else key="agent" />
          </template>
          
          <!-- Fallback content if role doesn't match -->
          <div v-else class="role-error">
            <h2>Dashboard Error</h2>
            <p>Unable to load the appropriate dashboard for role: "{{ userRole }}"</p>
            <button @click="logout(true)" class="logout-button mt-4">
              <font-awesome-icon icon="sign-out-alt" class="mr-2" />
              Logout and Try Again
            </button>
          </div>
          
          <!-- Mobile notification system for both admin and agent -->
          <MobileDetectionNotification 
            v-if="isMobile"
            :auto-hide-time="7000"
            @click="handleDetectionClick"
          />
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
  faTachometerAlt, faVideo, faExclamationTriangle, faChartLine, faCog, faUserLock, faUser, faLock,
  faBell, faComment, faCommentAlt, faEye, faCommentDots
} from '@fortawesome/free-solid-svg-icons'
import axios from 'axios'
import anime from 'animejs/lib/anime.es.js'
import LoginComponent from './components/Login.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import AgentDashboard from './components/AgentDashboard.vue'
// Import mobile versions of dashboards
import MobileAdminDashboard from './components/MobileAdminDashboard.vue'
import MobileAgentDashboard from './components/MobileAgentDashboard.vue'
// Import mobile authentication components
import MobileLoginComponent from './components/MobileLogin.vue'
import MobileCreateAccount from './components/MobileCreateAccount.vue'
import MobileForgotPassword from './components/MobileForgotPassword.vue'
// Import mobile notification components
import MobileDetectionNotification from './components/MobileDetectionNotification.vue'
// These components are used by child components
// import MobileNavigationBar from './components/MobileNavigationBar.vue'
// import MobileNotificationBadge from './components/MobileNotificationBadge.vue'
import { useToast } from "vue-toastification"
import "vue-toastification/dist/index.css"
import { useIsMobile } from './composables/useIsMobile'
import { useMobileNotifications } from './composables/useMobileNotifications'

// Add all required icons
library.add(
  faMoon, faSun, faSignOutAlt, faBroadcastTower,
  faTachometerAlt, faVideo, faExclamationTriangle, faChartLine, faCog,
  faUserLock, faUser, faLock, faBell, faComment, faCommentAlt, 
  faEye, faCommentDots
)

export default {
  name: 'App',
  components: {
    FontAwesomeIcon,
    LoginComponent,
    AdminDashboard,
    AgentDashboard,
    MobileAdminDashboard,
    MobileAgentDashboard,
    MobileDetectionNotification,
    MobileLoginComponent,
    MobileCreateAccount,
    MobileForgotPassword
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
    const mobileAuthView = ref('login') // Controls which mobile auth component to show
    
    // Use mobile detection composable
    const { isMobile } = useIsMobile()
    
    // Use mobile notifications composable
    const { 
      notifications, 
      unreadCount: unreadNotificationCount, 
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream
    } = useMobileNotifications()
    
    // Provide theme to child components
    provide('theme', isDarkTheme)
    
    // Provide notification data to child components
    provide('notifications', notifications)
    provide('unreadNotifications', unreadNotificationCount)
    
    // Handle detection notification click
    const handleDetectionClick = (detection) => {
      console.log('Detection notification clicked:', detection);
      
      // If it's a streaming detection, navigate to the stream view
      if (detection?.room_url) {
        toast.info(`Navigating to stream: ${detection.streamer || 'Unknown'}`);
        
        // Navigate to appropriate view based on detection type
        if (detection.event_type === 'keyword_detected') {
          // For keyword detection, go to chat monitoring
          // If we have a stream ID, use that for direct navigation
          const streamId = detection.stream_id || detection.details?.stream_id;
          if (streamId) {
            // Implement appropriate navigation logic here
            console.log(`View stream ${streamId} chat`);
          }
        } else if (detection.event_type === 'object_detected') {
          // For object detection, go to video monitoring
          const streamId = detection.stream_id || detection.details?.stream_id;
          if (streamId) {
            // Implement appropriate navigation logic here
            console.log(`View stream ${streamId} video`);
          }
        }
        
        // Mark as read
        if (detection.id) {
          markAsRead(detection.id);
        }
      }
    };
    
    // Initial setup
    onMounted(() => {
      console.log("App component mounted")
      
      // Load theme preference
      const savedTheme = localStorage.getItem('themePreference')
      isDarkTheme.value = savedTheme ? savedTheme === 'dark' : true
      
      // Set up axios defaults
      axios.defaults.baseURL = "http://localhost:5000"
      axios.defaults.withCredentials = true
      
      // Apply theme to document
      document.documentElement.setAttribute('data-theme', isDarkTheme.value ? 'dark' : 'light')
      
      // Apply theme colors to all areas of the document
      document.documentElement.style.backgroundColor = isDarkTheme.value ? 'var(--dark-bg)' : 'var(--light-bg)'
      document.body.style.backgroundColor = isDarkTheme.value ? 'var(--dark-bg)' : 'var(--light-bg)'
      document.documentElement.style.color = isDarkTheme.value ? 'var(--dark-text)' : 'var(--light-text)'
      document.body.style.color = isDarkTheme.value ? 'var(--dark-text)' : 'var(--light-text)'
      
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
      // Update document theme and background color when theme changes
      document.documentElement.setAttribute('data-theme', newValue ? 'dark' : 'light')
      
      // These are backup styles in case the CSS variables don't apply
      document.documentElement.style.backgroundColor = newValue ? 'var(--dark-bg)' : 'var(--light-bg)'
      document.body.style.backgroundColor = newValue ? 'var(--dark-bg)' : 'var(--light-bg)'
      
      // Ensure all areas use theme colors
      document.documentElement.style.color = newValue ? 'var(--dark-text)' : 'var(--light-text)'
      document.body.style.color = newValue ? 'var(--dark-text)' : 'var(--light-text)'
      
      // Save theme preference to localStorage
      localStorage.setItem('themePreference', newValue ? 'dark' : 'light')
    })
    
    // Method to update theme from child components
    const updateTheme = (isDark) => {
      isDarkTheme.value = isDark
    }
    
    // Provide theme update method to child components
    provide('updateTheme', updateTheme)
    
    // Initialize loading spinner animation
    const initSpinnerAnimation = () => {
      if (!spinnerContainer.value) return;
      
      // Simplify animations on mobile to save resources
      const animationDuration = isMobile.value ? 400 : 800;
      
      // Animate the spinner container
      anime({
        targets: spinnerContainer.value,
        opacity: [0, 1],
        translateY: ['-20px', '0px'],
        duration: animationDuration,
        easing: 'easeOutExpo'
      });
      
      // Animate the spinner circles - simpler on mobile
      anime({
        targets: '.spinner-circle',
        scale: [0, 1],
        opacity: [0, 1],
        delay: anime.stagger(isMobile.value ? 50 : 100, {start: isMobile.value ? 150 : 300}),
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
      
      // Interactive hover effect setup - skip on mobile
      if (!isMobile.value) {
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
      }
    };
    
    // Methods
    const toggleTheme = () => {
      // Skip complex animation on mobile for better performance
      if (isMobile.value) {
        isDarkTheme.value = !isDarkTheme.value
        localStorage.setItem('themePreference', isDarkTheme.value ? 'dark' : 'light')
        return;
      }
      
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
      overlay.style.backgroundColor = isDarkTheme.value ? 'var(--light-bg)' : 'var(--dark-bg)'
      
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
          const newTextColor = isDarkTheme.value ? 'var(--dark-text)' : 'var(--light-text)'
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
      
      // Use simplified animations for mobile
      const animDuration = isMobile.value ? 400 : 800;
      
      // Animate header controls with a smooth entrance
      anime({
        targets: '.header-controls',
        translateY: ['-50px', '0'],
        opacity: [0, 1],
        duration: animDuration,
        easing: 'easeOutExpo'
      })
      
      // Animate sidebar if available
      if (sidebar.value && isLoggedIn.value) {
        anime({
          targets: sidebar.value,
          translateX: ['-100%', '0'],
          opacity: [0, 1],
          duration: animDuration,
          easing: 'easeOutExpo',
          delay: isMobile.value ? 100 : 200
        })
        
        // Animate sidebar items - simplify for mobile
        anime({
          targets: sidebar.value.querySelectorAll('.sidebar-item'),
          translateX: ['-30px', '0'],
          opacity: [0, 1],
          delay: anime.stagger(isMobile.value ? 40 : 80, {start: isMobile.value ? 300 : 600}),
          duration: isMobile.value ? 300 : 600,
          easing: 'easeOutCubic'
        })
      }
      
      // Animate logout button appearance if available
      if (logoutButton.value) {
        anime({
          targets: logoutButton.value,
          translateY: ['20px', '0'],
          opacity: [0, 1],
          delay: isMobile.value ? 600 : 1200,
          duration: isMobile.value ? 300 : 600,
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
            duration: isMobile.value ? 300 : 600,
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
            duration: isMobile.value ? 300 : 600,
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
          duration: isMobile.value ? 300 : 600,
          easing: 'easeInOutExpo',
          complete: () => {
            logout(false);
            isCheckingAuth.value = false;
          }
        });
      }
    };
    
    const handleLoginSuccess = (userData) => {
      console.log("Login successful:", userData);
      isLoggedIn.value = true;
      userRole.value = userData.role;
      
      // Store user role in localStorage
      localStorage.setItem('userRole', userData.role);
    };
    
    const handleAccountCreated = (username) => {
      console.log("Account created successfully for:", username);
      
      // Show success message
      toast.success(`Account created for ${username}! You can now log in.`);
      
      // Switch back to login view
      mobileAuthView.value = 'login';
      
      // Apply entrance animations
      setTimeout(() => {
        animateControls();
      }, 100);
    };
    
    const logout = (showAlert = true) => {
      console.log("Logging out");
      localStorage.removeItem('userRole');
      isLoggedIn.value = false;
      userRole.value = null;
      
      if (showAlert) {
        toast.info("You have been logged out");
      }
    };
    
    const handleResize = () => {
      // For any window resize operations beyond what the useIsMobile composable handles
      console.log("Window resized - handled by useIsMobile composable");
    };
    
    return {
      isMobile,
      isDarkTheme,
      isLoggedIn,
      isCheckingAuth,
      userRole,
      showDebugInfo,
      appContainer,
      themeToggle,
      sidebar,
      dashboardContainer,
      handleDetectionClick,
      unreadNotificationCount,
      notifications,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      spinnerContainer,
      toggleTheme,
      handleLoginSuccess,
      handleAccountCreated,
      mobileAuthView,
      logout
    }
  }
}
</script>

<style>
/* Define CSS variables for theming */
:root {
  /* Light theme colors */
  --light-bg: #f8f9fa;
  --light-text: #2d3748;
  --light-text-secondary: #4a5568;
  --light-border: #e2e8f0;
  --light-card-bg: #ffffff;
  --light-hover: #edf2f7;
  --light-primary: #4299e1;
  --light-secondary: #a0aec0;
  --light-success: #48bb78;
  --light-warning: #ecc94b;
  --light-danger: #f56565;
  --light-shadow: rgba(0, 0, 0, 0.1);
  
  /* Dark theme colors */
  --dark-bg: #121212;
  --dark-bg-elevated: #1e1e1e;
  --dark-text: #f0f0f0;
  --dark-text-secondary: #a0aec0;
  --dark-border: #2d3748;
  --dark-card-bg: #1a1a1a;
  --dark-hover: #2a2a2a;
  --dark-primary: #63b3ed;
  --dark-secondary: #718096;
  --dark-success: #68d391;
  --dark-warning: #f6e05e;
  --dark-danger: #fc8181;
  --dark-shadow: rgba(0, 0, 0, 0.3);
}

/* Base styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  overflow-x: hidden;
  background-color: inherit;
  color: inherit;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background-color 0.5s, color 0.5s;
  min-height: 100vh;
  position: relative;
}

/* Theme-specific styles */
[data-theme='light'] {
  background-color: var(--light-bg);
  color: var(--light-text);
}

[data-theme='dark'] {
  background-color: var(--dark-bg);
  color: var(--dark-text);
}

/* App container */
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header controls */
.header-controls {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  gap: 10px;
}

/* Theme toggle button */
.theme-toggle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--light-text);
  color: var(--light-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

[data-theme='dark'] .theme-toggle {
  background-color: var(--dark-text);
  color: var(--dark-bg);
}

.theme-toggle:hover {
  transform: scale(1.1);
}

/* Dashboard container */
.dashboard {
  display: flex;
  min-height: 100vh;
}

.content-area {
  flex-grow: 1;
  transition: padding 0.3s ease;
  padding: 0;
}

.theme-container {
  width: 100%;
  height: 100%;
}

/* Loading overlay */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

[data-theme='light'] .loading-overlay {
  background-color: rgba(248, 249, 250, 0.8);
}

[data-theme='dark'] .loading-overlay {
  background-color: rgba(18, 18, 18, 0.8);
}

.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.spinner-circle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--light-primary);
  transform: translate(-50%, -50%) rotate(calc(var(--i) * 30deg)) translateY(-30px);
  transform-origin: center;
  opacity: calc(1 - (var(--i) * 0.08));
}

[data-theme='dark'] .spinner-circle {
  background-color: var(--dark-primary);
}

.spinner-text {
  margin-top: 20px;
  font-size: 1rem;
  color: var(--light-text);
  text-align: center;
}

[data-theme='dark'] .spinner-text {
  color: var(--dark-text);
}

/* Error state */
.role-error {
  max-width: 600px;
  margin: 80px auto;
  padding: 30px;
  background-color: var(--light-card-bg);
  border-radius: 8px;
  box-shadow: 0 4px 6px var(--light-shadow);
  text-align: center;
}

[data-theme='dark'] .role-error {
  background-color: var(--dark-card-bg);
  box-shadow: 0 4px 6px var(--dark-shadow);
}

.role-error h2 {
  margin-bottom: 15px;
  color: var(--light-danger);
}

[data-theme='dark'] .role-error h2 {
  color: var(--dark-danger);
}

.role-error p {
  margin-bottom: 20px;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .role-error p {
  color: var(--dark-text-secondary);
}

.logout-button {
  padding: 10px 20px;
  background-color: var(--light-primary);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s ease;
}

[data-theme='dark'] .logout-button {
  background-color: var(--dark-primary);
}

.logout-button:hover {
  background-color: var(--light-primary-dark, #3182ce);
}

[data-theme='dark'] .logout-button:hover {
  background-color: var(--dark-primary-light, #90cdf4);
}

/* Debug info panel */
.debug-info {
  position: fixed;
  top: 70px;
  right: 20px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 9999;
  max-width: 300px;
}

.debug-info p {
  margin: 5px 0;
}

/* Transition animations */
.page-transition-enter-active,
.page-transition-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.page-transition-enter-from,
.page-transition-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* Margin and padding utility classes */
.mt-4 {
  margin-top: 1rem;
}

.mr-2 {
  margin-right: 0.5rem;
}

/* Notification styles */
.notification-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  top: -5px;
  right: -5px;
  min-width: 18px;
  height: 18px;
  background-color: var(--light-danger);
  color: white;
  border-radius: 9px;
  font-size: 10px;
  font-weight: bold;
  padding: 0 4px;
  z-index: 1;
}

[data-theme='dark'] .notification-badge {
  background-color: var(--dark-danger);
}

.notification-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 90%;
  max-width: 350px;
  background-color: var(--light-card-bg);
  box-shadow: -3px 0 15px var(--light-shadow);
  z-index: 1000;
  transition: transform 0.3s ease;
  transform: translateX(100%);
  overflow-y: auto;
}

[data-theme='dark'] .notification-panel {
  background-color: var(--dark-card-bg);
  box-shadow: -3px 0 15px var(--dark-shadow);
}

.notification-panel.open {
  transform: translateX(0);
}

.notification-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.notification-overlay.open {
  opacity: 1;
  pointer-events: auto;
}

.notification-item {
  padding: 12px 15px;
  border-bottom: 1px solid var(--light-border);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

[data-theme='dark'] .notification-item {
  border-bottom-color: var(--dark-border);
}

.notification-item:hover {
  background-color: var(--light-hover);
}

[data-theme='dark'] .notification-item:hover {
  background-color: var(--dark-hover);
}

.notification-item.unread {
  border-left: 3px solid var(--light-primary);
  background-color: rgba(66, 153, 225, 0.05);
}

[data-theme='dark'] .notification-item.unread {
  border-left-color: var(--dark-primary);
  background-color: rgba(99, 179, 237, 0.05);
}

.notification-time {
  font-size: 0.8rem;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .notification-time {
  color: var(--dark-text-secondary);
}

.notification-detection {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 350px;
  background-color: var(--light-card-bg);
  color: var(--light-text);
  border-radius: 8px;
  box-shadow: 0 4px 15px var(--light-shadow);
  padding: 15px;
  z-index: 1001;
  animation: slideUp 0.3s ease forwards;
}

[data-theme='dark'] .notification-detection {
  background-color: var(--dark-card-bg);
  color: var(--dark-text);
  box-shadow: 0 4px 15px var(--dark-shadow);
}

@keyframes slideUp {
  from {
    transform: translate(-50%, 100%);
    opacity: 0;
  }
  to {
    transform: translate(-50%, 0);
    opacity: 1;
  }
}

/* Mobile-specific styles */
@media (max-width: 768px) {
  .header-controls {
    top: 10px;
    right: 10px;
  }
  
  .theme-toggle {
    width: 36px;
    height: 36px;
  }
  
  .content-area {
    padding: 0;
  }
  
  .spinner {
    width: 60px;
    height: 60px;
  }
  
  .spinner-circle {
    width: 8px;
    height: 8px;
    transform: translate(-50%, -50%) rotate(calc(var(--i) * 30deg)) translateY(-24px);
  }
  
  .spinner-text {
    margin-top: 15px;
    font-size: 0.9rem;
  }
  
  .role-error {
    padding: 20px;
    margin: 60px auto;
  }
  
  .debug-info {
    top: 60px;
    right: 10px;
    max-width: 250px;
    font-size: 10px;
  }
  
  .notification-panel {
    width: 100%;
    max-width: none;
  }
  
  .notification-detection {
    bottom: 65px; /* Position above mobile navigation bar */
  }
}
</style>