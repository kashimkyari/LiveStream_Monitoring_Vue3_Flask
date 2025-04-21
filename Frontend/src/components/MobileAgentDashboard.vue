<template>
  <div class="mobile-agent-dashboard" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="page-header">
      <h1>Agent Dashboard <span class="mobile-badge">Mobile</span></h1>
    </div>
    
    <div class="dashboard-tabs">
      <div 
        v-for="(tab, index) in tabs" 
        :key="index" 
        class="tab-item" 
        :class="{ active: activeTab === index }"
        @click="activeTab = index"
      >
        <div class="tab-icon-container">
          <font-awesome-icon :icon="tab.icon" class="tab-icon" />
          <span v-if="tab.icon === 'bell' && unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </div>
        <span class="tab-text">{{ tab.name }}</span>
      </div>
    </div>
    
    <div class="tab-content">
      <!-- My Streams tab -->
      <div v-if="activeTab === 0" class="tab-pane">
        <div class="section-header">
          <h2>My Assigned Streams</h2>
          <div class="refresh-button" @click="loadAssignments">
            <font-awesome-icon icon="sync" :class="{ 'fa-spin': isLoadingAssignments }" />
          </div>
        </div>
        
        <div v-if="isLoadingAssignments" class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading your streams...</p>
        </div>
        
        <div v-else-if="assignments.length === 0" class="empty-state">
          <p>You don't have any assigned streams.</p>
        </div>
        
        <div v-else class="stream-cards">
          <div 
            v-for="assignment in assignments" 
            :key="assignment.id" 
            class="stream-card card"
            @click="openStreamDetails(assignment.stream)"
          >
            <div class="stream-card-header">
              <h3>{{ assignment.stream.streamer_username }}</h3>
              <div class="stream-platform" :class="assignment.stream.platform">
                {{ assignment.stream.platform }}
              </div>
            </div>
            <div class="stream-card-body">
              <div class="stream-info">
                <p class="stream-viewers">
                  <font-awesome-icon icon="eye" /> 
                  {{ formatNumber(assignment.stream.viewer_count || 0) }}
                </p>
                <p class="stream-time">
                  <font-awesome-icon icon="clock" />
                  {{ formatStreamTime(assignment.stream.stream_start_time) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Analytics Tab -->
      <div v-else-if="activeTab === 1" class="tab-pane">
        <div class="section-header">
          <h2>My Performance</h2>
        </div>
        
        <div class="stats-container">
          <div class="stat-card card">
            <div class="stat-value">{{ stats.totalAssignments }}</div>
            <div class="stat-label">Total Assignments</div>
          </div>
          
          <div class="stat-card card">
            <div class="stat-value">{{ stats.activeStreams }}</div>
            <div class="stat-label">Active Streams</div>
          </div>
          
          <div class="stat-card card">
            <div class="stat-value">{{ stats.completedToday }}</div>
            <div class="stat-label">Completed Today</div>
          </div>
        </div>
        
        <div class="performance-chart-container">
          <!-- Mobile-optimized chart would go here -->
          <p class="placeholder-text">Performance chart (simplified for mobile)</p>
        </div>
      </div>
      
      <!-- Messages Tab -->
      <div v-else-if="activeTab === 2" class="tab-pane">
        <div class="section-header">
          <h2>Messages</h2>
          <div class="refresh-button" @click="loadConversations">
            <font-awesome-icon icon="sync" :class="{ 'fa-spin': isLoadingMessages }" />
          </div>
        </div>
        
        <!-- Conversations List -->
        <div v-if="!selectedConversation" class="conversations-list">
          <div v-if="isLoadingMessages" class="loading-container">
            <div class="loading-spinner"></div>
            <p>Loading your messages...</p>
          </div>
          
          <div v-else-if="conversations.length === 0" class="empty-state">
            <font-awesome-icon icon="comment-slash" size="2x" class="empty-icon mb-3" />
            <p>No conversations yet</p>
          </div>
          
          <div 
            v-else
            v-for="conversation in conversations" 
            :key="conversation.userId"
            class="conversation-item"
            :class="{ unread: conversation.unreadCount > 0 }"
            @click="openConversation(conversation)"
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
              <div class="message-preview" :class="{ 'font-weight-bold': conversation.unreadCount > 0 }">
                {{ conversation.lastMessage.message.length > 50 
                  ? conversation.lastMessage.message.substring(0, 50) + '...' 
                  : conversation.lastMessage.message }}
              </div>
            </div>
            <div v-if="conversation.unreadCount > 0" class="unread-count">
              {{ conversation.unreadCount }}
            </div>
          </div>
        </div>
        
        <!-- Individual Conversation View -->
        <div v-else class="conversation-view">
          <div class="conversation-header">
            <button class="back-button" @click="closeConversation">
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
          
          <div class="messages-container" ref="messagesContainer">
            <div v-if="isLoadingConversation" class="loading-container">
              <div class="loading-spinner"></div>
              <p>Loading messages...</p>
            </div>
            
            <div v-else-if="activeConversationMessages.length === 0" class="empty-state">
              <p>No messages yet. Send the first message!</p>
            </div>
            
            <div v-else class="message-bubbles">
              <div 
                v-for="message in activeConversationMessages" 
                :key="message.id"
                class="message-bubble"
                :class="{ 
                  'outgoing': message.sender_id === currentUserId,
                  'incoming': message.sender_id !== currentUserId,
                  'unread': !message.read && message.sender_id !== currentUserId
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
                    :class="{ 'read': message.read }"
                  />
                </div>
              </div>
            </div>
          </div>
          
          <div class="message-input-container">
            <textarea 
              v-model="newMessage" 
              class="message-input" 
              placeholder="Type a message..." 
              @keyup.enter="sendMessage"
              rows="1"
              ref="messageInput"
            ></textarea>
            <button 
              class="send-button" 
              @click="sendMessage"
              :disabled="!newMessage.trim() || isSendingMessage"
            >
              <font-awesome-icon :icon="isSendingMessage ? 'spinner' : 'paper-plane'" :spin="isSendingMessage" />
            </button>
          </div>
        </div>
      </div>
      
      <!-- Notifications Tab -->
      <div v-else-if="activeTab === 3" class="tab-pane">
        <div class="section-header">
          <h2>Notifications</h2>
          <div class="notification-controls">
            <button class="btn btn-sm btn-outline-primary" @click="markAllAsRead" v-if="unreadCount > 0">
              <font-awesome-icon icon="check-double" /> Mark All Read
            </button>
          </div>
        </div>
        
        <div class="notification-filters">
          <div class="filter-toggle">
            <span>Group by Type</span>
            <div class="toggle-switch" :class="{ active: notifications.groupByType }" @click="toggleGroupByType">
              <div class="toggle-switch-handle"></div>
            </div>
          </div>
          <div class="filter-toggle">
            <span>Group by Stream</span>
            <div class="toggle-switch" :class="{ active: notifications.groupByStream }" @click="toggleGroupByStream">
              <div class="toggle-switch-handle"></div>
            </div>
          </div>
        </div>
        
        <div v-if="notifications.items.length === 0" class="empty-state">
          <font-awesome-icon icon="bell-slash" size="2x" class="empty-icon" />
          <p>No notifications to display</p>
        </div>
        
        <div v-else class="notification-list">
          <div 
            v-for="notification in notifications.items" 
            :key="notification.id"
            class="notification-item"
            :class="{ unread: !notification.read }"
            @click="markAsRead(notification.id)"
          >
            <div class="notification-icon" :style="{ backgroundColor: getNotificationColor(notification) }">
              <font-awesome-icon :icon="getNotificationIcon(notification)" />
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ getNotificationTitle(notification) }}</div>
              <div class="notification-text">{{ notification.message }}</div>
              <div class="notification-time">{{ formatNotificationTimeAgo(notification.timestamp) }}</div>
            </div>
            <div class="notification-status">
              <div v-if="!notification.read" class="unread-indicator"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Settings Tab -->
      <div v-else-if="activeTab === 4" class="tab-pane">
        <div class="section-header">
          <h2>Settings</h2>
        </div>
        
        <div class="settings-form">
          <div class="form-group">
            <label class="form-label">Notification Preferences</label>
            <div class="toggle-option">
              <span>Email Notifications</span>
              <div class="toggle-switch" :class="{ active: settings.emailNotifications }" @click="toggleSetting('emailNotifications')">
                <div class="toggle-switch-handle"></div>
              </div>
            </div>
            
            <div class="toggle-option">
              <span>Push Notifications</span>
              <div class="toggle-switch" :class="{ active: settings.pushNotifications }" @click="toggleSetting('pushNotifications')">
                <div class="toggle-switch-handle"></div>
              </div>
            </div>
            
            <div class="toggle-option">
              <span>Group Notifications by Type</span>
              <div class="toggle-switch" :class="{ active: notifications.groupByType }" @click="toggleGroupByType">
                <div class="toggle-switch-handle"></div>
              </div>
            </div>
            
            <div class="toggle-option">
              <span>Group Notifications by Stream</span>
              <div class="toggle-switch" :class="{ active: notifications.groupByStream }" @click="toggleGroupByStream">
                <div class="toggle-switch-handle"></div>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Theme Preference</label>
            <div class="theme-options">
              <div 
                class="theme-option" 
                :class="{ selected: isDarkTheme }"
                @click="setTheme(true)"
              >
                <font-awesome-icon icon="moon" />
                <span>Dark</span>
              </div>
              <div 
                class="theme-option" 
                :class="{ selected: !isDarkTheme }"
                @click="setTheme(false)"
              >
                <font-awesome-icon icon="sun" />
                <span>Light</span>
              </div>
            </div>
          </div>
          
          <button class="btn btn-primary save-settings" @click="saveSettings">
            Save Settings
          </button>
          
          <button 
            class="btn btn-outline-danger logout-button mt-4" 
            @click="logout" 
            :disabled="isLoggingOut"
          >
            <font-awesome-icon 
              icon="sign-out-alt" 
              :spin="isLoggingOut" 
              class="mr-1" 
            /> 
            {{ isLoggingOut ? 'Logging out...' : 'Logout' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject, onMounted, watch, nextTick } from 'vue'
import { useToast } from 'vue-toastification'
import StreamService from '../services/StreamService'
import AuthService from '../services/AuthService'
import MessageService from '../services/MessageService'
import { formatDistance, format } from 'date-fns'
import { useMobileNotifications } from '../composables/useMobileNotifications'
import anime from 'animejs/lib/anime.es'
import io from 'socket.io-client'

export default {
  name: 'MobileAgentDashboard',
  setup() {
    // Theme state - synced with app-level theme
    const isDarkTheme = ref(localStorage.getItem('themePreference') === 'dark')
    
    // Get theme update method from App.vue
    const updateAppTheme = inject('updateTheme', null)
    
    // If app provides a theme, use that
    const appTheme = inject('isDarkTheme', null)
    if (appTheme !== null) {
      isDarkTheme.value = appTheme.value
    }
    const toast = useToast()
    
    // Use mobile notifications composable
    const { 
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      formatTimeAgo: formatNotificationTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle
    } = useMobileNotifications()
    
    // Tab management
    const tabs = [
      { name: 'Streams', icon: 'video' },
      { name: 'Analytics', icon: 'chart-line' },
      { name: 'Messages', icon: 'comment' },
      { name: 'Notifications', icon: 'bell' },
      { name: 'Settings', icon: 'cog' }
    ]
    const activeTab = ref(0)
    
    // Streams data
    const assignments = ref([])
    const isLoadingAssignments = ref(false)
    
    // Analytics data (simplified for mobile)
    const stats = ref({
      totalAssignments: 0,
      activeStreams: 0,
      completedToday: 0
    })
    
    // Settings
    const settings = ref({
      emailNotifications: true,
      pushNotifications: false
    })
    
    // Stream detail modal
    const showStreamDetailModal = ref(false)
    const selectedStream = ref(null)
    
    // Load assignments when component mounts
    onMounted(async () => {
      await loadAssignments()
      calculateStats()
    })
    
    // Load agent's assigned streams
    const loadAssignments = async () => {
      try {
        isLoadingAssignments.value = true
        // Get the agent's ID, typically this would come from a user store
        const agentId = localStorage.getItem('userId') || '1' // Fallback for demo
        
        const response = await StreamService.getAgentAssignments(agentId)
        assignments.value = response.data
        
        // Calculate stats after loading assignments
        calculateStats()
      } catch (error) {
        console.error('Failed to load assignments:', error)
        toast.error('Could not load your stream assignments')
      } finally {
        isLoadingAssignments.value = false
      }
    }
    
    // Calculate analytics stats based on assignments
    const calculateStats = () => {
      stats.value.totalAssignments = assignments.value.length
      
      // Count active streams (simplified logic for example)
      stats.value.activeStreams = assignments.value.filter(a => 
        a.stream.stream_status === 'live'
      ).length
      
      // Count completed today (simplified)
      const today = new Date().toDateString()
      stats.value.completedToday = assignments.value.filter(a => 
        a.completed && new Date(a.completed_at).toDateString() === today
      ).length
    }
    
    // Open stream details modal
    const openStreamDetails = (stream) => {
      selectedStream.value = stream
      showStreamDetailModal.value = true
    }
    
    // Toggle a setting value
    const toggleSetting = (settingName) => {
      settings.value[settingName] = !settings.value[settingName]
    }
    
    // Set theme preference with bidirectional syncing
    const setTheme = (isDark) => {
      // Update local theme
      isDarkTheme.value = isDark
      
      // Save to localStorage for persistence
      localStorage.setItem('themePreference', isDark ? 'dark' : 'light')
      
      // Sync with app-level theme if available
      if (updateAppTheme && typeof updateAppTheme === 'function') {
        updateAppTheme(isDark)
      }
    }
    
    // Save settings
    const saveSettings = () => {
      // In a real app, this would save to an API
      toast.success('Settings saved successfully')
    }
    
    // Format number for display (e.g. 1000 -> 1K)
    const formatNumber = (num) => {
      if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M'
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K'
      }
      return num
    }
    
    // Format stream time as relative time
    const formatStreamTime = (timestamp) => {
      if (!timestamp) return 'Unknown'
      
      try {
        const date = new Date(timestamp)
        return formatDistance(date, new Date(), { addSuffix: true })
      } catch (e) {
        console.error('Error formatting date:', e)
        return 'Unknown'
      }
    }
    
    // Handle user logout with delay animation for better UX
    const isLoggingOut = ref(false)
    const logout = async () => {
      // Prevent multiple clicks
      if (isLoggingOut.value) return
      
      isLoggingOut.value = true
      toast.info("Logging out in 3 seconds...")
      
      // Animated countdown using animejs timeline
      const timeline = anime.timeline({
        easing: 'easeOutExpo'
      })
      
      // Subtle UI animations during countdown
      timeline.add({
        targets: '.mobile-agent-dashboard',
        opacity: [1, 0.9],
        duration: 3000
      })
      
      // Set a timeout for the actual logout
      setTimeout(async () => {
        try {
          // Call the auth service logout endpoint - don't await to avoid API errors
          // showing unnecessary error toasts to user
          AuthService.logout().catch(err => console.warn('Logout API error:', err))
          
          // Since we're using the finally block in AuthService.logout(),
          // local storage will always be cleared, so we don't need to do it again here
          
          // Notify parent component about logout
          const logout = inject('logout')
          if (typeof logout === 'function') {
            logout(true) // This will navigate to login page
          } else {
            // Fallback - redirect to login page
            window.location.href = '/'
          }
          
          // No toast needed here as the page will redirect
        } catch (error) {
          console.error('Logout error in component:', error)
          isLoggingOut.value = false
          
          // Reset opacity if logout fails
          anime({
            targets: '.mobile-agent-dashboard',
            opacity: 1,
            duration: 300
          })
        }
      }, 3000)
    }
    
    // Synchronize theme with app-level theme
    watch(isDarkTheme, (newValue) => {
      if (updateAppTheme && typeof updateAppTheme === 'function') {
        updateAppTheme(newValue)
      }
    })
    
    // Messaging functionality
    const conversations = ref([])
    const isLoadingMessages = ref(false)
    const selectedConversation = ref(null)
    const activeConversationMessages = ref([])
    const isLoadingConversation = ref(false)
    const newMessage = ref('')
    const isSendingMessage = ref(false)
    const messagesContainer = ref(null)
    const messageInput = ref(null)
    const messageUnreadCounts = ref({})
    const totalUnreadMessageCount = ref(0)
    
    // Current user ID for messaging
    const currentUserId = parseInt(localStorage.getItem('userId')) || null
    
    // Socket connection for real-time messaging
    let socket = null
    
    // Initialize Socket.IO connection for real-time messaging
    onMounted(() => {
      // Initialize socket connection if logged in
      if (currentUserId) {
        initializeSocketConnection()
      }
      
      // Load conversations when first visiting messages tab
      watch(activeTab, (newTab) => {
        if (newTab === 2 && conversations.value.length === 0) {
          loadConversations()
        }
      })
    })
    
    // Initialize socket.io connection
    const initializeSocketConnection = () => {
      if (socket) return // Already connected
      
      // Connect to Socket.IO server (same domain as REST API)
      socket = io('http://localhost:5000', {  // Explicit server URL
        path: '/ws',                         // Matches server path
        transports: ['websocket'],           // Keep if you want WS-only
        upgrade: false,                      // Keep if you want to disable upgrade
        query: {
          userId: currentUserId
        }
      })
      
      // Handle connection events
      socket.on('connect', () => {
        console.log('Socket.IO connected')
      })
      
      // Handle message events
      socket.on('new_message', (message) => {
        // If message is in the current conversation, add it to the list
        if (selectedConversation.value && 
            (message.sender_id === selectedConversation.value.userId || 
             message.receiver_id === selectedConversation.value.userId)) {
          activeConversationMessages.value.push(message)
          
          // Auto-scroll to the bottom of the conversation
          scrollToBottom()
          
          // Mark as read if the user is viewing the conversation
          if (message.sender_id !== currentUserId) {
            markMessageAsRead(message.id)
          }
        } else {
          // Update unread counts
          updateUnreadCount(message.sender_id)
        }
        
        // Update conversation list
        refreshConversationsList()
      })
      
      // Handle user status events (online/offline)
      socket.on('user_status', (data) => {
        const { userId, status } = data
        
        // Update conversations list with new status
        const conversation = conversations.value.find(c => c.userId === userId)
        if (conversation) {
          conversation.online = status === 'online'
        }
        
        // Update selected conversation if applicable
        if (selectedConversation.value && selectedConversation.value.userId === userId) {
          selectedConversation.value.online = status === 'online'
        }
      })
      
      // Handle typing indicator events
      socket.on('typing', (data) => {
        if (selectedConversation.value && data.userId === selectedConversation.value.userId) {
          selectedConversation.value.isTyping = true
          
          // Clear typing indicator after a delay
          if (selectedConversation.value.typingTimeout) {
            clearTimeout(selectedConversation.value.typingTimeout)
          }
          
          selectedConversation.value.typingTimeout = setTimeout(() => {
            if (selectedConversation.value) {
              selectedConversation.value.isTyping = false
            }
          }, 3000)
        }
      })
      
      // Handle errors
      socket.on('error', (error) => {
        console.error('Socket.IO error:', error)
      })
      
      // Handle disconnection
      socket.on('disconnect', () => {
        console.log('Socket.IO disconnected')
      })
    }
    
    // Load conversations list
    const loadConversations = async () => {
      try {
        isLoadingMessages.value = true
        
        // Get recent conversations from API
        const response = await MessageService.getLatestConversations()
        
        // Format conversations for display
        conversations.value = response.data.map(conv => ({
          userId: conv.user_id,
          username: conv.username,
          lastMessage: {
            id: conv.last_message_id,
            message: conv.last_message,
            timestamp: conv.last_message_time
          },
          unreadCount: conv.unread_count || 0,
          online: conv.online || false
        }))
        
        // Update total unread count
        totalUnreadMessageCount.value = conversations.value.reduce(
          (total, conv) => total + conv.unreadCount, 0
        )
        
      } catch (error) {
        console.error('Failed to load conversations:', error)
        toast.error('Could not load your conversations')
      } finally {
        isLoadingMessages.value = false
      }
    }
    
    // Open a specific conversation
    const openConversation = async (conversation) => {
      try {
        selectedConversation.value = conversation
        isLoadingConversation.value = true
        
        // Load messages for this conversation
        const response = await MessageService.getMessages(conversation.userId)
        activeConversationMessages.value = response.data
        
        // Mark all messages from this user as read
        if (conversation.unreadCount > 0) {
          await MessageService.markMessagesRead(conversation.userId)
          
          // Update unread count
          updateUnreadCounts()
        }
        
        // Join room for real-time updates
        if (socket) {
          socket.emit('join_room', { user_id: conversation.userId })
        }
        
        // Focus message input
        await nextTick()
        if (messageInput.value) {
          messageInput.value.focus()
        }
        
        // Scroll to bottom of conversation
        scrollToBottom()
        
      } catch (error) {
        console.error('Failed to load conversation:', error)
        toast.error('Could not load messages')
      } finally {
        isLoadingConversation.value = false
      }
    }
    
    // Close the current conversation
    const closeConversation = () => {
      selectedConversation.value = null
      activeConversationMessages.value = []
    }
    
    // Send a new message
    const sendMessage = async () => {
      if (!newMessage.value.trim() || !selectedConversation.value || isSendingMessage.value) {
        return
      }
      
      try {
        isSendingMessage.value = true
        
        // Send message to API
        const response = await MessageService.sendMessage({
          receiver_id: selectedConversation.value.userId,
          message: newMessage.value.trim()
        })
        
        // Add the sent message to the conversation
        const sentMessage = response.data
        activeConversationMessages.value.push(sentMessage)
        
        // Update the conversation's last message
        selectedConversation.value.lastMessage = {
          id: sentMessage.id,
          message: sentMessage.message,
          timestamp: sentMessage.timestamp
        }
        
        // Clear the input field
        newMessage.value = ''
        
        // Scroll to bottom of conversation
        scrollToBottom()
        
      } catch (error) {
        console.error('Failed to send message:', error)
        toast.error('Could not send message')
      } finally {
        isSendingMessage.value = false
        
        // Refocus the input field
        if (messageInput.value) {
          messageInput.value.focus()
        }
      }
    }
    
    // Mark a single message as read
    const markMessageAsRead = async (messageId) => {
      try {
        await MessageService.markMessageRead(messageId)
        
        // Update the message in the current conversation
        const message = activeConversationMessages.value.find(m => m.id === messageId)
        if (message) {
          message.read = true
        }
        
        // Update unread counts
        updateUnreadCounts()
        
      } catch (error) {
        console.error('Failed to mark message as read:', error)
      }
    }
    
    // Update unread count for a specific user
    const updateUnreadCount = async (userId) => {
      try {
        const response = await MessageService.getUnreadCount(userId)
        const count = response.data.count
        
        // Update the conversation unread count
        const conversation = conversations.value.find(c => c.userId === userId)
        if (conversation) {
          conversation.unreadCount = count
        }
        
        // Update total unread count
        updateTotalUnreadCount()
        
      } catch (error) {
        console.error('Failed to update unread count:', error)
      }
    }
    
    // Update all unread counts
    const updateUnreadCounts = async () => {
      try {
        const response = await MessageService.getTotalUnreadCount()
        totalUnreadMessageCount.value = response.data.count
        
        // Refresh the conversations list to get updated counts
        refreshConversationsList()
        
      } catch (error) {
        console.error('Failed to update unread counts:', error)
      }
    }
    
    // Update total unread count
    const updateTotalUnreadCount = () => {
      totalUnreadMessageCount.value = conversations.value.reduce(
        (total, conv) => total + conv.unreadCount, 0
      )
    }
    
    // Refresh the conversations list
    const refreshConversationsList = async () => {
      // Only refresh if not in a conversation
      if (!selectedConversation.value) {
        await loadConversations()
      }
    }
    
    // Scroll to bottom of messages container
    const scrollToBottom = () => {
      nextTick(() => {
        if (messagesContainer.value) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        }
      })
    }
    
    // Format message time for chat bubbles
    const formatMessageTime = (timestamp) => {
      if (!timestamp) return ''
      
      try {
        const date = new Date(timestamp)
        return format(date, 'p') // 'p' gives time in 12-hour format (e.g., 9:30 PM)
      } catch (e) {
        console.error('Error formatting message time:', e)
        return ''
      }
    }
    
    // Format message time for conversation list (relative time)
    const formatMessageTimeAgo = (timestamp) => {
      if (!timestamp) return ''
      
      try {
        const date = new Date(timestamp)
        const now = new Date()
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))
        
        // If message is from today, show time
        if (diffDays === 0) {
          return format(date, 'p')
        }
        // If message is from yesterday, show 'Yesterday'
        else if (diffDays === 1) {
          return 'Yesterday'
        }
        // If message is from this week, show day name
        else if (diffDays < 7) {
          return format(date, 'EEE') // 'EEE' gives abbreviated day name (e.g., Mon)
        }
        // Otherwise show date
        else {
          return format(date, 'MMM d') // 'MMM d' gives abbreviated month and day (e.g., Jan 15)
        }
      } catch (e) {
        console.error('Error formatting message time ago:', e)
        return ''
      }
    }
    
    return {
      // Tab management
      tabs,
      activeTab,
      
      // Assignments and streams
      assignments,
      isLoadingAssignments,
      stats,
      
      // Settings
      settings,
      showStreamDetailModal,
      selectedStream,
      isDarkTheme,
      
      // Notifications (from composable)
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      formatNotificationTimeAgo,
      getNotificationIcon,
      getNotificationColor,
      getNotificationTitle,
      
      // Messaging
      conversations,
      isLoadingMessages,
      selectedConversation,
      activeConversationMessages,
      isLoadingConversation,
      newMessage,
      isSendingMessage,
      messagesContainer,
      messageInput,
      currentUserId,
      totalUnreadMessageCount,
      loadConversations,
      openConversation,
      closeConversation,
      sendMessage,
      markMessageAsRead,
      formatMessageTime,
      formatMessageTimeAgo,
      messageUnreadCounts,
      
      // Methods
      loadAssignments,
      openStreamDetails,
      toggleSetting,
      setTheme,
      saveSettings,
      formatNumber,
      formatStreamTime,
      logout,
      isLoggingOut
    }
  }
}
</script>

