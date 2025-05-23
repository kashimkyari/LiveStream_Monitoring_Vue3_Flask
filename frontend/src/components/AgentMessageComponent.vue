<template>
  <div class="messaging-container" :class="{ 'mobile-view': isMobile }">
    <!-- User panel (sidebar) -->
    <div :class="[
      'user-panel',
      { 'collapsed': isMobile && !showSidebar }
    ]" ref="userPanel">
      <div class="panel-header">
        <div class="header-actions">
          <button class="filter-button" @click="toggleFilterDropdown" ref="filterButton">
            <font-awesome-icon icon="filter" />
            <span>{{ activeFilter === 'all' ? 'All' : activeFilter === 'online' ? 'Online' : 'Unread' }}</span>
            <font-awesome-icon icon="chevron-down" class="dropdown-icon" :class="{ 'rotated': showFilterDropdown }" />
          </button>
          <div v-if="showFilterDropdown" class="filter-dropdown" ref="filterDropdown">
            <button :class="['filter-option', { active: activeFilter === 'all' }]" @click="setFilter('all')">
              <font-awesome-icon icon="users" />
              <span>All Users</span>
            </button>
            <button :class="['filter-option', { active: activeFilter === 'online' }]" @click="setFilter('online')">
              <font-awesome-icon icon="circle" class="online-icon" />
              <span>Online Users</span>
            </button>
            <button :class="['filter-option', { active: activeFilter === 'unread' }]" @click="setFilter('unread')">
              <font-awesome-icon icon="envelope" />
              <span>Unread Messages</span>
            </button>
          </div>
        </div>
        <div class="search-wrapper">
          <font-awesome-icon icon="search" class="search-icon" />
          <input type="text" v-model="searchQuery" placeholder="Search users..." class="search-input"
            ref="searchInput" />
          <button v-if="searchQuery" class="clear-search" @click="searchQuery = ''">
            <font-awesome-icon icon="times-circle" />
          </button>
        </div>
      </div>

      <div class="users-list" ref="usersList">
        <div v-for="user in filteredUsers" :key="user.id" :class="['user-card', {
          'active': selectedUser?.id === user.id,
          'unread': unreadCounts[user.id] > 0
        }]" @click="handleUserSelect(user)" :data-user-id="user.id" ref="userCard">
          <div class="user-avatar" :style="getAvatarGradient(user.username)">
            <span>{{ getInitials(user.username) }}</span>
            <div :class="['status-indicator', getUserStatus(user)]"></div>
          </div>

          <div class="user-info">
            <div class="user-name-wrapper">
              <h3 class="user-name">{{ user.username }}</h3>
              <span class="message-time">{{ getLastMessageTime(user.id) }}</span>
            </div>
            <div class="last-message-wrapper">
              <p class="last-message">
                <span v-if="typingUsers[user.id]" class="typing-indicator-text">typing...</span>
                <span v-else>{{ getLastMessage(user.id) }}</span>
              </p>
              <div v-if="unreadCounts[user.id]" class="unread-badge">
                {{ unreadCounts[user.id] }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="isLoading && users.length === 0" class="loading-users">
          <div class="spinner"></div>
          <p>Loading contacts...</p>
        </div>

        <div v-else-if="filteredUsers.length === 0" class="empty-users-list">
          <font-awesome-icon icon="user-slash" class="empty-icon" />
          <p>{{ searchQuery ? 'No users match your search' : 'No users available' }}</p>
        </div>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="chat-area" ref="chatArea">
      <template v-if="selectedUser">
        <div class="chat-header" ref="chatHeader">
          <button v-if="isMobile" class="back-button" @click="showSidebar = true">
            <font-awesome-icon icon="arrow-left" />
          </button>

          <div class="user-avatar" :style="getAvatarGradient(selectedUser.username)">
            <span>{{ getInitials(selectedUser.username) }}</span>
            <div :class="['status-indicator', getUserStatus(selectedUser)]"></div>
          </div>

          <div class="chat-user-info">
            <h3>{{ selectedUser.username }}</h3>
            <p :class="['user-status-text', getUserStatus(selectedUser)]">
              {{ getUserStatus(selectedUser) === 'online' ? 'Online' : 'Offline' }}
              <span v-if="!selectedUser.online && selectedUser.last_active">
                • Last seen {{ formatTimeAgo(selectedUser.last_active) }}
              </span>
            </p>
          </div>

          <div class="chat-actions">
            <button class="action-button" @click="toggleInfoPanel">
              <font-awesome-icon icon="info-circle" />
            </button>
          </div>
        </div>

        <div class="messages-container" ref="messagesContainer" @scroll="handleScroll">
          <div v-if="isLoading" class="loading-messages">
            <div class="spinner"></div>
            <p>Loading messages...</p>
          </div>

          <div v-else-if="messages.length === 0" class="empty-messages">
            <font-awesome-icon icon="comments" class="empty-icon" />
            <p>No messages yet</p>
            <p class="start-hint">Start a conversation with {{ selectedUser.username }}</p>
          </div>

          <template v-else>
            <!-- Date groups -->
            <div v-for="(group, date) in messagesByDate" :key="date" class="date-group">
              <div class="date-separator">
                <div class="line"></div>
                <span class="date">{{ formatDateHeader(date) }}</span>
                <div class="line"></div>
              </div>

              <div v-for="(message, index) in group" :key="message.id || `temp-${message.tempId}`" class="message-group"
                ref="messageItem">
                <div class="message-time-header" v-if="shouldShowTimeHeader(message, group[index - 1])">
                  {{ formatTimeHeader(message.timestamp) }}
                </div>

                <div :class="['message', isUserMessage(message) ? 'sent' : 'received',
                  message.is_system ? 'system' : '']">
                  <template v-if="message.is_system">
                    <!-- System message template -->
                    <div class="system-message-content">
                      <font-awesome-icon icon="bell" class="system-icon" />
                      <p>{{ message.message }}</p>
                      <button v-if="message.details" class="details-btn"
                        @click="showNotificationDetails(message.details)">
                        Details
                      </button>
                    </div>
                  </template>
                  <template v-else>
                    <div class="message-bubble">
                      <!-- Add attachment preview if message has attachment -->
                      <div v-if="message.attachment" class="attachment-preview">
                        <div v-if="isImageAttachment(message.attachment)" class="image-attachment">
                          <img :src="message.attachment.url" @click="viewAttachment(message.attachment)" />
                        </div>
                        <div v-else class="file-attachment" @click="downloadAttachment(message.attachment)">
                          <font-awesome-icon icon="file" />
                          <span>{{ message.attachment.name }}</span>
                        </div>
                      </div>
                      <div class="message-content">{{ message.message }}</div>
                      <div class="message-meta">
                        <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                        <span v-if="isUserMessage(message)" class="message-status">
                          <span v-if="message.sending" class="sending-status">
                            <font-awesome-icon icon="circle-notch" spin />
                          </span>
                          <span v-else-if="message.error" class="error-status">
                            <font-awesome-icon icon="exclamation-circle" />
                          </span>
                          <span v-else>
                            {{ message.read ? '✓✓' : '✓' }}
                          </span>
                        </span>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </template>

          <!-- Typing indicator -->
          <div class="typing-indicator" v-if="isTyping">
            <div class="typing-bubble">
              <div class="typing-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
              </div>
              <span class="typing-name">{{ typingName }} is typing</span>
            </div>
          </div>
        </div>

        <!-- Message composer with attachment support -->
        <div class="message-composer" ref="messageComposer">
          <input type="file" ref="fileInput" style="display: none" @change="handleFileSelected" />

          <!-- Attachment preview -->
          <div v-if="selectedFile" class="attachment-preview-container">
            <div class="selected-file">
              <font-awesome-icon :icon="isImageFile(selectedFile) ? 'image' : 'file'" />
              <span>{{ selectedFile.name }}</span>
              <button class="remove-file-btn" @click="removeSelectedFile">
                <font-awesome-icon icon="times" />
              </button>
            </div>
          </div>

          <div class="composer-actions">
            <button class="composer-btn" @click="openFileSelector">
              <font-awesome-icon icon="paperclip" />
            </button>
          </div>

          <div class="input-wrapper">
            <textarea v-model="inputMessage" placeholder="Type a message..." @keydown.enter.prevent="sendMessage"
              @input="autoGrow" @keydown="handleTyping" ref="messageInput" rows="1"></textarea>
          </div>

          <button class="send-btn" :class="{ 'active': inputMessage.trim().length > 0 || selectedFile }"
            @click="sendMessage">
            <font-awesome-icon icon="paper-plane" />
          </button>
        </div>
      </template>

      <!-- Empty state when no user is selected -->
      <div v-else class="empty-chat-state">
        <font-awesome-icon icon="comment-dots" class="empty-icon" />
        <h3>Your Messages</h3>
        <p>Select a user to start chatting</p>
        <button v-if="isMobile" class="select-user-btn" @click="showSidebar = true">
          <font-awesome-icon icon="users" />
          Show Users
        </button>
      </div>
    </div>

    <!-- Info Panel (User Details) -->
    <div v-if="selectedUser && showInfoPanel" class="info-panel" :class="{ 'mobile-info-panel': isMobile }"
      ref="infoPanel">
      <div class="info-header">
        <h3>User Info</h3>
        <button class="close-info-btn" @click="toggleInfoPanel">
          <font-awesome-icon icon="times" />
        </button>
      </div>

      <div class="info-content">
        <div class="user-avatar large" :style="getAvatarGradient(selectedUser.username)">
          <span>{{ getInitials(selectedUser.username) }}</span>
        </div>

        <h2 class="user-fullname">{{ selectedUser.username }}</h2>

        <div class="user-details">
          <div class="detail-item">
            <font-awesome-icon icon="user" class="detail-icon" />
            <span class="detail-label">Username:</span>
            <span class="detail-value">{{ selectedUser.username }}</span>
          </div>

          <div class="detail-item">
            <font-awesome-icon icon="clock" class="detail-icon" />
            <span class="detail-label">Last active:</span>
            <span class="detail-value">{{ getLastActive(selectedUser) }}</span>
          </div>

          <div class="detail-item">
            <font-awesome-icon :icon="selectedUser.online ? 'circle' : 'circle'"
              :class="selectedUser.online ? 'online-icon' : 'offline-icon'" class="detail-icon" />
            <span class="detail-label">Status:</span>
            <span class="detail-value" :class="selectedUser.online ? 'online-text' : 'offline-text'">
              {{ selectedUser.online ? 'Online' : 'Offline' }}
            </span>
          </div>
        </div>

        <div class="info-actions">
          <button class="info-action-btn danger" @click="clearConversation">
            <font-awesome-icon icon="trash-alt" />
            <span>Clear Conversation</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Attachment viewer modal -->
    <div v-if="viewingAttachment" class="modal-overlay" @click.self="closeAttachmentModal">
      <div class="modal-content attachment-viewer">
        <button class="close-modal-btn" @click="closeAttachmentModal">
          <font-awesome-icon icon="times" />
        </button>
        <img v-if="viewingAttachment" :src="viewingAttachment.url" />
      </div>
    </div>

    <!-- Mobile toggle sidebar button (visible when sidebar is collapsed) -->
    <button v-if="isMobile && !showSidebar && !selectedUser" class="mobile-toggle-sidebar" @click="showSidebar = true">
      <font-awesome-icon icon="bars" />
    </button>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import axios from 'axios';
