<template>
  <section class="dashboard-tab">
    <div class="dashboard-header">
      <h2>Dashboard</h2>
    </div>

    <!-- Stats section -->
    <div class="stats-section">
      <StatCard 
        v-for="stat in stats"
        :key="stat.label"
        :value="stat.value"
        :label="stat.label"
        :icon="stat.icon"
      />
    </div>

    <!-- Search and Controls -->
    <div class="controls-section">
      <div class="search-box">
        <font-awesome-icon icon="search" class="search-icon" />
        <input v-model="searchQuery" placeholder="Search streams..." class="search-input" />
      </div>
      <div class="view-controls" style="display: flex; gap: 1rem;">
        <button 
          @click="openRefreshModal" 
          class="view-toggle-btn refresh-btn"
          :disabled="refreshing"
          data-tooltip="Refreshes one stream at a time to avoid crashing"
        >
          <font-awesome-icon 
            :icon="refreshing ? 'spinner' : 'sync-alt'" 
            :spin="refreshing"
          />
          {{ refreshing ? 'Refreshing...' : 'Refresh Streams' }}
        </button>
      </div>
    </div>

    <!-- Refresh Feedback -->
    <div v-if="refreshMessages.length" class="refresh-messages">
      <div 
        v-for="(message, index) in refreshMessages" 
        :key="index"
        :class="['refresh-message', message.type]"
      >
        {{ message.text }}
      </div>
    </div>

    <!-- Refresh Modal -->
    <div v-if="showModal" class="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div class="modal-content">
        <div class="modal-header">
          <h3 id="modal-title">Select Streams to Refresh</h3>
          <button @click="closeRefreshModal" class="modal-close-btn" aria-label="Close modal">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <div class="modal-body">
          <div v-if="streams.length === 0" class="no-streams">
            No streams available to refresh.
          </div>
          <div v-else class="stream-selection">
            <div class="select-all">
              <input 
                type="checkbox" 
                id="select-all" 
                :checked="isAllSelected" 
                @change="toggleSelectAll"
                aria-label="Select all streams"
              />
              <label for="select-all">Select All ({{ streams.length }})</label>
            </div>
            <div class="stream-list">
              <div class="stream-list-header">
                <span class="checkbox-column"></span>
                <span class="username-column">Username</span>
                <span class="platform-column">Platform</span>
                <span class="status-column">Status</span>
                <span class="url-column">Room URL</span>
              </div>
              <div 
                v-for="stream in streams" 
                :key="stream.id" 
                class="stream-item"
              >
                <input 
                  type="checkbox" 
                  :id="'stream-' + stream.id"
                  :value="stream.id"
                  v-model="selectedStreamIds"
                  :aria-label="'Select ' + stream.streamer_username"
                />
                <label :for="'stream-' + stream.id" class="stream-details">
                  <span class="username-column">{{ stream.streamer_username }}</span>
                  <span class="platform-column">{{ stream.type }}</span>
                  <span class="status-column">{{ stream.status }}</span>
                  <span class="url-column" :title="stream.room_url">
                    {{ truncateUrl(stream.room_url) }}
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button 
            @click="closeRefreshModal" 
            class="modal-btn cancel-btn"
            :disabled="modalLoading"
            aria-label="Cancel"
          >
            Cancel
          </button>
          <button 
            @click="refreshSelectedStreams" 
            class="modal-btn refresh-btn"
            :disabled="modalLoading || selectedStreamIds.length === 0"
            aria-label="Refresh selected streams"
          >
            <font-awesome-icon 
              :icon="modalLoading ? 'spinner' : 'sync-alt'" 
              :spin="modalLoading"
            />
            {{ modalLoading ? 'Refreshing...' : 'Refresh Selected' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Stream sections -->
    <div class="streams-section">
      <!-- Online Streams -->
      <div class="section-header" @click="toggleOnlineCollapse">
        <h3>Online Streams ({{ onlineStreams.length }})</h3>
        <font-awesome-icon :icon="isOnlineCollapsed ? 'chevron-down' : 'chevron-up'" />
      </div>
      <div v-show="!isOnlineCollapsed" :class="['stream-container', viewMode]">
        <StreamCard 
          v-for="stream in filteredOnlineStreams" 
          :key="stream.id"
          :stream="enhanceStreamWithUsername(stream)" 
          :detectionCount="getDetectionCount(stream)"
          :totalStreams="onlineStreams.length"
          @click="openStream(stream)"
          @detection-toggled="handleDetectionToggled"
          @status-change="handleStreamStatusChange"
        />
      </div>
      
      <!-- Offline Streams -->
      <div class="section-header offline-section" @click="toggleOfflineCollapse">
        <h3>Offline Streams ({{ offlineStreams.length }})</h3>
        <font-awesome-icon :icon="isOfflineCollapsed ? 'chevron-down' : 'chevron-up'" />
      </div>
      <div v-show="!isOfflineCollapsed" :class="['stream-container', viewMode]">
        <StreamCard 
          v-for="stream in filteredOfflineStreams" 
          :key="stream.id"
          :stream="enhanceStreamWithUsername(stream)" 
          :detectionCount="getDetectionCount(stream)"
          :totalStreams="offlineStreams.length"
          @click="openStream(stream)"
          @detection-toggled="handleDetectionToggled"
          @status-change="handleStreamStatusChange"
        />
      </div>
    </div>
  </section>
</template>

<script>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import StatCard from './StatCard.vue'
import StreamCard from './StreamCard.vue'
import axios from 'axios'

export default {
  name: 'DashboardTab',
  components: {
    StatCard,
    StreamCard
  },
  props: {
    dashboardStats: Object,
    streams: Array,
    detections: Object,
    agents: {
      type: Array,
      default: () => []
    }
  },
  emits: ['open-stream', 'refresh-streams', 'update-streams'],
  setup(props, { emit }) {
    const searchQuery = ref('');
    const viewMode = ref('grid');
    const isOnlineCollapsed = ref(false);
    const isOfflineCollapsed = ref(true);
    const notifications = ref([]);
    const isLoading = ref(true);
    const refreshing = ref(false);
    const refreshMessages = ref([]);
    const showModal = ref(false);
    const selectedStreamIds = ref([]);
    const modalLoading = ref(false);

    // Computed stats with fallback
    const stats = computed(() => [{
      value: props.streams.filter(s => s.status === 'online' || s.status === 'monitoring').length,
      label: 'Active Streams',
      icon: 'broadcast-tower'
    }, {
      value: (notifications.value || []).filter(n => 
        ['object_detection', 'audio_detection', 'chat_detection'].includes(n.event_type)
      ).length,
      label: 'Total Detections',
      icon: 'exclamation-triangle'
    }, {
      value: props.agents.filter(a => a.status === 'active').length,
      label: 'Active Agents',
      icon: 'user-shield'
    }]);

    // Include 'online' and 'monitoring' statuses in Online Streams
    const onlineStreams = computed(() => 
      props.streams.filter(s => s.status === 'online' || s.status === 'monitoring')
    );

    // Exclude 'online' and 'monitoring' from Offline Streams
    const offlineStreams = computed(() => 
      props.streams.filter(s => s.status !== 'online' && s.status !== 'monitoring')
    );

    const filteredOnlineStreams = computed(() => 
      onlineStreams.value.filter(s => 
        s.streamer_username.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    );

    const filteredOfflineStreams = computed(() => 
      offlineStreams.value.filter(s => 
        s.streamer_username.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    );

    const isAllSelected = computed(() => 
      props.streams.length > 0 && 
      selectedStreamIds.value.length === props.streams.length
    );

    const enhanceStreamWithUsername = (stream) => {
      if (!stream || !props.agents) return stream;
      const assignedAgent = props.agents.find(a => a.id === stream.assigned_agent_id);
      return {
        ...stream,
        agent: {
          username: assignedAgent?.username || 'Unassigned',
          status: assignedAgent?.status || 'inactive'
        }
      };
    };

    const handleDetectionToggled = ({ streamId, active }) => {
      const updatedStreams = props.streams.map(s => 
        s.id === streamId ? { ...s, isDetecting: active } : s
      );
      emit('update-streams', updatedStreams);
    };

    const handleStreamStatusChange = ({ streamId, newStatus }) => {
      const updatedStreams = props.streams.map(s => 
        s.id === streamId ? { ...s, status: newStatus } : s
      );
      emit('update-streams', updatedStreams);
    };

    const getDetectionCount = (stream) => 
      props.detections[stream.room_url]?.length || 0;

    const addRefreshMessage = (text, type = 'info') => {
      refreshMessages.value.push({ text, type });
      setTimeout(() => {
        refreshMessages.value.shift();
      }, 5000);
    };

    const openRefreshModal = () => {
      selectedStreamIds.value = []; // Reset selections
      showModal.value = true;
    };

    const closeRefreshModal = () => {
      if (!modalLoading.value) {
        showModal.value = false;
        selectedStreamIds.value = [];
      }
    };

    const toggleSelectAll = () => {
      if (isAllSelected.value) {
        selectedStreamIds.value = [];
      } else {
        selectedStreamIds.value = props.streams.map(stream => stream.id);
      }
    };

    const truncateUrl = (url) => {
      const maxLength = 30;
      return url.length > maxLength ? url.substring(0, maxLength - 3) + '...' : url;
    };

    const refreshSelectedStreams = async () => {
      if (selectedStreamIds.value.length === 0) {
        addRefreshMessage('Please select at least one stream to refresh.', 'error');
        return;
      }

      refreshing.value = true;
      modalLoading.value = true;
      refreshMessages.value = []; // Clear previous messages

      try {
        addRefreshMessage('Refreshing selected streams...', 'info');
        const response = await axios.post('/api/streams/refresh_selected', {
          stream_ids: selectedStreamIds.value
        });
        if (response.status === 200) {
          addRefreshMessage('Streams refreshed and monitoring started.', 'success');
          const { data } = await axios.get('/api/streams');
          emit('update-streams', data);
        } else {
          addRefreshMessage('Failed to refresh streams.', 'error');
        }
      } catch (error) {
        console.error('Error refreshing streams:', error);
        addRefreshMessage(`Error: ${error.response?.data?.error || error.message}`, 'error');
      } finally {
        refreshing.value = false;
        modalLoading.value = false;
        showModal.value = false;
        selectedStreamIds.value = [];
      }
    };

    const openStream = (stream) => emit('open-stream', stream);
    const toggleViewMode = () => viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid';
    const toggleOnlineCollapse = () => isOnlineCollapsed.value = !isOnlineCollapsed.value;
    const toggleOfflineCollapse = () => isOfflineCollapsed.value = !isOfflineCollapsed.value;

    // Fetch notifications on mount
    onMounted(async () => {
      try {
        const { data } = await axios.get('/api/notifications');
        notifications.value = data || [];
        isLoading.value = false;
      } catch (error) {
        console.error('Error fetching notifications:', error);
        addRefreshMessage('Failed to load notifications.', 'error');
        notifications.value = [];
        isLoading.value = false;
      }
    });

    // Handle Esc key for modal
    const handleEsc = (e) => {
      if (e.key === 'Escape' && showModal.value) {
        closeRefreshModal();
      }
    };

    onMounted(() => {
      window.addEventListener('keydown', handleEsc);
    });

    onUnmounted(() => {
      window.removeEventListener('keydown', handleEsc);
    });
    
    return {
      stats,
      searchQuery,
      viewMode,
      isOnlineCollapsed,
      isOfflineCollapsed,
      onlineStreams,
      offlineStreams,
      filteredOnlineStreams,
      filteredOfflineStreams,
      getDetectionCount,
      openStream,
      handleDetectionToggled,
      enhanceStreamWithUsername,
      handleStreamStatusChange,
      toggleViewMode,
      toggleOnlineCollapse,
      toggleOfflineCollapse,
      isLoading,
      refreshing,
      refreshMessages,
      showModal,
      selectedStreamIds,
      modalLoading,
      isAllSelected,
      openRefreshModal,
      closeRefreshModal,
      toggleSelectAll,
      truncateUrl,
      refreshSelectedStreams
    };
  }
}
</script>

<style scoped>
.dashboard-tab {
  width: auto;
  padding-right: 20px;
}

.dashboard-header h2 {
  margin: 0 0 2rem;
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-color);
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.controls-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.6;
  color: var(--text-color);
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 35px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--input-bg);
  color: var(--text-color);
  font-size: 0.9rem;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

.view-toggle-btn, .refresh-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.2s, box-shadow 0.2s;
}

.view-toggle-btn:hover, .refresh-btn:hover {
  background: var(--primary-hover);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.view-toggle-btn:focus, .refresh-btn:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

.view-toggle-btn:disabled, .refresh-btn:disabled {
  background: var(--disabled-color);
  cursor: not-allowed;
  box-shadow: none;
}

.refresh-messages {
  margin-bottom: 1rem;
}

.refresh-message {
  padding: 8px 12px;
  margin-bottom: 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.refresh-message.info {
  background: var(--info-bg);
  color: var(--info-text);
}

.refresh-message.success {
  background: var(--success-bg);
  color: var(--success-text);
}

.refresh-message.error {
  background: var(--error-bg);
  color: var(--error-text);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: var(--modal-bg, black);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 1rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-color);
}

.modal-close-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: var(--text-color);
  padding: 0.5rem;
  border-radius: 4px;
  transition: color 0.2s, background 0.2s;
}

.modal-close-btn:hover, .modal-close-btn:focus {
  color: var(--primary-color);
  background: var(--input-bg);
  outline: none;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 0 1rem;
}

.no-streams {
  text-align: center;
  color: var(--text-color);
  padding: 1.5rem;
  font-size: 0.9rem;
}

.stream-selection {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.select-all {
  padding: 0.75rem;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  display: flex;
  align-items: center;
}

.select-all input {
  margin-right: 0.75rem;
  width: 1.2rem;
  height: 1.2rem;
  cursor: pointer;
}

.select-all input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
}

.select-all label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-color);
  cursor: pointer;
}

