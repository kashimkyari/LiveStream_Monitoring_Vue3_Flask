<template>
  <div class="settings-tab">
    <div class="tab-header">
      <h2>Settings</h2>
    </div>
    
    <div class="settings-list">
      <div class="settings-section">
        <h3>Display Settings</h3>
        <div class="setting-item">
          <label class="switch">
            <input type="checkbox" 
                   :checked="isDarkTheme"
                   @change="$emit('update:isDarkTheme', $event.target.checked)">
            <span class="slider round"></span>
          </label>
          <span class="setting-label">Dark Mode</span>
        </div>
      </div>
      
      <div class="settings-section">
        <h3>Data Settings</h3>
        <div class="setting-item">
          <label class="switch">
            <input type="checkbox" 
                   :checked="enableBackgroundRefresh"
                   @change="$emit('update:enableBackgroundRefresh', $event.target.checked)">
            <span class="slider round"></span>
          </label>
          <span class="setting-label">Background Refresh</span>
        </div>
        <div class="refresh-interval-setting">
          <span class="setting-label">Refresh Interval</span>
          <select 
            :value="refreshIntervalMinutes"
            @input="$emit('update:refreshIntervalMinutes', $event.target.value)"
            class="interval-select"
          >
            <option value="1">1 minute</option>
            <option value="5">5 minutes</option>
            <option value="10">10 minutes</option>
            <option value="30">30 minutes</option>
          </select>
        </div>
      </div>
      
      <div class="settings-section">
        <h3>Notification Settings</h3>
        <div class="setting-item">
          <label class="switch">
            <input type="checkbox"
                   :checked="isGroupedByType"
                   @change="$emit('update:isGroupedByType', $event.target.checked)">
            <span class="slider round"></span>
          </label>
          <span class="setting-label">Group by Event Type</span>
        </div>
        <div class="setting-item">
          <label class="switch">
            <input type="checkbox"
                   :checked="isGroupedByStream"
                   @change="$emit('update:isGroupedByStream', $event.target.checked)">
            <span class="slider round"></span>
          </label>
          <span class="setting-label">Group by Stream</span>
        </div>
        <div class="setting-item notification-action" @click="markAllAsRead" v-if="unreadCount > 0">
          <font-awesome-icon icon="check-double" class="setting-icon" />
          <span class="setting-label">Mark All as Read ({{ unreadCount }})</span>
        </div>
      </div>
      
      <div class="settings-section">
        <h3>Account</h3>
        <div class="setting-item" @click="logout">
          <font-awesome-icon icon="sign-out-alt" class="setting-icon" />
          <span class="setting-label">Logout</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// import { defineEmits } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

export default {
  name: 'MobileAdminSettings',
  props: {
    isDarkTheme: Boolean,
    enableBackgroundRefresh: Boolean,
    refreshIntervalMinutes: String,
    isGroupedByType: Boolean,
    isGroupedByStream: Boolean,
    unreadCount: Number
  },
  emits: [
    'update:isDarkTheme',
    'update:enableBackgroundRefresh',
    'update:refreshIntervalMinutes',
    'update:isGroupedByType',
    'update:isGroupedByStream',
    'mark-all-read',
    'logout'
  ],
  setup(props, { emit }) {
    const toast = useToast()
    
    // Handle dark theme change
    const handleDarkThemeChange = (value) => {
      localStorage.setItem('themePreference', value ? 'dark' : 'light')
      emit('update:isDarkTheme', value)
    }

    // Handle background refresh change
    const handleBackgroundRefreshChange = (value) => {
      emit('update:enableBackgroundRefresh', value)
    }

    // Handle refresh interval change
    const handleRefreshIntervalChange = (value) => {
      emit('update:refreshIntervalMinutes', value)
    }

    // Handle group by type change
    const handleGroupByTypeChange = (value) => {
      emit('update:isGroupedByType', value)
    }

    // Handle group by stream change
    const handleGroupByStreamChange = (value) => {
      emit('update:isGroupedByStream', value)
    }

    // Mark all notifications as read
    const markAllAsRead = async () => {
      try {
        await axios.post('/api/notifications/mark-all-read')
        emit('mark-all-read')
        toast.success('All notifications marked as read')
      } catch (error) {
        console.error('Error marking all notifications as read:', error)
        toast.error('Failed to mark all notifications as read')
      }
    }

    // Logout
    const logout = async () => {
      try {
        await axios.post('/api/logout')
        toast.info('Logged out successfully')
        window.location.href = '/'
      } catch (error) {
        console.error('Logout failed:', error)
        toast.error('Logout failed')
      }
    }

    return {
      markAllAsRead,
      logout,
      handleDarkThemeChange,
      handleBackgroundRefreshChange,
      handleRefreshIntervalChange,
      handleGroupByTypeChange,
      handleGroupByStreamChange
    }
  }
}
</script>

<style scoped>
.mobile-admin-dashboard,
.mobile-admin-dashboard * {
  font-family: var(--font-family);
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.mobile-admin-dashboard {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  color: var(--text-color);
  padding-bottom: 70px; /* Space for bottom nav */
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 1rem;
}
</style>