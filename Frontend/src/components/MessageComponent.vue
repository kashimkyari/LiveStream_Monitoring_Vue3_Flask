<template>
  <div class="messaging-container">
    <!-- Floating Action Button for mobile -->
    <div 
      v-if="isMobile" 
      class="floating-action-btn"
      @click="toggleSidebar"
      ref="floatingBtn"
    >
      <span>{{ toggleBtnText }}</span>
    </div>

    <!-- Side Panel with User List -->
    <div 
      :class="['user-panel', {'collapsed': isMobile && !showSidebar}]"
      ref="userPanel"
    >
      <div class="panel-header glass-panel">
        <h2>Conversations</h2>
        <div class="search-container">
          <input 
            type="text" 
            placeholder="Search users..." 
            v-model="searchQuery"
            @focus="animateSearchFocus"
            @blur="animateSearchBlur"
            ref="searchInput"
          />
          <span class="search-icon">
            <font-awesome-icon icon="search" />
          </span>
        </div>
        <div class="status-filter">
          <button 
            :class="['filter-btn', activeFilter === 'all' ? 'active' : '']"
            @click="filterUsers('all')"
          >
            All
          </button>
          <button 
            :class="['filter-btn', activeFilter === 'online' ? 'active' : '']"
            @click="filterUsers('online')"
          >
            Online
          </button>
          <button 
            :class="['filter-btn', activeFilter === 'unread' ? 'active' : '']"
            @click="filterUsers('unread')"
          >
            Unread
          </button>
        </div>
      </div>

      <div class="users-list" ref="usersList">
        <div 
          v-for="user in filteredUsers" 
          :key="user.id"
          :class="['user-card', {'active': selectedUser?.id === user.id}]"
          @click="handleUserSelect(user)"
          ref="userCard"
        >
          <div class="user-avatar" :style="getAvatarGradient(user.username)">
            <span>{{ user.username[0].toUpperCase() }}</span>
            <div :class="['status-indicator', user.online ? 'online' : 'offline']"></div>
          </div>
          <div class="user-info">
            <h3>{{ user.username }}</h3>
            <p class="last-message">{{ getLastMessage(user.id) }}</p>
            <span class="message-time">{{ getLastMessageTime(user.id) }}</span>
            <div v-if="unreadCounts[user.id]" class="unread-badge">
              {{ unreadCounts[user.id] }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="chat-area" ref="chatArea">
      <template v-if="selectedUser">
        <div class="chat-header glass-panel">
          <div 
            v-if="isMobile" 
            class="back-button" 
            @click="closeMobileChat"
          >
            <font-awesome-icon icon="arrow-left" />
          </div>
          <div class="user-avatar" :style="getAvatarGradient(selectedUser.username)">
            <span>{{ selectedUser.username[0].toUpperCase() }}</span>
            <div :class="['status-indicator', selectedUser.online ? 'online' : 'offline']"></div>
          </div>
          <div class="user-details">
            <h2>{{ selectedUser.username }}</h2>
            <p>{{ selectedUser.online ? 'Online' : 'Last seen ' + formatLastActive(selectedUser.last_active) }}</p>
          </div>
          <div class="chat-actions">
            <button class="action-btn">
              <font-awesome-icon icon="phone" />
            </button>
            <button class="action-btn">
              <font-awesome-icon icon="video" />
            </button>
            <button class="action-btn" @click="toggleInfo">
              <font-awesome-icon icon="info-circle" />
            </button>
          </div>
        </div>

        <div class="messages-container" ref="messagesContainer">
          <div class="date-separator">
            <span>{{ getCurrentDate() }}</span>
          </div>
          
          <div 
            v-for="(message, index) in groupedMessages"
            :key="index"
            class="message-group"
          >
            <div class="message-time-header" v-if="message.showTimestamp">
              {{ formatTimeHeader(message.timestamp) }}
            </div>
            
            <div 
              :class="['message', isUserMessage(message) ? 'sent' : 'received', 
                        message.is_system ? 'system' : '']"
              ref="messageItem"
            >
              <template v-if="message.is_system">
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
                  <div class="message-content">{{ message.message }}</div>
                  <div class="message-meta">
                    <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                    <span v-if="isUserMessage(message)" class="message-status">
                      {{ message.read ? '✓✓' : '✓' }}
                    </span>
                  </div>
                </div>
              </template>
            </div>
          </div>
          
          <div class="typing-indicator" v-if="isTyping">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
          </div>
        </div>

        <div class="message-composer glass-panel">
          <button class="composer-btn">
            <font-awesome-icon icon="paperclip" />
          </button>
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
            :class="{'active': inputMessage.trim().length > 0}"
            @click="sendMessage"
          >
            <font-awesome-icon icon="paper-plane" />
          </button>
        </div>
      </template>

      <div v-else class="empty-state">
        <div class="welcome-content">
          <div class="illustration">
            <font-awesome-icon icon="comments" />
          </div>
          <h2>Welcome to Secure Messaging</h2>
          <p>Select a conversation to start messaging</p>
        </div>
      </div>
    </div>

    <!-- Info Panel (User Details) -->
    <div 
      :class="['info-panel', {'show': showInfoPanel}]"
      ref="infoPanel"
    >
      <div class="info-header glass-panel">
        <button class="close-btn" @click="toggleInfo">
          <font-awesome-icon icon="times" />
        </button>
        <h3>Information</h3>
      </div>
      
      <div class="info-content" v-if="selectedUser">
        <div class="user-profile">
          <div 
            class="large-avatar" 
            :style="getAvatarGradient(selectedUser.username)"
          >
            {{ selectedUser.username[0].toUpperCase() }}
          </div>
          <h2>{{ selectedUser.username }}</h2>
          <p class="role-badge">{{ selectedUser.role }}</p>
        </div>
        
        <div class="info-section">
          <h4>About</h4>
          <p>{{ selectedUser.bio || "No bio available" }}</p>
        </div>
        
        <div class="actions-group">
          <button class="info-action" @click="forwardDetection" v-if="user.role === 'admin'">
            <font-awesome-icon icon="share" />
            <span>Forward Alert</span>
          </button>
          <button class="info-action danger">
            <font-awesome-icon icon="trash-alt" />
            <span>Delete Chat</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Notification Details Modal -->
    <div 
      v-if="notificationDetails" 
      class="modal-overlay"
      @click.self="closeNotificationModal"
      ref="modalOverlay"
    >
      <div class="modal-content glass-panel">
        <div class="modal-header">
          <h3>Alert Details</h3>
          <button class="close-modal-btn" @click="closeNotificationModal">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <div class="alert-details">
          <div class="alert-meta">
            <div class="meta-item">
              <font-awesome-icon icon="desktop" />
              <span>{{ notificationDetails.platform || 'Unknown Platform' }}</span>
            </div>
            <div class="meta-item">
              <font-awesome-icon icon="user" />
              <span>{{ notificationDetails.streamer || 'Unknown User' }}</span>
            </div>
            <div class="meta-item">
              <font-awesome-icon icon="clock" />
              <span>{{ formatDateTime(notificationDetails.timestamp) }}</span>
            </div>
          </div>
          
          <div class="alert-content">
            <template v-if="notificationDetails.event_type === 'object_detection'">
              <div class="detection-preview">
                <img 
                  v-if="notificationDetails.annotated_image"
                  :src="`data:image/jpeg;base64,${notificationDetails.annotated_image}`" 
                  alt="Detection"
                />
              </div>
              <div class="detection-items">
                <div 
                  v-for="(det, i) in notificationDetails.detections" 
                  :key="i"
                  class="detection-tag"
                >
                  <span class="tag-name">{{ det.class }}</span>
                  <span class="tag-confidence">{{ (det.confidence * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </template>
            
            <template v-else-if="notificationDetails.event_type === 'chat_detection'">
              <div class="keywords-container">
                <div 
                  v-for="(kw, i) in notificationDetails.keywords" 
                  :key="i"
                  class="keyword-chip"
                >
                  {{ kw }}
                </div>
              </div>
              <div class="chat-transcript">
                <div 
                  v-for="(msg, i) in notificationDetails.messages" 
                  :key="i"
                  class="transcript-message"
                >
                  <span class="transcript-sender">{{ msg.sender }}</span>
                  <p>{{ msg.message }}</p>
                </div>
              </div>
            </template>
            
            <template v-else-if="notificationDetails.event_type === 'audio_detection'">
              <div class="audio-detection">
                <div class="audio-keyword">
                  <font-awesome-icon icon="volume-up" />
                  <span>{{ notificationDetails.keyword }}</span>
                </div>
                <div class="audio-transcript">
                  "{{ notificationDetails.transcript }}"
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import axios from 'axios';
import { format, formatDistanceToNow, parseISO } from 'date-fns';
import anime from 'animejs';
import { io } from 'socket.io-client';
import { library } from '@fortawesome/fontawesome-svg-core';
import { 
  faSearch, faArrowLeft, faPhone, faVideo, faInfoCircle, 
  faPaperclip, faPaperPlane, faComments, faTimes, faUserSlash,
  faTrashAlt, faBell, faDesktop, faUser, faClock, faVolumeUp, faShare
} from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

library.add(
  faSearch, faArrowLeft, faPhone, faVideo, faInfoCircle,
  faPaperclip, faPaperPlane, faComments, faTimes, faUserSlash,
  faTrashAlt, faBell, faDesktop, faUser, faClock, faVolumeUp, faShare
);

export default {
  name: 'MessageComponent',
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
    // Socket.io connection
    const socket = ref(null);

    // Responsive state
    const isMobile = ref(window.innerWidth < 768);
    const showSidebar = ref(!isMobile.value);
    const toggleBtnText = computed(() => showSidebar.value ? 'Chat' : 'Users');

    // UI state
    const showInfoPanel = ref(false);
    const activeFilter = ref('all');
    const searchQuery = ref('');
    const isTyping = ref(false);
    const notificationDetails = ref(null);

    // Data state
    const messages = ref([]);
    const onlineUsers = ref([]);
    const selectedUser = ref(null);
    const inputMessage = ref('');
    const unreadCounts = reactive({});
    const typingTimeout = ref(null);
    const lastMessages = reactive({});
    
    // Refs for animations
    const userPanel = ref(null);
    const userCard = ref(null);
    const chatArea = ref(null);
    const messagesContainer = ref(null);
    const messageItem = ref(null);
    const infoPanel = ref(null);
    const searchInput = ref(null);
    const messageInput = ref(null);
    const floatingBtn = ref(null);
    const modalOverlay = ref(null);
    const usersList = ref(null);
    
    // Computed properties
    const filteredUsers = computed(() => {
      let users = [...onlineUsers.value];
      
      // Apply search filter
      if (searchQuery.value) {
        users = users.filter(user => 
          user.username.toLowerCase().includes(searchQuery.value.toLowerCase())
        );
      }
      
      // Apply status filter
      switch (activeFilter.value) {
        case 'online':
          users = users.filter(user => user.online);
          break;
        case 'unread':
          users = users.filter(user => unreadCounts[user.id] && unreadCounts[user.id] > 0);
          break;
      }
      
      // Sort by online status first, then by unread messages
      return users.sort((a, b) => {
        // Online users first
        if (a.online !== b.online) return a.online ? -1 : 1;
        
        // Users with unread messages next
        const aUnread = unreadCounts[a.id] || 0;
        const bUnread = unreadCounts[b.id] || 0;
        if (aUnread !== bUnread) return bUnread - aUnread;
        
        // Alphabetical order as fallback
        return a.username.localeCompare(b.username);
      });
    });
    
    const groupedMessages = computed(() => {
      // Group messages and add timestamps between groups
      if (!messages.value.length) return [];
      
      let result = [...messages.value];
      
      // Add a showTimestamp flag to messages that should display a time header
      let lastTime = null;
      result.forEach((message) => { // Removed unused index parameter
        const msgDate = new Date(message.timestamp);
        const msgHour = msgDate.getHours();
        
        if (!lastTime || lastTime.getHours() !== msgHour || 
            (msgDate - lastTime) > 30 * 60 * 1000) {
          message.showTimestamp = true;
        } else {
          message.showTimestamp = false;
        }
        
        lastTime = msgDate;
      });
      
      return result;
    });

    // Socket.io setup
    const setupSocket = () => {
      // Initialize socket connection
      socket.value = io();
      
      // Handle connect event
      socket.value.on('connect', () => {
        console.log('Connected to socket server');
        fetchOnlineUsers();
      });
      
      // Handle receiving messages
      socket.value.on('receive_message', (message) => {
        if (message.sender_id !== props.user.id) {
          // Mark as unread if it's not from the current user
          if (!selectedUser.value || selectedUser.value.id !== message.sender_id) {
            unreadCounts[message.sender_id] = (unreadCounts[message.sender_id] || 0) + 1;
          } else {
            // If chat is open with this user, mark as read
            markMessageAsRead(message.id);
          }
          
          // Add typing indicator briefly before showing the message
          if (selectedUser.value && selectedUser.value.id === message.sender_id) {
            isTyping.value = true;
            setTimeout(() => {
              isTyping.value = false;
              
              // Add message to messages array
              if (messages.value.findIndex(m => m.id === message.id) === -1) {
                messages.value.push(message);
                
                // Update last message for this conversation
                lastMessages[message.sender_id] = message;
                
                // Scroll to bottom and animate
                nextTick(() => {
                  scrollToBottom();
                  animateNewMessage();
                });
              }
            }, 1000);
          } else {
            // For users we're not chatting with, just update last messages
            if (messages.value.findIndex(m => m.id === message.id) === -1) {
              lastMessages[message.sender_id] = message;
            }
          }
        } else {
          // Message from current user (confirmation of sent message)
          if (messages.value.findIndex(m => m.id === message.id) === -1) {
            messages.value.push(message);
            
            // Update last message for this conversation
            if (selectedUser.value) {
              lastMessages[selectedUser.value.id] = message;
            }
            
            // Scroll to bottom and animate
            nextTick(() => {
              scrollToBottom();
              animateNewMessage();
            });
          }
        }
      });
      
      // Handle typing status updates
      socket.value.on('typing', (data) => {
        if (selectedUser.value && data.sender_username === selectedUser.value.username) {
          isTyping.value = data.typing;
        }
      });
      
      // Handle user status updates
      socket.value.on('user_status', (data) => {
        const userIndex = onlineUsers.value.findIndex(u => u.id === data.userId);
        if (userIndex !== -1) {
          onlineUsers.value[userIndex].online = data.online;
          
          // If it's the selected user, update UI
          if (selectedUser.value && selectedUser.value.id === data.userId) {
            selectedUser.value.online = data.online;
          }
        }
      });
      
      // If admin, subscribe to admin room
      if (props.user.role === 'admin') {
        socket.value.emit('admin_subscribe');
        
        socket.value.on('notification_forwarded', (data) => {
          console.log('Notification forwarded:', data);
          // Could show a toast notification here
        });
      }
    };

    // Methods for data fetching
    const fetchMessages = async (receiverId) => {
      try {
        const res = await axios.get(`/api/messages/${receiverId}`);
        if (res.data) {
          messages.value = res.data;
          
          // Mark received messages as read
          const receivedMsgIds = res.data
            .filter(msg => msg.sender_id === receiverId && !msg.read)
            .map(msg => msg.id);
          
          if (receivedMsgIds.length > 0) {
            markMessagesRead(receivedMsgIds);
          }
          
          // Update last messages for this user
          if (res.data.length > 0) {
            const latestMsg = res.data[res.data.length - 1];
            lastMessages[receiverId] = latestMsg;
          }
          
          // Reset unread count for this user
          unreadCounts[receiverId] = 0;
          
          nextTick(() => {
            scrollToBottom();
            animateMessages();
          });
        }
      } catch (error) {
        console.error('Error fetching messages:', error);
      }
    };

    const fetchOnlineUsers = async () => {
      try {
        const res = await axios.get('/api/online-users');
        onlineUsers.value = res.data;
        
        // Update unread counts
        for (const user of onlineUsers.value) {
          if (!lastMessages[user.id]) {
            // Fetch last message for each user
            try {
              const msgRes = await axios.get(`/api/messages/${user.id}?limit=1`);
              if (msgRes.data && msgRes.data.length > 0) {
                lastMessages[user.id] = msgRes.data[0];
                
                // Count unread messages
                const unreadRes = await axios.get(`/api/messages/${user.id}/unread/count`);
                if (unreadRes.data && unreadRes.data.count) {
                  unreadCounts[user.id] = unreadRes.data.count;
                }
              }
            } catch (e) {
              console.error(`Error fetching data for user ${user.id}:`, e);
            }
          }
        }
        
        nextTick(() => {
          animateUserCards();
        });
      } catch (error) {
        console.error('Error fetching users:', error);
      }
    };
    
    const markMessageAsRead = async (messageId) => {
      try {
        await axios.put('/api/messages/mark-read', {
          messageIds: [messageId]
        });
      } catch (error) {
        console.error('Error marking message as read:', error);
      }
    };
    
    const markMessagesRead = async (messageIds) => {
      try {
        await axios.put('/api/messages/mark-read', {
          messageIds: messageIds
        });
      } catch (error) {
        console.error('Error marking messages as read:', error);
      }
    };
    
    const sendMessage = async () => {
      const content = inputMessage.value.trim();
      if (!content || !selectedUser.value) return;
      
      try {
        // Send via API
        await axios.post('/api/messages', { // Removed response assignment
            receiver_id: selectedUser.value.id,
            message: content
          });
        
        // Clear input
        inputMessage.value = '';
        
        // Reset textarea height
        if (messageInput.value) {
          messageInput.value.style.height = 'auto';
        }
        
        // Send via socket to improve real-time experience
        socket.value.emit('send_message', {
          receiver_username: selectedUser.value.username,
          message: content
        });
        
        // Let socket handle the message display via receive_message event
      } catch (error) {
        console.error('Message send error:', error);
        
        // Add temporary message to show error state
        messages.value.push({
          id: 'temp-' + Date.now(),
          sender_id: props.user.id,
          receiver_id: selectedUser.value.id,
          message: content,
          timestamp: new Date().toISOString(),
          read: false,
          error: true
        });
        
        // Clear input on error too
        inputMessage.value = '';
      }
    };
    
    const handleTyping = () => {
      if (!selectedUser.value || !socket.value) return;
      
      // Clear existing timeout
      if (typingTimeout.value) {
        clearTimeout(typingTimeout.value);
      }
      
      // Emit typing event
      socket.value.emit('typing', {
        receiver_username: selectedUser.value.username,
        typing: true
      });
      
      // Set timeout to stop typing indicator after 2 seconds of inactivity
      typingTimeout.value = setTimeout(() => {
        socket.value.emit('typing', {
          receiver_username: selectedUser.value.username,
          typing: false
        });
      }, 2000);
    };
    
    const forwardDetection = () => {
      // Only available for admins
      if (props.user.role !== 'admin' || !selectedUser.value) return;
      
      // For demo, we'll just show this functionality exists
      alert(`This would forward the latest detection to ${selectedUser.value.username}`);
      
      // In a real implementation, you'd have a modal to select a notification
      // and then use socket.emit('forward_notification', {notification_id, agent_id})
    };

    // UI Helper Methods
    const handleUserSelect = (user) => {
      selectedUser.value = user;
      
      // On mobile, hide the sidebar when a user is selected
      if (isMobile.value) {
        showSidebar.value = false;
      }
      
      // Register user activity
      if (socket.value) {
        socket.value.emit('user_activity');
      }
      
      // Fetch messages for this user
      fetchMessages(user.id);
      
      // Animate chat area
      animateChatArea();
    };
    
    const toggleSidebar = () => {
      showSidebar.value = !showSidebar.value;
      
      // Animate sidebar toggle
      animateSidebarToggle();
    };
    
    const closeMobileChat = () => {
      // On mobile, switch from chat to user list
      if (isMobile.value) {
        showSidebar.value = true;
      }
    };
    
    const toggleInfo = () => {
      showInfoPanel.value = !showInfoPanel.value;
      
      // Animate info panel
      animateInfoPanel();
    };
    
    const filterUsers = (filter) => {
      activeFilter.value = filter;
      
      // Animate filter change
      anime({
        targets: document.querySelector(`.filter-btn.active`),
        scale: [0.9, 1],
        duration: 300,
        easing: 'spring(1, 80, 10, 0)'
      });
    };
    
    const autoGrow = () => {
      if (!messageInput.value) return;
      
      // Reset height to auto to accurately measure the new height
      messageInput.value.style.height = 'auto';
      
      // Set new height (capped at 100px)
      const newHeight = Math.min(messageInput.value.scrollHeight, 100);
      messageInput.value.style.height = `${newHeight}px`;
    };

    const showNotificationDetails = (details) => {
      notificationDetails.value = details;
      nextTick(() => {
        animateModal();
      });
    };
    
    const closeNotificationModal = () => {
      // Fade out animation
      anime({
        targets: modalOverlay.value,
        opacity: [1, 0],
        duration: 300,
        easing: 'easeOutQuad',
        complete: () => {
          notificationDetails.value = null;
        }
      });
    };
    
    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
      }
    };

    // Helper methods for displaying data
    const getLastMessage = (userId) => {
      if (lastMessages[userId]) {
        return lastMessages[userId].message;
      }
      return 'Start a conversation';
    };
    
    const getLastMessageTime = (userId) => {
      if (lastMessages[userId]) {
        return formatDistanceToNow(new Date(lastMessages[userId].timestamp), { addSuffix: true });
      }
      return '';
    };
    
    const formatLastActive = (timestamp) => {
      if (!timestamp) return 'unknown';
      try {
        return formatDistanceToNow(parseISO(timestamp), { addSuffix: true });
      } catch (e) {
        return 'unknown';
      }
    };
    
    const formatTime = (timestamp) => {
      return format(new Date(timestamp), 'h:mm a');
    };
    
    const formatTimeHeader = (timestamp) => {
      return format(new Date(timestamp), 'h:mm a');
    };
    
    const formatDateTime = (timestamp) => {
      if (!timestamp) return 'Unknown';
      try {
        return format(new Date(timestamp), 'MMM d, yyyy h:mm a');
      } catch (e) {
        return 'Invalid date';
      }
    };
    
    const getCurrentDate = () => {
      return format(new Date(), 'EEEE, MMMM d');
    };
    
    const isUserMessage = (message) => {
      return message.sender_id === props.user.id;
    };
    
    const getAvatarGradient = (username) => {
      // Generate a consistent gradient based on username
      const hash = username.charCodeAt(0) + username.length;
      const hue1 = hash % 360;
      const hue2 = (hue1 + 40) % 360;
      
      return {
        background: `linear-gradient(135deg, hsl(${hue1}, 70%, 60%), hsl(${hue2}, 70%, 50%))`
      };
    };

    // Animation Methods
    const animateSidebarToggle = () => {
      if (!userPanel.value) return;
      
      if (showSidebar.value) {
        // Show sidebar
        anime({
          targets: userPanel.value,
          translateX: [-300, 0],
          opacity: [0, 1],
          duration: 500,
          easing: 'easeOutExpo'
        });
      } else {
        // Hide sidebar
        anime({
          targets: userPanel.value,
          translateX: [0, -300],
          opacity: [1, 0],
          duration: 500,
          easing: 'easeOutExpo'
        });
      }
    };
    
    const animateChatArea = () => {
      if (!chatArea.value) return;
      
      anime({
        targets: chatArea.value,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 500,
        easing: 'easeOutQuad'
      });
    };
    
    const animateInfoPanel = () => {
      if (!infoPanel.value) return;
      
      if (showInfoPanel.value) {
        // Show info panel
        anime({
          targets: infoPanel.value,
          translateX: [300, 0],
          opacity: [0, 1],
          duration: 500,
          easing: 'easeOutExpo'
        });
      } else {
        // Hide info panel
        anime({
          targets: infoPanel.value,
          translateX: [0, 300],
          opacity: [1, 0],
          duration: 500,
          easing: 'easeOutExpo'
        });
      }
    };
    
    const animateUserCards = () => {
      if (!userCard.value) return;
      
      anime({
        targets: userCard.value,
        translateY: [20, 0],
        opacity: [0, 1],
        delay: anime.stagger(50),
        duration: 500,
        easing: 'easeOutQuad'
      });
    };
    
    const animateMessages = () => {
      if (!messageItem.value) return;
      
      anime({
        targets: messageItem.value,
        translateY: [20, 0],
        opacity: [0, 1],
        delay: anime.stagger(50),
        duration: 500,
        easing: 'easeOutQuad'
      });
    };
    
    const animateNewMessage = () => {
      const lastMessage = document.querySelector('.message:last-child');
      if (lastMessage) {
        anime({
          targets: lastMessage,
          translateY: [20, 0],
          opacity: [0, 1],
          duration: 500,
          easing: 'easeOutElastic(1, .6)'
        });
      }
    };
    
    const animateSearchFocus = () => {
      if (!searchInput.value) return;
      
      anime({
        targets: searchInput.value.parentNode,
        scale: [1, 1.03],
        boxShadow: ['0 2px 5px rgba(0,0,0,0.1)', '0 4px 10px rgba(0,0,0,0.2)'],
        duration: 300,
        easing: 'easeOutQuad'
      });
    };
    
    const animateSearchBlur = () => {
      if (!searchInput.value) return;
      
      anime({
        targets: searchInput.value.parentNode,
        scale: [1.03, 1],
        boxShadow: ['0 4px 10px rgba(0,0,0,0.2)', '0 2px 5px rgba(0,0,0,0.1)'],
        duration: 300,
        easing: 'easeOutQuad'
      });
    };
    
    const animateModal = () => {
      if (!modalOverlay.value) return;
      
      // Fade in overlay
      anime({
        targets: modalOverlay.value,
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuad'
      });
      
      // Scale in modal content
      anime({
        targets: modalOverlay.value.querySelector('.modal-content'),
        scale: [0.9, 1],
        opacity: [0, 1],
        duration: 400,
        easing: 'spring(1, 80, 10, 0)'
      });
    };

    // Responsive design methods
    const handleResize = () => {
      isMobile.value = window.innerWidth < 768;
      
      // If transitioning from mobile to desktop, ensure sidebar is shown
      if (!isMobile.value) {
        showSidebar.value = true;
      }
    };

    // Lifecycle hooks
    onMounted(() => {
      setupSocket();
      fetchOnlineUsers();
      
      // Set up resize listener
      window.addEventListener('resize', handleResize);
      
      // Add CSS-style class to body for any global styling needs
      document.body.classList.add('secure-messaging-app');
    });
    
    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize);
      
      // Disconnect socket on unmount
      if (socket.value) {
        socket.value.disconnect();
      }
      
      // Clean up global styling
      document.body.classList.remove('secure-messaging-app');
    });
    
    // Watch for changes
    watch(selectedUser, (newUser) => {
      if (newUser) {
        // Update document title with user name
        document.title = `Chat with ${newUser.username}`;
      } else {
        document.title = 'Secure Messaging';
      }
    });

    return {
      // State
      isMobile,
      showSidebar,
      toggleBtnText,
      showInfoPanel,
      activeFilter,
      searchQuery,
      messages,
      filteredUsers,
      groupedMessages,
      selectedUser,
      inputMessage,
      isTyping,
      unreadCounts,
      notificationDetails,
      
      // Methods
      handleUserSelect,
      toggleSidebar,
      closeMobileChat,
      toggleInfo,
      filterUsers,
      sendMessage,
      autoGrow,
      handleTyping,
      showNotificationDetails,
      closeNotificationModal,
      forwardDetection,
      
      // Helpers
      getLastMessage,
      getLastMessageTime,
      formatLastActive,
      formatTime,
      formatTimeHeader,
      formatDateTime,
      getCurrentDate,
      isUserMessage,
      getAvatarGradient,
      
      // Refs
      userPanel,
      userCard,
      chatArea,
      messagesContainer,
      messageItem,
      infoPanel,
      searchInput,
      messageInput,
      floatingBtn,
      modalOverlay,
      usersList,
      
      // Animation methods
      animateSearchFocus,
      animateSearchBlur
    };
  }
};
        </script> 

