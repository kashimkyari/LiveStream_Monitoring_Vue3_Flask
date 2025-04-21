<template>
  <div class="notifications-panel" :class="{ 'active': isOpen }">
    <div class="panel-header">
      <h2>Notifications</h2>
      <div class="panel-actions">
        <button class="preferences-button" @click="openPreferences">
          <font-awesome-icon icon="sliders-h" />
        </button>
        <button class="close-button" @click="closePanel">
          <font-awesome-icon icon="times" />
        </button>
      </div>
    </div>
    
    <div class="panel-filters">
      <div class="filter-group">
        <button 
          class="filter-button" 
          :class="{ 'active': showOnlyUnread }"
          @click="toggleUnreadFilter"
        >
          <font-awesome-icon icon="eye" />
          <span>{{ showOnlyUnread ? 'All' : 'Unread' }}</span>
        </button>
        
        <select 
          class="filter-select" 
          v-model="selectedType"
          @change="applyTypeFilter"
        >
          <option value="">All types</option>
          <option v-for="type in notificationTypes" :key="type" :value="type">
            {{ formatEventType(type) }}
          </option>
        </select>
      </div>
      
      <button 
        class="mark-all-button"
        @click="markAllAsRead"
        :disabled="loading || !hasUnread"
      >
        <font-awesome-icon :icon="loading ? 'spinner' : 'check-double'" :spin="loading" />
        <span>Mark all read</span>
      </button>
    </div>
    
    <div class="notifications-container" ref="notificationsContainer">
      <!-- Loading indicator -->
      <div class="loading-indicator" v-if="loading">
        <font-awesome-icon icon="spinner" spin />
        <span>Loading notifications...</span>
      </div>
      
      <!-- Empty state -->
      <div class="empty-state" v-else-if="!loading && filteredNotifications.length === 0">
        <font-awesome-icon icon="bell-slash" class="empty-icon" />
        <p>No notifications to display</p>
        <button class="refresh-button" @click="refreshNotifications">
          <font-awesome-icon icon="sync" />
          <span>Refresh</span>
        </button>
      </div>
      
      <!-- Grouped notifications by type -->
      <div class="notifications-list" v-else-if="groupByType">
        <div 
          v-for="group in filteredNotifications" 
          :key="group.event_type"
          class="notification-group"
        >
          <div class="group-header">
            <h3>{{ group.title }}</h3>
            <span class="group-count">{{ group.notifications.length }}</span>
          </div>
          
          <notification-item
            v-for="notification in group.notifications"
            :key="notification.id"
            :notification="notification"
            @click="onNotificationClick(notification)"
            @mark-read="markAsRead(notification.id)"
          />
        </div>
      </div>
      
      <!-- Grouped notifications by stream -->
      <div class="notifications-list" v-else-if="groupByStream">
        <div 
          v-for="group in filteredNotifications" 
          :key="group.room_url"
          class="notification-group"
        >
          <div class="group-header">
            <h3>{{ group.streamer }}</h3>
            <span class="group-badge">{{ group.platform }}</span>
            <span class="group-count">{{ group.notifications.length }}</span>
          </div>
          
          <notification-item
            v-for="notification in group.notifications"
            :key="notification.id"
            :notification="notification"
            @click="onNotificationClick(notification)"
            @mark-read="markAsRead(notification.id)"
          />
        </div>
      </div>
      
      <!-- Regular notification list -->
      <div class="notifications-list" v-else>
        <notification-item
          v-for="notification in filteredNotifications"
          :key="notification.id"
          :notification="notification"
          @click="onNotificationClick(notification)"
          @mark-read="markAsRead(notification.id)"
        />
      </div>
    </div>
    
    <!-- Notification preferences dialog -->
    <div class="preferences-dialog" v-if="showPreferences">
      <div class="preferences-header">
        <h3>Notification Preferences</h3>
        <button class="close-button" @click="closePreferences">
          <font-awesome-icon icon="times" />
        </button>
      </div>
      
      <div class="preferences-content">
        <div class="preference-item">
          <span>Show only unread</span>
          <toggle-switch v-model="preferences.showOnlyUnread" />
        </div>
        
        <div class="preference-item">
          <span>Group by stream</span>
          <toggle-switch v-model="preferences.groupByStream" />
        </div>
        
        <div class="preference-item">
          <span>Group by type</span>
          <toggle-switch v-model="preferences.groupByType" />
        </div>
        
        <div class="preference-item">
          <span>Mute notifications</span>
          <toggle-switch v-model="preferences.muteNotifications" />
        </div>
        
        <div class="preference-item">
          <span>Notification sound</span>
          <select v-model="preferences.notificationSound" class="sound-select">
            <option value="default">Default</option>
            <option value="alert">Alert</option>
            <option value="soft">Soft</option>
            <option value="none">None</option>
          </select>
        </div>
      </div>
      
      <div class="preferences-footer">
        <button class="save-button" @click="savePreferences">
          <font-awesome-icon icon="save" />
          <span>Save preferences</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, inject } from 'vue';
