/**
 * Enhanced Mobile Detection Composable
 * 
 * Provides reactive state for detecting and responding to mobile devices
 * with optimized performance.
 * 
 * Features:
 * - Reactive mobile state that updates on window resize with debouncing
 * - Breakpoint customization
 * - Device type detection (phone, tablet, desktop)
 * - User agent detection for more accurate device identification
 * - Orientation detection (portrait/landscape)
 * - Passive event listeners for better performance
 * - SessionStorage caching to reduce expensive recalculations
 */
import { ref, onMounted, onUnmounted, computed, readonly } from 'vue';

// Debounce function to limit resize event handling frequency using requestAnimationFrame
// eslint-disable-next-line no-unused-vars
const debounce = (fn, _delay) => {
  let timer = null;
  return function(...args) {
    if (timer) cancelAnimationFrame(timer);
    timer = requestAnimationFrame(() => {
      fn.apply(this, args);
      timer = null;
    });
  };
};

export function useIsMobile(customBreakpoint = 768, tabletBreakpoint = 1024) {
  // State with initial values from sessionStorage if available
  const initialWidth = typeof window !== 'undefined' ? (
    parseInt(sessionStorage.getItem('windowWidth')) || window.innerWidth
  ) : 0;
  
  const windowWidth = ref(initialWidth);
  const breakpoint = ref(customBreakpoint);
  const tabletBreakpointRef = ref(tabletBreakpoint);
  const orientation = ref(
    typeof window !== 'undefined' 
      ? window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'
      : 'portrait'
  );
  
  // Check user agent for mobile devices
  const userAgentIsMobile = typeof navigator !== 'undefined' && (
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  );
  
  // Use hardware concurrency to detect low-power devices
  const isLowPowerDevice = ref(
    typeof navigator !== 'undefined' && 
    navigator.hardwareConcurrency && 
    navigator.hardwareConcurrency <= 4
  );
  
  // Computed properties
  const isMobile = computed(() => {
    // Combine both checks - either screen width is small OR user agent is mobile on a smaller screen
    return windowWidth.value < breakpoint.value || 
           (userAgentIsMobile && windowWidth.value < tabletBreakpointRef.value);
  });
  
  const isTablet = computed(() => {
    // Is tablet if: not a phone AND either between tablet breakpoints OR is mobile device with larger screen
    return !isPhone.value && (
      (windowWidth.value >= 768 && windowWidth.value < tabletBreakpointRef.value) ||
      (userAgentIsMobile && windowWidth.value >= tabletBreakpointRef.value)
    );
  });
  
  const isPhone = computed(() => windowWidth.value < 768);
  const isDesktop = computed(() => !isMobile.value && !isTablet.value);
  const isPortrait = computed(() => orientation.value === 'portrait');
  const isLandscape = computed(() => orientation.value === 'landscape');
  
  // Enhanced update function with caching
  const updateWindowDimensions = () => {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    windowWidth.value = width;
    orientation.value = height > width ? 'portrait' : 'landscape';
    
    // Cache values in sessionStorage to improve initial load performance on refresh
    try {
      sessionStorage.setItem('windowWidth', width.toString());
      sessionStorage.setItem('orientation', orientation.value);
    } catch (e) {
      // Handle storage exceptions quietly
    }
  };
  
  // Debounced update function for performance
  const debouncedUpdate = debounce(updateWindowDimensions, 16); // ~60fps
  
  // Set custom breakpoint
  const setBreakpoint = (value) => {
    breakpoint.value = value;
  };
  
  // Set tablet breakpoint
  const setTabletBreakpoint = (value) => {
    tabletBreakpointRef.value = value;
  };
  
  // Get device type as string
  const getDeviceType = () => {
    if (isPhone.value) return 'phone';
    if (isTablet.value) return 'tablet';
    return 'desktop';
  };
  
  // Setup listeners - use passive events for better performance
  onMounted(() => {
    window.addEventListener('resize', debouncedUpdate, { passive: true });
    window.addEventListener('orientationchange', updateWindowDimensions, { passive: true });
    updateWindowDimensions(); // Initial calculation
  });
  
  // Clean up
  onUnmounted(() => {
    window.removeEventListener('resize', debouncedUpdate);
    window.removeEventListener('orientationchange', updateWindowDimensions);
  });
  
  return {
    // State - use readonly to prevent external modification
    windowWidth: readonly(windowWidth),
    breakpoint: readonly(breakpoint),
    
    // Computed
    isMobile,
    isTablet,
    isPhone,
    isDesktop,
    isPortrait,
    isLandscape,
    isLowPowerDevice: readonly(isLowPowerDevice),
    
    // Methods
    getDeviceType,
    setBreakpoint,
    setTabletBreakpoint
  };
}