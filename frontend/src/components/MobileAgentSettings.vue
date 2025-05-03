<template>
  <div class="mobile-agent-settings">
    <div class="section-header">
      <h2>Settings</h2>
    </div>

    <div class="settings-form">
      <div class="form-group">
        <label class="form-label">Notification Preferences</label>
        <div class="toggle-option">
          <span>Email Notifications</span>
          <div 
            class="toggle-switch" 
            :class="{ active: settings.emailNotifications }" 
            @click="toggleEmailNotifications"
          >
            <div class="toggle-switch-handle"></div>
          </div>
        </div>
        
        <div class="toggle-option">
          <span>Push Notifications</span>
          <div 
            class="toggle-switch" 
            :class="{ active: settings.pushNotifications }" 
            @click="togglePushNotifications"
          >
            <div class="toggle-switch-handle"></div>
          </div>
        </div>
        
        <!-- Telegram connection status -->
        <div class="telegram-status" v-if="settings.pushNotifications">
          <div v-if="telegramConnected" class="status-connected">
            <font-awesome-icon :icon="['fab', 'telegram']" class="telegram-icon" />
            <div class="status-text">
              <span class="status-label">Connected to Telegram</span>
              <span class="status-username">@{{ telegramUsername }}</span>
            </div>
            <button class="btn-change" @click="showTelegramModal = true">
              Change
            </button>
          </div>
          <div v-else class="status-disconnected" @click="showTelegramModal = true">
            <font-awesome-icon :icon="['fab', 'telegram']" class="telegram-icon" />
            <div class="status-text">
              <span class="status-label">Connect to Telegram</span>
              <span class="status-description">Required for push notifications</span>
            </div>
            <font-awesome-icon icon="chevron-right" class="icon-right" />
          </div>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Theme Preference</label>
        <div class="theme-options">
          <div 
            class="theme-option" 
            :class="{ selected: isDarkTheme }"
            @click="$emit('set-theme', true)"
          >
            <font-awesome-icon icon="moon" />
            <span>Dark</span>
          </div>
          <div 
            class="theme-option" 
            :class="{ selected: !isDarkTheme }"
            @click="$emit('set-theme', false)"
          >
            <font-awesome-icon icon="sun" />
            <span>Light</span>
          </div>
        </div>
      </div>

      <button 
        class="btn btn-primary save-settings" 
        @click="$emit('save-settings')"
      >
        <font-awesome-icon icon="save" class="icon-left" />
        Save Settings
      </button>

      <button 
        class="btn btn-outline-danger logout-button" 
        @click="showLogoutConfirmation = true"
        :disabled="isLoggingOut"
      >
        <font-awesome-icon 
          :icon="isLoggingOut ? 'spinner' : 'sign-out-alt'" 
          :spin="isLoggingOut" 
          class="icon-left"
        />
        {{ isLoggingOut ? 'Logging out...' : 'Logout' }}
      </button>
    </div>
    
    <!-- Custom Mobile Logout Bottom Sheet -->
    <transition name="sheet-slide">
      <div v-if="showLogoutConfirmation" class="bottom-sheet-overlay" @click="showLogoutConfirmation = false">
        <div class="bottom-sheet-container" @click.stop ref="logoutSheet">
          <div class="bottom-sheet-handle"></div>
          <div class="sheet-content">
            <div class="sheet-header">
              <font-awesome-icon icon="sign-out-alt" class="sheet-icon" />
              <h3>Logout Confirmation</h3>
            </div>
            <p class="sheet-message">Are you sure you want to logout from your account?</p>
            <div class="sheet-actions">
              <button 
                class="btn btn-danger" 
                @click="handleLogout"
                :disabled="isLoggingOut"
              >
                <font-awesome-icon 
                  :icon="isLoggingOut ? 'spinner' : 'sign-out-alt'" 
                  :spin="isLoggingOut" 
                  class="icon-left"
                />
                {{ isLoggingOut ? 'Logging out...' : 'Logout' }}
              </button>
              <button 
                class="btn btn-outline-secondary" 
                @click="showLogoutConfirmation = false"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- Mobile Logout Animation -->
    <div v-if="showLogoutAnimation" class="logout-animation-overlay">
      <div class="logout-animation-container" ref="logoutAnimationContainer">
        <font-awesome-icon icon="sign-out-alt" class="logout-icon" ref="logoutIcon" />
        <div class="logout-message" ref="logoutMessage">Logging out...</div>
        <div class="logout-spinner" ref="logoutSpinner">
          <div class="spinner-circle" v-for="n in 12" :key="n" :style="`--i: ${n}`"></div>
        </div>
      </div>
    </div>
    
    <!-- Telegram Setup Modal -->
    <TelegramSetupModal 
      :is-visible="showTelegramModal"
      @close="showTelegramModal = false"
      @telegram-connected="handleTelegramConnected"
    />
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, watch, nextTick, onMounted } from 'vue'
import axios from 'axios'
import anime from 'animejs/lib/anime.es.js'
import TelegramSetupModal from './TelegramSetupModal.vue'

