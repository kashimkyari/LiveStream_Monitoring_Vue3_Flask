<template>
  <div class="mobile-admin-home" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="welcome-section">
      <h2>Welcome, {{ user?.name || 'Admin' }}</h2>
      <p class="welcome-text">Here's your overview for today</p>
    </div>
    <div class="stats-grid">
      <div class="stat-card" v-for="(stat, key) in computedStats" :key="key">
        <div class="stat-icon">
          <font-awesome-icon :icon="statIcons[key]" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat }}</div>
          <div class="stat-label">{{ key.charAt(0).toUpperCase() + key.slice(1) }}</div>
        </div>
      </div>
    </div>
    <div class="quick-actions">
      <button class="action-button" @click="$emit('add-stream')">
        <font-awesome-icon icon="plus" /> Add Stream
      </button>
      <button class="action-button" @click="$emit('add-agent')">
        <font-awesome-icon icon="plus" /> Add Agent
      </button>
    </div>
    <div class="recent-activity">
      <h3>Recent Activity</h3>
      <div class="activity-list">
        <div class="activity-item" v-for="(detection, index) in recentDetections" :key="index">
          <font-awesome-icon :icon="getActivityIcon(detection)" class="activity-icon" :class="getActivityClass(detection)" />
          <div class="activity-content">
            <p>{{ summarizeDescription(detection) }}</p>
            <span class="activity-time">{{ formatTime(detection.timestamp) }}</span>
          </div>
        </div>
        <p v-if="!recentDetections.length" class="no-data">No recent activity</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { ref, onMounted, watch } from 'vue';

export default {
  name: 'MobileAdminHome',
  props: {
    user: {
      type: Object,
      default: () => ({})
    },
    stats: {
      type: Object,
      default: () => ({ streams: 0, agents: 0, detections: 0, notifications: 0 })
    },
    recentDetections: {
      type: Array,
      default: () => []
    },
    recentNotifications: {
      type: Array,
      default: () => []
    },
    isDarkTheme: Boolean
  },
  emits: ['refresh-data', 'add-stream', 'add-agent'],
  // eslint-disable-next-line 
  setup(props, { emit }) {
    const statIcons = {
      streams: 'video',
      agents: 'users',
      detections: 'eye',
      notifications: 'bell'
    };
    const formatTime = (timestamp) => new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Local state for computed detections
    const computedStats = ref({ ...props.stats });
    
    const fetchNotifications = async () => {
      try {
        const response = await axios.get('/api/notifications');
        const notifications = response.data;
        // Compute total detections based on specific event types
        const totalDetections = notifications.filter(n => 
          n.event_type === 'object_detection' || 
          n.event_type === 'audio_detection' || 
          n.event_type === 'chat_detection'
        ).length;
        computedStats.value.detections = totalDetections;
      } catch (error) {
        console.error('Error fetching notifications:', error);
      }
    };
    
    onMounted(() => {
      fetchNotifications();
    });
    
    // Watch for changes in stats prop, but keep detections from local computation
    watch(() => props.stats, (newStats) => {
      computedStats.value = { ...newStats, detections: computedStats.value.detections };
    });
    
    // Function to determine icon based on activity type
    const getActivityIcon = (detection) => {
      if (detection.event_type) {
        switch (detection.event_type.toLowerCase()) {
          case 'object_detection':
            return 'eye';
          case 'audio_detection':
            return 'microphone';
          case 'chat_detection':
            return 'comments';
          default:
            return 'eye';
        }
      }
      return 'eye'; // Fallback icon
    };
    
    // Function to add a class for styling based on activity type
    const getActivityClass = (detection) => {
      if (detection.event_type) {
        return `activity-${detection.event_type.toLowerCase().replace('_', '-')}`;
      }
      return '';
    };
    
    // Function to summarize description for better readability
    const summarizeDescription = (detection) => {
      let desc = detection.description || 'Activity detected';
      // Truncate long descriptions
      if (desc.length > 50) {
        desc = desc.substring(0, 47) + '...';
      }
      // Add context if event_type is available
      if (detection.event_type) {
        switch (detection.event_type.toLowerCase()) {
          case 'object_detection':
            return `Object: ${desc}`;
          case 'audio_detection':
            return `Audio: ${desc}`;
          case 'chat_detection':
            return `Chat: ${desc}`;
          default:
            return desc;
        }
      }
      return desc;
    };
    
    return { statIcons, formatTime, computedStats, getActivityIcon, getActivityClass, summarizeDescription };
  }
};
</script>

