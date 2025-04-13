<template>
  <section class="dashboard-tab">
    <div class="dashboard-header">
      <h2>Stream Monitoring Dashboard</h2>
      <div class="stats-container">
        <StatCard 
          v-for="stat in stats"
          :key="stat.label"
          :value="stat.value"
          :label="stat.label"
          :icon="stat.icon"
        />
      </div>
    </div>

    <div class="stream-grid">
      <StreamCard
        v-for="stream in streams"
        :key="stream.id"
        :stream="stream"
        :detection-count="getDetectionCount(stream)"
        @click="$emit('open-stream', stream)"
      />
    </div>
  </section>
</template>

<script>
import { computed } from 'vue'
import StatCard from './StatCard.vue'
import StreamCard from './StreamCard.vue'

export default {
  name: 'DashboardTab',
  components: {
    StatCard,
    StreamCard
  },
  props: {
    dashboardStats: Object,
    streams: Array,
    detections: Object
  },
  emits: ['open-stream'],
  setup(props) {
    const stats = computed(() => [
      { 
        value: props.dashboardStats.ongoing_streams, 
        label: 'Active Streams',
        icon: 'broadcast-tower'
      },
      { 
        value: props.dashboardStats.total_detections, 
        label: 'Total Detections',
        icon: 'exclamation-triangle'
      },
      { 
        value: props.dashboardStats.active_agents, 
        label: 'Active Agents',
        icon: 'user-shield'
      }
    ])
    
    const getDetectionCount = (stream) => {
      return props.detections[stream.room_url]?.length || 0
    }
    
    return {
      stats,
      getDetectionCount
    }
  }
}
</script>

<style scoped>
.dashboard-tab {
  animation: fadeIn 0.4s ease;
}

.dashboard-header {
  margin-bottom: 30px;
}

.dashboard-header h2 {
  margin-bottom: 20px;
  font-size: 1.8rem;
  color: var(--text-color);
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stream-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Responsive styles */
@media (max-width: 768px) {
  .stats-container {
    grid-template-columns: 1fr;
  }
  
  .stream-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 576px) {
  .stream-grid {
    grid-template-columns: 1fr;
  }
}
</style>