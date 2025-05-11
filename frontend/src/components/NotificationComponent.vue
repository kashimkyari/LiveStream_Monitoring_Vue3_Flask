<template>
  <div class="notifications-container" :class="{ 'dark-mode': isDarkMode }">
    <!-- Top navigation bar with filters and actions -->
    <header class="top-navigation">
      <div class="tab-filters">
        <button 
          v-for="tab in ['All', 'Unread', 'Detections']" 
          :key="tab"
          class="tab-button"
          :class="{ 'active': mainFilter === tab }"
          @click="handleMainFilterChange(tab)"
        >
          <span class="tab-text">{{ tab }}</span>
          <span v-if="tab === 'Unread'" class="count-badge">{{ unreadCount }}</span>
        </button>
      </div>
      
      <div class="action-controls">
        <button class="icon-button refresh" @click="fetchNotifications" title="Refresh">
          <font-awesome-icon icon="sync-alt" />
        </button>
        <button class="icon-button menu" @click="toggleMenu" title="More Actions">
          <font-awesome-icon icon="ellipsis-v" />
        </button>
        
        <!-- Dropdown menu -->
        <Transition name="fade">
          <div v-if="isMenuOpen" class="actions-dropdown">
            <button @click="prepareCreateForm" class="dropdown-item">
              <font-awesome-icon icon="plus" />
              <span>Create Notification</span>
            </button>
            <button 
              @click="markAllAsRead"
              :disabled="!hasUnreadNotifications"
              class="dropdown-item"
            >
              <font-awesome-icon icon="check-double" />
              <span>Mark All as Read</span>
            </button>
            <button 
              @click="confirmDeleteAll"
              :disabled="!hasNotifications"
              class="dropdown-item"
            >
              <font-awesome-icon icon="trash-alt" />
              <span>Delete All</span>
            </button>
            <button @click="toggleSound" class="dropdown-item">
              <font-awesome-icon :icon="soundEnabled ? 'volume-up' : 'volume-mute'" />
              <span>{{ soundEnabled ? 'Disable Sound' : 'Enable Sound' }}</span>
            </button>
          </div>
        </Transition>
      </div>
    </header>
    
    <!-- Sub-filters for detection types -->
    <Transition name="slide">
      <div v-if="mainFilter === 'Detections'" class="detection-filters">
        <button 
          v-for="subTab in ['Visual', 'Audio', 'Chat']" 
          :key="subTab"
          class="detection-filter-button"
          :class="{ active: detectionSubFilter === subTab }"
          @click="detectionSubFilter = subTab"
        >
          <font-awesome-icon :icon="getDetectionTypeIcon(subTab)" class="filter-icon" />
          <span>{{ subTab }}</span>
        </button>
      </div>
    </Transition>
    
    <!-- Main content area -->
    <div class="content-container">
      <!-- Left panel: Notifications list -->
      <section class="notifications-section" :class="{ 'expanded': !selectedNotification }">
        <div class="section-header">
          <h2 class="section-title">
            Notifications 
            <span class="notification-count">({{ filteredNotifications.length }})</span>
          </h2>
          <div class="section-actions" v-if="isAdmin">
            <button class="icon-button small" title="Filter" @click="showFilterOptions = !showFilterOptions">
              <font-awesome-icon icon="filter" />
            </button>
            <button class="icon-button small" title="Sort" @click="showSortOptions = !showSortOptions">
              <font-awesome-icon icon="sort" />
            </button>
          </div>
        </div>
        
        <!-- Filter/Sort dropdown menus -->
        <Transition name="fade">
          <div v-if="showFilterOptions" class="dropdown-panel filter-panel">
            <div class="dropdown-header">
              <h3>Filter by</h3>
              <button class="icon-button x-small" @click="showFilterOptions = false">
                <font-awesome-icon icon="times" />
              </button>
            </div>
            <div class="filter-options">
              <label class="filter-option">
                <input type="checkbox" v-model="filterOptions.visual" />
                <span>Visual Detections</span>
              </label>
              <label class="filter-option">
                <input type="checkbox" v-model="filterOptions.audio" />
                <span>Audio Detections</span>
              </label>
              <label class="filter-option">
                <input type="checkbox" v-model="filterOptions.chat" />
                <span>Chat Detections</span>
              </label>
              <label class="filter-option">
                <input type="checkbox" v-model="filterOptions.system" />
                <span>System Notifications</span>
              </label>
            </div>
          </div>
        </Transition>
        
        <Transition name="fade">
          <div v-if="showSortOptions" class="dropdown-panel sort-panel">
            <div class="dropdown-header">
              <h3>Sort by</h3>
              <button class="icon-button x-small" @click="showSortOptions = false">
                <font-awesome-icon icon="times" />
              </button>
            </div>
            <div class="sort-options">
              <button 
                class="sort-option" 
                :class="{ active: sortOption === 'newest' }"
                @click="changeSortOption('newest')"
              >
                <font-awesome-icon icon="sort-amount-down" />
                <span>Newest first</span>
              </button>
              <button 
                class="sort-option" 
                :class="{ active: sortOption === 'oldest' }"
                @click="changeSortOption('oldest')"
              >
                <font-awesome-icon icon="sort-amount-up" />
                <span>Oldest first</span>
              </button>
              <button 
                class="sort-option" 
                :class="{ active: sortOption === 'priority' }"
                @click="changeSortOption('priority')"
              >
                <font-awesome-icon icon="exclamation" />
                <span>Priority</span>
              </button>
            </div>
          </div>
        </Transition>
        
        <!-- Loading, error, or empty states -->
        <div v-if="loading" class="state-display loading-state">
          <div class="spinner"></div>
          <p>Loading notifications...</p>
        </div>
        
        <div v-else-if="error" class="state-display error-state">
          <div class="error-icon">
            <font-awesome-icon icon="exclamation-triangle" />
          </div>
          <p>{{ error }}</p>
          <button class="retry-button" @click="fetchNotifications">
            <font-awesome-icon icon="redo" />
            <span>Try Again</span>
          </button>
        </div>
        
        <div v-else-if="filteredNotifications.length === 0" class="state-display empty-state">
          <div class="empty-icon">
            <font-awesome-icon icon="bell" />
          </div>
          <p>No notifications to display</p>
        </div>
        
        <!-- Notifications list -->
        <div v-else class="notifications-list">
          <TransitionGroup name="list" tag="div">
            <div 
              v-for="notification in filteredNotifications" 
              :key="notification.id"
              class="notification-item"
              :class="{ 
                'read': notification.read, 
                'unread': !notification.read, 
                'selected': isNotificationSelected(notification),
                'new': newNotificationIds.includes(notification.id),
                'high-priority': getNotificationPriority(notification) === 'high',
                'medium-priority': getNotificationPriority(notification) === 'medium'
              }"
              @click="selectNotification(notification)"
            >
              <div 
                class="notification-status"
                :style="{ backgroundColor: getNotificationColor(notification) }"
              ></div>
              
              <div class="notification-details">
                <div class="notification-header">
                  <div class="notification-type">
                    <font-awesome-icon :icon="getNotificationTypeIcon(notification)" class="type-icon" />
                    <span>{{ getNotificationType(notification) }}</span>
                  </div>
                  <span class="notification-time">{{ formatTimestamp(notification.timestamp) }}</span>
                </div>
                
                <div class="notification-summary">
                  {{ getNotificationMessage(notification) }}
                </div>
                
                <div class="notification-metadata">
                  <div class="source-info">
                    <span class="platform">{{ getNotificationPlatform(notification) }}</span>
                    <span class="separator">•</span>
                    <span class="streamer">{{ getStreamerName(notification) }}</span>
                  </div>
                  
                  <span 
                    v-if="shouldShowConfidence(notification)" 
                    class="confidence-indicator"
                    :class="getConfidenceClass(notification)"
                  >
                    {{ formatConfidence(getConfidenceValue(notification)) }}
                  </span>
                </div>
              </div>
              
              <div class="notification-actions">
                <button 
                  v-if="!notification.read" 
                  class="action-button read" 
                  @click.stop="markAsRead(notification.id)"
                  title="Mark as Read"
                >
                  <font-awesome-icon icon="check" />
                </button>
                <button 
                  class="action-button delete" 
                  @click.stop="confirmDelete(notification.id)"
                  title="Delete"
                >
                  <font-awesome-icon icon="times" />
                </button>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </section>
      
      <!-- Right panel: Notification details -->
      <section class="details-section" v-if="selectedNotification || isMobile">
        <Transition name="fade" mode="out-in">
          <div v-if="!selectedNotification && isMobile" class="empty-details">
            <div class="empty-details-icon">
              <font-awesome-icon icon="clipboard" />
            </div>
            <p>Select a notification to view details</p>
          </div>
          
          <div v-else-if="selectedNotification" class="details-content">
            <div class="details-header">
              <div class="header-left">
                <button v-if="isMobile" class="back-button" @click="clearSelection">
                  <font-awesome-icon icon="arrow-left" />
                  <span>Back</span>
                </button>
                <h2 class="details-title">{{ getNotificationDetailTitle() }}</h2>
              </div>
              
              <div class="details-actions">
                <button 
                  v-if="!selectedNotification.read" 
                  class="action-button primary" 
                  @click="markAsRead(selectedNotification.id)"
                >
                  <font-awesome-icon icon="check" />
                  <span>Mark as Read</span>
                </button>
                <button 
                  class="action-button secondary" 
                  @click="prepareEditForm"
                >
                  <font-awesome-icon icon="edit" />
                  <span>Edit</span>
                </button>
                <button 
                  class="action-button warning" 
                  @click="confirmDelete(selectedNotification.id)"
                >
                  <font-awesome-icon icon="trash-alt" />
                  <span>Delete</span>
                </button>
                
                <button 
                  v-if="isAdmin" 
                  class="action-button forward" 
                  @click="openAgentSelector"
                >
                  <font-awesome-icon icon="share" />
                  <span>Forward</span>
                </button>
              </div>
            </div>
            
            <!-- Notification details content -->
            <div class="details-body">
              <div class="details-card">
                <h3 class="card-title">
                  <font-awesome-icon icon="info-circle" />
                  <span>Basic Information</span>
                </h3>
                
                <div class="details-fields">
                  <div class="detail-field">
                    <span class="field-label">Type:</span>
                    <span class="field-value">{{ selectedNotification.event_type }}</span>
                  </div>
                  <div class="detail-field">
                    <span class="field-label">Stream URL:</span>
                    <a 
                      :href="selectedNotification.room_url" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      class="field-link"
                    >
                      {{ truncateUrl(selectedNotification.room_url) }}
                      <font-awesome-icon icon="external-link-alt" class="external-icon" />
                    </a>
                  </div>
                  <div class="detail-field">
                    <span class="field-label">Timestamp:</span>
                    <span class="field-value">{{ formatTimestamp(selectedNotification.timestamp, true) }}</span>
                  </div>
                  <div class="detail-field">
                    <span class="field-label">Platform:</span>
                    <span class="field-value platform-badge">{{ selectedNotification.details?.platform || 'Unknown' }}</span>
                  </div>
                  <div class="detail-field">
                    <span class="field-label">Streamer:</span>
                    <span class="field-value">{{ selectedNotification.details?.streamer_name || 'Unknown' }}</span>
                  </div>
                  <div v-if="selectedNotification.assigned_agent" class="detail-field">
                    <span class="field-label">Assigned Agent:</span>
                    <span class="field-value agent-badge">{{ selectedNotification.assigned_agent }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Detection-specific details -->
              <div v-if="isVisualDetection" class="details-card">
                <h3 class="card-title">
                  <font-awesome-icon icon="camera" />
                  <span>Visual Detection Details</span>
                </h3>
                
                <div 
                  v-if="hasDetections" 
                  class="detection-results"
                >
                  <div class="detection-classes">
                    <div 
                      v-for="(detection, index) in getDetections" 
                      :key="index"
                      class="detection-class-item"
                      :class="getConfidenceClassForValue(detection.confidence)"
                    >
                      <span class="class-name">{{ detection.class }}</span>
                      <span class="confidence-badge">
                        {{ formatConfidence(detection.confidence) }}
                      </span>
                    </div>
                  </div>
                  
                  <div 
                    v-if="hasAnnotatedImage"
                    class="detection-image-container"
                  >
                    <img 
                      :src="getAnnotatedImageSrc"
                      alt="Detection Image"
                      class="detection-image"
                      @click="openImageModal(selectedNotification.details.annotated_image)"
                    />
                    <div class="image-caption">
                      <font-awesome-icon icon="search-plus" />
                      <span>Click to enlarge</span>
                    </div>
                  </div>
                </div>
                
                <div v-else class="no-details-message">
                  <font-awesome-icon icon="info-circle" />
                  <span>No detection details available</span>
                </div>
              </div>
              
              <div v-if="isChatDetection" class="details-card">
                <h3 class="card-title">
                  <font-awesome-icon icon="comment-alt" />
                  <span>Chat Detection Details</span>
                </h3>
                
                <div class="chat-details">
                  <div class="chat-message-container">
                    <h4 class="chat-message-heading">Message Content:</h4>
                    <div class="chat-message-content">
                      <p>{{ getChatMessage }}</p>
                    </div>
                  </div>
                  
                  <div 
                    v-if="hasFlaggedKeywords"
                    class="keywords-container"
                  >
                    <h4 class="keywords-heading">Flagged Keywords:</h4>
                    <div class="keyword-tags">
                      <span 
                        v-for="(keyword, index) in getFlaggedKeywords" 
                        :key="index"
                        class="keyword-tag"
                      >
                        {{ keyword }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="isAudioDetection" class="details-card">
                <h3 class="card-title">
                  <font-awesome-icon icon="microphone" />
                  <span>Audio Detection Details</span>
                </h3>
                
                <div class="audio-details">
                  <div class="transcript-container">
                    <h4 class="transcript-heading">Transcript:</h4>
                    <div class="transcript-content">
                      <p>{{ getTranscript }}</p>
                    </div>
                  </div>
                  
                  <div v-if="hasAudioKeyword" class="audio-keyword-container">
                    <h4 class="keyword-heading">Flagged Keyword:</h4>
                    <span class="keyword-tag highlighted">{{ getAudioKeyword }}</span>
                  </div>
                  
                  <div v-if="hasSentimentScore" class="sentiment-container">
                    <h4 class="sentiment-heading">Sentiment Analysis:</h4>
                    <div class="sentiment-meter">
                      <div class="sentiment-bar">
                        <div 
                          class="sentiment-value" 
                          :style="{ width: getSentimentPercentage, backgroundColor: getSentimentColor }"
                        ></div>
                      </div>
                      <div class="sentiment-labels">
                        <span>Negative</span>
                        <span>Neutral</span>
                        <span>Positive</span>
                      </div>
                    </div>
                    <div class="sentiment-score">Score: {{ getSentimentScore }}</div>
                  </div>
                </div>
              </div>
              
              <!-- Raw JSON (admin only) -->
              <div v-if="isAdmin" class="details-card">
                <div class="card-header-with-action">
                  <h3 class="card-title">
                    <font-awesome-icon icon="code" />
                    <span>Raw Data</span>
                  </h3>
                  
                  <button class="toggle-button" @click="toggleRawData">
                    {{ showRawJson ? 'Hide' : 'Show' }} Raw JSON
                  </button>
                </div>
                
                <div v-if="showRawJson" class="raw-data-container">
                  <pre class="json-content">{{ getFormattedJsonData }}</pre>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </section>
    </div>
    
    <!-- Modal components -->
    <Teleport to="body">
      <!-- Delete confirmation modal -->
      <Transition name="modal">
        <div v-if="isDeleteModalOpen" class="modal-overlay" @click="cancelDelete">
          <div class="modal-dialog" @click.stop>
            <div class="modal-header">
              <h3>Confirm Delete</h3>
              <button class="close-button" @click="cancelDelete">
                <font-awesome-icon icon="times" />
              </button>
            </div>
            <div class="modal-body">
              <p v-if="deleteMultiple">Are you sure you want to delete all notifications? This action cannot be undone.</p>
              <p v-else>Are you sure you want to delete this notification? This action cannot be undone.</p>
            </div>
            <div class="modal-footer">
              <button class="button secondary" @click="cancelDelete">Cancel</button>
              <button class="button warning" @click="confirmDeleteAction">Delete</button>
            </div>
          </div>
        </div>
      </Transition>
      
      <!-- Agent selection modal -->
      <Transition name="modal">
        <div v-if="isAgentDropdownOpen" class="modal-overlay" @click="closeAgentSelector">
          <div class="modal-dialog" @click.stop>
            <div class="modal-header">
              <h3>Forward to Agent</h3>
              <button class="close-button" @click="closeAgentSelector">
                <font-awesome-icon icon="times" />
              </button>
            </div>
            
            <div class="modal-body">
              <div v-if="loading" class="loading-agents">
                <div class="spinner small"></div>
                <p>Loading agents...</p>
              </div>
              
              <div v-else-if="!agents.length" class="no-agents">
                <font-awesome-icon icon="user-slash" />
                <p>No agents available</p>
              </div>
              
              <div v-else class="agents-list">
                <div 
                  v-for="agent in agents" 
                  :key="agent.id" 
                  class="agent-list-item"
                  @click="forwardNotification(agent.id)"
                >
                  <div class="agent-status" :class="agent.online ? 'online' : 'offline'"></div>
                  <div class="agent-details">
                    <div class="agent-name">{{ agent.username }}</div>
                    <div class="agent-email">{{ agent.email || 'No email' }}</div>
                  </div>
                  <div class="forward-icon">
                    <font-awesome-icon icon="paper-plane" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
      
      <!-- Image modal -->
      <Transition name="modal">
        <div v-if="imageModalSrc" class="modal-overlay" @click="closeImageModal">
          <div class="image-modal-container" @click.stop>
            <div class="image-modal-header">
              <h3>Detection Image</h3>
              <button class="close-button" @click="closeImageModal">
                <font-awesome-icon icon="times" />
              </button>
            </div>
            <div class="image-modal-body">
              <img :src="imageModalSrc" alt="Detection Image" class="full-image" />
            </div>
          </div>
        </div>
      </Transition>
      
      <!-- Notification form modal -->
      <Transition name="modal">
        <div v-if="isFormModalOpen" class="modal-overlay" @click="closeForm">
          <div class="modal-dialog form-dialog" @click.stop>
            <div class="modal-header">
              <h3>{{ formAction === 'create' ? 'Create Notification' : 'Edit Notification' }}</h3>
              <button class="close-button" @click="closeForm">
                <font-awesome-icon icon="times" />
              </button>
            </div>
            
            <div class="modal-body">
              <form @submit.prevent="submitForm" class="notification-form">
                <div class="form-group">
                  <label for="event_type">Event Type</label>
                  <select id="event_type" v-model="form.event_type" required class="form-select">
                    <option value="object_detection">Visual Detection</option>
                    <option value="audio_detection">Audio Detection</option>
                    <option value="chat_detection">Chat Detection</option>
                    <option value="system_notification">System Notification</option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label for="room_url">Stream URL</label>
                  <input 
                    type="url" 
                    id="room_url" 
                    v-model="form.room_url" 
                    required 
                    placeholder="https://example.com/stream" 
                    class="form-input"
                  />
                </div>
                
                <div class="form-group">
                  <label for="platform">Platform</label>
                  <input 
                    type="text" 
                    id="platform" 
                    v-model="form.platform" 
                    placeholder="e.g., Twitch, YouTube" 
                    class="form-input"
                  />
                </div>
                
                <div class="form-group">
                  <label for="streamer">Streamer Name</label>
                  <input 
                    type="text" 
                    id="streamer" 
                    v-model="form.streamer_name" 
                    placeholder="Streamer username" 
                    class="form-input"
                  />
                </div>
                
                <div v-if="form.event_type === 'object_detection'" class="form-group">
                  <label for="detections">Detections (JSON format)</label>
                  <textarea 
                    id="detections" 
                    v-model="form.detections" 
                    placeholder='[{"class": "object_name", "confidence": 0.95}]' 
                    rows="3"
                    class="form-textarea"
                  ></textarea>
                </div>
                
                <div v-else-if="form.event_type === 'chat_detection'" class="form-group">
                  <label for="message">Chat Message</label>
                  <textarea 
                    id="message" 
                    v-model="form.message" 
                    placeholder="Chat message content" 
                    rows="3"
                    class="form-textarea"
                  ></textarea>
                  
                  <label for="keywords" class="mt-3">Keywords (comma separated)</label>
                  <input 
                    type="text" 
                    id="keywords" 
                    v-model="form.keywords" 
                    placeholder="keyword1, keyword2" 
                    class="form-input"
                  />
                </div>
                
                <div v-else-if="form.event_type === 'audio_detection'" class="form-group">
                  <label for="transcript">Audio Transcript</label>
                  <textarea 
                    id="transcript" 
                    v-model="form.transcript" 
                    placeholder="Transcript of detected audio" 
                    rows="3"
                    class="form-textarea"
                  ></textarea>
                  
                  <label for="audio_keyword" class="mt-3">Flagged Keyword</label>
                  <input 
                    type="text" 
                    id="audio_keyword" 
                    v-model="form.keyword" 
                    placeholder="Detected keyword" 
                    class="form-input"
                  />
                </div>
                
                <div class="form-actions">
                  <button type="button" class="button secondary" @click="closeForm">Cancel</button>
                  <button type="submit" class="button primary">
                    {{ formAction === 'create' ? 'Create' : 'Update' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
// Import from project's main implementation
import axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

export default {
  name: 'NotificationComponent',
  components: {
    FontAwesomeIcon
  },
  props: {
    // Optional user role, defaults to 'agent' if not provided
    userRole: {
      type: String,
      default: 'agent',
      validator: (value) => ['admin', 'agent'].includes(value)
    },
    // Pass custom notification fetch URL if needed
    notificationUrl: {
      type: String,
      default: '/api/notifications'
    },
    // Auto refresh interval in milliseconds, set to 0 to disable
    refreshInterval: {
      type: Number,
      default: 30000 // 30 seconds
    },
    // Enable dark mode (enabled by default)
    isDarkMode: {
      type: Boolean,
      default: true
    }
  },
  setup(props) {
    // State management
    const notifications = ref([]);
    const loading = ref(false);
    const error = ref(null);
    
    // UI state
    const mainFilter = ref('All');
    const detectionSubFilter = ref('Visual');
    const selectedNotification = ref(null);
    const isMenuOpen = ref(false);
    const isDeleteModalOpen = ref(false);
    const isAgentDropdownOpen = ref(false);
    const showRawJson = ref(false);
    const imageModalSrc = ref(null);
    const isFormModalOpen = ref(false);
    const deleteTargetId = ref(null);
    const deleteMultiple = ref(false);
    const soundEnabled = ref(true);
    const newNotificationIds = ref([]);
    const showFilterOptions = ref(false);
    const showSortOptions = ref(false);
    const isMobile = ref(window.innerWidth < 768);
    const refreshTimerId = ref(null);
    const agents = ref([]);
    
    // Form state
    const formAction = ref('create');
    const form = ref({
      event_type: 'system_notification',
      room_url: '',
      platform: '',
      streamer_name: '',
      message: '',
      keywords: '',
      transcript: '',
      keyword: '',
      detections: ''
    });
    
    // Filter and sort options
    const filterOptions = ref({
      visual: true,
      audio: true,
      chat: true,
      system: true
    });
    
    const sortOption = ref('newest');
    
    // Computed properties
    const isAdmin = computed(() => props.userRole === 'admin');
    
    const unreadCount = computed(() => {
      return notifications.value.filter(n => !n.read).length;
    });
    
    const hasUnreadNotifications = computed(() => unreadCount.value > 0);
    
    const hasNotifications = computed(() => notifications.value.length > 0);
    
    const filteredNotifications = computed(() => {
      // Apply main filters
      let filtered = [...notifications.value];
      
      if (mainFilter.value === 'Unread') {
        filtered = filtered.filter(n => !n.read);
      } else if (mainFilter.value === 'Detections') {
        filtered = filtered.filter(n => {
          if (!n.event_type) return false;
          
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
      
      // Apply type filters if enabled
      if (!(filterOptions.value.visual && filterOptions.value.audio && 
            filterOptions.value.chat && filterOptions.value.system)) {
        filtered = filtered.filter(n => {
          if (n.event_type === 'object_detection') return filterOptions.value.visual;
          if (n.event_type === 'audio_detection') return filterOptions.value.audio;
          if (n.event_type === 'chat_detection') return filterOptions.value.chat;
          return filterOptions.value.system; // Any other type is considered system
        });
      }
      
      // Apply sorting
      if (sortOption.value === 'newest') {
        filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      } else if (sortOption.value === 'oldest') {
        filtered.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
      } else if (sortOption.value === 'priority') {
        filtered.sort((a, b) => {
          // Sort by priority (unread first, then by type, then by recency)
          if (a.read !== b.read) return a.read ? 1 : -1;
          
          const priorityA = getNotificationPriorityValue(a);
          const priorityB = getNotificationPriorityValue(b);
          if (priorityA !== priorityB) return priorityB - priorityA;
          
          return new Date(b.timestamp) - new Date(a.timestamp);
        });
      }
      
      return filtered;
    });
    
    // Notification details helpers for selected notification
    const isVisualDetection = computed(() => {
      return selectedNotification.value?.event_type === 'object_detection';
    });
    
    const isChatDetection = computed(() => {
      return selectedNotification.value?.event_type === 'chat_detection';
    });
    
    const isAudioDetection = computed(() => {
      return selectedNotification.value?.event_type === 'audio_detection';
    });
    
    const hasDetections = computed(() => {
      return selectedNotification.value?.details?.detections?.length > 0;
    });
    
    const getDetections = computed(() => {
      return selectedNotification.value?.details?.detections || [];
    });
    
    const hasAnnotatedImage = computed(() => {
      return !!selectedNotification.value?.details?.annotated_image;
    });
    
    const getAnnotatedImageSrc = computed(() => {
      if (!hasAnnotatedImage.value) return '';
      return `data:image/png;base64,${selectedNotification.value.details.annotated_image}`;
    });
    
    const getChatMessage = computed(() => {
      return selectedNotification.value?.details?.message || 'No message content';
    });
    
    const hasFlaggedKeywords = computed(() => {
      return selectedNotification.value?.details?.keywords?.length > 0;
    });
    
    const getFlaggedKeywords = computed(() => {
      return selectedNotification.value?.details?.keywords || [];
    });
    
    const getTranscript = computed(() => {
      return selectedNotification.value?.details?.transcript || 'No transcript available';
    });
    
    const hasAudioKeyword = computed(() => {
      return !!selectedNotification.value?.details?.keyword;
    });
    
    const getAudioKeyword = computed(() => {
      return selectedNotification.value?.details?.keyword || '';
    });
    
    const hasSentimentScore = computed(() => {
      return typeof selectedNotification.value?.details?.sentiment_score === 'number';
    });
    
    const getSentimentScore = computed(() => {
      return selectedNotification.value?.details?.sentiment_score?.toFixed(2) || 0;
    });
    
    const getSentimentPercentage = computed(() => {
      if (!hasSentimentScore.value) return '50%';
      
      // Convert sentiment score from [-1, 1] to [0, 100]
      const score = parseFloat(getSentimentScore.value);
      const percentage = ((score + 1) / 2) * 100;
      return `${percentage}%`;
    });
    
    const getSentimentColor = computed(() => {
      if (!hasSentimentScore.value) return '#888';
      
      const score = parseFloat(getSentimentScore.value);
      if (score < -0.25) return 'var(--color-danger)';
      if (score > 0.25) return 'var(--color-success)';
      return 'var(--color-warning)';
    });
    
    const getFormattedJsonData = computed(() => {
      if (!selectedNotification.value?.details) return '{}';
      return JSON.stringify(selectedNotification.value.details, null, 2);
    });
    
    // API methods
    const fetchNotifications = async () => {
      try {
        loading.value = true;
        error.value = null;
        
        const response = await axios.get(props.notificationUrl);
        
        // Check for new notifications
        const previousIds = notifications.value.map(n => n.id);
        const newIds = response.data
          .filter(n => !previousIds.includes(n.id))
          .map(n => n.id);
        
        if (newIds.length > 0) {
          newNotificationIds.value = [...newIds];
          
          // Play sound if enabled
          if (soundEnabled.value && newIds.length > 0) {
            playNotificationSound();
          }
          
          // Clear new notification IDs after 5 seconds
          setTimeout(() => {
            newNotificationIds.value = [];
          }, 5000);
        }
        
        notifications.value = response.data;
      } catch (err) {
        console.error('Failed to fetch notifications:', err);
        error.value = 'Failed to load notifications. Please try again.';
      } finally {
        loading.value = false;
      }
    };
    
    const markAsRead = async (id) => {
      try {
        await axios.put(`/api/notifications/${id}/read`);
        
        // Update local state
        const notification = notifications.value.find(n => n.id === id);
        if (notification) {
          notification.read = true;
        }
      } catch (err) {
        console.error('Failed to mark notification as read:', err);
      }
    };
    
    const markAllAsRead = async () => {
      try {
        await axios.put('/api/notifications/read-all');
        
        // Update local state
        notifications.value.forEach(n => {
          n.read = true;
        });
      } catch (err) {
        console.error('Failed to mark all notifications as read:', err);
      }
    };
    
    const deleteNotification = async (id) => {
      try {
        await axios.delete(`/api/notifications/${id}`);
        
        // Update local state
        notifications.value = notifications.value.filter(n => n.id !== id);
        
        // Clear selection if the deleted notification was selected
        if (selectedNotification.value && selectedNotification.value.id === id) {
          selectedNotification.value = null;
        }
      } catch (err) {
        console.error('Failed to delete notification:', err);
      }
    };
    
    const deleteAllNotifications = async () => {
      try {
        await axios.delete('/api/notifications');
        
        // Update local state
        notifications.value = [];
        selectedNotification.value = null;
      } catch (err) {
        console.error('Failed to delete all notifications:', err);
      }
    };
    
    // Handler functions
    const handleMainFilterChange = (tab) => {
      mainFilter.value = tab;
      // Close the menu when changing filters
      isMenuOpen.value = false;
    };
    
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value;
      // Close other dropdown menus when menu is opened
      if (isMenuOpen.value) {
        showFilterOptions.value = false;
        showSortOptions.value = false;
      }
    };
    
    const toggleSound = () => {
      soundEnabled.value = !soundEnabled.value;
      isMenuOpen.value = false;
    };
    
    const selectNotification = (notification) => {
      selectedNotification.value = notification;
      
      // If the notification is unread, mark it as read
      if (notification && !notification.read) {
        markAsRead(notification.id);
      }
    };
    
    const clearSelection = () => {
      selectedNotification.value = null;
    };
    
    const isNotificationSelected = (notification) => {
      return selectedNotification.value && selectedNotification.value.id === notification.id;
    };
    
    const confirmDelete = (id) => {
      deleteTargetId.value = id;
      deleteMultiple.value = false;
      isDeleteModalOpen.value = true;
    };
    
    const confirmDeleteAll = () => {
      deleteMultiple.value = true;
      isDeleteModalOpen.value = true;
    };
    
    const cancelDelete = () => {
      isDeleteModalOpen.value = false;
      deleteTargetId.value = null;
      deleteMultiple.value = false;
    };
    
    const confirmDeleteAction = async () => {
      try {
        if (deleteMultiple.value) {
          await deleteAllNotifications();
        } else if (deleteTargetId.value) {
          await deleteNotification(deleteTargetId.value);
        }
      } catch (err) {
        console.error('Failed to delete notification(s):', err);
      } finally {
        isDeleteModalOpen.value = false;
        deleteTargetId.value = null;
        deleteMultiple.value = false;
      }
    };
    
    const openAgentSelector = async () => {
      isAgentDropdownOpen.value = true;
      
      try {
        const response = await axios.get('/api/agents');
        agents.value = response.data;
      } catch (err) {
        console.error('Failed to fetch agents:', err);
        agents.value = [];
      }
    };
    
    const closeAgentSelector = () => {
      isAgentDropdownOpen.value = false;
    };
    
    const forwardNotification = async (agentId) => {
      if (!selectedNotification.value) return;
      
      try {
        await axios.post(`/api/notifications/${selectedNotification.value.id}/forward`, {
          agent_id: agentId
        });
        
        // Update UI to show forwarded status
        if (selectedNotification.value.details) {
          const agent = agents.value.find(a => a.id === agentId);
          selectedNotification.value.details.assigned_agent = agent?.username || 'Unknown Agent';
        }
        
        isAgentDropdownOpen.value = false;
      } catch (err) {
        console.error('Failed to forward notification:', err);
      }
    };
    
    const openImageModal = (imageBase64) => {
      imageModalSrc.value = `data:image/png;base64,${imageBase64}`;
    };
    
    const closeImageModal = () => {
      imageModalSrc.value = null;
    };
    
    const prepareCreateForm = () => {
      formAction.value = 'create';
      form.value = {
        event_type: 'system_notification',
        room_url: '',
        platform: '',
        streamer_name: '',
        message: '',
        keywords: '',
        transcript: '',
        keyword: '',
        detections: ''
      };
      isFormModalOpen.value = true;
      isMenuOpen.value = false;
    };
    
    const prepareEditForm = () => {
      if (!selectedNotification.value) return;
      
      formAction.value = 'edit';
      
      // Extract values from the selected notification
      const details = selectedNotification.value.details || {};
      form.value = {
        event_type: selectedNotification.value.event_type,
        room_url: selectedNotification.value.room_url,
        platform: details.platform || '',
        streamer_name: details.streamer_name || '',
        // Chat details
        message: details.message || '',
        keywords: Array.isArray(details.keywords) ? details.keywords.join(', ') : '',
        // Audio details
        transcript: details.transcript || '',
        keyword: details.keyword || '',
        // Visual details
        detections: details.detections ? JSON.stringify(details.detections) : ''
      };
      
      isFormModalOpen.value = true;
    };
    
    const closeForm = () => {
      isFormModalOpen.value = false;
    };
    
    const submitForm = async () => {
      try {
        // Prepare the notification data
        const notificationData = {
          event_type: form.value.event_type,
          room_url: form.value.room_url,
          details: {
            platform: form.value.platform,
            streamer_name: form.value.streamer_name
          }
        };
        
        // Add type-specific details
        if (form.value.event_type === 'object_detection') {
          try {
            notificationData.details.detections = form.value.detections ? 
              JSON.parse(form.value.detections) : [];
          } catch (e) {
            console.error('Invalid JSON for detections:', e);
            notificationData.details.detections = [];
          }
        } else if (form.value.event_type === 'chat_detection') {
          notificationData.details.message = form.value.message;
          notificationData.details.keywords = form.value.keywords
            .split(',')
            .map(k => k.trim())
            .filter(k => k.length > 0);
        } else if (form.value.event_type === 'audio_detection') {
          notificationData.details.transcript = form.value.transcript;
          notificationData.details.keyword = form.value.keyword;
        }
        
        if (formAction.value === 'create') {
          await axios.post('/api/notifications', notificationData);
        } else {
          await axios.put(`/api/notifications/${selectedNotification.value.id}`, notificationData);
        }
        
        // Refresh notifications
        await fetchNotifications();
        
        // Close the form
        isFormModalOpen.value = false;
      } catch (err) {
        console.error('Failed to submit notification form:', err);
      }
    };
    
    const toggleRawData = () => {
      showRawJson.value = !showRawJson.value;
    };
    
    const changeSortOption = (option) => {
      sortOption.value = option;
      showSortOptions.value = false;
    };
    
    // Utility functions
    const playNotificationSound = () => {
      // In a real implementation, this would play a sound
      console.log('Playing notification sound');
    };
    
    // Helper functions
    const getNotificationColor = (notification) => {
      if (!notification || !notification.event_type) return '#999';
      
      switch (notification.event_type) {
        case 'object_detection': return 'var(--color-danger)';
        case 'audio_detection': return 'var(--color-warning)';
        case 'chat_detection': return 'var(--color-primary)';
        default: return 'var(--color-info)';
      }
    };
    
    const getNotificationType = (notification) => {
      if (!notification || !notification.event_type) return 'Unknown';
      
      switch (notification.event_type) {
        case 'object_detection': return 'Visual Detection';
        case 'audio_detection': return 'Audio Detection';
        case 'chat_detection': return 'Chat Detection';
        case 'system_notification': return 'System Notification';
        default: return notification.event_type.replace(/_/g, ' ');
      }
    };
    
    const getNotificationTypeIcon = (notification) => {
      if (!notification || !notification.event_type) return 'bell';
      
      switch (notification.event_type) {
        case 'object_detection': return 'camera';
        case 'audio_detection': return 'microphone';
        case 'chat_detection': return 'comment-alt';
        case 'system_notification': return 'info-circle';
        default: return 'bell';
      }
    };
    
    const getDetectionTypeIcon = (type) => {
      switch (type) {
        case 'Visual': return 'camera';
        case 'Audio': return 'microphone';
        case 'Chat': return 'comment-alt';
        default: return 'bell';
      }
    };
    
    const getNotificationMessage = (notification) => {
      if (!notification || !notification.details) return 'No details available';
      
      const details = notification.details;
      
      switch (notification.event_type) {
        case 'object_detection':
          if (details.detections && details.detections.length > 0) {
            const detection = details.detections[0];
            return `Detected ${detection.class} (${formatConfidence(detection.confidence)})`;
          }
          return 'Object detected in stream';
          
        case 'audio_detection':
          if (details.keyword) {
            return `Flagged keyword detected: "${details.keyword}"`;
          } else if (details.transcript) {
            return `Audio transcript: "${truncateText(details.transcript, 60)}"`;
          }
          return 'Audio detection alert';
          
        case 'chat_detection':
          if (details.message) {
            return `Chat message: "${truncateText(details.message, 60)}"`;
          }
          return 'Flagged chat message detected';
          
        case 'system_notification':
          return details.message || 'System notification';
          
        default:
          return 'Notification received';
      }
    };
    
    const getNotificationDetailTitle = () => {
      if (!selectedNotification.value) return '';
      
      return getNotificationType(selectedNotification.value);
    };
    
    const getNotificationPriority = (notification) => {
      if (!notification) return 'low';
      
      // Unread notifications always have higher priority
      if (!notification.read) {
        if (notification.event_type === 'object_detection') {
          // Check if confidence is high
          if (notification.details?.detections?.[0]?.confidence > 0.85) {
            return 'high';
          }
          return 'medium';
        }
        
        if (notification.event_type === 'chat_detection' || 
            notification.event_type === 'audio_detection') {
          return 'medium';
        }
      }
      
      return 'low';
    };
    
    const getNotificationPriorityValue = (notification) => {
      const priority = getNotificationPriority(notification);
      switch (priority) {
        case 'high': return 3;
        case 'medium': return 2;
        case 'low': return 1;
        default: return 0;
      }
    };
    
    const getNotificationPlatform = (notification) => {
      return notification.details?.platform || 'Unknown';
    };
    
    const getStreamerName = (notification) => {
      return notification.details?.streamer_name || 'Unknown';
    };
    
    const shouldShowConfidence = (notification) => {
      return notification.event_type === 'object_detection' && 
             notification.details?.detections?.length > 0;
    };
    
    const getConfidenceValue = (notification) => {
      if (!notification.details?.detections?.length) return 0;
      return notification.details.detections[0].confidence;
    };
    
    const getConfidenceClass = (notification) => {
      const confidence = getConfidenceValue(notification);
      return getConfidenceClassForValue(confidence);
    };
    
    const getConfidenceClassForValue = (confidence) => {
      if (confidence >= 0.85) return 'high';
      if (confidence >= 0.7) return 'medium';
      return 'low';
    };
    
    const formatConfidence = (confidence) => {
      if (confidence === undefined || confidence === null) return 'N/A';
      return `${Math.round(confidence * 100)}%`;
    };
    
    const formatTimestamp = (timestamp, fullFormat = false) => {
      if (!timestamp) return 'Unknown';
      
      const date = new Date(timestamp);
      
      if (fullFormat) {
        return date.toLocaleString(undefined, {
          year: 'numeric', 
          month: 'short', 
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
      }
      
      // For timestamps that are today
      const now = new Date();
      const isToday = date.getDate() === now.getDate() && 
                     date.getMonth() === now.getMonth() && 
                     date.getFullYear() === now.getFullYear();
      
      if (isToday) {
        return date.toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      
      // For timestamps in the last 7 days
      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
      
      if (date > oneWeekAgo) {
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        return `${days[date.getDay()]} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
      }
      
      // For older timestamps
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric'
      });
    };
    
    const truncateUrl = (url, maxLength = 40) => {
      if (!url) return 'No URL';
      if (url.length <= maxLength) return url;
      
      return url.substring(0, maxLength - 3) + '...';
    };
    
    const truncateText = (text, maxLength = 100) => {
      if (!text) return '';
      if (text.length <= maxLength) return text;
      
      return text.substring(0, maxLength - 3) + '...';
    };
    
    // Setup real-time updates and auto-refresh
    const setupAutoRefresh = () => {
      if (props.refreshInterval > 0) {
        refreshTimerId.value = setInterval(async () => {
          await fetchNotifications();
        }, props.refreshInterval);
      }
    };
    
    const cleanupAutoRefresh = () => {
      if (refreshTimerId.value) {
        clearInterval(refreshTimerId.value);
      }
    };
    
    // Handle window resize for mobile detection
    const handleResize = () => {
      isMobile.value = window.innerWidth < 768;
    };
    
    // Lifecycle hooks
    onMounted(async () => {
      // Initial data loading
      await fetchNotifications();
      
      // Set up auto-refresh
      setupAutoRefresh();
      
      // Listen for resize events
      window.addEventListener('resize', handleResize);
    });
    
    onBeforeUnmount(() => {
      // Clean up auto-refresh
      cleanupAutoRefresh();
      
      // Remove resize listener
      window.removeEventListener('resize', handleResize);
    });
    
    return {
      // State
      notifications,
      filteredNotifications,
      selectedNotification,
      mainFilter,
      detectionSubFilter,
      isMenuOpen,
      isDeleteModalOpen,
      isAgentDropdownOpen,
      isFormModalOpen,
      showRawJson,
      loading,
      error,
      imageModalSrc,
      formAction,
      form,
      unreadCount,
      soundEnabled,
      newNotificationIds,
      agents,
      filterOptions,
      sortOption,
      showFilterOptions,
      showSortOptions,
      deleteMultiple,
      isMobile,
      isAdmin,
      hasUnreadNotifications,
      hasNotifications,
      
      // Detail computed properties
      isVisualDetection,
      isChatDetection,
      isAudioDetection,
      hasDetections,
      getDetections,
      hasAnnotatedImage,
      getAnnotatedImageSrc,
      getChatMessage,
      hasFlaggedKeywords,
      getFlaggedKeywords,
      getTranscript,
      hasAudioKeyword,
      getAudioKeyword,
      hasSentimentScore,
      getSentimentScore,
      getSentimentPercentage,
      getSentimentColor,
      getFormattedJsonData,
      
      // Methods
      fetchNotifications,
      markAsRead,
      markAllAsRead,
      deleteNotification,
      deleteAllNotifications,
      handleMainFilterChange,
      toggleMenu,
      toggleSound,
      selectNotification,
      clearSelection,
      isNotificationSelected,
      confirmDelete,
      confirmDeleteAll,
      cancelDelete,
      confirmDeleteAction,
      openAgentSelector,
      closeAgentSelector,
      forwardNotification,
      openImageModal,
      closeImageModal,
      prepareCreateForm,
      prepareEditForm,
      closeForm,
      submitForm,
      toggleRawData,
      changeSortOption,
      
      // Helper functions
      getNotificationColor,
      getNotificationType,
      getNotificationTypeIcon,
      getDetectionTypeIcon,
      getNotificationMessage,
      getNotificationDetailTitle,
      getNotificationPriority,
      getNotificationPlatform,
      getStreamerName,
      shouldShowConfidence,
      getConfidenceValue,
      getConfidenceClass,
      getConfidenceClassForValue,
      formatConfidence,
      formatTimestamp,
      truncateUrl,
      truncateText
    };
  }
};
</script>

<style scoped>
/* ---------- Variables ---------- */
:root {
  --color-primary: #4f46e5;
  --color-primary-hover: #4338ca;
  --color-primary-light: #eef2ff;
  
  --color-secondary: #64748b;
  --color-secondary-hover: #475569;
  --color-secondary-light: #f8fafc;
  
  --color-success: #10b981;
  --color-success-hover: #059669;
  --color-success-light: #ecfdf5;
  
  --color-warning: #f59e0b;
  --color-warning-hover: #d97706;
  --color-warning-light: #fffbeb;
  
  --color-danger: #ef4444;
  --color-danger-hover: #dc2626;
  --color-danger-light: #fef2f2;
  
  --color-info: #3b82f6;
  --color-info-hover: #2563eb;
  --color-info-light: #eff6ff;
  
  --color-gray-50: #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-200: #e5e7eb;
  --color-gray-300: #d1d5db;
  --color-gray-400: #9ca3af;
  --color-gray-500: #6b7280;
  --color-gray-600: #4b5563;
  --color-gray-700: #374151;
  --color-gray-800: #1f2937;
  --color-gray-900: #111827;
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  
  --border-radius-sm: 0.25rem;
  --border-radius: 0.375rem;
  --border-radius-md: 0.5rem;
  --border-radius-lg: 0.75rem;
  --border-radius-xl: 1rem;
  
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 1.875rem;
  
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  
  --transition-fast: 150ms;
  --transition-normal: 250ms;
  --transition-slow: 350ms;
}

/* ---------- Base Styles ---------- */
.notifications-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--color-gray-50);
  color: var(--color-gray-900);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.notifications-container.dark-mode {
  background-color: var(--color-gray-900);
  color: var(--color-gray-50);
}

/* ---------- Top Navigation ---------- */
.top-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  background-color: white;
  border-bottom: 1px solid var(--color-gray-200);
  position: relative;
  z-index: 10;
  box-shadow: var(--shadow-sm);
}

.dark-mode .top-navigation {
  background-color: var(--color-gray-800);
  border-bottom-color: var(--color-gray-700);
}

.tab-filters {
  display: flex;
  gap: var(--space-2);
}

.tab-button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: none;
  border-radius: var(--border-radius);
  color: var(--color-gray-600);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.tab-button:hover {
  background-color: var(--color-gray-100);
  color: var(--color-gray-900);
}

.tab-button.active {
  background-color: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.dark-mode .tab-button {
  color: var(--color-gray-400);
}

.dark-mode .tab-button:hover {
  background-color: var(--color-gray-700);
  color: var(--color-gray-100);
}

.dark-mode .tab-button.active {
  background-color: rgba(79, 70, 229, 0.2);
  color: #818cf8;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 var(--space-1);
  border-radius: 9999px;
  background-color: var(--color-primary);
  color: white;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.dark-mode .count-badge {
  background-color: #6366f1;
}

.action-controls {
  display: flex;
  gap: var(--space-2);
  position: relative;
}

.icon-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: var(--border-radius);
  background-color: transparent;
  color: var(--color-gray-600);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.icon-button:hover {
  background-color: var(--color-gray-100);
  color: var(--color-gray-900);
}

.icon-button.small {
  width: 2rem;
  height: 2rem;
  font-size: var(--font-size-sm);
}

.icon-button.x-small {
  width: 1.5rem;
  height: 1.5rem;
  font-size: var(--font-size-xs);
}

.dark-mode .icon-button {
  color: var(--color-gray-400);
}

.dark-mode .icon-button:hover {
  background-color: var(--color-gray-700);
  color: var(--color-gray-100);
}

.icon-button.refresh:hover {
  color: var(--color-info);
}

.actions-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 240px;
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-gray-200);
  z-index: 20;
  margin-top: var(--space-2);
  overflow: hidden;
}

.dark-mode .actions-dropdown {
  background-color: var(--color-gray-800);
  border-color: var(--color-gray-700);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  text-align: left;
  background: none;
  border: none;
  color: var(--color-gray-700);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background-color var(--transition-fast) ease;
}

.dropdown-item:hover {
  background-color: var(--color-gray-100);
}

.dropdown-item:active {
  background-color: var(--color-gray-200);
}

.dropdown-item:disabled {
  color: var(--color-gray-400);
  cursor: not-allowed;
}

.dark-mode .dropdown-item {
  color: var(--color-gray-300);
}

.dark-mode .dropdown-item:hover {
  background-color: var(--color-gray-700);
}

.dark-mode .dropdown-item:active {
  background-color: var(--color-gray-600);
}

.dark-mode .dropdown-item:disabled {
  color: var(--color-gray-600);
}

/* ---------- Detection Sub Filters ---------- */
.detection-filters {
  display: flex;
  background-color: white;
  border-bottom: 1px solid var(--color-gray-200);
  padding: var(--space-2) var(--space-4);
  gap: var(--space-3);
}

.dark-mode .detection-filters {
  background-color: var(--color-gray-800);
  border-bottom-color: var(--color-gray-700);
}

.detection-filter-button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--border-radius);
  background: none;
  border: 1px solid var(--color-gray-300);
  color: var(--color-gray-600);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.detection-filter-button:hover {
  background-color: var(--color-gray-100);
  color: var(--color-gray-900);
  border-color: var(--color-gray-400);
}

.detection-filter-button.active {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.dark-mode .detection-filter-button {
  border-color: var(--color-gray-600);
  color: var(--color-gray-400);
}

.dark-mode .detection-filter-button:hover {
  background-color: var(--color-gray-700);
  color: var(--color-gray-100);
  border-color: var(--color-gray-500);
}

.dark-mode .detection-filter-button.active {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.filter-icon {
  font-size: var(--font-size-sm);
}

/* ---------- Main Content Area ---------- */
.content-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ---------- Notifications Section ---------- */
.notifications-section {
  width: 35%;
  min-width: 350px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-gray-200);
  background-color: white;
  overflow: hidden;
  transition: width var(--transition-normal) ease;
}

.notifications-section.expanded {
  width: 100%;
}

.dark-mode .notifications-section {
  background-color: var(--color-gray-800);
  border-right-color: var(--color-gray-700);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-gray-200);
}

.dark-mode .section-header {
  border-bottom-color: var(--color-gray-700);
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
  margin: 0;
}

.dark-mode .section-title {
  color: var(--color-gray-100);
}

.notification-count {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-normal);
  color: var(--color-gray-500);
}

.dark-mode .notification-count {
  color: var(--color-gray-400);
}

.section-actions {
  display: flex;
  gap: var(--space-2);
}

/* ---------- Filter and Sort Dropdowns ---------- */
.dropdown-panel {
  position: absolute;
  top: 50px;
  right: 20px;
  width: 240px;
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-gray-200);
  z-index: 15;
  overflow: hidden;
}

.dark-mode .dropdown-panel {
  background-color: var(--color-gray-800);
  border-color: var(--color-gray-700);
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-gray-200);
}

.dark-mode .dropdown-header {
  border-bottom-color: var(--color-gray-700);
}

.dropdown-header h3 {
  margin: 0;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-900);
}

.dark-mode .dropdown-header h3 {
  color: var(--color-gray-100);
}

.filter-options, .sort-options {
  padding: var(--space-2);
}

.filter-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2);
  cursor: pointer;
  color: var(--color-gray-700);
  font-size: var(--font-size-sm);
}

.filter-option:hover {
  background-color: var(--color-gray-100);
  border-radius: var(--border-radius);
}

.dark-mode .filter-option {
  color: var(--color-gray-300);
}

.dark-mode .filter-option:hover {
  background-color: var(--color-gray-700);
}

.sort-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2);
  background: none;
  border: none;
  text-align: left;
  color: var(--color-gray-700);
  font-size: var(--font-size-sm);
  cursor: pointer;
  border-radius: var(--border-radius);
}

.sort-option:hover {
  background-color: var(--color-gray-100);
}

.sort-option.active {
  background-color: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
}

.dark-mode .sort-option {
  color: var(--color-gray-300);
}

.dark-mode .sort-option:hover {
  background-color: var(--color-gray-700);
}

.dark-mode .sort-option.active {
  background-color: rgba(79, 70, 229, 0.2);
  color: #818cf8;
}

/* ---------- State Displays ---------- */
.state-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  text-align: center;
  min-height: 200px;
}

.loading-state .spinner {
  border: 3px solid var(--color-gray-200);
  border-top: 3px solid var(--color-primary);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-4);
}

.spinner.small {
  width: 24px;
  height: 24px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.dark-mode .loading-state .spinner {
  border-color: var(--color-gray-700);
  border-top-color: #818cf8;
}

.error-state {
  color: var(--color-danger);
}

.error-icon {
  font-size: 2rem;
  margin-bottom: var(--space-4);
}

.retry-button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-4);
  padding: var(--space-2) var(--space-4);
  background-color: var(--color-gray-100);
  border: none;
  border-radius: var(--border-radius);
  color: var(--color-gray-800);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.retry-button:hover {
  background-color: var(--color-gray-200);
}

.dark-mode .retry-button {
  background-color: var(--color-gray-700);
  color: var(--color-gray-200);
}

.dark-mode .retry-button:hover {
  background-color: var(--color-gray-600);
}

.empty-state {
  color: var(--color-gray-500);
}

.empty-icon, .empty-details-icon {
  font-size: 2.5rem;
  margin-bottom: var(--space-4);
  color: var(--color-gray-300);
}

.dark-mode .empty-icon, .dark-mode .empty-details-icon {
  color: var(--color-gray-600);
}

/* ---------- Notifications List ---------- */
.notifications-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.notification-item {
  display: flex;
  margin-bottom: var(--space-2);
  border-radius: var(--border-radius);
  background-color: white;
  border: 1px solid var(--color-gray-200);
  overflow: hidden;
  transition: all var(--transition-fast) ease;
  position: relative;
  cursor: pointer;
}

.notification-item:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
  border-color: var(--color-gray-300);
}

.notification-item.selected {
  border-color: var(--color-primary);
  background-color: var(--color-primary-light);
}

.notification-item.unread {
  background-color: white;
  font-weight: var(--font-weight-medium);
}

.notification-item.read {
  background-color: var(--color-gray-50);
  opacity: 0.9;
}

.notification-item.high-priority {
  border-left: 3px solid var(--color-danger);
}

.notification-item.medium-priority {
  border-left: 3px solid var(--color-warning);
}

.notification-item.new {
  animation: highlight 2s ease-out;
}

@keyframes highlight {
  0% { background-color: var(--color-primary-light); }
  100% { background-color: white; }
}

.dark-mode .notification-item {
  background-color: var(--color-gray-800);
  border-color: var(--color-gray-700);
}

.dark-mode .notification-item:hover {
  border-color: var(--color-gray-600);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1);
}

.dark-mode .notification-item.selected {
  border-color: #818cf8;
  background-color: rgba(79, 70, 229, 0.2);
}

.dark-mode .notification-item.unread {
  background-color: var(--color-gray-800);
}

.dark-mode .notification-item.read {
  background-color: var(--color-gray-900);
}

.dark-mode .notification-item.new {
  animation: dark-highlight 2s ease-out;
}

@keyframes dark-highlight {
  0% { background-color: rgba(79, 70, 229, 0.2); }
  100% { background-color: var(--color-gray-800); }
}

.notification-status {
  width: 4px;
  min-height: 100%;
  background-color: var(--color-primary);
}

.notification-details {
  flex: 1;
  padding: var(--space-3);
  overflow: hidden;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}

.notification-type {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-900);
}

.dark-mode .notification-type {
  color: var(--color-gray-100);
}

.type-icon {
  color: var(--color-gray-500);
}

.dark-mode .type-icon {
  color: var(--color-gray-400);
}

.notification-time {
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
}

.dark-mode .notification-time {
  color: var(--color-gray-400);
}

.notification-summary {
  margin-bottom: var(--space-2);
  font-size: var(--font-size-sm);
  line-height: 1.4;
  color: var(--color-gray-800);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.dark-mode .notification-summary {
  color: var(--color-gray-300);
}

.notification-metadata {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
}

.dark-mode .notification-metadata {
  color: var(--color-gray-400);
}

.source-info {
  display: flex;
  align-items: center;
}

.separator {
  margin: 0 var(--space-1);
}

.platform {
  text-transform: capitalize;
}

.confidence-indicator {
  padding: var(--space-1) var(--space-2);
  border-radius: var(--border-radius-sm);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-xs);
  background-color: var(--color-gray-200);
}

.confidence-indicator.high {
  background-color: var(--color-success-light);
  color: var(--color-success);
}

.confidence-indicator.medium {
  background-color: var(--color-warning-light);
  color: var(--color-warning);
}

.confidence-indicator.low {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
}

.dark-mode .confidence-indicator {
  background-color: var(--color-gray-700);
}

.dark-mode .confidence-indicator.high {
  background-color: rgba(16, 185, 129, 0.2);
  color: #34d399;
}

.dark-mode .confidence-indicator.medium {
  background-color: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.dark-mode .confidence-indicator.low {
  background-color: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.notification-actions {
  display: flex;
  flex-direction: column;
  padding: var(--space-1);
  opacity: 0;
  transition: opacity var(--transition-fast) ease;
}

.notification-item:hover .notification-actions {
  opacity: 1;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin-bottom: var(--space-1);
  border-radius: var(--border-radius-sm);
  background-color: var(--color-gray-100);
  color: var(--color-gray-600);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.action-button:hover {
  background-color: var(--color-gray-200);
  color: var(--color-gray-900);
}

.action-button.read:hover {
  background-color: var(--color-success-light);
  color: var(--color-success);
}

.action-button.delete:hover {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
}

.dark-mode .action-button {
  background-color: var(--color-gray-700);
  color: var(--color-gray-400);
}

.dark-mode .action-button:hover {
  background-color: var(--color-gray-600);
  color: var(--color-gray-200);
}

.dark-mode .action-button.read:hover {
  background-color: rgba(16, 185, 129, 0.2);
  color: #34d399;
}

.dark-mode .action-button.delete:hover {
  background-color: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

/* ---------- Details Section ---------- */
.details-section {
  flex: 1;
  overflow-y: auto;
  background-color: var(--color-gray-50);
  position: relative;
}

.dark-mode .details-section {
  background-color: var(--color-gray-900);
}

.empty-details {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--color-gray-500);
}

.dark-mode .empty-details {
  color: var(--color-gray-400);
}

.details-content {
  padding: var(--space-4);
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-6);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.back-button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background-color: transparent;
  border: 1px solid var(--color-gray-300);
  border-radius: var(--border-radius);
  color: var(--color-gray-700);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.back-button:hover {
  background-color: var(--color-gray-100);
  color: var(--color-gray-900);
}

.dark-mode .back-button {
  border-color: var(--color-gray-600);
  color: var(--color-gray-300);
}

.dark-mode .back-button:hover {
  background-color: var(--color-gray-700);
  color: var(--color-gray-100);
}

.details-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  margin: 0;
}

.dark-mode .details-title {
  color: var(--color-gray-100);
}

.details-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.action-button.primary, 
.action-button.secondary, 
.action-button.warning, 
.action-button.forward {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: auto;
  height: auto;
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-sm);
}

.action-button.primary {
  background-color: var(--color-primary);
  color: white;
}

.action-button.primary:hover {
  background-color: var(--color-primary-hover);
  color: white;
}

.action-button.secondary {
  background-color: var(--color-gray-200);
  color: var(--color-gray-700);
}

.action-button.secondary:hover {
  background-color: var(--color-gray-300);
  color: var(--color-gray-900);
}

.action-button.warning {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
}

.action-button.warning:hover {
  background-color: var(--color-danger);
  color: white;
}

.action-button.forward {
  background-color: var(--color-info-light);
  color: var(--color-info);
}

.action-button.forward:hover {
  background-color: var(--color-info);
  color: white;
}

.dark-mode .action-button.primary {
  background-color: #6366f1;
  color: white;
}

.dark-mode .action-button.primary:hover {
  background-color: #4f46e5;
}

.dark-mode .action-button.secondary {
  background-color: var(--color-gray-700);
  color: var(--color-gray-300);
}

.dark-mode .action-button.secondary:hover {
  background-color: var(--color-gray-600);
  color: var(--color-gray-100);
}

.dark-mode .action-button.warning {
  background-color: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.dark-mode .action-button.warning:hover {
  background-color: #ef4444;
  color: white;
}

.dark-mode .action-button.forward {
  background-color: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.dark-mode .action-button.forward:hover {
  background-color: #3b82f6;
  color: white;
}

/* ---------- Details Body ---------- */
.details-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.details-card {
  background-color: white;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.dark-mode .details-card {
  background-color: var(--color-gray-800);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.1);
}

.card-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-gray-200);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
}

.dark-mode .card-title {
  border-bottom-color: var(--color-gray-700);
  color: var(--color-gray-100);
}

.card-header-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-gray-200);
}

.dark-mode .card-header-with-action {
  border-bottom-color: var(--color-gray-700);
}

.toggle-button {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  padding: 0;
}

.toggle-button:hover {
  text-decoration: underline;
}

.dark-mode .toggle-button {
  color: #818cf8;
}

.details-fields {
  padding: var(--space-4);
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-4);
}

.detail-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.field-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-500);
  text-transform: uppercase;
}

.dark-mode .field-label {
  color: var(--color-gray-400);
}

.field-value {
  font-size: var(--font-size-sm);
  color: var(--color-gray-900);
}

.dark-mode .field-value {
  color: var(--color-gray-200);
}

.field-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  text-decoration: none;
}

.field-link:hover {
  text-decoration: underline;
}

.dark-mode .field-link {
  color: #818cf8;
}

.external-icon {
  font-size: var(--font-size-xs);
}

.platform-badge, .agent-badge {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  text-transform: capitalize;
}

.platform-badge {
  background-color: var(--color-info-light);
  color: var(--color-info);
}

.agent-badge {
  background-color: var(--color-primary-light);
  color: var(--color-primary);
}

.dark-mode .platform-badge {
  background-color: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.dark-mode .agent-badge {
  background-color: rgba(79, 70, 229, 0.2);
  color: #818cf8;
}

/* ---------- Detection Details ---------- */
.detection-results {
  padding: var(--space-4);
}

.detection-classes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.detection-class-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--border-radius);
  background-color: var(--color-gray-100);
}

.detection-class-item.high {
  background-color: var(--color-success-light);
}

.detection-class-item.medium {
  background-color: var(--color-warning-light);
}

.detection-class-item.low {
  background-color: var(--color-danger-light);
}

.dark-mode .detection-class-item {
  background-color: var(--color-gray-700);
}

.dark-mode .detection-class-item.high {
  background-color: rgba(16, 185, 129, 0.2);
}

.dark-mode .detection-class-item.medium {
  background-color: rgba(245, 158, 11, 0.2);
}

.dark-mode .detection-class-item.low {
  background-color: rgba(239, 68, 68, 0.2);
}

.class-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  text-transform: capitalize;
}

.confidence-badge {
  padding: var(--space-1);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  background-color: rgba(0, 0, 0, 0.1);
}

.dark-mode .confidence-badge {
  background-color: rgba(255, 255, 255, 0.1);
}

.detection-image-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: var(--space-4);
}

.detection-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: transform var(--transition-fast) ease;
}

.detection-image:hover {
  transform: scale(1.02);
}

.image-caption {
  margin-top: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.dark-mode .image-caption {
  color: var(--color-gray-400);
}

.no-details-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-6);
  color: var(--color-gray-500);
  font-size: var(--font-size-sm);
}

.dark-mode .no-details-message {
  color: var(--color-gray-400);
}

/* ---------- Chat Details ---------- */
.chat-details, .audio-details {
  padding: var(--space-4);
}

.chat-message-container, .transcript-container {
  margin-bottom: var(--space-4);
}

.chat-message-heading, .transcript-heading, 
.keywords-heading, .keyword-heading, 
.sentiment-heading {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-700);
  margin: 0 0 var(--space-2) 0;
}

.dark-mode .chat-message-heading, 
.dark-mode .transcript-heading, 
.dark-mode .keywords-heading, 
.dark-mode .keyword-heading, 
.dark-mode .sentiment-heading {
  color: var(--color-gray-300);
}

.chat-message-content, .transcript-content {
  padding: var(--space-3);
  background-color: var(--color-gray-100);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  line-height: 1.5;
  color: var(--color-gray-800);
}

.dark-mode .chat-message-content, 
.dark-mode .transcript-content {
  background-color: var(--color-gray-700);
  color: var(--color-gray-200);
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.keyword-tag {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  background-color: var(--color-warning-light);
  color: var(--color-warning);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.keyword-tag.highlighted {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
}

.dark-mode .keyword-tag {
  background-color: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.dark-mode .keyword-tag.highlighted {
  background-color: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

/* ---------- Sentiment Analysis ---------- */
.sentiment-container {
  margin-top: var(--space-4);
}

.sentiment-meter {
  margin-top: var(--space-2);
}

.sentiment-bar {
  height: 12px;
  background-color: var(--color-gray-200);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: var(--space-1);
  position: relative;
}

.dark-mode .sentiment-bar {
  background-color: var(--color-gray-700);
}

.sentiment-value {
  height: 100%;
  border-radius: 999px;
  transition: width var(--transition-normal) ease;
}

.sentiment-labels {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
}

.dark-mode .sentiment-labels {
  color: var(--color-gray-400);
}

.sentiment-score {
  margin-top: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
  text-align: center;
}

.dark-mode .sentiment-score {
  color: var(--color-gray-300);
}

/* ---------- Raw Data ---------- */
.raw-data-container {
  padding: var(--space-4);
  overflow-x: auto;
}

.json-content {
  font-family: monospace;
  font-size: var(--font-size-sm);
  line-height: 1.5;
  color: var(--color-gray-800);
  background-color: var(--color-gray-100);
  padding: var(--space-3);
  border-radius: var(--border-radius);
  white-space: pre-wrap;
  overflow-x: auto;
}

.dark-mode .json-content {
  background-color: var(--color-gray-700);
  color: var(--color-gray-200);
}

/* ---------- Modal Components ---------- */
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
  z-index: 50;
}

.modal-dialog {
  width: 90%;
  max-width: 500px;
  background-color: white;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  animation: modal-fade-in var(--transition-normal) ease;
}

.form-dialog {
  max-width: 600px;
}

@keyframes modal-fade-in {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.dark-mode .modal-dialog {
  background-color: var(--color-gray-800);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-gray-200);
}

.dark-mode .modal-header {
  border-bottom-color: var(--color-gray-700);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
}

.dark-mode .modal-header h3 {
  color: var(--color-gray-100);
}

.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--border-radius-sm);
  background-color: var(--color-gray-100);
  color: var(--color-gray-600);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.close-button:hover {
  background-color: var(--color-gray-200);
  color: var(--color-gray-900);
}

.dark-mode .close-button {
  background-color: var(--color-gray-700);
  color: var(--color-gray-400);
}

.dark-mode .close-button:hover {
  background-color: var(--color-gray-600);
  color: var(--color-gray-100);
}

.modal-body {
  padding: var(--space-4);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  padding: var(--space-4);
  border-top: 1px solid var(--color-gray-200);
  gap: var(--space-3);
}

.dark-mode .modal-footer {
  border-top-color: var(--color-gray-700);
}

.button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast) ease;
  border: none;
}

.button.primary {
  background-color: var(--color-primary);
  color: white;
}

.button.primary:hover {
  background-color: var(--color-primary-hover);
}

.button.secondary {
  background-color: var(--color-gray-200);
  color: var(--color-gray-700);
}

.button.secondary:hover {
  background-color: var(--color-gray-300);
  color: var(--color-gray-900);
}

.button.warning {
  background-color: var(--color-danger);
  color: white;
}

.button.warning:hover {
  background-color: var(--color-danger-hover);
}

.dark-mode .button.primary {
  background-color: #6366f1;
  color: white;
}

.dark-mode .button.primary:hover {
  background-color: #4f46e5;
}

.dark-mode .button.secondary {
  background-color: var(--color-gray-700);
  color: var(--color-gray-300);
}

.dark-mode .button.secondary:hover {
  background-color: var(--color-gray-600);
  color: var(--color-gray-100);
}

.dark-mode .button.warning {
  background-color: #ef4444;
  color: white;
}

.dark-mode .button.warning:hover {
  background-color: #dc2626;
}

/* ---------- Agent List ---------- */
.loading-agents, .no-agents {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
  text-align: center;
  color: var(--color-gray-500);
}

.dark-mode .loading-agents, .dark-mode .no-agents {
  color: var(--color-gray-400);
}

.agents-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-height: 300px;
  overflow-y: auto;
}

.agent-list-item {
  display: flex;
  align-items: center;
  padding: var(--space-3);
  border-radius: var(--border-radius);
  background-color: var(--color-gray-50);
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.agent-list-item:hover {
  background-color: var(--color-primary-light);
}

.dark-mode .agent-list-item {
  background-color: var(--color-gray-700);
}

.dark-mode .agent-list-item:hover {
  background-color: rgba(79, 70, 229, 0.2);
}

.agent-status {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: var(--space-3);
  background-color: var(--color-gray-400);
}

.agent-status.online {
  background-color: var(--color-success);
}

.agent-status.offline {
  background-color: var(--color-gray-400);
}

.agent-details {
  flex: 1;
}

.agent-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-900);
}

.agent-email {
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
}

.dark-mode .agent-name {
  color: var(--color-gray-100);
}

.dark-mode .agent-email {
  color: var(--color-gray-400);
}

.forward-icon {
  color: var(--color-gray-500);
  transition: transform var(--transition-fast) ease;
}

.agent-list-item:hover .forward-icon {
  transform: translateX(2px);
  color: var(--color-primary);
}

.dark-mode .agent-list-item:hover .forward-icon {
  color: #818cf8;
}

/* ---------- Image Modal ---------- */
.image-modal-container {
  width: 90%;
  max-width: 900px;
  background-color: white;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  animation: modal-fade-in var(--transition-normal) ease;
}

.dark-mode .image-modal-container {
  background-color: var(--color-gray-800);
}

.image-modal-body {
  padding: var(--space-4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.full-image {
  max-width: 100%;
  max-height: 80vh;
  border-radius: var(--border-radius);
}

/* ---------- Notification Form ---------- */
.notification-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-group label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-700);
}

.dark-mode .form-group label {
  color: var(--color-gray-300);
}

.form-input, .form-select, .form-textarea {
  padding: var(--space-2) var(--space-3);
  background-color: var(--color-gray-50);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--border-radius);
  font-size: var(--font-size-sm);
  color: var(--color-gray-900);
  width: 100%;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 1px var(--color-primary);
}

.dark-mode .form-input, .dark-mode .form-select, .dark-mode .form-textarea {
  background-color: var(--color-gray-700);
  border-color: var(--color-gray-600);
  color: var(--color-gray-100);
}

.dark-mode .form-input:focus, .dark-mode .form-select:focus, .dark-mode .form-textarea:focus {
  border-color: #818cf8;
  box-shadow: 0 0 0 1px #818cf8;
}

.form-textarea {
  min-height: 80px;
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-2);
}

.mt-3 {
  margin-top: var(--space-3);
}

/* ---------- Animations ---------- */
.fade-enter-active, .fade-leave-active {
  transition: opacity var(--transition-normal) ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-enter-active, .slide-leave-active {
  transition: all var(--transition-normal) ease;
}
.slide-enter-from, .slide-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}

.list-move, 
.list-enter-active, 
.list-leave-active {
  transition: all var(--transition-normal) ease;
}

.list-enter-from, 
.list-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* ---------- Modal Animations ---------- */
.modal-enter-active, .modal-leave-active {
  transition: all var(--transition-normal) ease;
}
.modal-enter-from, .modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* ---------- Responsive Adjustments ---------- */
@media (max-width: 768px) {
  .content-container {
    flex-direction: column;
  }
  
  .notifications-section {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-gray-200);
    max-height: 50vh;
  }
  
  .dark-mode .notifications-section {
    border-bottom-color: var(--color-gray-700);
  }
  
  .details-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .details-actions {
    width: 100%;
    margin-top: var(--space-3);
  }
  
  .tab-filters {
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  
  .tab-filters::-webkit-scrollbar {
    display: none;
  }
  
  .details-fields {
    grid-template-columns: 1fr;
  }
}
</style>