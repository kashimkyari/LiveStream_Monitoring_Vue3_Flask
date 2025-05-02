<template>
  <div class="settings-tab" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="tab-header">
      <h2>Settings</h2>
    </div>

    <div class="settings-list">
      <div class="settings-section">
        <h3>Display Settings</h3>
        <div class="setting-item">
          <label class="switch">
            <input
              type="checkbox"
              :checked="isDarkTheme"
              @change="$emit('update:is-dark-theme', $event.target.checked)"
            />
            <span class="slider round"></span>
          </label>
          <span class="setting-label">Dark Mode</span>
        </div>
      </div>

      <div class="settings-section">
        <h3>Data Settings</h3>
        <div class="setting-item">
          <label class="switch">
            <input
              type="checkbox"
              :checked="enableBackgroundRefresh"
              @change="$emit('update:enable-background-refresh', $event.target.checked)"
            />
            <span class="slider round"></span>
          </label>
          <span class="setting-label">Background Refresh</span>
        </div>
        <div class="refresh-interval-setting">
          <span class="setting-label">Refresh Interval</span>
          <select
            :value="refreshIntervalMinutes"
            @input="$emit('update:refresh-interval-minutes', $event.target.value)"
            class="interval-select"
          >
            <option value="1">1 minute</option>
            <option value="5">5 minutes</option>
            <option value="10">10 minutes</option>
            <option value="30">30 minutes</option>
          </select>
        </div>
      </div>

      <div class="settings-section">
        <h3>Notification Settings</h3>
        <div class="setting-item">
          <label class="switch">
            <input
              type="checkbox"
              :checked="settings.pushNotifications"
              @change="togglePushNotifications"
            />
            <span class="slider round"></span>
          </label>
          <span class="setting-label">Push Notifications</span>
        </div>
        <div class="telegram-status" v-if="settings.pushNotifications">
          <div v-if="telegramConnected" class="status-connected">
            <font-awesome-icon :icon="['fab', 'telegram']" class="telegram-icon" />
            <div class="status-text">
              <span class="status-label">Connected to Telegram</span>
              <span class="status-username">@{{ telegramUsername }}</span>
            </div>
            <button class="btn-change" @click="showTelegramModal = true">Change</button>
          </div>
          <div
            v-else
            class="status-disconnected"
            @click="showTelegramModal = true"
          >
            <font-awesome-icon :icon="['fab', 'telegram']" class="telegram-icon" />
            <div class="status-text">
              <span class="status-label">Connect to Telegram</span>
              <span class="status-description">Required for push notifications</span>
            </div>
            <font-awesome-icon icon="chevron-right" class="icon-right" />
          </div>
        </div>
        <div class="setting-item">
          <label class="switch">
            <input
              type="checkbox"
              :checked="isGroupedByType"
              @change="$emit('update:is-grouped-by-type', $event.target.checked)"
            />
            <span class="slider round"></span>
          </label>
          <span class="setting-label">Group by Event Type</span>
        </div>
        <div class="setting-item">
          <label class="switch">
            <input
              type="checkbox"
              :checked="isGroupedByStream"
              @change="$emit('update:is-grouped-by-stream', $event.target.checked)"
            />
            <span class="slider round"></span>
          </label>
          <span class="setting-label">Group by Stream</span>
        </div>
        <div
          class="setting-item notification-action"
          @click="markAllAsRead"
          v-if="unreadCount > 0"
        >
          <font-awesome-icon icon="check-double" class="setting-icon" />
          <span class="setting-label">Mark All as Read ({{ unreadCount }})</span>
        </div>
      </div>

      <div class="settings-section">
        <h3>Account</h3>
        <div
          class="setting-item"
          @click="showLogoutConfirmation = true"
        >
          <font-awesome-icon icon="sign-out-alt" class="setting-icon" />
          <span class="setting-label">Logout</span>
        </div>
      </div>
    </div>

    <!-- Logout Confirmation Bottom Sheet -->
    <transition name="sheet-slide">
      <div
        v-if="showLogoutConfirmation"
        class="bottom-sheet-overlay"
        @click="showLogoutConfirmation = true"
      >
        <div
          class="bottom-sheet-container"
          @click.stop
          ref="logoutSheet"
        >
          <div class="bottom-sheet-handle"></div>
          <div class="sheet-content">
            <div class="sheet-header">
              <font-awesome-icon icon="sign-out-alt" class="sheet-icon" />
              <h3>Logout Confirmation</h3>
            </div>
            <p class="sheet-message">
              Are you sure you want to logout from your account?
            </p>
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
                @click="showLogoutConfirmation = true"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Logout Animation Overlay -->
    <div v-if="showLogoutAnimation" class="logout-animation-overlay">
      <div
        class="logout-animation-container"
        ref="logoutAnimationContainer"
      >
        <font-awesome-icon
          icon="sign-out-alt"
          class="logout-icon"
          ref="logoutIcon"
        />
        <div class="logout-message" ref="logoutMessage">
          Logging out...
        </div>
        <div class="logout-spinner" ref="logoutSpinner">
          <div
            class="spinner-circle"
            v-for="n in 12"
            :key="n"
            :style="`--i: ${n}`"
          ></div>
        </div>
      </div>
    </div>

    <TelegramSetupModal
      :is-visible="showTelegramModal"
      @close="showTelegramModal = false"
      @telegram-connected="handleTelegramConnected"
    />
  </div>