<style scoped>
.messaging-container {
  display: flex;
  height: 100vh;
  width: 100%;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow: hidden;
  position: relative;
}

/* Glass panel effect */
.glass-panel {
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background-color: rgba(var(--bg-color-rgb, 210, 175, 190), 0.07);
  border: 1px solid rgba(var(--text-color-rgb, 240, 240, 240), 0.1);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

/* User Panel */
.user-panel {
  width: 320px;
  height: 100%;
  border-right: 1px solid var(--input-border);
  display: flex;
  flex-direction: column;
  transition: transform 0.4s cubic-bezier(0.19, 1, 0.22, 1);
  background-color: var(--bg-color);
  z-index: 10;
}

.user-panel.collapsed {
  transform: translateX(-100%);
}

.panel-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--input-border);
  position: sticky;
  top: 0;
  z-index: 5;
}

.panel-header h2 {
  margin-bottom: 1rem;
  font-weight: 600;
  font-size: 1.5rem;
}

.search-container {
  position: relative;
  margin-bottom: 1rem;
}

.search-container input {
  width: 100%;
  padding: 0.8rem 1rem 0.8rem 2.5rem;
  border-radius: 8px;
  border: 1px solid var(--input-border);
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 1rem;
  transition: all 0.3s ease;
}

.search-container input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.2);
  outline: none;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-color);
  opacity: 0.7;
}