import { useMobileNotifications } from '../composables/useMobileNotifications';

// NotificationItem component - inline component for simplicity
const NotificationItem = {
  name: 'NotificationItem',
  props: {
    notification: {
      type: Object,
      required: true
    }
  },
  emits: ['click', 'mark-read'],
  setup(props, { emit }) {
    const formattedTime = computed(() => {
      if (!props.notification.timestamp) return '';
      
      const date = new Date(props.notification.timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + 
             ' ' + date.toLocaleDateString();
    });
    
    const notificationIcon = computed(() => {
      switch (props.notification.event_type) {
        case 'face_detected': return 'user';
        case 'object_detected': return 'cube';
        case 'keyword_detected': return 'comment';
        case 'stream_created': return 'play-circle';
        case 'stream_ended': return 'stop-circle';
        default: return 'bell';
      }
    });
    
    const handleClick = () => {
      emit('click', props.notification);
    };
    
    const markAsRead = (event) => {
      event.stopPropagation();
      emit('mark-read', props.notification.id);
    };
    
    return {
      formattedTime,
      notificationIcon,
      handleClick,
      markAsRead
    };
  },
  template: `
    <div 
      class="notification-item" 
      :class="{ 'unread': !notification.read }"
      @click="handleClick"
    >
      <div class="notification-icon">
        <font-awesome-icon :icon="notificationIcon" />
      </div>
      <div class="notification-content">
        <div class="notification-header">
          <span class="notification-title">{{ notification.event_type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') }}</span>
          <span class="notification-time">{{ formattedTime }}</span>
        </div>
        <div class="notification-message">
          {{ notification.details?.message || 'No details available' }}
        </div>
        <div class="notification-source">
          <span>{{ notification.streamer || notification.details?.streamer_name || 'Unknown' }}</span>
          <span class="notification-platform">{{ notification.platform || notification.details?.platform || 'Unknown' }}</span>
        </div>
      </div>
      <div class="notification-actions">
        <button 
          class="read-button" 
          v-if="!notification.read"
          @click="markAsRead"
        >
          <font-awesome-icon icon="check" />
        </button>
      </div>
    </div>
  `
};

// ToggleSwitch component - inline component for simplicity
const ToggleSwitch = {
  name: 'ToggleSwitch',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const toggle = () => {
      emit('update:modelValue', !props.modelValue);
    };
    
    return {
      toggle
    };
  },
  template: `
    <div class="toggle-switch" :class="{ 'active': modelValue }" @click="toggle">
      <div class="toggle-handle"></div>
    </div>
  `
};

