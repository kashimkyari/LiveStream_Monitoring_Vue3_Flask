<template>
  <div v-if="isVisible" class="notifications-container">
    <!-- Header with counter -->
    <div class="header">
      <h3>Notifications <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span></h3>
      <div class="header-actions">
        <button 
          v-if="hasUnreadNotifications" 
          class="btn-action" 
          @click="markAllAsRead"
        >
          Mark all read
        </button>
        <button class="btn-close" @click="$emit('close')">×</button>
      </div>
    </div>

    <!-- Status displays (loading, error, empty) -->
    <div v-if="loading" class="status-container">
      <div class="spinner"></div>
      <p>Loading notifications...</p>
    </div>
    
    <div v-else-if="error" class="status-container error">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchNotifications">Try again</button>
    </div>
    
    <div v-else-if="notifications.length === 0" class="status-container empty">
      <div class="empty-icon">🔔</div>
      <p>No notifications</p>
    </div>

    <!-- Notification list -->
    <div v-else class="notifications-list">
      <div 
        v-for="notification in notifications" 
        :key="notification.id"
        :class="['notification-item', { unread: !notification.read }]"
        @click="viewDetails(notification)"
      >
        <!-- Icon by type -->
        <div :class="['notification-icon', getTypeClass(notification)]">
          <i :class="getTypeIcon(notification)"></i>
        </div>
        
        <!-- Content -->
        <div class="notification-content">
          <div class="notification-header">
            <span class="type-label">{{ getTypeLabel(notification) }}</span>
            <span class="time">{{ formatTime(notification.timestamp) }}</span>
          </div>
          
          <!-- Summary based on notification type -->
          <p class="summary">{{ getSummary(notification) }}</p>
          
          <!-- Preview content based on type -->
          <div v-if="notification.event_type === 'object_detection'" class="preview">
            <div 
              v-for="(detection, idx) in notification.details.detections?.slice(0, 2)" 
              :key="idx"
              class="detection-tag"
            >
              {{ detection.class }} 
              <span :class="['confidence', getConfidenceClass(detection.confidence)]">
                {{ Math.round(detection.confidence * 100) }}%
              </span>
            </div>
            <span v-if="(notification.details.detections?.length || 0) > 2" class="more">
              +{{ notification.details.detections.length - 2 }} more
            </span>
          </div>
          
          <div v-else-if="notification.event_type === 'audio_detection'" class="preview">
            <span 
              v-for="(keyword, idx) in notification.details.keywords?.slice(0, 3)" 
              :key="idx"
              class="keyword-tag"
            >
              {{ keyword }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Details modal -->
  <Teleport to="body">
    <div v-if="selectedNotification" class="modal">
      <div class="modal-backdrop" @click="closeDetails"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ getTypeLabel(selectedNotification) }}</h3>
          <div class="modal-actions">
            <button 
              v-if="!selectedNotification.read" 
              class="btn-mark-read" 
              @click="markAsRead(selectedNotification.id)"
            >
              Mark read
            </button>
            <button class="btn-close" @click="closeDetails">×</button>
          </div>
        </div>
        
        <div class="modal-time">{{ formatTimeDetail(selectedNotification.timestamp) }}</div>
        
        <!-- Visual detection details -->
        <div v-if="selectedNotification.event_type === 'object_detection'" class="detection-details">
          <div v-if="hasImages(selectedNotification)" class="detection-images">
            <img 
              v-if="selectedNotification.details.annotated_image" 
              :src="formatImageSrc(selectedNotification.details.annotated_image)" 
              alt="Detection"
              class="detection-image"
            />
          </div>
          
          <div v-if="selectedNotification.details.detections?.length" class="detections-list">
            <h4>Detected Objects</h4>
            <div class="detections-grid">
              <div 
                v-for="(detection, idx) in selectedNotification.details.detections" 
                :key="idx"
                class="detection-item"
              >
                <span class="detection-name">{{ detection.class }}</span>
                <span 
                  :class="['confidence-label', getConfidenceClass(detection.confidence)]"
                >
                  {{ Math.round(detection.confidence * 100) }}%
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Audio detection details -->
        <div v-else-if="selectedNotification.event_type === 'audio_detection'" class="audio-details">
          <div v-if="selectedNotification.details.keywords?.length" class="keywords-section">
            <h4>Detected Keywords</h4>
            <div class="keywords-list">
              <span 
                v-for="(keyword, idx) in selectedNotification.details.keywords" 
                :key="idx"
                class="keyword"
              >
                {{ keyword }}
              </span>
            </div>
          </div>
          
          <div v-if="selectedNotification.details.transcript" class="transcript-section">
            <h4>Transcript</h4>
            <p class="transcript-text">{{ selectedNotification.details.transcript }}</p>
          </div>
        </div>
        
        <!-- Chat detection details -->
        <div v-else-if="selectedNotification.event_type === 'chat_detection'" class="chat-details">
          <div class="keyword-section">
            <h4>Detected Keyword</h4>
            <span class="highlighted-keyword">{{ selectedNotification.details.keyword }}</span>
          </div>
          
          <div v-if="selectedNotification.details.ocr_text" class="context-section">
            <h4>Message Context</h4>
            <p class="context-text">{{ selectedNotification.details.ocr_text }}</p>
          </div>
        </div>
        
        <!-- Stream details -->
        <div v-else-if="selectedNotification.event_type === 'stream_created'" class="stream-details">
          <div class="streamer-section">
            <h4>Stream Created By</h4>
            <p class="streamer">{{ selectedNotification.details.streamer_name || 'Unknown' }}</p>
          </div>
          
          <div v-if="selectedNotification.details.stream_url" class="url-section">
            <h4>Stream URL</h4>
            <div class="url-container">
              <a 
                :href="selectedNotification.details.stream_url" 
                target="_blank" 
                class="stream-url"
              >
                {{ selectedNotification.details.stream_url }}
              </a>
              <button class="btn-copy" @click="copyToClipboard(selectedNotification.details.stream_url)">
                Copy
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, defineProps, defineEmits } from 'vue';
import { formatDistanceToNow, format } from 'date-fns';

