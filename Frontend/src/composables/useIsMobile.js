/**
 * Mobile Detection Composable
 * 
 * Provides reactive state for detecting and responding to mobile devices
 * Features:
 * - Reactive mobile state that updates on window resize
 * - Breakpoint customization
 * - Device type detection (phone, tablet, desktop)
 */
import { ref, onMounted, onUnmounted, computed } from 'vue';

export function useIsMobile(customBreakpoint = 768) {
  // State
  const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 0);
  const breakpoint = ref(customBreakpoint);
  
  // Computed properties
  const isMobile = computed(() => windowWidth.value < breakpoint.value);
  const isTablet = computed(() => windowWidth.value >= 768 && windowWidth.value < 1024);
  const isPhone = computed(() => windowWidth.value < 768);
  const isDesktop = computed(() => windowWidth.value >= 1024);
  
  // Update window width on resize
  const updateWindowWidth = () => {
    windowWidth.value = window.innerWidth;
  };
  
  // Set custom breakpoint
  const setBreakpoint = (value) => {
    breakpoint.value = value;
  };
  
  // Get device type as string
  const getDeviceType = () => {
    if (isPhone.value) return 'phone';
    if (isTablet.value) return 'tablet';
    return 'desktop';
  };
  
  // Setup resize listener
  onMounted(() => {
    window.addEventListener('resize', updateWindowWidth);
    updateWindowWidth();
  });
  
  // Clean up
  onUnmounted(() => {
    window.removeEventListener('resize', updateWindowWidth);
  });
  
  return {
    // State
    windowWidth,
    breakpoint,
    
    // Computed
    isMobile,
    isTablet,
    isPhone,
    isDesktop,
    
    // Methods
    getDeviceType,
    setBreakpoint
  };
}