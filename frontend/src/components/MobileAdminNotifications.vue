<template>
  <div class="notifications-container" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="header">
      <h2>Notifications</h2>
      <div class="header-actions">
        <button
          @click="$emit('refresh')"
          :disabled="notificationsLoading"
          class="refresh-btn"
        >
          <font-awesome-icon
            :icon="['fas', 'sync-alt']"
            :class="{ 'spinning': notificationsLoading }"
          />
        </button>
        <button
          @click="$emit('mark-all-read')"
          :disabled="unreadCount === 0"
          class="mark-all-read-btn"
        >
          Mark All Read
        </button>
      </div>
    </div>

    <div class="filter-section">
      <label>
        <input
          type="checkbox"
          v-model="groupByType"
          @change="$emit('toggle-group-by-type')"
        />
        Group by Type
      </label>
      <label>
        <input
          type="checkbox"
          v-model="groupByStream"
          @change="$emit('toggle-group-by-stream')"
        />
        Group by Streamer
      </label>
    </div>

    <div v-if="notificationsLoading" class="loading">
      Loading notifications...
    </div>
    <div v-else-if="notifications.length === 0" class="no-notifications">
      No notifications available.
    </div>
    <div v-else class="notifications-list">
      <template v-if="groupByType || groupByStream">
        <div
          v-for="(group, key) in groupedNotifications"
          :key="key"
          class="notification-group"
        >
          <h3>
            {{
              groupByType
                ? key.replace('_', ' ').toUpperCase()
                : group[0].details.streamer_name
            }}
          </h3>
          <div
            v-for="notification in group"
            :key="notification.id"
            class="notification-item"
            :class="{ 'unread': !notification.read }"
          >
            <div class="notification-content">
              <div class="notification-header">
                <span
                  class="type"
                  :class="getTypeClass(notification.event_type)"
                >
                  {{ notification.event_type.replace('_', ' ') }}
                </span>
                <span class="time">{{ formatTime(notification.timestamp) }}</span>
              </div>
              <div class="notification-details">
                <p>
                  <strong>Streamer:</strong>
                  {{ notification.details.streamer_name || 'Unknown' }}
                </p>
                <p>
                  <strong>Platform:</strong>
                  {{ notification.details.platform || 'Unknown' }}
                </p>
                <p v-if="notification.event_type === 'object_detection'">
                  <strong>Objects:</strong>
                  {{ formatObjects(notification.details.detections) }}
                </p>
                <p v-if="notification.event_type === 'audio_detection'">
                  <strong>Keyword:</strong>
                  {{ notification.details.keyword || 'N/A' }}<br />
                  <strong>Transcript:</strong>
                  {{
                    notification.details.transcript.slice(0, 100) +
                    (notification.details.transcript.length > 100 ? '...' : '')
                  }}
                </p>
                <p
                  v-if="
                    notification.event_type === 'chat_detection' ||
                    notification.event_type === 'chat_sentiment_detection'
                  "
                >
                  <strong>Sender:</strong>
                  {{ notification.details.detections[0]?.sender || 'Unknown' }}<br />
                  <strong>Message:</strong>
                  {{
                    notification.details.detections[0]?.message.slice(0, 100) +
                    (notification.details.detections[0]?.message.length > 100
                      ? '...'
                      : '')
                  }}
                </p>
                <p>
                  <strong>Assigned Agent:</strong>
                  {{ notification.details.assigned_agent || 'Unassigned' }}
                </p>
              </div>
              <button
                v-if="!notification.read"
                @click="$emit('mark-as-read', notification.id)"
                class="mark-read-btn"
              >
                Mark as Read
              </button>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="notification-item"
          :class="{ 'unread': !notification.read }"
        >
          <div class="notification-content">
            <div class="notification-header">
              <span
                class="type"
                :class="getTypeClass(notification.event_type)"
              >
                {{ notification.event_type.replace('_', ' ') }}
              </span>
              <span class="time">{{ formatTime(notification.timestamp) }}</span>
            </div>
            <div class="notification-details">
              <p>
                <strong>Streamer:</strong>
                {{ notification.details.streamer_name || 'Unknown' }}
              </p>
              <p>
                <strong>Platform:</strong>
                {{ notification.details.platform || 'Unknown' }}
              </p>
              <p v-if="notification.event_type === 'object_detection'">
                <strong>Objects:</strong>
                {{ formatObjects(notification.details.detections) }}
              </p>
              <p v-if="notification.event_type === 'audio_detection'">
                <strong>Keyword:</strong>
                {{ notification.details.keyword || 'N/A' }}<br />
                <strong>Transcript:</strong>
                {{
                  notification.details.transcript.slice(0, 100) +
                  (notification.details.transcript.length > 100 ? '...' : '')
                }}
              </p>
              <p
                v-if="
                  notification.event_type === 'chat_detection' ||
                  notification.event_type === 'chat_sentiment_detection'
                "
              >
                <strong>Sender:</strong>
                {{ notification.details.detections[0]?.sender || 'Unknown' }}<br />
                <strong>Message:</strong>
                {{
                  notification.details.detections[0]?.message.slice(0, 100) +
                  (notification.details.detections[0]?.message.length > 100
                    ? '...'
                    : '')
                }}
              </p>
              <p>
                <strong>Assigned Agent:</strong>
                {{ notification.details.assigned_agent || 'Unassigned' }}
              </p>
            </div>
            <button
              v-if="!notification.read"
              @click="$emit('mark-as-read', notification.id)"
              class="mark-read-btn"
            >
              Mark as Read
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faSyncAlt } from '@fortawesome/free-solid-svg-icons'
import { library } from '@fortawesome/fontawesome-svg-core'