<style scoped>
.mobile-agent-dashboard {
  padding: 1rem;
  max-width: 100%;
}

.mobile-badge {
  font-size: 0.7rem;
  background-color: var(--primary-color);
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  margin-left: 0.5rem;
  vertical-align: middle;
}

.dashboard-tabs {
  display: flex;
  background-color: var(--input-bg);
  border-radius: 8px;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 10;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 0.8rem 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 2px solid transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.tab-item.active {
  border-bottom-color: var(--primary-color);
  color: var(--primary-color);
}

.tab-icon-container {
  position: relative;
  display: inline-block;
}

.tab-icon {
  font-size: 1.2rem;
  margin-bottom: 0.3rem;
}

.notification-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background-color: var(--danger-color, #dc3545);
  color: white;
  border-radius: 10px;
  font-size: 0.6rem;
  min-width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.tab-text {
  font-size: 0.8rem;
  font-weight: 500;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.section-header h2 {
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
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

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 0;
}

.empty-state {
  text-align: center;
  padding: 2rem 0;
  color: var(--text-light);
}

.stream-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

.stream-card {
  padding: 1rem;
  cursor: pointer;
}

.stream-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.8rem;
}

.stream-card-header h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.stream-platform {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-transform: capitalize;
}

.stream-platform.chaturbate {
  background-color: #f5a623;
  color: white;
}

.stream-platform.stripchat {
  background-color: #7e57c2;
  color: white;
}

.stream-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--text-light);
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.8rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  padding: 1rem;
  text-align: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.3rem;
  color: var(--primary-color);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-light);
}

