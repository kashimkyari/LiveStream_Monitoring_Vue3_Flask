<template>
  <div class="messaging-container" :class="{ 'mobile-view': isMobile }">
    <!-- User panel (sidebar) -->
    <div 
      :class="[
        'user-panel', 
        { 'collapsed': isMobile && !showSidebar }
      ]" 
      ref="userPanel"
    >
      <div class="panel-header">
        <h2>Messages</h2>
        <div class="header-actions">
          <button class="filter-button" @click="toggleFilterDropdown" ref="filterButton">
            <font-awesome-icon icon="filter" />
            <span>{{ activeFilter === 'all' ? 'All' : activeFilter === 'online' ? 'Online' : 'Unread' }}</span>
            <font-awesome-icon icon="chevron-down" class="dropdown-icon" :class="{ 'rotated': showFilterDropdown }" />
          </button>
          <div v-if="showFilterDropdown" class="filter-dropdown" ref="filterDropdown">
            <button 
              :class="['filter-option', { active: activeFilter === 'all' }]" 
              @click="setFilter('all')"
            >
              <font-awesome-icon icon="users" />
              <span>All Users</span>
            </button>
            <button 
              :class="['filter-option', { active: activeFilter === 'online' }]" 
              @click="setFilter('online')"
            >
              <font-awesome-icon icon="circle" class="online-icon" />
              <span>Online Users</span>
            </button>
            <button 
              :class="['filter-option', { active: activeFilter === 'unread' }]" 
              @click="setFilter('unread')"
            >
              <font-awesome-icon icon="envelope" />
              <span>Unread Messages</span>
            </button>
          </div>
        </div>
        <div class="search-wrapper">
          <font-awesome-icon icon="search" class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search users..." 
            class="search-input"
            ref="searchInput"
          />
          <button v-if="searchQuery" class="clear-search" @click="searchQuery = ''">
            <font-awesome-icon icon="times-circle" />
          </button>
        </div>
      </div>
      
      <div class="users-list" ref="usersList">
        <div 
          v-for="user in filteredUsers" 
          :key="user.id"
          :class="['user-card', { 
            'active': selectedUser?.id === user.id,
            'unread': unreadCounts[user.id] > 0
          }]"
          @click="handleUserSelect(user)"
          ref="userCard"
        >
          <div class="user-avatar" :style="getAvatarGradient(user.username)">
            <span>{{ user.username[0].toUpperCase() }}</span>
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
        
        <div v-if="filteredUsers.length === 0" class="empty-users-list">
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
            <span>{{ selectedUser.username[0].toUpperCase() }}</span>
            <div :class="['status-indicator', getUserStatus(selectedUser)]"></div>
          </div>
          
          <div class="chat-user-info">
            <h3>{{ selectedUser.username }}</h3>
            <p :class="['user-status-text', getUserStatus(selectedUser)]">
              {{ getUserStatus(selectedUser) === 'online' ? 'Online' : 'Offline' }}
            </p>
          </div>
          
          <div class="chat-actions">
            <button class="action-button" @click="toggleInfoPanel">
              <font-awesome-icon icon="info-circle" />
            </button>
          </div>
        </div>
        
        <div 
          class="messages-container" 
          ref="messagesContainer"
          @scroll="handleScroll"
        >
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
              
              <div 
                v-for="(message, index) in group"
                :key="message.id"
                class="message-group"
              >
                <div class="message-time-header" v-if="shouldShowTimeHeader(message, group[index-1])">
                  {{ formatTimeHeader(message.timestamp) }}
                </div>
                
                <div 
                  :class="['message', isUserMessage(message) ? 'sent' : 'received', 
                            message.is_system ? 'system' : '']"
                  ref="messageItem"
                >
                  <template v-if="message.is_system">
                    <!-- System message template -->
                    <div class="system-message-content">
                      <font-awesome-icon icon="bell" class="system-icon" />
                      <p>{{ message.message }}</p>
                      <button 
                        v-if="message.details" 
                        class="details-btn"
                        @click="showNotificationDetails(message.details)"
                      >
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
          <input
            type="file"
            ref="fileInput"
            style="display: none"
            @change="handleFileSelected"
          />
          
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
            <textarea 
              v-model="inputMessage" 
              placeholder="Type a message..." 
              @keydown.enter.prevent="sendMessage"
              @input="autoGrow"
              @keydown="handleTyping"
              ref="messageInput"
              rows="1"
            ></textarea>
          </div>
          
          <button 
            class="send-btn" 
            :class="{'active': inputMessage.trim().length > 0 || selectedFile}"
            @click="sendMessage"
          >
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
    <div 
      v-if="selectedUser && showInfoPanel" 
      class="info-panel" 
      :class="{ 'mobile-info-panel': isMobile }"
      ref="infoPanel"
    >
      <div class="info-header">
        <h3>User Info</h3>
        <button class="close-info-btn" @click="toggleInfoPanel">
          <font-awesome-icon icon="times" />
        </button>
      </div>
      
      <div class="info-content">
        <div class="user-avatar large" :style="getAvatarGradient(selectedUser.username)">
          <span>{{ selectedUser.username[0].toUpperCase() }}</span>
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
            <font-awesome-icon 
              :icon="selectedUser.online ? 'circle' : 'circle'" 
              :class="selectedUser.online ? 'online-icon' : 'offline-icon'"
              class="detail-icon" 
            />
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
    <div 
      v-if="viewingAttachment" 
      class="modal-overlay"
      @click.self="closeAttachmentModal"
    >
      <div class="modal-content attachment-viewer">
        <button class="close-modal-btn" @click="closeAttachmentModal">
          <font-awesome-icon icon="times" />
        </button>
        <img v-if="viewingAttachment" :src="viewingAttachment.url" />
      </div>
    </div>
    
    <!-- Mobile toggle sidebar button (visible when sidebar is collapsed) -->
    <button 
      v-if="isMobile && !showSidebar && !selectedUser" 
      class="mobile-toggle-sidebar"
      @click="showSidebar = true"
    >
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