.stream-list {
  max-height: 50vh;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--input-bg);
}

.stream-list-header {
  display: grid;
  grid-template-columns: 50px 2fr 1fr 1fr 2fr;
  padding: 0.75rem 1rem;
  background: var(--input-bg);
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-color);
  position: sticky;
  top: 0;
  z-index: 1;
}

.stream-item {
  display: grid;
  grid-template-columns: 50px 2fr 1fr 1fr 2fr;
  padding: 0.75rem 1rem;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.9rem;
  color: var(--text-color);
}

.stream-item:nth-child(odd) {
  background: var(--secondary-rgb);
}

.stream-item:last-child {
  border-bottom: none;
  background: var(--secondary-rgb);
}

.stream-item:hover {
  background: rgba(var(--secondary-rgb), 0.05);
  
}

.stream-item input {
  margin: 0;
  width: 1.2rem;
  height: 1.2rem;
  cursor: pointer;
}

.stream-item input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
}

.stream-details {
  display: contents;
  cursor: pointer;
}

.stream-details span {
  padding: 0 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.username-column {
  font-weight: 500;
}

.platform-column {
  text-transform: capitalize;
  color: var(--text-secondary);
}

.status-column {
  text-transform: capitalize;
}

.url-column {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.checkbox-column {
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-footer {
  padding-top: 1rem;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  border-top: 1px solid var(--border-color);
}

.modal-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s, box-shadow 0.2s;
}

.cancel-btn {
  background: var(--secondary-color);
  color: white;
}

.cancel-btn:hover, .cancel-btn:focus {
  background: var(--secondary-hover);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  outline: none;
}

.refresh-btn {
  background: var(--primary-color);
  color: white;
}

.refresh-btn:hover, .refresh-btn:focus {
  background: var(--primary-hover);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  outline: none;
}

.modal-btn:disabled {
  background: var(--disabled-color);
  cursor: not-allowed;
  box-shadow: none;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0 1rem;
  cursor: pointer;
}

.section-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-color);
}

