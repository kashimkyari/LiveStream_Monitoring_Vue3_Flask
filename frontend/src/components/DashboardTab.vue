<template>
  <section class="dashboard-tab">
    <div class="dashboard-header">
      <h2>Stream Dashboard</h2>
    </div>

    <!-- Stats section (separate container outside of the stream grid) -->
    <div class="stats-section" ref="statsSection">
      <StatCard 
        v-for="(stat, index) in stats"
        :key="stat.label"
        :value="stat.value"
        :label="stat.label"
        :icon="stat.icon"
        :index="index"
        class="stat-card"
      />
    </div>

    <!-- Search and Controls -->
    <div class="controls-section">
      <div class="search-box">
        <font-awesome-icon icon="search" class="search-icon" />
        <input v-model="searchQuery" placeholder="Search streams..." class="search-input" />
      </div>
      <div class="view-controls">
        <button @click="toggleViewMode" class="view-toggle-btn">
          <font-awesome-icon :icon="viewMode === 'grid' ? 'list' : 'th-large'" />
          {{ viewMode === 'grid' ? 'List View' : 'Grid View' }}
        </button>
        <div class="refresh-control">
          <button @click="openRefreshModal" class="view-toggle-btn refresh-btn">
            <font-awesome-icon icon="sync-alt" />
            Refresh Streams
          </button>
        </div>
      </div>
    </div>

    <!-- Refresh Modal -->
    <div v-if="isRefreshModalOpen" class="modal-overlay">
      <div class="refresh-modal">
        <h3>Select Streams to Refresh</h3>
        <div class="checkbox-group">
          <label>
            <input type="checkbox" v-model="selectAllStreams" @change="toggleSelectAll" />
            Select All
          </label>
          <label v-for="stream in streams" :key="stream.id">
            <input type="checkbox" v-model="selectedStreams" :value="stream.id" />
            {{ stream.streamer_username }} ({{ stream.status === 'online' ? 'Online' : 'Offline' }})
          </label>
        </div>
        <div class="modal-buttons">
          <button @click="closeRefreshModal" class="cancel-btn">Cancel</button>
          <button @click="refreshSelectedStreams" class="confirm-btn">Refresh Selected</button>
        </div>
      </div>
    </div>

    <!-- Stream sections with headers -->
    <div class="streams-section">
      <!-- Online Streams -->
      <div class="section-header" @click="toggleOnlineCollapse">
        <h3>Online Streams</h3>
        <span class="stream-count">{{ onlineStreams.length }} streams</span>
        <font-awesome-icon :icon="isOnlineCollapsed ? 'chevron-down' : 'chevron-up'" class="collapse-icon" />
      </div>
      <div v-if="!isOnlineCollapsed" :class="['stream-container', viewMode === 'list' ? 'list-view' : 'grid-view']">
        <StreamCard 
          v-for="(stream, index) in filteredOnlineStreams" 
          :key="stream.id"
          :stream="enhanceStreamWithUsername(stream)" 
          :index="index"
          :detectionCount="getDetectionCount(stream)"
          :totalStreams="onlineStreams.length"
          class="stream-card"
          @click="openStream(stream, index)"
          @detection-toggled="handleDetectionToggled"
        ></StreamCard>
      </div>
      
      <!-- Offline Streams -->
      <div class="section-header offline-section" @click="toggleOfflineCollapse">
        <h3>Offline Streams</h3>
        <span class="stream-count">{{ offlineStreams.length }} streams</span>
        <font-awesome-icon :icon="isOfflineCollapsed ? 'chevron-down' : 'chevron-up'" class="collapse-icon" />
      </div>
      <div v-if="!isOfflineCollapsed" :class="['stream-container', viewMode === 'list' ? 'list-view' : 'grid-view']">
        <StreamCard 
          v-for="(stream, index) in filteredOfflineStreams" 
          :key="stream.id"
          :stream="enhanceStreamWithUsername(stream)" 
          :index="index"
          :detectionCount="getDetectionCount(stream)"
          :totalStreams="offlineStreams.length"
          class="stream-card"
          @click="openStream(stream, index)"
          @detection-toggled="handleDetectionToggled"
        ></StreamCard>
      </div>
    </div>
  </section>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import anime from 'animejs/lib/anime.es.js'
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
  emits: ['open-stream', 'refresh-streams'],
  setup(props, { emit }) {
    const statsSection = ref(null);
    const searchQuery = ref('');
    const viewMode = ref('grid'); // 'grid' or 'list'
    const isRefreshModalOpen = ref(false);
    const selectedStreams = ref([]);
    const selectAllStreams = ref(false);
    const isOnlineCollapsed = ref(true);
    const isOfflineCollapsed = ref(true);
    const notifications = ref([]);
    
    // Fetch notifications on mount
    const fetchNotifications = async () => {
      try {
        const response = await axios.get('/api/notifications');
        notifications.value = response.data;
      } catch (error) {
        console.error('Error fetching notifications:', error);
      }
    };
    
    // Compute dynamic stats based on props data and notifications
    const stats = computed(() => {
      // Count active streams (where status is 'online')
      const activeStreamsCount = props.streams.filter(stream => stream.status === 'online').length;
      
      // Compute total detections from notifications
      const totalDetectionsCount = notifications.value.filter(n => 
        n.event_type === 'object_detection' || 
        n.event_type === 'audio_detection' || 
        n.event_type === 'chat_detection'
      ).length;
      
      // Compute active agents (agents with status 'active')
      const activeAgentsCount = props.agents.filter(agent => agent.status === 'active').length;
      
      return [
        { 
          value: activeStreamsCount, 
        label: 'Active Streams',
        icon: 'broadcast-tower'
      },
      { 
          value: totalDetectionsCount, 
        label: 'Total Detections',
        icon: 'exclamation-triangle'
      },
      { 
          value: activeAgentsCount, 
        label: 'Active Agents',
        icon: 'user-shield'
      }
      ];
    });

    // Separate streams into online and offline
    const onlineStreams = computed(() => {
      return props.streams.filter(stream => stream.status === 'online');
    });

    const offlineStreams = computed(() => {
      return props.streams.filter(stream => stream.status !== 'online');
    });

    // Filtered streams based on search query
    const filteredOnlineStreams = computed(() => {
      return onlineStreams.value.filter(stream => 
        stream.streamer_username.toLowerCase().includes(searchQuery.value.toLowerCase())
      );
    });

    const filteredOfflineStreams = computed(() => {
      return offlineStreams.value.filter(stream => 
        stream.streamer_username.toLowerCase().includes(searchQuery.value.toLowerCase())
      );
    });

    // Add the enhanceStreamWithUsername function
    const enhanceStreamWithUsername = (stream) => {
      if (!stream || !props.agents) return stream;
      
      // Find the agent assigned to this stream
      const assignedAgent = props.agents.find(agent => agent.id === stream.assigned_agent_id);
      
      // Return enhanced stream with username info
      return {
        ...stream,
        agent: {
          username: assignedAgent ? assignedAgent.username : 'Unassigned',
          status: assignedAgent ? assignedAgent.status : 'inactive'
        }
      };
    };

    const handleDetectionToggled = (data) => {
      console.log(`Detection ${data.active ? 'started' : 'stopped'} for ${data.stream.streamer_username}`);
      // You can add additional logic here, like showing a notification
    };
    
    const getDetectionCount = (stream) => {
      return props.detections[stream.room_url]?.length || 0;
    };
    
    const openStream = (stream, index) => {
      // Animate the card click
      const clickedCard = document.querySelectorAll('.stream-card')[index];
      if (clickedCard) {
        anime({
          targets: clickedCard,
          scale: [1, 1.05, 1],
          duration: 400,
          easing: 'easeInOutQuad'
        });
      }
      
      // Emit the event after a short delay for better UX
      setTimeout(() => {
        emit('open-stream', stream);
      }, 150);
    };

    const toggleViewMode = () => {
      viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid';
    };

    const openRefreshModal = () => {
      isRefreshModalOpen.value = true;
    };

    const closeRefreshModal = () => {
      isRefreshModalOpen.value = false;
      selectedStreams.value = [];
      selectAllStreams.value = false;
    };

    const toggleSelectAll = () => {
      if (selectAllStreams.value) {
        selectedStreams.value = props.streams.map(stream => stream.id);
      } else {
        selectedStreams.value = [];
      }
    };

    const refreshSelectedStreams = () => {
      if (selectedStreams.value.length > 0) {
        emit('refresh-streams', { streamIds: selectedStreams.value });
      } else {
        emit('refresh-streams', { all: true });
      }
      closeRefreshModal();
    };

    const toggleOnlineCollapse = () => {
      isOnlineCollapsed.value = !isOnlineCollapsed.value;
    };

    const toggleOfflineCollapse = () => {
      isOfflineCollapsed.value = !isOfflineCollapsed.value;
    };
    
    onMounted(() => {
      // Animate the header with a fade-in and slide-up effect
      anime({
        targets: '.dashboard-header',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 600,
        easing: 'easeOutExpo'
      });
      
      // Animate stats cards with a staggered entrance
      anime({
        targets: '.stat-card',
        opacity: [0, 1],
        translateY: [20, 0],
        scale: [0.9, 1],
        delay: anime.stagger(100, {start: 300}),
        duration: 800,
        easing: 'easeOutElastic(1, .5)'
      });
      
      // Animate streams section header
      anime({
        targets: '.section-header',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 600,
        delay: 400,
        easing: 'easeOutExpo'
      });
      
      // Animate stream cards with a staggered entrance
      anime({
        targets: '.stream-card',
        opacity: [0, 1],
        translateY: [30, 0],
        scale: [0.95, 1],
        delay: anime.stagger(80, {start: 700, from: 'center'}),
        duration: 700,
        easing: 'easeOutCubic'
      });
      
      // Expand Online Streams section if there are online streams
      if (onlineStreams.value.length > 0) {
        isOnlineCollapsed.value = false;
      }
      
      // Fetch notifications for total detections
      fetchNotifications();
    });
    
    return {
      stats,
      statsSection,
      searchQuery,
      viewMode,
      isRefreshModalOpen,
      selectedStreams,
      selectAllStreams,
      isOnlineCollapsed,
      isOfflineCollapsed,
      getDetectionCount,
      openStream,
      handleDetectionToggled,
      enhanceStreamWithUsername,
      onlineStreams,
      offlineStreams,
      filteredOnlineStreams,
      filteredOfflineStreams,
      toggleViewMode,
      openRefreshModal,
      closeRefreshModal,
      toggleSelectAll,
      refreshSelectedStreams,
      toggleOnlineCollapse,
      toggleOfflineCollapse
    };
  }
}
</script>