// Configure axios to use the backend URL
axios.defaults.baseURL = 'https://54.86.99.85:5000';
import { library } from '@fortawesome/fontawesome-svg-core';
import { 
  faSearch, faArrowLeft, faPhone, faVideo, faInfoCircle, 
  faPaperclip, faPaperPlane, faComments, faTimes, faUserSlash,
  faTrashAlt, faBell, faDesktop, faUser, faClock, faVolumeUp, faShare,
  faFile, faExclamationCircle, faCircleNotch, faImage, faFilter,
  faUsers, faCircle, faEnvelope, faChevronDown, faCommentDots, faBars,
  faTimesCircle
} from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

library.add(
  faSearch, faArrowLeft, faPhone, faVideo, faInfoCircle,
  faPaperclip, faPaperPlane, faComments, faTimes, faUserSlash,
  faTrashAlt, faBell, faDesktop, faUser, faClock, faVolumeUp, faShare,
  faFile, faExclamationCircle, faCircleNotch, faImage, faFilter,
  faUsers, faCircle, faEnvelope, faChevronDown, faCommentDots, faBars,
  faTimesCircle
);

export default {
  name: 'AdminMessageComponent',
  components: {
    FontAwesomeIcon
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
      
      return result;
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
    const initSocket = () => {
      // Connect to the backend at https://54.86.99.85:5000
      socket.value = io('https://54.86.99.85:5000/messages', { 
        path: '/ws',
        transports: ['websocket']
      });
      
      socket.value.on('connect', () => {
        console.log('Connected to WebSocket server at https://54.86.99.85:5000');
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
            sender_id: props.user.id
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
      const { user_id, online } = data;
      
      // Find user and update status
      const userIndex = users.value.findIndex(u => u.id === user_id);
      if (userIndex !== -1) {
        users.value[userIndex].online = online;
        
        // Animate status change
        const userCard = Array.from(userCard.value || []).find(card => 
          card.getAttribute('data-user-id') === user_id.toString()
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
      if (selectedUser.value && selectedUser.value.id === user_id) {
        selectedUser.value.online = online;
      }
    };
    
    const handleTypingIndicator = (data) => {
      const { user_id, typing } = data;
      
      // Only care about selected user's typing status
      if (selectedUser.value && user_id === selectedUser.value.id) {
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
      typingUsers[user_id] = typing;
      
      // If not selected, animate the user card
      if (typing && (!selectedUser.value || selectedUser.value.id !== user_id)) {
        const userCard = Array.from(userCard.value || []).find(card => 
          card.getAttribute('data-user-id') === user_id.toString()
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
      return message.sender_id === props.user.id;
    };
    
    const getLastMessage = (userId) => {
      // Find last message for user
      const userMessages = messages.value.filter(m => 
        m.sender_id === userId || m.recipient_id === userId
      );
      
      if (userMessages.length === 0) return 'No messages yet';
      
      const lastMessage = userMessages[userMessages.length - 1];
      
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
      // Find last message time for user
      const userMessages = messages.value.filter(m => 
        m.sender_id === userId || m.recipient_id === userId
      );
      
      if (userMessages.length === 0) return '';
      
      const lastMessage = userMessages[userMessages.length - 1];
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
      // Implementation for showing notification details
    };
    
    // Animation methods
    const animateUserCardSelection = (user) => {
      const activeCard = document.querySelector('.user-card.active');
      if (activeCard) {
        anime({
          targets: activeCard,
          scale: [1, 0.98, 1],
          duration: 300,
          easing: 'easeOutQuad'
        });
      }
      
      const selectedCard = Array.from(userCard.value || []).find(card => 
        card.getAttribute('data-user-id') === user.id.toString()
      );
      
      if (selectedCard) {
        anime({
          targets: selectedCard,
          scale: [1, 1.05, 1],
          backgroundColor: [
            'rgba(59, 130, 246, 0)',
            'rgba(59, 130, 246, 0.1)',
            'rgba(59, 130, 246, 0.05)'
          ],
          duration: 400,
          easing: 'easeOutQuad'
        });
      }
    };
    
    const animateMessagesEntrance = () => {
      if (!messageItem.value || messageItem.value.length === 0) return;
      
      anime({
        targets: messageItem.value,
        opacity: [0, 1],
        translateY: [10, 0],
        delay: anime.stagger(50, { from: 'last' }),
        duration: 400,
        easing: 'easeOutQuad'
      });
    };
    
    const animateOlderMessagesEntrance = () => {
      const messages = document.querySelectorAll('.message');
      if (!messages || messages.length === 0) return;
      
      // Only animate the new messages (assuming they're at the top)
      const messagesToAnimate = Array.from(messages).slice(0, messagesPerPage.value);
      
      anime({
        targets: messagesToAnimate,
        opacity: [0, 1],
        translateY: [-10, 0],
        delay: anime.stagger(10),
        duration: 300,
        easing: 'easeOutQuad'
      });
    };
    
    const checkMobile = () => {
      isMobile.value = window.innerWidth < 768;
      if (isMobile.value) {
        showSidebar.value = !selectedUser.value;
      } else {
        showSidebar.value = true;
      }
    };
    
    // Initialize
    onMounted(() => {
      // Initialize WebSocket connection
      initSocket();
      
      // Fetch online users
      fetchUsers();
      
      // Check if mobile
      checkMobile();
      window.addEventListener('resize', checkMobile);
      
      // Add data-user-id attributes to user cards
      nextTick(() => {
        if (userCard.value && userCard.value.length) {
          userCard.value.forEach((card, index) => {
            if (users.value[index]) {
              card.setAttribute('data-user-id', users.value[index].id);
            }
          });
        }
      });
      
      // Initial animations
      anime({
        targets: userPanel.value,
        translateX: [-50, 0],
        opacity: [0, 1],
        duration: 500,
        easing: 'easeOutQuad'
      });
      
      anime({
        targets: chatArea.value,
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 500,
        easing: 'easeOutQuad'
      });
    });
    
    onBeforeUnmount(() => {
      // Clean up WebSocket connection
      if (socket.value) {
        socket.value.disconnect();
      }
      
      // Clean up event listeners
      window.removeEventListener('resize', checkMobile);
      
      // Clear timeouts
      if (typingTimeout.value) {
        clearTimeout(typingTimeout.value);
      }
      if (isScrolling.value) {
        clearTimeout(isScrolling.value);
      }
    });
    
    // Watch for selected user changes
    watch(selectedUser, (newUser, oldUser) => {
      // Update UI based on selected user change
      if (newUser && (!oldUser || newUser.id !== oldUser.id)) {
        // Close info panel when changing users
        showInfoPanel.value = false;
      }
      
      // On mobile, hide sidebar when a user is selected
      if (isMobile.value && newUser) {
        showSidebar.value = false;
      }
    });
    
    // Watch for filter dropdown changes
    watch(showFilterDropdown, (isOpen) => {
      // Close dropdown when clicking outside
      if (isOpen) {
        const handleClickOutside = (event) => {
          if (filterButton.value && !filterButton.value.contains(event.target) && 
              filterDropdown.value && !filterDropdown.value.contains(event.target)) {
            showFilterDropdown.value = false;
            document.removeEventListener('click', handleClickOutside);
          }
        };
        
        // Add event listener with a delay to prevent immediate closure
        setTimeout(() => {
          document.addEventListener('click', handleClickOutside);
        }, 10);
      }
    });
    
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
      notificationDetails,
      unreadCounts,
      typingUsers,
      isConnected,
      isTyping,
      typingName,
      selectedFile,
      viewingAttachment,
      
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
      isUserMessage,
      getLastMessage,
      getLastMessageTime,
      getUserStatus,
      getAvatarGradient,
      formatDateHeader,
      formatTimeHeader,
      formatTime,
      shouldShowTimeHeader,
      getLastActive,
      handleTyping,
      autoGrow,
      toggleInfoPanel,
      clearConversation,
      openFileSelector,
      handleFileSelected,
      removeSelectedFile,
      isImageAttachment,
      isImageFile,
      viewAttachment,
      closeAttachmentModal,
      downloadAttachment,
      toggleFilterDropdown,
      setFilter,
      handleScroll,
      showNotificationDetails
    };
  }
};
</script>

<style scoped>
/* Base Container */
.messaging-container {
  display: flex;
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
  background-color: var(--bg-color);
  color: var(--text-color);
}

/* User Panel (Sidebar) */
.user-panel {
  width: 320px;
  height: 100%;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  background-color: var(--panel-bg);
  transition: transform 0.3s ease, width 0.3s ease;
  overflow: hidden;
  z-index: 10;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 12px;
  background-color: var(--header-bg);
}

.panel-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
}

.filter-button {
  background-color: var(--input-bg);
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.9rem;
  color: var(--text-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.filter-button:hover {
  background-color: var(--hover-bg);
}

.dropdown-icon {
  font-size: 0.7rem;
  transition: transform 0.2s ease;
}

.dropdown-icon.rotated {
  transform: rotate(180deg);
}

.filter-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 180px;
  background-color: var(--dropdown-bg);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  z-index: 20;
  margin-top: 5px;
  transform-origin: top left;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  width: 100%;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-color);
}

.filter-option:hover {
  background-color: var(--hover-bg);
}

.filter-option.active {
  background-color: var(--selected-item-bg);
  color: var(--primary-color);
  font-weight: 500;
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.clear-search {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.9rem;
  transition: color 0.2s ease;
}

.clear-search:hover {
  color: var(--text-color);
}

.users-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.user-card:hover {
  background-color: var(--hover-bg);
}

.user-card.active {
  background-color: var(--selected-item-bg);
}

.user-card.unread {
  background-color: var(--unread-bg);
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  font-size: 1.25rem;
  position: relative;
  flex-shrink: 0;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.status-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--panel-bg);
}

.status-indicator.online {
  background-color: var(--online-color);
}

.status-indicator.offline {
  background-color: var(--offline-color);
}

.user-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-name-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.last-message-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.last-message {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 190px;
}

.typing-indicator-text {
  color: var(--primary-color);
  font-style: italic;
}

.unread-badge {
  background-color: var(--primary-color);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
}

.empty-users-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
  color: var(--text-muted);
  text-align: center;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  opacity: 0.2;
}

/* Chat Area */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--chat-bg);
  position: relative;
}

.chat-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: var(--header-bg);
  height: 70px;
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--input-bg);
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-button:hover {
  background-color: var(--hover-bg);
}

.chat-user-info {
  flex: 1;
  min-width: 0;
}

.chat-user-info h3 {
  margin: 0 0 4px 0;
  font-size: 1.1rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-status-text {
  margin: 0;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 4px;
}

.user-status-text.online {
  color: var(--online-color);
}

.user-status-text.offline {
  color: var(--text-muted);
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--input-bg);
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-button:hover {
  background-color: var(--hover-bg);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.loading-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
  color: var(--text-muted);
  text-align: center;
}

.empty-messages .empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  opacity: 0.2;
}

.start-hint {
  font-size: 0.9rem;
  opacity: 0.7;
  margin-top: 8px;
}

.date-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.date-separator {
  display: flex;
  align-items: center;
  margin: 16px 0;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.date-separator .line {
  flex: 1;
  height: 1px;
  background-color: var(--border-color);
}

.date-separator .date {
  padding: 0 12px;
  font-weight: 500;
}

.message-time-header {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 8px 0;
}

.message-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.message {
  max-width: 80%;
  display: flex;
  flex-direction: column;
  gap: 4px;
  animation: fadeIn 0.3s ease;
}

.message.sent {
  align-self: flex-end;
}

.message.received {
  align-self: flex-start;
}

.message-bubble {
  padding: 10px 12px;
  border-radius: 16px;
  position: relative;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message.sent .message-bubble {
  background-color: var(--sent-message-bg);
  color: var(--sent-message-text);
  border-bottom-right-radius: 4px;
}

.message.received .message-bubble {
  background-color: var(--received-message-bg);
  color: var(--received-message-text);
  border-bottom-left-radius: 4px;
}

.message-content {
  font-size: 0.95rem;
  line-height: 1.4;
  word-break: break-word;
}

.message-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.message.sent .message-meta {
  color: rgba(255, 255, 255, 0.7);
}

.message-status {
  display: flex;
  align-items: center;
}

.sending-status {
  font-size: 0.8rem;
}

.error-status {
  color: var(--error-color);
}

.attachment-preview {
  margin-bottom: 8px;
  border-radius: 8px;
  overflow: hidden;
}

.image-attachment {
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.image-attachment:hover {
  opacity: 0.9;
}

.image-attachment img {
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
  object-fit: cover;
}

.file-attachment {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background-color: var(--file-bg);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.file-attachment:hover {
  background-color: var(--file-hover-bg);
}

.file-attachment span {
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.system-message-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background-color: var(--system-message-bg);
  border-radius: 8px;
  font-size: 0.9rem;
  color: var(--system-message-text);
}

.system-icon {
  color: var(--primary-color);
}

.details-btn {
  padding: 4px 8px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.details-btn:hover {
  background-color: var(--primary-dark);
}

.typing-indicator {
  align-self: flex-start;
  margin-top: 4px;
  opacity: 0;
}

.typing-bubble {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background-color: var(--received-message-bg);
  border-radius: 16px;
  max-width: 150px;
}

.typing-dots {
  display: flex;
  align-items: center;
  gap: 3px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--text-muted);
  animation: bounce 1.4s infinite ease-in-out;
  transform-origin: center bottom;
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
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.6;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.typing-name {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.message-composer {
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  background-color: var(--composer-bg);
}

.attachment-preview-container {
  width: 100%;
  overflow: hidden;
}

.selected-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: var(--file-bg);
  border-radius: 8px;
  margin-bottom: 8px;
}

.selected-file span {
  flex: 1;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.remove-file-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.remove-file-btn:hover {
  background-color: var(--hover-bg);
  color: var(--error-color);
}

.composer-actions {
  display: flex;
  align-items: center;
}

.composer-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--input-bg);
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.composer-btn:hover {
  background-color: var(--hover-bg);
}

.input-wrapper {
  flex: 1;
  border-radius: 18px;
  background-color: var(--input-bg);
  padding: 8px 12px;
  transition: all 0.2s ease;
}

.input-wrapper:focus-within {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

textarea {
  width: 100%;
  background: none;
  border: none;
  resize: none;
  padding: 0;
  font-family: inherit;
  font-size: 0.95rem;
  color: var(--text-color);
  max-height: 150px;
  outline: none;
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  opacity: 0.7;
}

.send-btn.active {
  opacity: 1;
  transform: scale(1.05);
}

.send-btn:hover {
  transform: scale(1.1);
}

.empty-chat-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--text-muted);
  padding: 20px;
}

.empty-chat-state .empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
  opacity: 0.2;
}

.empty-chat-state h3 {
  margin: 0 0 8px 0;
  font-size: 1.5rem;
  color: var(--text-color);
}

.empty-chat-state p {
  font-size: 1rem;
  margin: 0 0 20px 0;
}

.select-user-btn {
  padding: 10px 20px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.select-user-btn:hover {
  background-color: var(--primary-dark);
  transform: translateY(-1px);
}

/* Info Panel */
.info-panel {
  width: 280px;
  height: 100%;
  border-left: 1px solid var(--border-color);
  background-color: var(--panel-bg);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  overflow: hidden;
}

.info-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--header-bg);
}

.info-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 500;
}

.close-info-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-info-btn:hover {
  background-color: var(--hover-bg);
  color: var(--text-color);
}

.info-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-y: auto;
}

.user-avatar.large {
  width: 80px;
  height: 80px;
  font-size: 2rem;
  margin-bottom: 16px;
}

.user-fullname {
  margin: 0 0 20px 0;
  font-size: 1.2rem;
  font-weight: 600;
  text-align: center;
}

.user-details {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.9rem;
}

.detail-icon {
  width: 16px;
  color: var(--text-muted);
}

.detail-label {
  font-weight: 500;
  min-width: 80px;
}

.detail-value {
  color: var(--text-muted);
}

.online-icon {
  color: var(--online-color);
}

.offline-icon {
  color: var(--offline-color);
}

.online-text {
  color: var(--online-color);
}

.offline-text {
  color: var(--text-muted);
}

.info-actions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}

