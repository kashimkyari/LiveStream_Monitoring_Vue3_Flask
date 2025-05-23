<template>
  <SpeedInsights />
  <div id="app" :data-theme="isDarkTheme ? 'dark' : 'light'" :class="{ 'mobile-view': isMobile }" ref="appContainer">
    <!-- Enhanced loading spinner with particle effects -->
    <div v-if="isCheckingAuth || (isLoggedIn && !userRole)" class="loading-overlay">
      <!-- Particle background -->
      <div class="particle-background" ref="particleBackground">
        <div 
          v-for="(style, index) in particleStyles" 
          :key="index" 
          class="background-particle"
          :style="style"
        ></div>
      </div>
      
      <div class="spinner-container" ref="spinnerContainer" @mouseenter="handleSpinnerHover"
        @mouseleave="handleSpinnerLeave">
        <!-- Main glowing particle spinner -->
        <div class="particle-spinner" ref="spinner">
          <div class="orbit-ring"></div>
          <div class="orbit-ring orbit-ring-2"></div>
          <div 
            v-for="n in 8" 
            :key="n" 
            class="spinner-particle" 
            :style="`--i: ${n}; --delay: ${n * 0.15}s`"
          ></div>
          <div class="center-glow"></div>
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
import { SpeedInsights } from '@vercel/speed-insights/vue'
import { useToast } from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import { useIsMobile } from './composables/useIsMobile'

// Components
import LoginComponent from './components/Login.vue'
import AdminDashboard from './components/AdminDashboard.vue'
import AgentDashboard from './components/AgentDashboard.vue'
import MobileAdminDashboard from './components/MobileAdminDashboard.vue'
import MobileAgentDashboard from './components/MobileAgentDashboard.vue'
import MobileLoginComponent from './components/MobileLogin.vue'
import MobileForgotPassword from './components/MobileForgotPassword.vue'

// Icon setup
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
const particleBackground = ref(null)
const showDebugInfo = ref(false)
const mobileAuthView = ref('login')
const unreadNotificationCount = ref(0)
const isOffline = ref(false)
const sessionLastChecked = ref('Never')
const loadingMessage = ref('Verifying session...')
const maxRetryAttempts = 3
const retryAttempts = ref(0)
const retryDelay = 3000
const sessionToken = ref(null)
const sessionExpiry = ref(null)
const particleStyles = ref([])

const SESSION_TOKEN_KEY = 'session_token'
const SESSION_EXPIRY_KEY = 'session_expiry'
const USER_ROLE_KEY = 'userRole'
const LAST_CHECKED_KEY = 'session_last_checked'

const { isMobile } = useIsMobile()

const animationConfig = {
  basic: { duration: 800, easing: 'easeOutExpo' },
  mobile: { duration: 400, easing: 'easeOutExpo' }
}

const getAnimationParams = () =>
  isMobile.value ? animationConfig.mobile : animationConfig.basic

const generateParticleStyles = () => {
  const styles = []
  for (let i = 0; i < 50; i++) {
    const size = Math.random() * 4 + 1
    const x = Math.random() * 100
    const y = Math.random() * 100
    const duration = Math.random() * 20 + 10
    const delay = Math.random() * 5
    const opacity = Math.random() * 0.3 + 0.1
    
    styles.push({
      width: `${size}px`,
      height: `${size}px`,
      left: `${x}%`,
      top: `${y}%`,
      animationDuration: `${duration}s`,
      animationDelay: `${delay}s`,
      opacity: opacity
    })
  }
  return styles
}

const handleSpinnerHover = () => {
  anime({
    targets: spinnerContainer.value.querySelectorAll('.spinner-particle'),
    scale: 1.3,
    duration: 300,
    easing: 'easeOutBack'
  })
  
  anime({
    targets: spinnerContainer.value.querySelector('.center-glow'),
    scale: 1.2,
    duration: 300,
    easing: 'easeOutBack'
  })
}

const handleSpinnerLeave = () => {
  anime({
    targets: spinnerContainer.value.querySelectorAll('.spinner-particle'),
    scale: 1,
    duration: 300,
    easing: 'easeOutBack'
  })
  
  anime({
    targets: spinnerContainer.value.querySelector('.center-glow'),
    scale: 1,
    duration: 300,
    easing: 'easeOutBack'
  })
}

