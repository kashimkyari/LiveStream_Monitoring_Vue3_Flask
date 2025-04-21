<template>
  <div class="mobile-nav-container">
    <div class="mobile-tab-bar">
      <div 
        v-for="item in navigationItems" 
        :key="item.id"
        class="nav-item"
        :class="{ 'active': activeTab === item.id }"
        @click="changeTab(item.id)"
      >
        <div class="nav-icon-container">
          <font-awesome-icon :icon="item.icon" />
          <mobile-notification-badge 
            v-if="item.id === 'notifications' && unreadCount > 0"
            :count="unreadCount"
            size="small"
            :animated="newNotificationReceived"
          />
          <mobile-notification-badge 
            v-if="item.id === 'messages' && messageCount > 0"
            :count="messageCount"
            size="small"
            :animated="newMessageReceived"
          />
        </div>
        <span class="nav-label">{{ item.label }}</span>
      </div>
    </div>
    
    <transition name="fade">
      <div class="theme-toggle" v-if="showThemeToggle">
        <button class="theme-button" @click="toggleTheme">
          <font-awesome-icon :icon="isDarkTheme ? 'sun' : 'moon'" />
          <span>{{ isDarkTheme ? 'Light Mode' : 'Dark Mode' }}</span>
        </button>
      </div>
    </transition>
    
    <transition name="slide-left">
      <div class="profile-dropdown" v-if="showProfileDropdown">
        <div class="profile-header">
          <div class="profile-avatar">
            <font-awesome-icon icon="user-circle" />
          </div>
          <div class="profile-info">
            <div class="profile-name">{{ username }}</div>
            <div class="profile-role">{{ roleName }}</div>
          </div>
          <button class="close-dropdown" @click="closeProfileDropdown">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        
        <div class="profile-menu">
          <div class="menu-section">
            <div class="menu-item" @click="toggleThemeToggle">
              <font-awesome-icon :icon="isDarkTheme ? 'sun' : 'moon'" />
              <span>Theme</span>
            </div>
            
            <div class="menu-item" @click="handleSettings">
              <font-awesome-icon icon="cog" />
              <span>Settings</span>
            </div>
          </div>
          
          <div class="menu-section">
            <div class="menu-item logout" @click="handleLogout">
              <font-awesome-icon icon="sign-out-alt" />
              <span>Logout</span>
            </div>
          </div>
        </div>
      </div>
    </transition>
    
    <div class="logout-confirm" v-if="showLogoutConfirm">
      <div class="logout-dialog">
        <h3>Confirm Logout</h3>
        <p>Are you sure you want to log out?</p>
        <div class="logout-actions">
          <button class="cancel-button" @click="cancelLogout">Cancel</button>
          <button class="confirm-button" @click="confirmLogout">
            <span v-if="!loggingOut">Logout</span>
            <font-awesome-icon v-else icon="spinner" spin />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';
import { useToast } from 'vue-toastification';
import MobileNotificationBadge from './MobileNotificationBadge.vue';
import { useMobileNotifications } from '../composables/useMobileNotifications';
import MessageService from '../services/MessageService';

export default {
  name: 'MobileNavigationBar',
  components: {
    MobileNotificationBadge
  },
  props: {
    activeTab: {
      type: String,
      required: true
    }
  },
  emits: ['tab-change', 'theme-change', 'settings'],
  setup(props, { emit }) {
    // Reactive state
    const showProfileDropdown = ref(false);
    const showThemeToggle = ref(false);
    const showLogoutConfirm = ref(false);
    const loggingOut = ref(false);
    const username = ref(localStorage.getItem('username') || null);
    const userRole = ref(localStorage.getItem('userRole') || 'user');
    const isDarkTheme = ref(localStorage.getItem('theme') === 'dark');
    const newNotificationReceived = ref(false);
    const newMessageReceived = ref(false);
    
    // Get notification and message counts from respective services
    const { unreadCount } = useMobileNotifications();
    const messageCount = MessageService.unreadCount;
    
    // When unread notification count changes, animate badge
    watch(unreadCount, (newCount, oldCount) => {
      if (newCount > oldCount) {
        newNotificationReceived.value = true;
        setTimeout(() => {
          newNotificationReceived.value = false;
        }, 3000);
      }
    });
    
    // When unread message count changes, animate badge
    watch(messageCount, (newCount, oldCount) => {
      if (newCount > oldCount) {
        newMessageReceived.value = true;
        setTimeout(() => {
          newMessageReceived.value = false;
        }, 3000);
      }
    });
    
    // Toast for notifications
    const toast = useToast();
    
    // Computed properties
    const roleName = computed(() => {
      if (!userRole.value) return '';
      return userRole.value.charAt(0).toUpperCase() + userRole.value.slice(1);
    });
    
    const navigationItems = computed(() => {
      const baseItems = [
        { id: 'home', label: 'Home', icon: 'house' },
        { id: 'streams', label: 'Streams', icon: 'video' },
        { id: 'messages', label: 'Messages', icon: 'comment' },
        { id: 'notifications', label: 'Alerts', icon: 'bell' },
        { id: 'profile', label: 'Profile', icon: 'user' }
      ];
      
      // Admin-specific items
      if (userRole.value === 'admin') {
        // Instead of adding a new tab, we'll handle admin-specific views
        // within existing tabs to keep the interface clean
      }
      
      return baseItems;
    });
    
    // Methods
    const changeTab = (tabId) => {
      if (tabId === 'profile') {
        showProfileDropdown.value = !showProfileDropdown.value;
        return;
      }
      
      if (tabId === props.activeTab) return;
      emit('tab-change', tabId);
      
      // Close dropdowns when changing tabs
      showProfileDropdown.value = false;
      showThemeToggle.value = false;
    };
    
    const closeProfileDropdown = () => {
      showProfileDropdown.value = false;
    };
    
    const toggleThemeToggle = () => {
      showThemeToggle.value = !showThemeToggle.value;
    };
    
    const toggleTheme = () => {
      isDarkTheme.value = !isDarkTheme.value;
      
      // Save theme preference
      localStorage.setItem('theme', isDarkTheme.value ? 'dark' : 'light');
      
      // Apply theme to document
      document.documentElement.setAttribute('data-bs-theme', isDarkTheme.value ? 'dark' : 'light');
      
      // Notify parent component
      emit('theme-change', isDarkTheme.value ? 'dark' : 'light');
      
      // Close theme toggle
      showThemeToggle.value = false;
    };
    
    const handleSettings = () => {
      emit('settings');
      showProfileDropdown.value = false;
    };
    
    const handleLogout = () => {
      showLogoutConfirm.value = true;
      showProfileDropdown.value = false;
    };
    
    const cancelLogout = () => {
      showLogoutConfirm.value = false;
    };
    
    const confirmLogout = async () => {
      // Prevent multiple executions
      if (loggingOut.value) return;
      
      loggingOut.value = true;
      
      try {
        await axios.post('/api/logout');
        
        // Show toast and wait briefly before clearing localStorage and redirecting
        toast.success('Logged out successfully');
        
        setTimeout(() => {
          localStorage.removeItem('userId');
          localStorage.removeItem('username');
          localStorage.removeItem('userRole');
          
          // Redirect to login page
          window.location.href = '/login';
        }, 1000);
      } catch (error) {
        console.error('Logout failed:', error);
        toast.error('Logout failed. Please try again.');
      } finally {
        loggingOut.value = false;
        showLogoutConfirm.value = false;
      }
    };
    
    // Initialize
    onMounted(() => {
      // Apply current theme
      document.documentElement.setAttribute('data-bs-theme', isDarkTheme.value ? 'dark' : 'light');
    });
    
    return {
      navigationItems,
      showProfileDropdown,
      showThemeToggle,
      showLogoutConfirm,
      loggingOut,
      username,
      roleName,
      isDarkTheme,
      unreadCount,
      messageCount,
      newNotificationReceived,
      newMessageReceived,
      changeTab,
      closeProfileDropdown,
      toggleThemeToggle,
      toggleTheme,
      handleSettings,
      handleLogout,
      cancelLogout,
      confirmLogout
    };
  }
};
</script>

