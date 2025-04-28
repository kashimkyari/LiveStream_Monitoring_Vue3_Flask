<template>
  <div class="dashboard-grid" ref="dashboardGrid">
    <!-- Stats Overview -->
    <div class="dashboard-card stats-card" ref="statsCard">
      <div class="card-header">
        <h2>Monitoring Stats</h2>
        <span class="card-period">Last 24 hours</span>
      </div>
      <div class="stats-container">
        <div class="stat-item" v-for="(value, key, index) in stats" :key="key" :ref="el => { if (el) statItems[index] = el }">
          <div class="stat-value">{{ value }}</div>
          <div class="stat-label">{{ formatStatLabel(key) }}</div>
        </div>
      </div>
    </div>

    <!-- Recent Alerts -->
    <div class="dashboard-card alerts-card" ref="alertsCard">
      <div class="card-header">
        <h2>Recent Alerts</h2>
        <span class="view-all" @click="$emit('navigate', 'notifications')">View All</span>
      </div>
      <div v-if="recentAlerts.length > 0">
        <div v-for="(alert, index) in recentAlerts" :key="index" class="alert-item" :ref="el => { if (el) alertItems[index] = el }">
          <div class="alert-icon" :class="alert.level">
            <font-awesome-icon :icon="getAlertIcon(alert.level)" />
          </div>
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-description">{{ alert.description }}</div>
            <div class="alert-time">{{ formatTimestamp(alert.timestamp) }}</div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <font-awesome-icon :icon="['fas', 'bell-slash']" class="empty-icon" />
        <div class="empty-message">No recent alerts</div>
      </div>
    </div>

    <!-- Active Streams -->
    <div class="dashboard-card streams-card" ref="streamsCard">
      <div class="card-header">
        <h2>Active Streams</h2>
        <span class="view-all" @click="$emit('navigate', 'streams')">View All</span>
      </div>
      <div v-if="activeStreams.length > 0">
        <div v-for="(stream, index) in activeStreams" :key="index" class="stream-item" :ref="el => { if (el) streamItems[index] = el }">
          <div class="stream-preview">
            <div class="stream-status-indicator" :class="{ live: stream.isLive }"></div>
            <div class="stream-thumbnail"></div>
          </div>
          <div class="stream-content">
            <div class="stream-name">{{ stream.streamer_username || 'Unnamed Stream' }}</div>
            <div class="stream-location">{{ getPlatformName(stream.type) }}</div>
            <div class="stream-duration">{{ stream.assigned_agent ? `Agent: ${stream.assigned_agent}` : 'Unassigned' }}</div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <font-awesome-icon :icon="['fas', 'video-slash']" class="empty-icon" />
        <div class="empty-message">No active streams</div>
      </div>
    </div>

    <!-- Keywords Detection -->
    <div class="dashboard-card keywords-card" ref="keywordsCard">
      <div class="card-header">
        <h2>Keywords Detection</h2>
        <span class="card-count">{{ chatKeywords.length }} active</span>
      </div>
      <div class="keywords-container">
        <div v-for="(keyword, index) in chatKeywords" :key="index" class="keyword-item" :ref="el => { if (el) keywordItems[index] = el }">
          <div class="keyword-name">{{ keyword.keyword }}</div>
          <div class="keyword-badge" :class="getPriorityClass(keyword)">
            {{ getPriorityLabel(keyword) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Flagged Objects -->
    <div class="dashboard-card objects-card" ref="objectsCard">
      <div class="card-header">
        <h2>Object Detection</h2>
        <span class="card-count">{{ flaggedObjects.length }} active</span>
      </div>
      <div class="objects-container">
        <div v-for="(object, index) in flaggedObjects" :key="index" class="object-item" :ref="el => { if (el) objectItems[index] = el }">
          <div class="object-icon">
            <font-awesome-icon :icon="getObjectIcon(object.object_name)" />
          </div>
          <div class="object-name">{{ object.object_name }}</div>
          <div class="object-badge" :class="getConfidenceClass(object.confidence)">
            {{ object.confidence }}%
          </div>
        </div>
      </div>
    </div>

    <!-- Telegram Recipients -->
    <div class="dashboard-card telegram-card" ref="telegramCard">
      <div class="card-header">
        <h2>Telegram Recipients</h2>
        <span class="card-count">{{ telegramRecipients.length }} active</span>
      </div>
      <div class="recipients-container">
        <div v-for="(recipient, index) in telegramRecipients" :key="index" class="recipient-item" :ref="el => { if (el) recipientItems[index] = el }">
          <div class="recipient-avatar"></div>
          <div class="recipient-name">{{ recipient.telegram_username }}</div>
          <div class="recipient-status" :class="recipient.active ? 'active' : 'inactive'">
            {{ recipient.active ? 'active' : 'inactive' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import anime from 'animejs/lib/anime.es.js'

export default {
  name: 'AgentDashboardOverview',
  components: {
    FontAwesomeIcon
  },
  props: {
    stats: {
      type: Object,
      required: true
    },
    recentAlerts: {
      type: Array,
      default: () => []
    },
    activeStreams: {
      type: Array,
      default: () => []
    },
    chatKeywords: {
      type: Array,
      default: () => []
    },
    flaggedObjects: {
      type: Array,
      default: () => []
    },
    telegramRecipients: {
      type: Array,
      default: () => []
    }
  },
  emits: ['navigate'],
  // eslint-disable-next-line
  setup(props) {
    // Refs for animation
    const dashboardGrid = ref(null)
    const statsCard = ref(null)
    const alertsCard = ref(null)
    const streamsCard = ref(null)
    const keywordsCard = ref(null)
    const objectsCard = ref(null)
    const telegramCard = ref(null)
    const statItems = ref([])
    const alertItems = ref([])
    const streamItems = ref([])
    const keywordItems = ref([])
    const objectItems = ref([])
    const recipientItems = ref([])
    
    // Helper methods
    const formatStatLabel = (key) => {
      if (!key) return '';
      
      // Convert camelCase to Title Case with spaces
      return key
        .replace(/([A-Z])/g, ' $1') // Insert a space before all uppercase letters
        .replace(/^./, str => str.toUpperCase()) // Capitalize the first letter
        .trim();
    }
    
    const getAlertIcon = (level) => {
      switch (level) {
        case 'critical':
          return ['fas', 'exclamation-circle']
        case 'warning':
          return ['fas', 'exclamation-triangle']
        case 'info':
          return ['fas', 'info-circle']
        case 'success':
          return ['fas', 'check-circle']
        default:
          return ['fas', 'bell']
      }
    }
    
    const getPlatformName = (type) => {
      if (!type) return 'Unknown Platform';
      
      // Convert to readable platform name
      switch (type.toLowerCase()) {
        case 'chaturbate':
          return 'Chaturbate'
        case 'stripchat':
          return 'Stripchat'
        default:
          return type.charAt(0).toUpperCase() + type.slice(1)
      }
    }
    
    const getObjectIcon = (objectName) => {
      if (!objectName) return ['fas', 'box'];
      
      // Map common objects to appropriate icons
      const objectMap = {
        'camera': 'camera',
        'person': 'user',
        'gun': 'skull',
        'weapon': 'skull',
        'knife': 'exclamation',
        'cigarette': 'smoking',
        'flag': 'flag',
        'fire': 'fire'
      }
      
      const iconName = objectMap[objectName.toLowerCase()] || 'box'
      return ['fas', iconName]
    }
    
    const getPriorityClass = (keyword) => {
      // Use the keyword object to determine priority
      if (!keyword || !keyword.priority) return 'medium'
      
      const priority = keyword.priority.toLowerCase()
      return priority || 'medium'
    }
    
    const getPriorityLabel = (keyword) => {
      // Use the keyword object to get the priority label
      if (!keyword || !keyword.priority) return 'Medium'
      
      const priority = keyword.priority
      return priority.charAt(0).toUpperCase() + priority.slice(1)
    }
    
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return '';
      
      const date = new Date(timestamp);
      
      // Check if it's today
      const today = new Date();
      const isToday = date.getDate() === today.getDate() && 
                      date.getMonth() === today.getMonth() && 
                      date.getFullYear() === today.getFullYear();
      
      if (isToday) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
      
      return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
    
    const getConfidenceClass = (confidence) => {
      if (!confidence) return 'low';
      
      const confidenceValue = parseFloat(confidence);
      if (confidenceValue >= 80) return 'high';
      if (confidenceValue >= 50) return 'medium';
      return 'low';
    }
    
    // Animation function
    const animateDashboard = () => {
      nextTick(() => {
        // Create a timeline for animated entrance
        const tl = anime.timeline({
          easing: 'easeOutExpo',
          duration: 600
        });
        
        // Animate stats card if it exists
        if (statsCard.value) {
          tl.add({
            targets: statsCard.value,
            translateY: [20, 0],
            opacity: [0, 1],
            duration: 500
          });
        }
        
        // Collect and filter valid stat items
        const validStatItems = statItems.value.filter(Boolean);
        if (validStatItems.length > 0) {
          tl.add({
            targets: validStatItems,
            translateY: [15, 0],
            opacity: [0, 1],
            delay: anime.stagger(80),
            duration: 600
          }, '-=400');
        }
        
        // Collect cards that exist in the DOM
        const cards = [
          alertsCard.value,
          streamsCard.value,
          keywordsCard.value,
          objectsCard.value,
          telegramCard.value
        ].filter(Boolean);
        
        if (cards.length > 0) {
          tl.add({
            targets: cards,
            translateY: [20, 0],
            opacity: [0, 1],
            delay: anime.stagger(100),
            duration: 600
          }, '-=400');
        }
        
        // Animate alert items
        const validAlertItems = alertItems.value.filter(Boolean);
        if (validAlertItems.length > 0) {
          tl.add({
            targets: validAlertItems,
            translateX: [10, 0],
            opacity: [0, 1],
            delay: anime.stagger(50, {start: 300}),
            duration: 500
          }, '-=500');
        }
        
        // Animate stream items
        const validStreamItems = streamItems.value.filter(Boolean);
        if (validStreamItems.length > 0) {
          tl.add({
            targets: validStreamItems,
            translateX: [10, 0],
            opacity: [0, 1],
            delay: anime.stagger(50, {start: 400}),
            duration: 500
          }, '-=450');
        }
        
        // Animate keyword items
        const validKeywordItems = keywordItems.value.filter(Boolean);
        if (validKeywordItems.length > 0) {
          tl.add({
            targets: validKeywordItems,
            scale: [0.9, 1],
            opacity: [0, 1],
            delay: anime.stagger(30, {start: 500}),
            duration: 400
          }, '-=400');
        }
        
        // Animate object items
        const validObjectItems = objectItems.value.filter(Boolean);
        if (validObjectItems.length > 0) {
          tl.add({
            targets: validObjectItems,
            scale: [0.9, 1],
            opacity: [0, 1],
            delay: anime.stagger(30, {start: 600}),
            duration: 400
          }, '-=350');
        }
        
        // Animate recipient items
        const validRecipientItems = recipientItems.value.filter(Boolean);
        if (validRecipientItems.length > 0) {
          tl.add({
            targets: validRecipientItems,
            translateY: [10, 0],
            opacity: [0, 1],
            delay: anime.stagger(50, {start: 700}),
            duration: 400
          }, '-=300');
        }
      });
    }
    
    // Run animations when component is mounted
    onMounted(() => {
      animateDashboard();
    });
    
    return {
      dashboardGrid,
      statsCard,
      alertsCard,
      streamsCard,
      keywordsCard,
      objectsCard,
      telegramCard,
      statItems,
      alertItems,
      streamItems,
      keywordItems,
      objectItems,
      recipientItems,
      formatStatLabel,
      getAlertIcon,
      getPlatformName,
      getObjectIcon,
      getPriorityClass,
      getPriorityLabel,
      formatTimestamp,
      getConfidenceClass
    }
  }
}
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: auto;
  gap: 24px;
  grid-template-areas:
    "stats stats stats"
    "alerts alerts streams"
    "keywords objects telegram";
}

.dashboard-card {
  background-color: var(--bg-color);
  border-radius: 12px;
  box-shadow: var(--box-shadow);
  padding: 20px;
  display: flex;
  flex-direction: column;
  opacity: 0; /* Start with opacity 0 for animation */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
}

.card-period, .card-count {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.view-all {
  font-size: 0.8rem;
  color: var(--primary-color);
  cursor: pointer;
  transition: opacity 0.2s;
}

.view-all:hover {
  opacity: 0.8;
}

/* Stats Card */
.stats-card {
  grid-area: stats;
}

.stats-container {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.stat-item {
  flex: 1;
  min-width: 120px;
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  background-color: var(--bg-light);
  opacity: 0; /* Start with opacity 0 for animation */
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 8px;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

/* Alerts Card */
.alerts-card {
  grid-area: alerts;
  max-height: 320px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  padding: 12px;
  border-radius: 8px;
  background-color: var(--bg-light);
  margin-bottom: 12px;
  transition: transform 0.2s;
  opacity: 0; /* Start with opacity 0 for animation */
}

.alert-item:hover {
  transform: translateY(-2px);
}

.alert-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
}

.alert-icon.critical {
  background-color: rgba(244, 67, 54, 0.1);
  color: #F44336;
}

.alert-icon.warning {
  background-color: rgba(255, 152, 0, 0.1);
  color: #FF9800;
}

.alert-icon.info {
  background-color: rgba(3, 169, 244, 0.1);
  color: #03A9F4;
}

.alert-icon.success {
  background-color: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-color);
}

.alert-description {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.alert-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Streams Card */
.streams-card {
  grid-area: streams;
  max-height: 320px;
  overflow-y: auto;
}

.stream-item {
  display: flex;
  padding: 12px;
  border-radius: 8px;
  background-color: var(--bg-light);
  margin-bottom: 12px;
  transition: transform 0.2s;
  opacity: 0; /* Start with opacity 0 for animation */
}

.stream-item:hover {
  transform: translateY(-2px);
}

.stream-preview {
  width: 60px;
  height: 45px;
  border-radius: 4px;
  background-color: #333;
  margin-right: 12px;
  position: relative;
  flex-shrink: 0;
}

.stream-status-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #888;
}

.stream-status-indicator.live {
  background-color: #F44336;
}

.stream-content {
  flex: 1;
}

.stream-name {
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-color);
}

.stream-location, .stream-duration {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

/* Keywords Card */
.keywords-card {
  grid-area: keywords;
  max-height: 320px;
  overflow-y: auto;
}

.keywords-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.keyword-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  background-color: var(--bg-light);
  transition: transform 0.2s;
  opacity: 0; /* Start with opacity 0 for animation */
}

.keyword-item:hover {
  transform: translateY(-2px);
}

.keyword-name {
  font-weight: 500;
  color: var(--text-color);
}

.keyword-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.keyword-badge.high {
  background-color: rgba(244, 67, 54, 0.1);
  color: #F44336;
}

.keyword-badge.medium {
  background-color: rgba(255, 152, 0, 0.1);
  color: #FF9800;
}

.keyword-badge.low {
  background-color: rgba(3, 169, 244, 0.1);
  color: #03A9F4;
}

/* Objects Card */
.objects-card {
  grid-area: objects;
  max-height: 320px;
  overflow-y: auto;
}

.objects-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.object-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  background-color: var(--bg-light);
  transition: transform 0.2s;
  opacity: 0; /* Start with opacity 0 for animation */
}

.object-item:hover {
  transform: translateY(-2px);
}

.object-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.05);
  margin-right: 12px;
  color: var(--text-color);
}