provide('theme', isDarkTheme)
provide('updateTheme', (isDark) => { isDarkTheme.value = isDark })
provide('toast', toast)

const detectSystemTheme = () => {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  isDarkTheme.value = prefersDark
  localStorage.setItem('themePreference', prefersDark ? 'dark' : 'light')
  document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light')
}

watch(isDarkTheme, (newValue) => {
  const theme = newValue ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem('themePreference', theme)
})

const initSpinnerAnimation = () => {
  if (!spinnerContainer.value) return

  anime({
    targets: spinnerContainer.value,
    opacity: [0, 1],
    translateY: ['-20px', '0px'],
    ...getAnimationParams()
  })

  anime({
    targets: spinnerContainer.value.querySelectorAll('.spinner-particle'),
    scale: [0, 1],
    opacity: [0, 1],
    delay: anime.stagger(100),
    duration: 600,
    easing: 'easeOutExpo'
  })

  anime({
    targets: spinnerContainer.value.querySelectorAll('.orbit-ring'),
    scale: [0, 1],
    opacity: [0, 1],
    duration: 800,
    easing: 'easeOutExpo'
  })

  anime({
    targets: spinnerContainer.value.querySelector('.center-glow'),
    scale: [0, 1],
    opacity: [0, 1],
    duration: 600,
    delay: 200,
    easing: 'easeOutExpo'
  })

  if (particleBackground.value) {
    anime({
      targets: particleBackground.value.querySelectorAll('.background-particle'),
      opacity: [0, 1],
      delay: anime.stagger(50),
      duration: 1000,
      easing: 'easeOutExpo'
    })
  }
}

const checkNetworkStatus = () => {
  const online = navigator.onLine
  isOffline.value = !online

  if (!online && isLoggedIn.value) {
    toast.warning("You're currently offline. Limited functionality available.")
  }

  return online
}

const handleNetworkChange = () => {
  const wasOffline = isOffline.value
  const online = checkNetworkStatus()

  if (online && wasOffline) {
    toast.info("You're back online. Syncing data...")
    checkAuthentication(true)
  }
}

const isSessionExpired = () => {
  if (!sessionExpiry.value) return true
  return new Date().getTime() > parseInt(sessionExpiry.value)
}

const storeSessionToken = (token, expiresIn = 86400) => {
  if (!token) return

  sessionToken.value = token
  const expiryTime = new Date().getTime() + (expiresIn * 1000)
  sessionExpiry.value = expiryTime.toString()

  localStorage.setItem(SESSION_TOKEN_KEY, token)
  localStorage.setItem(SESSION_EXPIRY_KEY, expiryTime.toString())
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

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

    if (!isSessionExpired()) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
      if (storedRole) {
        userRole.value = storedRole
        return true
      }
    }
  }

  return false
}

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
  userRole.value = user.username === 'admin' ? 'admin' : 'agent'
  localStorage.setItem(USER_ROLE_KEY, userRole.value)
  animateControls()

  nextTick(() => {
    userRole.value = user.username === 'admin' ? 'admin' : 'agent'
  })

  if (user.token) {
    storeSessionToken(user.token, user.expiresIn || 86400)
  }

  const now = new Date().getTime()
  localStorage.setItem(LAST_CHECKED_KEY, now.toString())
  sessionLastChecked.value = new Date(now).toLocaleString()
}