// Props
const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  user: {
    type: Object,
    default: () => ({})
  }
});

// Emits
const emit = defineEmits(['close', 'update:notifications']);

// State
const notifications = ref([]);
const loading = ref(true);
const error = ref(null);
const selectedNotification = ref(null);
const pollInterval = ref(null);

// Computed
const hasUnreadNotifications = computed(() => {
  return notifications.value.some(n => !n.read);
});

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.read).length;
});

// Lifecycle
onMounted(() => {
  if (props.isVisible) {
    fetchNotifications();
  }
  startPolling();
});

onUnmounted(() => {
  stopPolling();
});

// Watchers
watch(() => props.isVisible, (isVisible) => {
  if (isVisible) {
    fetchNotifications();
  }
});

// Methods
function startPolling() {
  pollInterval.value = setInterval(() => {
    if (props.isVisible) {
      fetchNotifications(true);
    }
  }, 30000); // 30 seconds
}

function stopPolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value);
    pollInterval.value = null;
  }
}

async function fetchNotifications(silent = false) {
  if (!silent) loading.value = true;
  error.value = null;
  
  try {
    // In real app, fetch from API
    // const response = await fetch('/api/notifications');
    // const data = await response.json();
    
    // Mock data for demo
    await new Promise(resolve => setTimeout(resolve, 500));
    notifications.value = getMockData();
    emit('update:notifications', unreadCount.value);
  } catch (err) {
    console.error('Failed to fetch notifications:', err);
    error.value = 'Could not load notifications. Please try again.';
  } finally {
    if (!silent) loading.value = false;
  }
}

function getTypeClass(notification) {
  const types = {
    'object_detection': 'visual',
    'audio_detection': 'audio',
    'chat_detection': 'chat',
    'stream_created': 'stream'
  };
  return types[notification.event_type] || 'generic';
}

function getTypeIcon(notification) {
  const icons = {
    'object_detection': 'icon-camera',
    'audio_detection': 'icon-mic',
    'chat_detection': 'icon-message',
    'stream_created': 'icon-video'
  };
  return icons[notification.event_type] || 'icon-bell';
}

function getTypeLabel(notification) {
  const labels = {
    'object_detection': 'Visual Alert',
    'audio_detection': 'Audio Alert',
    'chat_detection': 'Chat Alert',
    'stream_created': 'New Stream'
  };
  return labels[notification.event_type] || 'Alert';
}