<style scoped>
.dashboard-tab {
  width: 100%;
  padding: 1rem;
  box-sizing: border-box;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-header h2 {
  margin-bottom: 0.5rem;
  font-size: 2rem;
  color: var(--text-color);
  font-weight: 600;
  letter-spacing: -0.5px;
}

/* Stats section styling - separate from stream grid */
.stats-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 3rem; /* Increased spacing between stats and streams */
  padding-bottom: 1.5rem;
  position: relative;
}

/* Add a subtle separator between stats and streams */
.stats-section::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    var(--border-color, rgba(0, 0, 0, 0.1)),
    transparent
  );
}

/* Controls section */
.controls-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
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
  color: var(--text-muted, #6c757d);
  opacity: 0.6;
}

.search-input {
  width: 100%;
  padding: 10px 15px 10px 35px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
}

.view-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.view-toggle-btn, .refresh-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.view-toggle-btn:hover, .refresh-btn:hover {
  background-color: var(--primary-hover);
  transform: scale(1.02);
}

.refresh-control {
  display: flex;
  gap: 0.5rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

.refresh-modal {
  background-color: var(--input-bg);
  border-radius: 12px;
  padding: 1.5rem;
  width: 450px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  border: 1px solid var(--input-border);
  animation: slideIn 0.2s ease-out;
}

.refresh-modal h3 {
  margin-top: 0;
  margin-bottom: 1.25rem;
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 1px solid var(--input-border);
  padding-bottom: 0.5rem;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  max-height: 300px;
  overflow-y: auto;
  padding-right: 0.25rem;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  transition: background-color 0.2s ease;
}

.checkbox-group label:hover {
  background-color: var(--hover-bg);
}

.checkbox-group label:first-child {
  font-weight: 500;
  border-bottom: 1px solid var(--input-border);
}

.modal-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.cancel-btn, .confirm-btn {
  padding: 0.6rem 1.25rem;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.cancel-btn {
  background-color: var(--hover-bg);
  color: var(--text-color);
}

.cancel-btn:hover {
  background-color: var(--disabled-bg);
}

.confirm-btn {
  background-color: var(--primary-color);
  color: white;
}

.confirm-btn:hover {
  background-color: var(--primary-hover);
  transform: translateY(-2px);
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Streams section styling */
.streams-section {
  padding-top: 0.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  cursor: pointer;
}

.section-header.offline-section {
  margin-top: 2rem;
}

.section-header h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.stream-count {
  background-color: var(--primary-color, #3B82F6);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.collapse-icon {
  margin-left: 0.5rem;
  transition: transform 0.3s ease;
}

.stream-container {
  margin-bottom: 2rem;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* Enforce 3x3 grid */
  gap: 1.5rem;
  perspective: 1000px;
}

.list-view {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.list-view .stream-card {
  width: 100%;
  max-width: none;
  height: auto;
  min-height: 60px;
  aspect-ratio: unset;
  flex-direction: row;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.list-view .stream-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 10px rgba(0, 0, 0, 0.15);
}

.stream-card {
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275),
              box-shadow 0.3s ease;
  border-radius: 12px;
  overflow: hidden;
  backface-visibility: hidden;
}

.stream-card:hover {
  transform: scale(1.02) translateY(-4px);
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.15);
}

/* Responsive styles */
@media (max-width: 1280px) {
  .dashboard-tab {
    padding: 1.25rem;
    overflow: hidden;
  }
  
  .stats-section {
    gap: 1.25rem;
  }
  
  .grid-view {
    grid-template-columns: repeat(3, 1fr); /* Maintain 3 columns for larger screens */
  }
}

@media (max-width: 992px) {
  .dashboard-tab {
    padding: 1rem;
  }
  
  .stats-section {
    gap: 1rem;
  }
  
  .grid-view {
    grid-template-columns: repeat(2, 1fr); /* Reduce to 2 columns for medium screens */
    gap: 1.25rem;
  }
}

@media (max-width: 768px) {
  .dashboard-tab {
    padding: 0.75rem;
  }
  
  .dashboard-header h2 {
    font-size: 1.6rem;
    margin-bottom: 1.25rem;
  }
  
  .stats-section {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .section-header h3 {
    font-size: 1.3rem;
  }
  
  .grid-view {
    grid-template-columns: repeat(2, 1fr); /* 2 columns for smaller screens */
    gap: 1rem;
  }
  
  .list-view .stream-card {
    padding: 0.5rem;
    min-height: 50px;
  }
  
  .controls-section {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .search-input {
    width: 100%;
    margin-bottom: 0.5rem;
  }
}

@media (max-width: 640px) {
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .dashboard-tab {
    padding: 0.5rem;
  }
  
  .stats-section {
    grid-template-columns: 1fr;
  }
  
  .grid-view {
    grid-template-columns: 1fr; /* 1 column for very small screens */
  }
  
  .dashboard-header h2 {
    font-size: 1.4rem;
    margin-bottom: 1rem;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .refresh-modal {
    width: 90%;
    padding: 1.25rem;
  }
  
  .refresh-modal h3 {
    font-size: 1.2rem;
  }
  
  .modal-buttons {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .cancel-btn, .confirm-btn {
    width: 100%;
    text-align: center;
  }
}
</style>