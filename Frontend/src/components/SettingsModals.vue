<template>
  <teleport to="body">
    <!-- Backdrop -->
    <div v-if="showAnyModal" class="modal-backdrop" @click="closeAllModals" ref="backdropRef"></div>

    <!-- Add Keyword Modal -->
    <div v-if="showKeywordModal" class="modal-container" ref="keywordModalRef">
      <div class="modal-header">
        <button class="back-button" @click="closeKeywordModal">
          <font-awesome-icon :icon="['fas', 'arrow-left']" />
        </button>
        <h2>Add Keyword</h2>
        <button class="close-button" @click="closeKeywordModal">
          <font-awesome-icon :icon="['fas', 'times']" />
        </button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label for="keyword">Keyword</label>
          <input
            type="text"
            id="keyword"
            v-model="newKeyword"
            placeholder="Enter keyword to flag"
            @keyup.enter="addKeyword"
            ref="keywordInputRef"
          />
        </div>
      </div>
      <div class="modal-footer">
        <button class="cancel-button" @click="closeKeywordModal">Cancel</button>
        <button 
          class="submit-button" 
          @click="addKeyword" 
          :disabled="!newKeyword.trim()"
        >
          Add Keyword
        </button>
      </div>
    </div>

    <!-- Add Object Modal -->
    <div v-if="showObjectModal" class="modal-container" ref="objectModalRef">
      <div class="modal-header">
        <button class="back-button" @click="closeObjectModal">
          <font-awesome-icon :icon="['fas', 'arrow-left']" />
        </button>
        <h2>Add Object Detection</h2>
        <button class="close-button" @click="closeObjectModal">
          <font-awesome-icon :icon="['fas', 'times']" />
        </button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label for="object">Object Name</label>
          <input
            type="text"
            id="object"
            v-model="newObject"
            placeholder="Enter object to detect"
            @keyup.enter="addObject"
            ref="objectInputRef"
          />
        </div>
      </div>
      <div class="modal-footer">
        <button class="cancel-button" @click="closeObjectModal">Cancel</button>
        <button 
          class="submit-button" 
          @click="addObject" 
          :disabled="!newObject.trim()"
        >
          Add Object
        </button>
      </div>
    </div>

    <!-- Add Telegram Recipient Modal -->
    <div v-if="showTelegramModal" class="modal-container" ref="telegramModalRef">
      <div class="modal-header">
        <button class="back-button" @click="closeTelegramModal">
          <font-awesome-icon :icon="['fas', 'arrow-left']" />
        </button>
        <h2>Add Telegram Recipient</h2>
        <button class="close-button" @click="closeTelegramModal">
          <font-awesome-icon :icon="['fas', 'times']" />
        </button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label for="username">Telegram Username</label>
          <input
            type="text"
            id="username"
            v-model="newTelegramUsername"
            placeholder="Enter telegram username"
            ref="usernameInputRef"
          />
        </div>
        <div class="form-group">
          <label for="chatId">Chat ID</label>
          <input
            type="text"
            id="chatId"
            v-model="newTelegramChatId"
            placeholder="Enter chat ID"
            @keyup.enter="addTelegramRecipient"
          />
        </div>
      </div>
      <div class="modal-footer">
        <button class="cancel-button" @click="closeTelegramModal">Cancel</button>
        <button 
          class="submit-button" 
          @click="addTelegramRecipient" 
          :disabled="!newTelegramUsername.trim() || !newTelegramChatId.trim()"
        >
          Add Recipient
        </button>
      </div>
    </div>
  </teleport>
</template>

<script>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import axios from 'axios'
import anime from 'animejs/lib/anime.es.js'
import { library } from '@fortawesome/fontawesome-svg-core'
import { faTimes, faArrowLeft } from '@fortawesome/free-solid-svg-icons'

library.add(faTimes, faArrowLeft)