.info-action-btn {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: none;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.info-action-btn.danger {
  background-color: var(--danger-bg);
  color: var(--danger-color);
}

.info-action-btn.danger:hover {
  background-color: var(--danger-hover-bg);
}

/* Modal for attachments */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}

.modal-content {
  max-width: 90%;
  max-height: 90vh;
  background-color: var(--bg-color);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.attachment-viewer img {
  max-width: 100%;
  max-height: 80vh;
  display: block;
}

.close-modal-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 10;
}

.close-modal-btn:hover {
  background-color: rgba(0, 0, 0, 0.7);
}

/* Mobile view styles */
.mobile-view .user-panel {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 20;
  width: 100%;
  transform: translateX(0);
}

.mobile-view .user-panel.collapsed {
  transform: translateX(-100%);
}

.mobile-toggle-sidebar {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  z-index: 30;
  transition: all 0.2s ease;
}

.mobile-toggle-sidebar:hover {
  transform: scale(1.05);
  background-color: var(--primary-dark);
}

.mobile-view .mobile-info-panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  width: 100%;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Light theme variables */
:root {
  --primary-color: #3B82F6;
  --primary-dark: #2563EB;
  --online-color: #10B981;
  --offline-color: #9CA3AF;
  --error-color: #EF4444;
  --danger-color: #EF4444;
  
  --bg-color: #FFFFFF;
  --panel-bg: #FFFFFF;
  --chat-bg: #F9FAFB;
  --header-bg: #FFFFFF;
  --composer-bg: #FFFFFF;
  
  --text-color: #111827;
  --text-muted: #6B7280;
  
  --sent-message-bg: #3B82F6;
  --sent-message-text: #FFFFFF;
  --received-message-bg: #F3F4F6;
  --received-message-text: #1F2937;
  --system-message-bg: #FEF3C7;
  --system-message-text: #92400E;
  
  --border-color: #E5E7EB;
  --input-bg: #F3F4F6;
  --hover-bg: #F3F4F6;
  --selected-item-bg: rgba(59, 130, 246, 0.1);
  --unread-bg: rgba(59, 130, 246, 0.05);
  --file-bg: #F3F4F6;
  --file-hover-bg: #E5E7EB;
  --dropdown-bg: #FFFFFF;
  
  --danger-bg: rgba(239, 68, 68, 0.1);
  --danger-hover-bg: rgba(239, 68, 68, 0.2);
}