.status-filter {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.filter-btn {
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.filter-btn:hover {
  background-color: var(--hover-bg);
}

.filter-btn.active {
  background-color: var(--primary-color);
  color: #fff;
  border-color: var(--primary-color);
}

.users-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.users-list::-webkit-scrollbar {
  width: 6px;
}

.users-list::-webkit-scrollbar-track {
  background: transparent;
}

.users-list::-webkit-scrollbar-thumb {
  background-color: rgba(var(--text-color-rgb, 240, 240, 240), 0.3);
  border-radius: 20px;
}

.user-card {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.user-card:hover {
  background-color: var(--hover-bg);
  transform: translateY(-2px);
}

.user-card.active {
  background-color: rgba(var(--primary-color-rgb, 0, 123, 255), 0.1);
  border-left: 3px solid var(--primary-color);
}

.user-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 600;
  color: white;
  margin-right: 1rem;
  position: relative;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--bg-color);
  position: absolute;
  bottom: 0;
  right: 0;
}

.status-indicator.online {
  background-color: #4CAF50;
}

.status-indicator.offline {
  background-color: #9e9e9e;
}

.user-info {
  flex: 1;
  position: relative;
}

.user-info h3 {
  font-weight: 600;
  margin-bottom: 0.2rem;
  font-size: 1.1rem;
}

.last-message {
  color: var(--text-color);
  opacity: 0.8;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.message-time {
  position: absolute;
  top: 0;
  right: 0;
  font-size: 0.75rem;
  color: var(--text-color);
  opacity: 0.7;
}

.unread-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  background-color: var(--primary-color);
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
}

/* Chat Area */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.chat-header {
  padding: 1rem;
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--input-border);
  height: 80px;
}