import { format, formatDistanceToNow, parseISO, isToday, isYesterday } from 'date-fns';
import { io } from 'socket.io-client';
import anime from 'animejs/lib/anime.es.js';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

// Configure axios to use the backend URL
axios.defaults.baseURL = '     https://monitor-backend.jetcamstudio.com:5000';

export default {
  name: 'AgentMessageComponent',
  components: {
    FontAwesomeIcon
  },
  props: {
    user: {
      type: Object,
      required: true
    }
  },
  emits: ['refresh-messages'],
  setup(props, { emit }) {
    // State
    const currentUser = ref(props.user); // Initialize with prop, will be updated from session
    const users = ref([]);
    const messages = ref([]);
    const selectedUser = ref(null);
    const inputMessage = ref('');
    const isLoading = ref(false);
    const sessionLoading = ref(true);
    const searchQuery = ref('');
    const showSidebar = ref(true);
    const isMobile = ref(false);
    const showInfoPanel = ref(false);
    const activeFilter = ref('all');
    const showFilterDropdown = ref(false);
    const notificationDetails = ref(null);
    const unreadCounts = reactive({});
    const typingUsers = reactive({});
    const socket = ref(null);
    const isConnected = ref(false);
    const isTyping = ref(false);
    const typingTimeout = ref(null);
    const selectedFile = ref(null);
    const viewingAttachment = ref(null);
    const pendingMessages = ref([]);
    const isScrolling = ref(false);
    const hasMoreMessages = ref(true);
    const page = ref(1);
    const messagesPerPage = ref(20);

    // Refs
    const userPanel = ref(null);
    const usersList = ref(null);
    const userCard = ref(null);
    const chatArea = ref(null);
    const chatHeader = ref(null);
    const messagesContainer = ref(null);
    const messageItem = ref(null);
    const messageComposer = ref(null);
    const messageInput = ref(null);
    const fileInput = ref(null);
    const infoPanel = ref(null);
    const searchInput = ref(null);
    const filterButton = ref(null);
    const filterDropdown = ref(null);

    // Computed
    const filteredUsers = computed(() => {
      let result = users.value;

      // Apply search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase();
        result = result.filter(user =>
          user.username.toLowerCase().includes(query)
        );
      }

      // Apply status filter
      if (activeFilter.value === 'online') {
        result = result.filter(user => user.online);
      } else if (activeFilter.value === 'unread') {
        result = result.filter(user => unreadCounts[user.id] && unreadCounts[user.id] > 0);
      }

      // Filter out current user
      result = result.filter(user => user.id !== currentUser.value.id);

      // Sort: first unread, then online, then alphabetically
      return result.sort((a, b) => {
        // First by unread
        const aHasUnread = unreadCounts[a.id] > 0;
        const bHasUnread = unreadCounts[b.id] > 0;
        if (aHasUnread && !bHasUnread) return -1;
        if (!aHasUnread && bHasUnread) return 1;

        // Then by online status
        if (a.online && !b.online) return -1;
        if (!a.online && b.online) return 1;

        // Then by last message time (most recent first)
        const aLastMsg = getLastSingleMessage(a.id);
        const bLastMsg = getLastSingleMessage(b.id);

        if (aLastMsg && bLastMsg) {
          return new Date(bLastMsg.timestamp) - new Date(aLastMsg.timestamp);
        }

        if (aLastMsg && !bLastMsg) return -1;
        if (!aLastMsg && bLastMsg) return 1;

        // Finally by username
        return a.username.localeCompare(b.username);
      });
    });

    const messagesByDate = computed(() => {
      const groupedMessages = {};

      messages.value.forEach(message => {
        const date = new Date(message.timestamp).toLocaleDateString();
        if (!groupedMessages[date]) {
          groupedMessages[date] = [];
        }
        groupedMessages[date].push(message);
      });

      return groupedMessages;
    });

    const typingName = computed(() => {
      return selectedUser.value ? selectedUser.value.username : '';
    });

    // Methods
    const fetchCurrentUser = async () => {
      sessionLoading.value = true;
      try {
        const response = await axios.get('/api/session');
        if (response.data && response.data.user) {
          currentUser.value = response.data.user;
        }
      } catch (error) {
        console.error('Error fetching current user:', error);
        // Keep using props.user as fallback
      } finally {
        sessionLoading.value = false;
      }
    };

    const initSocket = () => {
      // Connect to the backend at     https://monitor-backend.jetcamstudio.com:5000
      socket.value = io('https://monitor-backend.jetcamstudio.com:5000/messages', {
        path: '/ws',
        transports: ['websocket']
      });

      socket.value.on('connect', () => {
        console.log('Connected to WebSocket server at     https://monitor-backend.jetcamstudio.com:5000');
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
      isLoading.value = true;
      try {
        const response = await axios.get('/api/online-users');
        users.value = response.data;

        // Initialize unread counts
        users.value.forEach(user => {
          fetchUnreadCount(user.id);
        });

        // Apply animations to user cards
        nextTick(() => {
          animateUserCards();
        });
      } catch (error) {
        console.error('Error fetching users:', error);
      } finally {
        isLoading.value = false;
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

        messages.value = response.data;
        hasMoreMessages.value = response.data.length === messagesPerPage.value;

        // Mark received messages as read
        markMessagesAsRead();

        // Scroll to bottom
        await nextTick();
        scrollToBottom();

        // Animate messages entrance
        animateMessagesEntrance();
      } catch (error) {
        console.error('Error fetching messages:', error);
      } finally {
        isLoading.value = false;
      }
    };

    const loadMoreMessages = async () => {
      if (!selectedUser.value || !hasMoreMessages.value || isLoading.value) return;

      isLoading.value = true;
      page.value += 1;

      try {
        const response = await axios.get(`/api/messages/${selectedUser.value.id}`, {
          params: {
            page: page.value,
            limit: messagesPerPage.value
          }
        });

        const oldMessages = response.data;
        hasMoreMessages.value = oldMessages.length === messagesPerPage.value;

        if (oldMessages.length > 0) {
          // Preserve scroll position
          const currentScrollTop = messagesContainer.value.scrollTop;
          const currentHeight = messagesContainer.value.scrollHeight;

          // Add messages to the beginning
          messages.value = [...oldMessages, ...messages.value];

          // Restore scroll position
          await nextTick();
          const newHeight = messagesContainer.value.scrollHeight;
          messagesContainer.value.scrollTop = currentScrollTop + (newHeight - currentHeight);

          // Animate new messages
          animateOlderMessagesEntrance();
        }
      } catch (error) {
        console.error('Error loading more messages:', error);
      } finally {
        isLoading.value = false;
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

    const markMessagesAsRead = async () => {
      if (!selectedUser.value) return;

      try {
        // Mark messages as read in the UI
        messages.value.forEach(message => {
          if (!isUserMessage(message) && !message.read) {
            message.read = true;
          }
        });

        // Reset unread counter
        unreadCounts[selectedUser.value.id] = 0;

        // Inform the server that messages were read
        await axios.post(`/api/messages/${selectedUser.value.id}/mark-read`);

        // Emit event to notify sender that messages were read
        if (isConnected.value) {
          socket.value.emit('message_read', {
            recipient_id: selectedUser.value.id,
            sender_id: currentUser.value.id
          });
        }
      } catch (error) {
        console.error('Error marking messages as read:', error);
      }
    };

    const handleUserSelect = async (user) => {
      // Don't reload if already selected
      if (selectedUser.value?.id === user.id) {
        // Just close the sidebar on mobile if the user is already selected
        if (isMobile.value) {
          showSidebar.value = false;
        }
        return;
      }

      // Animate selection
      animateUserCardSelection(user);

      // Set the selected user
      selectedUser.value = user;

      // On mobile, hide sidebar after selection
      if (isMobile.value) {
        showSidebar.value = false;
      }

      // Fetch messages
      await fetchMessages(user.id);

      // Focus the message input
      await nextTick();
      if (messageInput.value) {
        messageInput.value.focus();
      }
    };

    const sendMessage = async () => {
      if ((!inputMessage.value.trim() && !selectedFile.value) || !selectedUser.value) return;

      // Prepare message object
      const messageData = {
        recipient_id: selectedUser.value.id,
        message: inputMessage.value.trim(),
        timestamp: new Date().toISOString(),
        read: false,
        sending: true // Add a flag to indicate the message is sending
      };

      // Add file if present
      if (selectedFile.value) {
        const formData = new FormData();
        formData.append('file', selectedFile.value);

        try {
          const uploadResponse = await axios.post('/api/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          });

          messageData.attachment = {
            url: uploadResponse.data.url,
            name: selectedFile.value.name,
            type: selectedFile.value.type,
            size: selectedFile.value.size
          };

          // Clear the selected file
          removeSelectedFile();
        } catch (error) {
          console.error('Error uploading file:', error);
          // Continue without attachment if upload fails
        }
      }

      // Generate a temporary ID
      const tempId = `temp-${Date.now()}`;
      messageData.id = tempId;

      // Add to messages list
      messages.value.push(messageData);

      // Clear input and resize
      inputMessage.value = '';
      if (messageInput.value) {
        messageInput.value.style.height = 'auto';
      }

      // Scroll to bottom
      await nextTick();
      scrollToBottom();

      // Animate the new message
      const lastMessage = document.querySelector('.message:last-child');
      if (lastMessage) {
        anime({
          targets: lastMessage,
          opacity: [0, 1],
          translateY: [10, 0],
          duration: 300,
          easing: 'easeOutQuad'
        });
      }

      // Actually send the message
      try {
        // Send via socket if connected
        if (isConnected.value) {
          socket.value.emit('send_message', {
            receiver_username: selectedUser.value.username,
            message: messageData.message,
            attachment: messageData.attachment || null
          });
        } else {
          // Store for sending when reconnected
          pendingMessages.value.push({
            receiver_username: selectedUser.value.username,
            message: messageData.message,
            attachment: messageData.attachment || null
          });

          // Try API fallback
          sendMessageAPI(messageData, tempId);
        }
      } catch (error) {
        console.error('Error sending message:', error);
        // Mark message as failed
        const index = messages.value.findIndex(m => m.id === tempId);
        if (index !== -1) {
          messages.value[index].sending = false;
          messages.value[index].error = true;
        }
      }
    };

    const sendMessageAPI = async (messageData, tempId) => {
      try {
        // Remove sending flag for API
        const apiData = { ...messageData };
        delete apiData.sending;
        delete apiData.id;

        const response = await axios.post('/api/messages', apiData);

        // Update the temp message with the real one
        const index = messages.value.findIndex(m => m.id === tempId);
        if (index !== -1) {
          messages.value[index] = {
            ...response.data,
            sending: false
          };
        }
      } catch (error) {
        console.error('Error sending message via API:', error);
        // Mark message as failed
        const index = messages.value.findIndex(m => m.id === tempId);
        if (index !== -1) {
          messages.value[index].sending = false;
          messages.value[index].error = true;
        }
      }
    };

    const sendPendingMessages = () => {
      if (pendingMessages.value.length === 0 || !isConnected.value) return;

      pendingMessages.value.forEach(message => {
        socket.value.emit('send_message', {
          receiver_username: message.receiver_username,
          message: message.message,
          attachment: message.attachment || null
        });
      });

      pendingMessages.value = [];
    };

    const handleIncomingMessage = (message) => {
      // Check if message already exists
      const exists = messages.value.some(m =>
        m.id === message.id ||
        (m.timestamp === message.timestamp && m.message === message.message)
      );

      if (exists) return;

      // Check if message is from or to selected user
      const isFromSelected = message.sender_id === selectedUser.value?.id;
      const isToSelected = message.recipient_id === selectedUser.value?.id;

      if (isFromSelected || isToSelected) {
        // Update messages array
        messages.value.push(message);

        // Mark as read if it's from the selected user
        if (isFromSelected) {
          markMessagesAsRead();
        }

        // Scroll to bottom and animate
        nextTick(() => {
          scrollToBottom();
          const lastMessage = document.querySelector('.message:last-child');
          if (lastMessage) {
            anime({
              targets: lastMessage,
              opacity: [0, 1],
              translateY: [10, 0],
              duration: 300,
              easing: 'easeOutQuad'
            });
          }
        });
      } else {
        // Message is from another user, update their unread count
        const senderId = message.sender_id;
        unreadCounts[senderId] = (unreadCounts[senderId] || 0) + 1;

        // Animate the user card for the sender
        const senderCard = Array.from(userCard.value || []).find(card =>
          card.getAttribute('data-user-id') === senderId.toString()
        );

        if (senderCard) {
          anime({
            targets: senderCard,
            backgroundColor: [
              'rgba(59, 130, 246, 0.1)',
              'rgba(59, 130, 246, 0)',
            ],
            duration: 1000,
            easing: 'easeOutQuad'
          });
        }
      }
    };

    const updateUserStatus = (data) => {
      const { userId, online } = data;

      // Find user and update status
      const userIndex = users.value.findIndex(u => u.id === userId);
      if (userIndex !== -1) {
        users.value[userIndex].online = online;

        // Animate status change
        const userCard = Array.from(userCard.value || []).find(card =>
          card.getAttribute('data-user-id') === userId.toString()
        );

        if (userCard) {
          const statusIndicator = userCard.querySelector('.status-indicator');
          if (statusIndicator) {
            anime({
              targets: statusIndicator,
              scale: [1, 1.5, 1],
              opacity: [0.5, 1],
              duration: 500,
              easing: 'easeOutElastic(1, .5)'
            });
          }
        }
      }

      // Update selected user if needed
      if (selectedUser.value && selectedUser.value.id === userId) {
        selectedUser.value.online = online;
      }
    };

    const handleTypingIndicator = (data) => {
      // Check if the data contains sender_username
      if (!data.sender_username) return;

      // Find the user by username
      const typingUser = users.value.find(u => u.username === data.sender_username);
      if (!typingUser) return;

      const userId = typingUser.id;
      const typing = data.typing;

      // Only care about selected user's typing status
      if (selectedUser.value && userId === selectedUser.value.id) {
        isTyping.value = typing;

        if (typing) {
          // Show typing indicator with animation
          nextTick(() => {
            const typingIndicator = document.querySelector('.typing-indicator');
            if (typingIndicator) {
              anime({
                targets: typingIndicator,
                opacity: [0, 1],
                translateY: [10, 0],
                duration: 300,
                easing: 'easeOutQuad'
              });
            }
          });
        }
      }

      // Update typing status for all users
      typingUsers[userId] = typing;

      // If not selected, animate the user card
      if (typing && (!selectedUser.value || selectedUser.value.id !== userId)) {
        const userCard = Array.from(userCard.value || []).find(card =>
          card.getAttribute('data-user-id') === userId.toString()
        );

        if (userCard) {
          const typingText = userCard.querySelector('.typing-indicator-text');
          if (typingText) {
            anime({
              targets: typingText,
              opacity: [0, 1],
              duration: 300,
              easing: 'easeOutQuad'
            });
          }
        }
      }
    };

    const handleTyping = () => {
      if (!selectedUser.value || !isConnected.value) return;

      // Clear previous timeout
      if (typingTimeout.value) {
        clearTimeout(typingTimeout.value);
      }

      // Send typing indicator
      socket.value.emit('typing', {
        receiver_username: selectedUser.value.username,
        typing: true
      });

      // Set timeout to stop typing indicator
      typingTimeout.value = setTimeout(() => {
        if (socket.value && isConnected.value) {
          socket.value.emit('typing', {
            receiver_username: selectedUser.value.username,
            typing: false
          });
        }
      }, 2000);
    };

    const autoGrow = () => {
      if (!messageInput.value) return;

      // Reset height to calculate scroll height correctly
      messageInput.value.style.height = 'auto';

      // Calculate new height (with max height)
      const newHeight = Math.min(messageInput.value.scrollHeight, 150);
      messageInput.value.style.height = `${newHeight}px`;
    };

    const isUserMessage = (message) => {
      return message.sender_id === currentUser.value.id;
    };

    const getLastSingleMessage = (userId) => {
      // Find last message for user
      const userMessages = messages.value.filter(m =>
        m.sender_id === userId || m.recipient_id === userId
      );

      if (userMessages.length === 0) return null;

      return userMessages[userMessages.length - 1];
    };

    const getLastMessage = (userId) => {
      const lastMessage = getLastSingleMessage(userId);

      if (!lastMessage) return 'No messages yet';

      if (lastMessage.attachment) {
        return isImageAttachment(lastMessage.attachment)
          ? '📷 Image'
          : `📎 ${lastMessage.attachment.name}`;
      }

      return lastMessage.message.length > 30
        ? lastMessage.message.substring(0, 30) + '...'
        : lastMessage.message;
    };

    const getLastMessageTime = (userId) => {
      const lastMessage = getLastSingleMessage(userId);
      if (!lastMessage) return '';

      return formatMessageTime(lastMessage.timestamp);
    };

    const formatMessageTime = (timestamp) => {
      if (!timestamp) return '';

      const date = parseISO(timestamp);
      const now = new Date();

      if (isToday(date)) {
        return format(date, 'HH:mm');
      } else if (isYesterday(date)) {
        return 'Yesterday';
      } else if (now.getFullYear() === date.getFullYear()) {
        return format(date, 'MMM d');
      } else {
        return format(date, 'MM/dd/yy');
      }
    };

    const getUserStatus = (user) => {
      return user.online ? 'online' : 'offline';
    };

    const getInitials = (username) => {
      if (!username) return '';

      const parts = username.split(' ');
      if (parts.length > 1) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }

      return username[0].toUpperCase();
    };

    const getAvatarGradient = (username) => {
      // Generate consistent color based on username
      const hash = username.split('').reduce((acc, char) => {
        return char.charCodeAt(0) + ((acc << 5) - acc);
      }, 0);

      const h = Math.abs(hash) % 360;
      const s = 65 + (Math.abs(hash) % 25); // 65-90%
      const l = 45 + (Math.abs(hash) % 15); // 45-60%

      return {
        background: `linear-gradient(135deg, hsl(${h}, ${s}%, ${l}%), hsl(${(h + 40) % 360}, ${s}%, ${l - 10}%))`
      };
    };

    const formatDateHeader = (dateString) => {
      const date = new Date(dateString);
      const today = new Date();

      if (isToday(date)) {
        return 'Today';
      } else if (isYesterday(date)) {
        return 'Yesterday';
      } else if (date.getFullYear() === today.getFullYear()) {
        return format(date, 'MMMM d');
      } else {
        return format(date, 'MMMM d, yyyy');
      }
    };

    const formatTimeHeader = (timestamp) => {
      if (!timestamp) return '';
      return format(parseISO(timestamp), 'h:mm a');
    };

    const formatTime = (timestamp) => {
      if (!timestamp) return '';
      return format(parseISO(timestamp), 'HH:mm');
    };

    const formatTimeAgo = (timestamp) => {
      if (!timestamp) return '';
      return formatDistanceToNow(parseISO(timestamp), { addSuffix: true });
    };

    const shouldShowTimeHeader = (message, prevMessage) => {
      if (!prevMessage) return true;

      const current = parseISO(message.timestamp);
      const previous = parseISO(prevMessage.timestamp);

      // Show time header if there's a 15-minute gap
      return Math.abs(current - previous) > 15 * 60 * 1000;
    };

    const getLastActive = (user) => {
      if (user.online) return 'Now';
      if (!user.last_active) return 'Unknown';

      return formatDistanceToNow(parseISO(user.last_active), { addSuffix: true });
    };

    const scrollToBottom = () => {
      if (!messagesContainer.value) return;

      const container = messagesContainer.value;
      container.scrollTop = container.scrollHeight;
    };

    const toggleInfoPanel = () => {
      showInfoPanel.value = !showInfoPanel.value;

      // Animate panel
      nextTick(() => {
        if (infoPanel.value) {
          if (showInfoPanel.value) {
            // Show animation
            anime({
              targets: infoPanel.value,
              translateX: [300, 0],
              opacity: [0, 1],
              duration: 300,
              easing: 'easeOutQuad'
            });
          } else {
            // Hide animation
            anime({
              targets: infoPanel.value,
              translateX: [0, 300],
              opacity: [1, 0],
              duration: 300,
              easing: 'easeOutQuad'
            });
          }
        }
      });
    };

    const clearConversation = async () => {
      if (!selectedUser.value) return;

      try {
        await axios.delete(`/api/messages/${selectedUser.value.id}`);

        // Clear messages in UI
        messages.value = [];

        // Animate info panel exit
        if (infoPanel.value) {
          anime({
            targets: infoPanel.value,
            translateX: [0, 300],
            opacity: [1, 0],
            duration: 300,
            easing: 'easeOutQuad',
            complete: () => {
              showInfoPanel.value = false;
            }
          });
        }
      } catch (error) {
        console.error('Error clearing conversation:', error);
      }
    };

    const openFileSelector = () => {
      if (fileInput.value) {
        fileInput.value.click();
      }
    };

    const handleFileSelected = (event) => {
      const file = event.target.files[0];
      if (!file) return;

      selectedFile.value = file;

      // Animate attachment preview
      nextTick(() => {
        const preview = document.querySelector('.attachment-preview-container');
        if (preview) {
          anime({
            targets: preview,
            opacity: [0, 1],
            height: [0, 'auto'],
            duration: 300,
            easing: 'easeOutQuad'
          });
        }
      });
    };

    const removeSelectedFile = () => {
      if (!selectedFile.value) return;

      // Animate attachment preview removal
      const preview = document.querySelector('.attachment-preview-container');
      if (preview) {
        anime({
          targets: preview,
          opacity: [1, 0],
          height: ['auto', 0],
          duration: 300,
          easing: 'easeOutQuad',
          complete: () => {
            selectedFile.value = null;
            if (fileInput.value) {
              fileInput.value.value = '';
            }
          }
        });
      } else {
        selectedFile.value = null;
        if (fileInput.value) {
          fileInput.value.value = '';
        }
      }
    };

    const isImageAttachment = (attachment) => {
      return attachment.type && attachment.type.startsWith('image/');
    };

    const isImageFile = (file) => {
      return file.type && file.type.startsWith('image/');
    };

    const viewAttachment = (attachment) => {
      viewingAttachment.value = attachment;

      // Animate modal entrance
      nextTick(() => {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
          anime({
            targets: modal,
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutQuad'
          });

          anime({
            targets: modal.querySelector('.modal-content'),
            scale: [0.9, 1],
            opacity: [0, 1],
            duration: 400,
            easing: 'easeOutQuad'
          });
        }
      });
    };

    const closeAttachmentModal = () => {
      // Animate modal exit
      const modal = document.querySelector('.modal-overlay');
      if (modal) {
        anime({
          targets: modal,
          opacity: [1, 0],
          duration: 300,
          easing: 'easeOutQuad',
          complete: () => {
            viewingAttachment.value = null;
          }
        });

        anime({
          targets: modal.querySelector('.modal-content'),
          scale: [1, 0.9],
          opacity: [1, 0],
          duration: 300,
          easing: 'easeOutQuad'
        });
      } else {
        viewingAttachment.value = null;
      }
    };

    const downloadAttachment = (attachment) => {
      // Create a hidden anchor and trigger download
      const a = document.createElement('a');
      a.href = attachment.url;
      a.download = attachment.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    };

    const toggleFilterDropdown = () => {
      showFilterDropdown.value = !showFilterDropdown.value;

      // Animate dropdown
      nextTick(() => {
        if (filterDropdown.value) {
          if (showFilterDropdown.value) {
            // Show animation
            anime({
              targets: filterDropdown.value,
              opacity: [0, 1],
              translateY: [-10, 0],
              scaleY: [0.8, 1],
              duration: 300,
              easing: 'easeOutQuad'
            });
          }
        }

        // Animate icon rotation
        if (filterButton.value) {
          anime({
            targets: filterButton.value.querySelector('.dropdown-icon'),
            rotate: showFilterDropdown.value ? [0, 180] : [180, 0],
            duration: 300,
            easing: 'easeOutQuad'
          });
        }
      });
    };

    const setFilter = (filter) => {
      activeFilter.value = filter;
      showFilterDropdown.value = false;

      // Animate filter change
      nextTick(() => {
        anime({
          targets: usersList.value,
          opacity: [0.8, 1],
          translateY: [5, 0],
          duration: 300,
          easing: 'easeOutQuad'
        });
      });
    };

    const handleScroll = () => {
      if (!messagesContainer.value) return;

      isScrolling.value = true;

      const container = messagesContainer.value;

      // Check if user scrolled to top (load more messages)
      if (container.scrollTop < 50 && hasMoreMessages.value && !isLoading.value) {
        loadMoreMessages();
      }

      clearTimeout(isScrolling.value);
      isScrolling.value = setTimeout(() => {
        isScrolling.value = false;
      }, 100);
    };

    const showNotificationDetails = (details) => {
      notificationDetails.value = details;
      // Show details modal or panel
    };

    // Animation functions
    const animateUserCards = () => {
      if (!userCard.value || userCard.value.length === 0) return;

      anime({
        targets: userCard.value,
        opacity: [0, 1],
        translateY: [10, 0],
        delay: anime.stagger(50),
        duration: 400,
        easing: 'easeOutCubic'
      });
    };

    const animateUserCardSelection = (user) => {
      const userCards = userCard.value;
      if (!userCards || userCards.length === 0) return;

      // Find the card for the selected user
      const selectedCard = Array.from(userCards).find(
        card => card.getAttribute('data-user-id') === user.id.toString()
      );

      if (selectedCard) {
        anime({
          targets: selectedCard,
          scale: [1, 1.05, 1],
          backgroundColor: [
            'rgba(var(--primary-rgb), 0.1)',
            'rgba(var(--primary-rgb), 0.2)',
            'rgba(var(--primary-rgb), 0.1)'
          ],
          duration: 600,
          easing: 'easeOutElastic(1, .6)'
        });
      }
    };

    const animateMessagesEntrance = () => {
      if (!messageItem.value || messageItem.value.length === 0) return;

      anime({
        targets: messageItem.value,
        opacity: [0, 1],
        translateY: [10, 0],
        delay: anime.stagger(50),
        duration: 400,
        easing: 'easeOutCubic'
      });
    };

    const animateOlderMessagesEntrance = () => {
      if (!messageItem.value || messageItem.value.length < messagesPerPage.value) return;

      const oldMessages = Array.from(messageItem.value).slice(0, messagesPerPage.value);

      anime({
        targets: oldMessages,
        opacity: [0, 1],
        translateY: [-10, 0],
        delay: anime.stagger(20),
        duration: 300,
        easing: 'easeOutCubic'
      });
    };

    // Lifecycle hooks
    onMounted(async () => {
      // Check for mobile view
      isMobile.value = window.innerWidth < 768;
      window.addEventListener('resize', () => {
        isMobile.value = window.innerWidth < 768;
      });

      // Fetch current user from session
      await fetchCurrentUser();

      // Initialize socket connection
      initSocket();

      // Fetch users
      fetchUsers();

      // Component entrance animation
      nextTick(() => {
        anime({
          targets: '.messaging-container',
          opacity: [0, 1],
          duration: 500,
          easing: 'easeOutCubic'
        });
      });
    });

    onBeforeUnmount(() => {
      // Clean up event listeners
      window.removeEventListener('resize', () => {
        isMobile.value = window.innerWidth < 768;
      });

      // Disconnect socket
      if (socket.value) {
        socket.value.disconnect();
      }

      // Clear any pending timeouts
      if (typingTimeout.value) {
        clearTimeout(typingTimeout.value);
      }
    });

    // Watch handlers
    watch(selectedUser, (newUser, oldUser) => {
      if (newUser && newUser.id !== oldUser?.id) {
        // Animate chat area when user is selected
        anime({
          targets: chatArea.value,
          opacity: [0.5, 1],
          translateY: [10, 0],
          duration: 300,
          easing: 'easeOutCubic'
        });
      }
    });

    watch(searchQuery, () => {
      // Animate filtered results
      nextTick(() => {
        if (userCard.value && userCard.value.length > 0) {
          anime({
            targets: userCard.value,
            opacity: [0.5, 1],
            translateX: [-10, 0],
            delay: anime.stagger(30),
            duration: 300,
            easing: 'easeOutCubic'
          });
        }
      });
    });

    // Public methods
    const refreshMessages = () => {
      fetchUsers();
      if (selectedUser.value) {
        fetchMessages(selectedUser.value.id);
      }
      emit('refresh-messages');
    };

    return {
      // State
      users,
      filteredUsers,
      messages,
      messagesByDate,
      selectedUser,
      inputMessage,
      isLoading,
      searchQuery,
      showSidebar,
      isMobile,
      showInfoPanel,
      activeFilter,
      showFilterDropdown,
      typingUsers,
      isTyping,
      typingName,
      selectedFile,
      viewingAttachment,
      hasMoreMessages,
      unreadCounts,

      // Refs
      userPanel,
      usersList,
      userCard,
      chatArea,
      chatHeader,
      messagesContainer,
      messageItem,
      messageComposer,
      messageInput,
      fileInput,
      infoPanel,
      searchInput,
      filterButton,
      filterDropdown,

      // Methods
      handleUserSelect,
      sendMessage,
      handleTyping,
      autoGrow,
      scrollToBottom,
      handleScroll,
      toggleInfoPanel,
      clearConversation,
      openFileSelector,
      handleFileSelected,
      removeSelectedFile,
      viewAttachment,
      closeAttachmentModal,
      downloadAttachment,
      toggleFilterDropdown,
      setFilter,
      refreshMessages,
      isUserMessage,
      getLastMessage,
      getLastMessageTime,
      getUserStatus,
      getInitials,
      getAvatarGradient,
      formatDateHeader,
      formatTimeHeader,
      formatTime,
      formatTimeAgo,
      shouldShowTimeHeader,
      getLastActive,
      isImageAttachment,
      isImageFile,
      showNotificationDetails
    };
  }
};
</script>

<style scoped>
.messaging-container {
  display: flex;
  height: 100%;
  width: 100%;
  background-color: var(--bg-color, #f8f9fa);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
  position: relative;
}

/* User panel (sidebar) */
.user-panel {
  width: 350px;
  min-width: 300px;
  height: 100%;
  border-right: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
  background-color: var(--card-bg, #ffffff);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
  background-color: var(--header-bg, #ffffff);
}

.panel-header h2 {
  margin: 0 0 15px;
  font-size: 1.5rem;
  color: var(--heading-color, #333);
  font-weight: 600;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  position: relative;
}

.filter-button {
  display: flex;
  align-items: center;
  background: var(--button-secondary-bg, #f0f2f5);
  border: 1px solid var(--button-secondary-border, rgba(0, 0, 0, 0.1));
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.9rem;
  color: var(--text-color, #333);
  cursor: pointer;
  transition: all 0.2s;
}

.filter-button:hover {
  background-color: var(--button-secondary-hover-bg, #e4e6e9);
}

.dropdown-icon {
  margin-left: 5px;
  transition: transform 0.2s;
}

.dropdown-icon.rotated {
  transform: rotate(180deg);
}

.filter-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 200px;
  background-color: var(--dropdown-bg, #fff);
  border: 1px solid var(--dropdown-border, rgba(0, 0, 0, 0.1));
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 10;
  margin-top: 5px;
  overflow: hidden;
  transform-origin: top center;
}

.filter-option {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  font-size: 0.9rem;
  color: var(--text-color, #333);
  cursor: pointer;
  transition: background-color 0.2s;
}

.filter-option:hover {
  background-color: var(--dropdown-hover-bg, #f0f2f5);
}

.filter-option.active {
  background-color: var(--dropdown-active-bg, rgba(0, 123, 255, 0.1));
  color: var(--primary-color, #0a84ff);
  font-weight: 500;
}

.filter-option span {
  margin-left: 10px;
}

.online-icon {
  color: var(--online-color, #4caf50);
  font-size: 0.7rem;
}

.search-wrapper {
  display: flex;
  align-items: center;
  background-color: var(--input-bg, #f0f2f5);
  border: 1px solid var(--input-border, rgba(0, 0, 0, 0.1));
  border-radius: 20px;
  padding: 8px 12px;
  transition: border-color 0.2s;
}

.search-wrapper:focus-within {
  border-color: var(--primary-color, #0a84ff);
}

.search-icon {
  color: var(--text-muted, #8e8e8e);
  margin-right: 8px;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.95rem;
  color: var(--text-color, #333);
}

.search-input::placeholder {
  color: var(--text-muted, #8e8e8e);
}

.clear-search {
  background: none;
  border: none;
  color: var(--text-muted, #8e8e8e);
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.clear-search:hover {
  color: var(--text-color, #333);
}

.users-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.user-card {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 5px;
}

.user-card:hover {
  background-color: var(--card-hover-bg, #f0f2f5);
}

.user-card.active {
  background-color: var(--card-active-bg, rgba(0, 123, 255, 0.1));
}

.user-card.unread {
  background-color: var(--notification-bg, rgba(0, 123, 255, 0.05));
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  font-weight: 600;
  font-size: 1.1rem;
  position: relative;
  margin-right: 12px;
  flex-shrink: 0;
}

.user-avatar.large {
  width: 80px;
  height: 80px;
  font-size: 1.8rem;
  margin: 0 auto 15px;
}

.status-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--offline-color, #8e8e8e);
  border: 2px solid var(--card-bg, #fff);
}

.status-indicator.online {
  background-color: var(--online-color, #4caf50);
}

.user-info {
  flex: 1;
  min-width: 0;
  /* Needed for text-overflow to work */
}

.user-name-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 3px;
}

.user-name {
  margin: 0;
  font-size: 1rem;
  color: var(--text-color, #333);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-muted, #8e8e8e);
  white-space: nowrap;
  margin-left: 5px;
}

.last-message-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.last-message {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted, #8e8e8e);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.typing-indicator-text {
  color: var(--primary-color, #0a84ff);
  font-style: italic;
}

.unread-badge {
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  background-color: var(--primary-color, #0a84ff);
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0 6px;
  margin-left: 8px;
}

.loading-users,
.empty-users-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  color: var(--text-muted, #8e8e8e);
  text-align: center;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid var(--spinner-trail, #f0f2f5);
  border-top-color: var(--primary-color, #0a84ff);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 15px;
  color: var(--text-muted, #8e8e8e);
  opacity: 0.5;
}

/* Chat Area */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color, #f8f9fa);
  position: relative;
}

.chat-header {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background-color: var(--header-bg, #ffffff);
  border-bottom: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
}

.back-button {
  background: none;
  border: none;
  color: var(--text-color, #333);
  margin-right: 15px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.back-button:hover {
  background-color: var(--button-hover-bg, #f0f2f5);
}

.chat-user-info {
  flex: 1;
  margin-left: 15px;
}

.chat-user-info h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--text-color, #333);
  font-weight: 600;
}

.user-status-text {
  margin: 5px 0 0;
  font-size: 0.85rem;
  color: var(--text-muted, #8e8e8e);
}

.user-status-text.online {
  color: var(--online-color, #4caf50);
}

.chat-actions {
  display: flex;
  gap: 10px;
}

.action-button {
  background: none;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: var(--text-color, #333);
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-button:hover {
  background-color: var(--button-hover-bg, #f0f2f5);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--messages-bg, #f0f2f5);
}

.loading-messages,
.empty-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted, #8e8e8e);
  text-align: center;
}

.start-hint {
  margin-top: 5px;
  font-size: 0.9rem;
  opacity: 0.7;
}

.date-group {
  margin-bottom: 20px;
}

.date-separator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 15px 0;
  color: var(--text-muted, #8e8e8e);
}

.line {
  flex: 1;
  height: 1px;
  background-color: var(--separator-line, rgba(0, 0, 0, 0.1));
}

.date {
  padding: 0 15px;
  font-size: 0.85rem;
  font-weight: 600;
}

.message-group {
  margin-bottom: 12px;
}

.message-time-header {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted, #8e8e8e);
  margin: 15px 0 5px;
  font-weight: 500;
}

.message {
  max-width: 70%;
  margin-bottom: 3px;
  clear: both;
  position: relative;
}

.message.sent {
  float: right;
}

.message.received {
  float: left;
}

.message.system {
  max-width: 80%;
  margin: 15px auto;
  clear: both;
  float: none;
  text-align: center;
}

.message-bubble {
  padding: 12px 15px;
  border-radius: 18px;
  position: relative;
  font-size: 0.95rem;
  color: var(--text-color, #333);
  background-color: var(--message-received-bg, #ffffff);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.sent .message-bubble {
  background-color: var(--message-sent-bg, #0a84ff);
  color: var(--message-sent-text, white);
  border-bottom-right-radius: 4px;
}

.received .message-bubble {
  background-color: var(--message-received-bg, #ffffff);
  border-bottom-left-radius: 4px;
}

.system-message-content {
  background-color: var(--system-message-bg, rgba(0, 123, 255, 0.05));
  padding: 10px 15px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  border: 1px solid var(--system-message-border, rgba(0, 123, 255, 0.1));
}

.system-icon {
  margin-right: 8px;
  color: var(--primary-color, #0a84ff);
}

.details-btn {
  margin-left: 10px;
  background-color: var(--button-secondary-bg, rgba(0, 0, 0, 0.05));
  border: none;
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 0.8rem;
  cursor: pointer;
  color: var(--primary-color, #0a84ff);
  transition: background-color 0.2s;
}

.details-btn:hover {
  background-color: var(--button-secondary-hover-bg, rgba(0, 0, 0, 0.1));
}

.attachment-preview {
  margin-bottom: 10px;
  border-radius: 8px;
  overflow: hidden;
}

.image-attachment {
  cursor: pointer;
}

.image-attachment img {
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
  display: block;
}

.file-attachment {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  cursor: pointer;
  gap: 8px;
}

.sent .file-attachment {
  background-color: rgba(255, 255, 255, 0.1);
}

.message-content {
  word-break: break-word;
  line-height: 1.4;
}

.message-meta {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 0.75rem;
}

.sent .message-meta {
  color: var(--message-sent-meta, rgba(255, 255, 255, 0.8));
}

.received .message-meta {
  color: var(--text-muted, #8e8e8e);
}

.message-status {
  display: flex;
  align-items: center;
}

.sending-status {
  color: var(--message-sending, rgba(255, 255, 255, 0.5));
}

.error-status {
  color: var(--message-error, #ff4d4f);
}

.typing-indicator {
  padding: 10px 0;
  clear: both;
  display: flex;
  margin-bottom: 10px;
}

.typing-bubble {
  display: flex;
  align-items: center;
  background-color: var(--message-received-bg, #ffffff);
  padding: 8px 15px;
  border-radius: 18px;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.typing-dots {
  display: flex;
  align-items: center;
  margin-right: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-muted, #8e8e8e);
  margin: 0 2px;
  animation: bounce 1.5s infinite ease-in-out;
}

.dot:nth-child(1) {
  animation-delay: 0s;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {

  0%,
  60%,
  100% {
    transform: translateY(0);
  }

  30% {
    transform: translateY(-6px);
  }
}

.typing-name {
  font-size: 0.9rem;
  color: var(--text-muted, #8e8e8e);
}

/* Message composer */
.message-composer {
  padding: 15px;
  background-color: var(--composer-bg, #ffffff);
  border-top: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
}

.attachment-preview-container {
  margin-bottom: 10px;
  overflow: hidden;
}

.selected-file {
  background-color: var(--attachment-preview-bg, #f0f2f5);
  border-radius: 8px;
  padding: 10px 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
}

.remove-file-btn {
  position: absolute;
  right: 10px;
  background-color: var(--attachment-remove-bg, rgba(0, 0, 0, 0.1));
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: var(--text-muted, #8e8e8e);
  cursor: pointer;
  transition: background-color 0.2s;
}

.remove-file-btn:hover {
  background-color: var(--attachment-remove-hover-bg, rgba(0, 0, 0, 0.2));
  color: var(--text-color, #333);
}

.composer-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.composer-btn {
  background: none;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: var(--composer-icon, #8e8e8e);
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.composer-btn:hover {
  background-color: var(--composer-btn-hover-bg, #f0f2f5);
  color: var(--primary-color, #0a84ff);
}

.input-wrapper {
  flex: 1;
  background-color: var(--composer-input-bg, #f0f2f5);
  border-radius: 20px;
  padding: 10px 15px;
  margin: 0 10px;
  max-height: 150px;
  overflow-y: auto;
}

textarea.message-input {
  width: 100%;
  border: none;
  background: transparent;
  resize: none;
  outline: none;
  padding: 0;
  color: var(--text-color, #333);
  font-size: 0.95rem;
  font-family: inherit;
  line-height: 1.4;
}

textarea.message-input::placeholder {
  color: var(--text-muted, #8e8e8e);
}

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background-color: var(--send-btn-bg, #e4e6e9);
  color: var(--send-btn-color, #8e8e8e);
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: not-allowed;
  transition: all 0.2s;
}

.send-btn.active {
  background-color: var(--primary-color, #0a84ff);
  color: white;
  cursor: pointer;
}

.send-btn.active:hover {
  background-color: var(--primary-dark, #0070e0);
  transform: scale(1.05);
}

.send-btn.active:active {
  transform: scale(0.95);
}

/* Empty state */
.empty-chat-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: var(--text-muted, #8e8e8e);
  text-align: center;
  padding: 20px;
}

.empty-chat-state .empty-icon {
  font-size: 5rem;
  margin-bottom: 20px;
  color: var(--primary-light, rgba(10, 132, 255, 0.2));
}

.empty-chat-state h3 {
  margin: 0 0 10px;
  font-size: 1.5rem;
  color: var(--text-color, #333);
}

.select-user-btn {
  margin-top: 20px;
  padding: 10px 20px;
  background-color: var(--primary-color, #0a84ff);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
}

.select-user-btn:hover {
  background-color: var(--primary-dark, #0070e0);
}

/* Info Panel */
.info-panel {
  width: 300px;
  height: 100%;
  background-color: var(--panel-bg, #ffffff);
  border-left: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
}

.info-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color, rgba(0, 0, 0, 0.1));
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--text-color, #333);
}

.close-info-btn {
  background: none;
  border: none;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: var(--text-muted, #8e8e8e);
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.close-info-btn:hover {
  background-color: var(--button-hover-bg, #f0f2f5);
  color: var(--text-color, #333);
}

.info-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.user-fullname {
  text-align: center;
  margin: 0 0 20px;
  font-size: 1.4rem;
  color: var(--text-color, #333);
}

.user-details {
  margin-bottom: 30px;
}

.detail-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.detail-icon {
  width: 20px;
  margin-right: 10px;
  color: var(--text-muted, #8e8e8e);
}

.detail-label {
  width: 100px;
  font-size: 0.9rem;
  color: var(--text-muted, #8e8e8e);
}

.detail-value {
  flex: 1;
  font-size: 0.95rem;
  color: var(--text-color, #333);
  font-weight: 500;
}

.online-icon {
  color: var(--online-color, #4caf50);
}

.offline-icon {
  color: var(--offline-color, #8e8e8e);
}

.online-text {
  color: var(--online-color, #4caf50);
}

.offline-text {
  color: var(--offline-color, #8e8e8e);
}

.info-actions {
  margin-top: 30px;
}

.info-action-btn {
  width: 100%;
  padding: 10px 15px;
  border-radius: 8px;
  border: none;
  background-color: var(--button-secondary-bg, #f0f2f5);
  color: var(--text-color, #333);
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background-color 0.2s;
}

.info-action-btn:hover {
  background-color: var(--button-secondary-hover-bg, #e4e6e9);
}

.info-action-btn.danger {
  color: var(--danger-color, #ff4d4f);
}

.info-action-btn.danger:hover {
  background-color: var(--danger-light, rgba(255, 77, 79, 0.1));
}

/* Attachment viewer */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.modal-content {
  max-width: 90%;
  max-height: 90%;
  position: relative;
  border-radius: 10px;
  overflow: hidden;
}

.attachment-viewer img {
  max-width: 100%;
  max-height: 90vh;
  display: block;
}

.close-modal-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.5);
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  cursor: pointer;
  transition: background-color 0.2s;
}

.close-modal-btn:hover {
  background-color: rgba(0, 0, 0, 0.7);
}

/* Mobile Toggle Button */
.mobile-toggle-sidebar {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: var(--primary-color, #0a84ff);
  color: white;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.2rem;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s, background-color 0.2s;
  z-index: 10;
}

.mobile-toggle-sidebar:hover {
  background-color: var(--primary-dark, #0070e0);
  transform: scale(1.05);
}

.mobile-toggle-sidebar:active {
  transform: scale(0.95);
}

/* Mobile Styles */
@media (max-width: 768px) {
  .messaging-container.mobile-view {
    flex-direction: column;
    height: 90%;
  }

  .user-panel {
    width: 100%;
    min-width: auto;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 20;
    transform: translateX(0);
    transition: transform 0.3s ease;
  }

  .user-panel.collapsed {
    transform: translateX(-100%);
  }

  .chat-area {
    width: 100%;
    height: 100%;
  }

  .info-panel {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    z-index: 30;
    transform: translateX(0);
    transition: transform 0.3s ease;
  }

  .mobile-info-panel {
    width: 85%;
    max-width: 320px;
  }

  /* Chat composer mobile adjustments */
  .message-composer {
    padding: 10px;
  }

  .input-wrapper {
    margin: 0 5px;
  }

  .composer-actions {
    margin-bottom: 5px;
  }
}

/* Dark Mode Adjustments */
@media (prefers-color-scheme: dark) {

  .user-panel,
  .chat-header,
  .message-composer,
  .info-panel,
  .panel-header,
  .modal-content {
    background-color: var(--dark-bg, #1c1c1e);
    border-color: var(--dark-border, rgba(255, 255, 255, 0.1));
  }

  .messages-container {
    background-color: var(--dark-messages-bg, #121214);
  }

  .message-bubble,
  .typing-bubble,
  .selected-file {
    background-color: var(--dark-card-bg, #2c2c2e);
  }

  .sent .message-bubble {
    background-color: var(--dark-primary, #0a84ff);
  }

  .input-wrapper,
  .search-wrapper,
  .filter-button {
    background-color: var(--dark-input-bg, #2c2c2e);
    border-color: var(--dark-border, rgba(255, 255, 255, 0.1));
  }

  .filter-dropdown {
    background-color: var(--dark-dropdown-bg, #323234);
    border-color: var(--dark-border, rgba(255, 255, 255, 0.1));
  }

  .user-card:hover {
    background-color: var(--dark-hover-bg, #2c2c2e);
  }

  .user-card.active {
    background-color: var(--dark-active-bg, rgba(10, 132, 255, 0.2));
  }

  .status-indicator {
    border-color: var(--dark-bg, #1c1c1e);
  }

  .search-input,
  .message-input {
    color: var(--dark-text, #f5f5f7);
  }

  .search-input::placeholder,
  .message-input::placeholder {
    color: var(--dark-text-muted, #8e8e8e);
  }

  .panel-header h2,
  .chat-user-info h3,
  .user-name,
  .message-content,
  .user-fullname,
  .detail-value {
    color: var(--dark-text, #f5f5f7);
  }

  .empty-icon,
  .last-message,
  .message-time,
  .text-muted,
  .detail-label,
  .detail-icon {
    color: var(--dark-text-muted, #8e8e8e);
  }

  .line {
    background-color: var(--dark-border, rgba(255, 255, 255, 0.1));
  }
}

/* Animation classes */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s;
}

.slide-enter,
.slide-leave-to {
  transform: translateX(-100%);
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.3s;
}

.slide-right-enter,
.slide-right-leave-to {
  transform: translateX(100%);
}
</style>