/* Dark theme variables */
@media (prefers-color-scheme: dark) {
  :root {
    --primary-color: #60A5FA;
    --primary-dark: #3B82F6;
    --online-color: #34D399;
    --offline-color: #9CA3AF;
    --error-color: #F87171;
    --danger-color: #F87171;
    
    --bg-color: #111827;
    --panel-bg: #1F2937;
    --chat-bg: #111827;
    --header-bg: #1F2937;
    --composer-bg: #1F2937;
    
    --text-color: #F9FAFB;
    --text-muted: #9CA3AF;
    
    --sent-message-bg: #3B82F6;
    --sent-message-text: #FFFFFF;
    --received-message-bg: #374151;
    --received-message-text: #F9FAFB;
    --system-message-bg: #4B5563;
    --system-message-text: #F9FAFB;
    
    --border-color: #374151;
    --input-bg: #374151;
    --hover-bg: #374151;
    --selected-item-bg: rgba(96, 165, 250, 0.2);
    --unread-bg: rgba(96, 165, 250, 0.1);
    --file-bg: #374151;
    --file-hover-bg: #4B5563;
    --dropdown-bg: #1F2937;
    
    --danger-bg: rgba(248, 113, 113, 0.1);
    --danger-hover-bg: rgba(248, 113, 113, 0.2);
  }
}

/* Responsive design */
@media (max-width: 767px) {
  .user-panel {
    width: 100%;
  }
  
  .info-panel {
    width: 100%;
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .user-panel {
    width: 280px;
  }
  
  .info-panel {
    width: 250px;
  }
}

@media (min-width: 1024px) {
  .user-panel {
    width: 320px;
  }
  
  .info-panel {
    width: 280px;
  }
}
</style>