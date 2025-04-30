<template>
  <div class="mobile-admin-home" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="welcome-section">
      <h2>Welcome, {{ user?.name || 'Admin' }}</h2>
      <p class="welcome-text">Here's your overview for today</p>
    </div>
    <div class="stats-grid">
      <div class="stat-card" v-for="(stat, key) in stats" :key="key">
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
      <button class="action-button" @click="$emit('refresh-data')">
        <font-awesome-icon icon="sync" /> Refresh
      </button>
    </div>
    <div class="recent-activity">
      <h3>Recent Activity</h3>
      <div class="activity-list">
        <div class="activity-item" v-for="(detection, index) in recentDetections" :key="index">
          <font-awesome-icon icon="eye" class="activity-icon" />
          <div class="activity-content">
            <p>{{ detection.description }}</p>
            <span class="activity-time">{{ formatTime(detection.timestamp) }}</span>
          </div>
        </div>
        <p v-if="!recentDetections.length" class="no-data">No recent activity</p>
      </div>
    </div>
  </div>
</template>

<script>

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
  setup() {
    const statIcons = {
      streams: 'video',
      agents: 'users',
      detections: 'eye',
      notifications: 'bell'
    }
    const formatTime = (timestamp) => new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    return { statIcons, formatTime }
  }
}
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

.quick-actions { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.action-button { background-color: var(--primary-color); color: white; border: none; border-radius: var(--border-radius); padding: 10px 16px; display: flex; align-items: center; gap: 8px; cursor: pointer; transition: var(--transition); box-shadow: var(--shadow-sm); font-size: 0.875rem; }
.action-button:hover { background-color: var(--secondary-color); }

.recent-activity h3 { font-size: 1.25rem; font-weight: 600; color: var(--text-color); margin: 0 0 12px; }
.activity-list { display: flex; flex-direction: column; gap: 12px; }
.activity-item { display: flex; align-items: center; gap: 12px; background-color: var(--card-bg); padding: 12px; border-radius: var(--border-radius); box-shadow: var(--shadow-sm); border: 1px solid var(--border-color); }
.activity-icon { color: var(--primary-color); font-size: 1.2rem; }
.activity-content p { margin: 0; font-size: 0.875rem; color: var(--text-color); }
.activity-time { font-size: 0.75rem; color: var(--text-light); }
.no-data { font-size: 0.875rem; color: var(--text-light); text-align: center; }
</style>