</template>

<script>
import { ref, watch, nextTick, onMounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
  faCheckDouble,
  faSignOutAlt,
  faSpinner,
  faChevronRight
} from '@fortawesome/free-solid-svg-icons'
import { faTelegram } from '@fortawesome/free-brands-svg-icons'
import { library } from '@fortawesome/fontawesome-svg-core'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import anime from 'animejs/lib/anime.es.js'
import TelegramSetupModal from './TelegramSetupModal.vue'

library.add(faCheckDouble, faSignOutAlt, faSpinner, faChevronRight, faTelegram)

export default {
  name: 'MobileAdminSettings',
  components: {
    FontAwesomeIcon,
    TelegramSetupModal
  },
  props: {
    isDarkTheme: {
      type: Boolean,
      default: false
    },
    enableBackgroundRefresh: {
      type: Boolean,
      default: false
    },
    refreshIntervalMinutes: {
      type: [String, Number],
      default: '5'
    },
    isGroupedByType: {
      type: Boolean,
      default: false
    },
    isGroupedByStream: {
      type: Boolean,
      default: false
    },
    unreadCount: {
      type: Number,
      default: 0
    },
    settings: {
      type: Object,
      default: () => ({
        pushNotifications: false
      })
    }
  },
  emits: [
    'update:is-dark-theme',
    'update:enable-background-refresh',
    'update:refresh-interval-minutes',
    'update:is-grouped-by-type',
    'update:is-grouped-by-stream',
    'mark-all-read',
    'logout',
    'logout-start',
    'logout-error',
    'update-settings'
  ],
  setup(props, { emit }) {
    const toast = useToast()
    const showTelegramModal = ref(false)
    const telegramConnected = ref(false)
    const telegramUsername = ref('')
    const showLogoutConfirmation = ref(false)
    const showLogoutAnimation = ref(false)
    const isLoggingOut = ref(false)
    const logoutSheet = ref(null)
    const logoutAnimationContainer = ref(null)
    const logoutIcon = ref(null)
    const logoutMessage = ref(null)
    const logoutSpinner = ref(null)

    onMounted(async () => {
      try {
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

    const togglePushNotifications = () => {
      if (!props.settings.pushNotifications && !telegramConnected.value) {
        showTelegramModal.value = true
      }
      emit('update-settings', {
        ...props.settings,
        pushNotifications: !props.settings.pushNotifications
      })
    }

    const handleTelegramConnected = ({ username, chatId }) => {
      telegramConnected.value = true
      telegramUsername.value = username
      try {
        const currentSettings = localStorage.getItem('userSettings')
          ? JSON.parse(localStorage.getItem('userSettings'))
          : {}
        localStorage.setItem(
          'userSettings',
          JSON.stringify({
            ...currentSettings,
            telegramUsername: username,
            telegramChatId: chatId
          })
        )
        emit('update-settings', {
          ...props.settings,
          telegramUsername: username,
          telegramChatId: chatId,
          pushNotifications: true
        })
        toast.success('Telegram connected successfully')
      } catch (error) {
        console.error('Error saving telegram settings:', error)
        toast.error('Failed to save Telegram settings')
      }
    }

    const markAllAsRead = async () => {
      try {
        await axios.post(
          '/api/notifications/mark-all-read',
          {},
          {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          }
        )
        emit('mark-all-read')
        toast.success('All notifications marked as read')
      } catch (error) {
        console.error('Error marking all notifications as read:', error)
        toast.error('Failed to mark all notifications as read')
      }
    }

    const animateSheet = () => {
      anime({
        targets: logoutSheet.value,
        translateY: ['100%', '0%'],
        duration: 300,
        easing: 'easeOutCubic'
      })
    }

    const playLogoutAnimation = () => {
      showLogoutAnimation.value = true
      window.location.href = '/';
      nextTick(() => {
        if (logoutAnimationContainer.value) {
          anime({
            targets: logoutAnimationContainer.value,
            opacity: [0, 1],
            duration: 400,
            easing: 'easeOutQuad'
          })
        }
        if (logoutIcon.value) {
          anime({
            targets: logoutIcon.value,
            scale: [0, 1],
            opacity: [0, 1],
            duration: 500,
            easing: 'easeOutBack'
          })
        }
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
        window.location.href = '/';
        setTimeout(() => {
          completeLogout();
          
        }, 1800)
      })
    }

    const completeLogout = () => {
      anime({
        targets: logoutAnimationContainer.value,
        opacity: 0,
        duration: 400,
        easing: 'easeInQuad',
        complete: () => {
          showLogoutAnimation.value = false
          emit('logout')
          localStorage.removeItem('token')
          localStorage.removeItem('userSettings')
          toast.info('Logged out successfully')
          // window.location.href = '/'
        }
      })
    }

    const handleLogout = async () => {
      // Trigger vibration feedback
      if (navigator.vibrate) {
        navigator.vibrate(50)
      }
      try {
        showLogoutConfirmation.value = true
        isLoggingOut.value = true
        emit('logout-start')
        const response = await axios.post(
          '/api/logout',
          {},
          {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          }
        )
        if (response.status === 200) {
          // window.location.href = '/';
          playLogoutAnimation();
          

        }
      } catch (error) {
        console.error('Logout failed:', error)
        emit('logout-error', error)
        isLoggingOut.value = false
        showLogoutAnimation.value = false
        toast.error('Logout failed')
      }
    }

    watch(showLogoutConfirmation, (newValue) => {
      if (newValue) {
        nextTick(() => {
          animateSheet()
        })
      }
    })

    return {
      showTelegramModal,
      telegramConnected,
      telegramUsername,
      showLogoutConfirmation,
      showLogoutAnimation,
      isLoggingOut,
      logoutSheet,
      logoutAnimationContainer,
      logoutIcon,
      logoutMessage,
      logoutSpinner,
      togglePushNotifications,
      handleTelegramConnected,
      markAllAsRead,
      handleLogout
    }
  }
}
</script>

<style scoped>
.settings-tab {
  --primary-color: #4361ee;
  --secondary-color: #3f37c9;
  --background-color: #f8f9fa;
  --card-bg: #ffffff;
  --text-color: #333333;
  --text-light: #777777;
  --border-color: #e0e0e0;
  --danger-color: #dc3545;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  --border-radius: 12px;
  --border-radius-sm: 8px;
  background-color: var(--background-color);
  color: var(--text-color);
  padding: 20px;
  min-height: 100vh;
  font-family: 'Arial', sans-serif;
  line-height: 1.5;
}

.settings-tab[data-theme="dark"] {
  --primary-color: #4cc9f0;
  --secondary-color: #4895ef;
  --background-color: #121212;
  --card-bg: #1e1e1e;
  --text-color: #f8f9fa;
  --text-light: #b0b0b0;
  --border-color: #333333;
  --danger-color: #dc3545;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
}

.tab-header {
  margin-bottom: 20px;
}

.tab-header h2 {
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--text-color);
}

.settings-section {
  margin-bottom: 24px;
}

.settings-section h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 12px;
}

.setting-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 0;
}

