/**
 * Message Service
 * Handles all messaging functionality with optimized endpoints for mobile
 */
import axios from 'axios';
import { ref, computed } from 'vue';
import { useToast } from 'vue-toastification';
import io from 'socket.io-client';

class MessageService {
  constructor() {
    // Private reactive state
    this._conversations = ref([]);
    this._activeConversation = ref(null);
    this._messages = ref([]);
    this._loading = ref(false);
    this._sending = ref(false);
    this._error = ref(null);
    this._unreadCount = ref(0);
    this._onlineUsers = ref([]);
    this._toast = useToast();
    
    // Socket.IO connection
    this._socket = null;
    this._setupSocketConnection();
  }
  
  /**
   * Set up Socket.IO connection for real-time messaging
   * @private
   */
  _setupSocketConnection() {
    this._socket = io('https://54.86.99.85:8080', { 
      path: '/ws',
      transports: ['websocket', 'polling'] // Optional: match server config
    });
    
    // Listen for message events
    this._socket.on('new_message', (message) => {
      this._handleNewMessage(message);
    });
    
    // Listen for read status events
    this._socket.on('message_read', (data) => {
      this._handleMessageRead(data);
    });
    
    // Listen for typing events
    this._socket.on('typing', (data) => {
      // Emit typing event for components to handle
      document.dispatchEvent(new CustomEvent('message:typing', { detail: data }));
    });
    
    // Listen for online status changes
    this._socket.on('user_status', (data) => {
      this._updateUserStatus(data);
    });
  }
  
  /**
   * Handle incoming new message
   * @private
   */
  _handleNewMessage(message) {
    // Check if this is a new conversation
    const existingConversation = this._conversations.value.find(c => 
      c.userId === message.sender_id || c.userId === message.receiver_id
    );
    
    if (!existingConversation) {
      // Create a new conversation and fetch user details
      this.getOnlineUsers().then(() => {
        const otherUserId = message.sender_id === this.currentUserId ? message.receiver_id : message.sender_id;
        const user = this._onlineUsers.value.find(u => u.id === otherUserId);
        
        if (user) {
          this._conversations.value.push({
            userId: user.id,
            username: user.username,
            lastMessage: message.message,
            timestamp: message.timestamp,
            unread: message.receiver_id === this.currentUserId && !message.read ? 1 : 0,
            online: user.online
          });
        }
      });
    } else {
      // Update existing conversation
      existingConversation.lastMessage = message.message;
      existingConversation.timestamp = message.timestamp;
      if (message.receiver_id === this.currentUserId && !message.read) {
        existingConversation.unread++;
      }
    }
    
    // Update unread count total
    if (message.receiver_id === this.currentUserId && !message.read) {
      this._unreadCount.value++;
    }
    
    // Add to current conversation if active
    if (this._activeConversation.value) {
      const isActiveConversation = 
        (message.sender_id === this._activeConversation.value.userId && message.receiver_id === this.currentUserId) || 
        (message.receiver_id === this._activeConversation.value.userId && message.sender_id === this.currentUserId);
      
      if (isActiveConversation) {
        this._messages.value.push(message);
        
        // Automatically mark as read if we're the receiver
        if (message.receiver_id === this.currentUserId && !message.read) {
          this.markMessageRead(message.id);
        }
      }
    }
  }
  
  /**
   * Handle message read status update
   * @private
   */
  _handleMessageRead(data) {
    const { message_id, user_id } = data;
    
    // Update message in current conversation
    const message = this._messages.value.find(m => m.id === message_id);
    if (message) {
      message.read = true;
    }
    
    // Update unread count in conversation list
    const conversation = this._conversations.value.find(c => c.userId === user_id);
    if (conversation && conversation.unread > 0) {
      conversation.unread--;
    }
    
    // Update total unread count
    if (this._unreadCount.value > 0) {
      this._unreadCount.value--;
    }
  }
  
  /**
   * Update online status of a user
   * @private
   */
  _updateUserStatus(data) {
    const { user_id, online } = data;
    
    // Update in online users list
    const user = this._onlineUsers.value.find(u => u.id === user_id);
    if (user) {
      user.online = online;
    }
    
    // Update in conversation list
    const conversation = this._conversations.value.find(c => c.userId === user_id);
    if (conversation) {
      conversation.online = online;
    }
  }
  
  /**
   * Get current user ID from localStorage
   * @private
   */
  get currentUserId() {
    return localStorage.getItem('userId');
  }
  
