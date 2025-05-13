<template>
  <div class="admin-settings-container" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="settings-sidebar">
      <h3 class="sidebar-title">Settings</h3>
      <ul class="settings-menu">
        <li class="menu-item active">
          <font-awesome-icon icon="cog" class="menu-icon" />
          <span>General Settings</span>
        </li>
      </ul>
    </div>

    <main class="settings-content">
      <div class="settings-header">
        <h2>General Settings</h2>
      </div>

      <div class="settings-body">
        <section class="settings-section">
          <h3>Notifications</h3>
          <div class="settings-options">
            <div class="option">
              <span>Email Notifications</span>
              <div 
                class="toggle-switch" 
                :class="{ active: settings.emailNotifications }" 
                @click="toggleEmailNotifications"
              >
                <div class="toggle-handle"></div>
              </div>
            </div>

            <div class="option">
              <span>Push Notifications</span>
              <div 
                class="toggle-switch" 
                :class="{ active: settings.pushNotifications }" 
                @click="togglePushNotifications"
              >
                <div class="toggle-handle"></div>
              </div>
            </div>

            <div class="telegram-status" v-if="settings.pushNotifications">
              <div v-if="telegramConnected" class="status-connected">
                <font-awesome-icon :icon="['fab', 'telegram']" class="telegram-icon" />
                <div class="status-details">
                  <span>Connected to Telegram</span>
                  <span>@{{ telegramUsername }}</span>
                </div>
                <button class="btn-outline" @click="showTelegramModal = true">Change</button>
              </div>
              <div v-else class="status-disconnected" @click="showTelegramModal = true">
                <font-awesome-icon :icon="['fab', 'telegram']" class="telegram-icon" />
                <span>Connect to Telegram</span>
              </div>
            </div>
          </div>
        </section>

        <section class="settings-section">
          <h3>Appearance</h3>
          <div class="theme-options">
            <div 
              class="theme-option" 
              :class="{ selected: isDarkTheme }" 
              @click="$emit('set-theme', true)"
            >
              <font-awesome-icon icon="moon" class="theme-icon" />
              <span>Dark Mode</span>
            </div>
            <div 
              class="theme-option" 
              :class="{ selected: !isDarkTheme }" 
              @click="$emit('set-theme', false)"
            >
              <font-awesome-icon icon="sun" class="theme-icon" />
              <span>Light Mode</span>
            </div>
          </div>
        </section>

        <div class="action-buttons">
          <button class="btn-primary" @click="saveSettings">
            <font-awesome-icon icon="save" class="icon-left" /> Save Changes
         -Y</button>
          <button 
            class="btn-danger" 
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
      </div>
    </main>

    <transition name="modal-fade">
      <div v-if="showLogoutConfirmation" class="modal-overlay" @click="showLogoutConfirmation = false">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <font-awesome-icon icon="sign-out-alt" class="modal-icon" />
            <h3>Confirm Logout</h3>
            <button class="close-btn" @click="showLogoutConfirmation = false">
              <font-awesome-icon icon="times" />
            </button>
          </div>
          <p>Are you sure you want to log out?</p>
          <div class="modal-actions">
            <button class="btn-danger" @click="handleLogout(playLogoutAnimation)" :disabled="isLoggingOut">
              <font-awesome-icon 
                :icon="isLoggingOut ? 'spinner' : 'sign-out-alt'" 
                :spin="isLoggingOut" 
                class="icon-left"
              />
              {{ isLoggingOut ? 'Logging out...' : 'Logout' }}
            </button>
            <button class="btn-outline" @click="showLogoutConfirmation = false">Cancel</button>
          </div>
        </div>
      </div>
    </transition>

    <div v-if="showLogoutAnimation" class="logout-animation-overlay">
      <div class="logout-animation-container" ref="logoutAnimationContainer">
        <font-awesome-icon icon="sign-out-alt" class="logout-icon" ref="logoutIcon" />
        <div class="logout-message" ref="logoutMessage">Logging out...</div>
        <div class="logout-spinner" ref="logoutSpinner">
          <div class="spinner-circle" v-for="n in 12" :key="n" :style="`--i: ${n}`"></div>
        </div>
      </div>
    </div>

    <TelegramOnboarding
      :is-visible="showTelegramModal"
      :existing-username="telegramUsername"
      :existing-chat-id="telegramChatId"
      @close="showTelegramModal = false"
      @telegram-connected="handleTelegramConnected"
    />
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, nextTick } from 'vue'
import anime from 'animejs/lib/anime.es.js'
import TelegramOnboarding from './TelegramOnboarding.vue'
import { useSettings } from '../composables/useSettings'

