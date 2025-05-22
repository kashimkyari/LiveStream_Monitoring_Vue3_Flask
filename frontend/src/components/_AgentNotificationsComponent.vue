<template>
  <div class="notifications-page" :class="{ 'dark-mode': isDarkMode }">
    <!-- Top navigation bar with filters and actions -->
    <div class="top-bar">
      <div class="filter-tabs">
        <button v-for="tab in ['All', 'Unread', 'Detections']" :key="tab" class="tab-btn"
          :class="{ 'active': mainFilter === tab }" @click="handleMainFilterChange(tab)">
          {{ tab }}
          <span v-if="tab === 'Unread'" class="badge">{{ unreadCount }}</span>
        </button>
      </div>

      <div class="action-buttons">
        <button class="icon-btn refresh-btn" @click="fetchNotifications" title="Refresh">
          <span class="icon">↻</span>
        </button>
        <button class="icon-btn" @click="toggleDarkMode" :title="isDarkMode ? 'Light Mode' : 'Dark Mode'">
          <span class="icon">{{ isDarkMode ? '☀️' : '🌙' }}</span>
        </button>
        <button class="icon-btn menu-btn" @click="isMenuOpen = !isMenuOpen" title="More Actions">
          <span class="icon">⋮</span>
        </button>
      </div>

      <!-- Dropdown menu -->
      <div v-if="isMenuOpen" class="dropdown-menu">
        <button @click="markAllAsRead" :disabled="filteredNotifications.filter(n => !n.read).length === 0">
          Mark All as Read
        </button>
        <button @click="isDeleteModalOpen = true" :disabled="filteredNotifications.length === 0">
          Delete All
        </button>
        <button @click="toggleSound">
          {{ soundEnabled ? 'Disable Sound' : 'Enable Sound' }}
        </button>
      </div>
    </div>

    <!-- Sub-filters for detection types -->
    <div v-if="mainFilter === 'Detections'" class="sub-filters">
      <button v-for="subTab in ['Visual', 'Audio', 'Chat']" :key="subTab" class="sub-filter-btn"
        :class="{ active: detectionSubFilter === subTab }" @click="detectionSubFilter = subTab">
        {{ subTab }}
      </button>
    </div>

    <!-- Main content area -->
    <div class="content-area">
      <!-- Left panel: Notifications list -->
      <div class="notifications-panel">
        <div class="panel-header">
          <h2>Notifications <span class="count">({{ filteredNotifications.length }})</span></h2>
        </div>

        <!-- Loading, error, or empty states -->
        <div v-if="loading" class="state-container">
          <div class="loading-spinner"></div>
          <p>Loading notifications...</p>
        </div>
        <div v-else-if="error" class="error-state">
          <p>{{ error }}</p>
          <button @click="fetchNotifications">Try Again</button>
        </div>
        <div v-else-if="filteredNotifications.length === 0" class="empty-state">
          <div class="empty-icon">🔔</div>
          <p>No notifications to display</p>
        </div>

        <!-- Notifications list -->
        <div v-else class="notification-list">
          <TransitionGroup name="list" tag="div">
            <div v-for="notification in filteredNotifications" :key="notification.id" class="notification-card" :class="{
              'read': notification.read,
              'unread': !notification.read,
              'selected': selectedNotification && selectedNotification.id === notification.id,
              'new-notification': newNotificationIds.includes(notification.id)
            }" @click="handleNotificationClick(notification)">
              <div class="notification-indicator" :style="{ backgroundColor: getNotificationColor(notification) }">
              </div>

              <div class="notification-content">
                <div class="notification-header">
                  <span class="notification-type">{{ getNotificationType(notification) }}</span>
                  <span class="notification-time">{{ formatTimestamp(notification.timestamp) }}</span>
                </div>

                <div class="notification-message">
                  {{ getNotificationMessage(notification) }}
                </div>

                <div class="notification-meta">
                  <span class="notification-source">
                    {{ notification.details?.platform || 'System' }} |
                    {{ notification.details?.streamer_name || 'Unknown' }}
                  </span>
                  <span v-if="notification.event_type === 'object_detection' &&
                    notification.details?.detections?.length" class="notification-confidence">
                    {{ formatConfidence(notification.details.detections[0].confidence) }}
                  </span>
                </div>
              </div>

              <div class="notification-actions">
                <button v-if="!notification.read" class="action-btn read-btn" @click.stop="markAsRead(notification.id)"
                  title="Mark as Read">
                  ✓
                </button>
                <button class="action-btn delete-btn" @click.stop="deleteNotification(notification.id)" title="Delete">
                  ×
                </button>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </div>

      <!-- Right panel: Notification details -->
      <div class="details-panel" v-if="selectedNotification || isMobile">
        <div v-if="!selectedNotification && isMobile" class="empty-detail">
          <div class="empty-icon">📋</div>
          <p>Select a notification to view details</p>
        </div>

        <div v-else-if="selectedNotification" class="detail-content">
          <div class="detail-header">
            <button v-if="isMobile" class="back-btn" @click="selectedNotification = null">
              &larr; Back
            </button>
            <h2>{{ getNotificationDetailTitle() }}</h2>

            <div class="detail-actions">
              <button v-if="!selectedNotification.read" class="action-btn" @click="markAsRead(selectedNotification.id)">
                Mark as Read
              </button>
              <button class="action-btn delete-btn" @click="isDeleteModalOpen = true">
                Delete
              </button>
              <button v-if="assignedToMe" class="action-btn view-stream-btn"
                @click="viewStreamDetails(selectedNotification)">
                View Stream
              </button>
            </div>
          </div>

          <!-- Notification details content -->
          <div class="detail-body">
            <div class="detail-field">
              <label>Type:</label>
              <span>{{ selectedNotification.event_type }}</span>
            </div>
            <div class="detail-field">
              <label>Stream URL:</label>
              <a :href="selectedNotification.room_url" target="_blank" rel="noopener noreferrer" class="url-link">
                {{ truncateUrl(selectedNotification.room_url) }}
              </a>
            </div>
            <div class="detail-field">
              <label>Timestamp:</label>
              <span>{{ formatTimestamp(selectedNotification.timestamp, true) }}</span>
            </div>
            <div class="detail-field">
              <label>Platform:</label>
              <span>{{ selectedNotification.details?.platform || 'Unknown' }}</span>
            </div>
            <div class="detail-field">
              <label>Streamer:</label>
              <span>{{ selectedNotification.details?.streamer_name || 'Unknown' }}</span>
            </div>
            <div v-if="selectedNotification.assigned_agent" class="detail-field">
              <label>Assigned To:</label>
              <span>
                {{ selectedNotification.assigned_agent }}
                <span v-if="assignedToMe" class="assigned-badge">You</span>
              </span>
            </div>

            <!-- Detection-specific details -->
            <div v-if="selectedNotification.event_type === 'object_detection'" class="type-details detection-details">
              <h3>Visual Detection</h3>

              <!-- Detection images -->
              <div class="detection-images">
                <div v-if="selectedNotification.details?.annotated_image" class="image-container">
                  <h4>Annotated Image</h4>
                  <img :src="formatImage(selectedNotification.details.annotated_image)" alt="Annotated Detection"
                    class="detection-image" @click="openImageModal(selectedNotification.details.annotated_image)" />
                </div>

                <div v-if="selectedNotification.details?.captured_image" class="image-container">
                  <h4>Captured Image</h4>
                  <img :src="formatImage(selectedNotification.details.captured_image)" alt="Captured Image"
                    class="detection-image" @click="openImageModal(selectedNotification.details.captured_image)" />
                </div>
              </div>

              <!-- Detected objects -->
              <div v-if="selectedNotification.details?.detections?.length" class="detected-objects">
                <h4>Detected Objects</h4>
                <div class="detections-grid">
                  <div v-for="(detection, index) in selectedNotification.details.detections" :key="index"
                    class="detection-item" :class="{ 'high-confidence': detection.confidence > 0.8 }">
                    <span class="detection-class">{{ detection.class }}</span>
                    <span class="confidence-badge"
                      :style="{ backgroundColor: getConfidenceColor(detection.confidence) }">
                      {{ formatConfidence(detection.confidence) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedNotification.event_type === 'audio_detection'" class="type-details audio-details">
              <h3>Audio Detection</h3>

              <div v-if="selectedNotification.details?.keyword" class="keyword-section">
                <h4>Flagged Keyword</h4>
                <div class="keyword-tag">{{ selectedNotification.details.keyword }}</div>
              </div>

              <div v-if="selectedNotification.details?.transcript" class="transcript-section">
                <h4>Transcript</h4>
                <div class="transcript-text">
                  {{ selectedNotification.details.transcript }}
                </div>
              </div>

              <div v-if="selectedNotification.details?.sentiment_score" class="sentiment-section">
                <h4>Sentiment Analysis</h4>
                <div class="sentiment-indicator"
                  :class="getSentimentClass(selectedNotification.details.sentiment_score)">
                  {{ formatSentiment(selectedNotification.details.sentiment_score) }}
                </div>
              </div>
            </div>

            <div v-if="selectedNotification.event_type === 'chat_detection'" class="type-details chat-details">
              <h3>Chat Detection</h3>

              <div v-if="selectedNotification.details?.keywords?.length" class="keyword-section">
                <h4>Flagged Keywords</h4>
                <div class="keywords-list">
                  <span v-for="(keyword, index) in selectedNotification.details.keywords" :key="index"
                    class="keyword-tag">
                    {{ keyword }}
                  </span>
                </div>
              </div>

              <div class="message-section">
                <h4>Chat Message</h4>
                <div class="chat-message">
                  <div v-if="selectedNotification.details?.sender" class="message-sender">
                    From: {{ selectedNotification.details.sender }}
                  </div>
                  <div class="message-text">
                    {{ selectedNotification.details?.message || 'No message content' }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedNotification.event_type === 'stream_created'" class="type-details stream-details">
              <h3>Stream Created</h3>

              <div class="stream-info">
                <p>A new stream has been created and assigned to you.</p>
                <button class="action-btn view-stream-btn" @click="viewStreamDetails(selectedNotification)">
                  View Stream Details
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <div v-if="isDeleteModalOpen" class="modal-overlay" @click="isDeleteModalOpen = false">
        <div class="modal-container delete-modal" @click.stop>
          <div class="modal-header">
            <h3>Confirm Deletion</h3>
            <button class="close-btn" @click="isDeleteModalOpen = false">&times;</button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete {{ selectedNotification ? 'this notification' : 'all notifications' }}?
            </p>
            <p class="warning">This action cannot be undone.</p>
          </div>
          <div class="modal-footer">
            <button class="cancel-btn" @click="isDeleteModalOpen = false">Cancel</button>
            <button class="confirm-btn"
              @click="selectedNotification ? deleteNotification(selectedNotification.id) : deleteAllNotifications()">
              Delete
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Image viewer modal -->
    <Teleport to="body">
      <div v-if="imageModalSrc" class="modal-overlay" @click="imageModalSrc = null">
        <div class="image-modal" @click.stop>
          <button class="close-btn" @click="imageModalSrc = null">&times;</button>
          <img :src="imageModalSrc" alt="Full size image" />
        </div>
      </div>
    </Teleport>

    <!-- Toast notifications -->
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div v-for="toast in toasts" :key="toast.id" class="toast" :class="toast.type">
          {{ toast.message }}
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch, defineProps, defineEmits } from 'vue';
import axios from 'axios';
import anime from 'animejs/lib/anime.es.js';
import { io } from 'socket.io-client';
import { formatDistanceToNow, parseISO } from 'date-fns';

// Props
const props = defineProps({
  user: {
    type: Object,
    default: null
  },
  ongoingStreams: {
    type: Array,
    default: () => []
  }
});

// Emits
const emit = defineEmits(['view-stream']);

// State
const notifications = ref([]);
const filteredNotifications = ref([]);
const selectedNotification = ref(null);
const loading = ref(true);
const error = ref(null);
const mainFilter = ref('All');
const detectionSubFilter = ref('Visual');
const isMenuOpen = ref(false);
const isDeleteModalOpen = ref(false);
const isDarkMode = ref(localStorage.getItem('darkMode') === 'true');
const soundEnabled = ref(localStorage.getItem('notificationSound') !== 'false');
const isMobile = ref(window.innerWidth < 768);
const imageModalSrc = ref(null);
const newNotificationIds = ref([]);
const toasts = ref([]);
const socket = ref(null);
let toastCounter = 0;

// Computed
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length;
});