.stream-container {
  display: grid;
  gap: 1rem;
}

.stream-container.grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.stream-container.list {
  grid-template-columns: 1fr;
  width: 100%;
  height: 20%;
  display: flex;  
}

[data-tooltip] {
  position: relative;
}

[data-tooltip]:hover:after {
  content: attr(data-tooltip);
  position: absolute;
  top: -2rem;
  left: 50%;
  transform: translateX(-50%);
  background: var(--tooltip-bg);
  color: var(--tooltip-text);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  white-space: nowrap;
  z-index: 10;
}

@media (max-width: 768px) {
  .dashboard-tab {
    margin-left: 10px;
    padding-right: 10px;
  }

  .controls-section {
    flex-direction: column;
  }
  
  .search-box {
    max-width: 100%;
  }
  
  .view-controls {
    width: 100%;
    display: flex;
    gap: 0.5rem;
  }
  
  .view-toggle-btn, .refresh-btn {
    flex: 1;
    justify-content: center;
  }

  .modal-content {
    width: 95%;
    max-width: 95%;
    padding: 1rem;
  }

  .modal-footer {
    flex-direction: column;
    gap: 0.5rem;
  }

  .modal-btn {
    width: 100%;
    justify-content: center;
  }

  .stream-list-header, .stream-item {
    grid-template-columns: 50px 1fr 1fr;
  }

  .status-column, .url-column {
    display: none;
  }

  .select-all input, .stream-item input {
    width: 1.4rem;
    height: 1.4rem;
  }
}
</style>