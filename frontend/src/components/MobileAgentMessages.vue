<template>
  <div class="mobile-agent-messages">
    <div class="section-header">
      <h2>Messages</h2>
      <div class="refresh-button" @click="$emit('load-conversations')">
        <font-awesome-icon icon="sync" :class="{ 'fa-spin': isLoading }" />
      </div>
    </div>

    <div v-if="!selectedConversation" class="conversations-list">
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>Loading your messages...</p>
      </div>

      <div v-else-if="conversations.length === 0" class="empty-state">
        <font-awesome-icon icon="comment-slash" class="empty-icon" />
        <p>No conversations yet</p>
      </div>

      <div 
        v-else
        v-for="conversation in conversations" 
        :key="conversation.userId"
        class="conversation-item"
        :class="{ unread: conversation.unreadCount > 0 }"
        @click="$emit('open-conversation', conversation)"
      >
        <div class="user-avatar">
          <font-awesome-icon icon="user" />
          <div v-if="conversation.online" class="online-indicator"></div>
        </div>
        <div class="conversation-content">
          <div class="conversation-header">
            <h3 class="username">{{ conversation.username }}</h3>
            <span class="message-time">{{ formatMessageTimeAgo(conversation.lastMessage.timestamp) }}</span>
          </div>
          <div class="message-preview">
            {{ truncateMessage(conversation.lastMessage.message) }}
          </div>
        </div>
        <div v-if="conversation.unreadCount > 0" class="unread-count">
          {{ conversation.unreadCount }}
        </div>
      </div>
    </div>

    <div v-else class="conversation-view">
      <div class="conversation-header">
        <button class="back-button" @click="$emit('close-conversation')">
          <font-awesome-icon icon="arrow-left" />
        </button>
        <div class="user-info">
          <h3>{{ selectedConversation.username }}</h3>
          <div class="online-status">
            <span class="status-indicator" :class="{ online: selectedConversation.online }"></span>
            {{ selectedConversation.online ? 'Online' : 'Offline' }}
          </div>
        </div>
      </div>

      <div class="messages-container">
        <div v-if="messages.length === 0" class="empty-state">
          <p>No messages yet. Send the first message!</p>
        </div>

        <div v-else class="message-bubbles">
          <div 
            v-for="message in messages" 
            :key="message.id"
            class="message-bubble"
            :class="{ 
              outgoing: message.sender_id === currentUserId,
              incoming: message.sender_id !== currentUserId
            }"
          >
            <div class="message-content">
              {{ message.message }}
            </div>
            <div class="message-time">
              {{ formatMessageTime(message.timestamp) }}
              <font-awesome-icon 
                v-if="message.sender_id === currentUserId" 
                :icon="message.read ? 'check-double' : 'check'" 
                class="read-status"
              />
            </div>
          </div>
        </div>
      </div>

      <div class="message-input-container">
        <textarea 
          v-model="localMessage" 
          class="message-input" 
          placeholder="Type a message..." 
          @keyup.enter.prevent="$emit('send-message', localMessage)"
          rows="1"
        ></textarea>
        <button 
  class="send-button" 
  @click="$emit('send-message', localMessage)"
  :disabled="!localMessage.trim() || isSending"
>
  <font-awesome-icon :icon="isSending ? 'spinner' : 'paper-plane'" :spin="isSending" />
</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, watch } from 'vue'
import { format } from 'date-fns'

// Use ref to create local state for newMessage
const localMessage = ref('')

// Define props
const props = defineProps({
  conversations: {
    type: Array,
    default: () => []
  },
  selectedConversation: {
    type: Object,
    default: null
  },
  messages: {
    type: Array,
    default: () => []
  },
  newMessage: {
    type: String,
    default: ''
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  isSending: {
    type: Boolean,
    default: false
  },
  currentUserId: {
    type: Number,
    required: true
  }
})

// Watch for changes in the prop to sync with local state
watch(() => props.newMessage, (newVal) => {
  localMessage.value = newVal
})

// Define emits properly
defineEmits([
  'load-conversations',
  'open-conversation',
  'close-conversation',
  'send-message',
  'scroll-bottom'
])

const truncateMessage = (text) => {
  return text.length > 50 ? text.substring(0, 47) + '...' : text
}

const formatMessageTime = (timestamp) => {
  try {
    return format(new Date(timestamp), 'HH:mm')
  } catch {
    return ''
  }
}

const formatMessageTimeAgo = (timestamp) => {
  try {
    const date = new Date(timestamp)
    return date.toLocaleDateString() === new Date().toLocaleDateString() 
      ? format(date, 'HH:mm')
      : format(date, 'dd/MM/yy')
  } catch {
    return ''
  }
}
</script>

<style scoped>
.mobile-agent-messages {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.refresh-button {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background-color: var(--input-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  margin-bottom: 0.5rem;
  background-color: var(--input-bg);
  border-radius: 8px;
  transition: all 0.2s;
}

.conversation-item.unread {
  border-left: 3px solid var(--primary-color);
  background-color: var(--hover-bg);
}

.user-avatar {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--secondary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
}

.online-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #28a745;
  border: 2px solid var(--body-bg);
}

.conversation-content {
  flex: 1;
  min-width: 0;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.username {
  font-size: 0.9rem;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-light);
}

.message-preview {
  font-size: 0.85rem;
  color: var(--text-light);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.unread-count {
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  background-color: var(--primary-color);
  color: white;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.conversation-view {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0;
}

.message-bubbles {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  padding: 0 1rem;
}

.message-bubble {
  max-width: 85%;
  padding: 0.8rem;
  border-radius: 12px;
}

.message-bubble.outgoing {
  background-color: var(--primary-color);
  color: white;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
}

.message-bubble.incoming {
  background-color: var(--input-bg);
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}

.message-content {
  word-break: break-word;
  line-height: 1.4;
}

.message-time {
  font-size: 0.7rem;
  opacity: 0.8;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.read-status {
  font-size: 0.6rem;
}

.message-input-container {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 0;
  border-top: 1px solid var(--border-color);
}

.message-input {
  flex: 1;
  padding: 0.8rem;
  border-radius: 20px;
  background-color: var(--input-bg);
  border: 1px solid var(--border-color);
  resize: none;
  max-height: 120px;
}

.send-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-light);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  gap: 1rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-color);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .message-bubble {
    max-width: 90%;
  }
  
  .message-input {
    padding: 0.6rem;
  }
}
</style>