.back-button {
  margin-right: 1rem;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: var(--hover-bg);
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-button:hover {
  background-color: var(--input-bg);
}

.user-details {
  flex: 1;
}

.user-details h2 {
  font-weight: 600;
  margin-bottom: 0.2rem;
}

.user-details p {
  font-size: 0.9rem;
  opacity: 0.8;
}

.chat-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--hover-bg);
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-color);
}

.action-btn:hover {
  background-color: var(--input-bg);
  transform: translateY(-2px);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background-color: rgba(var(--text-color-rgb, 240, 240, 240), 0.3);
  border-radius: 20px;
}

.date-separator {
  text-align: center;
  margin: 1rem 0;
  position: relative;
}

.date-separator::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  width: 30%;
  height: 1px;
  background-color: var(--input-border);
}

.date-separator::after {
  content: '';
  position: absolute;
  right: 0;
  top: 50%;
  width: 30%;
  height: 1px;
  background-color: var(--input-border);
}

.date-separator span {
  background-color: var(--bg-color);
  padding: 0 1rem;
  font-size: 0.8rem;
  color: var(--text-color);
  opacity: 0.7;
  position: relative;
  z-index: 1;
}

.message-group {
  margin-bottom: 1rem;
  position: relative;
}

.message-time-header {
  text-align: center;
  margin: 0.8rem 0;
  font-size: 0.8rem;
  color: var(--text-color);
  opacity: 0.7;
}

