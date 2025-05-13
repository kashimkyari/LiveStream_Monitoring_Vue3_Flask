// src/composables/useSettings.js
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

export function useSettings(defaultSettings = { emailNotifications: true, pushNotifications: false }) {
  const toast = useToast()
  
  // Telegram state
  const telegramConnected = ref(false)
  const telegramUsername = ref('')
  const telegramChatId = ref('')
  const showTelegramModal = ref(false)
  
  // Settings state
  const settings = ref({ ...defaultSettings })
  const isLoggingOut = ref(false)
  const showLogoutConfirmation = ref(false)
  
  // Fetch settings on mount
  onMounted(async () => {
    try {
      const response = await axios.get('/api/user/telegram', { withCredentials: true })
      telegramConnected.value = !!(response.data.telegram_username && response.data.chat_id)
      telegramUsername.value = response.data.telegram_username || ''
      telegramChatId.value = response.data.chat_id || ''
      settings.value.pushNotifications = response.data.receive_updates || false
    } catch (error) {
      console.error('Error loading settings:', error)
      toast.error('Failed to load settings')
    }
  })

  // Save settings to backend
  const saveSettings = async () => {
    try {
      const response = await axios.post('/api/user/telegram', {
        telegram_username: telegramUsername.value,
        chat_id: telegramChatId.value,
        receive_updates: settings.value.pushNotifications
      }, { withCredentials: true })
      toast.success(response.data.message || 'Settings saved')
    } catch (error) {
      console.error('Error saving settings:', error)
      toast.error('Failed to save settings')
    }
  }

  // Notification toggles
  const toggleEmailNotifications = () => {
    settings.value.emailNotifications = !settings.value.emailNotifications
    saveSettings()
  }

  const togglePushNotifications = () => {
    if (!settings.value.pushNotifications && !telegramConnected.value) {
      // Show modal to connect Telegram when enabling push notifications
      showTelegramModal.value = true
    } else {
      // Toggle push notifications and save
      settings.value.pushNotifications = !settings.value.pushNotifications
      saveSettings()
    }
  }

  // Handle Telegram connection
  const handleTelegramConnected = ({ username, chatId }) => {
    telegramConnected.value = true
    telegramUsername.value = username
    telegramChatId.value = chatId
    settings.value.pushNotifications = true // Enable push notifications on successful connection
    showTelegramModal.value = false
    saveSettings()
  }

  // Logout handler
  const handleLogout = async (playAnimation) => {
    try {
      isLoggingOut.value = true
      showLogoutConfirmation.value = false
      const response = await axios.post('/api/logout', {}, { withCredentials: true })
      if (response.status === 200) {
        playAnimation()
      }
    } catch (error) {
      console.error('Logout failed:', error)
      toast.error('Failed to log out')
      isLoggingOut.value = false
    }
  }

  return {
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
  }
}