library.add(faSyncAlt)

export default {
  name: 'MobileAdminNotifications',
  components: {
    FontAwesomeIcon
  },
  props: {
    notifications: {
      type: Array,
      default: () => []
    },
    notificationsLoading: {
      type: Boolean,
      default: false
    },
    unreadCount: {
      type: Number,
      default: 0
    },
    groupedNotifications: {
      type: Object,
      default: () => ({})
    },
    isGroupedByType: {
      type: Boolean,
      default: false
    },
    isGroupedByStream: {
      type: Boolean,
      default: false
    },
    isDarkTheme: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'mark-as-read',
    'mark-all-read',
    'toggle-group-by-type',
    'toggle-group-by-stream',
    'refresh'
  ],
  setup(props) {
    const groupByType = ref(props.isGroupedByType)
    const groupByStream = ref(props.isGroupedByStream)

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const formatObjects = (detections) => {
      if (!detections || !Array.isArray(detections)) return 'None'
      return detections
        .map((d) => `${d.class} (${(d.confidence * 100).toFixed(1)}%)`)
        .join(', ')
    }

    const getTypeClass = (type) => {
      switch (type) {
        case 'object_detection':
          return 'type-object'
        case 'audio_detection':
          return 'type-audio'
        case 'chat_detection':
        case 'chat_sentiment_detection':
          return 'type-chat'
        default:
          return 'type-default'
      }
    }

    return {
      groupByType,
      groupByStream,
      formatTime,
      formatObjects,
      getTypeClass
    }
  }
}
</script>

<style scoped>
.notifications-container {
  --primary-color: #4361ee;
  --secondary-color: #3f37c9;
  --background-color: #f8f9fa;
  --card-bg: #ffffff;
  --text-color: #333333;
  --text-light: #777777;
  --border-color: #e0e0e0;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  --border-radius: 12px;
  --border-radius-sm: 8px;
  padding: 20px;
  background-color: var(--background-color);
  color: var(--text-color);
  min-height: 100vh;
  font-family: 'Arial', sans-serif;
  line-height: 1.5;
}

.notifications-container[data-theme="dark"] {
  --primary-color: #4cc9f0;
  --secondary-color: #4895ef;
  --background-color: #121212;
  --card-bg: #1e1e1e;
  --text-color: #f8f9fa;
  --text-light: #b0b0b0;
  --border-color: #333333;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--text-color);
}

.header-actions {
  display: flex;
  gap: 10px;
}

.refresh-btn,
.mark-all-read-btn {
  padding: 10px 14px;
  border: none;
  border-radius: var(--border-radius-sm);
  background-color: var(--primary-color);
  color: white;
  cursor: pointer;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 6px;
}

.refresh-btn:disabled,
.mark-all-read-btn:disabled {
  background-color: var(--border-color);
  cursor: not-allowed;
}

.refresh-btn svg {
  font-size: 0.9rem;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

.filter-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  font-size: 0.95rem;
}

.filter-section label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-color);
}

.loading,
.no-notifications {
  text-align: center;
  padding: 20px;
  color: var(--text-light);
  font-size: 1.1rem;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-group h3 {
  font-size: 1.2rem;
  font-weight: 500;
  margin: 16px 0 12px;
  color: var(--text-color);
}

.notification-item {
  background-color: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 16px;
  box-shadow: var(--shadow-sm);
  transition: background-color 0.2s;
}

.notification-item.unread {
  background-color: #e6f0ff;
}

[data-theme="dark"] .notification-item.unread {
  background-color: #3a4a6a;
}

.notification-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type {
  font-weight: 500;
  font-size: 0.95rem;
  padding: 3px 10px;
  border-radius: 14px;
}

.type-object {
  background-color: #ff9800;
  color: white;
}

.type-audio {
  background-color: #4caf50;
  color: white;
}

.type-chat {
  background-color: #2196f3;
  color: white;
}

.type-default {
  background-color: var(--text-light);
  color: var(--card-bg);
}

.time {
  font-size: 0.85rem;
  color: var(--text-light);
}

.notification-details p {
  margin: 6px 0;
  font-size: 0.95rem;
  color: var(--text-color);
}

.notification-details p strong {
  font-weight: 600;
}

.mark-read-btn {
  padding: 8px 14px;
  border: none;
  border-radius: var(--border-radius-sm);
  background-color: #28a745;
  color: white;
  cursor: pointer;
  font-size: 0.9rem;
  align-self: flex-end;
}

.mark-read-btn:hover {
  background-color: #218838;
}
</style>