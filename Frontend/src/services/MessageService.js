/**
 * Message Service for handling messaging functionality
 * This service provides methods for sending and receiving messages,
 * managing conversations, and handling real-time messaging features.
 */

import axios from 'axios';

class MessageService {
  /**
   * Send a message to another user
   * @param {Object} messageData - The message data
   * @param {number} messageData.receiver_id - The ID of the receiver
   * @param {string} messageData.message - The message content
   * @param {number} [messageData.attachment_id] - Optional attachment ID
   * @returns {Promise} - Promise with the sent message
   */
  async sendMessage(messageData) {
    try {
      const response = await axios.post('/api/messages/send', messageData);
      return response;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }

  /**
   * Get messages between the current user and another user
   * @param {number} userId - The ID of the other user
   * @returns {Promise} - Promise with the messages
   */
  async getMessages(userId) {
    try {
      const response = await axios.get(`/api/messages/${userId}`);
      return response;
    } catch (error) {
      console.error('Error getting messages:', error);
      throw error;
    }
  }

  /**
   * Get online users
   * @returns {Promise} - Promise with the online users
   */
  async getOnlineUsers() {
    try {
      const response = await axios.get('/api/messages/online-users');
      return response;
    } catch (error) {
      console.error('Error getting online users:', error);
      throw error;
    }
  }

  /**
   * Mark all messages from a specific user as read
   * @param {number} userId - The ID of the user whose messages to mark as read
   * @returns {Promise} - Promise with the result
   */
  async markMessagesRead(userId) {
    try {
      const response = await axios.post('/api/messages/mark-read', { user_id: userId });
      return response;
    } catch (error) {
      console.error('Error marking messages as read:', error);
      throw error;
    }
  }

  /**
   * Mark a single message as read
   * @param {number} messageId - The ID of the message to mark as read
   * @returns {Promise} - Promise with the result
   */
  async markMessageRead(messageId) {
    try {
      const response = await axios.post(`/api/messages/mark-message-read/${messageId}`);
      return response;
    } catch (error) {
      console.error('Error marking message as read:', error);
      throw error;
    }
  }

  /**
   * Get the count of unread messages from a specific user
   * @param {number} userId - The ID of the user
   * @returns {Promise} - Promise with the count
   */
  async getUnreadCount(userId) {
    try {
      const response = await axios.get(`/api/messages/unread-count/${userId}`);
      return response;
    } catch (error) {
      console.error('Error getting unread count:', error);
      throw error;
    }
  }

  /**
   * Get the total count of all unread messages
   * @returns {Promise} - Promise with the count
   */
  async getTotalUnreadCount() {
    try {
      const response = await axios.get('/api/messages/total-unread-count');
      return response;
    } catch (error) {
      console.error('Error getting total unread count:', error);
      throw error;
    }
  }

  /**
   * Get the latest conversations with the last message for each
   * @returns {Promise} - Promise with the conversations
   */
  async getLatestConversations() {
    try {
      const response = await axios.get('/api/messages/latest-conversations');
      return response;
    } catch (error) {
      console.error('Error getting latest conversations:', error);
      throw error;
    }
  }

  /**
   * Upload a file attachment
   * @param {FormData} formData - The form data with the file
   * @returns {Promise} - Promise with the uploaded attachment
   */
  async uploadAttachment(formData) {
    try {
      const response = await axios.post('/api/messages/upload-attachment', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response;
    } catch (error) {
      console.error('Error uploading attachment:', error);
      throw error;
    }
  }
}

export default new MessageService();