.performance-chart-container {
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-text {
  color: var(--text-light);
  font-style: italic;
}

.settings-form {
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
}

.toggle-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--border-color);
}

.toggle-option:last-child {
  border-bottom: none;
}

.toggle-switch {
  width: 48px;
  height: 24px;
  border-radius: 12px;
  background-color: var(--border-color);
  position: relative;
  cursor: pointer;
  transition: background-color 0.2s;
}

.toggle-switch.active {
  background-color: var(--primary-color);
}

.toggle-switch-handle {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: white;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.toggle-switch.active .toggle-switch-handle {
  transform: translateX(24px);
}

.theme-options {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  background-color: var(--hover-bg);
  cursor: pointer;
}

.theme-option.selected {
  background-color: var(--primary-color);
  color: white;
}

.save-settings {
  width: 100%;
  margin-top: 1rem;
}

.logout-button {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
}

/* Notification Styles */
.notification-controls {
  display: flex;
  gap: 0.5rem;
}

.notification-filters {
  display: flex;
  justify-content: space-between;
  background-color: var(--hover-bg);
  border-radius: 8px;
  padding: 0.8rem 1rem;
  margin-bottom: 1rem;
}

.filter-toggle {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.85rem;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.notification-item {
  display: flex;
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  border-left: 3px solid transparent;
}

.notification-item.unread {
  border-left-color: var(--primary-color);
  background-color: var(--hover-bg);
}

.notification-icon {
  width: 2.5rem;
  height: 2.5rem;
  min-width: 2.5rem;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 600;
  margin-bottom: 0.3rem;
}

.notification-text {
  font-size: 0.85rem;
  color: var(--text-light);
  line-height: 1.4;
  margin-bottom: 0.5rem;
  word-break: break-word;
}

.notification-time {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.notification-status {
  display: flex;
  align-items: center;
}

.unread-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary-color);
}

/* Messages Tab Styles */
.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.conversation-item {
  display: flex;
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  border-left: 3px solid transparent;
}

.conversation-item.unread {
  border-left-color: var(--primary-color);
  background-color: var(--hover-bg);
}

.user-avatar {
  width: 3rem;
  height: 3rem;
  min-width: 3rem;
  border-radius: 50%;
  background-color: var(--secondary-color, #6c757d);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  position: relative;
}

.online-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #28a745;
  border: 2px solid var(--body-bg);
  position: absolute;
  bottom: 0;
  right: 0;
}

.conversation-content {
  flex: 1;
  min-width: 0; /* Prevent text overflow */
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.3rem;
}

.username {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-light);
  white-space: nowrap;
}

