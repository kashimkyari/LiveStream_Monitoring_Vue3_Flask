<template>
  <section class="dashboard-tab">
    <div class="dashboard-header">
      <h2>Dashboard</h2>
    </div>

    <!-- Stats section with skeleton loading -->
    <div class="stats-section">
      <template v-if="!isLoading">
        <StatCard 
          v-for="stat in stats"
          :key="stat.label"
          :value="stat.value"
          :label="stat.label"
          :icon="stat.icon"
        />
      </template>
      <template v-else>
        <div v-for="i in 3" :key="i" class="dashboard-skeleton stat-card">
          <div class="skeleton-icon"></div>
          <div class="skeleton-content">
            <div class="skeleton-value"></div>
            <div class="skeleton-label"></div>
          </div>
        </div>
      </template>
    </div>

    <!-- Search and Controls -->
    <div class="controls-section">
      <div class="search-box">
        <font-awesome-icon icon="search" class="search-icon" />
        <input v-model="searchQuery" placeholder="Search streams..." class="search-input" />
      </div>
      <div class="view-controls" style="display: flex; gap: 1rem;">
        
        <button @click="refreshStreams" class="view-toggle-btn refresh-btn">
          <font-awesome-icon icon="sync-alt" />
          Refresh All
        </button>
      </div>
    </div>

    <!-- Stream sections with skeleton loading -->
    <div class="streams-section">
      <!-- Online Streams -->
      <div class="section-header" @click="toggleOnlineCollapse">
        <h3>Online Streams {{ !isLoading ? `(${onlineStreams.length})` : '' }}</h3>
        <font-awesome-icon :icon="isOnlineCollapsed ? 'chevron-down' : 'chevron-up'" />
      </div>
      <div v-show="!isOnlineCollapsed" :class="['stream-container', viewMode]">
        <template v-if="!isLoading">
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
        </template>
        <template v-else>
          <div v-for="i in 3" :key="i" class="dashboard-skeleton stream-card">
            <div class="skeleton-thumbnail"></div>
            <div class="skeleton-content">
              <div class="skeleton-header">
                <div class="skeleton-title"></div>
                <div class="skeleton-tag"></div>
              </div>
              <div class="skeleton-info">
                <div class="skeleton-text"></div>
                <div class="skeleton-text"></div>
              </div>
            </div>
          </div>
        </template>
      </div>
      
      <!-- Offline Streams -->
      <div class="section-header offline-section" @click="toggleOfflineCollapse">
        <h3>Offline Streams {{ !isLoading ? `(${offlineStreams.length})` : '' }}</h3>
        <font-awesome-icon :icon="isOfflineCollapsed ? 'chevron-down' : 'chevron-up'" />
      </div>
      <div v-show="!isOfflineCollapsed" :class="['stream-container', viewMode]">
        <template v-if="!isLoading">
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
        </template>
        <template v-else>
          <div v-for="i in 3" :key="i" class="dashboard-skeleton stream-card">
            <div class="skeleton-thumbnail"></div>
            <div class="skeleton-content">
              <div class="skeleton-header">
                <div class="skeleton-title"></div>
                <div class="skeleton-tag"></div>
              </div>
              <div class="skeleton-info">
                <div class="skeleton-text"></div>
                <div class="skeleton-text"></div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
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
    
    // Computed stats
    const stats = computed(() => [{
      value: props.streams.filter(s => s.status === 'online').length,
      label: 'Active Streams',
      icon: 'broadcast-tower'
    }, {
      value: notifications.value.filter(n => 
        ['object_detection', 'audio_detection', 'chat_detection'].includes(n.event_type)
      ).length,
      label: 'Total Detections',
      icon: 'exclamation-triangle'
    }, {
      value: props.agents.filter(a => a.status === 'active').length,
      label: 'Active Agents',
      icon: 'user-shield'
    }]);

    const onlineStreams = computed(() => 
      props.streams.filter(s => s.status === 'online')
    );

    const offlineStreams = computed(() => 
      props.streams.filter(s => s.status !== 'online')
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
    
    const openStream = (stream) => emit('open-stream', stream);
    const toggleViewMode = () => viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid';
    const refreshStreams = () => emit('refresh-streams', { all: true });
    const toggleOnlineCollapse = () => isOnlineCollapsed.value = !isOnlineCollapsed.value;
    const toggleOfflineCollapse = () => isOfflineCollapsed.value = !isOfflineCollapsed.value;
    
    onMounted(async () => {
      try {
        const { data } = await axios.get('/api/notifications');
        notifications.value = data;
        isLoading.value = false;
      } catch (error) {
        console.error('Error fetching notifications:', error);
        isLoading.value = false;
      }
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
      refreshStreams,
      toggleOnlineCollapse,
      toggleOfflineCollapse,
      isLoading
    };
  }
}
</script>

