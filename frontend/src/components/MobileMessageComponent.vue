<template>
  <div class="mobile-messaging-container">
    <!-- User list view (shows when no conversation is selected) -->
    <div v-if="!selectedUser" class="user-list-view">
      <div class="mobile-header">
        <h1>Messages</h1>
        <div class="header-actions">
          <button class="filter-button" @click="toggleFilterDropdown">
            <font-awesome-icon icon="filter" />
            <span class="filter-label">{{ activeFilter === 'all' ? 'All' : activeFilter === 'online' ? 'Online' :
              'Unread' }}</span>
          </button>
        </div>
      </div>

      <!-- Filter dropdown -->
      <div v-if="showFilterDropdown" class="filter-dropdown">
        <button :class="['filter-option', { active: activeFilter === 'all' }]" @click="setFilter('all')">
          <font-awesome-icon icon="users" />
          <span>All Users</span>
        </button>
        <button :class="['filter-option', { active: activeFilter === 'online' }]" @click="setFilter('online')">
          <font-awesome-icon icon="circle" class="online-icon" />
          <span>Online</span>
        </button>
        <button :class="['filter-option', { active: activeFilter === 'unread' }]" @click="setFilter('unread')">
          <font-awesome-icon icon="envelope" />
          <span>Unread</span>
        </button>
      </div>

      <!-- Search bar -->
      <div class="search-bar">
        <font-awesome-icon icon="search" class="search-icon" />
        <input type="text" v-model="searchQuery" placeholder="Search users..." class="search-input" />
        <button v-if="searchQuery" class="clear-btn" @click="searchQuery = ''">
          <font-awesome-icon icon="times" />
        </button>
      </div>

      <!-- User list -->
      <div class="users-list">
        <div v-if="isLoading" class="loading-container">
          <div class="loading-spinner"></div>
          <span>Loading users...</span>
        </div>

        <div v-else-if="filteredUsers.length === 0" class="empty-state">
          <font-awesome-icon icon="user-slash" size="2x" />
          <p>No users found</p>
        </div>

        <div v-for="user in filteredUsers" :key="user.id" class="user-item" @click="selectUser(user)">
          <div class="user-status" :class="{ online: user.online }"></div>
          <div class="user-avatar">
            {{ getUserInitials(user.username) }}
          </div>
          <div class="user-info">
            <div class="user-name">{{ user.username }}</div>
            <div class="user-preview">
              <span v-if="typingUsers[user.id]" class="typing-indicator">Typing...</span>
              <span v-else-if="user.lastMessage" class="last-message">{{ truncateMessage(user.lastMessage) }}</span>
              <span v-else class="no-messages">No messages</span>
            </div>
          </div>
          <div class="user-meta">
            <div v-if="user.lastMessageTime" class="timestamp">
              {{ formatTime(user.lastMessageTime) }}
            </div>
            <div v-if="unreadCounts[user.id]" class="unread-badge">
              {{ unreadCounts[user.id] }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat view (shows when a conversation is selected) -->
    <div v-else class="chat-view">
      <!-- Chat header -->
      <div class="chat-header">
        <button class="back-button" @click="closeChat">
          <font-awesome-icon icon="arrow-left" />
        </button>
        <div class="user-info" @click="toggleUserInfo">
          <div class="user-avatar">
            {{ getUserInitials(selectedUser.username) }}
          </div>
          <div class="user-details">
            <div class="user-name">{{ selectedUser.username }}</div>
            <div class="user-status-text">
              {{ selectedUser.online ? 'Online' : 'Offline' }}
            </div>
          </div>
        </div>
        <div class="header-actions">
          <button class="info-button" @click="toggleUserInfo">
            <font-awesome-icon icon="info-circle" />
          </button>
        </div>
      </div>

      <!-- Chat messages -->
      <div class="messages-container" ref="messagesContainer" @scroll="handleScroll"
        v-mobile-chat-scroll="{ activateCondition: !isLoading && !fetchingMoreMessages }">
        <div v-if="fetchingMoreMessages" class="load-more-spinner">
          <div class="loading-spinner small"></div>
        </div>

        <div v-if="messages.length === 0 && !isLoading" class="empty-chat">
          <div class="empty-illustration">
            <font-awesome-icon icon="comments" size="3x" />
          </div>
          <p>No messages yet</p>
          <p class="empty-chat-hint">Start the conversation with {{ selectedUser.username }}</p>
        </div>

        <div v-for="(message, index) in messages" :key="message.id" class="message-wrapper"
          :class="{ 'own-message': message.sender_id === user.id }">
          <div class="message-date" v-if="showDateDivider(message, index)">
            {{ formatMessageDate(message.timestamp) }}
          </div>

          <div class="message" :class="{ 'own': message.sender_id === user.id }">
            <!-- System message -->
            <div v-if="message.is_system" class="system-message">
              <div class="message-content system">
                {{ message.message }}
              </div>
            </div>

            <!-- Regular message -->
            <div v-else class="message-bubble" :class="{ 'has-attachment': message.attachment }">
              <div class="message-content">
                <!-- Media attachment -->
                <div v-if="message.attachment" class="attachment" @click="viewAttachment(message.attachment)">
                  <div v-if="isImageAttachment(message.attachment)" class="image-attachment">
                    <img :src="message.attachment.url" alt="Attachment" />
                  </div>
                  <div v-else class="file-attachment">
                    <font-awesome-icon icon="file" class="file-icon" />
                    <div class="file-info">
                      <div class="file-name">{{ message.attachment.name }}</div>
                      <div class="file-meta">
                        {{ formatFileSize(message.attachment.size) }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Message text -->
                <div v-if="message.message" class="message-text">
                  {{ message.message }}
                </div>
              </div>

              <div class="message-meta">
                <span class="message-time">{{ formatMessageTime(message.timestamp) }}</span>
                <font-awesome-icon v-if="message.sender_id === user.id" icon="check-double" class="message-status"
                  :class="{ 'read': message.read }" />
              </div>
            </div>
          </div>
        </div>

        <!-- Typing indicator -->
        <div v-if="typingUsers[selectedUser.id]" class="typing-indicator-container">
          <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <div class="typing-text">{{ selectedUser.username }} is typing...</div>
        </div>
      </div>

      <!-- Message input -->
      <div class="message-composer">
        <div class="attachment-preview" v-if="selectedFile">
          <div class="preview-header">
            <span class="file-name">{{ selectedFile.name }}</span>
            <button class="remove-file" @click="removeSelectedFile">
              <font-awesome-icon icon="times" />
            </button>
          </div>
          <div class="preview-content">
            <img v-if="previewUrl" :src="previewUrl" alt="Preview" class="image-preview" />
            <div v-else class="file-preview">
              <font-awesome-icon icon="file" class="file-icon" />
              <div class="file-meta">{{ formatFileSize(selectedFile.size) }}</div>
            </div>
          </div>
        </div>

        <div class="input-container">
          <button class="attach-button" @click="triggerFileInput">
            <font-awesome-icon icon="paperclip" />
          </button>
          <input type="file" ref="fileInput" class="file-input" @change="handleFileSelect"
            accept="image/*,application/pdf,text/plain,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" />

          <textarea v-model="inputMessage" @input="handleInput" @keydown.enter.prevent="sendMessage"
            placeholder="Type a message..." class="message-input" ref="messageInput" rows="1"></textarea>

          <button class="send-button" :class="{ 'active': inputMessage.trim() || selectedFile }" @click="sendMessage"
            :disabled="!inputMessage.trim() && !selectedFile">
            <font-awesome-icon icon="paper-plane" />
          </button>
        </div>
      </div>

      <!-- User info panel (slides in from right) -->
      <div class="user-info-panel" :class="{ 'open': showInfoPanel }">
        <div class="info-panel-header">
          <h3>User Info</h3>
          <button class="close-panel" @click="showInfoPanel = false">
            <font-awesome-icon icon="times" />
          </button>
        </div>

        <div class="info-panel-content">
          <div class="user-avatar large">
            {{ getUserInitials(selectedUser.username) }}
          </div>
          <h3 class="user-full-name">{{ selectedUser.username }}</h3>
          <div class="user-detail-item">
            <font-awesome-icon icon="envelope" class="detail-icon" />
            <span>{{ selectedUser.email || 'No email available' }}</span>
          </div>
          <div class="user-detail-item">
            <font-awesome-icon icon="clock" class="detail-icon" />
            <span>Last active: {{ formatLastActive(selectedUser.last_active) }}</span>
          </div>

          <div class="info-panel-actions">
            <button class="panel-action-btn" @click="clearChatHistory">
              <font-awesome-icon icon="trash-alt" />
              <span>Clear Chat</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Attachment viewer modal -->
      <div v-if="viewingAttachment" class="attachment-viewer">
        <div class="attachment-viewer-header">
          <h3>{{ viewingAttachment.name }}</h3>
          <button class="close-viewer" @click="viewingAttachment = null">
            <font-awesome-icon icon="times" />
          </button>
        </div>

        <div class="attachment-viewer-content">
          <img v-if="isImageAttachment(viewingAttachment)" :src="viewingAttachment.url" alt="Attachment"
            class="attachment-image" />
          <div v-else class="attachment-file">
            <font-awesome-icon icon="file" size="3x" class="file-icon" />
            <div class="file-name">{{ viewingAttachment.name }}</div>
            <div class="file-size">{{ formatFileSize(viewingAttachment.size) }}</div>
            <a :href="viewingAttachment.url" download class="download-link">
              <font-awesome-icon icon="download" />
              <span>Download</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useToast } from 'vue-toastification'
import { io } from 'socket.io-client'
import axios from 'axios'
import { format, formatDistance, isToday, isYesterday, parseISO } from 'date-fns'
import { mobileChatScroll } from '../directives/MobileChatScroll'

export default {
  name: 'MobileMessageComponent',
  directives: {
    'mobile-chat-scroll': mobileChatScroll
  },
  props: {
    user: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    // State
    const users = ref([]);
    const messages = ref([]);
    const selectedUser = ref(null);
    const inputMessage = ref('');
    const isLoading = ref(false);
    const searchQuery = ref('');
    const activeFilter = ref('all');
    const showFilterDropdown = ref(false);
    const unreadCounts = reactive({});
    const typingUsers = reactive({});
    const socket = ref(null);
    const isConnected = ref(false);
    const isTyping = ref(false);
    const typingTimeout = ref(null);
    const selectedFile = ref(null);
    const viewingAttachment = ref(null);
    const pendingMessages = ref([]);
    const hasMoreMessages = ref(true);
    const page = ref(1);
    const messagesPerPage = ref(20);
    const showInfoPanel = ref(false);
    const previewUrl = ref(null);
    const fetchingMoreMessages = ref(false);

    // Refs
    const messagesContainer = ref(null);
    const messageInput = ref(null);
    const fileInput = ref(null);

    // Toast
    const toast = useToast();

    // Computed
    const filteredUsers = computed(() => {
      let result = users.value;

      // Apply search
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase();
        result = result.filter(user =>
          user.username.toLowerCase().includes(query)
        );
      }

      // Apply filter
      if (activeFilter.value === 'online') {
        result = result.filter(user => user.online);
      } else if (activeFilter.value === 'unread') {
        result = result.filter(user => unreadCounts[user.id]);
      }

      // Sort by online status and lastMessageTime
      return result.sort((a, b) => {
        // Online users first
        if (a.online && !b.online) return -1;
        if (!a.online && b.online) return 1;

        // Then by unread count
        if (unreadCounts[a.id] && !unreadCounts[b.id]) return -1;
        if (!unreadCounts[a.id] && unreadCounts[b.id]) return 1;

        // Then by last message time
        const aTime = a.lastMessageTime ? new Date(a.lastMessageTime) : new Date(0);
        const bTime = b.lastMessageTime ? new Date(b.lastMessageTime) : new Date(0);
        return bTime - aTime;
      });
    });

    // Calculate total unread count
    const unreadCount = computed(() => {
      return Object.values(unreadCounts).reduce((sum, count) => sum + count, 0);
    });

    // Methods
    const initSocket = () => {
      // Connect to the backend at     https://monitor-backend.jetcamstudio.com:5000
      socket.value = io('     https://monitor-backend.jetcamstudio.com:5000messages', {
        path: '/ws',
        transports: ['websocket']
      });

      const socketUrl = `     https://monitor-backend.jetcamstudio.com:5000messages`;

      console.log('Connecting to WebSocket server:', socketUrl);
      socket.value = io(socketUrl, {
        path: '/ws',
        transports: ['websocket', 'polling']
      });

      socket.value.on('connect', () => {
        console.log('Connected to WebSocket server');
        isConnected.value = true;

        // Send pending messages if any
        sendPendingMessages();
      });

      socket.value.on('disconnect', () => {
        console.log('Disconnected from WebSocket server');
        isConnected.value = false;
      });

      socket.value.on('receive_message', (message) => {
        console.log('Received message:', message);
        handleIncomingMessage(message);
      });

      socket.value.on('user_status', (data) => {
        console.log('User status update:', data);
        updateUserStatus(data);
      });

      socket.value.on('typing', (data) => {
        console.log('Typing indicator:', data);
        handleTypingIndicator(data);
      });

      socket.value.on('error', (error) => {
        console.error('Socket error:', error);
      });
    };

    const fetchUsers = async () => {
      try {
        const response = await axios.get('/api/online-users');
        users.value = response.data;

        // Initialize unread counts
        users.value.forEach(user => {
          fetchUnreadCount(user.id);
        });
      } catch (error) {
        console.error('Error fetching users:', error);
      }
    };

    const fetchMessages = async (userId) => {
      if (!userId) return;

      isLoading.value = true;
      page.value = 1;
      messages.value = [];

      try {
        const response = await axios.get(`/api/messages/${userId}`, {
          params: {
            page: page.value,
            limit: messagesPerPage.value
          }
        });

        messages.value = response.data.messages;
        hasMoreMessages.value = response.data.has_more;

        // Mark messages as read
        markMessagesAsRead(userId);

        // Update unread count
        unreadCounts[userId] = 0;

        // Scroll to bottom on next tick
        await nextTick();
        scrollToBottom();
      } catch (error) {
        console.error('Error fetching messages:', error);
        toast.error('Failed to load messages');
      } finally {
        isLoading.value = false;
      }
    };

    const fetchMoreMessages = async () => {
      if (!selectedUser.value || !hasMoreMessages.value || fetchingMoreMessages.value) return;

      fetchingMoreMessages.value = true;
      const userId = selectedUser.value.id;
      const nextPage = page.value + 1;

      try {
        const response = await axios.get(`/api/messages/${userId}`, {
          params: {
            page: nextPage,
            limit: messagesPerPage.value
          }
        });

        const oldMessages = response.data.messages;
        messages.value = [...oldMessages, ...messages.value];
        hasMoreMessages.value = response.data.has_more;
        page.value = nextPage;

        // Maintain scroll position
        await nextTick();
        if (messagesContainer.value && oldMessages.length > 0) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight - messagesContainer.value.clientHeight;
        }
      } catch (error) {
        console.error('Error fetching more messages:', error);
        toast.error('Failed to load more messages');
      } finally {
        fetchingMoreMessages.value = false;
      }
    };

    const fetchUnreadCount = async (userId) => {
      try {
        const response = await axios.get(`/api/messages/${userId}/unread-count`);
        unreadCounts[userId] = response.data.count;
      } catch (error) {
        console.error(`Error fetching unread count for user ${userId}:`, error);
      }
    };

    const selectUser = (user) => {
      selectedUser.value = user;
      fetchMessages(user.id);
    };

    const closeChat = () => {
      selectedUser.value = null;
    };

    const sendMessage = async () => {
      if ((!inputMessage.value.trim() && !selectedFile.value) || !selectedUser.value) return;

      const messageData = {
        receiver_id: selectedUser.value.id,
        message: inputMessage.value.trim(),
        attachment: null
      };

      // Reset input
      inputMessage.value = '';
      resizeTextarea();

      // Handle attachment
      if (selectedFile.value) {
        try {
          const formData = new FormData();
          formData.append('file', selectedFile.value);

          const response = await axios.post('/api/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          });

          messageData.attachment = response.data;
        } catch (error) {
          console.error('Error uploading file:', error);
          toast.error('Failed to upload file');
          return;
        } finally {
          // Reset file selection
          selectedFile.value = null;
          previewUrl.value = null;
        }
      }

      // Create optimistic message
      const optimisticMessage = {
        id: `temp-${Date.now()}`,
        sender_id: props.user.id,
        receiver_id: selectedUser.value.id,
        message: messageData.message,
        attachment: messageData.attachment,
        timestamp: new Date().toISOString(),
        read: false,
        is_system: false,
        pending: true
      };

      // Add to messages
      messages.value.push(optimisticMessage);

      // Scroll to bottom
      await nextTick();
      scrollToBottom();

      // Send message via socket
      if (isConnected.value) {
        socket.value.emit('send_message', messageData, (response) => {
          if (response.success) {
            // Update the optimistic message with real data
            const index = messages.value.findIndex(m => m.id === optimisticMessage.id);
            if (index !== -1) {
              messages.value[index] = { ...response.message, pending: false };
            }

            // Update last message in user list
            updateUserLastMessage(selectedUser.value.id, response.message);
          } else {
            console.error('Failed to send message:', response.error);
            toast.error('Failed to send message');

            // Mark message as failed
            const index = messages.value.findIndex(m => m.id === optimisticMessage.id);
            if (index !== -1) {
              messages.value[index].failed = true;
            }

            // Add to pending messages to retry later
            pendingMessages.value.push(messageData);
          }
        });
      } else {
        // Socket not connected, add to pending
        pendingMessages.value.push(messageData);
        toast.warning('You are offline. Message will be sent when connection is restored.');
      }
    };

    const handleIncomingMessage = (message) => {
      // Check if we already have the message (prevent duplicates)
      const existingIndex = messages.value.findIndex(m => m.id === message.id);
      if (existingIndex !== -1) return;

      // Add to messages if current chat is open
      if (selectedUser.value &&
        (message.sender_id === selectedUser.value.id ||
          message.receiver_id === selectedUser.value.id)) {
        messages.value.push(message);
        nextTick(scrollToBottom);

        // Mark as read if from the selected user
        if (message.sender_id === selectedUser.value.id) {
          markMessagesAsRead(selectedUser.value.id);
        }
      } else if (message.sender_id !== props.user.id) {
        // Increment unread count for sender
        unreadCounts[message.sender_id] = (unreadCounts[message.sender_id] || 0) + 1;

        // Show notification
        const sender = users.value.find(u => u.id === message.sender_id);
        if (sender) {
          toast.info(`New message from ${sender.username}`);
        }
      }

      // Update last message in user list
      updateUserLastMessage(message.sender_id === props.user.id ? message.receiver_id : message.sender_id, message);
    };

    const updateUserLastMessage = (userId, message) => {
      const userIndex = users.value.findIndex(u => u.id === userId);
      if (userIndex !== -1) {
        users.value[userIndex].lastMessage = message.message || (message.attachment ? 'Attachment' : '');
        users.value[userIndex].lastMessageTime = message.timestamp;
      }
    };

    const updateUserStatus = (data) => {
      const userIndex = users.value.findIndex(u => u.id === data.user_id);
      if (userIndex !== -1) {
        users.value[userIndex].online = data.online;
        users.value[userIndex].last_active = data.last_active;
      }
    };

    const markMessagesAsRead = async (userId) => {
      if (!userId) return;

      try {
        await axios.post(`/api/messages/${userId}/read`);

        // Update UI
        messages.value.forEach(message => {
          if (message.sender_id === userId && !message.read) {
            message.read = true;
          }
        });

        // Update unread count
        unreadCounts[userId] = 0;

        // Notify via socket
        if (isConnected.value) {
          socket.value.emit('message_status', {
            user_id: userId,
            status: 'read'
          });
        }
      } catch (error) {
        console.error('Error marking messages as read:', error);
      }
    };

    const handleTypingIndicator = (data) => {
      if (data.sender_id === props.user.id) return;

      typingUsers[data.sender_id] = data.typing;

      // Clear typing indicator after 3 seconds if no update
      if (data.typing) {
        setTimeout(() => {
          typingUsers[data.sender_id] = false;
        }, 3000);
      }
    };

    const handleInput = () => {
      resizeTextarea();

      // Send typing indicator
      if (!isTyping.value && selectedUser.value) {
        isTyping.value = true;

        if (isConnected.value) {
          socket.value.emit('typing', {
            receiver_id: selectedUser.value.id,
            typing: true
          });
        }

        // Clear previous timeout
        if (typingTimeout.value) {
          clearTimeout(typingTimeout.value);
        }

        // Set new timeout
        typingTimeout.value = setTimeout(() => {
          isTyping.value = false;

          if (isConnected.value && selectedUser.value) {
            socket.value.emit('typing', {
              receiver_id: selectedUser.value.id,
              typing: false
            });
          }
        }, 3000);
      }
    };

    const resizeTextarea = () => {
      if (!messageInput.value) return;

      // Reset height
      messageInput.value.style.height = 'auto';

      // Set new height
      const newHeight = Math.min(messageInput.value.scrollHeight, 120);
      messageInput.value.style.height = `${newHeight}px`;
    };

    const scrollToBottom = () => {
      if (!messagesContainer.value) return;
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    };

    const handleScroll = () => {
      if (!messagesContainer.value) return;

      // Check if scrolled to top to load more messages
      if (messagesContainer.value.scrollTop < 50 && hasMoreMessages.value && !fetchingMoreMessages.value) {
        fetchMoreMessages();
      }
    };

    const setFilter = (filter) => {
      activeFilter.value = filter;
      showFilterDropdown.value = false;
    };

    const toggleFilterDropdown = () => {
      showFilterDropdown.value = !showFilterDropdown.value;
    };

    const toggleUserInfo = () => {
      showInfoPanel.value = !showInfoPanel.value;
    };

    const clearChatHistory = async () => {
      if (!selectedUser.value) return;

      try {
        await axios.delete(`/api/messages/${selectedUser.value.id}`);
        messages.value = [];
        toast.success('Chat history cleared');
        showInfoPanel.value = false;
      } catch (error) {
        console.error('Error clearing chat history:', error);
        toast.error('Failed to clear chat history');
      }
    };

    const sendPendingMessages = () => {
      if (!isConnected.value || pendingMessages.value.length === 0) return;

      // Clone and clear pending messages
      const toSend = [...pendingMessages.value];
      pendingMessages.value = [];

      // Send each pending message
      toSend.forEach(message => {
        socket.value.emit('send_message', message, (response) => {
          if (!response.success) {
            console.error('Failed to send pending message:', response.error);
            pendingMessages.value.push(message);
          } else {
            toast.success('Pending message sent');
          }
        });
      });
    };

    const triggerFileInput = () => {
      if (fileInput.value) {
        fileInput.value.click();
      }
    };

    const handleFileSelect = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File size exceeds 10MB limit');
        event.target.value = null;
        return;
      }

      selectedFile.value = file;

      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          previewUrl.value = e.target.result;
        };
        reader.readAsDataURL(file);
      } else {
        previewUrl.value = null;
      }

      // Reset file input
      event.target.value = null;
    };

    const removeSelectedFile = () => {
      selectedFile.value = null;
      previewUrl.value = null;
    };

    const viewAttachment = (attachment) => {
      viewingAttachment.value = attachment;
    };

    const isImageAttachment = (attachment) => {
      if (!attachment || !attachment.url) return false;
      const ext = attachment.url.split('.').pop().toLowerCase();
      return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext);
    };

    const formatFileSize = (size) => {
      if (!size) return '0 B';

      const units = ['B', 'KB', 'MB', 'GB'];
      let i = 0;
      let formattedSize = size;

      while (formattedSize >= 1024 && i < units.length - 1) {
        formattedSize /= 1024;
        i++;
      }

      return `${formattedSize.toFixed(1)} ${units[i]}`;
    };

    const formatTime = (timestamp) => {
      if (!timestamp) return '';

      const date = parseISO(timestamp);

      if (isToday(date)) {
        return format(date, 'HH:mm');
      } else if (isYesterday(date)) {
        return 'Yesterday';
      } else {
        return format(date, 'dd/MM/yy');
      }
    };

    const formatMessageTime = (timestamp) => {
      if (!timestamp) return '';
      return format(parseISO(timestamp), 'HH:mm');
    };

    const formatMessageDate = (timestamp) => {
      if (!timestamp) return '';

      const date = parseISO(timestamp);

      if (isToday(date)) {
        return 'Today';
      } else if (isYesterday(date)) {
        return 'Yesterday';
      } else {
        return format(date, 'EEEE, MMMM d, yyyy');
      }
    };

    const formatLastActive = (timestamp) => {
      if (!timestamp) return 'Never';
      return formatDistance(parseISO(timestamp), new Date(), { addSuffix: true });
    };

    const showDateDivider = (message, index) => {
      if (index === 0) return true;

      const currentDate = parseISO(message.timestamp);
      const prevDate = parseISO(messages.value[index - 1].timestamp);

      return !isSameDay(currentDate, prevDate);
    };

    const isSameDay = (date1, date2) => {
      return format(date1, 'yyyy-MM-dd') === format(date2, 'yyyy-MM-dd');
    };

    const getUserInitials = (username) => {
      if (!username) return '';
      return username.charAt(0).toUpperCase();
    };

    const truncateMessage = (message) => {
      if (!message) return '';
      return message.length > 30 ? `${message.substring(0, 27)}...` : message;
    };

    // Initialize
    onMounted(() => {
      fetchUsers();
      initSocket();

      // Setup click handlers
      document.addEventListener('click', (event) => {
        // Close filter dropdown when clicking outside
        if (showFilterDropdown.value &&
          !event.target.closest('.filter-button') &&
          !event.target.closest('.filter-dropdown')) {
          showFilterDropdown.value = false;
        }
      });
    });

    // Clean up
    onUnmounted(() => {
      if (socket.value) {
        socket.value.disconnect();
      }

      if (typingTimeout.value) {
        clearTimeout(typingTimeout.value);
      }
    });

    // Watch for changes
    watch(selectedUser, (newValue) => {
      if (newValue) {
        // Reset some state when changing users
        page.value = 1;
        hasMoreMessages.value = true;
        showInfoPanel.value = false;
      }
    });

    return {
      // State
      users,
      messages,
      selectedUser,
      inputMessage,
      isLoading,
      searchQuery,
      activeFilter,
      showFilterDropdown,
      unreadCounts,
      typingUsers,
      isConnected,
      selectedFile,
      viewingAttachment,
      hasMoreMessages,
      showInfoPanel,
      previewUrl,
      fetchingMoreMessages,

      // Refs
      messagesContainer,
      messageInput,
      fileInput,

      // Computed
      filteredUsers,
      unreadCount,

      // Methods
      selectUser,
      closeChat,
      sendMessage,
      handleInput,
      handleScroll,
      setFilter,
      toggleFilterDropdown,
      toggleUserInfo,
      clearChatHistory,
      triggerFileInput,
      handleFileSelect,
      removeSelectedFile,
      viewAttachment,
      isImageAttachment,
      formatFileSize,
      formatTime,
      formatMessageTime,
      formatMessageDate,
      formatLastActive,
      showDateDivider,
      getUserInitials,
      truncateMessage
    };
  }
};
</script>

