<template>
  <div>
    <!-- Overlay for the modal -->
    <transition name="fade">
      <div v-if="isVisible" class="modal-overlay" @click="closeOnOverlayClick ? closeModal() : null">
        <!-- Modal container with animation -->
        <div class="modal-container" @click.stop ref="modalRef">
          <div class="modal-handle"></div>
          
          <div class="modal-content">
            <div class="modal-header">
              <div class="telegram-icon">
                <font-awesome-icon :icon="['fab', 'telegram']" />
              </div>
              <h3>Connect Telegram</h3>
              <button class="close-button" @click="closeModal">
                <font-awesome-icon icon="times" />
              </button>
            </div>
            
            <div class="modal-body">
              <p class="modal-description">
                Link your Telegram account to receive push notifications directly to your device.
              </p>
              
              <div class="setup-instructions" v-if="!isSubmitting">
                <div class="instruction-step">
                  <div class="step-number">1</div>
                  <div class="step-text">
                    Start a chat with <span class="bot-name">@chatidfindbot</span> on Telegram
                  </div>
                </div>
                
                <div class="instruction-step">
                  <div class="step-number">2</div>
                  <div class="step-text">
                    Send the command <span class="command">/me</span> to receive your Chat ID
                  </div>
                </div>
                
                <div class="instruction-step">
                  <div class="step-number">3</div>
                  <div class="step-text">
                    Enter your Telegram username and Chat ID below
                  </div>
                </div>
              </div>
              
              <form @submit.prevent="submitForm" class="telegram-form">
                <div class="form-field">
                  <label for="telegram-username">Telegram Username</label>
                  <div class="input-wrapper">
                    <span class="input-prefix">@</span>
                    <input 
                      id="telegram-username" 
                      v-model="telegramUsername" 
                      type="text" 
                      placeholder="username"
                      :disabled="isSubmitting"
                    />
                  </div>
                  <div v-if="errors.username" class="error-message">{{ errors.username }}</div>
                </div>
                
                <div class="form-field">
                  <label for="chat-id">Chat ID</label>
                  <input 
                    id="chat-id" 
                    v-model="chatId" 
                    type="text" 
                    placeholder="Your Chat ID from the bot"
                    :disabled="isSubmitting"
                  />
                  <div v-if="errors.chatId" class="error-message">{{ errors.chatId }}</div>
                </div>
                
                <div v-if="errorMessage" class="server-error">{{ errorMessage }}</div>
                
                <div class="form-actions">
                  <button 
                    type="button" 
                    class="btn btn-outline" 
                    @click="closeModal"
                    :disabled="isSubmitting"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    class="btn btn-primary" 
                    :disabled="isSubmitting"
                  >
                    <template v-if="isSubmitting">
                      <font-awesome-icon icon="spinner" spin class="icon-left" />
                      Connecting...
                    </template>
                    <template v-else>
                      <font-awesome-icon icon="link" class="icon-left" />
                      Connect
                    </template>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- Success Animation Overlay -->
    <div v-if="showSuccessAnimation" class="success-animation-overlay">
      <div class="success-animation-container" ref="successAnimationContainer">
        <div class="success-icon" ref="successIcon">
          <font-awesome-icon icon="check-circle" />
        </div>
        <div class="success-message" ref="successMessage">
          Telegram Connected Successfully!
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, defineEmits, defineProps } from 'vue'
import axios from 'axios'
import anime from 'animejs/lib/anime.es.js'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  closeOnOverlayClick: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['close', 'telegram-connected'])

// Form data
const telegramUsername = ref('')
const chatId = ref('')
const errors = ref({})
const errorMessage = ref('')
const isSubmitting = ref(false)
const modalRef = ref(null)

// Success animation state
const showSuccessAnimation = ref(false)
const successAnimationContainer = ref(null)
const successIcon = ref(null)
const successMessage = ref(null)

// Validate the form
const validateForm = () => {
  errors.value = {}
  let isValid = true
  
  if (!telegramUsername.value.trim()) {
    errors.value.username = 'Telegram username is required'
    isValid = false
  }
  
  if (!chatId.value.trim()) {
    errors.value.chatId = 'Chat ID is required'
    isValid = false
  } else if (!/^-?\d+$/.test(chatId.value.trim())) {
    errors.value.chatId = 'Chat ID must be a valid number'
    isValid = false
  }
  
  return isValid
}

// Submit form handler
const submitForm = async () => {
  if (!validateForm()) return
  
  isSubmitting.value = true
  errorMessage.value = ''
  
  try {
    // Remove @ if user included it
    const username = telegramUsername.value.trim().replace(/^@/, '')
    
   const response = await axios.post(
     '/api/telegram_recipients',
     {
       telegram_username: username,
       chat_id: chatId.value.trim()
     },
     {
       withCredentials: true // Critical: Ensures cookies (session, auth) are sent with the request
     }
   )

    
    if (response.status === 201) {
      isSubmitting.value = false
      showSuccessAnimation.value = true
      playSuccessAnimation()
      
      // Emit event that telegram was connected successfully
      emit('telegram-connected', {
        username: username,
        chatId: chatId.value.trim()
      })
    }
  } catch (error) {
    isSubmitting.value = false
    let message = 'An error occurred while connecting your Telegram account'
    
    if (error.response) {
      if (error.response.status === 400) {
        message = error.response.data.message || 'This Telegram username may already be registered'
      }
    }
    
    errorMessage.value = message
  }
}

