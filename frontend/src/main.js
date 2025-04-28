import { createApp } from 'vue'
import App from './App.vue'
import { io } from 'socket.io-client'
import { library } from '@fortawesome/fontawesome-svg-core'
import { mobileDetector } from './services/mobileDetector'
import './assets/styles/common.css'
import { 
  faUserLock, 
  faUser, 
  faLock, 
  faSignInAlt, 
  faExclamationCircle, 
  faSpinner,
  faSync, 
  faEdit, 
  faTrash, 
  faBell, 
  faPlus, 
  faCheck, 
  faExclamationTriangle, 
  faStream, 
  faCog, 
  faHouse,
  faPlay,
  faStop,
  faBinoculars ,
  faLink
} from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import Toast from "vue-toastification"
import "vue-toastification/dist/index.css"
import { inject } from "@vercel/analytics"
import { createPinia } from 'pinia'
import { faTelegram } from '@fortawesome/free-brands-svg-icons';

// Add all icons to the library
library.add(
  faUserLock, 
  faUser, 
  faLock, 
  faSignInAlt, 
  faExclamationCircle, 
  faSpinner,
  faSync, 
  faEdit, 
  faTrash, 
  faBell, 
  faPlus, 
  faCheck, 
  faExclamationTriangle, 
  faStream, 
  faCog,
  faHouse,
  faPlay,
  faStop,
  faBinoculars,
  faLink,
  faTelegram

)

// Create a single app instance
const app = createApp(App)

// Register the FontAwesomeIcon component
app.component('FontAwesomeIcon', FontAwesomeIcon)

// Use plugins
app.use(Toast, {
  transition: "Vue-Toastification__bounce",
  maxToasts: 3,
  newestOnTop: true,
  position: "top",
  timeout: 5000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: "button",
  icon: true,
  rtl: false
})

app.config.globalProperties.$socket = io('https://54.86.99.85:5000', {
  path: '/ws',
  withCredentials: true,
  transports: ['websocket', 'polling'] // Recommended for fallback
})

app.use(inject())
app.use(createPinia())

// Initialize mobile detector
mobileDetector.initialize(768)

// Make mobile detector available globally
app.config.globalProperties.$mobileDetector = mobileDetector

// Mount the app
app.mount('#app')