  /**
   * Get all conversations for the current user
   * @returns {Promise<Array>}
   */
  async getConversations() {
    if (this._loading.value) return this._conversations.value;
    
    this._loading.value = true;
    try {
      // First get online users to have user data
      await this.getOnlineUsers();
      
      // Then we need to build conversations from messages
      // Since there's no direct endpoint for conversations, we'll fetch messages
      // for each online user and build the conversations list from them
      const userId = this.currentUserId;
      const conversationsMap = new Map();
      
      // For each online user, check if we have messages with them
      for (const user of this._onlineUsers.value) {
        if (user.id == userId) continue; // Skip current user
        
        try {
          // Use the endpoint to get messages with this user
          const response = await axios.get(`/api/messages/${user.id}`);
          
          if (response.data && response.data.length > 0) {
            // Get the most recent message
            const messages = response.data.sort((a, b) => 
              new Date(b.timestamp) - new Date(a.timestamp)
            );
            const lastMessage = messages[0];
            
            // Count unread messages
            const unreadCount = messages.filter(m => 
              m.receiver_id == userId && !m.read
            ).length;
            
            // Add to conversations map
            conversationsMap.set(user.id, {
              userId: user.id,
              username: user.username,
              lastMessage: lastMessage.message,
              timestamp: lastMessage.timestamp,
              unread: unreadCount,
              online: user.online || false,
              last_active: user.last_active
            });
          }
        } catch (err) {
          console.error(`Failed to get messages with user ${user.id}:`, err);
        }
      }
      
      // Convert map to array and sort by timestamp (newest first)
      this._conversations.value = Array.from(conversationsMap.values())
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      
      return this._conversations.value;
    } catch (error) {
      this._handleError('Failed to load conversations');
      return [];
    } finally {
      this._loading.value = false;
    }
  }
  
  /**
   * Get all messages for a specific conversation
   * @param {number|string} userId - The user ID of the other participant
   * @returns {Promise<Array>}
   */
  async getMessages(userId) {
    if (!userId) return [];
    
    this._loading.value = true;
    try {
      const response = await axios.get(`/api/messages/${userId}`);
      
      if (response.data) {
        this._messages.value = response.data;
        
        // Set active conversation
        const user = this._onlineUsers.value.find(u => u.id == userId);
        if (user) {
          this._activeConversation.value = {
            userId: user.id,
            username: user.username,
            online: user.online,
            last_active: user.last_active
          };
        } else {
          // If user not found in online users, create minimal conversation object
          this._activeConversation.value = {
            userId: userId,
            username: `User ${userId}`,
            online: false
          };
        }
        
        // Mark messages as read
        const unreadMessages = this._messages.value.filter(
          m => m.receiver_id === this.currentUserId && !m.read
        );
        
        if (unreadMessages.length > 0) {
          // Get unread message IDs
          const messageIds = unreadMessages.map(m => m.id);
          
          // Mark these messages as read
          await this.markMessagesRead(messageIds);
          
          // Update conversation unread count
          const conversation = this._conversations.value.find(c => c.userId == userId);
          if (conversation) {
            conversation.unread = 0;
          }
        }
        
        return this._messages.value;
      }
      
      return [];
    } catch (error) {
      this._handleError('Failed to load messages');
      return [];
    } finally {
      this._loading.value = false;
    }
  }
  
  /**
   * Send a message to another user
   * @param {string|number} receiverId - Recipient user ID
   * @param {string} message - Message text
   * @param {number|null} attachmentId - Optional attachment ID
   * @returns {Promise<Object>} - Sent message details
   */
  async sendMessage(receiverId, message, attachmentId = null) {
    if (!receiverId) {
      this._handleError('Recipient ID is required');
      return null;
    }
    
    if (!message && !attachmentId) {
      this._handleError('Message or attachment is required');
      return null;
    }
    
    this._sending.value = true;
    
    try {
      const payload = {
        receiver_id: receiverId,
        message: message || ''
      };
      
      if (attachmentId) {
        payload.attachment_id = attachmentId;
      }
      
      const response = await axios.post('/api/messages', payload);
      
      if (response.data) {
        const sentMessage = response.data;
        
        // Add to current messages list if relevant
        if (this._activeConversation.value && this._activeConversation.value.userId == receiverId) {
          this._messages.value.push(sentMessage);
        }
        
        // Update or create conversation in list
        const existingConversation = this._conversations.value.find(c => c.userId == receiverId);
        
        if (existingConversation) {
          existingConversation.lastMessage = message || 'Attachment';
          existingConversation.timestamp = sentMessage.timestamp;
        } else {
          // Get user details
          const user = this._onlineUsers.value.find(u => u.id == receiverId);
          
          this._conversations.value.unshift({
            userId: receiverId,
            username: user ? user.username : `User ${receiverId}`,
            lastMessage: message || 'Attachment',
            timestamp: sentMessage.timestamp,
            unread: 0,
            online: user ? user.online : false
          });
        }
        
        return sentMessage;
      }
      
      return null;
    } catch (error) {
      this._handleError('Failed to send message');
      return null;
    } finally {
      this._sending.value = false;
    }
  }
  
