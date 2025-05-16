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
        <button @click="refreshStreams" class="view-toggle-btn refresh-btn">
          <font-awesome-icon icon="sync-alt" />
          Refresh All
        </button>
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
</style>