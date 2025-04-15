<template>
  <section class="dashboard-tab">
    <div class="dashboard-header">
      <h2>Stream Dashboard</h2>
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
        v-for="(stream, index) in streams"
        :key="stream.id"
        :stream="stream"
        :detection-count="getDetectionCount(stream)"
        @click="openStream(stream, index)"
        class="stream-card"
      />
    </div>
  </section>
</template>

<script>
import { computed, onMounted } from 'vue'
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
      const clickedCard = document.querySelectorAll('.stream-card')[index];
      if (clickedCard) {
        anime({
          targets: clickedCard,
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
        targets: '.dashboard-header',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 600,
        easing: 'easeOutExpo'
      })
      
      // Animate stats cards with a staggered entrance
      anime({
        targets: '.stats-container .stat-card',
        opacity: [0, 1],
        translateY: [20, 0],
        scale: [0.9, 1],
        delay: anime.stagger(100, {start: 300}),
        duration: 800,
        easing: 'easeOutElastic(1, .5)'
      })
      
      // Animate stream cards with a staggered entrance
      anime({
        targets: '.stream-card',
        opacity: [0, 1],
        translateY: [30, 0],
        scale: [0.95, 1],
        delay: anime.stagger(80, {start: 800, from: 'center'}),
        duration: 700,
        easing: 'easeOutCubic'
      })
    })
    
    return {
      stats,
      getDetectionCount,
      openStream
    }
  }
}
</script>

<style scoped>
.dashboard-tab {
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
  
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-header h2 {
  margin-bottom: 1.5rem;
  font-size: 2rem;
  color: var(--text-color);
  font-weight: 600;
  letter-spacing: -0.5px;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stream-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
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
}

@media (max-width: 992px) {
  .dashboard-tab {
    padding: 1rem;
  }
  
  .stats-container {
    gap: 1.25rem;
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
  
  .stats-container {
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }
  
  .stream-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
  }
}

@media (max-width: 640px) {
  .stats-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .dashboard-tab {
    padding: 0.5rem;
  }
  
  .stats-container {
    grid-template-columns: 1fr;
  }
  
  .stream-grid {
    grid-template-columns: 1fr;
  }
  
  .dashboard-header h2 {
    font-size: 1.4rem;
    margin-bottom: 1rem;
  }
}
</style>