const props = defineProps({
  settings: {
    type: Object,
    default: () => ({
      emailNotifications: true,
      pushNotifications: false
    })
  },
  isDarkTheme: {
    type: Boolean,
    default: false
  },
  isLoggingOut: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'toggle-setting', 
  'set-theme', 
  'save-settings',
  'logout',
  'logout-start',
  'logout-error',
  'update-settings'
])

// Sheet and animation controls
const showLogoutConfirmation = ref(false)
const showLogoutAnimation = ref(false)
const logoutSheet = ref(null)
const logoutAnimationContainer = ref(null)
const logoutIcon = ref(null)
const logoutMessage = ref(null)
const logoutSpinner = ref(null)

// Telegram related state
const showTelegramModal = ref(false)
const telegramConnected = ref(false)
const telegramUsername = ref('')

// Check if telegram is connected on component mount
onMounted(async () => {
  try {
    // Get user settings from localStorage or API
    const userSettings = localStorage.getItem('userSettings')
    if (userSettings) {
      const parsedSettings = JSON.parse(userSettings)
      if (parsedSettings.telegramUsername) {
        telegramConnected.value = true
        telegramUsername.value = parsedSettings.telegramUsername
      }
    }
  } catch (error) {
    console.error('Error loading telegram settings:', error)
  }
})

// Toggle notification settings
const toggleEmailNotifications = () => {
  emit('toggle-setting', 'emailNotifications')
}

const togglePushNotifications = () => {
  // If turning on push notifications and telegram not connected, show the modal
  if (!props.settings.pushNotifications && !telegramConnected.value) {
    showTelegramModal.value = true
  }
  
  emit('toggle-setting', 'pushNotifications')
}

// Handle telegram connection success
const handleTelegramConnected = ({ username, chatId }) => {
  telegramConnected.value = true
  telegramUsername.value = username
  
  // Save to localStorage for persistence
  try {
    const currentSettings = localStorage.getItem('userSettings') 
      ? JSON.parse(localStorage.getItem('userSettings')) 
      : {}
      
    localStorage.setItem('userSettings', JSON.stringify({
      ...currentSettings,
      telegramUsername: username,
      telegramChatId: chatId
    }))
    
    // Update app settings
    emit('update-settings', {
      ...props.settings,
      telegramUsername: username,
      telegramChatId: chatId
    })
  } catch (error) {
    console.error('Error saving telegram settings:', error)
  }
}

// Run animation when the sheet shows
const animateSheet = () => {
  anime({
    targets: logoutSheet.value,
    translateY: ['100%', '0%'],
    duration: 300,
    easing: 'easeOutCubic'
  })
}

// Mobile-optimized logout animation
// Mobile-optimized logout animation
const playLogoutAnimation = () => {
  showLogoutAnimation.value = true
  
  // Wait for next tick to ensure refs are populated after showLogoutAnimation is set to true
  nextTick(() => {
    // Container animation
    if (logoutAnimationContainer.value) {
      anime({
        targets: logoutAnimationContainer.value,
        opacity: [0, 1],
        duration: 400,
        easing: 'easeOutQuad'
      })
    }
    
    // Icon animation
    if (logoutIcon.value) {
      anime({
        targets: logoutIcon.value,
        scale: [0, 1],
        opacity: [0, 1],
        duration: 500,
        easing: 'easeOutBack'
      })
    }
    
    // Message animation
    if (logoutMessage.value) {
      anime({
        targets: logoutMessage.value,
        opacity: [0, 1],
        translateY: ['10px', '0px'],
        delay: 200,
        duration: 400,
        easing: 'easeOutQuad'
      })
    }
    
    // Spinner circles animation
    if (logoutSpinner.value) {
      const spinnerCircles = logoutSpinner.value.querySelectorAll('.spinner-circle')
      anime({
        targets: spinnerCircles,
        scale: [0, 1],
        opacity: [0, 1],
        delay: anime.stagger(50),
        duration: 400,
        easing: 'easeOutExpo',
        complete: () => {
          // Rotate the entire spinner
          if (logoutSpinner.value) {
            anime({
              targets: logoutSpinner.value,
              rotate: '360deg',
              duration: 1500,
              loop: true,
              easing: 'linear'
            })
          }
        }
      })
    }
    
    // After a delay, fade out and complete logout
    setTimeout(() => {
      completeLogout()
    }, 1800) // Slightly shorter for mobile
  })
}

// Fade out animation and complete logout
const completeLogout = () => {
  anime({
    targets: logoutAnimationContainer.value,
    opacity: 0,
    duration: 400,
    easing: 'easeInQuad',
    complete: () => {
      showLogoutAnimation.value = false
      emit('logout')
      // Clear any stored settings on logout
      localStorage.removeItem('userSettings')
      window.location.href = '/dashboard';
    }
  })
}

// Watch for sheet visibility to trigger animation
watch(showLogoutConfirmation, (newValue) => {
  if (newValue) {
    nextTick(() => {
      animateSheet()
    })
  }
})

