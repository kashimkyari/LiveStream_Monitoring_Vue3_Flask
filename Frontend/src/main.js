import { createApp } from 'vue'
import App from './App.vue'
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
  transition: 'Vue-Toastification__bounce',
  maxToasts: 5,
  newestOnTop: true,
  timeout: 5000
})

// Mount the app
app.mount('#app')