.message-preview {
  font-size: 0.85rem;
  color: var(--text-light);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.unread-count {
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  background-color: var(--primary-color);
  color: white;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

/* Individual Conversation View */
.conversation-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 10rem);
  max-height: calc(100vh - 10rem);
}

.conversation-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.8rem 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1rem;
}

.back-button {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-info {
  flex: 1;
}

.user-info h3 {
  margin: 0;
  font-size: 1rem;
}

.online-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-light);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-light);
}

.status-indicator.online {
  background-color: #28a745;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0;
}

.message-bubbles {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message-bubble {
  max-width: 80%;
  padding: 0.8rem 1rem;
  border-radius: 12px;
  position: relative;
}

.message-bubble.outgoing {
  align-self: flex-end;
  background-color: var(--primary-color);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-bubble.incoming {
  align-self: flex-start;
  background-color: var(--input-bg);
  border-bottom-left-radius: 4px;
}

.message-bubble.unread {
  border: 1px solid var(--primary-color);
}

.message-content {
  margin-bottom: 0.5rem;
  word-break: break-word;
  line-height: 1.4;
}

.message-time {
  font-size: 0.7rem;
  text-align: right;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 0.3rem;
}

.message-bubble.outgoing .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.message-bubble.incoming .message-time {
  color: var(--text-light);
}

.read-status {
  font-size: 0.7rem;
}

.read-status.read {
  color: #4FC3F7;
}

.message-input-container {
  display: flex;
  padding: 1rem 0;
  border-top: 1px solid var(--border-color);
  margin-top: auto;
}

.message-input {
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 0.8rem 1rem;
  background-color: var(--input-bg);
  resize: none;
  color: var(--text-color);
  max-height: 100px;
}

.message-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.send-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  border: none;
  margin-left: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.send-button:disabled {
  background-color: var(--text-light);
  cursor: not-allowed;
}

.empty-icon {
  margin-bottom: 1rem;
  color: var(--text-light);
}

/* Message Styles */
.message-list {
  background-color: var(--input-bg);
  border-radius: 8px;
  padding: 1rem;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>