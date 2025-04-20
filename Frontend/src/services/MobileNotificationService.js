/**
 * MobileNotificationService
 * Optimized notification service for mobile views with reduced data transfer
 * and battery-friendly caching and background refresh policies.
 */
import axios from 'axios';
import { ref, computed } from 'vue';
import { useToast } from 'vue-toastification';

class MobileNotificationService {
  constructor() {
    // Private reactive data
    this._notifications = ref([]);
    this._loading = ref(false);
    this._error = ref(null);
    this._groupByType = ref(false);
    this._groupByStream = ref(false);
    this._lastRefresh = ref(Date.now());
    this._refreshInterval = 60000; // 1 minute refresh by default
    this._toast = useToast();
    
    // Initialize background refresh
    this._setupBackgroundRefresh();
  }
  
  /**
   * Get all notifications with optional filtering
   * @param {Object} options - Filter options
   * @param {boolean} [options.onlyUnread=false] - Only return unread notifications
   * @param {boolean} [options.forceRefresh=false] - Force network refresh
   * @returns {Promise<Array>} - Array of notifications
   */
  async getNotifications({ onlyUnread = false, forceRefresh = false } = {}) {
    try {
      // Check cache first unless force refresh
      const timeSinceLastRefresh = Date.now() - this._lastRefresh.value;
      if (this._notifications.value.length > 0 && 
          !forceRefresh && 
          timeSinceLastRefresh < this._refreshInterval) {
        console.log('Using cached notifications');
        return this._filterNotifications(onlyUnread);
      }
      
      this._loading.value = true;
      
      // Fetch mobile-optimized notification data
      const response = await axios.get('/api/notifications');
      
      if (response.data.success) {
        // Update cache
        this._notifications.value = response.data.notifications;
        this._lastRefresh.value = Date.now();
        this._error.value = null;
      } else {
        this._error.value = response.data.message || 'Failed to load notifications';
        this._toast.error(this._error.value);
      }
      
      return this._filterNotifications(onlyUnread);
    } catch (error) {
      this._error.value = error.message || 'Failed to load notifications';
      this._toast.error(this._error.value);
      return [];
    } finally {
      this._loading.value = false;
    }
  }
  
  /**
   * Filter notifications based on read status
   * @private
   * @param {boolean} onlyUnread - Only return unread notifications
   * @returns {Array} - Filtered notifications
   */
  _filterNotifications(onlyUnread) {
    if (onlyUnread) {
      return this._notifications.value.filter(n => !n.read);
    }
    return this._notifications.value;
  }
  
  /**
   * Mark a notification as read
   * @param {number} notificationId - ID of notification to mark as read
   * @returns {Promise<boolean>} - Success status
   */
  async markAsRead(notificationId) {
    try {
      const response = await axios.put(`/api/notifications/${notificationId}/read`);
      
      if (response.data.success) {
        // Update cache
        const notification = this._notifications.value.find(n => n.id === notificationId);
        if (notification) {
          notification.read = true;
        }
        return true;
      } else {
        this._toast.error(response.data.message || 'Failed to mark notification as read');
        return false;
      }
    } catch (error) {
      this._toast.error(error.message || 'Failed to mark notification as read');
      return false;
    }
  }
  
  /**
   * Mark all notifications as read
   * @returns {Promise<boolean>} - Success status
   */
  async markAllAsRead() {
    try {
      const response = await axios.put('/api/notifications/read-all');
      
      if (response.data.success) {
        // Update cache
        this._notifications.value.forEach(n => n.read = true);
        return true;
      } else {
        this._toast.error(response.data.message || 'Failed to mark all notifications as read');
        return false;
      }
    } catch (error) {
      this._toast.error(error.message || 'Failed to mark all notifications as read');
      return false;
    }
  }
  
  /**
   * Get unread notification count
   * @returns {Promise<number>} - Count of unread notifications
   */
  async getUnreadCount() {
    try {
      const response = await axios.get('/api/notifications/unread/count');
      
      if (response.data.success) {
        return response.data.count || 0;
      } else {
        console.error(response.data.message || 'Failed to get unread count');
        return 0;
      }
    } catch (error) {
      console.error(error.message || 'Failed to get unread count');
      return 0;
    }
  }
  
  /**
   * Toggle grouping by notification type
   */
  toggleGroupByType() {
    this._groupByType.value = !this._groupByType.value;
    
    // Can't group by both type and stream simultaneously
    if (this._groupByType.value) {
      this._groupByStream.value = false;
    }
  }
  
  /**
   * Toggle grouping by stream
   */
  toggleGroupByStream() {
    this._groupByStream.value = !this._groupByStream.value;
    
    // Can't group by both type and stream simultaneously
    if (this._groupByStream.value) {
      this._groupByType.value = false;
    }
  }
  
  /**
   * Group notifications by type or stream
   * @returns {Object} - Grouped notifications
   */
  getGroupedNotifications() {
    const notifications = this._notifications.value;
    
    if (this._groupByType.value) {
      return this._groupByNotificationType(notifications);
    } else if (this._groupByStream.value) {
      return this._groupByStreamSource(notifications);
    } else {
      return { 'All Notifications': notifications };
    }
  }
  
  /**
   * Group notifications by type
   * @private
   * @param {Array} notifications - Notifications to group
   * @returns {Object} - Grouped notifications
   */
  _groupByNotificationType(notifications) {
    const groups = {};
    
    notifications.forEach(notification => {
      const type = notification.event_type || 'Other';
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(notification);
    });
    
    return groups;
  }
  
  /**
   * Group notifications by stream source
   * @private
   * @param {Array} notifications - Notifications to group
   * @returns {Object} - Grouped notifications
   */
  _groupByStreamSource(notifications) {
    const groups = {};
    
    notifications.forEach(notification => {
      const streamer = notification.streamer_username || 
                      (notification.details?.streamer_username) || 
                      'Unknown Source';
      if (!groups[streamer]) {
        groups[streamer] = [];
      }
      groups[streamer].push(notification);
    });
    
    return groups;
  }
  
  /**
   * Set up background refresh for notifications
   * @private
   */
  _setupBackgroundRefresh() {
    setInterval(async () => {
      // Only auto-refresh if the user is likely active
      const timeSinceLastRefresh = Date.now() - this._lastRefresh.value;
      if (timeSinceLastRefresh > this._refreshInterval && document.visibilityState === 'visible') {
        console.log('Background refresh of notifications');
        await this.getNotifications({ forceRefresh: true });
      }
    }, this._refreshInterval);
  }
  
  // Expose reactive properties
  get notifications() {
    return this._notifications;
  }
  
  get loading() {
    return this._loading;
  }
  
  get error() {
    return this._error;
  }
  
  get groupByType() {
    return this._groupByType;
  }
  
  get groupByStream() {
    return this._groupByStream;
  }
  
  get groupedNotifications() {
    return computed(() => this.getGroupedNotifications());
  }
  
  get unreadCount() {
    return computed(() => 
      this._notifications.value.filter(n => !n.read).length
    );
  }
}

// Create singleton instance
const service = new MobileNotificationService();
export default service;