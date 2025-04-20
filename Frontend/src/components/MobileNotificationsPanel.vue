<template>
  <div class="notification-overlay" :class="{ 'open': isOpen }" @click="close"></div>
  
  <div class="notification-panel" :class="{ 'open': isOpen }">
    <div class="panel-header">
      <h2>Notifications</h2>
      <div class="header-actions">
        <button class="header-btn" @click="toggleGroupByType">
          <font-awesome-icon icon="layer-group" :class="{ 'active': isGroupedByType }" />
        </button>
        <button class="header-btn" @click="toggleGroupByStream">
          <font-awesome-icon icon="stream" :class="{ 'active': isGroupedByStream }" />
        </button>
        <button class="header-btn" @click="markAllAsRead">
          <font-awesome-icon icon="check-double" />
        </button>
        <button class="header-btn close-btn" @click="close">
          <font-awesome-icon icon="times" />
        </button>
      </div>
    </div>
    
    <div v-if="loading" class="panel-loader">
      <div class="spinner-small"></div>
      <p>Loading notifications...</p>
    </div>
    
    <div v-else-if="notificationGroups && Object.keys(notificationGroups).length === 0" class="empty-state">
      <font-awesome-icon icon="bell-slash" size="2x" />
      <p>No notifications yet</p>
    </div>
    
    <div v-else class="notification-list">
      <div v-for="(notifications, groupName) in notificationGroups" :key="groupName" class="notification-group">
        <div v-if="isGroupedByType || isGroupedByStream" class="group-header">
          <h3>{{ formatGroupName(groupName) }}</h3>
          <span class="group-count">{{ notifications.length }}</span>
        </div>
        
        <div v-for="notification in notifications" 
          :key="notification.id" 
          class="notification-item"
          :class="{ 'unread': !notification.read }"
          @click="onNotificationClick(notification)">
          
          <div class="notification-icon">
            <font-awesome-icon :icon="getNotificationIcon(notification)" 
                              :style="{ color: getNotificationColor(notification) }" />
          </div>
          
          <div class="notification-content">
            <div class="notification-title">{{ getNotificationTitle(notification) }}</div>
            <div class="notification-details" v-if="notification.details">
              {{ getNotificationDetails(notification) }}
            </div>
            <div class="notification-time">{{ formatTimeAgo(notification.timestamp) }}</div>
          </div>
          
          <div class="notification-actions">
            <button class="mark-read-btn" 
                    v-if="!notification.read"
                    @click.stop="markAsRead(notification.id)">
              <font-awesome-icon icon="check" />
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="panel-footer">
      <button class="refresh-btn" @click="refreshNotifications" :disabled="loading">
        <font-awesome-icon icon="sync" :class="{ 'fa-spin': loading }" />
        Refresh
      </button>
    </div>
  </div>
</template>

<script>
import { computed, ref, onMounted, watch } from 'vue';
import { useMobileNotifications } from '../composables/useMobileNotifications';

export default {
  name: 'MobileNotificationsPanel',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'notification-click'],
  setup(props, { emit }) {
    const { 
      notifications, 
      groupedNotifications,
      isGroupedByType,
      isGroupedByStream,
      loading,
      error,
      loadNotifications,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      formatTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle
    } = useMobileNotifications();
    
    const refreshing = ref(false);
    
    // Get the notification groups
    const notificationGroups = computed(() => {
      return groupedNotifications.value;
    });
    
    // Format group name for display
    const formatGroupName = (name) => {
      if (!name) return 'Unknown';
      
      // For event types, make them more readable
      if (isGroupedByType.value) {
        // Convert snake_case to Title Case
        return name.replace(/_/g, ' ')
          .replace(/\w\S*/g, (txt) => {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
          });
      }
      
      // For streamer names, just return as is
      return name;
    };
    
    // Get notification details
    const getNotificationDetails = (notification) => {
      if (!notification || !notification.details) return '';
      
      if (typeof notification.details === 'string') {
        try {
          // Try to parse JSON if it's a string
          const details = JSON.parse(notification.details);
          return details.message || '';
        } catch (e) {
          return notification.details;
        }
      } else if (typeof notification.details === 'object') {
        return notification.details.message || 
               notification.details.keyword || 
               notification.details.object_name || '';
      }
      
      return '';
    };
    
    // Close panel
    const close = () => {
      emit('close');
    };
    
    // Handle notification click
    const onNotificationClick = (notification) => {
      if (!notification.read) {
        markAsRead(notification.id);
      }
      emit('notification-click', notification);
    };
    
    // Refresh notifications
    const refreshNotifications = async () => {
      refreshing.value = true;
      await loadNotifications({ forceRefresh: true });
      refreshing.value = false;
    };
    
    // Watch for panel open to refresh
    watch(() => props.isOpen, (newValue) => {
      if (newValue) {
        refreshNotifications();
      }
    });
    
    // Initial load
    onMounted(() => {
      loadNotifications();
    });
    
    return {
      // State
      notifications,
      notificationGroups,
      isGroupedByType,
      isGroupedByStream,
      loading: computed(() => loading.value || refreshing.value),
      error,
      
      // Methods
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      close,
      onNotificationClick,
      refreshNotifications,
      
      // Helpers
      formatGroupName,
      formatTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle,
      getNotificationDetails
    };
  }
};
</script>

