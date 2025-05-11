import { ref } from 'vue';
import axios from 'axios';

/**
 * Composable to manage notifications
 * @param {string} apiUrl - The API URL to fetch notifications from
 * @returns {Object} - Notification related data and methods
 */
export function useNotifications(apiUrl = '/api/notifications') {
  const notifications = ref([]);
  const loading = ref(false);
  const error = ref(null);

  /**
   * Fetch notifications from the API
   */
  const fetchNotifications = async () => {
    try {
      loading.value = true;
      error.value = null;
      
      const response = await axios.get(apiUrl);
      notifications.value = response.data;
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
      error.value = 'Failed to load notifications. Please try again.';
    } finally {
      loading.value = false;
    }
  };

  /**
   * Mark a notification as read
   * @param {number} id - Notification ID
   */
  const markAsRead = async (id) => {
    try {
      await axios.put(`${apiUrl}/${id}/read`);
      
      // Update local state
      const notification = notifications.value.find(n => n.id === id);
      if (notification) {
        notification.read = true;
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
      throw err;
    }
  };

  /**
   * Mark all notifications as read
   */
  const markAllAsRead = async () => {
    try {
      await axios.put(`${apiUrl}/read-all`);
      
      // Update local state
      notifications.value.forEach(n => {
        n.read = true;
      });
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
      throw err;
    }
  };

  /**
   * Delete a notification
   * @param {number} id - Notification ID
   */
  const deleteNotification = async (id) => {
    try {
      await axios.delete(`${apiUrl}/${id}`);
      
      // Update local state
      notifications.value = notifications.value.filter(n => n.id !== id);
    } catch (err) {
      console.error('Failed to delete notification:', err);
      throw err;
    }
  };

  /**
   * Delete all notifications
   */
  const deleteAllNotifications = async () => {
    try {
      await axios.delete(apiUrl);
      
      // Update local state
      notifications.value = [];
    } catch (err) {
      console.error('Failed to delete all notifications:', err);
      throw err;
    }
  };

  /**
   * Create a new notification
   * @param {Object} notification - Notification data
   */
  const createNotification = async (notification) => {
    try {
      const response = await axios.post(apiUrl, notification);
      
      // Add the new notification to the local state
      if (response.data && response.data.notification) {
        notifications.value.unshift(response.data.notification);
      }
      
      return response.data;
    } catch (err) {
      console.error('Failed to create notification:', err);
      throw err;
    }
  };

  /**
   * Update an existing notification
   * @param {number} id - Notification ID
   * @param {Object} data - Updated notification data
   */
  const updateNotification = async (id, data) => {
    try {
      const response = await axios.put(`${apiUrl}/${id}`, data);
      
      // Update the notification in the local state
      const index = notifications.value.findIndex(n => n.id === id);
      if (index !== -1 && response.data && response.data.notification) {
        notifications.value[index] = response.data.notification;
      }
      
      return response.data;
    } catch (err) {
      console.error('Failed to update notification:', err);
      throw err;
    }
  };

  /**
   * Forward a notification to an agent
   * @param {number} id - Notification ID
   * @param {number} agentId - Agent ID
   */
  const forwardNotification = async (id, agentId) => {
    try {
      const response = await axios.post(`${apiUrl}/${id}/forward`, { agent_id: agentId });
      
      // Update the notification in the local state if needed
      // This depends on what the API returns
      
      return response.data;
    } catch (err) {
      console.error('Failed to forward notification:', err);
      throw err;
    }
  };

  return {
    notifications,
    loading,
    error,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    deleteAllNotifications,
    createNotification,
    updateNotification,
    forwardNotification
  };
}