const assignedToMe = computed(() => {
  if (!selectedNotification.value || !props.user) return false;

  const assignedAgent = selectedNotification.value.assigned_agent;
  return assignedAgent === props.user.username;
});

// Methods
const fetchNotifications = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await axios.get('/api/notifications');
    notifications.value = response.data;
    applyFilters();
    loading.value = false;
  } catch (err) {
    console.error('Error fetching notifications:', err);
    error.value = 'Failed to load notifications. Please try again.';
    loading.value = false;
  }
};

const applyFilters = () => {
  let filtered = [...notifications.value];

  // Apply main filter
  if (mainFilter.value === 'Unread') {
    filtered = filtered.filter(n => !n.read);
  } else if (mainFilter.value === 'Detections') {
    filtered = filtered.filter(n => {
      // Apply detection sub-filter
      if (detectionSubFilter.value === 'Visual') {
        return n.event_type === 'object_detection';
      } else if (detectionSubFilter.value === 'Audio') {
        return n.event_type === 'audio_detection';
      } else if (detectionSubFilter.value === 'Chat') {
        return n.event_type === 'chat_detection';
      }
      return false;
    });
  }

  filteredNotifications.value = filtered;
};

const handleMainFilterChange = (filter) => {
  mainFilter.value = filter;
  applyFilters();

  // Deselect notification when changing filters
  if (selectedNotification.value) {
    selectedNotification.value = null;
  }
};