export default {
  name: 'SettingsModals',
  components: {
    FontAwesomeIcon
  },
  emits: ['notification', 'update:keywords', 'update:objects', 'update:telegramRecipients', 'modal-closed'],
  props: {
    triggerPositions: {
      type: Object,
      default: () => ({})
    },
    isMobile: {
      type: Boolean,
      default: false
    },
    darkMode: {  // Add dark mode prop
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    // Modal visibility states
    const showKeywordModal = ref(false)
    const showObjectModal = ref(false)
    const showTelegramModal = ref(false)

    // Form data
    const newKeyword = ref('')
    const newObject = ref('')
    const newTelegramUsername = ref('')
    const newTelegramChatId = ref('')

    // Refs for animation targets
    const backdropRef = ref(null)
    const keywordModalRef = ref(null)
    const objectModalRef = ref(null)
    const telegramModalRef = ref(null)
    const keywordInputRef = ref(null)
    const objectInputRef = ref(null)
    const usernameInputRef = ref(null)

    // Store positions of trigger elements
    const triggerElements = ref({
      keyword: null,
      object: null,
      telegram: null
    })

    // Computed property to check if any modal is open
    const showAnyModal = computed(() => 
      showKeywordModal.value || showObjectModal.value || showTelegramModal.value
    )

    // Apply theme class to modals when theme changes
    watch(() => props.darkMode, (isDark) => {
  nextTick(() => {
    const modals = [keywordModalRef.value, objectModalRef.value, telegramModalRef.value]
    modals.forEach(modal => {
      if (modal) {
        if (isDark) {
          modal.classList.add('dark-theme')
          modal.classList.remove('light-theme')
        } else {
          modal.classList.add('light-theme')
          modal.classList.remove('dark-theme')
        }
      }
    })
  })
}, { immediate: true })
    // Animation functions
    const animateModalOpen = (modalRef, triggerPosition) => {
      if (!modalRef.value) return
      
      anime.remove([backdropRef.value, modalRef.value])
      
      // Position the modal
      positionModal(modalRef.value, triggerPosition)
      
      // Apply theme class
      if (props.darkMode) {
        modalRef.value.classList.add('dark-theme')
        modalRef.value.classList.remove('light-theme')
      } else {
        modalRef.value.classList.add('light-theme')
        modalRef.value.classList.remove('dark-theme')
      }
      
      // Animate backdrop
      anime({
        targets: backdropRef.value,
        opacity: [0, 0.5],
        duration: 300,
        easing: 'easeOutQuad'
      })
      
      // Animate modal
      anime({
        targets: modalRef.value,
        opacity: [0, 1],
        scale: [0.9, 1],
        duration: 400,
        easing: 'easeOutExpo'
      })
    }

    const animateModalClose = (modalRef, onComplete) => {
      if (!modalRef.value) {
        if (onComplete) onComplete()
        return
      }
      
      anime.remove([backdropRef.value, modalRef.value])
      
      // Animate backdrop
      anime({
        targets: backdropRef.value,
        opacity: 0,
        duration: 300,
        easing: 'easeOutQuad'
      })
      
      // Animate modal
      anime({
        targets: modalRef.value,
        opacity: 0,
        scale: 0.9,
        duration: 300,
        easing: 'easeInQuad',
        complete: onComplete
      })
    }
    
    // Helper function to position modal
    const positionModal = (modalElement, triggerPosition) => {
      if (!modalElement || !triggerPosition) return
      
      if (props.isMobile) {
        // For mobile devices, center on screen
        modalElement.style.top = '50%'
        modalElement.style.left = '50%'
        modalElement.style.transform = 'translate(-50%, -50%)'
      } else {
        // For desktop, position relative to trigger
        const viewportHeight = window.innerHeight
        const modalHeight = modalElement.offsetHeight || 300
        
        // Calculate vertical position
        let topPosition = triggerPosition.top
        
        // Ensure the modal stays in viewport
        if (topPosition + modalHeight > viewportHeight - 20) {
          topPosition = Math.max(20, viewportHeight - modalHeight - 20)
        }
        
        modalElement.style.top = `${topPosition}px`
        modalElement.style.left = `${triggerPosition.left + triggerPosition.width + 10}px`
        modalElement.style.transform = 'none'
      }
    }

    // Open modal functions with position info
    const openKeywordModal = (triggerEl) => {
      if (triggerEl) {
        triggerElements.value.keyword = triggerEl.getBoundingClientRect()
      }
      
      showKeywordModal.value = true
      nextTick(() => {
        animateModalOpen(keywordModalRef, triggerElements.value.keyword)
        if (keywordInputRef.value) keywordInputRef.value.focus()
      })
    }

    const openObjectModal = (triggerEl) => {
      if (triggerEl) {
        triggerElements.value.object = triggerEl.getBoundingClientRect()
      }
      
      showObjectModal.value = true
      nextTick(() => {
        animateModalOpen(objectModalRef, triggerElements.value.object)
        if (objectInputRef.value) objectInputRef.value.focus()
      })
    }

    const openTelegramModal = (triggerEl) => {
      if (triggerEl) {
        triggerElements.value.telegram = triggerEl.getBoundingClientRect()
      }
      
      showTelegramModal.value = true
      nextTick(() => {
        animateModalOpen(telegramModalRef, triggerElements.value.telegram)
        if (usernameInputRef.value) usernameInputRef.value.focus()
      })
    }

    // Close modal functions - now with emit to coordinate with parent
    const closeKeywordModal = () => {
      animateModalClose(keywordModalRef, () => {
        showKeywordModal.value = false
        newKeyword.value = ''
        emit('modal-closed')
      })
    }

    const closeObjectModal = () => {
      animateModalClose(objectModalRef, () => {
        showObjectModal.value = false
        newObject.value = ''
        emit('modal-closed')
      })
    }

    const closeTelegramModal = () => {
      animateModalClose(telegramModalRef, () => {
        showTelegramModal.value = false
        newTelegramUsername.value = ''
        newTelegramChatId.value = ''
        emit('modal-closed')
      })
    }

    const closeAllModals = (event) => {
      if (event.target === backdropRef.value) {
        if (showKeywordModal.value) closeKeywordModal()
        if (showObjectModal.value) closeObjectModal()
        if (showTelegramModal.value) closeTelegramModal()
      }
    }

    // Submit functions
    const addKeyword = async () => {
      if (!newKeyword.value.trim()) return
      
      try {
        const res = await axios.post('/api/keywords', { keyword: newKeyword.value.trim() })
        emit('notification', res.data.message || 'Keyword added successfully', 'success')
        emit('update:keywords')
        closeKeywordModal()
      } catch (error) {
        const msg = error.response?.data.message || 'Error adding keyword'
        emit('notification', msg, 'error')
        
        // If keyword already exists, still close modal
        if (error.response?.status === 400 && 
            msg.toLowerCase().includes('exists')) {
          closeKeywordModal()
        }
      }
    }

    const addObject = async () => {
      if (!newObject.value.trim()) return
      
      try {
        const res = await axios.post('/api/objects', { object_name: newObject.value.trim() })
        emit('notification', res.data.message || 'Object added successfully', 'success')
        emit('update:objects')
        closeObjectModal()
      } catch (error) {
        const msg = error.response?.data.message || 'Error adding object'
        emit('notification', msg, 'error')
        
        // If object already exists, still close modal
        if (error.response?.status === 400 && 
            msg.toLowerCase().includes('exists')) {
          closeObjectModal()
        }
      }
    }

    const addTelegramRecipient = async () => {
      if (!newTelegramUsername.value.trim() || !newTelegramChatId.value.trim()) return
      
      try {
        const res = await axios.post('/api/telegram_recipients', {
          telegram_username: newTelegramUsername.value.trim(),
          chat_id: newTelegramChatId.value.trim()
        })
        emit('notification', res.data.message || 'Recipient added successfully', 'success')
        emit('update:telegramRecipients')
        closeTelegramModal()
      } catch (error) {
        const msg = error.response?.data.message || 'Error adding recipient'
        emit('notification', msg, 'error')
        
        // If recipient already exists, still close modal
        if (error.response?.status === 400 && 
            msg.toLowerCase().includes('exists')) {
          closeTelegramModal()
        }
      }
    }

    // Watch for prop changes to update positioning
    onMounted(() => {
      window.addEventListener('resize', () => {
        if (showKeywordModal.value) {
          positionModal(keywordModalRef.value, triggerElements.value.keyword)
        } else if (showObjectModal.value) {
          positionModal(objectModalRef.value, triggerElements.value.object)
        } else if (showTelegramModal.value) {
          positionModal(telegramModalRef.value, triggerElements.value.telegram)
        }
      })
    })

    // Expose functions and variables to be used outside
    return {
      // Modal visibility
      showKeywordModal,
      showObjectModal,
      showTelegramModal,
      showAnyModal,
      
      // Form data
      newKeyword,
      newObject,
      newTelegramUsername,
      newTelegramChatId,
      
      // Refs
      backdropRef,
      keywordModalRef,
      objectModalRef,
      telegramModalRef,
      keywordInputRef,
      objectInputRef,
      usernameInputRef,
      
      // Modal controls
      openKeywordModal,
      openObjectModal,
      openTelegramModal,
      closeKeywordModal,
      closeObjectModal,
      closeTelegramModal,
      closeAllModals,
      
      // Submit functions
      addKeyword,
      addObject,
      addTelegramRecipient
    }
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1500;
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
}

.modal-container {
  position: fixed;
  max-width: 95%;
  width: 480px;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  z-index: 1600;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  opacity: 0;
}

/* Light theme styles */
.modal-container.light-theme {
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  color: #333333;
}

.light-theme .modal-header {
  border-bottom: 1px solid #e0e0e0;
}

.light-theme .modal-header h2 {
  color: #333333;
}

.light-theme .back-button,
.light-theme .close-button {
  color: #555555;
}

.light-theme .back-button:hover,
.light-theme .close-button:hover {
  background-color: #f0f0f0;
}

.light-theme .form-group label {
  color: #555555;
}

.light-theme .form-group input {
  border: 1px solid #e0e0e0;
  background-color: #f7f7f7;
  color: #333333;
}

.light-theme .form-group input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.2);
}

