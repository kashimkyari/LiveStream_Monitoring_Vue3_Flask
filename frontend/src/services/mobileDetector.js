import { ref, onMounted, onUnmounted } from 'vue';

// Singleton pattern to ensure we only have one instance of mobile detection
let isMobile = ref(false);
let isTablet = ref(false);
let isPortrait = ref(false);
let isInitialized = false;
let resizeHandler = null;
let orientationHandler = null;
let resizeTimeout = null;

/**
 * Initializes the mobile detector service with improved performance
 * @param {number} mobileBreakpoint - The breakpoint width in pixels to consider as mobile
 * @param {number} tabletBreakpoint - The breakpoint width in pixels to consider as tablet
 */
const initialize = (mobileBreakpoint = 768, tabletBreakpoint = 1024) => {
  if (isInitialized) return;
  
  // More efficient mobile detection that also checks user agent for better accuracy
  const checkMobile = () => {
    // Use navigator.userAgent for first-pass detection (faster than resize calculations)
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
    
    // First check user agent for better performance
    const isMobileDevice = mobileRegex.test(userAgent);
    
    // Then refine with screen width for responsive design support
    const screenWidth = window.innerWidth;
    
    isMobile.value = screenWidth < mobileBreakpoint || (isMobileDevice && screenWidth < tabletBreakpoint);
    isTablet.value = (screenWidth >= mobileBreakpoint && screenWidth < tabletBreakpoint) || 
                     (isMobileDevice && screenWidth >= tabletBreakpoint);
    
    // Check orientation too
    isPortrait.value = window.innerHeight > window.innerWidth;
    
    // Save detection results to sessionStorage to reduce recalculation
    try {
      sessionStorage.setItem('isMobile', String(isMobile.value));
      sessionStorage.setItem('isTablet', String(isTablet.value));
      sessionStorage.setItem('isPortrait', String(isPortrait.value));
    } catch (e) {
      // Handle storage exceptions quietly
    }
  };
  
  // More efficient debounced resize handler with throttling
  const handleResize = () => {
    // Cancel previous timeout
    if (resizeTimeout) {
      window.cancelAnimationFrame(resizeTimeout);
    }
    
    // Schedule new check using requestAnimationFrame for better performance
    resizeTimeout = window.requestAnimationFrame(() => {
      checkMobile();
    });
  };
  
  // Set up handlers
  resizeHandler = handleResize;
  orientationHandler = checkMobile; // Immediate check on orientation change
  
  // Initial check with cache from sessionStorage for better performance
  if (typeof window !== 'undefined') {
    // Try to get cached values first
    try {
      const cachedIsMobile = sessionStorage.getItem('isMobile');
      const cachedIsTablet = sessionStorage.getItem('isTablet');
      const cachedIsPortrait = sessionStorage.getItem('isPortrait');
      
      if (cachedIsMobile !== null && cachedIsTablet !== null) {
        isMobile.value = cachedIsMobile === 'true';
        isTablet.value = cachedIsTablet === 'true';
        isPortrait.value = cachedIsPortrait === 'true';
      } else {
        checkMobile();
      }
    } catch (e) {
      checkMobile();
    }
    
    // Add passive event listener for better scroll performance
    window.addEventListener('resize', resizeHandler, { passive: true });
    window.addEventListener('orientationchange', orientationHandler, { passive: true });
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

// Add eslint-disable comment to prevent warning
/* eslint-disable no-unused-vars */
/**
 * Throttle utility function (more performant than debounce for scroll/resize)
 * Keep this function for potential future use.
 */
const throttle = (fn, delay) => {
  let lastCall = 0;
  return function(...args) {
    const now = Date.now();
    if (now - lastCall < delay) return;
    lastCall = now;
    return fn.apply(this, args);
  };
};
/* eslint-enable no-unused-vars */

/**
 * Enhanced composable for responsive detection with tablet and orientation support
 * @param {number} mobileBreakpoint - The pixel width to consider as mobile
 * @param {number} tabletBreakpoint - The pixel width to consider as tablet
 * @returns {object} - The device detection state object
 */
export function useMobileDetector(mobileBreakpoint = 768, tabletBreakpoint = 1024) {
  onMounted(() => {
    initialize(mobileBreakpoint, tabletBreakpoint);
  });
  
  onUnmounted(() => {
    // We don't clean up on component unmount to maintain the singleton,
    // but we can clean up when the app is unloaded
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', cleanup);
    }
  });
  
  return {
    isMobile,
    isTablet,
    isPortrait,
    // Computed properties for convenience
    get isDesktop() { return !isMobile.value && !isTablet.value; },
    get isLandscape() { return !isPortrait.value; }
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
  },
  get isTablet() {
    if (!isInitialized && typeof window !== 'undefined') {
      initialize();
    }
    return isTablet;
  },
  get isPortrait() {
    if (!isInitialized && typeof window !== 'undefined') {
      initialize();
    }
    return isPortrait;
  },
  get isDesktop() {
    if (!isInitialized && typeof window !== 'undefined') {
      initialize();
    }
    return !isMobile.value && !isTablet.value;
  },
  get isLandscape() {
    if (!isInitialized && typeof window !== 'undefined') {
      initialize();
    }
    return !isPortrait.value;
  }
};

export default mobileDetector;