const getNotificationColor = (notification) => {
  if (notification.event_type === 'object_detection') {
    return '#e74c3c'; // Red
  } else if (notification.event_type === 'audio_detection') {
    return '#3498db'; // Blue
  } else if (notification.event_type === 'chat_detection') {
    return '#f39c12'; // Orange
  } else if (notification.event_type === 'stream_created') {
    return '#2ecc71'; // Green
  }
  return '#95a5a6'; // Gray for others
};

const getNotificationType = (notification) => {
  if (notification.event_type === 'object_detection') {
    return 'Visual';
  } else if (notification.event_type === 'audio_detection') {
    return 'Audio';
  } else if (notification.event_type === 'chat_detection') {
    return 'Chat';
  } else if (notification.event_type === 'stream_created') {
    return 'Stream';
  }
  return 'General';
};

const getNotificationMessage = (notification) => {
  if (notification.event_type === 'object_detection') {
    const detections = notification.details?.detections || [];
    if (detections.length > 0) {
      return `Detected: ${detections.map(d => d.class).join(', ')}`;
    }
    return 'Object detected';
  } else if (notification.event_type === 'audio_detection') {
    return notification.details?.transcript?.substring(0, 100) || 'Audio detected';
  } else if (notification.event_type === 'chat_detection') {
    return notification.details?.message?.substring(0, 100) || 'Chat message detected';
  } else if (notification.event_type === 'stream_created') {
    return `New stream: ${notification.details?.streamer_name || 'Unknown streamer'}`;
  }
  return notification.details?.message || 'Notification received';
};

