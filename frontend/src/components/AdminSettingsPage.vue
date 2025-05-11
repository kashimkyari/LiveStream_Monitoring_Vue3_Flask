<template>
    <div class="settings-page" :data-theme="isDarkTheme ? 'dark' : 'light'">
      <!-- Header -->
      <header class="page-header">
        <h1>Settings</h1>
      </header>
  
      <!-- Main Content -->
      <main class="settings-content">
        <!-- Keywords Section -->
        <section class="settings-section">
          <h2>Keywords</h2>
          <div class="section-content">
            <div class="items-list" v-if="keywords.length">
              <div v-for="keyword in keywords" :key="keyword.id" class="item">
                <span>{{ keyword.keyword }}</span>
                <button class="delete-button" @click="deleteKeyword(keyword.id)">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
            </div>
            <p v-else class="no-items">No keywords added yet.</p>
            <button class="add-button" @click="openKeywordModal($event.target)">
              Add Keyword
            </button>
          </div>
        </section>
  
        <!-- Objects Section -->
        <section class="settings-section">
          <h2>Object Detection</h2>
          <div class="section-content">
            <div class="items-list" v-if="objects.length">
              <div v-for="object in objects" :key="object.id" class="item">
                <span>{{ object.object_name }}</span>
                <button class="delete-button" @click="deleteObject(object.id)">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
            </div>
            <p v-else class="no-items">No objects added yet.</p>
            <button class="add-button" @click="openObjectModal($event.target)">
              Add Object
            </button>
          </div>
        </section>
  
        <!-- Telegram Recipients Section -->
        <section class="settings-section">
          <h2>Telegram Recipients</h2>
          <div class="section-content">
            <div class="items-list" v-if="telegramRecipients.length">
              <div v-for="recipient in telegramRecipients" :key="recipient.id" class="item">
                <span>{{ recipient.telegram_username }} ({{ recipient.chat_id }})</span>
                <button class="delete-button" @click="deleteTelegramRecipient(recipient.id)">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </div>
            </div>
            <p v-else class="no-items">No recipients added yet.</p>
            <button class="add-button" @click="openTelegramModal($event.target)">
              Add Recipient
            </button>
          </div>
        </section>
      </main>
  
      <!-- Logout Button -->
      <button class="logout-button" @click="handleLogout" ref="logoutButton">
        <font-awesome-icon icon="sign-out-alt" class="icon" /> Logout
      </button>
  
      <!-- Modals -->
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
    </div>
  </template>
  
  <script>
  import { ref, computed, nextTick, onMounted } from 'vue'
  import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
  import { library } from '@fortawesome/fontawesome-svg-core'
  import { faTimes, faArrowLeft, faTrash, faSignOutAlt } from '@fortawesome/free-solid-svg-icons'
  import { useToast } from 'vue-toastification'
  import axios from 'axios'
  import anime from 'animejs/lib/anime.es.js'
  
  library.add(faTimes, faArrowLeft, faTrash, faSignOutAlt)
  
  export default {
    name: 'AdminSettingsPage',
    components: {
      FontAwesomeIcon
    },
    props: {
      isDarkTheme: {
        type: Boolean,
        default: false
      }
    },
    setup() {
      const toast = useToast()
      
      // Modal visibility states
      const showKeywordModal = ref(false)
      const showObjectModal = ref(false)
      const showTelegramModal = ref(false)
  
      // Form data
      const newKeyword = ref('')
      const newObject = ref('')
      const newTelegramUsername = ref('')
      const newTelegramChatId = ref('')
  
      // Data lists
      const keywords = ref([])
      const objects = ref([])
      const telegramRecipients = ref([])
  
      // Refs for animation targets
      const backdropRef = ref(null)
      const keywordModalRef = ref(null)
      const objectModalRef = ref(null)
      const telegramModalRef = ref(null)
      const keywordInputRef = ref(null)
      const objectInputRef = ref(null)
      const usernameInputRef = ref(null)
      const logoutButton = ref(null)
  
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
  
      // Computed property to detect mobile
      const isMobile = computed(() => window.innerWidth <= 768)
  
      // Local session storage keys
      const SESSION_TOKEN_KEY = 'session_token'
      const SESSION_EXPIRY_KEY = 'session_expiry'
      const USER_ROLE_KEY = 'admin'
  
      // Logout handler
      const handleLogout = () => {
        // Animate logout button
        anime({
          targets: logoutButton.value,
          translateY: [0, '20px'],
          opacity: [1, 0],
          duration: 400,
          easing: 'easeOutExpo',
          complete: async () => {
            try {
              await axios.post('/api/logout')
              // Clear session data
              localStorage.removeItem(SESSION_TOKEN_KEY)
              localStorage.removeItem(SESSION_EXPIRY_KEY)
              localStorage.removeItem(USER_ROLE_KEY)
              delete axios.defaults.headers.common['Authorization']
  
              toast.info("You have been logged out", {
                timeout: 2000,
                position: "top-center",
                icon: true
              })
  
              // Reset to home page
              setTimeout(() => {
                window.location = '/'
              }, 2000)
            } catch (error) {
              toast.error('Error during logout', {
                position: "top-center"
              })
              console.error('Logout error:', error)
            }
          }
        })
      }
  
      // Fetch data
      const fetchKeywords = async () => {
        try {
          const res = await axios.get('/api/keywords')
          keywords.value = res.data
        } catch (error) {
          toast.error('Error fetching keywords', {
            position: "top-center"
          })
        }
      }
  
      const fetchObjects = async () => {
        try {
          const res = await axios.get('/api/objects')
          objects.value = res.data
        } catch (error) {
          toast.error('Error fetching objects', {
            position: "top-center"
          })
        }
      }
  
      const fetchTelegramRecipients = async () => {
        try {
          const res = await axios.get('/api/telegram_recipients')
          telegramRecipients.value = res.data
        } catch (error) {
          toast.error('Error fetching recipients', {
            position: "top-center"
          })
        }
      }
  
      // Delete functions
      const deleteKeyword = async (id) => {
        try {
          const res = await axios.delete(`/api/keywords/${id}`)
          toast.success(res.data.message || 'Keyword deleted successfully', {
            position: "top-center"
          })
          await fetchKeywords()
        } catch (error) {
          toast.error(error.response?.data.message || 'Error deleting keyword', {
            position: "top-center"
          })
        }
      }
  
      const deleteObject = async (id) => {
        try {
          const res = await axios.delete(`/api/objects/${id}`)
          toast.success(res.data.message || 'Object deleted successfully', {
            position: "top-center"
          })
          await fetchObjects()
        } catch (error) {
          toast.error(error.response?.data.message || 'Error deleting object', {
            position: "top-center"
          })
        }
      }
  
      const deleteTelegramRecipient = async (id) => {
        try {
          const res = await axios.delete(`/api/telegram_recipients/${id}`)
          toast.success(res.data.message || 'Recipient deleted successfully', {
            position: "top-center"
          })
          await fetchTelegramRecipients()
        } catch (error) {
          toast.error(error.response?.data.message || 'Error deleting recipient', {
            position: "top-center"
          })
        }
      }
  
      // Animation functions
      const animateModalOpen = (modalRef, triggerPosition) => {
        if (!modalRef.value) return
        
        anime.remove([backdropRef.value, modalRef.value])
        
        // Position the modal
        positionModal(modalRef.value, triggerPosition)
        
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
        
        if (isMobile.value) {
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
  
      // Open modal functions
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
  
      // Close modal functions
      const closeKeywordModal = () => {
        animateModalClose(keywordModalRef, () => {
          showKeywordModal.value = false
          newKeyword.value = ''
        })
      }
  
      const closeObjectModal = () => {
        animateModalClose(objectModalRef, () => {
          showObjectModal.value = false
          newObject.value = ''
        })
      }
  
      const closeTelegramModal = () => {
        animateModalClose(telegramModalRef, () => {
          showTelegramModal.value = false
          newTelegramUsername.value = ''
          newTelegramChatId.value = ''
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
          toast.success(res.data.message || 'Keyword added successfully', {
            position: "top-center"
          })
          await fetchKeywords()
          closeKeywordModal()
        } catch (error) {
          const msg = error.response?.data.message || 'Error adding keyword'
          toast.error(msg, {
            position: "top-center"
          })
          if (error.response?.status === 400 && msg.toLowerCase().includes('exists')) {
            closeKeywordModal()
          }
        }
      }
  
      const addObject = async () => {
        if (!newObject.value.trim()) return
        
        try {
          const res = await axios.post('/api/objects', { object_name: newObject.value.trim() })
          toast.success(res.data.message || 'Object added successfully', {
            position: "top-center"
          })
          await fetchObjects()
          closeObjectModal()
        } catch (error) {
          const msg = error.response?.data.message || 'Error adding object'
          toast.error(msg, {
            position: "top-center"
          })
          if (error.response?.status === 400 && msg.toLowerCase().includes('exists')) {
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
          toast.success(res.data.message || 'Recipient added successfully', {
            position: "top-center"
          })
          await fetchTelegramRecipients()
          closeTelegramModal()
        } catch (error) {
          const msg = error.response?.data.message || 'Error adding recipient'
          toast.error(msg, {
            position: "top-center"
          })
          if (error.response?.status === 400 && msg.toLowerCase().includes('exists')) {
            closeTelegramModal()
          }
        }
      }
  
      // Initialize data
      onMounted(async () => {
        await Promise.all([fetchKeywords(), fetchObjects(), fetchTelegramRecipients()])
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
  
        // Data lists
        keywords,
        objects,
        telegramRecipients,
  
        // Refs
        backdropRef,
        keywordModalRef,
        objectModalRef,
        telegramModalRef,
        keywordInputRef,
        objectInputRef,
        usernameInputRef,
        logoutButton,
  
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
        addTelegramRecipient,
  
        // Delete functions
        deleteKeyword,
        deleteObject,
        deleteTelegramRecipient,
  
        // Logout
        handleLogout
      }
    }
  }
  </script>
  
  <style scoped>
  :root {
    --sidebar-width-expanded: 0px;
    --sidebar-width-collapsed: 50px;
    --sidebar-mobile-height: 65px;
    --stream-base-width: 480px;
    --stream-base-height: 360px;
    --stream-min-width: 240px;
    --stream-min-height: 180px;
    --primary-rgb: 59, 130, 246; /* blue-500 */
    --secondary-rgb: 156, 163, 175; /* gray-400 */
    --success-rgb: 16, 185, 129; /* green-500 */
    --danger-rgb: 239, 68, 68; /* red-500 */
    --warning-rgb: 245, 158, 11; /* yellow-500 */
    --info-rgb: 14, 165, 233; /* sky-500 */
    --bg-color: #f5f5f5;
    --text-color: #333333;
    --error-bg: #ffe6e6;
    --error-border: #ff9999;
  }
  
  [data-theme="dark"] {
    --primary-rgb: 96, 165, 250; /* blue-400 */
    --secondary-rgb: 156, 163, 175; /* gray-400 */
    --success-rgb: 34, 197, 94; /* green-400 */
    --danger-rgb: 248, 113, 113; /* red-400 */
    --warning-rgb: 251, 191, 36; /* yellow-400 */
    --info-rgb: 56, 189, 248; /* sky-400 */
    --bg-color: #121212;
    --text-color: #f0f0f0;
    --error-bg: #2d1a1a;
    --error-border: #5c2d2d;
  }
  
  .settings-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    min-height: 100vh;
    background-color: var(--bg-color);
    color: var(--text-color);
    position: relative;
    transition: all 0.3s ease;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  .page-header h1 {
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--text-color);
  }
  
  .settings-content {
    display: grid;
    gap: 1.5rem;
  }
  
  .settings-section {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
  }
  
  [data-theme="dark"] .settings-section {
    background-color: rgba(255, 255, 255, 0.05);
  }
  
  .settings-section h2 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
    color: var(--text-color);
  }
  
  .section-content {
    padding: 0.5rem;
  }
  
  .items-list {
    margin-bottom: 1rem;
  }
  
  .item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    border-bottom: 1px solid rgba(var(--secondary-rgb), 0.2);
    color: var(--text-color);
  }
  
  .item:last-child {
    border-bottom: none;
  }
  
  .delete-button {
    background: none;
    border: none;
    color: rgba(var(--danger-rgb), 1);
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 50%;
    transition: all 0.3s ease;
  }
  
  .delete-button:hover {
    background-color: rgba(var(--danger-rgb), 0.1);
  }
  
  .no-items {
    color: rgba(var(--text-color), 0.6);
    font-style: italic;
    margin-bottom: 1rem;
  }
  
  .add-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    background-color: rgba(var(--primary-rgb), 1);
    color: white;
    font-weight: 500;
    cursor: pointer;
    border: none;
    font-size: 1rem;
    transition: all 0.3s ease;
  }
  
  .add-button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
  }
  
  .logout-button {
    position: fixed;
    top: 1rem;
    right: 1rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    background-color: rgb(239, 68, 68);
    color: white;
    font-weight: 500;
    cursor: pointer;
    border: none;
    font-size: 1rem;
    transition: all 0.3s ease;
    z-index: 1000;
  }
  
  .logout-button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
  }
  
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1500;
    opacity: 0;
  }
  
  .modal-container {
    position: fixed;
    max-width: 95%;
    width: 480px;
    border-radius: 8px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
    z-index: 1600;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background-color: var(--bg-color);
    color: var(--text-color);
    opacity: 0;
  }
  
  .modal-header {
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(var(--secondary-rgb), 0.2);
  }
  
  .modal-header h2 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    flex: 1;
    text-align: center;
    color: var(--text-color);
  }
  
  .back-button, .close-button {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    color: var(--text-color);
    transition: all 0.3s ease;
  }
  
  .back-button:hover, .close-button:hover {
    background-color: rgba(var(--secondary-rgb), 0.1);
  }
  
  .modal-body {
    padding: 1rem;
    flex: 1;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--text-color);
  }
  
  .form-group input {
    width: 100%;
    padding: 0.75rem;
    border-radius: 6px;
    font-size: 1rem;
    border: 1px solid rgba(var(--secondary-rgb), 0.3);
    background-color: rgba(var(--bg-color), 0.8);
    color: var(--text-color);
    transition: all 0.3s ease;
  }
  
  .form-group input:focus {
    outline: none;
    border-color: rgba(var(--primary-rgb), 1);
    box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.2);
  }
  
  .modal-footer {
    padding: 1rem;
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    border-top: 1px solid rgba(var(--secondary-rgb), 0.2);
  }
  
  .cancel-button {
    padding: 0.75rem 1rem;
    background-color: transparent;
    border: 1px solid rgba(var(--secondary-rgb), 0.3);
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    color: var(--text-color);
    transition: all 0.3s ease;
  }
  
  .cancel-button:hover {
    background-color: rgba(var(--secondary-rgb), 0.1);
  }
  
  .submit-button {
    padding: 0.75rem 1rem;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    background-color: rgba(var(--primary-rgb), 1);
    color: white;
    transition: all 0.3s ease;
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
  
  .icon {
    font-size: 1rem;
    display: inline-block;
  }
  
  @media (max-width: 768px) {
    .settings-page {
      padding: 0.75rem;
    }
  
    .page-header h1 {
      font-size: 1.5rem;
    }
  
    .settings-section {
      padding: 1rem;
    }
  
    .settings-section h2 {
      font-size: 1.1rem;
    }
  
    .modal-container {
      width: 90%;
      top: 50% !important;
      left: 50% !important;
      transform: translate(-50%, -50%) !important;
    }
  
    .modal-header h2 {
      font-size: 1rem;
    }
  
    .form-group input {
      padding: 0.5rem;
    }
  
    .cancel-button, .submit-button {
      padding: 0.5rem 0.75rem;
      font-size: 0.9rem;
    }
  
    .logout-button {
      padding: 0.5rem 1rem;
      font-size: 0.9rem;
    }
  }
  </style>