<style scoped>
.mobile-admin-home {
  font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --primary-color: #4361ee;
  --primary-light: #4361ee20;
  --secondary-color: #3f37c9;
  --text-color: #333333;
  --text-light: #777777;
  --background-color: #f8f9fa;
  --card-bg: #ffffff;
  --border-color: #e0e0e0;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  --border-radius: 12px;
  background-color: var(--background-color);
  color: var(--text-color);
  padding: 12px;
}

.mobile-admin-home[data-theme="dark"] {
  --primary-color: #4cc9f0;
  --primary-light: #4cc9f020;
  --secondary-color: #4895ef;
  --text-color: #f8f9fa;
  --text-light: #b0b0b0;
  --background-color: #121212;
  --card-bg: #1e1e1e;
  --border-color: #333333;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
}

.welcome-section { margin-bottom: 16px; }
.welcome-section h2 { font-size: 1.25rem; font-weight: 600; color: var(--text-color); margin: 0 0 4px; }
.welcome-text { font-size: 0.875rem; color: var(--text-light); }

.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background-color: var(--card-bg); border-radius: var(--border-radius); padding: 14px; display: flex; flex-direction: column; align-items: center; box-shadow: var(--shadow-sm); transition: var(--transition); border: 1px solid var(--border-color); }
.stat-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.stat-icon { background-color: var(--primary-light); color: var(--primary-color); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; font-size: 1.2rem; }
.stat-content { text-align: center; }
.stat-value { font-weight: 700; font-size: 1.4rem; margin-bottom: 2px; color: var(--text-color); }
.stat-label { font-size: 0.75rem; color: var(--text-light); }

.quick-actions { 
  display: flex; 
  justify-content: center; 
  gap: 16px; 
  margin-bottom: 16px; 
  margin-top: 0; 
  flex-wrap: nowrap; 
  padding: 0 20px; 
}
@media (max-width: 400px) {
  .quick-actions { 
    justify-content: center; 
  }
  .action-button { 
    min-width: 120px; 
    padding: 10px 16px; 
  }
}
.action-button { 
  background-color: var(--primary-color); 
  color: white; 
  border: none; 
  border-radius: var(--border-radius); 
  padding: 12px 24px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  gap: 10px; 
  cursor: pointer; 
  transition: var(--transition); 
  box-shadow: var(--shadow-sm); 
  font-size: 0.9rem; 
  font-weight: 600; 
  min-width: 160px; 
  text-transform: uppercase; 
  letter-spacing: 0.5px; 
}
.action-button:hover { 
  background-color: var(--secondary-color); 
  transform: translateY(-2px); 
  box-shadow: var(--shadow-md); 
}

.recent-activity h3 { font-size: 1.25rem; font-weight: 600; color: var(--text-color); margin: 0 0 12px; }
.activity-list { display: flex; flex-direction: column; gap: 12px; }
.activity-item { display: flex; align-items: center; gap: 12px; background-color: var(--card-bg); padding: 12px; border-radius: var(--border-radius); box-shadow: var(--shadow-sm); border: 1px solid var(--border-color); }
.activity-icon { color: var(--primary-color); font-size: 1.2rem; }
.activity-content p { margin: 0; font-size: 0.875rem; color: var(--text-color); max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.activity-time { font-size: 0.75rem; color: var(--text-light); }
.no-data { font-size: 0.875rem; color: var(--text-light); text-align: center; }

/* Add specific colors for different activity types */
.activity-object-detection { color: #4CAF50; } /* Green for object detection */
.activity-audio-detection { color: #2196F3; } /* Blue for audio detection */
.activity-chat-detection { color: #FFC107; } /* Yellow for chat detection */

/* Blur effect for parent component when modal is open */
.mobile-admin-home.modal-open {
  filter: blur(5px);
  pointer-events: none;
}

/* Overlay for blur effect */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
}
</style>