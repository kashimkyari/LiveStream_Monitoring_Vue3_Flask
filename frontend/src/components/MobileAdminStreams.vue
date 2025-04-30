<template>
  <div class="streams-container" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="header">
      <h2>Streams</h2>
      <div class="header-actions">
        <button @click="showAddStreamModal = true" class="add-stream-btn">
          <font-awesome-icon :icon="['fas', 'plus']" class="icon" />
          Add Stream
        </button>
        <button
          @click="refreshStreams"
          :disabled="refreshingStreams"
          class="refresh-btn"
        >
          <font-awesome-icon
            :icon="['fas', 'sync-alt']"
            class="icon"
            :class="{ 'spinning': refreshingStreams }"
          />
        </button>
      </div>
    </div>

    <div class="search-section">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search streams by username..."
        class="search-input"
      />
    </div>

    <div v-if="loading || refreshingStreams" class="loading">
      Loading streams...
    </div>
    <div v-else-if="filteredStreams.length === 0" class="no-streams">
      No streams found.
    </div>
    <div v-else class="streams-list">
      <div
        v-for="stream in filteredStreams"
        :key="stream.id"
        class="stream-item"
        @click="$emit('stream-selected', stream)"
      >
        <div class="stream-content">
          <div class="stream-header">
            <span class="username">{{ stream.streamer_username || 'Unknown' }}</span>
            <span class="status" :class="getStatusClass(stream.status)">
              {{ stream.status || 'Unknown' }}
            </span>
          </div>
          <div class="stream-details">
            <p><strong>Type:</strong> {{ stream.type || 'N/A' }}</p>
            <p><strong>Platform:</strong> {{ stream.platform || 'Unknown' }}</p>
            <p>
              <strong>Assignments:</strong>
              {{ stream.assignments?.length ? stream.assignments.map(a => agents.find(agent => agent.id === a.agent_id)?.username || 'Unknown').join(', ') : 'None' }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <MobileAddStreamModal
      :is-visible="showAddStreamModal"
      :is-dark-theme="isDarkTheme"
      :job-id="jobId"
      @close="handleModalClose"
      @start-stream-creation="handleStartStreamCreation"
      @stream-created="handleStreamCreated"
    />
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faPlus, faSyncAlt } from '@fortawesome/free-solid-svg-icons'
import { library } from '@fortawesome/fontawesome-svg-core'
import { useMobileDashboardData } from '../composables/useMobileDashboardData'
import MobileAddStreamModal from './MobileAddStreamModal.vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

library.add(faPlus, faSyncAlt)

export default {
  name: 'MobileAdminStreams',
  components: { FontAwesomeIcon, MobileAddStreamModal },
  props: {
    loading: { type: Boolean, default: false },
    refreshingStreams: { type: Boolean, default: false },
    allStreams: { type: Array, default: () => [] },
    agents: { type: Array, default: () => [] },
    isDarkTheme: { type: Boolean, default: false }
  },
  emits: ['refresh', 'stream-selected', 'add-stream'],
  setup(props, { emit }) {
    const { refreshStream } = useMobileDashboardData()
    const searchQuery = ref('')
    const showAddStreamModal = ref(false)
    const jobId = ref(null)
    const toast = useToast()

    const filteredStreams = computed(() => {
      if (!props.allStreams || !Array.isArray(props.allStreams)) return []
      return props.allStreams.filter(
        (stream) =>
          stream &&
          stream.streamer_username &&
          stream.streamer_username.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    })

    const refreshStreams = () => {
      props.allStreams.forEach((stream) => {
        if (stream.id) refreshStream(stream.id)
      })
      emit('refresh')
    }

    const getStatusClass = (status) => {
      status = status || 'unknown'
      switch (status.toLowerCase()) {
        case 'active':
        case 'live':
          return 'status-active'
        case 'inactive':
        case 'offline':
          return 'status-inactive'
        default:
          return 'status-unknown'
      }
    }

    const handleStartStreamCreation = async ({ platform, room_url, agent_id }) => {
      try {
        const token = localStorage.getItem('token')
        if (!token) throw new Error('No authentication token found')
        const payload = { platform, room_url: room_url.toLowerCase(), agent_id: agent_id || null }
        const response = await axios.post('/api/streams/interactive', payload, {
          headers: { Authorization: `Bearer ${token}` }
        })
        jobId.value = response.data.job_id
      } catch (error) {
        console.error('Error starting stream creation:', error)
        const message = error.response?.data?.message || 'Failed to start stream creation'
        if (error.response?.status === 400) {
          toast.error(`Invalid input: ${message}`)
        } else if (error.response?.status === 409) {
          toast.error('Stream already exists')
        } else {
          toast.error('Server error. Please try again.')
        }
        showAddStreamModal.value = false
      }
    }

    const handleStreamCreated = (streamData) => {
      emit('add-stream', streamData)
      emit('refresh')
      jobId.value = null
      showAddStreamModal.value = false
    }

    const handleModalClose = () => {
      showAddStreamModal.value = false
      jobId.value = null
    }

    return {
      searchQuery,
      filteredStreams,
      refreshStreams,
      getStatusClass,
      showAddStreamModal,
      jobId,
      handleStartStreamCreation,
      handleStreamCreated,
      handleModalClose
    }
  }
}
</script>

<style scoped>
.streams-container {
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

.streams-container[data-theme="dark"] {
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

.add-stream-btn,
.refresh-btn {
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

.add-stream-btn:disabled,
.refresh-btn:disabled {
  background-color: var(--border-color);
  cursor: not-allowed;
}

.icon {
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

.search-section {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  font-size: 0.95rem;
  color: var(--text-color);
  background-color: var(--card-bg);
}

.search-input::placeholder {
  color: var(--text-light);
}

.loading,
.no-streams {
  text-align: center;
  padding: 20px;
  color: var(--text-light);
  font-size: 1.1rem;
}

.streams-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stream-item {
  background-color: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 16px;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: background-color 0.2s;
}

.stream-item:hover {
  background-color: var(--primary-light);
}

.stream-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stream-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.username {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--text-color);
  max-width: 75%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status {
  font-size: 0.85rem;
  padding: 3px 10px;
  border-radius: 14px;
  text-transform: capitalize;
}

.status-active {
  background-color: #4caf50;
  color: white;
}

.status-inactive {
  background-color: #f44336;
  color: white;
}

.status-unknown {
  background-color: var(--text-light);
  color: var(--card-bg);
}

.stream-details p {
  margin: 6px 0;
  font-size: 0.95rem;
  color: var(--text-color);
}

.stream-details p strong {
  font-weight: 600;
}
</style>