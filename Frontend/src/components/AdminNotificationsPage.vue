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
          class="create-btn"
          @click="prepareCreateForm"
        >
          Create Notification
        </button>
        <button 
          class="mark-all-read"
          @click="markAllAsRead"
          :disabled="filteredNotifications.filter(n => !n.read).length === 0"
        >
          Mark All as Read
        </button>
        <button 
          class="delete-all"
          @click="isDeleteModalOpen = true"
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
        <h3>Notifications ({{ filteredNotifications.length }})</h3>
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading notifications...</p>
        </div>
        <div v-else-if="error" class="error-message">{{ error }}</div>
        <div v-else-if="filteredNotifications.length === 0" class="empty-state">
          <div class="empty-icon">🔔</div>
          <p>No notifications to display</p>
        </div>
        <div v-else class="notifications-list" ref="notificationsList">
          <div 
            v-for="notification in filteredNotifications" 
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
              <button 
                class="edit-btn" 
                @click="prepareEditForm"
              >
                Edit
              </button>
              <button 
                class="delete-btn" 
                @click="isDeleteModalOpen = true"
              >
                Delete
              </button>
              
              <div v-if="user && user.role === 'admin'" class="forward-section">
                <button class="forward-btn" @click="isAgentDropdownOpen = true">
                  Forward to Agent
                </button>
              </div>
            </div>
          </div>
          
          <div class="detail-content">
            <div class="detail-field">
              <label>Type:</label>
              <span>{{ selectedNotification.event_type }}</span>
            </div>
            <div class="detail-field">
              <label>Stream URL:</label>
              <a 
                :href="selectedNotification.room_url" 
                target="_blank" 
                rel="noopener noreferrer"
              >
                {{ selectedNotification.room_url }}
              </a>
            </div>
            <div class="detail-field">
              <label>Timestamp:</label>
              <span>{{ formatTimestamp(selectedNotification.timestamp) }}</span>
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
              <label>Assigned Agent:</label>
              <span>{{ selectedNotification.assigned_agent }}</span>
            </div>
            
            <!-- Specific detail sections based on event type -->
            <div v-if="selectedNotification.event_type === 'object_detection'" class="detection-details">
              <h4>Detection Details</h4>
              <div 
                v-if="selectedNotification.details && 
                      selectedNotification.details.detections && 
                      selectedNotification.details.detections.length > 0" 
                class="detections-list"
              >
                <div 
                  v-for="(detection, index) in selectedNotification.details.detections" 
                  :key="index"
                  class="detection-item"
                >
                  <span class="detection-class">{{ detection.class }}</span>
                  <span class="detection-confidence">
                    {{ formatConfidence(detection.confidence) }}
                  </span>
                </div>
              </div>
              <div 
                v-if="selectedNotification.details && selectedNotification.details.annotated_image"
                class="detection-image"
              >
                <img 
                  :src="`data:image/png;base64,${selectedNotification.details.annotated_image}`"
                  alt="Detection Image"
                />
              </div>
            </div>
            
            <div v-if="selectedNotification.event_type === 'chat_detection'" class="chat-details">
              <h4>Chat Details</h4>
              <div class="chat-message">
                <p>{{ selectedNotification.details?.message || 'No message content' }}</p>
              </div>
              <div 
                v-if="selectedNotification.details && selectedNotification.details.keywords && 
                      selectedNotification.details.keywords.length > 0"
                class="keywords-list"
              >
                <h5>Flagged Keywords:</h5>
                <div class="keywords">
                  <span 
                    v-for="(keyword, index) in selectedNotification.details.keywords" 
                    :key="index"
                    class="keyword-tag"
                  >
                    {{ keyword }}
                  </span>
                </div>
              </div>
            </div>
            
            <div v-if="selectedNotification.event_type === 'audio_detection'" class="audio-details">
              <h4>Audio Details</h4>
              <div class="audio-transcript">
                <h5>Transcript:</h5>
                <p>{{ selectedNotification.details?.transcript || 'No transcript available' }}</p>
              </div>
              <div v-if="selectedNotification.details && selectedNotification.details.keyword" class="keyword">
                <h5>Flagged Keyword:</h5>
                <span class="keyword-tag">{{ selectedNotification.details.keyword }}</span>
              </div>
            </div>
          </div>
          
          <!-- Raw JSON view for admins -->
          <div v-if="user && user.role === 'admin'" class="raw-json">
            <h4>Raw Details:</h4>
            <pre>{{ JSON.stringify(selectedNotification.details, null, 2) }}</pre>
          </div>
        </div>
      </div>
      
      <!-- Agent dropdown modal -->
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
                      <div class="agent-email">{{ agent.email || 'No email' }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </TransitionChild>
          </div>
        </Dialog>
      </TransitionRoot>
      
      <!-- Delete confirmation modal -->
      <TransitionRoot appear :show="isDeleteModalOpen" as="template">
        <Dialog as="div" @close="isDeleteModalOpen = false" class="delete-dialog">
          <div class="delete-modal-overlay">
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
              <div class="delete-modal-content">
                <DialogTitle as="h3" class="modal-header">
                  Delete Confirmation
                  <button class="modal-close-btn" @click="isDeleteModalOpen = false">
                    &times;
                  </button>
                </DialogTitle>
                <div class="modal-body">
                  <p v-if="selectedNotification">
                    Are you sure you want to delete this notification?
                  </p>
                  <p v-else>
                    Are you sure you want to delete all notifications?
                  </p>
                </div>
                <div class="modal-footer">
                  <button 
                    class="cancel-btn" 
                    @click="isDeleteModalOpen = false"
                  >
                    Cancel
                  </button>
                  <button 
                    class="confirm-btn" 
                    @click="selectedNotification ? deleteNotification(selectedNotification.id) : deleteAllNotifications()"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </TransitionChild>
          </div>
        </Dialog>
      </TransitionRoot>
      
      <!-- Edit notification modal -->
      <TransitionRoot appear :show="isEditModalOpen" as="template">
        <Dialog as="div" @close="isEditModalOpen = false" class="edit-dialog">
          <div class="edit-modal-overlay">
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
              <div class="edit-modal-content">
                <DialogTitle as="h3" class="modal-header">
                  Edit Notification
                  <button class="modal-close-btn" @click="isEditModalOpen = false">
                    &times;
                  </button>
                </DialogTitle>
                <div class="modal-body">
                  <div class="form-group">
                    <label for="event-type">Event Type:</label>
                    <select id="event-type" v-model="editForm.event_type">
                      <option v-for="option in eventTypes" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label for="room-url">Room URL:</label>
                    <input id="room-url" type="text" v-model="editForm.room_url" />
                  </div>
                  <div class="form-group">
                    <label for="details">Details (JSON):</label>
                    <textarea id="details" v-model="editForm.details" rows="10"></textarea>
                  </div>
                </div>
                <div class="modal-footer">
                  <button 
                    class="cancel-btn" 
                    @click="isEditModalOpen = false"
                  >
                    Cancel
                  </button>
                  <button 
                    class="save-btn" 
                    @click="updateNotification"
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            </TransitionChild>
          </div>
        </Dialog>
      </TransitionRoot>
      
      <!-- Create notification modal -->
      <TransitionRoot appear :show="isCreateModalOpen" as="template">
        <Dialog as="div" @close="isCreateModalOpen = false" class="create-dialog">
          <div class="create-modal-overlay">
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
              <div class="create-modal-content">
                <DialogTitle as="h3" class="modal-header">
                  Create Notification
                  <button class="modal-close-btn" @click="isCreateModalOpen = false">
                    &times;
                  </button>
                </DialogTitle>
                <div class="modal-body">
                  <div class="form-group">
                    <label for="create-event-type">Event Type:</label>
                    <select id="create-event-type" v-model="editForm.event_type">
                      <option v-for="option in eventTypes" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label for="create-room-url">Room URL:</label>
                    <input id="create-room-url" type="text" v-model="editForm.room_url" />
                  </div>
                  <div class="form-group">
                    <label for="create-details">Details (JSON):</label>
                    <textarea id="create-details" v-model="editForm.details" rows="10"></textarea>
                  </div>
                </div>
                <div class="modal-footer">
                  <button 
                    class="cancel-btn" 
                    @click="isCreateModalOpen = false"
                  >
                    Cancel
                  </button>
                  <button 
                    class="create-btn" 
                    @click="createNotification"
                  >
                    Create Notification
                  </button>
                </div>
              </div>
            </TransitionChild>
          </div>
        </Dialog>
      </TransitionRoot>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { Dialog, DialogOverlay, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue';

export default {
  components: {
    Dialog,
    DialogOverlay,
    DialogTitle,
    TransitionChild,
    TransitionRoot
  },
  setup() {
    const notifications = ref([]);
    const selectedNotification = ref(null);
    const mainFilter = ref('All');
    const detectionSubFilter = ref('Visual');
    const loading = ref(false);
    const error = ref(null);
    const isAgentDropdownOpen = ref(false);
    const agents = ref([]);
    const user = ref(null);
    const isDeleteModalOpen = ref(false);
    const isEditModalOpen = ref(false);
    const isCreateModalOpen = ref(false);
    const editForm = ref({
      event_type: '',
      room_url: '',
      details: {}
    });
    
    // For create/edit notification form
    const eventTypes = [
      { value: 'object_detection', label: 'Object Detection' },
      { value: 'chat_detection', label: 'Chat Detection' },
      { value: 'audio_detection', label: 'Audio Detection' },
      { value: 'stream_created', label: 'Stream Created' }
    ];
    
    // Function to fetch all notifications
    const fetchNotifications = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const response = await axios.get('/api/notifications');
        if (response.status === 200) {
          notifications.value = response.data;
        }
      } catch (err) {
        error.value = 'Failed to load notifications';
        console.error('Error fetching notifications:', err);
      } finally {
        loading.value = false;
      }
    };
    
    // Function to fetch user session info
    const fetchUserInfo = async () => {
      try {
        const response = await axios.get('/api/session');
        if (response.status === 200 && response.data.isLoggedIn) {
          user.value = response.data.user;
        }
      } catch (err) {
        console.error('Error fetching user info:', err);
      }
    };
    
    // Function to fetch agents
    const fetchAgents = async () => {
      try {
        const response = await axios.get('/api/agents');
        if (response.status === 200) {
          agents.value = response.data;
        }
      } catch (err) {
        console.error('Error fetching agents:', err);
      }
    };
    
    // Function to mark a notification as read
    const markAsRead = async (notificationId) => {
      try {
        const response = await axios.put(`/api/notifications/${notificationId}/read`);
        if (response.status === 200) {
          // Update local state
          const index = notifications.value.findIndex(n => n.id === notificationId);
          if (index !== -1) {
            notifications.value[index].read = true;
            
            // Update selected notification if it's the same one
            if (selectedNotification.value && selectedNotification.value.id === notificationId) {
              selectedNotification.value.read = true;
            }
          }
        }
      } catch (err) {
        console.error('Error marking notification as read:', err);
      }
    };
    
    // Function to mark all notifications as read
    const markAllAsRead = async () => {
      try {
        const response = await axios.put('/api/notifications/read-all');
        if (response.status === 200) {
          // Update local state
          notifications.value = notifications.value.map(n => ({ ...n, read: true }));
          
          // Update selected notification if there is one
          if (selectedNotification.value) {
            selectedNotification.value.read = true;
          }
        }
      } catch (err) {
        console.error('Error marking all notifications as read:', err);
      }
    };
    
    // Function to delete a notification
    const deleteNotification = async (notificationId) => {
      try {
        const response = await axios.delete(`/api/notifications/${notificationId}`);
        if (response.status === 200) {
          // Update local state
          notifications.value = notifications.value.filter(n => n.id !== notificationId);
          
          // Clear selected notification if it's the one being deleted
          if (selectedNotification.value && selectedNotification.value.id === notificationId) {
            selectedNotification.value = null;
          }
          
          // Close modal
          isDeleteModalOpen.value = false;
        }
      } catch (err) {
        console.error('Error deleting notification:', err);
      }
    };
    
    // Function to delete all notifications
    const deleteAllNotifications = async () => {
      try {
        const response = await axios.delete('/api/notifications/delete-all');
        if (response.status === 200) {
          // Update local state
          notifications.value = [];
          selectedNotification.value = null;
        }
      } catch (err) {
        console.error('Error deleting all notifications:', err);
      }
    };
    
    // Function to forward notification to an agent
    const forwardNotification = async (agentId) => {
      if (!selectedNotification.value) return;
      
      try {
        const response = await axios.post(`/api/notifications/${selectedNotification.value.id}/forward`, {
          agent_id: agentId
        });
        
        if (response.status === 200) {
          // Update selected notification
          const agent = agents.value.find(a => a.id === agentId);
          if (agent) {
            selectedNotification.value.details = selectedNotification.value.details || {};
            selectedNotification.value.details.assigned_agent = agent.username;
            selectedNotification.value.assigned_agent = agent.username;
            
            // Also update in the notifications list
            const index = notifications.value.findIndex(n => n.id === selectedNotification.value.id);
            if (index !== -1) {
              notifications.value[index].details = { ...notifications.value[index].details, assigned_agent: agent.username };
              notifications.value[index].assigned_agent = agent.username;
            }
          }
          
          // Close dropdown
          isAgentDropdownOpen.value = false;
        }
      } catch (err) {
        console.error('Error forwarding notification:', err);
      }
    };
    
    // Function to get notification color based on type
    const getNotificationColor = (notification) => {
      switch (notification.event_type) {
        case 'object_detection':
          return '#673AB7';  // Purple
        case 'chat_detection':
          return '#03A9F4';  // Blue
        case 'audio_detection':
          return '#E91E63';  // Pink
        case 'stream_created':
          return '#009688';  // Teal
        default:
          return '#9E9E9E';  // Grey
      }
    };
    
    // Function to get notification message
    const getNotificationMessage = (notification) => {
      switch (notification.event_type) {
        case 'object_detection':
          return `Object Detection: ${(notification.details?.detections || [])
            .map(d => d.class)
            .join(', ')}`;
        case 'chat_detection':
          return `Chat Detection: ${notification.details?.message || 'Message flagged'}`;
        case 'audio_detection':
          return `Audio Detection: ${notification.details?.keyword || 'Audio flagged'}`;
        case 'stream_created':
          return `New Stream: ${notification.details?.streamer_username || 'Unknown streamer'}`;
        default:
          return 'Notification';
      }
    };
    
    // Function to get notification detail title
    const getNotificationDetailTitle = () => {
      if (!selectedNotification.value) return '';
      
      switch (selectedNotification.value.event_type) {
        case 'object_detection':
          return 'Object Detection Details';
        case 'chat_detection':
          return 'Chat Detection Details';
        case 'audio_detection':
          return 'Audio Detection Details';
        case 'stream_created':
          return 'New Stream Details';
        default:
          return 'Notification Details';
      }
    };
    
    // Function to format timestamp
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'Unknown';
      
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const notificationDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      
      if (notificationDate.getTime() === today.getTime()) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' +
             date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };
    
    // Function to format confidence value
    const formatConfidence = (confidence) => {
      if (confidence === undefined || confidence === null) return 'N/A';
      return `${(confidence * 100).toFixed(1)}%`;
    };
    
    // Function to handle notification click
    const handleNotificationClick = (notification) => {
      selectedNotification.value = notification;
    };
    
    // Function to handle main filter change
    const handleMainFilterChange = (filter) => {
      mainFilter.value = filter;
    };
    
    // Function to prepare edit form with selected notification
    const prepareEditForm = () => {
      if (!selectedNotification.value) return;
      
      editForm.value = {
        event_type: selectedNotification.value.event_type,
        room_url: selectedNotification.value.room_url,
        details: JSON.stringify(selectedNotification.value.details || {}, null, 2)
      };
      
      isEditModalOpen.value = true;
    };
    
    // Function to prepare create form
    const prepareCreateForm = () => {
      editForm.value = {
        event_type: 'stream_created',
        room_url: '',
        details: JSON.stringify({
          platform: '',
          streamer_name: '',
          message: 'Stream created'
        }, null, 2)
      };
      
      isCreateModalOpen.value = true;
    };
    
    // Function to update a notification
    const updateNotification = async () => {
      if (!selectedNotification.value) return;
      
      try {
        // Parse JSON details
        let parsedDetails;
        try {
          parsedDetails = JSON.parse(editForm.value.details);
        } catch (jsonErr) {
          alert('Invalid JSON in details field');
          return;
        }
        
        const response = await axios.put(`/api/notifications/${selectedNotification.value.id}`, {
          event_type: editForm.value.event_type,
          room_url: editForm.value.room_url,
          details: parsedDetails
        });
        
        if (response.status === 200) {
          // Update local state
          const updatedNotification = response.data.notification;
          
          // Update in notifications list
          const index = notifications.value.findIndex(n => n.id === updatedNotification.id);
          if (index !== -1) {
            notifications.value[index] = {
              ...notifications.value[index],
              event_type: updatedNotification.event_type,
              room_url: updatedNotification.room_url,
              details: updatedNotification.details
            };
          }
          
          // Update selected notification
          selectedNotification.value = {
            ...selectedNotification.value,
            event_type: updatedNotification.event_type,
            room_url: updatedNotification.room_url,
            details: updatedNotification.details
          };
          
          // Close modal
          isEditModalOpen.value = false;
        }
      } catch (err) {
        console.error('Error updating notification:', err);
        alert('Failed to update notification');
      }
    };
    
    // Function to create a notification
    const createNotification = async () => {
      try {
        // Parse JSON details
        let parsedDetails;
        try {
          parsedDetails = JSON.parse(editForm.value.details);
        } catch (jsonErr) {
          alert('Invalid JSON in details field');
          return;
        }
        
        const response = await axios.post('/api/notifications', {
          event_type: editForm.value.event_type,
          room_url: editForm.value.room_url,
          details: parsedDetails
        });
        
        if (response.status === 201) {
          // Add to notifications list
          notifications.value = [response.data.notification, ...notifications.value];
          
          // Close modal
          isCreateModalOpen.value = false;
        }
      } catch (err) {
        console.error('Error creating notification:', err);
        alert('Failed to create notification');
      }
    };
    
    // Computed property for filtered notifications
    const filteredNotifications = computed(() => {
      let filtered = [...notifications.value];
      
      // Apply main filter
      if (mainFilter.value === 'Unread') {
        filtered = filtered.filter(n => !n.read);
      } else if (mainFilter.value === 'Detections') {
        if (detectionSubFilter.value === 'Visual') {
          filtered = filtered.filter(n => n.event_type === 'object_detection');
        } else if (detectionSubFilter.value === 'Audio') {
          filtered = filtered.filter(n => n.event_type === 'audio_detection');
        } else if (detectionSubFilter.value === 'Chat') {
          filtered = filtered.filter(n => n.event_type === 'chat_detection');
        }
      }
      
      return filtered;
    });
    
    // Initialization
    onMounted(async () => {
      await fetchUserInfo();
      await fetchNotifications();
      await fetchAgents();
    });
    
    return {
      notifications,
      filteredNotifications,
      selectedNotification,
      mainFilter,
      detectionSubFilter,
      loading,
      error,
      isAgentDropdownOpen,
      agents,
      user,
      isDeleteModalOpen,
      isEditModalOpen,
      isCreateModalOpen,
      editForm,
      eventTypes,
      
      fetchNotifications,
      markAsRead,
      markAllAsRead,
      deleteNotification,
      deleteAllNotifications,
      forwardNotification,
      getNotificationColor,
      getNotificationMessage,
      getNotificationDetailTitle,
      formatTimestamp,
      formatConfidence,
      handleNotificationClick,
      handleMainFilterChange,
      prepareEditForm,
      prepareCreateForm,
      updateNotification,
      createNotification
    };
  }
}
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
  background-color: rgba(var(--bg-color-rgb, 210, 175, 190), 0.07);
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