.object-name {
  flex: 1;
  font-weight: 500;
  color: var(--text-color);
}

.object-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.object-badge.high {
  background-color: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.object-badge.medium {
  background-color: rgba(255, 152, 0, 0.1);
  color: #FF9800;
}

.object-badge.low {
  background-color: rgba(244, 67, 54, 0.1);
  color: #F44336;
}

/* Telegram Card */
.telegram-card {
  grid-area: telegram;
  max-height: 320px;
  overflow-y: auto;
}

.recipients-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recipient-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  background-color: var(--bg-light);
  transition: transform 0.2s;
  opacity: 0; /* Start with opacity 0 for animation */
}

.recipient-item:hover {
  transform: translateY(-2px);
}

.recipient-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #1E88E5;
  margin-right: 12px;
}

.recipient-name {
  flex: 1;
  font-weight: 500;
  color: var(--text-color);
}

.recipient-status {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.recipient-status.active {
  background-color: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.recipient-status.inactive {
  background-color: rgba(158, 158, 158, 0.1);
  color: #9E9E9E;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  text-align: center;
}

.empty-icon {
  font-size: 2rem;
  color: #ccc;
  margin-bottom: 12px;
}

.empty-message {
  font-weight: 500;
  color: var(--text-secondary);
}

/* Media Query for medium screens */
@media (max-width: 992px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
    grid-template-areas:
      "stats stats"
      "alerts streams"
      "keywords objects"
      "telegram telegram";
  }
}

/* Media Query for mobile */
@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    grid-template-areas:
      "stats"
      "alerts"
      "streams"
      "keywords"
      "objects"
      "telegram";
    gap: 16px;
  }
  
  .dashboard-card {
    padding: 16px;
  }
  
  .stats-container {
    gap: 16px;
  }
  
  .stat-item {
    min-width: 80px;
    padding: 12px;
  }
  
  .stat-value {
    font-size: 1.5rem;
  }
}

/* Animation classes */
.fade-in {
  animation: fadeIn 0.5s forwards;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.slide-up {
  animation: slideUp 0.5s forwards;
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(20px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}
</style>