.message {
  margin-bottom: 0.5rem;
  display: flex;
  flex-direction: column;
  max-width: 80%;
  animation-duration: 0.3s;
  position: relative;
}

.message.sent {
  align-self: flex-end;
}

.message.received {
  align-self: flex-start;
}

.message-bubble {
  padding: 0.8rem 1rem;
  border-radius: 16px;
  position: relative;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message.sent .message-bubble {
  background-color: var(--primary-color);
  border-bottom-right-radius: 4px;
}

.message.received .message-bubble {
  background-color: var(--input-bg);
  border-bottom-left-radius: 4px;
}

.message-content {
  margin-bottom: 0.2rem;
  line-height: 1.4;
}

.message-meta {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  font-size: 0.7rem;
  opacity: 0.8;
  gap: 0.3rem;
}

.system-message-content {
  padding: 1rem;
  border-radius: 12px;
  background-color: rgba(255, 152, 0, 0.1);
  border: 1px solid rgba(255, 152, 0, 0.2);
  display: flex;
  align-items: center;
  gap: 0.8rem;
  width: 100%;
  margin: 1rem 0;
}

.system-icon {
  color: #ff9800;
  font-size: 1.2rem;
}

.system-message-content p {
  flex: 1;
  color: var(--text-color);
  font-weight: 500;
}

.details-btn {
  padding: 0.4rem 0.8rem;
  background-color: rgba(255, 152, 0, 0.2);
  border-radius: 16px;
  border: none;
  color: #ff9800;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.8rem;
  font-weight: 500;
}

.details-btn:hover {
  background-color: rgba(255, 152, 0, 0.3);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.8rem 1rem;
  border-radius: 16px;
  background-color: var(--input-bg);
  width: fit-content;
  margin-bottom: 1rem;
  animation: fadeIn 0.3s ease;
}

.typing-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-color);
  opacity: 0.8;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator .dot:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-4px);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-composer {
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
  border-top: 1px solid var(--input-border);
}