<style scoped>
.mobile-nav-container {
  position: relative;
}

.mobile-tab-bar {
  display: flex;
  justify-content: space-around;
  align-items: center;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: var(--bs-body-bg);
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  cursor: pointer;
  transition: color 0.2s, transform 0.1s;
  color: var(--bs-secondary);
  user-select: none;
}

.nav-item.active {
  color: var(--bs-primary);
}

.nav-item:active {
  transform: scale(0.95);
}

.nav-icon-container {
  position: relative;
  font-size: 1.25rem;
  margin-bottom: 4px;
}

.nav-label {
  font-size: 0.75rem;
  font-weight: 500;
}

.theme-toggle {
  position: fixed;
  bottom: 70px;
  right: 16px;
  background-color: var(--bs-body-bg);
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
  padding: 8px;
  z-index: 999;
}

.theme-button {
  background: none;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  color: var(--bs-body-color);
  font-size: 0.9rem;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.theme-button:hover {
  background-color: var(--bs-secondary-bg);
}

.profile-dropdown {
  position: fixed;
  bottom: 70px;
  left: 16px;
  right: 16px;
  background-color: var(--bs-body-bg);
  border-radius: 12px;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.2);
  z-index: 1001;
  overflow: hidden;
}

.profile-header {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--bs-border-color);
}

.profile-avatar {
  font-size: 2.5rem;
  color: var(--bs-primary);
  margin-right: 12px;
}

.profile-info {
  flex: 1;
}

.profile-name {
  font-size: 1.1rem;
  font-weight: 600;
}

.profile-role {
  font-size: 0.9rem;
  color: var(--bs-secondary);
}

.close-dropdown {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: var(--bs-secondary);
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20px;
  transition: background-color 0.2s;
}

.close-dropdown:hover {
  background-color: var(--bs-secondary-bg);
  color: var(--bs-primary);
}

.profile-menu {
  padding: 8px 0;
}

.menu-section {
  padding: 8px 0;
  border-bottom: 1px solid var(--bs-border-color);
}

.menu-section:last-child {
  border-bottom: none;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background-color: var(--bs-secondary-bg);
}

.menu-item svg {
  width: 20px;
  margin-right: 12px;
  color: var(--bs-secondary);
}

.menu-item.logout {
  color: var(--bs-danger);
}

.menu-item.logout svg {
  color: var(--bs-danger);
}

.logout-confirm {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.logout-dialog {
  background-color: var(--bs-body-bg);
  border-radius: 12px;
  padding: 24px;
  width: 80%;
  max-width: 320px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.logout-dialog h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 1.25rem;
}

.logout-dialog p {
  margin-bottom: 24px;
}

.logout-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-button {
  background-color: var(--bs-secondary-bg);
  color: var(--bs-body-color);
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cancel-button:hover {
  filter: brightness(0.95);
}

.confirm-button {
  background-color: var(--bs-danger);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  min-width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-button:hover {
  filter: brightness(0.9);
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-left-enter-active,
.slide-left-leave-active {
  transition: transform 0.3s;
}

.slide-left-enter-from,
.slide-left-leave-to {
  transform: translateX(-100%);
}
</style>