export default {
  name: 'MobileNotificationsPanel',
  components: {
    NotificationItem,
    ToggleSwitch
  },
  props: {
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'notification-click'],
  setup(props, { emit }) {
    // Refs
    const notificationsContainer = ref(null);
    const showPreferences = ref(false);
    const selectedType = ref('');
    
    // Inject context help function
    const analyzeContext = inject('analyzeContext', null);
    
    // Use notifications composable
    const { 
      notifications, 
      filteredNotifications, 
      unreadCount, 
      loading, 
      error,
      preferences,
      notificationTypes,
      fetchNotifications, 
      markAsRead, 
      markAllAsRead,
      updatePreferences
    } = useMobileNotifications();
    
    // Computed properties
    const hasUnread = computed(() => unreadCount.value > 0);
    const showOnlyUnread = computed(() => preferences.value.showOnlyUnread);
    const groupByType = computed(() => preferences.value.groupByType);
    const groupByStream = computed(() => preferences.value.groupByStream);
    
    // Methods
    const closePanel = () => {
      emit('close');
    };
    
    const openPreferences = () => {
      showPreferences.value = true;
      
      // Show preferences help if it's the first time
      if (analyzeContext && !localStorage.getItem('notification_preferences_viewed')) {
        analyzeContext({
          screen: 'notifications',
          action: 'preferences',
          isFirstTime: true
        });
        localStorage.setItem('notification_preferences_viewed', 'true');
      }
    };
    
    const closePreferences = () => {
      showPreferences.value = false;
    };
    
    const savePreferences = () => {
      updatePreferences(preferences.value);
      closePreferences();
      
      // Show confirmation help after saving preferences
      if (analyzeContext) {
        analyzeContext({
          screen: 'notifications',
          action: 'preferences_saved',
          preferences: {
            showOnlyUnread: preferences.value.showOnlyUnread,
            groupByType: preferences.value.groupByType,
            groupByStream: preferences.value.groupByStream,
            notificationSound: preferences.value.notificationSound
          }
        });
      }
    };
    
    const onNotificationClick = (notification) => {
      if (!notification.read) {
        markAsRead(notification.id);
      }
      emit('notification-click', notification);
    };
    
    const toggleUnreadFilter = () => {
      updatePreferences({
        showOnlyUnread: !preferences.value.showOnlyUnread
      });
      
      // Show filter help if first time using a filter
      if (analyzeContext && !localStorage.getItem('notification_filter_used')) {
        analyzeContext({
          screen: 'notifications',
          action: 'filter',
          filterType: 'unread',
          isFirstTime: true
        });
        localStorage.setItem('notification_filter_used', 'true');
      }
    };
    
    const applyTypeFilter = () => {
      updatePreferences({
        filterByType: selectedType.value
      });
      
      // Show filter help if using type filter
      if (analyzeContext && selectedType.value && !localStorage.getItem('notification_type_filter_used')) {
        analyzeContext({
          screen: 'notifications',
          action: 'filter',
          filterType: 'type',
          selectedType: selectedType.value,
          isFirstTime: true
        });
        localStorage.setItem('notification_type_filter_used', 'true');
      }
    };
    
    const formatEventType = (type) => {
      return type
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    };
    
    const refreshNotifications = () => {
      fetchNotifications();
    };
    
    // Watch for panel open/close
    watch(() => props.isOpen, (isOpen) => {
      if (isOpen) {
        // Refresh notifications when panel opens
        fetchNotifications();
        
        // Scroll to top
        if (notificationsContainer.value) {
          notificationsContainer.value.scrollTop = 0;
        }
        
        // Show context help if appropriate
        if (analyzeContext) {
          // Check if this is first time viewing notifications
          const isFirstTimeViewing = !localStorage.getItem('notifications_panel_viewed');
          
          // Provide context to help system
          analyzeContext({
            screen: 'notifications',
            action: 'view',
            isFirstTime: isFirstTimeViewing,
            isEmpty: filteredNotifications.value.length === 0
          });
          
          // Remember that notifications have been viewed
          localStorage.setItem('notifications_panel_viewed', 'true');
        }
      }
    });
    
    // Initialize
    onMounted(() => {
      if (props.isOpen) {
        fetchNotifications();
      }
    });
    
    return {
      notificationsContainer,
      notifications,
      filteredNotifications,
      loading,
      error,
      unreadCount,
      hasUnread,
      showOnlyUnread,
      groupByType,
      groupByStream,
      preferences,
      notificationTypes,
      selectedType,
      showPreferences,
      closePanel,
      closePreferences,
      openPreferences,
      savePreferences,
      onNotificationClick,
      markAsRead,
      markAllAsRead,
      toggleUnreadFilter,
      applyTypeFilter,
      formatEventType,
      refreshNotifications
    };
  }
};
</script>

<style scoped>
.notifications-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  max-width: 420px;
  background-color: var(--bs-body-bg);
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  transform: translateX(100%);
  transition: transform 0.3s ease-in-out;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.notifications-panel.active {
  transform: translateX(0);
}

.panel-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--bs-border-color);
}

.panel-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.panel-actions {
  display: flex;
  gap: 12px;
}

.panel-actions button {
  background: none;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  color: var(--bs-secondary);
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 4px;
}

.panel-actions button:hover {
  color: var(--bs-primary);
  background-color: var(--bs-secondary-bg);
}

.panel-filters {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--bs-border-color);
  gap: 8px;
}

.filter-group {
  display: flex;
  gap: 8px;
}

