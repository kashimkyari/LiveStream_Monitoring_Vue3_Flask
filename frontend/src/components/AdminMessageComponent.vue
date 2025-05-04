<template>
  <div class="messaging-container flex h-screen" :class="{ 'mobile-view': isMobile }">
    <!-- User panel (sidebar) -->
    <div 
      :class="['user-panel bg-gray-100 p-4 shadow-md', { 'w-64': !isMobile || showSidebar, 'w-0 overflow-hidden': isMobile && !showSidebar }]">
      <div class="panel-header flex justify-between items-center mb-4">
        <h2 class="text-xl font-bold">Messages</h2>
        <div class="header-actions">
          <button @click="toggleFilterDropdown" class="filter-button flex items-center">
            <font-awesome-icon icon="filter" />
            <span>{{ activeFilter === 'all' ? 'All' : activeFilter === 'online' ? 'Online' : 'Unread' }}</span>
            <font-awesome-icon icon="chevron-down" class="ml-1" />
          </button>
          <div v-if="showFilterDropdown" class="filter-dropdown absolute bg-white shadow rounded mt-2">
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
      
      <div class="users-list overflow-y-auto max-h-[calc(100vh-200px)]">
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
    <div class="chat-area flex-1 flex flex-col">
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
        
        <div class="messages-container flex-1 overflow-y-auto p-4" @scroll="handleScroll">
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
        <div class="message-composer p-4 border-t">
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
axios.defaults.baseURL = 'https://monitor-backend.jetcamstudio.com:5000';
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
      // Connect to the backend at https://monitor-backend.jetcamstudio.com:5000
      socket.value = io('https://monitor-backend.jetcamstudio.com:5000/messages', { 
        path: '/ws',
        transports: ['websocket']
      });
      
      socket.value.on('connect', () => {
        console.log('Connected to WebSocket server at https://monitor-backend.jetcamstudio.com:5000');
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
      if (user) {
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
    
    const getUserStatus = (user) => user ? (user.online ? 'online' : 'offline') : 'offline';
    
    const getAvatarGradient = (username) => {
      if (!username) return {};
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
    
    // Add responsive logic
    const checkMobile = () => isMobile.value = window.innerWidth < 768;
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
/* Use theme variables matching App.vue's theme system */
.messaging-container {
  --bg-color: var(--bg-primary);
  --text-color: var(--text-primary);
  --border-color: var(--border-color);
  --primary-color: var(--accent-color);
  --hover-bg: var(--bg-hover);
  --online-color: #4ade80;
  --offline-color: #64748b;
}

.user-panel {
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  transition: width 0.3s ease;
}

.user-card {
  padding: 1rem;
  margin: 0.5rem 0;
  border-radius: 0.5rem;
  background: var(--bg-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-card:hover {
  background: var(--hover-bg);
  transform: translateX(2px);
}

.user-card.active {
  background: var(--primary-color);
  color: white;
}

.chat-area {
  background: var(--bg-primary);
}

.message.sent .message-bubble {
  background: var(--primary-color);
  color: white;
  border-radius: 1rem 1rem 0 1rem;
}

.message.received .message-bubble {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 1rem 1rem 1rem 0;
}

.message-composer {
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.search-input {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.filter-dropdown {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-indicator.online {
  background: var(--online-color);
  box-shadow: 0 0 8px rgba(74, 222, 128, 0.3);
}

.status-indicator.offline {
  background: var(--offline-color);
}

/* Mobile adaptations matching App.vue's breakpoints */
@media (max-width: 768px) {
  .user-panel {
    position: fixed;
    z-index: 100;
    height: 100vh;
    box-shadow: 4px 0 12px rgba(0, 0, 0, 0.1);
  }

  .chat-area {
    margin-left: 0;
  }

  .mobile-toggle-sidebar {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    background: var(--primary-color);
    color: white;
    padding: 0.75rem;
    border-radius: 50%;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}

/* Animations matching App.vue's motion system */
.message-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.message-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.typing-dots div {
  background: var(--text-secondary);
  animation: typing 1.4s infinite;
}

@keyframes typing {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
</style>

