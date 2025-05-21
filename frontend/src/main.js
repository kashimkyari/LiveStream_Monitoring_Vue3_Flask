import { createApp } from "vue";
import App from "./App.vue";
import { library } from "@fortawesome/fontawesome-svg-core";
import { mobileDetector } from "./services/mobileDetector";
import "./assets/styles/common.css";
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
  faBinoculars,
  faLink,
  faMoon, // Added for theme toggle
  faSun,
  faWifi3,
  faLightbulb, // Added for theme toggle
  faPlusCircle,
  faRocket,
  faChevronUp,
  faUserShield,
  faUserCheck,
  faUserSecret,
  faChartBar,
  faSatelliteDish,
  faUserPlus,
  faUserClock,
  faUserCircle,
  faTags,
  faTasks,
  faStickyNote,
  faStopCircle,
  faCheckCircle,
  faDownload,
  faDatabase,
  faFlagCheckered,
  faCircleNotch,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import Toast from "vue-toastification";
import "vue-toastification/dist/index.css";
import { inject } from "@vercel/analytics";
import { createPinia } from "pinia";
import {
  faTelegram,
  faGoogle,
  faApple,
} from "@fortawesome/free-brands-svg-icons";

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
  faMoon, // Added
  faSun, // Added
  faTelegram,
  faGoogle,
  faApple,
  faWifi3,
  faLightbulb,
  faPlusCircle,
  faRocket,
  faChevronUp,
  faUserShield,
  faUserCheck,
  faUserSecret,
  faChartBar,
  faSatelliteDish,
  faUserPlus,
  faUserClock,
  faUserCircle,
  faTags,
  faTasks,
  faStickyNote,
  faStopCircle,
  faCheckCircle,
  faDownload,
  faDatabase,
  faFlagCheckered,
  faCircleNotch
);

// Create a single app instance
const app = createApp(App);

// Register the FontAwesomeIcon component
app.component("FontAwesomeIcon", FontAwesomeIcon);

// Use plugins
app.use(Toast, {
  transition: "Vue-Toastification__bounce",
  maxToasts: 3,
  newestOnTop: true,
  position: "top-center",
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
  rtl: false,
});

inject(); // Call inject() outside of app.use to initialize analytics

app.use(createPinia());

// Initialize mobile detector
mobileDetector.initialize(768);

// Make mobile detector available globally
app.config.globalProperties.$mobileDetector = mobileDetector;

// Mount the app
app.mount("#app");
