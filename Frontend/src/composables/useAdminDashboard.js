// src/composables/useAdminDashboard.js
import { ref } from 'vue'

export function useAdminDashboard() {
  // State
  const isDarkTheme = ref(localStorage.getItem('themePreference') === 'dark' || true)
  const activeTab = ref('dashboard')
  const isOnline = ref(navigator.onLine)
  const sidebarMinimized = ref(true) // Track sidebar state
  const notifications = ref([])
  
  // Methods
  const handleSidebarToggle = (isMinimized) => {
    sidebarMinimized.value = isMinimized
  }
  
  return {
    isDarkTheme,
    activeTab,
    isOnline,
    sidebarMinimized,
    notifications,
    handleSidebarToggle
  }
}