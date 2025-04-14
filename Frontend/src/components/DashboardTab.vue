<template>
  <section class="dashboard-tab">
    <div class="dashboard-header" ref="dashboardHeader">
      <h2>Stream Dashboard</h2>
      <div class="stats-container" ref="statsContainer">
        <StatCard 
          v-for="stat in stats"
          :key="stat.label"
          :value="stat.value"
          :label="stat.label"
          :icon="stat.icon"
          ref="statCards"
        />
      </div>
    </div>

    <div class="stream-grid" ref="streamGrid">
      <StreamCard
        v-for="(stream, index) in streams"
        :key="stream.id"
        :stream="stream"
        :detection-count="getDetectionCount(stream)"
        @click="openStream(stream, index)"
        class="stream-card"
        ref="streamCards"
      />
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
    detections: Object
  },
  emits: ['open-stream'],
  setup(props, { emit }) {
    const dashboardHeader = ref(null)
    const statsContainer = ref(null)
    const streamGrid = ref(null)
    const statCards = ref([])
    const streamCards = ref([])
    
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
    
    const openStream = (stream, index) => {
      // Animate the card click
      if (streamCards.value[index]) {
        anime({
          targets: streamCards.value[index],
          scale: [1, 1.05, 1],
          duration: 400,
          easing: 'easeInOutQuad'
        })
      }
      
      // Emit the event after a short delay for better UX
      setTimeout(() => {
        emit('open-stream', stream)
      }, 150)
    }
    
    onMounted(() => {
      // Animate the header with a fade-in and slide-up effect
      anime({
        targets: dashboardHeader.value,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 600,
        easing: 'easeOutExpo'
      })
      
      // Animate stats cards with a staggered entrance
      anime({
        targets: statCards.value,
        opacity: [0, 1],
        translateY: [20, 0],
        scale: [0.9, 1],
        delay: anime.stagger(100, {start: 300}),
        duration: 800,
        easing: 'easeOutElastic(1, .5)'
      })
      
      // Animate stream cards with a staggered entrance
      anime({
        targets: streamGrid.value.querySelectorAll('.stream-card'),
        opacity: [0, 1],
        translateY: [30, 0],
        scale: [0.95, 1],
        delay: anime.stagger(80, {start: 800, grid: [3, 3], from: 'center'}),
        duration: 700,
        easing: 'easeOutCubic'
      })
    })
    
    return {
      stats,
      getDetectionCount,
      openStream,
      dashboardHeader,
      statsContainer,
      streamGrid,
      statCards,
      streamCards
    }
  }
}
</script>

<style scoped>
.dashboard-tab {
  animation: fadeIn 0.4s ease;
  max-width: calc(100% - 5rem);
  margin: 0 auto;
  padding: 1.5rem;
}

.dashboard-header {
  margin-bottom: 35px;
}

.dashboard-header h2 {
  margin-bottom: 25px;
  font-size: 2rem;
  color: var(--text-color);
  font-weight: 600;
  letter-spacing: -0.5px;
  opacity: 0;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 24px;
  margin-bottom: 35px;
}

.stream-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
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

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Responsive styles */
@media (max-width: 1280px) {
  .dashboard-tab {
    max-width: calc(100% - 4rem);
  }
}

@media (max-width: 992px) {
  .dashboard-tab {
    max-width: calc(100% - 3rem);
  }
  
  .stats-container {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .dashboard-tab {
    max-width: calc(100% - 2rem);
    padding: 1rem;
  }
  
  .stats-container {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }
  
  .stream-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 16px;
  }
  
  .dashboard-header h2 {
    font-size: 1.6rem;
    margin-bottom: 20px;
  }
}

@media (max-width: 576px) {
  .dashboard-tab {
    max-width: 100%;
    padding: 0.75rem;
  }
  
  .stats-container {
    grid-template-columns: 1fr;
  }
  
  .stream-grid {
    grid-template-columns: 1fr;
  }
  
  .dashboard-header h2 {
    font-size: 1.4rem;
  }
}
</style>