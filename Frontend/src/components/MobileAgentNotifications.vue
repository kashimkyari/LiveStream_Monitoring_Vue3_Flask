<template>
  <div class="mobile-agent-notifications">
    <div class="section-header">
      <h2>Notifications</h2>
      <div class="notification-controls">
        <button 
          v-if="unreadCount > 0"
          class="btn btn-sm btn-mark-all"
          @click="$emit('mark-all-read')"
        >
          <font-awesome-icon icon="check-double" />
          Mark All Read
        </button>
      </div>
    </div>

    <div class="notification-filters">
      <div class="filter-toggle">
        <span>Group by Type</span>
        <div 
          class="toggle-switch"
          :class="{ active: groupByType }"
          @click="$emit('toggle-group-type')"
        >
          <div class="toggle-switch-handle"></div>
        </div>
      </div>
      <div class="filter-toggle">
        <span>Group by Stream</span>
        <div 
          class="toggle-switch"
          :class="{ active: groupByStream }"
          @click="$emit('toggle-group-stream')"
        >
          <div class="toggle-switch-handle"></div>
        </div>
      </div>
    </div>

    <div v-if="notifications.length === 0" class="empty-state">
      <font-awesome-icon icon="bell-slash" class="empty-icon" />
      <p>No notifications to display</p>
    </div>

    <div v-else class="notification-list">
      <div 
        v-for="notification in notifications" 
        :key="notification.id"
        class="notification-item"
        :class="{ unread: !notification.read }"
        @click="$emit('mark-read', notification.id)"
      >
        <div class="notification-icon" :style="{ backgroundColor: notification.color }">
          <font-awesome-icon :icon="notification.icon" />
        </div>
        <div class="notification-content">
          <div class="notification-title">{{ notification.title }}</div>
          <div class="notification-text">{{ notification.message }}</div>
          <div class="notification-time">{{ notification.timeAgo }}</div>
        </div>
        <div class="notification-status">
          <div v-if="!notification.read" class="unread-indicator"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

defineProps({
  notifications: {
    type: Array,
    default: () => []
  },
  unreadCount: {
    type: Number,
    default: 0
  },
  groupByType: {
    type: Boolean,
    default: false
  },
  groupByStream: {
    type: Boolean,
    default: false
  }
})

defineEmits([
  'mark-read',
  'mark-all-read',
  'toggle-group-type',
  'toggle-group-stream'
])
</script>

<style scoped>
.mobile-agent-notifications {
  padding: 0 0.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.notification-controls {
  display: flex;
  gap: 0.5rem;
}

.btn-mark-all {
  background: none;
  border: 1px solid var(--primary-color);
  color: var(--primary-color);
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.notification-filters {
  display: flex;
  justify-content: space-between;
  background-color: var(--input-bg);
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
  align-items: center;
  padding: 1rem;
  background-color: var(--input-bg);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
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
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  margin-right: 1rem;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  margin-bottom: 0.3rem;
  color: var(--text-color);
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
  margin-left: 0.5rem;
}

.unread-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary-color);
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-light);
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
  opacity: 0.7;
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
</style>