.filter-button {
  background-color: var(--bs-secondary-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  cursor: pointer;
}

.filter-button.active {
  background-color: var(--bs-primary);
  color: white;
  border-color: var(--bs-primary);
}

.filter-select {
  background-color: var(--bs-secondary-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 4px;
  padding: 6px 8px;
  font-size: 0.875rem;
  min-width: 120px;
}

.mark-all-button {
  background-color: var(--bs-success-bg-subtle);
  color: var(--bs-success);
  border: 1px solid var(--bs-success-border-subtle);
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  cursor: pointer;
}

.mark-all-button:hover {
  background-color: var(--bs-success);
  color: white;
}

.mark-all-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.notifications-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  gap: 12px;
  color: var(--bs-secondary);
}

.loading-indicator svg {
  font-size: 1.5rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  gap: 16px;
  text-align: center;
  color: var(--bs-secondary);
}

.empty-icon {
  font-size: 2.5rem;
  opacity: 0.5;
  margin-bottom: 8px;
}

.refresh-button {
  background-color: var(--bs-primary-bg-subtle);
  color: var(--bs-primary);
  border: 1px solid var(--bs-primary-border-subtle);
  border-radius: 4px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  cursor: pointer;
}

.refresh-button:hover {
  background-color: var(--bs-primary);
  color: white;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-group {
  background-color: var(--bs-secondary-bg-subtle);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

.group-header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  background-color: var(--bs-secondary-bg);
  border-bottom: 1px solid var(--bs-border-color);
}

.group-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  flex: 1;
}

.group-badge {
  background-color: var(--bs-tertiary-bg);
  color: var(--bs-secondary);
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 8px;
}

.group-count {
  background-color: var(--bs-primary);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  min-width: 24px;
  height: 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}

/* Toggle Switch Component */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 46px;
  height: 24px;
  background-color: var(--bs-secondary-bg);
  border-radius: 34px;
  transition: background-color 0.2s;
  cursor: pointer;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.toggle-switch.active {
  background-color: var(--bs-primary);
}

.toggle-handle {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.toggle-switch.active .toggle-handle {
  transform: translateX(22px);
}

/* Preferences Dialog */
.preferences-dialog {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: var(--bs-body-bg);
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1010;
  overflow: hidden;
  animation: slide-up 0.3s ease-out forwards;
}

@keyframes slide-up {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.preferences-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--bs-border-color);
}

.preferences-header h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.preferences-content {
  padding: 16px;
}

.preference-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--bs-border-color);
}

.preference-item:last-child {
  border-bottom: none;
}

.sound-select {
  background-color: var(--bs-secondary-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 4px;
  padding: 6px 12px;
  min-width: 120px;
}

.preferences-footer {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--bs-border-color);
}

.save-button {
  background-color: var(--bs-primary);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 10px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.save-button:hover {
  background-color: var(--bs-primary-darker, var(--bs-primary));
}

/* Notification Item Component */
:deep(.notification-item) {
  display: flex;
  padding: 12px;
  border-radius: 8px;
  background-color: var(--bs-body-bg);
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  border: 1px solid var(--bs-border-color);
}

:deep(.notification-item:hover) {
  background-color: var(--bs-secondary-bg);
}

:deep(.notification-item.unread) {
  border-left: 3px solid var(--bs-primary);
  background-color: var(--bs-primary-bg-subtle);
}

:deep(.notification-icon) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 18px;
  background-color: var(--bs-secondary-bg);
  color: var(--bs-secondary);
  margin-right: 12px;
  flex-shrink: 0;
}

:deep(.notification-item.unread .notification-icon) {
  background-color: var(--bs-primary-bg-subtle);
  color: var(--bs-primary);
}

:deep(.notification-content) {
  flex: 1;
  min-width: 0;
}

:deep(.notification-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

:deep(.notification-title) {
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.notification-time) {
  font-size: 0.75rem;
  color: var(--bs-secondary);
  white-space: nowrap;
  margin-left: 8px;
}

:deep(.notification-message) {
  font-size: 0.875rem;
  margin-bottom: 4px;
  word-break: break-word;
}

:deep(.notification-source) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  color: var(--bs-secondary);
}

:deep(.notification-platform) {
  background-color: var(--bs-secondary-bg);
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: capitalize;
}

:deep(.notification-actions) {
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-left: 8px;
}

:deep(.read-button) {
  background: none;
  border: none;
  color: var(--bs-secondary);
  transition: color 0.2s;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 15px;
}

:deep(.read-button:hover) {
  color: var(--bs-primary);
  background-color: var(--bs-primary-bg-subtle);
}

/* Media queries */
@media (max-width: 420px) {
  .notifications-panel {
    max-width: 100%;
  }
}
</style>