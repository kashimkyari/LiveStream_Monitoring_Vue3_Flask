import { computed } from 'vue'
import { mobileDetector } from '../services/mobileDetector'

/**
 * A composable that provides reactive mobile state detection
 * This is now a wrapper around our centralized mobileDetector service
 * @param {number} breakpoint - The pixel width threshold for mobile detection (default: 768px)
 * @returns {object} - An object containing the isMobile ref
 */
export function useIsMobile(breakpoint = 768) {
  // Ensure the detector is initialized with the provided breakpoint
  mobileDetector.initialize(breakpoint)
  
  // Create a computed property that references the singleton state
  const isMobile = computed(() => mobileDetector.isMobile.value)

  return { isMobile }
}