<template>
  <SpeedInsights />
  <div id="app" :data-theme="isDarkTheme ? 'dark' : 'light'" :class="{ 'mobile-view': isMobile }" ref="appContainer">
    <!-- Loading spinner while checking authentication -->
    <div v-if="isCheckingAuth || (isLoggedIn && !userRole)" class="loading-overlay">
      <div class="spinner-container" ref="spinnerContainer" @mouseenter="handleSpinnerHover"
        @mouseleave="handleSpinnerLeave">
        <div class="spinner" ref="spinner">
          <div class="spinner-circle" v-for="n in 12" :key="n" :style="`--i: ${n}`"></div>
        </div>
        <div class="spinner-text">{{ loadingMessage }}</div>
      </div>
    </div>

    <transition name="page-transition" mode="out-in">
      <!-- Use mobile or desktop authentication components based on device type -->
      <template v-if="!isCheckingAuth && !isLoggedIn">
        <!-- Mobile Authentication Flow -->
        <template v-if="isMobile">
          <MobileLoginComponent v-if="mobileAuthView === 'login'" @login-success="handleLoginSuccess"
            @forgot-password="mobileAuthView = 'forgot-password'" :is-offline="isOffline" key="mobile-login" />
          <MobileForgotPassword v-else-if="mobileAuthView === 'forgot-password'" @back="mobileAuthView = 'login'"
            key="mobile-forgot-password" />
        </template>

        <!-- Desktop Authentication Flow -->
        <LoginComponent v-else @login-success="handleLoginSuccess" key="desktop-login" />
      </template>

      <div v-else-if="!isCheckingAuth && isLoggedIn && userRole" class="dashboard" key="dashboard"
        ref="dashboardContainer">
        <div class="content-area theme-container">
          <!-- Connection status indicator for mobile -->
          <div v-if="isOffline" class="offline-indicator">
            <font-awesome-icon icon="wifi-slash" /> Offline Mode
          </div>

          <!-- Debug info to help troubleshoot -->
          <div class="debug-info" v-if="showDebugInfo">
            <p>User Role: {{ userRole }}</p>
            <p>Is Admin: {{ userRole === 'admin' }}</p>
            <p>Is Agent: {{ userRole === 'agent' }}</p>
            <p>Is Mobile: {{ isMobile }}</p>
            <p>Is Dark Theme: {{ isDarkTheme }}</p>
            <p>Unread Notifications: {{ unreadNotificationCount }}</p>
            <p>Is Offline: {{ isOffline }}</p>
            <p>Session Last Checked: {{ sessionLastChecked }}</p>
          </div>

          <!-- Use appropriate component based on device type -->
          <template v-if="userRole === 'admin'">
            <MobileAdminDashboard v-if="isMobile" key="mobile-admin" :theme="isDarkTheme ? 'dark' : 'light'"
              :unread-notifications="unreadNotificationCount" :is-offline="isOffline" />
            <AdminDashboard v-else key="admin" />
          </template>

          <!-- Agent dashboard with mobile support -->
          <template v-else-if="userRole === 'agent'">
            <MobileAgentDashboard v-if="isMobile" key="mobile-agent" :theme="isDarkTheme ? 'dark' : 'light'"
              :unread-notifications="unreadNotificationCount" :is-offline="isOffline" />
            <AgentDashboard v-else key="agent" />
          </template>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, provide, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import {
  faMoon, faSun, faSignOutAlt, faBroadcastTower, faTachometerAlt,
  faVideo, faExclamationTriangle, faChartLine, faCog, faUserLock,
  faUser, faLock, faBell, faComment, faCommentAlt, faEye, faCommentDots,
  faExclamationCircle, faEyeSlash, faSpinner, faWifi3
} from '@fortawesome/free-solid-svg-icons'
import { faGoogle, faApple } from '@fortawesome/free-brands-svg-icons'
import axios from 'axios'
import anime from 'animejs/lib/anime.es.js'