.composer-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--hover-bg);
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-color);
}

.composer-btn:hover {
  background-color: var(--input-bg);
  transform: translateY(-2px);
}

.input-wrapper {
  flex: 1;
  border-radius: 24px;
  background-color: var(--input-bg);
  padding: 0.5rem 1rem;
  transition: all 0.3s ease;
  border: 1px solid var(--input-border);
}

.input-wrapper:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

textarea {
  width: 100%;
  background: transparent;
  border: none;
  resize: none;
  color: var(--text-color);
  font-size: 1rem;
  line-height: 1.5;
  max-height: 100px;
  padding: 0.2rem 0;
}

textarea:focus {
  outline: none;
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--hover-bg);
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-color);
  opacity: 0.5;
}

.send-btn.active {
  background-color: var(--primary-color);
  color: white;
  opacity: 1;
}

.send-btn.active:hover {
  transform: scale(1.05) translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(to bottom, transparent, rgba(var(--input-bg-rgb, 37, 37, 37), 0.1));
}

.welcome-content {
  text-align: center;
  max-width: 400px;
  padding: 2rem;
}

.illustration {
  font-size: 5rem;
  margin-bottom: 2rem;
  color: var(--primary-color);
  opacity: 0.7;
}

.welcome-content h2 {
  margin-bottom: 1rem;
  font-weight: 600;
}

