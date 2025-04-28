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

    <!-- Stream section with header -->
    <div class="streams-section">
      <div class="section-header">
        <h3>Active Streams</h3>
        <span class="stream-count">{{ streams.length }} streams</span>
      </div>
      
      <div class="stream-grid">
        <StreamCard 
          v-for="(stream, index) in streams" 
          :key="stream.id"
          :stream="enhanceStreamWithUsername(stream)" 
          :index="index"
          :detectionCount="getDetectionCount(stream)"
          :totalStreams="streams.length"
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
  emits: ['open-stream'],
  setup(props, { emit }) {
    const statsSection = ref(null);
    
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
    ]);

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
    });
    
    return {
      stats,
      statsSection,
      getDetectionCount,
      openStream,
      handleDetectionToggled,
      enhanceStreamWithUsername // Make sure to expose this function
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

/* Streams section styling */
.streams-section {
  padding-top: 0.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
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

.stream-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  perspective: 1000px;
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
  
  .stream-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 992px) {
  .dashboard-tab {
    padding: 1rem;
  }
  
  .stats-section {
    gap: 1rem;
  }
  
  .stream-grid {
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
  
  .stream-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
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
  
  .stream-grid {
    grid-template-columns: 1fr;
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
}
</style>