// Components
import LoginComponent from './components/Login.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import AgentDashboard from './components/AgentDashboard.vue'
import MobileAdminDashboard from './components/MobileAdminDashboard.vue'
import MobileAgentDashboard from './components/MobileAgentDashboard.vue'
import MobileLoginComponent from './components/MobileLogin.vue'
import MobileForgotPassword from './components/MobileForgotPassword.vue'

// Toasts & utilities
import { useToast } from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import { useIsMobile } from './composables/useIsMobile'
import { SpeedInsights } from '@vercel/speed-insights/vue';

// Icon setup - added WiFi slash icon
const faIcons = [
  faMoon, faSun, faSignOutAlt, faBroadcastTower, faTachometerAlt,
  faVideo, faExclamationTriangle, faChartLine, faCog, faUserLock,
  faUser, faLock, faBell, faComment, faCommentAlt, faEye, faCommentDots,
  faExclamationCircle, faEyeSlash, faSpinner, faWifi3
]
const fabIcons = [faGoogle, faApple]
library.add(...faIcons, ...fabIcons)

// State & refs
const toast = useToast()
const isDarkTheme = ref(true)
const isLoggedIn = ref(false)
const isCheckingAuth = ref(true)
const userRole = ref(null)
const appContainer = ref(null)
const sidebar = ref(null)
const logoutButton = ref(null)
const dashboardContainer = ref(null)
const spinnerContainer = ref(null)
const spinner = ref(null)
const showDebugInfo = ref(false)
const mobileAuthView = ref('login')
const unreadNotificationCount = ref(0)
const isOffline = ref(false)
const sessionLastChecked = ref('Never')
const loadingMessage = ref('Verifying session...')
const maxRetryAttempts = 3
const retryAttempts = ref(0)
const retryDelay = 3000 // 3 seconds
const sessionToken = ref(null)
const sessionExpiry = ref(null)

// Local session storage keys
const SESSION_TOKEN_KEY = 'session_token'
const SESSION_EXPIRY_KEY = 'session_expiry'
const USER_ROLE_KEY = 'userRole'
const LAST_CHECKED_KEY = 'session_last_checked'

// Composables
const { isMobile } = useIsMobile()

// Animation configurations
const animationConfig = {
  basic: { duration: 800, easing: 'easeOutExpo' },
  mobile: { duration: 400, easing: 'easeOutExpo' }
}

const getAnimationParams = () =>
  isMobile.value ? animationConfig.mobile : animationConfig.basic

// Spinner hover effects
const handleSpinnerHover = () => {
  anime({
    targets: spinnerContainer.value.querySelectorAll('.spinner-circle'),
    scale: 1.2,
    duration: 300,
    easing: 'easeOutBack'
  })
}

const handleSpinnerLeave = () => {
  anime({
    targets: spinnerContainer.value.querySelectorAll('.spinner-circle'),
    scale: 1,
    duration: 300,
    easing: 'easeOutBack'
  })
}

// Provide theme state and updater
provide('theme', isDarkTheme)
provide('updateTheme', (isDark) => { isDarkTheme.value = isDark })

// Provide toast to child components
provide('toast', toast)

// Theme handling - follow system preference
const detectSystemTheme = () => {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  isDarkTheme.value = prefersDark
  localStorage.setItem('themePreference', prefersDark ? 'dark' : 'light')
  document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
}

// Watch for changes in theme preference
watch(isDarkTheme, (newValue) => {
  const theme = newValue ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem('themePreference', theme)
})

// Spinner animation
const initSpinnerAnimation = () => {
  if (!spinnerContainer.value) return
  const { duration } = getAnimationParams()

  anime({
    targets: spinnerContainer.value,
    opacity: [0, 1],
    translateY: ['-20px', '0px'],
    ...getAnimationParams()
  })

  anime({
    targets: spinnerContainer.value.querySelectorAll('.spinner-circle'),
    scale: [0, 1],
    opacity: [0, 1],
    delay: anime.stagger(duration / 8),
    easing: 'easeOutExpo'
  })

  anime({
    targets: spinner.value,
    rotate: '360deg',
    duration: 2000,
    loop: true,
    easing: 'linear'
  })
}

