<template>
  <section class="agent-streams">
    <div class="dashboard-header">
      <h2>Agent Streams</h2>
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

    <!-- Skeleton for Stats Section -->
    <div v-if="localIsLoading" class="stats-section skeleton">
      <div v-for="n in 3" :key="'stat-skeleton-' + n" class="skeleton-stat-card">
        <div class="skeleton-icon"></div>
        <div class="skeleton-text skeleton-value"></div>
        <div class="skeleton-text skeleton-label"></div>
      </div>
    </div>

    <!-- Search and Controls -->
    <div class="controls-section">
      <div class="search-box">
        <font-awesome-icon icon="search" class="search-icon" />
        <input v-model="searchQuery" placeholder="Search assigned streams..." class="search-input" />
      </div>
      <div class="view-controls" style="display: flex; gap: 1rem;">
        <button 
          @click="refreshStreams" 
          class="view-toggle-btn refresh-btn"
          :disabled="refreshing"
          v-tooltip="'Refreshes one stream at a time to avoid crashing'"
        >
          <font-awesome-icon 
            :icon="refreshing ? 'spinner' : 'sync-alt'" 
            :spin="refreshing"
          />
          {{ refreshing ? 'Refreshing...' : 'Refresh All' }}
        </button>
      </div>
    </div>

    <!-- Skeleton for Controls Section -->
    <div v-if="localIsLoading" class="controls-section skeleton">
      <div class="search-box skeleton">
        <div class="search-icon skeleton-icon"></div>
        <div class="search-input skeleton-input"></div>
      </div>
      <div class="view-controls" style="display: flex; gap: 1rem;">
        <div class="view-toggle-btn refresh-btn skeleton-button"></div>
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

    <!-- Streams section -->
    <div class="streams-section">
      <div class="stream-container" :class="viewMode">
        <StreamCard 
          v-for="stream in filteredStreams" 
          :key="stream.id"
          :stream="enhanceStreamWithUsername(stream)" 
          :detectionCount="getDetectionCount(stream)"
          :totalStreams="localStreams.length"
          :agentUsername="stream.agent?.username"
          @click="openStreamDetails(stream)"
          @detection-toggled="handleDetectionToggled"
          @status-change="handleStreamStatusChange"
        />
      </div>
      
      <!-- Skeleton for Streams Section -->
      <div v-if="localIsLoading" class="stream-container grid skeleton">
        <div v-for="n in 3" :key="'stream-skeleton-' + n" class="skeleton-stream-card">
          <div class="skeleton-stream-image"></div>
          <div class="skeleton-stream-content">
            <div class="skeleton-text skeleton-stream-title"></div>
            <div class="skeleton-text skeleton-stream-info"></div>
            <div class="skeleton-text skeleton-stream-info"></div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div class="empty-state" v-if="localStreams.length === 0 && !localIsLoading">
        <font-awesome-icon icon="video-slash" class="empty-icon" />
        <div class="empty-title">No streams assigned</div>
        <div class="empty-description">Streams assigned to you will appear here</div>
      </div>
    </div>

    <!-- Loading State -->
    <div class="loading-overlay" v-if="localIsLoading && !showSkeleton">
      <div class="loader-container">
        <div class="loader-circle"></div>
        <div class="loader-text">Loading streams...</div>
      </div>
    </div>
    
    <!-- Error Message -->
    <div class="error-message" v-if="localError && !localIsLoading">
      <font-awesome-icon icon="exclamation-triangle" class="error-icon" />
      <div class="error-text">{{ localError }}</div>
      <button class="retry-button" @click="fetchAssignedStreams">
        <font-awesome-icon icon="sync" />
        <span>Retry</span>
      </button>
    </div>

    <!-- Stream Details Modal -->
    <StreamDetailsModal
      v-if="showModal && selectedStream"
      :stream="enhanceStreamWithUsername(selectedStream)"
      :detections="selectedStreamDetections"
      :isRefreshing="isRefreshingStream"
      @close="closeModal"
      @refresh="handleStreamRefresh"
    />
  </section>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import StreamCard from './StreamCard.vue';
import StreamDetailsModal from './StreamDetailsModal.vue';
import StatCard from './StatCard.vue';
import axios from 'axios';
import {
  faSync,
  faVideoSlash,
  faExclamationTriangle,
  faSearch,
  faSyncAlt,
  faSpinner
} from '@fortawesome/free-solid-svg-icons';