// Close modal handler
const closeModal = () => {
  emit('close')
}

// Play success animation
const playSuccessAnimation = () => {
  nextTick(() => {
    // Animate success container
    anime({
      targets: successAnimationContainer.value,
      opacity: [0, 1],
      duration: 400,
      easing: 'easeOutQuad'
    })
    
    // Animate success icon
    anime({
      targets: successIcon.value,
      scale: [0, 1],
      opacity: [0, 1],
      duration: 600,
      easing: 'easeOutBack'
    })
    
    // Animate success message
    anime({
      targets: successMessage.value,
      opacity: [0, 1],
      translateY: ['10px', '0px'],
      delay: 200,
      duration: 400,
      easing: 'easeOutQuad'
    })
    
    // After a delay, fade out and close modal
    setTimeout(() => {
      anime({
        targets: successAnimationContainer.value,
        opacity: 0,
        duration: 400,
        easing: 'easeInQuad',
        complete: () => {
          showSuccessAnimation.value = false
          closeModal()
        }
      })
    }, 2000)
  })
}

// Modal entrance animation
const animateModalIn = () => {
  nextTick(() => {
    anime({
      targets: modalRef.value,
      translateY: ['100%', '0%'],
      duration: 300,
      easing: 'easeOutCubic'
    })
  })
}

// Watch for visibility changes
watch(() => props.isVisible, (newValue) => {
  if (newValue) {
    // Reset form when opening
    telegramUsername.value = ''
    chatId.value = ''
    errors.value = {}
    errorMessage.value = ''
    isSubmitting.value = false
    
    // Animate modal in
    animateModalIn()
  }
})
</script>

<style scoped>
.modal-overlay {
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

.modal-container {
  width: 100%;
  background-color: var(--input-bg);
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
  overflow: hidden;
  transform: translateY(100%);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
}

.modal-handle {
  width: 40px;
  height: 4px;
  border-radius: 2px;
  background-color: var(--border-color);
  margin: 12px auto;
}

.modal-content {
  padding: 0 1.25rem 1.5rem;
}

.modal-header {
  display: flex;
  align-items: center;
  margin-bottom: 1.25rem;
  position: relative;
}

.telegram-icon {
  width: 40px;
  height: 40px;
  background-color: #0088cc;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.4rem;
  margin-right: 0.75rem;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-color);
}

.close-button {
  position: absolute;
  right: 0;
  top: 0;
  background: transparent;
  border: none;
  font-size: 1.2rem;
  color: var(--text-secondary);
  padding: 0.5rem;
  cursor: pointer;
}

.modal-description {
  margin: 0 0 1.25rem;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text-secondary);
}

.setup-instructions {
  background-color: var(--hover-bg);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1.25rem;
}

.instruction-step {
  display: flex;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.instruction-step:last-child {
  margin-bottom: 0;
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 600;
  margin-right: 0.75rem;
  flex-shrink: 0;
}

.step-text {
  font-size: 0.9rem;
  line-height: 1.4;
  padding-top: 0.2rem;
}

.bot-name, .command {
  font-weight: 600;
  background-color: rgba(0, 136, 204, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  color: #0088cc;
}

.telegram-form {
  margin-top: 1.5rem;
}

.form-field {
  margin-bottom: 1.25rem;
}

.form-field label {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

.input-wrapper {
  display: flex;
  align-items: center;
  position: relative;
}

.input-prefix {
  position: absolute;
  left: 12px;
  font-size: 0.95rem;
  color: var(--text-secondary);
}

input {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  border: 1.5px solid var(--border-color);
  background-color: var(--bg-color);
  font-size: 0.95rem;
  color: var(--text-color);
}

.input-wrapper input {
  padding-left: 28px;
}

input:focus {
  outline: none;
  border-color: var(--primary-color);
}

input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-message {
  color: var(--danger-color);
  font-size: 0.8rem;
  margin-top: 0.4rem;
}

.server-error {
  background-color: rgba(255, 0, 0, 0.1);
  color: var(--danger-color);
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
}

.btn {
  flex: 1;
  padding: 0.8rem;
  border-radius: 12px;
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
  margin-right: 0.5rem;
}

.btn-primary {
  background-color: var(--primary-color);
  border: none;
  color: white;
}

.btn-outline {
  background-color: transparent;
  border: 1.5px solid var(--border-color);
  color: var(--text-color);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Success Animation Styles */
.success-animation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1100;
}

.success-animation-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0;
}

.success-icon {
  font-size: 4rem;
  color: #4CAF50;
  margin-bottom: 1rem;
  opacity: 0;
}

.success-message {
  font-size: 1.2rem;
  color: white;
  font-weight: 500;
  opacity: 0;
}
</style>