// Check if the network is online
const checkNetworkStatus = () => {
  const online = navigator.onLine
  isOffline.value = !online

  if (!online && isLoggedIn.value) {
    toast.warning("You're currently offline. Limited functionality available.")
  }

  return online
}

// Network event listeners
const handleNetworkChange = () => {
  const wasOffline = isOffline.value
  const online = checkNetworkStatus()

  if (online && wasOffline) {
    toast.info("You're back online. Syncing data...")
    // Try to refresh session data when back online
    checkAuthentication(true)
  }
}

// Check if session token is expired
const isSessionExpired = () => {
  if (!sessionExpiry.value) return true
  return new Date().getTime() > parseInt(sessionExpiry.value)
}

// Store session token in localStorage
const storeSessionToken = (token, expiresIn = 86400) => {
  if (!token) return

  sessionToken.value = token
  // Calculate expiry time (current time + expiresIn in ms)
  const expiryTime = new Date().getTime() + (expiresIn * 1000)
  sessionExpiry.value = expiryTime.toString()

  // Store in localStorage for persistence
  localStorage.setItem(SESSION_TOKEN_KEY, token)
  localStorage.setItem(SESSION_EXPIRY_KEY, expiryTime.toString())

  // Set for future API calls
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`

  console.log(`Session token stored. Expires in ${expiresIn} seconds`)
}

// Try to restore session from localStorage
const restoreSessionFromStorage = () => {
  const storedToken = localStorage.getItem(SESSION_TOKEN_KEY)
  const storedExpiry = localStorage.getItem(SESSION_EXPIRY_KEY)
  const storedRole = localStorage.getItem(USER_ROLE_KEY)
  const lastChecked = localStorage.getItem(LAST_CHECKED_KEY)

  if (lastChecked) {
    sessionLastChecked.value = new Date(parseInt(lastChecked)).toLocaleString()
  }

  if (storedToken && storedExpiry) {
    sessionToken.value = storedToken
    sessionExpiry.value = storedExpiry

    // Check if token is not expired
    if (!isSessionExpired()) {
      // Set the token in the Authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`

      // If we have a valid stored role, use it
      if (storedRole) {
        console.log('Restoring session from storage with role:', storedRole)
        userRole.value = storedRole
        return true
      }
    } else {
      console.log('Stored session token is expired')
    }
  }

  return false
}

// Authentication handling
const hideSpinner = () => {
  anime({
    targets: spinnerContainer.value,
    translateY: [0, '-20px'],
    opacity: [1, 0],
    ...getAnimationParams(),
    complete: () => (isCheckingAuth.value = false)
  })
}

const handleAuthSuccess = (user) => {
  isLoggedIn.value = true
  // Set role based on username for admin, otherwise default to agent
  userRole.value = user.username === 'admin' ? 'admin' : 'agent'
  localStorage.setItem(USER_ROLE_KEY, userRole.value)
  animateControls()

  // Force re-render by resetting a temporary state
  nextTick(() => {
    userRole.value = user.username === 'admin' ? 'admin' : 'agent'
  })

  // Store session info
  if (user.token) {
    storeSessionToken(user.token, user.expiresIn || 86400)
  }

  // Record the last time we checked the session
  const now = new Date().getTime()
  localStorage.setItem(LAST_CHECKED_KEY, now.toString())
  sessionLastChecked.value = new Date(now).toLocaleString()
}

