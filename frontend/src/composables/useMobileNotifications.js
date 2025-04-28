/**
 * Mobile Notifications Composable
 * 
 * Provides a reactive interface for working with notifications in mobile views
 * Features:
 * - Real-time notification updates
 * - Notification filtering and grouping
 * - Read status management
 * - Notification preferences
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import axios from 'axios';
import { useToast } from 'vue-toastification';
import io from 'socket.io-client';
import { formatDistance } from 'date-fns';

export function useMobileNotifications() {
  // State
  const notifications = ref([]);
  const filteredNotifications = ref([]);
  const unreadCount = ref(0);
  const loading = ref(false);
  const error = ref(null);
  const socket = ref(null);
  const preferences = ref({
    showOnlyUnread: false,
    filterByType: null,
    groupByStream: false,
    groupByType: false,
    muteNotifications: false,
    notificationSound: 'default'
  });
  
  // Toast for notifications
  const toast = useToast();
  
  // Load user preferences from localStorage
  const loadPreferences = () => {
    try {
      const savedPrefs = localStorage.getItem('notificationPreferences');
      if (savedPrefs) {
        preferences.value = { ...preferences.value, ...JSON.parse(savedPrefs) };
      }
    } catch (e) {
      console.error('Failed to load notification preferences', e);
    }
  };
  
  // Save user preferences to localStorage
  const savePreferences = () => {
    try {
      localStorage.setItem('notificationPreferences', JSON.stringify(preferences.value));
    } catch (e) {
      console.error('Failed to save notification preferences', e);
    }
  };
  
  // Connect to Socket.IO for real-time notifications
  const connectSocket = () => {
  socket.value = io('https://54.86.99.85:5000', {
    path: '/ws',
    transports: ['websocket', 'polling'],
    secure: true
  });
    
    socket.value.on('notification', (notification) => {
      handleNewNotification(notification);
    });
    
    socket.value.on('notification_update', (data) => {
      if (data.action === 'read' || data.action === 'updated') {
        updateNotificationStatus(data.notification_id, data.action === 'read');
      } else if (data.action === 'deleted') {
        removeNotification(data.notification_id);
      }
    });
  };
  
  // Disconnect Socket.IO
  const disconnectSocket = () => {
    if (socket.value) {
      socket.value.disconnect();
      socket.value = null;
    }
  };
  
  // Handle a new notification
  const handleNewNotification = (notification) => {
    // Check if notification already exists to avoid duplicates
    const exists = notifications.value.some(n => n.id === notification.id);
    if (!exists) {
      notifications.value.unshift(notification);
      
      // Update unread count
      if (!notification.read) {
        unreadCount.value++;
      }
      
      // Apply filters
      applyFilters();
      
      // Show toast notification if not muted
      if (!preferences.value.muteNotifications) {
        showNotificationToast(notification);
      }
      
      // Play sound if enabled
      if (preferences.value.notificationSound !== 'none') {
        playNotificationSound(preferences.value.notificationSound);
      }
    }
  };
  
  // Show toast notification
  const showNotificationToast = (notification) => {
    const title = getNotificationTitle(notification);
    const message = getNotificationMessage(notification);
    
    toast.info(
      `<div><strong>${title}</strong><br>${message}</div>`, 
      { timeout: 5000, position: 'bottom-right' }
    );
  };
  
  // Get notification title based on event type
  const getNotificationTitle = (notification) => {
    switch (notification.event_type) {
      case 'face_detected':
        return 'Face Detected';
      case 'object_detected':
        return 'Object Detected';
      case 'keyword_detected':
        return 'Keyword Detected';
      case 'stream_created':
        return 'Stream Started';
      case 'stream_ended':
        return 'Stream Ended';
      default:
        return notification.event_type
          .split('_')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
    }
  };
  
  // Get notification icon based on event type
  const getNotificationIcon = (notification) => {
    switch (notification.event_type) {
      case 'face_detected':
        return 'user';
      case 'object_detected':
        return 'box';
      case 'keyword_detected':
        return 'comment';
      case 'stream_created':
        return 'video';
      case 'stream_ended':
        return 'video-slash';
      case 'assignment_changed':
        return 'exchange-alt';
      case 'system_alert':
        return 'exclamation-triangle';
      default:
        return 'bell';
    }
  };
  
  // Get notification color based on event type
  const getNotificationColor = (notification) => {
    switch (notification.event_type) {
      case 'face_detected':
        return '#4caf50'; // green
      case 'object_detected':
        return '#2196f3'; // blue
      case 'keyword_detected':
        return '#ff9800'; // orange
      case 'stream_created':
        return '#9c27b0'; // purple
      case 'stream_ended':
        return '#f44336'; // red
      case 'assignment_changed':
        return '#00bcd4'; // cyan
      case 'system_alert':
        return '#ff5722'; // deep orange
      default:
        return '#607d8b'; // blue grey
    }
  };
  
  // Format time as relative time ago (e.g. "5 minutes ago")
  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Unknown';
    
    try {
      const date = new Date(timestamp);
      return formatDistance(date, new Date(), { addSuffix: true });
    } catch (e) {
      console.error('Error formatting date:', e);
      return 'Unknown';
    }
  };
  
  // Get notification message based on details
  const getNotificationMessage = (notification) => {
    const details = notification.details || {};
    const streamer = details.streamer_name || notification.streamer || 'Unknown';
    
    // Format message based on event type
    switch (notification.event_type) {
      case 'face_detected':
        return `Face detected in ${streamer}'s stream with ${Math.round((details.confidence || 0) * 100)}% confidence`;
      case 'object_detected':
        return `${details.name || 'Object'} detected in ${streamer}'s stream`;
      case 'keyword_detected':
        return `"${details.keyword || 'Keyword'}" found in ${streamer}'s chat`;
      case 'stream_created':
        return `${streamer} started streaming on ${details.platform || 'platform'}`;
      case 'stream_ended':
        return `${streamer}'s stream has ended`;
      default:
        return details.message || `Notification from ${streamer}'s stream`;
    }
  };
  
  // Play notification sound
  const playNotificationSound = (soundType) => {
    let soundUrl = '';
    
    switch (soundType) {
      case 'default':
        soundUrl = '/assets/sounds/notification.mp3';
        break;
      case 'alert':
        soundUrl = '/assets/sounds/alert.mp3';
        break;
      case 'soft':
        soundUrl = '/assets/sounds/soft.mp3';
        break;
      default:
        soundUrl = '/assets/sounds/notification.mp3';
    }
    
    try {
      const audio = new Audio(soundUrl);
      audio.play().catch(e => console.warn('Could not play notification sound', e));
    } catch (e) {
      console.warn('Sound playback not supported', e);
    }
  };
  
  // Update notification read status
  const updateNotificationStatus = (notificationId, isRead = true) => {
    const notification = notifications.value.find(n => n.id === notificationId);
    if (notification) {
      const wasUnread = !notification.read;
      notification.read = isRead;
      
      // Update unread count
      if (wasUnread && isRead) {
        unreadCount.value = Math.max(0, unreadCount.value - 1);
      }
      
      // Apply filters
      applyFilters();
    }
  };
  
  // Remove notification
  const removeNotification = (notificationId) => {
    const index = notifications.value.findIndex(n => n.id === notificationId);
    if (index !== -1) {
      // Update unread count if removing an unread notification
      if (!notifications.value[index].read) {
        unreadCount.value = Math.max(0, unreadCount.value - 1);
      }
      
      // Remove notification
      notifications.value.splice(index, 1);
      
      // Apply filters
      applyFilters();
    }
  };
  
  // Apply filters based on preferences
  const applyFilters = () => {
    let result = [...notifications.value];
    
    // Filter by read status
    if (preferences.value.showOnlyUnread) {
      result = result.filter(n => !n.read);
    }
    
    // Filter by event type
    if (preferences.value.filterByType) {
      result = result.filter(n => n.event_type === preferences.value.filterByType);
    }
    
    // Group by stream if enabled
    if (preferences.value.groupByStream) {
      // Group notifications by room_url
      const grouped = {};
      result.forEach(notification => {
        const key = notification.room_url;
        if (!grouped[key]) {
          grouped[key] = {
            room_url: notification.room_url,
            streamer: notification.details?.streamer_name || notification.streamer || 'Unknown',
            platform: notification.details?.platform || 'Unknown',
            notifications: []
          };
        }
        grouped[key].notifications.push(notification);
      });
      
      // Convert back to array for rendering
      filteredNotifications.value = Object.values(grouped);
      return;
    }
    
    // Group by event type if enabled
    if (preferences.value.groupByType) {
      // Group notifications by event_type
      const grouped = {};
      result.forEach(notification => {
        const key = notification.event_type;
        if (!grouped[key]) {
          grouped[key] = {
            event_type: notification.event_type,
            title: getNotificationTitle(notification),
            notifications: []
          };
        }
        grouped[key].notifications.push(notification);
      });
      
      // Convert back to array for rendering
      filteredNotifications.value = Object.values(grouped);
      return;
    }
    
    // If no grouping, just use the filtered list
    filteredNotifications.value = result;
  };
  
  // Fetch notifications from API
  const fetchNotifications = async () => {
    loading.value = true;
    error.value = null;
    
    try {
      // Use the agent notifications endpoint from the documentation
      const response = await axios.get('/api/notifications');
      
      if (response.data) {
        notifications.value = response.data;
        
        // Count unread notifications
        unreadCount.value = notifications.value.filter(n => !n.read).length;
        
        // Apply filters
        applyFilters();
      }
    } catch (err) {
      console.error('Failed to fetch notifications', err);
      error.value = 'Failed to load notifications';
      toast.error('Failed to load notifications');
    } finally {
      loading.value = false;
    }
  };
  
  // Mark a notification as read
  const markAsRead = async (notificationId) => {
    try {
      // Use the correct endpoint from the documentation
      await axios.put(`/api/notifications/${notificationId}/read`);
      updateNotificationStatus(notificationId, true);
    } catch (err) {
      console.error('Failed to mark notification as read', err);
      toast.error('Failed to update notification');
    }
  };
  
  // Mark all notifications as read
  const markAllAsRead = async () => {
    try {
      // Use the correct endpoint from the documentation
      await axios.put('/api/notifications/read-all');
      
      // Update all notifications in local state
      notifications.value.forEach(n => {
        n.read = true;
      });
      
      // Reset unread count
      unreadCount.value = 0;
      
      // Apply filters
      applyFilters();
      
      toast.success('All notifications marked as read');
    } catch (err) {
      console.error('Failed to mark all notifications as read', err);
      toast.error('Failed to update notifications');
    }
  };
  
  // Delete a notification
  // Note: The API documentation doesn't specify a delete endpoint for notifications,
  // but we'll keep this method in case it's implemented in the future
  const deleteNotification = async (notificationId) => {
    try {
      // This is a placeholder. The API doesn't have a documented endpoint for deleting
      // notifications, so we should confirm with backend team if this is supported
      await axios.delete(`/api/notifications/${notificationId}`);
      removeNotification(notificationId);
      toast.success('Notification deleted');
    } catch (err) {
      console.error('Failed to delete notification', err);
      toast.error('Failed to delete notification');
    }
  };
  
  // Get notification types for filter dropdown
  const notificationTypes = computed(() => {
    const types = new Set();
    notifications.value.forEach(n => {
      types.add(n.event_type);
    });
    return Array.from(types).sort();
  });
  
  // Get streams for filter dropdown
  const notificationStreams = computed(() => {
    const streams = new Set();
    notifications.value.forEach(n => {
      if (n.room_url) {
        streams.add(n.room_url);
      }
    });
    return Array.from(streams).sort();
  });
  
  // Update notification preferences
  const updatePreferences = (newPreferences) => {
    preferences.value = { ...preferences.value, ...newPreferences };
    savePreferences();
    applyFilters();
  };
  
  // Initialize
  onMounted(() => {
    loadPreferences();
    fetchNotifications();
    connectSocket();
    
    // Apply filters whenever preferences change
    watch(preferences, () => {
      applyFilters();
    }, { deep: true });
  });
  
  // Clean up
  onUnmounted(() => {
    disconnectSocket();
  });
  
  return {
    // State
    notifications,
    filteredNotifications,
    unreadCount,
    loading,
    error,
    preferences,
    
    // Getters
    notificationTypes,
    notificationStreams,
    
    // Actions
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    updatePreferences,
    getNotificationTitle,
    getNotificationMessage,
    getNotificationIcon,
    getNotificationColor,
    formatTimeAgo
  };
}