<style scoped>
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  border-bottom: 1px solid var(--light-border);
  background-color: var(--light-card-bg);
  position: sticky;
  top: 0;
  z-index: 1;
}

[data-theme='dark'] .panel-header {
  border-bottom-color: var(--dark-border);
  background-color: var(--dark-card-bg);
}

.panel-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--light-text);
}

[data-theme='dark'] .panel-header h2 {
  color: var(--dark-text);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--light-hover);
  color: var(--light-text-secondary);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme='dark'] .header-btn {
  background-color: var(--dark-hover);
  color: var(--dark-text-secondary);
}

.header-btn:hover, .header-btn.active {
  background-color: var(--light-primary);
  color: white;
}

[data-theme='dark'] .header-btn:hover, 
[data-theme='dark'] .header-btn.active {
  background-color: var(--dark-primary);
}

.close-btn {
  background-color: var(--light-hover);
  color: var(--light-text-secondary);
}

[data-theme='dark'] .close-btn {
  background-color: var(--dark-hover);
  color: var(--dark-text-secondary);
}

.close-btn:hover {
  background-color: var(--light-danger);
  color: white;
}

[data-theme='dark'] .close-btn:hover {
  background-color: var(--dark-danger);
}

.notification-list {
  padding: 0;
  overflow-y: auto;
}

.notification-group {
  margin-bottom: 10px;
}

.group-header {
  padding: 10px 15px;
  background-color: var(--light-hover);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--light-border);
}

[data-theme='dark'] .group-header {
  background-color: var(--dark-hover);
  border-bottom-color: var(--dark-border);
}

.group-header h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--light-text);
}

[data-theme='dark'] .group-header h3 {
  color: var(--dark-text);
}

.group-count {
  background-color: var(--light-primary);
  color: white;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 0.7rem;
  font-weight: 600;
}

[data-theme='dark'] .group-count {
  background-color: var(--dark-primary);
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 15px;
  border-bottom: 1px solid var(--light-border);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

[data-theme='dark'] .notification-item {
  border-bottom-color: var(--dark-border);
}

.notification-item:hover {
  background-color: var(--light-hover);
}

[data-theme='dark'] .notification-item:hover {
  background-color: var(--dark-hover);
}

.notification-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(66, 153, 225, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

[data-theme='dark'] .notification-icon {
  background-color: rgba(99, 179, 237, 0.1);
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--light-text);
}

[data-theme='dark'] .notification-title {
  color: var(--dark-text);
}

.notification-details {
  font-size: 0.85rem;
  margin-bottom: 3px;
  color: var(--light-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

[data-theme='dark'] .notification-details {
  color: var(--dark-text-secondary);
}

.notification-time {
  font-size: 0.75rem;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .notification-time {
  color: var(--dark-text-secondary);
}

.notification-actions {
  flex-shrink: 0;
  margin-left: 8px;
}

.mark-read-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: transparent;
  color: var(--light-text-secondary);
  border: 1px solid var(--light-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

[data-theme='dark'] .mark-read-btn {
  color: var(--dark-text-secondary);
  border-color: var(--dark-border);
}

.mark-read-btn:hover {
  background-color: var(--light-success);
  color: white;
  border-color: var(--light-success);
}

[data-theme='dark'] .mark-read-btn:hover {
  background-color: var(--dark-success);
  border-color: var(--dark-success);
}

.panel-footer {
  padding: 15px;
  display: flex;
  justify-content: center;
  border-top: 1px solid var(--light-border);
  background-color: var(--light-card-bg);
  position: sticky;
  bottom: 0;
}

[data-theme='dark'] .panel-footer {
  border-top-color: var(--dark-border);
  background-color: var(--dark-card-bg);
}

.refresh-btn {
  padding: 8px 16px;
  background-color: var(--light-primary);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s ease;
}

[data-theme='dark'] .refresh-btn {
  background-color: var(--dark-primary);
}

.refresh-btn:hover:not(:disabled) {
  background-color: var(--light-primary-dark, #3182ce);
}

[data-theme='dark'] .refresh-btn:hover:not(:disabled) {
  background-color: var(--dark-primary-light, #90cdf4);
}

.refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.panel-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .panel-loader {
  color: var(--dark-text-secondary);
}

.spinner-small {
  width: 30px;
  height: 30px;
  border: 3px solid var(--light-hover);
  border-top-color: var(--light-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

[data-theme='dark'] .spinner-small {
  border-color: var(--dark-hover);
  border-top-color: var(--dark-primary);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 20px;
  text-align: center;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .empty-state {
  color: var(--dark-text-secondary);
}

.empty-state svg {
  margin-bottom: 15px;
  opacity: 0.7;
}
</style>