const getNotificationDetailTitle = () => {
  if (!selectedNotification.value) return '';

  if (selectedNotification.value.event_type === 'object_detection') {
    return 'Visual Detection';
  } else if (selectedNotification.value.event_type === 'audio_detection') {
    return 'Audio Detection';
  } else if (selectedNotification.value.event_type === 'chat_detection') {
    return 'Chat Detection';
  } else if (selectedNotification.value.event_type === 'stream_created') {
    return 'New Stream Assignment';
  }
  return 'Notification Details';
};

const formatTimestamp = (timestamp, detailed = false) => {
  if (!timestamp) return 'Unknown';

  try {
    const date = parseISO(timestamp);

    if (detailed) {
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).format(date);
    }

    return formatDistanceToNow(date, { addSuffix: true });
  } catch (err) {
    console.error('Error formatting timestamp:', err);
    return 'Invalid date';
  }
};

const formatImage = (image) => {
  if (!image) return '';

  // Check if it's already a valid URL
  if (image.startsWith('http') || image.startsWith('data:')) {
    return image;
  }

  // Otherwise assume it's a base64 string
  return `data:image/jpeg;base64,${image}`;
};

const formatConfidence = (confidence) => {
  if (typeof confidence !== 'number') return 'N/A';
  return `${Math.round(confidence * 100)}%`;
};

const getConfidenceColor = (confidence) => {
  if (confidence > 0.8) return '#2ecc71'; // Green
  if (confidence > 0.6) return '#f39c12'; // Orange
  return '#e74c3c'; // Red
};

const formatSentiment = (score) => {
  if (typeof score !== 'number') return 'Unknown';

  if (score < -0.5) return 'Very Negative';
  if (score < -0.2) return 'Negative';
  if (score < 0.2) return 'Neutral';
  if (score < 0.5) return 'Positive';
  return 'Very Positive';
};

const getSentimentClass = (score) => {
  if (typeof score !== 'number') return 'neutral';

  if (score < -0.5) return 'very-negative';
  if (score < -0.2) return 'negative';
  if (score < 0.2) return 'neutral';
  if (score < 0.5) return 'positive';
  return 'very-positive';
};

const truncateUrl = (url) => {
  if (!url) return '';
  return url.length > 40 ? url.substring(0, 37) + '...' : url;
};

