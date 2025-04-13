<template>
  <div class="messaging-container">
    <!-- Animated Sidebar -->
    <div class="user-list-container" ref="sidebar">
      <div class="sidebar-header">
        <h2 class="section-title">Online Users</h2>
        <div class="online-indicator"></div>
      </div>
      <div class="user-list">
        <div 
          v-for="(u, index) in onlineUsers" 
          :key="u.id" 
          :class="['user-card', selectedUser?.id === u.id ? 'active' : '']"
          @click="handleUserSelect(u)"
          :ref="'userCard' + index"
        >
          <div class="user-avatar">
            <span>{{ u.username[0] }}</span>
            <div :class="['online-status', u.online ? 'online' : 'offline']"></div>
          </div>
          <div class="user-info">
            <h3>{{ u.username }}</h3>
            <p>{{ u.role }}</p>
            <span v-if="unreadCounts[u.id] > 0" class="unread-count">{{ unreadCounts[u.id] }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Chat Area with Glass Morphism -->
    <div class="chat-container" ref="chatContainer">
      <template v-if="selectedUser">
        <div class="chat-header" ref="chatHeader">
          <div class="user-info">
            <div class="avatar">{{ selectedUser.username[0] }}</div>
            <div>
              <h2>{{ selectedUser.username }}</h2>
              <p class="status">
                {{ isUserOnline(selectedUser.id) ? 'Online' : 'Offline' }}
              </p>
            </div>
          </div>
        </div>
        
        <div class="messages-window" ref="messagesWindow">
          <div 
            v-for="(message, index) in messages" 
            :key="message.id" 
            :class="['message', isUserMessage(message) ? 'sent' : 'received', message.is_system ? 'system' : '']"
            :ref="'message' + index"
          >
            <template v-if="message.is_system">
              <div class="system-message">
                <div class="message-content">
                  {{ message.message }}
                  <button 
                    v-if="message.details" 
                    class="details-btn"
                    @click="notificationDetails = message.details"
                  >
                    View Alert Details
                  </button>
                </div>
                <span class="message-time">
                  {{ formatTime(message.timestamp) }}
                </span>
              </div>
            </template>
            <template v-else>
              <div class="message-header">
                <span v-if="!isUserMessage(message)" class="sender-name">
                  {{ getSenderName(message.sender_id) }}
                </span>
                <span class="message-time">
                  {{ formatTime(message.timestamp) }}
                </span>
              </div>
              <div class="message-content">
                {{ message.message }}
              </div>
              <div v-if="isUserMessage(message)" class="message-status">
                {{ message.read ? '✓✓' : '✓' }}
              </div>
            </template>
          </div>
        </div>

        <div class="message-input-container" ref="inputContainer">
          <textarea
            v-model="inputMessage"
            placeholder="Type your message..."
            @keypress.enter.prevent="sendMessage"
          ></textarea>
          <button @click="sendMessage" :disabled="!inputMessage.trim()">
            Send
          </button>
        </div>
      </template>

      <div v-else class="no-selection" ref="noSelection">
        <div class="welcome-message">
          <h1>Secure Messaging Platform</h1>
          <p>Select a user to start communicating</p>
        </div>
      </div>
    </div>

    <!-- Notification Modal -->
    <div v-if="notificationDetails" class="notification-modal">
      <div class="modal-content glass-effect">
        <button class="close-btn" @click="notificationDetails = null">×</button>
        <h3>Alert Details</h3>
        <div class="meta-info">
          <div>Platform: {{ notificationDetails.platform }}</div>
          <div>Streamer: {{ notificationDetails.streamer }}</div>
          <div>Time: {{ new Date(notificationDetails.timestamp).toLocaleString() }}</div>
        </div>
        <div class="alert-content">
          <template v-if="notificationDetails.event_type === 'object_detection'">
            <div class="image-preview" v-if="notificationDetails.annotated_image">
              <img 
                :src="`data:image/jpeg;base64,${notificationDetails.annotated_image}`" 
                alt="Annotated detection"
              />
            </div>
            <div class="detection-list">
              <div 
                v-for="(det, i) in notificationDetails.detections" 
                :key="i" 
                class="detection-item"
              >
                <span>{{ det.class }}</span>
                <span class="confidence">
                  {{ (det.confidence * 100).toFixed(1) }}%
                </span>
              </div>
            </div>
          </template>
          
          <template v-else-if="notificationDetails.event_type === 'chat_detection'">
            <div class="keywords-list">
              <span 
                v-for="(kw, i) in notificationDetails.keywords" 
                :key="i" 
                class="keyword-tag"
              >
                {{ kw }}
              </span>
            </div>
            <div class="chat-messages">
              <div 
                v-for="(msg, i) in notificationDetails.messages" 
                :key="i" 
                class="chat-message"
              >
                <span class="sender">{{ msg.sender }}:</span>
                <span class="content">{{ msg.message }}</span>
              </div>
            </div>
          </template>
          
          <template v-else-if="notificationDetails.event_type === 'audio_detection'">
            <div class="keyword">{{ notificationDetails.keyword }}</div>
            <div class="transcript">{{ notificationDetails.transcript }}</div>
          </template>
          
          <template v-else>
            <div>{{ JSON.stringify(notificationDetails) }}</div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';
import anime from 'animejs';

export default {
  name: 'MessageComponent',
  props: {
    user: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    // State
    const messages = ref([]);
    const inputMessage = ref('');
    const onlineUsers = ref([]);
    const selectedUser = ref(null);
    const unreadCounts = reactive({});
    const notificationDetails = ref(null);
    const messagesWindow = ref(null);
    const pollingInterval = ref(null);

    // Methods
    const fetchMessages = async (receiverId) => {
      try {
        const res = await axios.get(`/api/messages/${receiverId}`);
        if (res.data) {
          messages.value = res.data;
          nextTick(() => {
            if (messagesWindow.value) {
              messagesWindow.value.scrollTop = messagesWindow.value.scrollHeight;
            }
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
      } catch (error) {
        console.error('Error fetching online users:', error);
      }
    };

    const sendMessage = async () => {
      const content = inputMessage.value.trim();
      if (!content || !selectedUser.value) return;

      try {
        await axios.post('/api/messages', {
          receiver_id: selectedUser.value.id,
          message: content
        });
        inputMessage.value = '';
        fetchMessages(selectedUser.value.id);
      } catch (error) {
        console.error('Message send error:', error);
      }
    };

    const markMessagesAsRead = async (messageIds) => {
      try {
        await axios.put('/api/messages/mark-read', { messageIds });
      } catch (error) {
        console.error('Error marking messages as read:', error);
      }
    };

    const handleUserSelect = (user) => {
      selectedUser.value = user;
      if (unreadCounts[user.id]) {
        unreadCounts[user.id] = 0;
      }
    };

    const isUserMessage = (message) => {
      return message.sender_id === props.user.id;
    };

    const getSenderName = (senderId) => {
      const sender = onlineUsers.value.find(u => u.id === senderId);
      return sender ? sender.username : 'Unknown User';
    };

    const isUserOnline = (userId) => {
      const user = onlineUsers.value.find(u => u.id === userId);
      return user ? user.online : false;
    };

    const formatTime = (timestamp) => {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    };

    const calculateUnreads = () => {
      messages.value.forEach(msg => {
        if (!msg.read && msg.sender_id !== props.user.id) {
          if (!unreadCounts[msg.sender_id]) {
            unreadCounts[msg.sender_id] = 0;
          }
          unreadCounts[msg.sender_id]++;
        }
      });
    };

    const markAsRead = async () => {
      if (!selectedUser.value) return;
      
      const unreadIds = messages.value
        .filter(msg => !msg.read && msg.sender_id === selectedUser.value.id)
        .map(msg => msg.id);

      if (unreadIds.length > 0) {
        await markMessagesAsRead(unreadIds);
        fetchMessages(selectedUser.value.id);
      }
    };

    // Animations
    const initAnimations = () => {
          anime({
            targets: document.querySelectorAll('.user-card'),
            opacity: [0, 1],
            translateX: [-50, 0],
            delay: anime.stagger(100),
            duration: 800,
            easing: 'easeOutExpo'
          });

          anime({
            targets: '.chat-container',
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 600,
            easing: 'spring(1, 80, 10, 0)'
          });
        };

        const messageEnterAnimation = (index) => {
          anime({
            targets: document.querySelectorAll(`.message`)[index],
            scale: [0.95, 1],
            opacity: [0, 1],
            duration: 400,
            easing: 'easeOutBack'
          });
        };

    // Lifecycle hooks
    onMounted(() => {
      fetchOnlineUsers();
      initAnimations();
      
      pollingInterval.value = setInterval(() => {
        fetchOnlineUsers();
        if (selectedUser.value) {
          fetchMessages(selectedUser.value.id);
        }
      }, 10000);
    });

    onBeforeUnmount(() => {
      clearInterval(pollingInterval.value);
    });

    // Watchers
    watch(messages, (newVal, oldVal) => {
      calculateUnreads();
      if (newVal.length > oldVal.length) {
        messageEnterAnimation(newVal.length - 1);
      }
    });

    watch(selectedUser, (newUser) => {
      if (newUser) {
        fetchMessages(newUser.id);
      }
    });

    watch(messages, () => {
      markAsRead();
    });

    return {
      messages,
      inputMessage,
      onlineUsers,
      selectedUser,
      unreadCounts,
      notificationDetails,
      messagesWindow,
      fetchMessages,
      fetchOnlineUsers,
      sendMessage,
      handleUserSelect,
      isUserMessage,
      getSenderName,
      isUserOnline,
      formatTime
    };
  }
};
</script>

<style>
:root {
  --glass-bg: rgba(255, 255, 255, 0.05);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  --primary-gradient: linear-gradient(45deg, #6366f1, #8b5cf6);
}

.messaging-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  backdrop-filter: blur(10px);
}

.user-list-container {
  flex: 0 0 320px;
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border-right: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  padding: 1rem;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background: var(--glass-bg);
  border-radius: 12px;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.user-card {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-radius: 15px;
  background: var(--glass-bg);
  backdrop-filter: blur(5px);
  border: 1px solid var(--glass-border);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.user-card:hover {
  transform: translateX(10px);
  background: rgba(255, 255, 255, 0.1);
}

.user-card.active {
  background: var(--primary-gradient);
  border-color: rgba(255, 255, 255, 0.2);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 1rem;
  position: relative;
}

.online-status {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  position: absolute;
  bottom: -2px;
  right: -2px;
  border: 2px solid var(--glass-bg);
}

.online-status.online {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

.online-status.offline {
  background: #64748b;
}

.user-info {
  flex: 1;
  position: relative;
}

.user-info h3 {
  margin: 0;
  font-size: 1rem;
  color: white;
}

.user-info p {
  margin: 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
}

.unread-count {
  position: absolute;
  top: 0;
  right: 0;
  background: #ef4444;
  color: white;
  font-size: 0.7rem;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-container {
  flex: 1;
  background: var(--glass-bg);
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--glass-border);
  display: flex;
  align-items: center;
  background: var(--glass-bg);
}

.avatar {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: var(--primary-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 1.5rem;
}

.messages-window {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.message {
  max-width: 70%;
  padding: 1rem 1.5rem;
  border-radius: 20px;
  backdrop-filter: blur(5px);
  border: 1px solid var(--glass-border);
  animation: messageEnter 0.4s ease-out;
}

@keyframes messageEnter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.sent {
  align-self: flex-end;
  background: var(--primary-gradient);
  border: none;
  color: white;
}

.message.received {
  align-self: flex-start;
  background: var(--glass-bg);
  color: white;
}

.message.system {
  align-self: center;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  width: 80%;
}

.message-content {
  font-size: 0.95rem;
  line-height: 1.4;
}

.message-time {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  display: block;
  margin-top: 0.5rem;
}

.message-input-container {
  padding: 1.5rem;
  background: var(--glass-bg);
  border-top: 1px solid var(--glass-border);
  display: flex;
  gap: 1rem;
}

.message-input-container textarea {
  flex: 1;
  padding: 1rem;
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  color: white;
  font-size: 1rem;
  resize: none;
  transition: all 0.3s ease;
}

.message-input-container textarea:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.08);
}

.message-input-container button {
  padding: 0.75rem 2rem;
  background: var(--primary-gradient);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.message-input-container button:hover {
  transform: translateY(-1px);
}

.message-input-container button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notification-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(5px);
}

.glass-effect {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  padding: 2rem;
  max-width: 600px;
  width: 90%;
}

.online-indicator {
  width: 10px;
  height: 10px;
  background: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 12px #10b981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  70% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

@media (max-width: 768px) {
  .messaging-container {
    flex-direction: column;
  }
  
  .user-list-container {
    width: 100%;
    max-height: 40vh;
    flex: none;
  }
  
  .chat-container {
    height: 60vh;
  }
  
  .message {
    max-width: 85%;
  }
}
</style>