.setting-label {
  margin-left: 10px;
  font-size: 0.95rem;
  color: var(--text-color);
}

.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  transition: var(--transition);
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 2px;
  bottom: 2px;
  background-color: var(--card-bg);
  transition: var(--transition);
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--primary-color);
}

input:checked + .slider:before {
  transform: translateX(24px);
}

.interval-select {
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  background-color: var(--card-bg);
  color: var(--text-color);
  font-size: 0.95rem;
  width: 120px;
}

.notification-action {
  cursor: pointer;
  color: var(--primary-color);
  padding: 10px;
  border-radius: var(--border-radius-sm);
  transition: background-color 0.2s;
}

.notification-action:hover {
  background-color: var(--primary-light);
}

.setting-icon {
  margin-right: 8px;
  font-size: 1rem;
}

.telegram-status {
  margin: 12px 0;
}

.status-connected,
.status-disconnected {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: var(--border-radius-sm);
  background-color: var(--card-bg);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
}

.status-connected {
  border: 1px solid var(--primary-color);
}

.status-disconnected {
  border: 1px solid var(--border-color);
}

.telegram-icon {
  font-size: 1.5rem;
  color: var(--primary-color);
  margin-right: 12px;
}

.status-text {
  flex: 1;
}

.status-label {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-color);
}

