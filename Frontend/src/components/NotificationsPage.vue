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
                <button class="forward-btn" @click="setShowAgentDropdown(true)">
                  Forward to Agent
                </button>
                
                <transition name="modal-fade">
                  <div v-if="showAgentDropdown" class="forward-modal-overlay" @click="setShowAgentDropdown(false)">
                    <div class="forward-modal-content" @click.stop>
                      <div class="modal-header">
                        <h3>Select Agent</h3>
                        <button class="modal-close-btn" @click="setShowAgentDropdown(false)">
                          &times;
                        </button>
                      </div>
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
                  </div>
                </transition>
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

<script>
import axios from 'axios';
import anime from 'animejs/lib/anime.es.js';
import io from 'socket.io-client';

axios.defaults.withCredentials = true;
const SOCKET_SERVER_URL = 'http://54.86.99.85:5000';

export default {
  name: 'NotificationsPage',
  
  props: {
    user: {
      type: Object,
      default: null
    },
    ongoingStreams: {
      type: Array,
      default: () => []
    }
  },
  
  data() {
    return {
      notifications: [],
      loading: true,
      error: null,
      mainFilter: 'All',
      detectionSubFilter: 'Visual',
      selectedNotification: null,
      agents: [],
      dashboardStreams: [],
      showAgentDropdown: false,
      socket: null
    };
  },
  
  computed: {
    assignedAgent() {
      if (this.dashboardStreams && this.dashboardStreams.length > 0 && 
          this.selectedNotification && this.selectedNotification.details &&
          this.selectedNotification.details.stream) {
        const { platform, streamer } = this.selectedNotification.details.stream;
        const matchedStream = this.dashboardStreams.find(s =>
          s.platform.toLowerCase() === platform.toLowerCase() &&
          s.streamer_username.toLowerCase() === streamer.toLowerCase()
        );
        
        if (matchedStream && matchedStream.assignments && 
            matchedStream.assignments.length > 0 && matchedStream.assignments[0].agent) {
          const agentId = matchedStream.assignments[0].agent.id;
          const foundAgent = this.agents.find(a => a.id === agentId);
          if (foundAgent) return foundAgent.username;
          return matchedStream.assignments[0].agent.username || "Unassigned";
        }
      }
      return "Unassigned";
    }
  },
  
  created() {
    this.socket = io(SOCKET_SERVER_URL, { withCredentials: true });
    this.socket.on('notification_forwarded', this.fetchNotifications);
  },
  
  mounted() {
    this.fetchAgents();
    this.fetchNotifications();
    this.startNotificationPolling();
    this.animateControls();
  },
  
  beforeUnmount() {
    this.stopNotificationPolling();
    if (this.socket) {
      this.socket.disconnect();
    }
  },
  
  watch: {
    mainFilter() {
      this.fetchNotifications();
    },
    detectionSubFilter() {
      this.fetchNotifications();
    },
    selectedNotification(newVal) {
      if (newVal && newVal.event_type === 'object_detection') {
        this.fetchDashboardStreams();
      }
      
      // Animate the detail container when notification changes
      if (newVal) {
        this.$nextTick(() => {
          this.animateDetailContainer();
        });
      }
    }
  },
  
  methods: {
    formatImage(image) {
      if (image && !image.startsWith("data:")) {
        return "data:image/png;base64," + image;
      }
      return image;
    },
    
    formatTimestamp(timestamp) {
      return new Date(timestamp).toLocaleString();
    },
    
    formatConfidence(confidence) {
      return (typeof confidence === 'number' && confidence > 0)
        ? `${(confidence * 100).toFixed(1)}%`
        : '';
    },
    
    getConfidenceColor(confidence) {
      const conf = typeof confidence === 'number' ? confidence : 0;
      if (conf >= 0.9) return '#ff4444';
      if (conf >= 0.75) return '#ff8c00';
      if (conf >= 0.5) return '#ffcc00';
      return '#28a745';
    },
    
    getNotificationColor(notification) {
      if (notification.event_type === 'object_detection' && 
          notification.details?.detections?.[0]?.confidence) {
        return this.getConfidenceColor(notification.details.detections[0].confidence);
      } else if (notification.event_type === 'audio_detection') {
        return '#007bff';
      } else if (notification.event_type === 'chat_detection') {
        return '#8a2be2';
      } else if (notification.event_type === 'stream_created') {
        return '#28a745';
      }
      return '#28a745';
    },
    
    getNotificationMessage(notification) {
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
    },
    
    getNotificationDetailTitle() {
      if (!this.selectedNotification) return '';
      
      switch (this.selectedNotification.event_type) {
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
    },
    
    processNotifications(data) {
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
    },
    
    handleMainFilterChange(tab) {
      this.mainFilter = tab;
      if (tab === 'Detections') {
        this.detectionSubFilter = 'Visual';
      }
    },
    
    handleNotificationClick(notification) {
      if (!notification.read) {
        this.markAsRead(notification.id);
      }
      this.selectedNotification = notification;
      
      // Animate the clicked notification
      if (this.$refs.notificationItems) {
        const notificationElements = this.$refs.notificationItems;
        const clickedElement = Array.isArray(notificationElements) 
          ? notificationElements.find(el => el.__vue__.$vnode.key === notification.id)
          : null;
          
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
    },
    
    async fetchNotifications() {
      try {
        this.loading = true;
        this.error = null;
        const res = await axios.get('/api/notifications', { timeout: 10000 });
        
        if (res.status === 200 && Array.isArray(res.data)) {
          let processed = this.processNotifications(res.data);
          
          if (this.user && this.user.role === 'agent') {
            processed = processed.filter(n =>
              (n.assigned_agent || "").toLowerCase() === this.user.username.toLowerCase()
            );
          }
          
          if (this.mainFilter === 'Unread') {
            processed = processed.filter(n => !n.read);
          } else if (this.mainFilter === 'Detections') {
            const typeMap = {
              Visual: 'object_detection',
              Audio: 'audio_detection',
              Chat: 'chat_detection',
            };
            processed = processed.filter(n => n.event_type === typeMap[this.detectionSubFilter]);
          }
          
          this.notifications = processed;
          
          // Animate notifications entrance
          this.$nextTick(() => {
            this.animateNotificationItems();
          });
        } else {
          this.error = 'Unexpected response from server.';
        }
      } catch (err) {
        console.error('Error fetching notifications:', err);
        this.error = 'Failed to load notifications.';
      } finally {
        this.loading = false;
      }
    },
    
    async fetchAgents() {
      if (this.user && this.user.role === 'admin') {
        try {
          const res = await axios.get('/api/agents');
          this.agents = res.data;
        } catch (err) {
          console.error('Error fetching agents:', err);
        }
      }
    },
    
    async fetchDashboardStreams() {
      try {
        const res = await axios.get('/api/dashboard');
        if (res.status === 200 && res.data && res.data.streams) {
          this.dashboardStreams = res.data.streams;
        }
      } catch (err) {
        console.error('Error fetching dashboard streams:', err);
      }
    },
    
    startNotificationPolling() {
      this.notificationPollInterval = setInterval(() => {
        this.fetchNotifications();
      }, 60000);
    },
    
    stopNotificationPolling() {
      if (this.notificationPollInterval) {
        clearInterval(this.notificationPollInterval);
      }
    },
    
    async markAsRead(notificationId) {
      try {
        await axios.put(`/api/notifications/${notificationId}/read`);
        this.notifications = this.notifications.map(n => 
          n.id === notificationId ? { ...n, read: true } : n
        );
      } catch (err) {
        console.error('Error marking notification as read:', err);
      }
    },
    
    async markAllAsRead() {
      try {
        await axios.put('/api/notifications/read-all');
        this.notifications = this.notifications.map(n => ({ ...n, read: true }));
        
        // Show animation feedback
        anime({
          targets: '.notifications-list .notification-item',
          backgroundColor: ['rgba(255, 208, 0, 0.1)', 'rgba(255, 255, 255, 0.05)'],
          easing: 'easeOutQuad',
          duration: 1000,
          delay: anime.stagger(50)
        });
      } catch (err) {
        console.error('Error marking all notifications as read:', err);
      }
    },
    
    async deleteNotification(notificationId) {
      const notificationElement = this.$refs.notificationItems.find(
        el => el.__vue__.$vnode.key === notificationId
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
        this.notifications = this.notifications.filter(n => n.id !== notificationId);
        if (this.selectedNotification && this.selectedNotification.id === notificationId) {
          this.selectedNotification = null;
        }
      } catch (err) {
        console.error('Error deleting notification:', err);
      }
    },
    
    async deleteAllNotifications() {
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
        this.notifications = [];
        this.selectedNotification = null;
      } catch (err) {
        console.error('Error deleting all notifications:', err);
      }
    },
    
    setShowAgentDropdown(value) {
      this.showAgentDropdown = value;
      
      if (value) {
        this.$nextTick(() => {
          // Animate modal opening
          anime({
            targets: '.forward-modal-content',
            scale: [0.8, 1],
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutCubic'
          });
        });
      }
    },
    
    async forwardNotification(agentId) {
      if (!this.selectedNotification) return;
      
      try {
        await axios.post(`/api/notifications/${this.selectedNotification.id}/forward`, { 
          agent_id: agentId 
        });
        this.showAgentDropdown = false;
        this.fetchNotifications();
        
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
      } catch (err) {
        console.error('Forward error:', err);
      }
    },
    
    // Animation methods
    animateControls() {
      anime({
        targets: this.$refs.notificationsControls,
        translateY: ['-30px', 0],
        opacity: [0, 1],
        duration: 800,
        easing: 'easeOutExpo'
      });
    },
    
    animateNotificationItems() {
      if (!this.$refs.notificationItems || this.$refs.notificationItems.length === 0) return;
      
      anime({
        targets: this.$refs.notificationItems,
        translateX: ['-30px', 0],
        opacity: [0, 1],
        duration: 800,
        delay: anime.stagger(50),
        easing: 'easeOutCubic'
      });
    },
    
    animateDetailContainer() {
      if (!this.$refs.detailContainer) return;
      
      anime({
        targets: this.$refs.detailContainer,
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 500,
        easing: 'easeOutCubic'
      });
      
      if (this.$refs.streamerInfoCard) {
        anime({
          targets: this.$refs.streamerInfoCard,
          translateX: [30, 0],
          opacity: [0, 1],
          duration: 600,
          delay: 200,
          easing: 'easeOutCubic'
        });
      }
      
      if (this.$refs.detectedObjects) {
        anime({
          targets: this.$refs.detectedObjects,
          translateX: [30, 0],
          opacity: [0, 1],
          duration: 600,
          delay: 300,
          easing: 'easeOutCubic'
        });
      }
      
      if (this.$refs.detectionItems) {
        anime({
          targets: this.$refs.detectionItems,
          translateX: [20, 0],
          opacity: [0, 1],
          duration: 800,
          delay: anime.stagger(100),
          easing: 'easeOutCubic'
        });
      }
    },
    
    animateImageLoad(event) {
      anime({
        targets: event.target,
        scale: [0.9, 1],
        opacity: [0, 1],
        duration: 500,
        easing: 'easeOutCubic'
      });
    }
  }
};
</script>

<style>
.notifications-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  color: var(--text-color);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
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
</style>