function getSummary(notification) {
  switch(notification.event_type) {
    case 'object_detection': {
      const count = notification.details.detections?.length || 0;
      return `${count} object${count !== 1 ? 's' : ''} detected`;
    }
    case 'audio_detection': {
      return `Audio keyword detected: ${notification.details.keywords?.[0] || 'unknown'}`;
    }
    case 'chat_detection': {
      return `Chat keyword detected: ${notification.details.keyword || 'unknown'}`;
    }
    case 'stream_created': {
      return `Stream started by ${notification.details.streamer_name || 'Unknown'}`;
    }
    default: {
      return notification.message || 'New notification';
    }
  }
}

function getConfidenceClass(confidence) {
  if (!confidence) return 'low';
  if (confidence >= 0.85) return 'high';
  if (confidence >= 0.7) return 'medium';
  return 'low';
}

function formatTime(timestamp) {
  try {
    return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
  } catch (e) {
    return 'just now';
  }
}

function formatTimeDetail(timestamp) {
  try {
    return format(new Date(timestamp), 'PPpp');
  } catch (e) {
    return 'unknown time';
  }
}

function hasImages(notification) {
  return notification.details.annotated_image || notification.details.captured_image;
}

function formatImageSrc(image) {
  if (!image) return '';
  if (image.startsWith('data:')) return image;
  return `data:image/png;base64,${image}`;
}

function viewDetails(notification) {
  if (!notification.read) {
    markAsRead(notification.id, false);
  }
  selectedNotification.value = notification;
}

function closeDetails() {
  selectedNotification.value = null;
}

async function markAsRead(id, updateSelected = true) {
  // In real app, call API
  // await fetch(`/api/notifications/${id}/read`, { method: 'PUT' });
  
  notifications.value = notifications.value.map(n => 
    n.id === id ? { ...n, read: true } : n
  );
  
  if (updateSelected && selectedNotification.value?.id === id) {
    selectedNotification.value = { ...selectedNotification.value, read: true };
  }
  
  emit('update:notifications', unreadCount.value);
}

async function markAllAsRead() {
  // In real app, call API
  // await fetch('/api/notifications/mark-all-read', { method: 'PUT' });
  
  notifications.value = notifications.value.map(n => ({ ...n, read: true }));
  
  if (selectedNotification.value) {
    selectedNotification.value = { ...selectedNotification.value, read: true };
  }
  
  emit('update:notifications', 0);
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
    .catch(err => console.error('Failed to copy text:', err));
}

function getMockData() {
  return [
    {
      id: 1,
      event_type: 'object_detection',
      timestamp: new Date().toISOString(),
      read: false,
      details: {
        detections: [
          { class: 'Person', confidence: 0.95 },
          { class: 'Phone', confidence: 0.82 },
          { class: 'Laptop', confidence: 0.78 }
        ],
        annotated_image: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJYAAACWCAYAAAA8AXHiAAAAvklEQVR42u3QQQ0AAAAqQ/+MrwehAJVL7pNKJBKJRCKRSCQSiUQikUgkEolEIpFIJBKJRCKRSCQSiUQikUgkEolEIpFIJBKJRCKRSCQSiUQikUgkEolEIpFIJBKJRCKRSCQSiUQikUgkEolEIpFIJBKJRCKRSCQSiUQikUgkEolEIpFIJBKJRCKRSCQSiUQikUgkEolEIpFIJBKJRCKRSCQSiUQikUgkEolEIpFIJBKJRCKRSCQSiUQikUieBR8NXoZ9Pr6SAAAAAElFTkSuQmCC',
        platform: 'Streaming Platform'
      }
    },
    {
      id: 2,
      event_type: 'audio_detection',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      read: true,
      details: {
        keywords: ['hello', 'welcome', 'stream'],
        transcript: 'Hello there everyone, welcome to the stream'
      }
    },
    {
      id: 3,
      event_type: 'chat_detection',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      read: false,
      details: {
        keyword: 'private',
        ocr_text: 'Would you like to go private?'
      }
    },
    {
      id: 4,
      event_type: 'stream_created',
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      read: false,
      details: {
        streamer_name: 'StreamUser123',
        stream_url: 'https://example.com/stream/streamuser123'
      }
    }
  ];
}
</script>

<style scoped>
.notifications-container {
  width: 340px;
  max-height: 80vh;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid #eaeaea;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eaeaea;
}