const checkAuthentication = async (isRetry = false) => {
  try {
    // If retrying, update loading message
    if (isRetry) {
      loadingMessage.value = `Reconnecting... (Attempt ${retryAttempts.value + 1}/${maxRetryAttempts})`
    } else {
      loadingMessage.value = 'Verifying session...'
    }

    // Check if we're offline
    if (!checkNetworkStatus()) {
      console.log("Device is offline, checking for stored session")

      // Try to use stored session data
      if (restoreSessionFromStorage()) {
        console.log("Using stored credentials in offline mode")
        isLoggedIn.value = true
        hideSpinner()
        return
      } else {
        console.log("No valid stored session found for offline mode")
        isLoggedIn.value = false
        hideSpinner()
        return
      }
    }

    // First try to use stored session if available
    const useStoredSession = restoreSessionFromStorage()
    if (useStoredSession) {
      console.log("Found stored session, validating with server...")
    }

    // Enable debug logging for session check
    console.log("Checking authentication status with server")

    const { data } = await axios.get('/api/session')
    console.log("Session check response:", data)

    if (data.isLoggedIn) {
      console.log("User is logged in:", data.user)
      handleAuthSuccess(data.user)
    } else {
      console.log("Server reports user is not logged in, checking localStorage fallback")

      // If server says not logged in, but we restored from storage:
      // Could be a cookie issue but token is still valid
      if (useStoredSession && !isSessionExpired()) {
        console.log("Session token exists but server reports not logged in, trying token auth")

        try {
          // Try to authenticate using the token directly
          const tokenAuthResponse = await axios.post('/api/auth/token-verify', {
            token: sessionToken.value
          })

          if (tokenAuthResponse.data && tokenAuthResponse.data.valid) {
            console.log("Token is valid, session restored")
            handleAuthSuccess({
              role: userRole.value,
              token: tokenAuthResponse.data.refreshedToken || sessionToken.value,
              expiresIn: tokenAuthResponse.data.expiresIn || 86400
            })
            hideSpinner()
            return
          }
        } catch (tokenError) {
          console.error("Token verification failed:", tokenError)
        }
      }

      // If we get here, session couldn't be recovered
      logout(false)
    }
  } catch (error) {
    console.error("Auth check error:", error)
    if (error.response) {
      console.error("Error response:", error.response.data)
    }

    // Handle retry logic - especially important for mobile
    if (retryAttempts.value < maxRetryAttempts) {
      retryAttempts.value++
      console.log(`Authentication check failed. Retrying (${retryAttempts.value}/${maxRetryAttempts})...`)

      // Try to use stored credentials while waiting for retry
      if (restoreSessionFromStorage() && !isSessionExpired()) {
        console.log("Using stored credentials while waiting for retry")
        isLoggedIn.value = true
        userRole.value = localStorage.getItem(USER_ROLE_KEY)
      }

      setTimeout(() => checkAuthentication(true), retryDelay)
      return
    }

    // After max retries, check if we can use offline mode
    if (restoreSessionFromStorage() && !isSessionExpired()) {
      console.log("Using stored credentials after max retries")
      isLoggedIn.value = true
      toast.warning("Connection issues detected. Using offline mode.")
    } else {
      toast.error("Authentication check failed. Please log in again.")
      logout(false)
    }
  } finally {
    hideSpinner()
  }
}

// Control animations
const animateControls = () => {
  const { duration, easing } = getAnimationParams()

  anime({
    targets: '.header-controls',
    translateY: ['-50px', '0'],
    opacity: [0, 1],
    duration,
    easing
  })

  if (sidebar.value && isLoggedIn.value) {
    anime({
      targets: sidebar.value,
      translateX: ['-100%', '0'],
      opacity: [0, 1],
      duration,
      easing
    })

    anime({
      targets: sidebar.value.querySelectorAll('.sidebar-item'),
      translateX: ['-30px', '0'],
      opacity: [0, 1],
      delay: anime.stagger(60),
      duration,
      easing: 'easeOutCubic'
    })
  }

  if (logoutButton.value) {
    anime({
      targets: logoutButton.value,
      translateY: ['20px', '0'],
      opacity: [0, 1],
      duration,
      easing
    })
  }
}