.light-theme .modal-footer {
  border-top: 1px solid #e0e0e0;
}

.light-theme .cancel-button {
  color: #555555;
  border: 1px solid #e0e0e0;
}

.light-theme .cancel-button:hover {
  background-color: #f0f0f0;
}

.light-theme .submit-button {
  background-color: #007bff;
  color: white;
}

/* Dark theme styles */
.modal-container.dark-theme {
  background-color: #1e1e1e;
  border: 1px solid #333333;
  color: #f0f0f0;
}

.dark-theme .modal-header {
  border-bottom: 1px solid #333333;
}

.dark-theme .modal-header h2 {
  color: #f0f0f0;
}

.dark-theme .back-button,
.dark-theme .close-button {
  color: #cccccc;
}

.dark-theme .back-button:hover,
.dark-theme .close-button:hover {
  background-color: #333333;
}

.dark-theme .form-group label {
  color: #cccccc;
}

.dark-theme .form-group input {
  border: 1px solid #444444;
  background-color: #2d2d2d;
  color: #f0f0f0;
}

.dark-theme .form-group input:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25);
}

.dark-theme .modal-footer {
  border-top: 1px solid #333333;
}

.dark-theme .cancel-button {
  color: #cccccc;
  border: 1px solid #444444;
}

.dark-theme .cancel-button:hover {
  background-color: #333333;
}

.dark-theme .submit-button {
  background-color: #0d6efd;
  color: white;
}

.modal-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  flex: 1;
  text-align: center;
}

.back-button, .close-button {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.modal-body {
  padding: 20px;
  flex: 1;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.form-group input:focus {
  outline: none;
}

.modal-footer {
  padding: 16px 20px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-button {
  padding: 10px 16px;
  background-color: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.submit-button {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: transform 0.2s, opacity 0.2s;
}

.submit-button:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 768px) {
  .modal-container {
    width: 90%;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
  }
  
  .modal-header h2 {
    font-size: 1.1rem;
  }
  
  .form-group input {
    padding: 10px;
  }
  
  .cancel-button, .submit-button {
    padding: 8px 12px;
    font-size: 0.9rem;
  }
}
</style>