const handleNotificationClick = (notification) => {
  selectedNotification.value = notification;

  // On mobile, scroll to details
  if (isMobile.value) {
    nextTick(() => {
      const detailsPanel = document.querySelector('.details-panel');
      if (detailsPanel) {
        detailsPanel.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }

  // Animate the selection
  setTimeout(() => {
    const selectedCard = document.querySelector('.notification-card.selected');
    if (selectedCard) {
      anime({
        targets: selectedCard,
        scale: [1, 1.02, 1],
        duration: 300,
        easing: 'easeOutQuad'
      });
    }
  }, 10);
};

const markAsRead = async (id) => {
  try {
    await axios.put(`/api/notifications/${id}/read`);

    // Update local state
    const notification = notifications.value.find(n => n.id === id);
    if (notification) {
      notification.read = true;
      applyFilters();
    }

    showToast('Notification marked as read', 'success');
  } catch (err) {
    console.error('Error marking notification as read:', err);
    showToast('Failed to mark notification as read', 'error');
  }
};

const markAllAsRead = async () => {
  try {
    await axios.put('/api/notifications/read-all');

    // Update local state
    notifications.value.forEach(notification => {
      notification.read = true;
    });
    applyFilters();

    showToast('All notifications marked as read', 'success');
    isMenuOpen.value = false;
  } catch (err) {
    console.error('Error marking all notifications as read:', err);
    showToast('Failed to mark all notifications as read', 'error');
  }
};

const deleteNotification = async (id) => {
  try {
    await axios.delete(`/api/notifications/${id}`);

    // Update local state
    notifications.value = notifications.value.filter(n => n.id !== id);
    applyFilters();

    // Reset selected notification if it's the one being deleted
    if (selectedNotification.value && selectedNotification.value.id === id) {
      selectedNotification.value = null;
    }

    isDeleteModalOpen.value = false;
    showToast('Notification deleted', 'success');
  } catch (err) {
    console.error('Error deleting notification:', err);
    showToast('Failed to delete notification', 'error');
    isDeleteModalOpen.value = false;
  }
};

const deleteAllNotifications = async () => {
  try {
    await axios.delete('/api/notifications');

    // Update local state
    notifications.value = [];
    filteredNotifications.value = [];
    selectedNotification.value = null;

    isDeleteModalOpen.value = false;
    isMenuOpen.value = false;
    showToast('All notifications deleted', 'success');
  } catch (err) {
    console.error('Error deleting all notifications:', err);
    showToast('Failed to delete notifications', 'error');
    isDeleteModalOpen.value = false;
  }
};

const viewStreamDetails = (notification) => {
  // Find the stream in ongoingStreams that matches the notification
  const stream = props.ongoingStreams.find(s => {
    return s.room_url === notification.room_url ||
      s.streamer_name === notification.details?.streamer_name;
  });

  if (stream) {
    emit('view-stream', stream);
    showToast('Opening stream details', 'info');
  } else {
    showToast('Stream not found in your assignments', 'error');
  }
};

const openImageModal = (image) => {
  imageModalSrc.value = formatImage(image);
};

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value;
  localStorage.setItem('darkMode', isDarkMode.value);
};

const toggleSound = () => {
  soundEnabled.value = !soundEnabled.value;
  localStorage.setItem('notificationSound', soundEnabled.value);
  showToast(`Sound ${soundEnabled.value ? 'enabled' : 'disabled'}`, 'info');
  isMenuOpen.value = false;
};

const showToast = (message, type = 'info') => {
  const id = toastCounter++;
  toasts.value.push({ id, message, type });

  // Auto remove after 3 seconds
  setTimeout(() => {
    toasts.value = toasts.value.filter(toast => toast.id !== id);
  }, 3000);
};

const setupSocketConnection = () => {
  // Connect to socket server with namespace
  socket.value = io('     https://monitor-backend.jetcamstudio.com:5000notifications', {
    path: '/ws',
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    withCredentials: true,
    autoConnect: true
  });

  // Socket event handlers
  socket.value.on('connect', () => {
    console.log('Connected to notification server');
    showToast('Connected to notification server', 'success');
  });

  socket.value.on('connect_error', (error) => {
    console.error('Socket connection error:', error);
  });

  socket.value.on('disconnect', () => {
    console.log('Disconnected from notification server');
  });

  // Handle new notifications
  socket.value.on('notification', (data) => {
    console.log('New notification received:', data);

    // Add to local state if not already present
    if (!notifications.value.some(n => n.id === data.id)) {
      notifications.value.unshift(data);
      newNotificationIds.value.push(data.id);
      applyFilters();

      // Remove from newNotificationIds after animation completes
      setTimeout(() => {
        newNotificationIds.value = newNotificationIds.value.filter(id => id !== data.id);
      }, 5000);

      // Play sound if enabled
      if (soundEnabled.value) {
        playNotificationSound();
      }

      showToast('New notification received', 'info');
    }
  });

  // Handle notification updates (read status, etc.)
  socket.value.on('notification_update', (data) => {
    console.log('Notification update received:', data);

    const { id, type } = data;

    // Update local state
    if (type === 'read') {
      const notification = notifications.value.find(n => n.id === id);
      if (notification) {
        notification.read = true;
        applyFilters();
      }
    } else if (type === 'deleted') {
      notifications.value = notifications.value.filter(n => n.id !== id);
      applyFilters();

      // Reset selected notification if it's the one being deleted
      if (selectedNotification.value && selectedNotification.value.id === id) {
        selectedNotification.value = null;
      }
    }
  });
};

const playNotificationSound = () => {
  const audio = new Audio('/notification.mp3');
  audio.play().catch(err => console.error('Error playing notification sound:', err));
};

const handleResize = () => {
  isMobile.value = window.innerWidth < 768;
};

// Watch for filter changes
watch([mainFilter, detectionSubFilter], () => {
  applyFilters();
});

// Lifecycle hooks
onMounted(() => {
  fetchNotifications();
  setupSocketConnection();

  window.addEventListener('resize', handleResize);

  // Animation for initial load
  nextTick(() => {
    anime({
      targets: '.notification-card',
      translateY: [20, 0],
      opacity: [0, 1],
      delay: anime.stagger(50),
      easing: 'easeOutQuad'
    });
  });
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.disconnect();
  }

  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.notifications-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f8f9fa;
  color: #333;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Dark Mode */
.dark-mode {
  background-color: #121212;
  color: #e4e4e4;
}

.dark-mode .top-bar,
.dark-mode .sub-filters,
.dark-mode .notifications-panel,
.dark-mode .details-panel,
.dark-mode .modal-container {
  background-color: #1e1e1e;
  border-color: #333;
}

.dark-mode .dropdown-menu {
  background-color: #2a2a2a;
  border-color: #444;
}

.dark-mode .notification-card {
  background-color: #2a2a2a;
  border-color: #444;
}

.dark-mode .notification-card.selected {
  background-color: #333;
}

.dark-mode .notification-card.unread {
  background-color: #252835;
}

.dark-mode .notification-card:hover {
  background-color: #333;
}

.dark-mode .empty-state,
.dark-mode .empty-detail,
.dark-mode .error-state,
.dark-mode .state-container {
  background-color: #2a2a2a;
  color: #ccc;
}

.dark-mode .detection-item,
.dark-mode .keyword-tag {
  background-color: #333;
}

.dark-mode a {
  color: #4dabf7;
}

.dark-mode .modal-overlay {
  background-color: rgba(0, 0, 0, 0.7);
}

/* Top Navigation Bar */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background-color: #fff;
  border-bottom: 1px solid #e1e4e8;
  z-index: 10;
  position: relative;
}

.filter-tabs {
  display: flex;
  gap: 8px;
}

.tab-btn {
  padding: 6px 12px;
  border: none;
  background: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: #555;
  transition: all 0.2s ease;
  position: relative;
}

.tab-btn:hover {
  background-color: #f0f0f0;
}

.tab-btn.active {
  background-color: #ebf5fe;
  color: #0366d6;
}

.dark-mode .tab-btn:hover {
  background-color: #333;
}

.dark-mode .tab-btn.active {
  background-color: #1a365d;
  color: #4dabf7;
}

.badge {
  position: absolute;
  top: -6px;
  right: -8px;
  background-color: #e74c3c;
  color: white;
  border-radius: 12px;
  padding: 0 6px;
  font-size: 12px;
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background-color: #f0f0f0;
}

.dark-mode .icon-btn:hover {
  background-color: #333;
}

.icon {
  font-size: 18px;
}

.dropdown-menu {
  position: absolute;
  right: 20px;
  top: 60px;
  background-color: white;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 180px;
  z-index: 20;
}

.dropdown-menu button {
  display: block;
  width: 100%;
  text-align: left;
  padding: 10px 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

.dropdown-menu button:hover {
  background-color: #f6f8fa;
}

.dropdown-menu button:disabled {
  color: #a0a0a0;
  cursor: not-allowed;
}

.dark-mode .dropdown-menu button:hover {
  background-color: #333;
}

/* Sub-filters */
.sub-filters {
  display: flex;
  padding: 8px 20px;
  background-color: #fff;
  border-bottom: 1px solid #e1e4e8;
  gap: 8px;
}

.sub-filter-btn {
  padding: 4px 10px;
  border: 1px solid #e1e4e8;
  background: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sub-filter-btn:hover {
  background-color: #f6f8fa;
}

.sub-filter-btn.active {
  background-color: #0366d6;
  color: white;
  border-color: #0366d6;
}

.dark-mode .sub-filter-btn {
  border-color: #444;
}

.dark-mode .sub-filter-btn:hover {
  background-color: #333;
}

.dark-mode .sub-filter-btn.active {
  background-color: #1a365d;
  border-color: #1a365d;
}

/* Content Area */
.content-area {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.notifications-panel {
  width: 40%;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e1e4e8;
  background-color: #fff;
  position: relative;
}

.details-panel {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #fff;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e1e4e8;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.panel-header .count {
  color: #888;
  margin-left: 4px;
  font-weight: normal;
}

/* Notifications List */
.notification-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.notification-card {
  display: flex;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background-color: #fff;
  border: 1px solid #e1e4e8;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.notification-card:hover {
  background-color: #f6f8fa;
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.notification-card.selected {
  background-color: #f0f6ff;
  border-color: #79b8ff;
}

.notification-card.unread {
  background-color: #f0f7ff;
  border-left-width: 3px;
}

.notification-card.read {
  opacity: 0.8;
}

.dark-mode .notification-card.selected {
  background-color: #1a365d;
  border-color: #4dabf7;
}

.notification-indicator {
  width: 4px;
  border-radius: 2px;
  margin-right: 12px;
  background-color: #0366d6;
}

.notification-content {
  flex: 1;
  min-width: 0;
  /* For proper text truncation */
}

.notification-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.notification-type {
  font-size: 12px;
  font-weight: 600;
  color: #0366d6;
}

.notification-time {
  font-size: 12px;
  color: #888;
}

.notification-message {
  font-size: 14px;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notification-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #888;
}

.notification-source {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-confidence {
  color: #2ecc71;
  font-weight: 500;
}

.notification-actions {
  display: none;
  position: absolute;
  right: 8px;
  top: 8px;
}

.notification-card:hover .notification-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: none;
  background-color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background-color: #f0f0f0;
}

.action-btn.read-btn:hover {
  background-color: #d4edda;
  color: #28a745;
}

.action-btn.delete-btn:hover {
  background-color: #f8d7da;
  color: #dc3545;
}

.dark-mode .action-btn {
  background-color: rgba(30, 30, 30, 0.8);
}

.dark-mode .action-btn:hover {
  background-color: #333;
}

.dark-mode .action-btn.read-btn:hover {
  background-color: #1e4620;
  color: #4ade80;
}

.dark-mode .action-btn.delete-btn:hover {
  background-color: #4c1d24;
  color: #f87171;
}

/* New notification animation */
.notification-card.new-notification {
  animation: pulse 2s ease-in-out;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(66, 153, 225, 0.5);
  }

  70% {
    box-shadow: 0 0 0 10px rgba(66, 153, 225, 0);
  }

  100% {
    box-shadow: 0 0 0 0 rgba(66, 153, 225, 0);
  }
}

/* Empty/Error States */
.state-container,
.empty-state,
.empty-detail,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  height: 100%;
  color: #888;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.error-state {
  color: #dc3545;
}

.error-state button {
  margin-top: 12px;
  padding: 6px 12px;
  background-color: #f8d7da;
  color: #dc3545;
  border: 1px solid #dc3545;
  border-radius: 4px;
  cursor: pointer;
}

.dark-mode .error-state button {
  background-color: #4c1d24;
  color: #f87171;
  border-color: #f87171;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: #0366d6;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 12px;
}

.dark-mode .loading-spinner {
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #4dabf7;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Detail Section */
.detail-content {
  padding: 20px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #e1e4e8;
  padding-bottom: 12px;
}

.detail-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.detail-header .back-btn {
  padding: 6px 12px;
  background: none;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-right: 12px;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.detail-actions button {
  padding: 6px 12px;
  background: none;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.detail-actions button:hover {
  background-color: #f6f8fa;
}

.detail-actions .delete-btn {
  color: #dc3545;
  border-color: #dc3545;
}

.detail-actions .delete-btn:hover {
  background-color: #f8d7da;
}

.detail-actions .view-stream-btn {
  color: #0366d6;
  border-color: #0366d6;
}

.detail-actions .view-stream-btn:hover {
  background-color: #f0f7ff;
}

.dark-mode .detail-header .back-btn,
.dark-mode .detail-actions button {
  border-color: #444;
}

.dark-mode .detail-actions button:hover {
  background-color: #333;
}

.dark-mode .detail-actions .delete-btn {
  color: #f87171;
  border-color: #f87171;
}

.dark-mode .detail-actions .delete-btn:hover {
  background-color: #4c1d24;
}

.dark-mode .detail-actions .view-stream-btn {
  color: #4dabf7;
  border-color: #4dabf7;
}

.dark-mode .detail-actions .view-stream-btn:hover {
  background-color: #1a365d;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-field {
  display: flex;
  margin-bottom: 8px;
}

.detail-field label {
  width: 100px;
  font-weight: 500;
  color: #666;
}

.dark-mode .detail-field label {
  color: #aaa;
}

.url-link {
  color: #0366d6;
  text-decoration: none;
}

.url-link:hover {
  text-decoration: underline;
}

.assigned-badge {
  display: inline-block;
  padding: 2px 6px;
  background-color: #d4edda;
  color: #28a745;
  border-radius: 4px;
  font-size: 12px;
  margin-left: 8px;
}

.dark-mode .assigned-badge {
  background-color: #1e4620;
  color: #4ade80;
}

/* Type-specific content */
.type-details {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e1e4e8;
}

.type-details h3 {
  font-size: 16px;
  font-weight: 600;
  margin-top: 0;
  margin-bottom: 16px;
}

.type-details h4 {
  font-size: 14px;
  font-weight: 500;
  margin-top: 16px;
  margin-bottom: 8px;
  color: #666;
}

.dark-mode .type-details h4 {
  color: #aaa;
}

/* Detection type content */
.detection-images {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
}

.image-container {
  flex: 1;
  min-width: 200px;
  max-width: 100%;
}

.detection-image {
  width: 100%;
  border-radius: 6px;
  cursor: zoom-in;
  transition: transform 0.2s ease;
}

.detection-image:hover {
  transform: scale(1.02);
}

.detections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
  margin-top: 8px;
}

.detection-item {
  padding: 8px;
  border-radius: 4px;
  background-color: #f6f8fa;
  font-size: 13px;
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
}

.detection-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.detection-item.high-confidence {
  border-left: 3px solid #2ecc71;
}

.detection-class {
  font-weight: 500;
}

.confidence-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 12px;
  color: white;
  font-size: 12px;
  margin-top: 4px;
  align-self: flex-start;
}

/* Audio type content */
.transcript-text {
  background-color: #f6f8fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
}

.dark-mode .transcript-text {
  background-color: #2a2a2a;
}

.keyword-tag {
  display: inline-block;
  padding: 4px 8px;
  background-color: #e1e4e8;
  border-radius: 12px;
  font-size: 12px;
  margin-right: 6px;
  margin-bottom: 6px;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sentiment-indicator {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
}

.sentiment-indicator.very-negative {
  background-color: #fee2e2;
  color: #ef4444;
}

.sentiment-indicator.negative {
  background-color: #fecaca;
  color: #dc2626;
}

.sentiment-indicator.neutral {
  background-color: #e5e7eb;
  color: #6b7280;
}

.sentiment-indicator.positive {
  background-color: #d1fae5;
  color: #10b981;
}

.sentiment-indicator.very-positive {
  background-color: #a7f3d0;
  color: #059669;
}

.dark-mode .sentiment-indicator.very-negative {
  background-color: #7f1d1d;
  color: #fca5a5;
}

.dark-mode .sentiment-indicator.negative {
  background-color: #991b1b;
  color: #fca5a5;
}

.dark-mode .sentiment-indicator.neutral {
  background-color: #4b5563;
  color: #e5e7eb;
}

.dark-mode .sentiment-indicator.positive {
  background-color: #065f46;
  color: #a7f3d0;
}

.dark-mode .sentiment-indicator.very-positive {
  background-color: #064e3b;
  color: #a7f3d0;
}

/* Chat type content */
.chat-message {
  background-color: #f6f8fa;
  padding: 12px;
  border-radius: 4px;
  margin-top: 8px;
}

.message-sender {
  font-weight: 500;
  margin-bottom: 8px;
  color: #555;
}

.message-text {
  font-size: 14px;
  line-height: 1.5;
}

.dark-mode .chat-message {
  background-color: #2a2a2a;
}

.dark-mode .message-sender {
  color: #aaa;
}

/* Modals */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  width: 400px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e1e4e8;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e1e4e8;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
}

.cancel-btn,
.confirm-btn {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  border: 1px solid #e1e4e8;
}

.cancel-btn {
  background-color: white;
}

.confirm-btn {
  background-color: #0366d6;
  color: white;
  border-color: #0366d6;
}

.delete-modal .confirm-btn {
  background-color: #dc3545;
  border-color: #dc3545;
}

.warning {
  color: #dc3545;
  font-weight: 500;
}

.dark-mode .modal-container {
  background-color: #1e1e1e;
}

.dark-mode .cancel-btn {
  background-color: #2a2a2a;
}

.dark-mode .confirm-btn {
  background-color: #0f4c81;
}

.dark-mode .delete-modal .confirm-btn {
  background-color: #a02f3e;
}

/* Image modal */
.image-modal {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-modal img {
  max-width: 100%;
  max-height: 90vh;
  border-radius: 4px;
}

.image-modal .close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Toast notifications */
.toast-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toast {
  padding: 12px 16px;
  border-radius: 4px;
  color: white;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  min-width: 250px;
}

.toast.success {
  background-color: #2ecc71;
}

.toast.error {
  background-color: #e74c3c;
}

.toast.info {
  background-color: #3498db;
}

.toast.warning {
  background-color: #f39c12;
}

/* Animations */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(50px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(50px);
}

/* Responsive Design */
@media (max-width: 768px) {
  .content-area {
    flex-direction: column;
  }

  .notifications-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e1e4e8;
    max-height: 50vh;
  }

  .detail-actions {
    flex-wrap: wrap;
  }

  .top-bar {
    flex-wrap: wrap;
  }

  .filter-tabs {
    width: 100%;
    margin-bottom: 8px;
    justify-content: space-between;
  }

  .action-buttons {
    margin-left: auto;
  }

  .notification-card {
    padding: 8px;
  }

  .notification-message {
    font-size: 13px;
  }

  .notification-meta,
  .notification-time {
    font-size: 11px;
  }

  .detection-images {
    flex-direction: column;
  }
}
</style>