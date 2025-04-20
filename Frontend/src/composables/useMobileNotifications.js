/**
 * Mobile-optimized notifications composable
 * Uses MobileNotificationService for a more efficient implementation
 * specifically for mobile devices
 */
import { ref, computed, onMounted } from 'vue';
import MobileNotificationService from '../services/MobileNotificationService';

export function useMobileNotifications() {
  // Local reactive state
  const loading = ref(false);
  const error = ref(null);
  
  // Computed properties from service
  const notifications = computed(() => MobileNotificationService.notifications.value);
  const unreadCount = computed(() => MobileNotificationService.unreadCount.value);
  const groupedNotifications = computed(() => MobileNotificationService.groupedNotifications.value);
  const isGroupedByType = computed(() => MobileNotificationService.groupByType.value);
  const isGroupedByStream = computed(() => MobileNotificationService.groupByStream.value);
  
  /**
   * Load notifications from server
   * @param {Object} options - Options for loading notifications
   * @param {boolean} [options.onlyUnread=false] - Only load unread notifications
   * @param {boolean} [options.forceRefresh=false] - Force a refresh from server
   * @returns {Promise<Array>} - Array of notifications
   */
  const loadNotifications = async ({ onlyUnread = false, forceRefresh = false } = {}) => {
    loading.value = true;
    try {
      const result = await MobileNotificationService.getNotifications({ 
        onlyUnread, 
        forceRefresh 
      });
      error.value = MobileNotificationService.error.value;
      return result;
    } catch (err) {
      error.value = err.message || 'Failed to load notifications';
      return [];
    } finally {
      loading.value = false;
    }
  };
  
  /**
   * Mark a notification as read
   * @param {number} notificationId - ID of notification to mark as read
   * @returns {Promise<boolean>} - Success status
   */
  const markAsRead = async (notificationId) => {
    return await MobileNotificationService.markAsRead(notificationId);
  };
  
  /**
   * Mark all notifications as read
   * @returns {Promise<boolean>} - Success status
   */
  const markAllAsRead = async () => {
    return await MobileNotificationService.markAllAsRead();
  };
  
  /**
   * Toggle grouping notifications by type
   */
  const toggleGroupByType = () => {
    MobileNotificationService.toggleGroupByType();
  };
  
  /**
   * Toggle grouping notifications by stream
   */
  const toggleGroupByStream = () => {
    MobileNotificationService.toggleGroupByStream();
  };
  
  /**
   * Get count of unread notifications
   * @returns {Promise<number>} - Count of unread notifications
   */
  const getUnreadCount = async () => {
    return await MobileNotificationService.getUnreadCount();
  };
  
  /**
   * Format notification timestamp relative to now (e.g. "5 min ago")
   * @param {string|Date} timestamp - Timestamp to format
   * @returns {string} - Formatted timestamp
   */
  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return '';
    
    const now = new Date();
    const date = new Date(timestamp);
    const seconds = Math.floor((now - date) / 1000);
    
    // Return different formats based on how long ago
    if (seconds < 60) {
      return 'just now';
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      return `${minutes} min ago`;
    } else if (seconds < 86400) {
      const hours = Math.floor(seconds / 3600);
      return `${hours} hr ago`;
    } else if (seconds < 604800) {
      const days = Math.floor(seconds / 86400);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else {
      // Just return the date for older notifications
      return date.toLocaleDateString(undefined, { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };
  
  /**
   * Get notification icon based on type
   * @param {Object} notification - Notification object
   * @returns {string} - Icon name
   */
  const getNotificationIcon = (notification) => {
    if (!notification) return 'bell';
    
    // Get appropriate icon for different notification types
    const eventType = notification.event_type || '';
    
    switch (eventType.toLowerCase()) {
      case 'keyword_detected': {
        return 'comment-dots';
      }
      case 'object_detected': {
        return 'eye';
      }
      case 'stream_ended': {
        return 'video-slash';
      }
      case 'stream_started': {
        return 'video';
      }
      case 'assignment_created': {
        return 'user-check';
      }
      case 'assignment_removed': {
        return 'user-times';
      }
      default: {
        return 'bell';
      }
    }
  };
  
  /**
   * Get notification color based on type
   * @param {Object} notification - Notification object
   * @returns {string} - CSS color variable
   */
  const getNotificationColor = (notification) => {
    if (!notification) return 'var(--light-primary)';
    
    // Get appropriate color for different notification types
    const eventType = notification.event_type || '';
    
    switch (eventType.toLowerCase()) {
      case 'keyword_detected': {
        return 'var(--light-danger)';
      }
      case 'object_detected': {
        return 'var(--light-warning)';
      }
      case 'stream_ended': {
        return 'var(--light-secondary)';
      }
      case 'stream_started': {
        return 'var(--light-success)';
      }
      case 'assignment_created': {
        return 'var(--light-info)';
      }
      case 'assignment_removed': {
        return 'var(--light-danger)';
      }
      default: {
        return 'var(--light-primary)';
      }
    }
  };
  
  /**
   * Get human-readable notification title
   * @param {Object} notification - Notification object
   * @returns {string} - Formatted title
   */
  const getNotificationTitle = (notification) => {
    if (!notification) return 'Notification';
    
    // Get appropriate title for different notification types
    const eventType = notification.event_type || '';
    const streamer = notification.streamer_username || 
                    notification.details?.streamer_username || 
                    'Unknown';
    
    switch (eventType.toLowerCase()) {
      case 'keyword_detected': {
        return `Keyword detected in ${streamer}'s chat`;
      }
      case 'object_detected': {
        // Include object name if available
        const objectName = notification.details?.object_name || 'Object';
        return `${objectName} detected in ${streamer}'s stream`;
      }
      case 'stream_ended': {
        return `${streamer}'s stream ended`;
      }
      case 'stream_started': {
        return `${streamer} started streaming`;
      }
      case 'assignment_created': {
        return `You were assigned to monitor ${streamer}`;
      }
      case 'assignment_removed': {
        return `You were unassigned from ${streamer}`;
      }
      default: {
        return notification.message || 'New notification';
      }
    }
  };
  
  // Initialize on mount
  onMounted(async () => {
    await loadNotifications();
    await getUnreadCount();
  });
  
  return {
    // State
    notifications,
    loading,
    error,
    unreadCount,
    groupedNotifications,
    isGroupedByType,
    isGroupedByStream,
    
    // Actions
    loadNotifications,
    markAsRead,
    markAllAsRead,
    toggleGroupByType,
    toggleGroupByStream,
    getUnreadCount,
    
    // Helpers
    formatTimeAgo,
    getNotificationIcon,
    getNotificationColor,
    getNotificationTitle
  };
}