const handleLogout = async () => {
  try {
    showLogoutConfirmation.value = false
    emit('logout-start')
    
    // Call the logout API endpoint
    const response = await axios.post('/api/logout', {}, {
      withCredentials: true
    })
    
    // If successful, play the logout animation
    if (response.status === 200) {
      playLogoutAnimation()
    }

  } catch (error) {
    console.error('Logout failed:', error)
    emit('logout-error', error)
    showLogoutAnimation.value = false
    // Show toast notification for error (assuming there's a toast system in place)
  }
  // finally {
  //   window.location.href = '/dashboard';
  // }
}
</script>

<style scoped>
.mobile-agent-settings {
  padding: 1rem 0.75rem;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

.section-header {
  margin-bottom: 1.25rem;
  padding: 0 0.5rem;
}

.section-header h2 {
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.settings-form {
  background-color: var(--input-bg);
  border-radius: 16px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.form-group {
  margin-bottom: 1.75rem;
}

.form-label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: var(--primary-color);
  font-size: 1rem;
}

.toggle-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border-color);
}

.toggle-option span {
  font-size: 0.95rem;
}

.toggle-switch {
  width: 48px;
  height: 24px;
  border-radius: 24px;
  background-color: var(--border-color);
  position: relative;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.toggle-switch.active {
  background-color: var(--primary-color);
}

.toggle-switch-handle {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: white;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.toggle-switch.active .toggle-switch-handle {
  transform: translateX(24px);
}

.theme-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.25rem 0.75rem;
  border-radius: 12px;
  background-color: var(--hover-bg);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  touch-action: manipulation;
}

.theme-option:active {
  transform: scale(0.96);
}

.theme-option.selected {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-dark-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.theme-option svg {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.theme-option span {
  font-size: 0.9rem;
  font-weight: 500;
}

.btn {
  width: 100%;
  padding: 0.8rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  touch-action: manipulation;
}

.btn:active {
  transform: scale(0.98);
}

.btn .icon-left {
  margin-right: 0.5rem;
}

.save-settings {
  margin-top: 1.5rem;
  background-color: var(--primary-color);
  border: none;
  color: white;
}

.logout-button {
  margin-top: 0.75rem;
  background-color: red; /* Changed from transparent */
  border: 1.5px solid var(--danger-color);
  color: white; /* Changed from var(--danger-color) */

}

.logout-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Bottom Sheet Styles */
.bottom-sheet-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  z-index: 1000;
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
}

.bottom-sheet-container {
  width: 100%;
  background-color: var(--input-bg);
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
  overflow: hidden;
  transform: translateY(100%);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
}

.bottom-sheet-handle {
  width: 40px;
  height: 4px;
  border-radius: 2px;
  background-color: var(--border-color);
  margin: 12px auto;
}

.sheet-content {
  padding: 0 1.25rem 1.5rem;
}

.sheet-header {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.sheet-icon {
  font-size: 1.3rem;
  color: var(--danger-color);
  margin-right: 0.75rem;
}

.sheet-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-color);
}

.sheet-message {
  margin: 0 0 1.5rem;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text-secondary);
}

.sheet-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.btn-outline-secondary {
  background-color: transparent;
  border: 1.5px solid var(--border-color);
  color: var(--text-color);
}

.btn-danger {
  background-color: red;
  border: none;
  color: white;
}

/* Bottom sheet transitions */
.sheet-slide-enter-active,
.sheet-slide-leave-active {
  transition: opacity 0.3s ease;
}

.sheet-slide-enter-from,
.sheet-slide-leave-to {
  opacity: 0;
}

/* Logout Animation Styles - Mobile Optimized */
.logout-animation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

[data-theme='light'] .logout-animation-overlay {
  background-color: rgba(248, 249, 250, 0.9);
}

[data-theme='dark'] .logout-animation-overlay {
  background-color: rgba(18, 18, 18, 0.9);
}

.logout-animation-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding: 0 2rem;
}

.logout-icon {
  font-size: 3rem;
  color: var(--primary-color);
  margin-bottom: 1rem;
  opacity: 0;
}

[data-theme='light'] .logout-icon {
  color: var(--light-primary);
}

[data-theme='dark'] .logout-icon {
  color: var(--dark-primary);
}

.logout-message {
  font-size: 1.1rem;
  color: white;
  text-align: center;
  margin-bottom: 1.5rem;
  opacity: 0;
}

[data-theme='light'] .logout-message {
  color: var(--light-text);
}

[data-theme='dark'] .logout-message {
  color: var(--dark-text);
}

/* Spinner styles similar to App.vue */
.logout-spinner {
  position: relative;
  width: 60px;
  height: 60px;
}

.spinner-circle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--light-primary);
  transform: translate(-50%, -50%) rotate(calc(var(--i) * 30deg)) translateY(-24px);
  transform-origin: center;
  opacity: calc(1 - (var(--i) * 0.08));
}

[data-theme='dark'] .spinner-circle {
  background-color: var(--dark-primary);
}

/* Vibration feedback on buttons */
@keyframes btn-vibrate {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-2px); }
  40% { transform: translateX(2px); }
  60% { transform: translateX(-2px); }
  80% { transform: translateX(2px); }
}

.btn-danger:active {
  animation: btn-vibrate 0.3s ease;
}
</style>