const checkAuthentication = async (isRetry = false) => {
  try {
    if (isRetry) {
      loadingMessage.value = `Reconnecting... (Attempt ${retryAttempts.value + 1}/${maxRetryAttempts})`
    } else {
      loadingMessage.value = 'Verifying session...'
    }

    if (!checkNetworkStatus()) {
      if (restoreSessionFromStorage()) {
        isLoggedIn.value = true
        hideSpinner()
        return
      } else {
        isLoggedIn.value = false
        hideSpinner()
        return
      }
    }

    const useStoredSession = restoreSessionFromStorage()
    const { data } = await axios.get('/api/session')

    if (data.isLoggedIn) {
      handleAuthSuccess(data.user)
    } else {
      if (useStoredSession && !isSessionExpired()) {
        try {
          const tokenAuthResponse = await axios.post('/api/auth/token-verify', {
            token: sessionToken.value
          })

          if (tokenAuthResponse.data && tokenAuthResponse.data.valid) {
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
      logout(false)
    }
  } catch (error) {
    if (retryAttempts.value < maxRetryAttempts) {
      retryAttempts.value++
      if (restoreSessionFromStorage() && !isSessionExpired()) {
        isLoggedIn.value = true
        userRole.value = localStorage.getItem(USER_ROLE_KEY)
      }
      setTimeout(() => checkAuthentication(true), retryDelay)
      return
    }

    if (restoreSessionFromStorage() && !isSessionExpired()) {
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

const startSessionRefresh = () => {
  const REFRESH_INTERVAL = 5 * 60 * 1000
  const sessionInterval = setInterval(async () => {
    if (isOffline.value) return

    try {
      const { data } = await axios.get('/api/session')
      if (data.isLoggedIn) {
        if (data.user && data.user.token) {
          storeSessionToken(data.user.token, data.user.expiresIn || 86400)
        }
        const now = new Date().getTime()
        localStorage.setItem(LAST_CHECKED_KEY, now.toString())
        sessionLastChecked.value = new Date(now).toLocaleString()
      } else {
        toast.warning("Your session has expired. Please log in again.")
        logout(false)
      }
    } catch (error) {
      console.error("Session refresh error:", error)
    }
  }, REFRESH_INTERVAL)

  onUnmounted(() => {
    if (sessionInterval) {
      clearInterval(sessionInterval)
    }
  })
}

const handleLoginSuccess = (userData) => {
  retryAttempts.value = 0
  handleAuthSuccess(userData)
  toast.success("Welcome back!", {
    timeout: 2000,
    position: "top-center",
    icon: true
  })
  startSessionRefresh()
}

const logout = (showAlert = true) => {
  localStorage.removeItem(SESSION_TOKEN_KEY)
  localStorage.removeItem(SESSION_EXPIRY_KEY)
  localStorage.removeItem(USER_ROLE_KEY)
  isLoggedIn.value = false
  userRole.value = null
  sessionToken.value = null
  sessionExpiry.value = null
  delete axios.defaults.headers.common['Authorization']
  if (showAlert) {
    toast.info("You have been logged out", {
      timeout: 2000,
      position: "top-center",
      icon: true
    })
  }
}

onMounted(() => {
  detectSystemTheme()
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    isDarkTheme.value = e.matches
  })

  particleStyles.value = generateParticleStyles()
  axios.defaults.baseURL = "https://monitor-backend.jetcamstudio.com:5000"
  axios.defaults.withCredentials = true

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

  const urlParams = new URLSearchParams(window.location.search)
  showDebugInfo.value = urlParams.get('debug') === 'true'

  window.addEventListener('keydown', (e) => {
    if (e.shiftKey && e.altKey && e.code === 'KeyD') {
      showDebugInfo.value = !showDebugInfo.value
      toast.info(showDebugInfo.value ? 'Debug mode activated' : 'Debug mode deactivated')
    }
  })

  window.addEventListener('online', handleNetworkChange)
  window.addEventListener('offline', handleNetworkChange)
  checkNetworkStatus()
  setTimeout(checkAuthentication, 1500)
})
</script>

<style>
@import url('./styles/theme.css');

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: var(--bg-primary);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  backdrop-filter: blur(10px);
}

.particle-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.background-particle {
  position: absolute;
  background: var(--accent-primary);
  border-radius: 50%;
  animation: float-randomly 15s infinite linear;
  filter: blur(0.5px);
}

@keyframes float-randomly {
  0% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 0.6;
  }
  90% {
    opacity: 0.6;
  }
  100% {
    transform: translate(calc(random() * 100px - 50px), calc(random() * 100px - 50px)) rotate(360deg);
    opacity: 0;
  }
}

.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  z-index: 1;
  position: relative;
}

.particle-spinner {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.orbit-ring {
  position: absolute;
  border: 2px solid transparent;
  border-top: 2px solid var(--accent-primary);
  border-radius: 50%;
  width: 100%;
  height: 100%;
  animation: spin 3s linear infinite;
  opacity: 0.3;
}

.orbit-ring-2 {
  width: 80%;
  height: 80%;
  border-top: 2px solid var(--accent-secondary);
  animation: spin 2s linear infinite reverse;
  opacity: 0.2;
}

.spinner-particle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: radial-gradient(circle, var(--accent-primary) 0%, transparent 70%);
  border-radius: 50%;
  animation: orbit 4s linear infinite;
  animation-delay: calc(var(--delay));
  box-shadow: 
    0 0 10px var(--accent-primary),
    0 0 20px var(--accent-primary),
    0 0 30px var(--accent-primary);
  transform-origin: 60px;
}

.spinner-particle:nth-child(odd) {
  background: radial-gradient(circle, var(--accent-secondary) 0%, transparent 70%);
  box-shadow: 
    0 0 10px var(--accent-secondary),
    0 0 20px var(--accent-secondary),
    0 0 30px var(--accent-secondary);
  animation-direction: reverse;
  animation-duration: 3s;
}

.center-glow {
  position: absolute;
  width: 16px;
  height: 16px;
  background: radial-gradient(circle, var(--accent-primary) 0%, var(--accent-secondary) 50%, transparent 100%);
  border-radius: 50%;
  animation: pulse-glow 2s ease-in-out infinite;
  box-shadow: 
    0 0 20px var(--accent-primary),
    0 0 40px var(--accent-primary),
    0 0 60px var(--accent-primary);
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes orbit {
  from {
    transform: rotate(0deg) translateX(60px) rotate(0deg);
  }
  to {
    transform: rotate(360deg) translateX(60px) rotate(-360deg);
  }
}

@keyframes pulse-glow {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.5);
    opacity: 0.7;
  }
}