// Start periodic session refresh
const startSessionRefresh = () => {
  // Check session every 5 minutes
  const REFRESH_INTERVAL = 5 * 60 * 1000

  console.log(`Starting session refresh interval (every ${REFRESH_INTERVAL / 1000} seconds)`)

  // Set up refresh interval
  const sessionInterval = setInterval(async () => {
    // Skip refresh if offline
    if (isOffline.value) {
      console.log('Skipping session refresh - device is offline')
      return
    }

    console.log('Performing scheduled session refresh')
    try {
      const { data } = await axios.get('/api/session')

      if (data.isLoggedIn) {
        console.log("Session refreshed successfully")

        // Update token if provided
        if (data.user && data.user.token) {
          storeSessionToken(data.user.token, data.user.expiresIn || 86400)
        }

        // Update last checked timestamp
        const now = new Date().getTime()
        localStorage.setItem(LAST_CHECKED_KEY, now.toString())
        sessionLastChecked.value = new Date(now).toLocaleString()
      } else {
        console.warn("Session expired during refresh")
        toast.warning("Your session has expired. Please log in again.")
        logout(false)
      }
    } catch (error) {
      console.error("Session refresh error:", error)
      // Don't log out on refresh errors, just keep the existing session
    }
  }, REFRESH_INTERVAL)

  // Store reference to allow cleanup
  return sessionInterval
}

// Event handlers
const handleLoginSuccess = (userData) => {
  console.log("Login success:", userData)

  // Reset retry counter
  retryAttempts.value = 0

  handleAuthSuccess(userData)

  // Show toast notification for successful login
  toast.success("Welcome back!", {
    timeout: 2000,
    position: "top-center",
    icon: true
  })

  // Start session refresh
  const sessionInterval = startSessionRefresh()

  // Clear session refresh on component unmount
  onUnmounted(() => {
    if (sessionInterval) {
      clearInterval(sessionInterval)
    }
  })
}

const logout = (showAlert = true) => {
  // Clear session data
  localStorage.removeItem(SESSION_TOKEN_KEY)
  localStorage.removeItem(SESSION_EXPIRY_KEY)
  localStorage.removeItem(USER_ROLE_KEY)

  // Reset state
  isLoggedIn.value = false
  userRole.value = null
  sessionToken.value = null
  sessionExpiry.value = null
  delete axios.defaults.headers.common['Authorization']

  // Show toast notification for logout
  if (showAlert) {
    toast.info("You have been logged out", {
      timeout: 2000,
      position: "top-center",
      icon: true
    })
  }
}

// Lifecycle hooks
onMounted(() => {
  detectSystemTheme()
  // Listen for changes in system theme preference
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    isDarkTheme.value = e.matches
  })

  // Configure axios
  axios.defaults.baseURL = "   https://monitor-backend.jetcamstudio.com:5000"
  axios.defaults.withCredentials = true

  // Add request/response interceptors for debugging
  axios.interceptors.request.use(config => {
    console.log(`Making ${config.method.toUpperCase()} request to ${config.url}`)
    return config
  })

  axios.interceptors.response.use(
    response => {
      console.log(`Response from ${response.config.url}:`, response.status)
      return response
    },
    error => {
      console.error(`Error response from ${error.config?.url}:`, error.response?.status)
      return Promise.reject(error)
    }
  )

  document.documentElement.setAttribute('data-theme', isDarkTheme.value ? 'dark' : 'light')
  initSpinnerAnimation()

  // Set debug flag based on query parameter
  const urlParams = new URLSearchParams(window.location.search)
  showDebugInfo.value = urlParams.get('debug') === 'true'

  // Enable debug info when holding Shift+Alt+D
  window.addEventListener('keydown', (e) => {
    if (e.shiftKey && e.altKey && e.code === 'KeyD') {
      showDebugInfo.value = !showDebugInfo.value
      toast.info(showDebugInfo.value ? 'Debug mode activated' : 'Debug mode deactivated')
    }
  })

  // Set up network status listeners
  window.addEventListener('online', handleNetworkChange)
  window.addEventListener('offline', handleNetworkChange)

  // Check initial network status
  checkNetworkStatus()

  // Delay checking authentication slightly to allow spinner animation
  setTimeout(checkAuthentication, 1500)
})
</script>

<style>
@import url('./styles/theme.css');
/* Additional App-specific styles can be added here if needed */
</style>