<style scoped>
.mobile-messaging-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  background-color: var(--light-bg, #f5f5f5);
  color: var(--light-text, #333);
  overflow: hidden;
  position: relative;
}

[data-theme='dark'] .mobile-messaging-container {
  background-color: var(--dark-bg, #121212);
  color: var(--dark-text, #eee);
}

/* User list view styles */
.user-list-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.mobile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background-color: var(--light-card-bg, #fff);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

[data-theme='dark'] .mobile-header {
  background-color: var(--dark-card-bg, #1e1e1e);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.mobile-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-button {
  display: flex;
  align-items: center;
  background: none;
  border: 1px solid var(--light-border, #e0e0e0);
  border-radius: 20px;
  padding: 6px 12px;
  font-size: 0.9rem;
  color: var(--light-text, #333);
  cursor: pointer;
}

[data-theme='dark'] .filter-button {
  border-color: var(--dark-border, #444);
  color: var(--dark-text, #eee);
}

.filter-label {
  margin-left: 6px;
}

.filter-dropdown {
  position: absolute;
  top: 60px;
  right: 15px;
  background-color: var(--light-card-bg, #fff);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 20;
  width: 180px;
  overflow: hidden;
}

[data-theme='dark'] .filter-dropdown {
  background-color: var(--dark-card-bg, #1e1e1e);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.filter-option {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 12px 15px;
  background: none;
  border: none;
  text-align: left;
  font-size: 0.95rem;
  color: var(--light-text, #333);
  cursor: pointer;
}

[data-theme='dark'] .filter-option {
  color: var(--dark-text, #eee);
}

.filter-option:hover {
  background-color: var(--light-hover, #f5f5f5);
}

[data-theme='dark'] .filter-option:hover {
  background-color: var(--dark-hover, #2a2a2a);
}

.filter-option.active {
  background-color: var(--light-primary-light, #e6f7ff);
  color: var(--light-primary, #4361ee);
}

[data-theme='dark'] .filter-option.active {
  background-color: var(--dark-primary-light, #1a365d);
  color: var(--dark-primary, #90cdf4);
}

.filter-option span {
  margin-left: 10px;
}

.online-icon {
  color: var(--light-success, #48bb78);
}

[data-theme='dark'] .online-icon {
  color: var(--dark-success, #68d391);
}

.search-bar {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background-color: var(--light-card-bg, #fff);
  border-bottom: 1px solid var(--light-border, #e0e0e0);
  position: relative;
}

[data-theme='dark'] .search-bar {
  background-color: var(--dark-card-bg, #1e1e1e);
  border-bottom-color: var(--dark-border, #444);
}

.search-icon {
  position: absolute;
  left: 25px;
  color: var(--light-text-secondary, #666);
}

[data-theme='dark'] .search-icon {
  color: var(--dark-text-secondary, #aaa);
}

.search-input {
  flex: 1;
  background-color: var(--light-bg, #f5f5f5);
  border: none;
  border-radius: 20px;
  padding: 10px 40px;
  font-size: 0.95rem;
  color: var(--light-text, #333);
}

[data-theme='dark'] .search-input {
  background-color: var(--dark-bg, #121212);
  color: var(--dark-text, #eee);
}

.search-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--light-primary, #4361ee);
}

[data-theme='dark'] .search-input:focus {
  box-shadow: 0 0 0 2px var(--dark-primary, #90cdf4);
}

.clear-btn {
  position: absolute;
  right: 25px;
  background: none;
  border: none;
  color: var(--light-text-secondary, #666);
  cursor: pointer;
  font-size: 0.9rem;
}

[data-theme='dark'] .clear-btn {
  color: var(--dark-text-secondary, #aaa);
}

.users-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 0 15px;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid var(--light-border, #e0e0e0);
  cursor: pointer;
  position: relative;
}

[data-theme='dark'] .user-item {
  border-bottom-color: var(--dark-border, #444);
}

.user-item:hover {
  background-color: var(--light-hover, #f5f5f5);
}

[data-theme='dark'] .user-item:hover {
  background-color: var(--dark-hover, #2a2a2a);
}

.user-status {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--light-text-secondary, #999);
  margin-right: 10px;
  border: 2px solid var(--light-card-bg, #fff);
}

[data-theme='dark'] .user-status {
  background-color: var(--dark-text-secondary, #666);
  border-color: var(--dark-card-bg, #1e1e1e);
}

.user-status.online {
  background-color: var(--light-success, #48bb78);
}

[data-theme='dark'] .user-status.online {
  background-color: var(--dark-success, #68d391);
}

.user-avatar {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background-color: var(--light-primary, #4361ee);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 600;
  margin-right: 12px;
}

[data-theme='dark'] .user-avatar {
  background-color: var(--dark-primary, #90cdf4);
  color: var(--dark-bg, #121212);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-preview {
  font-size: 0.85rem;
  color: var(--light-text-secondary, #666);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

[data-theme='dark'] .user-preview {
  color: var(--dark-text-secondary, #aaa);
}

.typing-indicator {
  color: var(--light-primary, #4361ee);
  font-style: italic;
}

[data-theme='dark'] .typing-indicator {
  color: var(--dark-primary, #90cdf4);
}

.user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-left: 12px;
}

.timestamp {
  font-size: 0.75rem;
  color: var(--light-text-secondary, #666);
  margin-bottom: 4px;
}

[data-theme='dark'] .timestamp {
  color: var(--dark-text-secondary, #aaa);
}

.unread-badge {
  background-color: var(--light-primary, #4361ee);
  color: white;
  border-radius: 50%;
  min-width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  padding: 0 6px;
}

[data-theme='dark'] .unread-badge {
  background-color: var(--dark-primary, #90cdf4);
  color: var(--dark-bg, #121212);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--light-text-secondary, #666);
  text-align: center;
}

[data-theme='dark'] .empty-state {
  color: var(--dark-text-secondary, #aaa);
}

.empty-state p {
  margin-top: 15px;
  font-size: 1rem;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 3px solid var(--light-border, #e0e0e0);
  border-top-color: var(--light-primary, #4361ee);
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

[data-theme='dark'] .loading-spinner {
  border-color: var(--dark-border, #444);
  border-top-color: var(--dark-primary, #90cdf4);
}

.loading-spinner.small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Chat view styles */
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  background-color: var(--light-bg, #f5f5f5);
}

[data-theme='dark'] .chat-view {
  background-color: var(--dark-bg, #121212);
}

.chat-header {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background-color: var(--light-card-bg, #fff);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  z-index: 2;
}

[data-theme='dark'] .chat-header {
  background-color: var(--dark-card-bg, #1e1e1e);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.back-button {
  background: none;
  border: none;
  color: var(--light-text, #333);
  font-size: 1.2rem;
  margin-right: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

[data-theme='dark'] .back-button {
  color: var(--dark-text, #eee);
}

.back-button:active {
  background-color: var(--light-hover, #f5f5f5);
}

[data-theme='dark'] .back-button:active {
  background-color: var(--dark-hover, #2a2a2a);
}

.chat-header .user-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.chat-header .user-details {
  margin-left: 12px;
}

.chat-header .user-name {
  font-weight: 600;
  margin-bottom: 2px;
}

.user-status-text {
  font-size: 0.8rem;
  color: var(--light-text-secondary, #666);
}

[data-theme='dark'] .user-status-text {
  color: var(--dark-text-secondary, #aaa);
}

.info-button {
  background: none;
  border: none;
  color: var(--light-text, #333);
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

[data-theme='dark'] .info-button {
  color: var(--dark-text, #eee);
}

.info-button:active {
  background-color: var(--light-hover, #f5f5f5);
}

[data-theme='dark'] .info-button:active {
  background-color: var(--dark-hover, #2a2a2a);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
  display: flex;
  flex-direction: column;
}

.message-wrapper {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
  width: 100%;
}

.message-wrapper.own-message {
  align-items: flex-end;
}

.message-date {
  text-align: center;
  margin: 10px 0;
  color: var(--light-text-secondary, #666);
  font-size: 0.8rem;
  background-color: var(--light-bg-secondary, #eaeaea);
  border-radius: 15px;
  padding: 5px 10px;
  display: inline-block;
  align-self: center;
}

[data-theme='dark'] .message-date {
  color: var(--dark-text-secondary, #aaa);
  background-color: var(--dark-bg-secondary, #2a2a2a);
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 80%;
}

.message-bubble {
  background-color: var(--light-card-bg, #fff);
  border-radius: 18px;
  padding: 10px 15px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  margin-bottom: 2px;
  position: relative;
}

[data-theme='dark'] .message-bubble {
  background-color: var(--dark-card-bg, #1e1e1e);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.message-bubble.own {
  background-color: var(--light-primary-light, #e6f7ff);
  color: var(--light-text-dark, #333);
}

[data-theme='dark'] .message-bubble.own {
  background-color: var(--dark-primary-light, #1a365d);
  color: var(--dark-text, #eee);
}

.system-message {
  align-self: center;
  max-width: 80%;
  margin: 10px 0;
}

.message-content.system {
  background-color: var(--light-bg-secondary, #eaeaea);
  color: var(--light-text-secondary, #666);
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 0.85rem;
  text-align: center;
}

[data-theme='dark'] .message-content.system {
  background-color: var(--dark-bg-secondary, #2a2a2a);
  color: var(--dark-text-secondary, #aaa);
}

.attachment {
  margin-bottom: 5px;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
}

.image-attachment img {
  max-width: 100%;
  max-height: 200px;
  object-fit: cover;
  border-radius: 12px;
}

.file-attachment {
  display: flex;
  align-items: center;
  background-color: var(--light-bg-secondary, #eaeaea);
  padding: 10px;
  border-radius: 12px;
}

[data-theme='dark'] .file-attachment {
  background-color: var(--dark-bg-secondary, #2a2a2a);
}

.file-icon {
  font-size: 1.5rem;
  margin-right: 10px;
  color: var(--light-primary, #4361ee);
}

[data-theme='dark'] .file-icon {
  color: var(--dark-primary, #90cdf4);
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 0.75rem;
  color: var(--light-text-secondary, #666);
}

[data-theme='dark'] .file-meta {
  color: var(--dark-text-secondary, #aaa);
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  font-size: 0.7rem;
  color: var(--light-text-secondary, #666);
}

[data-theme='dark'] .message-meta {
  color: var(--dark-text-secondary, #aaa);
}

.message-time {
  margin-right: 5px;
}

.message-status {
  font-size: 0.8rem;
  color: var(--light-text-secondary, #999);
}

[data-theme='dark'] .message-status {
  color: var(--dark-text-secondary, #777);
}

.message-status.read {
  color: var(--light-primary, #4361ee);
}

[data-theme='dark'] .message-status.read {
  color: var(--dark-primary, #90cdf4);
}

.typing-indicator-container {
  display: flex;
  align-items: center;
  margin-top: 5px;
  margin-bottom: 10px;
}

.typing-dots {
  display: flex;
  align-items: center;
  background-color: var(--light-card-bg, #fff);
  border-radius: 18px;
  padding: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  margin-right: 10px;
}

[data-theme='dark'] .typing-dots {
  background-color: var(--dark-card-bg, #1e1e1e);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.typing-dots span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: var(--light-text-secondary, #666);
  margin: 0 2px;
  animation: typingAnimation 1.5s infinite ease-in-out;
}

[data-theme='dark'] .typing-dots span {
  background-color: var(--dark-text-secondary, #aaa);
}

.typing-dots span:nth-child(1) {
  animation-delay: 0s;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.3s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.6s;
}

@keyframes typingAnimation {

  0%,
  60%,
  100% {
    transform: translateY(0);
  }

  30% {
    transform: translateY(-5px);
  }
}

.typing-text {
  font-size: 0.85rem;
  color: var(--light-text-secondary, #666);
}

[data-theme='dark'] .typing-text {
  color: var(--dark-text-secondary, #aaa);
}

.message-composer {
  background-color: var(--light-card-bg, #fff);
  border-top: 1px solid var(--light-border, #e0e0e0);
  padding: 10px 15px;
  z-index: 2;
}

[data-theme='dark'] .message-composer {
  background-color: var(--dark-card-bg, #1e1e1e);
  border-top-color: var(--dark-border, #444);
}

.attachment-preview {
  background-color: var(--light-bg-secondary, #eaeaea);
  border-radius: 12px;
  margin-bottom: 10px;
  overflow: hidden;
}

[data-theme='dark'] .attachment-preview {
  background-color: var(--dark-bg-secondary, #2a2a2a);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--light-border, #e0e0e0);
}

[data-theme='dark'] .preview-header {
  border-bottom-color: var(--dark-border, #444);
}

.file-name {
  font-size: 0.9rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 250px;
}

.remove-file {
  background: none;
  border: none;
  color: var(--light-text, #333);
  cursor: pointer;
  font-size: 0.9rem;
}

[data-theme='dark'] .remove-file {
  color: var(--dark-text, #eee);
}

.preview-content {
  padding: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.image-preview {
  max-width: 100%;
  max-height: 150px;
  border-radius: 8px;
}

.file-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
}

.input-container {
  display: flex;
  align-items: center;
  background-color: var(--light-bg, #f5f5f5);
  border-radius: 24px;
  padding: 8px 15px;
}

[data-theme='dark'] .input-container {
  background-color: var(--dark-bg, #121212);
}

.attach-button {
  background: none;
  border: none;
  color: var(--light-text-secondary, #666);
  font-size: 1.2rem;
  margin-right: 10px;
  cursor: pointer;
}

[data-theme='dark'] .attach-button {
  color: var(--dark-text-secondary, #aaa);
}

.file-input {
  display: none;
}

.message-input {
  flex: 1;
  background: none;
  border: none;
  font-size: 0.95rem;
  resize: none;
  max-height: 120px;
  padding: 5px 0;
  color: var(--light-text, #333);
}

[data-theme='dark'] .message-input {
  color: var(--dark-text, #eee);
}

.message-input:focus {
  outline: none;
}

.send-button {
  background: none;
  border: none;
  color: var(--light-text-secondary, #999);
  font-size: 1.2rem;
  margin-left: 10px;
  cursor: pointer;
  opacity: 0.6;
}

[data-theme='dark'] .send-button {
  color: var(--dark-text-secondary, #777);
}

.send-button.active {
  color: var(--light-primary, #4361ee);
  opacity: 1;
}

[data-theme='dark'] .send-button.active {
  color: var(--dark-primary, #90cdf4);
}

.send-button:disabled {
  cursor: default;
}

.user-info-panel {
  position: fixed;
  top: 0;
  right: -100%;
  width: 85%;
  height: 100%;
  background-color: var(--light-card-bg, #fff);
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 20;
  transition: right 0.3s ease;
  display: flex;
  flex-direction: column;
}

[data-theme='dark'] .user-info-panel {
  background-color: var(--dark-card-bg, #1e1e1e);
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.3);
}

.user-info-panel.open {
  right: 0;
}

.info-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid var(--light-border, #e0e0e0);
}

[data-theme='dark'] .info-panel-header {
  border-bottom-color: var(--dark-border, #444);
}

.info-panel-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.close-panel {
  background: none;
  border: none;
  color: var(--light-text, #333);
  font-size: 1.2rem;
  cursor: pointer;
}

[data-theme='dark'] .close-panel {
  color: var(--dark-text, #eee);
}

.info-panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.user-avatar.large {
  width: 80px;
  height: 80px;
  font-size: 2rem;
  margin-bottom: 15px;
}

.user-full-name {
  font-size: 1.3rem;
  margin: 0 0 20px;
  text-align: center;
}

.user-detail-item {
  display: flex;
  align-items: center;
  width: 100%;
  margin-bottom: 15px;
  color: var(--light-text-secondary, #666);
}

[data-theme='dark'] .user-detail-item {
  color: var(--dark-text-secondary, #aaa);
}

.detail-icon {
  margin-right: 10px;
  width: 20px;
}

.info-panel-actions {
  margin-top: 30px;
  width: 100%;
}

.panel-action-btn {
  display: flex;
  align-items: center;
  width: 100%;
  background: none;
  border: none;
  padding: 12px;
  border-radius: 8px;
  font-size: 1rem;
  color: var(--light-danger, #e53e3e);
  cursor: pointer;
  justify-content: center;
}

[data-theme='dark'] .panel-action-btn {
  color: var(--dark-danger, #fc8181);
}

.panel-action-btn span {
  margin-left: 10px;
}

.panel-action-btn:hover {
  background-color: var(--light-danger-light, #fff5f5);
}

[data-theme='dark'] .panel-action-btn:hover {
  background-color: var(--dark-danger-light, #3a1b1b);
}

.attachment-viewer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.9);
  z-index: 30;
  display: flex;
  flex-direction: column;
}

.attachment-viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background-color: rgba(0, 0, 0, 0.7);
}

.attachment-viewer-header h3 {
  color: white;
  margin: 0;
  font-size: 1.1rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 250px;
}

.close-viewer {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
}

.attachment-viewer-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  overflow: auto;
}

.attachment-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
}

.attachment-file {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.1);
  padding: 30px;
  border-radius: 10px;
  color: white;
}

.file-size {
  margin: 10px 0;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.download-link {
  display: flex;
  align-items: center;
  background-color: var(--light-primary, #4361ee);
  color: white;
  text-decoration: none;
  padding: 10px 15px;
  border-radius: 5px;
  margin-top: 15px;
}

.download-link span {
  margin-left: 8px;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--light-text-secondary, #666);
  text-align: center;
  padding: 20px;
}

[data-theme='dark'] .empty-chat {
  color: var(--dark-text-secondary, #aaa);
}

.empty-illustration {
  margin-bottom: 15px;
  color: var(--light-bg-secondary, #ddd);
}

[data-theme='dark'] .empty-illustration {
  color: var(--dark-bg-secondary, #444);
}

.empty-chat p {
  margin: 5px 0;
}

.empty-chat-hint {
  font-size: 0.9rem;
  opacity: 0.7;
}

.load-more-spinner {
  display: flex;
  justify-content: center;
  padding: 10px 0;
}
</style>