defineProps({
  isDarkTheme: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['fetch-settings', 'set-theme', 'logout'])

const {
  settings,
  telegramConnected,
  telegramUsername,
  telegramChatId,
  showTelegramModal,
  isLoggingOut,
  showLogoutConfirmation,
  toggleEmailNotifications,
  togglePushNotifications,
  handleTelegramConnected,
  handleLogout,
  saveSettings
} = useSettings()

// Logout animation
const showLogoutAnimation = ref(false)
const logoutAnimationContainer = ref(null)
const logoutIcon = ref(null)
const logoutMessage = ref(null)
const logoutSpinner = ref(null)

const playLogoutAnimation = () => {
  showLogoutAnimation.value = true
  
  nextTick(() => {
    if (logoutAnimationContainer.value) {
      anime({
        targets: logoutAnimationContainer.value,
        opacity: [0, 1],
        scale: [0.8, 1],
        duration: 600,
        easing: 'easeOutCubic'
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
        translateY: [20, 0],
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
    
    setTimeout(() => {
      completeLogout()
    }, 2000)
  })
}

const completeLogout = () => {
  anime({
    targets: logoutAnimationContainer.value,
    opacity: 0,
    scale: 0.8,
    duration: 400,
    easing: 'easeInQuad',
    complete: () => {
      showLogoutAnimation.value = false
      emit('logout')
      localStorage.removeItem('userSettings')
      window.location.href = '/dashboard'
    }
  })
}
</script>


<style scoped>
@import '../styles/shared.css';
.admin-settings-container {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-color);
  color: var(--text-color);
}

.settings-sidebar {
  width: 250px;
  background-color: var(--sidebar-bg);
  padding: 1.5rem;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
}

.sidebar-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1.5rem;
}

.settings-menu {
  list-style: none;
  padding: 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.menu-item.active {
  background-color: var(--primary-color);
  color: white;
}

.menu-icon {
  margin-right: 0.75rem;
}

.settings-content {
  flex: 1;
  padding: 2rem;
}

.settings-header {
  margin-bottom: 2rem;
}

.settings-body {
  background-color: var(--content-bg);
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.settings-section {
  margin-bottom: 2rem;
}

.settings-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toggle-switch {
  width: 50px;
  height: 26px;
  background-color: var(--toggle-bg);
  border-radius: 26px;
  position: relative;
  cursor: pointer;
  transition: background-color 0.3s;
}

.toggle-switch.active {
  background-color: var(--primary-color);
}

.toggle-handle {
  width: 22px;
  height: 22px;
  background-color: white;
  border-radius: 50%;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.3s;
}

.toggle-switch.active .toggle-handle {
  transform: translateX(24px);
}

.theme-options {
  display: flex;
  gap: 1rem;
}

.theme-option {
  flex: 1;
  padding: 1rem;
  text-align: center;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.theme-option.selected {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-dark);
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-danger {
  background-color: var(--danger-color);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-outline {
  background-color: transparent;
  border: 2px solid var(--border-color);
  color: var(--text-color);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-container {
  background-color: var(--content-bg);
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.modal-icon {
  font-size: 1.5rem;
  color: var(--danger-color);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
</style>