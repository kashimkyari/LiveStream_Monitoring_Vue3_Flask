<template>
  <div class="notifications-page">
    <div class="notifications-controls" ref="notificationsControls">
      <div class="main-filter-controls">
        <button 
          v-for="tab in ['All', 'Unread', 'Detections']" 
          :key="tab"
          class="filter-btn"
          :class="{ active: mainFilter === tab }"
          @click="handleMainFilterChange(tab)"
        >
          {{ tab }}
        </button>
      </div>
      <div v-if="mainFilter === 'Detections'" class="sub-filter-controls">
        <button 
          v-for="subTab in ['Visual', 'Audio', 'Chat']" 
          :key="subTab"
          class="sub-filter-btn"
          :class="{ active: detectionSubFilter === subTab }"
          @click="detectionSubFilter = subTab"
        >
          {{ subTab }}
        </button>
      </div>
      <div class="action-controls">
        <button 
          class="mark-all-read"
          @click="markAllAsRead"
          :disabled="notifications.filter(n => !n.read).length === 0"
        >
          Mark All as Read
        </button>
        <button 
          class="delete-all"
          @click="deleteAllNotifications"
          :disabled="notifications.length === 0"
        >
          Delete All
        </button>
        <button class="refresh-notifications" @click="fetchNotifications">
          Refresh Notifications
        </button>
      </div>
    </div>
    <div class="notifications-container" ref="notificationsContainer">
      <div class="notifications-list-container">
        <h3>Notifications ({{ notifications.length }})</h3>
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading notifications...</p>
        </div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else-if="notifications.length === 0" class="empty-state">
          <div class="empty-icon">🔔</div>
          <p>No notifications to display</p>
        </div>
        <div v-else class="notifications-list" ref="notificationsList">
          <div 
            v-for="notification in notifications" 
            :key="notification.id"
            class="notification-item"
            :class="{ 
              'read': notification.read, 
              'unread': !notification.read, 
              'selected': selectedNotification && selectedNotification.id === notification.id 
            }"
            @click="handleNotificationClick(notification)"
            ref="notificationItems"
          >
            <div 
              class="notification-indicator"
              :style="{
                backgroundColor: getNotificationColor(notification)
              }"
            ></div>
            <div class="notification-content">
              <div class="notification-message">
                {{ getNotificationMessage(notification) }}
              </div>
              <div class="notification-meta">
                <span class="notification-time">
                  {{ formatTimestamp(notification.timestamp) }}
                </span>
                <span 
                  v-if="notification.event_type === 'object_detection' && 
                       notification.details && 
                       notification.details.detections && 
                       notification.details.detections.length > 0" 
                  class="notification-confidence"
                >
                  {{ formatConfidence(notification.details.detections[0].confidence) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="notification-detail-container" ref="detailContainer">
        <div v-if="!selectedNotification" class="empty-detail">
          <div class="empty-icon">📋</div>
          <p>Select a notification to view details</p>
        </div>
        
        <div v-else class="notification-detail">
          <div class="detail-header">
            <h3>{{ getNotificationDetailTitle() }}</h3>
            <div class="detail-actions">
              <button 
                v-if="!selectedNotification.read" 
                class="mark-read-btn" 
                @click="markAsRead(selectedNotification.id)"
              >
                Mark as Read
              </button>
              <div v-if="user && user.role === 'admin'" class="forward-section">
                <button class="forward-btn" @click="isAgentDropdownOpen = true">
                  Forward to Agent
                </button>
                
                <TransitionRoot appear :show="isAgentDropdownOpen" as="template">
                  <Dialog as="div" @close="isAgentDropdownOpen = false" class="agent-dropdown-dialog">
                    <div class="forward-modal-overlay">
                      <TransitionChild
                        as="template"
                        enter="duration-300 ease-out"
                        enter-from="opacity-0"
                        enter-to="opacity-100"
                        leave="duration-200 ease-in"
                        leave-from="opacity-100"
                        leave-to="opacity-0"
                      >
                        <DialogOverlay class="fixed inset-0 bg-black bg-opacity-30" />
                      </TransitionChild>
                      
                      <TransitionChild
                        as="template"
                        enter="duration-300 ease-out"
                        enter-from="scale-95 opacity-0"
                        enter-to="scale-100 opacity-100"
                        leave="duration-200 ease-in"
                        leave-from="scale-100 opacity-100"
                        leave-to="scale-95 opacity-0"
                      >
                        <div class="forward-modal-content">
                          <DialogTitle as="h3" class="modal-header">
                            Select Agent
                            <button class="modal-close-btn" @click="isAgentDropdownOpen = false">
                              &times;
                            </button>
                          </DialogTitle>
                          <div class="agent-list">
                            <div 
                              v-for="agent in agents" 
                              :key="agent.id" 
                              class="agent-option"
                              @click="forwardNotification(agent.id)"
                            >
                              <div :class="['agent-status-indicator', agent.online ? 'online' : 'offline']"></div>
                              <div class="agent-info">
                                <div class="agent-name">{{ agent.username }}</div>
                                <div class="agent-email">{{ agent.email }}</div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </TransitionChild>
                    </div>
                  </Dialog>
                </TransitionRoot>
              </div>
              <button class="delete-btn" @click="deleteNotification(selectedNotification.id)">
                Delete
              </button>
            </div>
          </div>
          
          <div class="detail-timestamp">
            Detected at: {{ formatTimestamp(selectedNotification.timestamp) }}
          </div>
          
          <!-- Audio detection details -->
          <div v-if="selectedNotification.event_type === 'audio_detection'" class="audio-detection-content">
            <p>Detected keywords: <strong>{{ selectedNotification.details?.keywords?.join(', ') }}</strong></p>
            <p>Transcript: {{ selectedNotification.details?.transcript }}</p>
          </div>
          
          <!-- Visual detection details -->
          <div v-else-if="selectedNotification.event_type === 'object_detection'" class="detection-content">
            <div class="image-gallery">
              <div v-if="selectedNotification.details?.annotated_image" class="image-card" ref="imageCard">
                <img
                  :src="formatImage(selectedNotification.details.annotated_image)"
                  alt="Annotated Detection"
                  class="detection-image"
                  @load="animateImageLoad"
                />
                <div class="image-label">Annotated Image</div>
              </div>
              <div v-if="selectedNotification.details?.captured_image" class="image-card" ref="imageCard">
                <img
                  :src="formatImage(selectedNotification.details.captured_image)"
                  alt="Captured Image"
                  class="detection-image"
                  @load="animateImageLoad"
                />
                <div class="image-label">Captured Image</div>
              </div>
            </div>
            <div class="streamer-info-card" ref="streamerInfoCard">
              <h4>Streamer Info</h4>
              <div class="info-item">
                <span class="info-label">Streamer:</span>
                <span class="info-value">{{ selectedNotification.details?.streamer_name }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">Assigned Agent:</span>
                <span class="info-value">
                  <template v-if="assignedAgent !== 'Unassigned'">
                    {{ assignedAgent }}
                  </template>
                  <span v-else class="unassigned-badge">⚠️ UNASSIGNED</span>
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">Platform:</span>
                <span class="info-value">{{ selectedNotification.details?.platform }}</span>
              </div>
            </div>
            <div class="detected-objects" ref="detectedObjects">
              <h4>Detected Objects</h4>
              <div 
                v-for="(detection, index) in selectedNotification.details?.detections" 
                :key="index" 
                class="detection-item"
                ref="detectionItems"
              >
                <span class="detection-class">{{ detection.class }}</span>
                <span 
                  class="confidence-badge"
                  :style="{ backgroundColor: getConfidenceColor(detection.confidence) }"
                >
                  {{ formatConfidence(detection.confidence) }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- Chat detection details -->
          <div v-else-if="selectedNotification.event_type === 'chat_detection'" class="chat-detection-content">
            <p>Detected chat keyword: <strong>{{ selectedNotification.details?.keyword }}</strong></p>
            <p class="chat-excerpt">{{ selectedNotification.details?.ocr_text }}</p>
          </div>
          
          <!-- Stream created details -->
          <div v-else-if="selectedNotification.event_type === 'stream_created'" class="stream-created-content">
            <p>A new stream has been created by <strong>{{ selectedNotification.details?.streamer_name || 'Unknown' }}</strong>.</p>
            <p v-if="selectedNotification.details?.stream_url">
              Stream URL: <a :href="selectedNotification.details.stream_url" target="_blank" rel="noopener noreferrer">
                {{ selectedNotification.details.stream_url }}
              </a>
            </p>
          </div>
          
          <!-- Default details -->
          <p v-else>{{ selectedNotification.message }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import axios from 'axios';
import anime from 'animejs/lib/anime.es.js';
import { io } from 'socket.io-client';
import { Dialog, DialogOverlay, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue';
import { useToast } from 'vue-toastification';

// Props
// eslint-disable-next-line
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

// Toast notifications
const toast = useToast();

// State
const notifications = ref([]);
const loading = ref(true);
const error = ref(null);
const mainFilter = ref('All');
const detectionSubFilter = ref('Visual');
const selectedNotification = ref(null);
const agents = ref([]);
const dashboardStreams = ref([]);
const isAgentDropdownOpen = ref(false);
const socket = ref(null);

// DOM refs
const notificationsControls = ref(null);
const notificationsContainer = ref(null);
const notificationsList = ref(null);
const notificationItems = ref([]);
const detailContainer = ref(null);
const streamerInfoCard = ref(null);
const detectedObjects = ref(null);
const detectionItems = ref([]);
const imageCard = ref(null);

// Computed
const assignedAgent = computed(() => {
  if (dashboardStreams.value && dashboardStreams.value.length > 0 && 
      selectedNotification.value && selectedNotification.value.details &&
      selectedNotification.value.details.stream) {
    const { platform, streamer } = selectedNotification.value.details.stream;
    const matchedStream = dashboardStreams.value.find(s =>
      s.platform.toLowerCase() === platform.toLowerCase() &&
      s.streamer_username.toLowerCase() === streamer.toLowerCase()
    );
    
    if (matchedStream && matchedStream.assignments && 
        matchedStream.assignments.length > 0 && matchedStream.assignments[0].agent) {
      const agentId = matchedStream.assignments[0].agent.id;
      const foundAgent = agents.value.find(a => a.id === agentId);
      if (foundAgent) return foundAgent.username;
      return matchedStream.assignments[0].agent.username || "Unassigned";
    }
  }
  return "Unassigned";
});

// Socket configuration
const SOCKET_SERVER_URL = 'http://54.86.99.85:5000';
axios.defaults.withCredentials = true;

// Socket connection
onMounted(() => {
  socket.value = io(SOCKET_SERVER_URL, { withCredentials: true });
  socket.value.on('notification_forwarded', fetchNotifications);
  
  fetchAgents();
  fetchNotifications();
  startNotificationPolling();
  animateControls();
});

onUnmounted(() => {
  stopNotificationPolling();
  if (socket.value) {
    socket.value.disconnect();
  }
});

// Watchers
watch(mainFilter, () => {
  fetchNotifications();
});

watch(detectionSubFilter, () => {
  fetchNotifications();
});

watch(selectedNotification, (newVal) => {
  if (newVal && newVal.event_type === 'object_detection') {
    fetchDashboardStreams();
  }
  
  // Animate the detail container when notification changes
  if (newVal) {
    nextTick(() => {
      animateDetailContainer();
    });
  }
});

// Methods
const formatImage = (image) => {
  if (image && !image.startsWith("data:")) {
    return "data:image/png;base64," + image;
  }
  return image;
};

const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toLocaleString();
};

const formatConfidence = (confidence) => {
  return (typeof confidence === 'number' && confidence > 0)
    ? `${(confidence * 100).toFixed(1)}%`
    : '';
};

const getConfidenceColor = (confidence) => {
  const conf = typeof confidence === 'number' ? confidence : 0;
  if (conf >= 0.9) return '#ff4444';
  if (conf >= 0.75) return '#ff8c00';
  if (conf >= 0.5) return '#ffcc00';
  return '#28a745';
};

const getNotificationColor = (notification) => {
  if (notification.event_type === 'object_detection' && 
      notification.details?.detections?.[0]?.confidence) {
    return getConfidenceColor(notification.details.detections[0].confidence);
  } else if (notification.event_type === 'audio_detection') {
    return '#007bff';
  } else if (notification.event_type === 'chat_detection') {
    return '#8a2be2';
  } else if (notification.event_type === 'stream_created') {
    return '#28a745';
  }
  return '#28a745';
};

const getNotificationMessage = (notification) => {
  if (notification.event_type === 'object_detection') {
    return `Detected ${notification.details?.detections?.length || 0} objects`;
  } else if (notification.event_type === 'audio_detection') {
    return `Detected keyword: ${notification.details?.keyword}`;
  } else if (notification.event_type === 'chat_detection') {
    return `Chat event: ${notification.details?.keyword}`;
  } else if (notification.event_type === 'stream_created') {
    return `New stream created by ${notification.details?.streamer_name || 'Unknown'}`;
  }
  return notification.message;
};

const getNotificationDetailTitle = () => {
  if (!selectedNotification.value) return '';
  
  switch (selectedNotification.value.event_type) {
    case 'audio_detection':
      return 'Audio Detection Details';
    case 'object_detection':
      return 'Visual Detection Details';
    case 'chat_detection':
      return 'Chat Detection Details';
    case 'stream_created':
      return 'New Stream Created';
    default:
      return 'Notification Details';
  }
};

const processNotifications = (data) => {
  return data.map(notification => {
    const assignedAgent = notification.details?.assigned_agent || 
                       notification.assigned_agent || 
                       "Unassigned";
    
    const baseNotification = {
      id: notification.id,
      event_type: notification.event_type,
      timestamp: notification.timestamp,
      read: notification.read,
      details: {
        ...notification.details,
        detections: (notification.details?.detections || []).map(d => ({
          class: d.class,
          confidence: d.confidence || d.score || 0,
          bbox: d.bbox || []
        })),
        images: notification.details?.images || {
          annotated: notification.details?.annotated_image,
          original: notification.details?.captured_image
        },
        stream: notification.details?.stream || {
          platform: notification.details?.platform,
          streamer: notification.details?.streamer_name,
          url: notification.room_url
        },
        agent: assignedAgent
      },
      assigned_agent: assignedAgent
    };

    return {
      ...baseNotification,
      displayType: notification.event_type === 'object_detection' ? 'object' : notification.event_type,
      previewText: notification.event_type === 'object_detection'
        ? `${notification.details.detections.length} objects detected`
        : notification.details.message,
      timestamp: notification.timestamp,
      confidence: notification.event_type === 'object_detection'
        ? Math.max(...(notification.details.detections.map(d => d.confidence))) || 0
        : 0
    };
  });
};

const handleMainFilterChange = (tab) => {
  mainFilter.value = tab;
  if (tab === 'Detections') {
    detectionSubFilter.value = 'Visual';
  }
};

const handleNotificationClick = (notification) => {
  if (!notification.read) {
    markAsRead(notification.id);
  }
  selectedNotification.value = notification;
  
  // Animate the clicked notification
  if (notificationItems.value) {
    const clickedElement = notificationItems.value.find(el => 
      el.__vnode.key === notification.id
    );
      
    if (clickedElement) {
      anime({
        targets: clickedElement,
        scale: [1, 1.03, 1],
        backgroundColor: [
          'rgba(255, 255, 255, 0.05)',
          'rgba(0, 123, 255, 0.15)',
          'rgba(255, 255, 255, 0.05)'
        ],
        duration: 400,
        easing: 'easeOutCubic'
      });
    }
  }
};

const fetchNotifications = async () => {
  try {
    loading.value = true;
    error.value = null;
    const res = await axios.get('/api/notifications', { timeout: 10000 });
    
    if (res.status === 200 && Array.isArray(res.data)) {
      let processed = processNotifications(res.data);
      
      if (props.user && props.user.role === 'agent') {
        processed = processed.filter(n =>
          (n.assigned_agent || "").toLowerCase() === props.user.username.toLowerCase()
        );
      }
      
      if (mainFilter.value === 'Unread') {
        processed = processed.filter(n => !n.read);
      } else if (mainFilter.value === 'Detections') {
        const typeMap = {
          Visual: 'object_detection',
          Audio: 'audio_detection',
          Chat: 'chat_detection',
        };
        processed = processed.filter(n => n.event_type === typeMap[detectionSubFilter.value]);
      }
      
      notifications.value = processed;
      
      // Animate notifications entrance
      nextTick(() => {
        animateNotificationItems();
      });
    } else {
      error.value = 'Unexpected response from server.';
    }
  } catch (err) {
    console.error('Error fetching notifications:', err);
    error.value = 'Failed to load notifications.';
    toast.error('Failed to load notifications');
  } finally {
    loading.value = false;
  }
};

const fetchAgents = async () => {
  if (props.user && props.user.role === 'admin') {
    try {
      const res = await axios.get('/api/agents');
      agents.value = res.data;
    } catch (err) {
      console.error('Error fetching agents:', err);
      toast.error('Failed to load agents');
    }
  }
};

const fetchDashboardStreams = async () => {
  try {
    const res = await axios.get('/api/dashboard');
    if (res.status === 200 && res.data && res.data.streams) {
      dashboardStreams.value = res.data.streams;
    }
  } catch (err) {
    console.error('Error fetching dashboard streams:', err);
    toast.error('Failed to load dashboard streams');
  }
};

let notificationPollInterval;

const startNotificationPolling = () => {
  notificationPollInterval = setInterval(() => {
    fetchNotifications();
  }, 60000);
};

const stopNotificationPolling = () => {
  if (notificationPollInterval) {
    clearInterval(notificationPollInterval);
  }
};

const markAsRead = async (notificationId) => {
  try {
    await axios.put(`/api/notifications/${notificationId}/read`);
    notifications.value = notifications.value.map(n => 
      n.id === notificationId ? { ...n, read: true } : n
    );
    toast.success('Notification marked as read');
  } catch (err) {
    console.error('Error marking notification as read:', err);
    toast.error('Failed to mark notification as read');
  }
};

const markAllAsRead = async () => {
  try {
    await axios.put('/api/notifications/read-all');
    notifications.value = notifications.value.map(n => ({ ...n, read: true }));
    
    // Show animation feedback
    anime({
      targets: '.notifications-list .notification-item',
      backgroundColor: ['rgba(255, 208, 0, 0.1)', 'rgba(255, 255, 255, 0.05)'],
      easing: 'easeOutQuad',
      duration: 1000,
      delay: anime.stagger(50)
    });
    
    toast.success('All notifications marked as read');
  } catch (err) {
    console.error('Error marking all notifications as read:', err);
    toast.error('Failed to mark all notifications as read');
  }
};

const deleteNotification = async (notificationId) => {
  const notificationElement = notificationItems.value.find(
    el => el.__vnode.key === notificationId
  );
  
  if (notificationElement) {
    // Animate deletion
    await anime({
      targets: notificationElement,
      translateX: [0, '100%'],
      opacity: [1, 0],
      easing: 'easeInOutQuad',
      duration: 500
    }).finished;
  }
  
  try {
    await axios.delete(`/api/notifications/${notificationId}`);
    notifications.value = notifications.value.filter(n => n.id !== notificationId);
    if (selectedNotification.value && selectedNotification.value.id === notificationId) {
      selectedNotification.value = null;
    }
    toast.success('Notification deleted');
  } catch (err) {
    console.error('Error deleting notification:', err);
    toast.error('Failed to delete notification');
  }
};

const deleteAllNotifications = async () => {
  // Animate all notifications disappearing
  await anime({
    targets: '.notifications-list .notification-item',
    translateX: [0, '100%'],
    opacity: [1, 0],
    easing: 'easeInOutQuad',
    duration: 500,
    delay: anime.stagger(50)
  }).finished;
  
  try {
    await axios.delete('/api/notifications/delete-all');
    notifications.value = [];
    selectedNotification.value = null;
    toast.success('All notifications deleted');
  } catch (err) {
    console.error('Error deleting all notifications:', err);
    toast.error('Failed to delete all notifications');
  }
};

const forwardNotification = async (agentId) => {
  if (!selectedNotification.value) return;
  
  try {
    await axios.post(`/api/notifications/${selectedNotification.value.id}/forward`, { 
      agent_id: agentId 
    });
    isAgentDropdownOpen.value = false;
    fetchNotifications();
    
    // Show success animation
    anime({
      targets: '.notification-detail',
      backgroundColor: [
        'rgba(40, 167, 69, 0.2)',
        'rgba(0, 0, 0, 0)'
      ],
      duration: 1000,
      easing: 'easeOutCubic'
    });
    
    toast.success('Notification forwarded to agent');
  } catch (err) {
    console.error('Forward error:', err);
    toast.error('Failed to forward notification');
  }
};

// Animation methods
const animateControls = () => {
  anime({
    targets: notificationsControls.value,
    translateY: ['-30px', 0],
    opacity: [0, 1],
    duration: 800,
    easing: 'easeOutExpo'
  });
};

const animateNotificationItems = () => {
  if (!notificationItems.value || notificationItems.value.length === 0) return;
  
  anime({
    targets: notificationItems.value,
    translateX: ['-30px', 0],
    opacity: [0, 1],
    duration: 800,
    delay: anime.stagger(50),
    easing: 'easeOutCubic'
  });
};

const animateDetailContainer = () => {
  if (!detailContainer.value) return;
  
  anime({
    targets: detailContainer.value,
    translateY: [20, 0],
    opacity: [0, 1],
    duration: 500,
    easing: 'easeOutCubic'
  });
  
  if (streamerInfoCard.value) {
    anime({
      targets: streamerInfoCard.value,
      translateX: [30, 0],
      opacity: [0, 1],
      duration: 600,
      delay: 200,
      easing: 'easeOutCubic'
    });
  }
  
  if (detectedObjects.value) {
    anime({
      targets: detectedObjects.value,
      translateX: [30, 0],
      opacity: [0, 1],
      duration: 600,
      delay: 300,
      easing: 'easeOutCubic'
    });
  }
  
  if (detectionItems.value && detectionItems.value.length > 0) {
    anime({
      targets: detectionItems.value,
      translateX: [20, 0],
      opacity: [0, 1],
      duration: 800,
      delay: anime.stagger(100),
      easing: 'easeOutCubic'
    });
  }
};

const animateImageLoad = (event) => {
  anime({
    targets: event.target,
    scale: [0.9, 1],
    opacity: [0, 1],
    duration: 500,
    easing: 'easeOutCubic'
  });
};
</script>

<style>
.notifications-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  color: var(--text-color);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

.notifications-controls {
  background-color: var(--input-bg);
  border-bottom: 1px solid var(--input-border);
  padding: 1rem;
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.notifications-container {
  display: flex;
  height: calc(100vh - 150px);
  overflow: hidden;
}

.notifications-list-container {
  flex: 1;
  padding: 1rem;
  border-right: 1px solid var(--input-border);
  overflow-y: auto;
  max-width: 40%;
}

.notification-detail-container {
  flex: 2;
  padding: 1rem;
  overflow-y: auto;
}

.main-filter-controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.filter-btn, .sub-filter-btn {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  background-color: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--input-border);
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

.filter-btn:hover, .sub-filter-btn:hover {
  background-color: var(--primary-color);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.filter-btn.active, .sub-filter-btn.active {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.sub-filter-controls {
  display: flex;
  gap: 0.8rem;
  margin-bottom: 1rem;
  padding-left: 1rem;
}

.sub-filter-btn {
  font-size: 0.9rem;
  padding: 0.4rem 1rem;
}

.action-controls {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.mark-all-read, .delete-all, .refresh-notifications {
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
  border: 1px solid var(--input-border);
}

.mark-all-read {
  background-color: #28a745;
  color: white;
  border-color: #28a745;
}

.mark-all-read:hover:not(:disabled) {
  background-color: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
}

.delete-all {
  background-color: #dc3545;
  color: white;
  border-color: #dc3545;
}

.delete-all:hover:not(:disabled) {
  background-color: #c82333;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(220, 53, 69, 0.3);
}

.refresh-notifications {
  background-color: var(--input-bg);
  color: var(--text-color);
}

.refresh-notifications:hover {
  background-color: var(--hover-bg);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.mark-all-read:disabled, .delete-all:disabled, .refresh-notifications:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.notification-item {
  display: flex;
  padding: 1rem;
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--input-border);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.notification-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background-color: rgba(255, 255, 255, 0.08);
}

.notification-item.selected {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 1px var(--primary-color);
  background-color: rgba(0, 123, 255, 0.08);
}

.notification-item.unread {
  font-weight: 600;
  background-color: rgba(0, 123, 255, 0.05);
}

.notification-indicator {
  width: 4px;
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  transition: all 0.2s ease;
}

.notification-content {
  flex: 1;
  padding-left: 0.5rem;
}

.notification-message {
  margin-bottom: 0.5rem;
  word-break: break-word;
}

.notification-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.notification-time {
  opacity: 0.8;
}

.notification-confidence {
  font-weight: 600;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(0, 123, 255, 0.2);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  padding: 1rem;
  background-color: rgba(220, 53, 69, 0.1);
  border: 1px solid rgba(220, 53, 69, 0.3);
  color: #dc3545;
  border-radius: 8px;
  margin: 1rem 0;
}

.empty-state, .empty-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--text-secondary);
  text-align: center;
  height: 100%;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.6;
}

.notification-detail {
  padding: 1.5rem;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid var(--input-border);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--input-border);
}

.detail-header h3 {
  margin: 0;
  font-size: 1.25rem;
}

.detail-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.mark-read-btn, .forward-btn, .delete-btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid var(--input-border);
  font-weight: 500;
}

.mark-read-btn {
  background-color: #28a745;
  color: white;
  border-color: #28a745;
}

.mark-read-btn:hover {
  background-color: #218838;
}

.forward-btn {
  background-color: #17a2b8;
  color: white;
  border-color: #17a2b8;
}

.forward-btn:hover {
  background-color: #138496;
}

.delete-btn {
  background-color: #dc3545;
  color: white;
  border-color: #dc3545;
}

.delete-btn:hover {
  background-color: #c82333;
}

.detail-timestamp {
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.image-gallery {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}

.image-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  overflow: hidden;
  background-color: rgba(0, 0, 0, 0.2);
  padding-bottom: 0.5rem;
}

.detection-image {
  max-width: 300px;
  max-height: 250px;
  object-fit: contain;
}

.image-label {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.streamer-info-card, .detected-objects {
  background-color: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--input-border);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.streamer-info-card h4, .detected-objects h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.1rem;
  color: var(--text-color);
  border-bottom: 1px solid var(--input-border);
  padding-bottom: 0.5rem;
}

.info-item {
  display: flex;
  margin-bottom: 0.8rem;
}

.info-label {
  width: 120px;
  color: var(--text-secondary);
}

.info-value {
  flex: 1;
  font-weight: 500;
}

.unassigned-badge {
  background-color: rgba(255, 193, 7, 0.2);
  color: #ffc107;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.detection-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  margin-bottom: 0.5rem;
  border: 1px solid var(--input-border);
  transition: all 0.2s ease;
}

.detection-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.detection-class {
  font-weight: 500;
}

.confidence-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  color: white;
}

.audio-detection-content, .chat-detection-content, .stream-created-content {
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid var(--input-border);
}

.chat-excerpt {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 1rem;
  border-radius: 6px;
  font-family: monospace;
  white-space: pre-wrap;
  overflow: auto;
  max-height: 300px;
}

.forward-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.forward-modal-content {
  background-color: var(--bg-color);
  border-radius: 12px;
  padding: 1.5rem;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--input-border);
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--input-border);
  font-size: 1.25rem;
  font-weight: 600;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-color);
  opacity: 0.7;
  transition: opacity 0.2s;
}

.modal-close-btn:hover {
  opacity: 1;
}

.agent-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.agent-option {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--input-border);
  cursor: pointer;
  transition: all 0.2s ease;
}

.agent-option:hover {
  background-color: rgba(0, 123, 255, 0.08);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.agent-status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 1rem;
}

.agent-status-indicator.online {
  background-color: #28a745;
  box-shadow: 0 0 8px rgba(40, 167, 69, 0.5);
}

.agent-status-indicator.offline {
  background-color: #dc3545;
  box-shadow: 0 0 8px rgba(220, 53, 69, 0.5);
}

.agent-info {
  display: flex;
  flex-direction: column;
}

.agent-name {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.agent-email {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .notifications-container {
    flex-direction: column;
    height: auto;
  }
  
  .notifications-list-container {
    max-width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--input-border);
  }
  
  .action-controls {
    flex-wrap: wrap;
  }
  
  .forward-modal-content {
    max-width: 90%;
  }
}

@media (max-width: 768px) {
  .main-filter-controls, .sub-filter-controls {
    flex-wrap: wrap;
  }
  
  .image-gallery {
    flex-direction: column;
    align-items: center;
  }
  
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .detail-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>