.spinner-text {
  color: var(--text-primary);
  font-size: 1.1rem;
  font-weight: 500;
  text-align: center;
  opacity: 0.8;
  animation: text-fade 2s ease-in-out infinite;
}

@keyframes text-fade {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .particle-spinner {
    width: 80px;
    height: 80px;
  }
  
  .spinner-particle {
    width: 6px;
    height: 6px;
    transform-origin: 40px;
  }
  
  .center-glow {
    width: 12px;
    height: 12px;
  }
  
  .spinner-text {
    font-size: 1rem;
  }
  
  .background-particle {
    animation-duration: 10s;
  }
}

[data-theme="dark"] .background-particle {
  filter: blur(0.5px) brightness(0.8);
}

[data-theme="dark"] .spinner-particle {
  box-shadow: 
    0 0 8px var(--accent-primary),
    0 0 16px var(--accent-primary),
    0 0 24px var(--accent-primary);
}

[data-theme="dark"] .center-glow {
  box-shadow: 
    0 0 15px var(--accent-primary),
    0 0 30px var(--accent-primary),
    0 0 45px var(--accent-primary);
}

[data-theme="light"] .loading-overlay {
  background: rgba(255, 255, 255, 0.95);
}

[data-theme="light"] .background-particle {
  filter: blur(0.5px) brightness(1.2);
}

[data-theme="light"] .spinner-particle {
  box-shadow: 
    0 0 6px var(--accent-primary),
    0 0 12px var(--accent-primary),
    0 0 18px var(--accent-primary);
}

[data-theme="light"] .center-glow {
  box-shadow: 
    0 0 10px var(--accent-primary),
    0 0 20px var(--accent-primary),
    0 0 30px var(--accent-primary);
}

.particle-spinner,
.background-particle,
.spinner-particle {
  will-change: transform;
}

@media (prefers-reduced-motion: reduce) {
  .background-particle {
    animation: none;
  }
  
  .orbit-ring,
  .orbit-ring-2 {
    animation-duration: 6s;
  }
  
  .spinner-particle {
    animation-duration: 8s;
  }
  
  .center-glow {
    animation: none;
  }
}
</style>