.welcome-content p {
  opacity: 0.8;
}

/* Info Panel */
.info-panel {
  width: 300px;
  height: 100%;
  position: absolute;
  right: 0;
  top: 0;
  background-color: var(--bg-color);
  border-left: 1px solid var(--input-border);
  transform: translateX(100%);
  transition: transform 0.4s cubic-bezier(0.19, 1, 0.22, 1);
  z-index: 15;
  display: flex;
  flex-direction: column;
}

.info-panel.show {
  transform: translateX(0);
}

.info-header {
  padding: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--input-border);
}

.info-header h3 {
  font-weight: 600;
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-color);
}

.close-btn:hover {
  background-color: var(--hover-bg);
}

.info-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.user-profile {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 2rem;
}

.large-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: 600;
  color: white;
  margin-bottom: 1rem;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.role-badge {
  background-color: var(--primary-color);
  color: white;
  padding: 0.3rem 0.8rem;
  border-radius: 16px;
  font-size: 0.8rem;
  font-weight: 500;
  margin-top: 0.5rem;
}

.info-section {
  margin-bottom: 2rem;
}

.info-section h4 {
  margin-bottom: 0.8rem;
  font-weight: 600;
  color: var(--text-color);
  opacity: 0.8;
  font-size: 1rem;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.media-item {
  aspect-ratio: 1;
  background-color: var(--input-bg);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.media-item:hover {
  transform: scale(1.05);
}

.actions-group {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.info-action {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1rem;
  border-radius: 8px;
  background-color: var(--input-bg);
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-color);
}

.info-action:hover {
  background-color: var(--hover-bg);
}

.info-action.danger {
  color: #f44336;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
  backdrop-filter: blur(5px);
}
.modal-content {
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--input-border);
}

.modal-header h3 {
  font-weight: 600;
}

.close-modal-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-color);
}

