import { createApp } from 'vue'
import App from './App.vue'
import { io } from 'socket.io-client'
import { library } from '@fortawesome/fontawesome-svg-core'
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
  faCog 
} from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import Toast from "vue-toastification"
import "vue-toastification/dist/index.css"

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
  faCog
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
  position: "top-right",
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

app.config.globalProperties.$socket = io(window.location.origin, {
  withCredentials: true
})

// Mount the app
app.mount('#app')