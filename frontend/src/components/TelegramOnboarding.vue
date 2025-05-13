<!-- src/components/TelegramOnboarding.vue -->
<template>
    <div class="telegram-onboarding" v-if="isVisible" @click.stop>
      <div class="modal-overlay" @click.self="resetAndClose">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3>{{ editing ? 'Update Telegram Settings' : 'Setup Telegram Notifications' }}</h3>
            <button class="close-btn" @click="resetAndClose">
              <font-awesome-icon icon="times" />
            </button>
          </div>
  
          <div class="modal-body">
            <div class="step" v-if="step === 1">
              <h4>Step 1: Connect to Our Telegram Bot</h4>
              <p>
                Scan the QR code or click the link to start a chat with our bot:
                <a :href="botLink" target="_blank">@JetCamStudioBot</a>
              </p>
              <div class="qr-code">
                <img :src="qrCodeUrl" alt="Telegram Bot QR Code" />
              </div>
              <button class="btn btn-primary" @click="step = 2">
                Next
              </button>
            </div>
  
            <div class="step" v-if="step === 2">
              <h4>Step 2: Enter Your Telegram Details</h4>
              <div class="form-group">
                <label for="telegramUsername">Telegram Username</label>
                <input
                  id="telegramUsername"
                  v-model="telegramUsername"
                  placeholder="e.g., @YourUsername"
                  @input="usernameTouched = true; validateUsername()"
                  :class="{ 'input-error': usernameError }"
                />
                <span class="error-message" v-if="usernameError">{{ usernameError }}</span>
              </div>
              <div class="form-group">
                <label for="telegramChatId">Chat ID</label>
                <input
                  id="telegramChatId"
                  v-model="telegramChatId"
                  placeholder="e.g., 123456789"
                  @input="chatIdTouched = true; validateChatId()"
                  :class="{ 'input-error': chatIdError }"
                />
                <span class="error-message" v-if="chatIdError">{{ chatIdError }}</span>
              </div>
              <p class="info-text">
                To get your Chat ID, send /start to the bot and then /getid.
              </p>
              <div class="button-group">
                <button class="btn btn-outline" @click="step = 1">Back</button>
                <button
                  class="btn btn-primary"
                  @click="saveTelegramDetails"
                >
                  <font-awesome-icon v-if="isSaving" icon="spinner" spin />
                  {{ isSaving ? 'Saving...' : 'Save' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted, defineEmits, defineProps, watch } from 'vue'
  import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
  import axios from 'axios'
  import { useToast } from 'vue-toastification'
  import QRCode from 'qrcode'
  
  const props = defineProps({
    isVisible: {
      type: Boolean,
      default: false
    },
    existingUsername: {
      type: String,
      default: ''
    },
    existingChatId: {
      type: String,
      default: ''
    }
  })
  
  const emit = defineEmits(['close', 'telegram-connected'])
  
  const toast = useToast()
  const step = ref(1)
  const telegramUsername = ref('')
  const telegramChatId = ref('')
  const usernameError = ref('')
  const chatIdError = ref('')
  const usernameTouched = ref(false)
  const chatIdTouched = ref(false)
  const isSaving = ref(false)
  const botLink = 'https://t.me/JetCamStudioBot'
  const qrCodeUrl = ref('')
  
  onMounted(async () => {
    try {
      qrCodeUrl.value = await QRCode.toDataURL(botLink, {
        width: 150,
        margin: 1
      })
    } catch (error) {
      console.error('Error generating QR code:', error)
      toast.error('Failed to generate QR code')
    }
  })
  
  watch(() => props.isVisible, (newVal) => {
    if (newVal) {
      telegramUsername.value = props.existingUsername || ''
      telegramChatId.value = props.existingChatId || ''
      step.value = props.existingUsername || props.existingChatId ? 2 : 1
      usernameTouched.value = false
      chatIdTouched.value = false
      validateUsername()
      validateChatId()
    }
  })
  
  const validateUsername = () => {
    if (!usernameTouched.value) {
      usernameError.value = ''
      return
    }
    if (!telegramUsername.value) {
      usernameError.value = 'Username is required'
    } else if (!telegramUsername.value.startsWith('@')) {
      usernameError.value = 'Username must start with @'
    } else if (telegramUsername.value.length < 5) {
      usernameError.value = 'Username must be at least 5 characters'
    } else {
      usernameError.value = ''
    }
  }
  
  const validateChatId = () => {
    if (!chatIdTouched.value) {
      chatIdError.value = ''
      return
    }
    if (!telegramChatId.value) {
      chatIdError.value = 'Chat ID is required'
    } else if (!/^\d+$/.test(telegramChatId.value)) {
      chatIdError.value = 'Chat ID must be numeric'
    } else {
      chatIdError.value = ''
    }
  }
  
  const saveTelegramDetails = async () => {
    if (usernameError.value || chatIdError.value) return
  
    isSaving.value = true
    try {
      const response = await axios.post('/api/user/telegram', {
        telegram_username: telegramUsername.value,
        chat_id: telegramChatId.value,
        receive_updates: true // Enable push notifications
      }, {
        withCredentials: true
      })
  
      toast.success(response.data.message || 'Telegram settings saved')
      emit('telegram-connected', {
        username: telegramUsername.value,
        chatId: telegramChatId.value
      })
      emit('close')
    } catch (error) {
      const msg = error.response?.data.message || 'Error saving Telegram settings'
      toast.error(msg)
    } finally {
      isSaving.value = false
    }
  }
  
  const resetAndClose = () => {
    telegramUsername.value = props.existingUsername || ''
    telegramChatId.value = props.existingChatId || ''
    step.value = 1
    usernameError.value = ''
    chatIdError.value = ''
    usernameTouched.value = false
    chatIdTouched.value = false
    emit('close')
  }
  
  const editing = computed(() => !!props.existingUsername || !!props.existingChatId)
  </script>
  
  
  <style scoped>
  .telegram-onboarding {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
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
    backdrop-filter: blur(4px);
  }
  
  .modal-container {
    background-color: var(--input-bg);
    border-radius: 12px;
    width: 100%;
    max-width: 500px;
    padding: 1.5rem;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .modal-header h3 {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--text-color);
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 1.2rem;
    color: var(--text-secondary);
    cursor: pointer;
  }
  
  .close-btn:hover {
    color: var(--text-color);
  }
  
  .modal-body {
    padding: 1rem 0;
  }
  
  .step {
    text-align: center;
  }
  
  .step h4 {
    font-size: 1.2rem;
    margin-bottom: 1rem;
    color: var(--primary-color);
  }
  
  .step p {
    font-size: 1rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
  }
  
  .qr-code {
    margin: 1rem auto;
    max-width: 150px;
  }
  
  .qr-code img {
    width: 100%;
    border-radius: 8px;
  }
  
  .form-group {
    margin-bottom: 1.5rem;
    text-align: left;
  }
  
  .form-group label {
    display: block;
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
    color: var(--text-color);
  }
  
  .form-group input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    font-size: 1rem;
    background-color: var(--hover-bg);
    color: var(--text-color);
    transition: border-color 0.3s ease;
  }
  
  .form-group input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.2);
  }
  
  .input-error {
    border-color: var(--danger-color) !important;
  }
  
  .error-message {
    color: var(--danger-color);
    font-size: 0.8rem;
    margin-top: 0.25rem;
    display: block;
  }
  
  .info-text {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
  }
  
  .button-group {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
  }
  
  .btn {
    padding: 0.8rem 1.5rem;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
  
  .btn-primary {
    background-color: var(--primary-color);
    color: white;
    border: none;
  }
  
  .btn-outline {
    background-color: transparent;
    border: 2px solid var(--border-color);
    color: var(--text-color);
  }
  
  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  </style>