.close-modal-btn:hover {
  background-color: var(--hover-bg);
}

.alert-details {
  padding: 1.5rem;
  overflow-y: auto;
  max-height: calc(80vh - 70px);
}

.alert-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--input-border);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-color);
  opacity: 0.8;
  font-size: 0.9rem;
}

.alert-content {
  margin-top: 1rem;
}

.detection-preview {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 1rem;
  background-color: var(--input-bg);
}

.detection-preview img {
  width: 100%;
  height: auto;
  display: block;
}

.detection-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.detection-tag {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 16px;
  background-color: rgba(var(--primary-color-rgb, 0, 123, 255), 0.1);
  border: 1px solid rgba(var(--primary-color-rgb, 0, 123, 255), 0.2);
}

.tag-name {
  font-weight: 500;
}

.tag-confidence {
  font-size: 0.8rem;
  opacity: 0.8;
}

.keywords-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.keyword-chip {
  padding: 0.4rem 0.8rem;
  border-radius: 16px;
  background-color: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.2);
  color: #f44336;
  font-size: 0.9rem;
}

.chat-transcript {
  background-color: var(--input-bg);
  border-radius: 12px;
  padding: 1rem;
  max-height: 300px;
  overflow-y: auto;
}

.transcript-message {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--input-border);
}

.transcript-message:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.transcript-sender {
  font-weight: 600;
  margin-bottom: 0.3rem;
  display: block;
}

.audio-detection {
  background-color: var(--input-bg);
  border-radius: 12px;
  padding: 1.5rem;
}

.audio-keyword {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  color: var(--primary-color);
}

.audio-transcript {
  font-style: italic;
  opacity: 0.9;
  line-height: 1.6;
}

/* Floating action button for mobile */
.floating-action-btn {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
  cursor: pointer;
  z-index: 100;
  transition: all 0.3s ease;
}

.floating-action-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 123, 255, 0.4);
}

/* CSS Variables */
:root {
  /* Light Theme (default) */
  --bg-color: #f8f9fa;
  --bg-color-rgb: 248, 249, 250;
  --text-color: #212529;
  --text-color-rgb: 33, 37, 41;
  --primary-color: #0d6efd;
  --primary-color-rgb: 13, 110, 253;
  --input-bg: #e9ecef;
  --input-bg-rgb: 233, 236, 239;
  --input-border: #dee2e6;
  --hover-bg: #dee2e6;
}

/* Dark Theme */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-color: #121212;
    --bg-color-rgb: 18, 18, 18;
    --text-color: #f0f0f0;
    --text-color-rgb: 240, 240, 240;
    --primary-color: #0d6efd;
    --primary-color-rgb: 13, 110, 253;
    --input-bg: #252525;
    --input-bg-rgb: 37, 37, 37;
    --input-border: #424242;
    --hover-bg: #333333;
  }
}

/* Media Queries */
@media (max-width: 1024px) {
  .user-panel {
    width: 280px;
  }
  
  .info-panel {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .messaging-container {
    position: relative;
  }
  
  .user-panel {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    z-index: 15;
  }
  
  .chat-area {
    width: 100%;
  }
  
  .info-panel {
    width: 100%;
  }
}

/* Animations */
@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes slideInLeft {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Utility Classes */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>