library.add(faSync, faVideoSlash, faExclamationTriangle, faSearch, faSyncAlt, faSpinner);

export default {
  name: 'AgentStreamsComponent',
  components: {
    FontAwesomeIcon,
    StreamCard,
    StreamDetailsModal,
    StatCard
  },
  props: {
    agentId: {
      type: [Number, String],
      default: null
    },
    streams: {
      type: Array,
      default: () => []
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    },
    detections: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['open-stream', 'refresh-streams', 'update-streams'],
  setup(props, { emit }) {
    // Core state
    const showModal = ref(false);
    const selectedStream = ref(null);
    const selectedStreamDetections = ref([]);
    const isRefreshingStream = ref(false);
    const viewMode = ref('grid');
    const localStreams = ref([]);
    const localIsLoading = ref(false);
    const localError = ref(null);
    const currentAgentId = ref(null);
    const agentData = ref(null);
    const agents = ref([]);
    const searchQuery = ref('');
    const notifications = ref([]);
    const refreshing = ref(false);
    const refreshMessages = ref([]);
    const showSkeleton = ref(true); // Control skeleton visibility

    // Computed properties
    const filteredStreams = computed(() => {
      const filtered = localStreams.value.filter(s => 
        s.streamer_username.toLowerCase().includes(searchQuery.value.toLowerCase())
      );
      return filtered.sort((a, b) => {
        const aIsLive = isStreamLive(a);
        const bIsLive = isStreamLive(b);
        return (bIsLive - aIsLive) || (a.streamer_username.localeCompare(b.streamer_username));
      });
    });

    const stats = computed(() => [{
      value: localStreams.value.filter(stream => isStreamLive(stream)).length,
      label: 'Assigned Live Streams',
      icon: 'broadcast-tower'
    }, {
      value: notifications.value.filter(n => 
        ['object_detection', 'audio_detection', 'chat_detection'].includes(n.event_type) &&
        localStreams.value.some(s => s.room_url === n.room_url)
      ).length,
      label: 'Detections in Assigned Streams',
      icon: 'exclamation-triangle'
    }, {
      value: agents.value.filter(a => a.id === currentAgentId.value && a.status === 'active').length,
      label: 'Agent Status',
      icon: 'user-shield'
    }]);

    // Core functions
    const isStreamLive = (stream) => {
      if (!stream) return false;
      const platform = stream.platform?.toLowerCase();
      return platform === 'chaturbate' ? !!stream.chaturbate_m3u8_url :
             platform === 'stripchat' ? !!stream.stripchat_m3u8_url :
             false;
    };

    const fetchCurrentAgent = async () => {
      try {
        const response = await axios.get('/api/session');
        if (response.data?.isLoggedIn) {
          currentAgentId.value = response.data.user.id;
          agentData.value = response.data.user;
          return response.data.user;
        }
        return null;
      } catch (error) {
        console.error('Error fetching current agent:', error);
        return null;
      }
    };

    const fetchAgents = async () => {
      try {
        const response = await axios.get('/api/agents');
        agents.value = response.data || [];
      } catch (error) {
        console.error('Error fetching agents:', error);
      }
    };
    
    const fetchAssignedStreams = async () => {
      if (localIsLoading.value) return;
      
      localIsLoading.value = true;
      localError.value = null;
      
      try {
        if (!currentAgentId.value) {
          const agent = await fetchCurrentAgent();
          if (!agent) {
            localError.value = 'Unable to authenticate. Please log in again.';
            return;
          }
        }

        if (agents.value.length === 0) {
          await fetchAgents();
        }
        
        const response = await axios.get('/api/streams');
        localStreams.value = (response.data || []).filter(stream =>
          stream.assignments?.some(assignment =>
            assignment.agent_id === currentAgentId.value &&
            assignment.status === 'active'
          )
        ).map(stream => ({
          ...stream,
          streamer_username: stream.streamer_username || stream.room_url.split('/').pop()
        }));
      } catch (error) {
        console.error('Error fetching streams:', error);
        localError.value = 'Failed to load streams. Please try again.';
      } finally {
        localIsLoading.value = false;
        showSkeleton.value = false; // Hide skeleton after loading
      }
    };

    const fetchNotifications = async () => {
      try {
        const { data } = await axios.get('/api/notifications');
        notifications.value = data;
      } catch (error) {
        console.error('Error fetching notifications:', error);
      }
    };

    const enhanceStreamWithUsername = (stream) => {
      if (!stream) return stream;
      const enhanced = JSON.parse(JSON.stringify(stream));
      
      if (enhanced.assignments?.length) {
        enhanced.assignments = enhanced.assignments.map(assignment => {
          const username = assignment.agent?.username ||
            agents.value.find(a => a.id === assignment.agent_id)?.username ||
            (assignment.agent_id === currentAgentId.value ? agentData.value?.username : null) ||
            `Agent ${assignment.agent_id}`;
          return {
            ...assignment,
            agent_username: username,
            stream_id: assignment.stream_id
          };
        });
        const currentAssignment = enhanced.assignments.find(a => a.agent_id === currentAgentId.value);
        enhanced.agent = {
          username: currentAssignment?.agent_username || 'Unassigned',
          status: currentAssignment?.status || 'inactive'
        };
      } else {
        enhanced.agent = { username: 'Unassigned', status: 'inactive' };
      }
      
      return enhanced;
    };
    
    const openStreamDetails = (stream) => {
      selectedStream.value = stream;
      selectedStreamDetections.value = props.detections[stream.room_url] || [];
      showModal.value = true;
      emit('open-stream', stream);
    };
    
    const closeModal = () => {
      showModal.value = false;
      selectedStream.value = null;
    };
    
    const handleStreamRefresh = async (streamId) => {
      isRefreshingStream.value = true;
      try {
        const response = await axios.put(`/api/streams/${streamId}`, { refresh: true });
        if (response.data?.stream) {
          const streamIndex = localStreams.value.findIndex(s => s.id === streamId);
          if (streamIndex >= 0) {
            localStreams.value[streamIndex] = response.data.stream;
            if (selectedStream.value?.id === streamId) {
              selectedStream.value = response.data.stream;
            }
            emit('update-streams', localStreams.value);
          }
        }
      } catch (error) {
        console.error('Error refreshing stream:', error);
        localError.value = 'Failed to refresh stream. Please try again.';
      } finally {
        isRefreshingStream.value = false;
      }
    };

    const addRefreshMessage = (text, type = 'info') => {
      refreshMessages.value.push({ text, type });
      setTimeout(() => {
        refreshMessages.value.shift();
      }, 5000);
    };

    const refreshStreams = async () => {
      if (refreshing.value) return;
      refreshing.value = true;
      refreshMessages.value = [];

      try {
        for (const stream of localStreams.value) {
          try {
            let endpoint, payload;
            if (stream.platform === 'chaturbate') {
              endpoint = '/api/streams/refresh/chaturbate';
              payload = { room_slug: stream.streamer_username };
            } else if (stream.platform === 'stripchat') {
              endpoint = '/api/streams/refresh/stripchat';
              payload = { room_url: stream.room_url };
            } else {
              addRefreshMessage(`Unsupported platform for ${stream.streamer_username}`, 'error');
              continue;
            }

            addRefreshMessage(`Refreshing ${stream.streamer_username}...`, 'info');
            const response = await axios.post(endpoint, payload);
            if (response.data.m3u8_url) {
              const updatedStreams = localStreams.value.map(s => 
                s.id === stream.id 
                  ? { 
                      ...s, 
                      [stream.platform === 'chaturbate' ? 'chaturbate_m3u8_url' : 'stripchat_m3u8_url']: response.data.m3u8_url 
                    } 
                  : s
              );
              localStreams.value = updatedStreams;
              emit('update-streams', updatedStreams);
              addRefreshMessage(`Refreshed ${stream.streamer_username} successfully`, 'success');
            } else {
              addRefreshMessage(`Failed to refresh ${stream.streamer_username}`, 'error');
            }
          } catch (error) {
            console.error(`Error refreshing ${stream.streamer_username}:`, error);
            addRefreshMessage(`Error refreshing ${stream.streamer_username}: ${error.response?.data?.message || error.message}`, 'error');
          }
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      } finally {
        refreshing.value = false;
      }
    };

    const handleDetectionToggled = ({ streamId, active }) => {
      const updatedStreams = localStreams.value.map(s => 
        s.id === streamId ? { ...s, isDetecting: active } : s
      );
      localStreams.value = updatedStreams;
      emit('update-streams', updatedStreams);
    };

    const handleStreamStatusChange = ({ streamId, newStatus }) => {
      const updatedStreams = localStreams.value.map(s => 
        s.id === streamId ? { ...s, status: newStatus } : s
      );
      localStreams.value = updatedStreams;
      emit('update-streams', updatedStreams);
    };

    const getDetectionCount = (stream) => 
      props.detections[stream.room_url]?.length || 0;

    onMounted(async () => {
      showSkeleton.value = true; // Show skeleton on mount
      await fetchAssignedStreams();
      await fetchNotifications();
    });

    return {
      viewMode,
      showModal,
      selectedStream,
      selectedStreamDetections,
      isRefreshingStream,
      filteredStreams,
      localStreams,
      localIsLoading,
      localError,
      stats,
      searchQuery,
      fetchAssignedStreams,
      openStreamDetails,
      closeModal,
      handleStreamRefresh,
      enhanceStreamWithUsername,
      handleDetectionToggled,
      handleStreamStatusChange,
      getDetectionCount,
      refreshStreams,
      refreshing,
      refreshMessages,
      showSkeleton
    };
  }
}
</script>

<style scoped>
.agent-streams {
  width: auto;
  padding-right: 20px;
  margin-left: 60px;
}

.dashboard-header h2 {
  margin: 0 0 2rem;
  font-size: 2rem;
  font-weight: 600;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stats-section.skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.skeleton-stat-card {
  background: var(--hover-color);
  border-radius: 6px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
}

.skeleton-icon {
  width: 24px;
  height: 24px;
  background: var(--border-color);
  border-radius: 50%;
  margin-bottom: 0.5rem;
  animation: pulse 1.5s infinite;
}

.skeleton-text {
  background: var(--border-color);
  border-radius: 4px;
  animation: pulse 1.5s infinite;
}

.skeleton-value {
  width: 60%;
  height: 20px;
  margin-bottom: 0.5rem;
}

.skeleton-label {
  width: 80%;
  height: 16px;
}

.controls-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.controls-section.skeleton {
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

.search-box.skeleton {
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
}

.search-icon.skeleton-icon {
  width: 16px;
  height: 16px;
  background: var(--border-color);
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 35px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--input-bg);
  color: var(--text-color);
}

.search-input.skeleton-input {
  width: 100%;
  height: 36px;
  background: var(--border-color);
  border-radius: 6px;
  animation: pulse 1.5s infinite;
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
}

.view-toggle-btn:disabled, .refresh-btn:disabled {
  background: var(--disabled-color);
  cursor: not-allowed;
}

.refresh-btn.skeleton-button {
  width: 120px;
  height: 36px;
  background: var(--border-color);
  border-radius: 6px;
  animation: pulse 1.5s infinite;
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

.stream-container {
  display: grid;
  gap: 1rem;
}

.stream-container.grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.stream-container.grid.skeleton {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.stream-container.list {
  grid-template-columns: 1fr;
  width: 100%;
  height: 20%;
  display: flex;  
}

.skeleton-stream-card {
  background: var(--hover-color);
  border-radius: 6px;
  padding: 1rem;
  display: flex;
  gap: 1rem;
  height: 150px;
}

.skeleton-stream-image {
  width: 100px;
  height: 100px;
  background: var(--border-color);
  border-radius: 6px;
  animation: pulse 1.5s infinite;
}

.skeleton-stream-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skeleton-stream-title {
  width: 70%;
  height: 20px;
}

.skeleton-stream-info {
  width: 50%;
  height: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  background-color: var(--hover-color);
  border-radius: 8px;
  margin: 30px 0;
}

.empty-icon {
  font-size: 2.5rem;
  color: var(--border-color);
  margin-bottom: 15px;
}

.empty-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 10px;
}

.empty-description {
  color: var(--text-color);
  margin-bottom: 20px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: var(--bg-color);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.19);
}

.loader-circle {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

.loader-text {
  font-size: 1rem;
  font-weight: 500;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  margin: 20px 0;
  background-color: rgba(220, 53, 69, 0.1);
  border-left: 4px solid #dc3545;
  border-radius: 6px;
}

.error-icon {
  color: #dc3545;
  font-size: 1.2rem;
}

.error-text {
  flex: 1;
}

.retry-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  background-color: var(--accent-color);
  color: white;
  cursor: pointer;
}

.retry-button:hover {
  background-color: var(--hover-color);
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .controls-section, .controls-section.skeleton {
    flex-direction: column;
  }
  
  .search-box, .search-box.skeleton {
    max-width: 100%;
  }
  
  .view-controls {
    width: 100%;
    display: flex;
    gap: 0.5rem;
  }
  
  .view-toggle-btn, .refresh-btn, .skeleton-button {
    flex: 1;
    justify-content: center;
  }
}
</style>