  /**
   * Mark messages as read
   * @param {Array<number>} messageIds - Array of message IDs to mark as read
   * @returns {Promise<boolean>} - Success status
   */
  async markMessagesRead(messageIds) {
    if (!messageIds || messageIds.length === 0) return false;
    
    try {
      await axios.put('/api/messages/mark-read', { messageIds });
      
      // Update local message read status
      messageIds.forEach(id => {
        const message = this._messages.value.find(m => m.id === id);
        if (message) {
          message.read = true;
        }
      });
      
      // Emit socket.io event to notify sender
      if (this._socket) {
        messageIds.forEach(id => {
          const message = this._messages.value.find(m => m.id === id);
          if (message) {
            this._socket.emit('read_message', {
              message_id: id,
              sender_id: message.sender_id,
              receiver_id: message.receiver_id
            });
          }
        });
      }
      
      return true;
    } catch (error) {
      console.error('Failed to mark messages as read:', error);
      return false;
    }
  }
  
  /**
   * Mark a single message as read
   * @param {number} messageId - Message ID to mark as read
   * @returns {Promise<boolean>} - Success status
   */
  async markMessageRead(messageId) {
    if (!messageId) return false;
    
    try {
      // Using the endpoint for marking a single message as read
      await axios.post(`/api/messages/mark-read/${messageId}`);
      
      // Update local message read status
      const message = this._messages.value.find(m => m.id === messageId);
      if (message) {
        message.read = true;
      }
      
      // Emit socket.io event to notify sender
      if (this._socket && message) {
        this._socket.emit('read_message', {
          message_id: messageId,
          sender_id: message.sender_id,
          receiver_id: message.receiver_id
        });
      }
      
      return true;
    } catch (error) {
      console.error('Failed to mark message as read:', error);
      return false;
    }
  }
  
  /**
   * Emit typing indicator
   * @param {number|string} receiverId - Recipient user ID
   */
  sendTypingIndicator(receiverId) {
    if (this._socket && receiverId) {
      this._socket.emit('typing', {
        sender_id: this.currentUserId,
        receiver_id: receiverId
      });
    }
  }
  
  /**
   * Get list of online users
   * @returns {Promise<Array>} - List of users
   */
  async getOnlineUsers() {
    try {
      const response = await axios.get('/api/online-users');
      
      if (response.data) {
        this._onlineUsers.value = response.data;
        return this._onlineUsers.value;
      }
      
      return [];
    } catch (error) {
      console.error('Failed to get online users:', error);
      return [];
    }
  }
  
  /**
   * Get total unread messages count
   * @returns {Promise<number>} - Total unread count
   */
  async getTotalUnreadCount() {
    try {
      // We need to calculate unread count from conversations
      await this.getConversations(); // Make sure conversations are up to date
      
      let count = 0;
      this._conversations.value.forEach(conversation => {
        count += conversation.unread || 0;
      });
      
      this._unreadCount.value = count;
      return { success: true, count };
    } catch (error) {
      console.error('Failed to calculate unread count:', error);
      return { success: false, count: this._unreadCount.value };
    }
  }
  
  /**
   * Handle error consistently
   * @private
   * @param {string} message - Error message
   */
  _handleError(message) {
    this._error.value = message;
    console.error(message);
    this._toast.error(message);
  }
  
  // Expose reactive properties as computed
  get conversations() {
    return computed(() => this._conversations.value);
  }
  
  get messages() {
    return computed(() => this._messages.value);
  }
  
  get activeConversation() {
    return computed(() => this._activeConversation.value);
  }
  
  get loading() {
    return computed(() => this._loading.value);
  }
  
  get sending() {
    return computed(() => this._sending.value);
  }
  
  get error() {
    return computed(() => this._error.value);
  }
  
  get unreadCount() {
    return computed(() => this._unreadCount.value);
  }
  
  get onlineUsers() {
    return computed(() => this._onlineUsers.value);
  }
}

// Create singleton instance
const messageService = new MessageService();
export default messageService;