.header h3 {
  font-size: 16px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.badge {
  background: #2563eb;
  color: white;
  font-size: 12px;
  border-radius: 10px;
  padding: 2px 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-action {
  font-size: 12px;
  background: transparent;
  color: #2563eb;
  border: none;
  padding: 4px 8px;
  cursor: pointer;
  border-radius: 4px;
}

.btn-action:hover {
  background: #eef2ff;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  color: #64748b;
}

.btn-close:hover {
  color: #334155;
}

/* Status displays */
.status-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  text-align: center;
  color: #64748b;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #e2e8f0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spinner 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spinner {
  to { transform: rotate(360deg); }
}

.status-container.error {
  color: #dc2626;
}

.btn-retry {
  margin-top: 8px;
  background: #2563eb;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.empty-icon {
  font-size: 24px;
  margin-bottom: 8px;
  opacity: 0.6;
}

/* Notifications list */
.notifications-list {
  overflow-y: auto;
  max-height: calc(80vh - 56px);
}

.notification-item {
  display: flex;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: background 0.2s;
}

.notification-item:hover {
  background: #f8fafc;
}

.notification-item.unread {
  background: #f0f9ff;
}

.notification-item.unread:hover {
  background: #e0f2fe;
}

/* Notification icons */
.notification-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
  color: white;
}

.notification-icon.visual {
  background: #22c55e;
}

.notification-icon.audio {
  background: #3b82f6;
}

.notification-icon.chat {
  background: #a855f7;
}

.notification-icon.stream {
  background: #ef4444;
}

.notification-icon.generic {
  background: #64748b;
}

/* Notification content */
.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.type-label {
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 600;
  color: #64748b;
}

.time {
  font-size: 11px;
  color: #94a3b8;
}

.summary {
  font-size: 14px;
  margin: 4px 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Preview sections */
.preview {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detection-tag {
  display: flex;
  align-items: center;
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  gap: 4px;
}

.confidence {
  font-size: 11px;
  padding: 1px 4px;
  border-radius: 3px;
  color: white;
}

.confidence.high {
  background: #22c55e;
}

.confidence.medium {
  background: #f59e0b;
}

.confidence.low {
  background: #ef4444;
}

.more {
  font-size: 11px;
  color: #94a3b8;
  align-self: center;
}

.keyword-tag {
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
}

/* Modal */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  width: 90%;
  max-width: 480px;
  max-height: 80vh;
  overflow-y: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.modal-actions {
  display: flex;
  gap: 8px;
}

.btn-mark-read {
  background: #2563eb;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.modal-time {
  color: #64748b;
  font-size: 13px;
  padding: 8px 16px;
  border-bottom: 1px solid #f1f5f9;
}

/* Detection details */
.detection-details, .audio-details, .chat-details, .stream-details {
  padding: 16px;
}

.detection-images {
  margin-bottom: 20px;
}

.detection-image {
  max-width: 100%;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

h4 {
  font-size: 15px;
  margin: 0 0 12px 0;
  color: #334155;
}

.detections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
}

.detection-item {
  background: #f8fafc;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.detection-name {
  font-size: 13px;
  font-weight: 500;
}

.confidence-label {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  color: white;
}

.confidence-label.high {
  background: #22c55e;
}

.confidence-label.medium {
  background: #f59e0b;
}

.confidence-label.low {
  background: #ef4444;
}

/* Audio details */
.keywords-section, .transcript-section {
  margin-bottom: 20px;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword {
  background: #f0f9ff;
  color: #2563eb;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 13px;
}

.transcript-text {
  background: #f8fafc;
  padding: 12px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}

/* Chat details */
.highlighted-keyword {
  display: inline-block;
  background: #fef2f2;
  color: #dc2626;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}

.context-text {
  background: #f8fafc;
  padding: 12px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5;
  margin-top: 8px;
}

/* Stream details */
.streamer {
  font-size: 16px;
  font-weight: 500;
}

.url-container {
  display: flex;
  align-items: center;
  background: #f8fafc;
  padding: 8px 12px;
  border-radius: 4px;
  gap: 8px;
  margin-top: 8px;
}

.stream-url {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #2563eb;
  text-decoration: none;
  font-size: 14px;
}

.btn-copy {
  background: #e2e8f0;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-copy:hover {
  background: #cbd5e1;
}
</style>