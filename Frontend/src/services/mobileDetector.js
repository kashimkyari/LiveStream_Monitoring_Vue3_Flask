import { ref, onMounted, onUnmounted } from 'vue';

// Singleton pattern to ensure we only have one instance of mobile detection
let isMobile = ref(false);
let isInitialized = false;
let resizeHandler = null;
let orientationHandler = null;

/**
 * Initializes the mobile detector service
 * @param {number} breakpoint - The breakpoint width in pixels to consider as mobile
 */
const initialize = (breakpoint = 768) => {
  if (isInitialized) return;
  
  const checkMobile = () => {
    isMobile.value = window.innerWidth < breakpoint;
  };
  
  const debouncedCheck = debounce(checkMobile, 100);
  
  // Set up handlers
  resizeHandler = () => debouncedCheck();
  orientationHandler = () => checkMobile();
  
  // Initial check
  if (typeof window !== 'undefined') {
    checkMobile();
    window.addEventListener('resize', resizeHandler);
    window.addEventListener('orientationchange', orientationHandler);
    isInitialized = true;
  }
};

/**
 * Cleans up event listeners
 */
const cleanup = () => {
  if (!isInitialized || typeof window === 'undefined') return;
  
  window.removeEventListener('resize', resizeHandler);
  window.removeEventListener('orientationchange', orientationHandler);
  isInitialized = false;
};

/**
 * Debounce utility function
 */
const debounce = (fn, delay) => {
  let timer = null;
  return function(...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
};

/**
 * Composable for using mobile detection
 * @param {number} breakpoint - The pixel width to consider as mobile
 * @returns {object} - The mobile state object
 */
export function useMobileDetector(breakpoint = 768) {
  onMounted(() => {
    initialize(breakpoint);
  });
  
  onUnmounted(() => {
    // We don't clean up on component unmount to maintain the singleton,
    // but we can clean up when the app is unloaded
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', cleanup);
    }
  });
  
  return {
    isMobile
  };
}

// For direct importing without the composable
export const mobileDetector = {
  initialize,
  cleanup,
  get isMobile() {
    if (!isInitialized && typeof window !== 'undefined') {
      initialize();
    }
    return isMobile;
  }
};

export default mobileDetector;