.status-username,
.status-description {
  font-size: 0.85rem;
  color: var(--text-light);
}

.btn-change {
  padding: 6px 12px;
  border: 1px solid var(--primary-color);
  border-radius: var(--border-radius-sm);
  background-color: transparent;
  color: var(--primary-color);
  font-size: 0.85rem;
  cursor: pointer;
}

.btn-change:hover {
  background-color: var(--primary-light);
}

.icon-right {
  font-size: 0.9rem;
  color: var(--text-light);
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
  background-color: var(--card-bg);
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
  padding: 0 20px 24px;
}

.sheet-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.sheet-icon {
  font-size: 1.4rem;
  color: var(--danger-color);
  margin-right: 12px;
}

.sheet-header h3 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-color);
}

.sheet-message {
  margin: 0 0 24px;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text-light);
}

.sheet-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn {
  width: 100%;
  padding: 12px;
  border-radius: var(--border-radius);
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.btn:active {
  transform: scale(0.98);
}

.btn .icon-left {
  margin-right: 8px;
}

.btn-danger {
  background-color: var(--danger-color);
  border: none;
  color: white;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-outline-secondary {
  background-color: transparent;
  border: 1.5px solid var(--border-color);
  color: var(--text-color);
}

/* Logout Animation Styles */
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
  padding: 0 32px;
}

.logout-icon {
  font-size: 3rem;
  color: var(--primary-color);
  margin-bottom: 16px;
  opacity: 0;
}

.logout-message {
  font-size: 1.1rem;
  color: var(--text-color);
  text-align: center;
  margin-bottom: 24px;
  opacity: 0;
}

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
  background-color: var(--primary-color);
  transform: translate(-50%, -50%) rotate(calc(var(--i) * 30deg)) translateY(-24px);
  transform-origin: center;
  opacity: calc(1 - (var(--i) * 0.08));
}

/* Bottom Sheet Transitions */
.sheet-slide-enter-active,
.sheet-slide-leave-active {
  transition: opacity 0.3s ease;
}

.sheet-slide-enter-from,
.sheet-slide-leave-to {
  opacity: 0;
}

/* Vibration Feedback */
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