<style scoped>
.dashboard-tab {
  width: 100%;
  padding-left: 1rem;
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
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 35px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--input-bg);
  color: var(--text-color);
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

@media (max-width: 768px) {
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
}

/* Skeleton Loading Styles */
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.skeleton-base {
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 8%,
    var(--skeleton-highlight) 18%,
    var(--skeleton-base) 33%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
}

.stat-skeleton {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  gap: 1rem;
  align-items: center;
  box-shadow: var(--shadow-sm);
}

.skeleton-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 8%,
    var(--skeleton-highlight) 18%,
    var(--skeleton-base) 33%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
}

.skeleton-content {
  flex: 1;
}

.skeleton-value {
  height: 24px;
  width: 60%;
  margin-bottom: 8px;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 8%,
    var(--skeleton-highlight) 18%,
    var(--skeleton-base) 33%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
}

.skeleton-label {
  height: 16px;
  width: 80%;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 8%,
    var(--skeleton-highlight) 18%,
    var(--skeleton-base) 33%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
}

.stream-skeleton {
  background: var(--card-bg);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.skeleton-thumbnail {
  width: 100%;
  height: 160px;
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 8%,
    var(--skeleton-highlight) 18%,
    var(--skeleton-base) 33%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
}

.skeleton-content {
  padding: 1rem;
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.skeleton-title {
  height: 20px;
  width: 60%;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 8%,
    var(--skeleton-highlight) 18%,
    var(--skeleton-base) 33%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
}

.skeleton-tag {
  height: 20px;
  width: 80px;
  border-radius: 20px;
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 8%,
    var(--skeleton-highlight) 18%,
    var(--skeleton-base) 33%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
}

.skeleton-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-text {
  height: 16px;
  width: 100%;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 8%,
    var(--skeleton-highlight) 18%,
    var(--skeleton-base) 33%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
}

.skeleton-text:last-child {
  width: 70%;
}

[data-theme='dark'] {
  --skeleton-base: rgba(255, 255, 255, 0.05);
  --skeleton-highlight: rgba(255, 255, 255, 0.1);
}

[data-theme='light'] {
  --skeleton-base: rgba(0, 0, 0, 0.05);
  --skeleton-highlight: rgba(0, 0, 0, 0.1);
}

/* Dashboard-specific Skeleton Loading Styles */
@keyframes dashboardShimmer {
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}

.dashboard-skeleton {
  background: var(--card-bg);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.dashboard-skeleton.stat-card {
  padding: 1rem;
  display: flex;
  gap: 1rem;
  align-items: center;
}

.dashboard-skeleton.stream-card {
  height: auto;
  display: flex;
  flex-direction: column;
}

.skeleton-thumbnail {
  width: 100%;
  height: 160px;
  background: var(--skeleton-bg);
  animation: dashboardShimmer 2s infinite linear;
}

.skeleton-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--skeleton-bg);
  animation: dashboardShimmer 2s infinite linear;
}

.skeleton-content {
  flex: 1;
  padding: 1rem;
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.skeleton-title {
  height: 20px;
  width: 60%;
  border-radius: 4px;
  background: var(--skeleton-bg);
  animation: dashboardShimmer 2s infinite linear;
}

.skeleton-tag {
  height: 20px;
  width: 80px;
  border-radius: 20px;
  background: var(--skeleton-bg);
  animation: dashboardShimmer 2s infinite linear;
}

.skeleton-value {
  height: 24px;
  width: 60%;
  margin-bottom: 8px;
  border-radius: 4px;
  background: var(--skeleton-bg);
  animation: dashboardShimmer 2s infinite linear;
}

.skeleton-label {
  height: 16px;
  width: 80%;
  border-radius: 4px;
  background: var(--skeleton-bg);
  animation: dashboardShimmer 2s infinite linear;
}

.skeleton-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-text {
  height: 16px;
  border-radius: 4px;
  background: var(--skeleton-bg);
  animation: dashboardShimmer 2s infinite linear;
}

.skeleton-text:first-child {
  width: 100%;
}

.skeleton-text:last-child {
  width: 70%;
}

/* Dashboard-specific theme variables */
:root {
  --skeleton-bg: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.05) 8%,
    rgba(0, 0, 0, 0.1) 18%,
    rgba(0, 0, 0, 0.05) 33%
  );
}

[data-theme='dark'] {
  --skeleton-bg: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.05) 8%,
    rgba(255, 255, 255, 0.1) 18%,
    rgba(255, 255, 255, 0.05) 33%
  );
}
</style>