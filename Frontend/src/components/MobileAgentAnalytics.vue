<template>
  <div class="mobile-agent-analytics">
    <div class="section-header">
      <h2>Agent Performance Dashboard</h2>
    </div>

    <!-- Real-time Stats Grid -->
    <div class="stats-container">
      <div class="stat-card" @click="toggleView('assignments')">
        <div class="stat-value">{{ formatNumber(stats.activeAssignments) }}</div>
        <div class="stat-label">Active Streams</div>
        <div class="stat-trend">
          <span :class="trendClass(stats.assignmentTrend)">↗ {{ stats.assignmentTrend }}%</span>
        </div>
      </div>

      <div class="stat-card" @click="toggleView('response')">
        <div class="stat-value">{{ stats.avgResponseTime }}m</div>
        <div class="stat-label">Avg Response</div>
        <div class="stat-trend">
          <span :class="trendClass(stats.responseTrend)">↙ {{ stats.responseTrend }}%</span>
        </div>
      </div>

      <div class="stat-card" @click="toggleView('resolutions')">
        <div class="stat-value">{{ stats.resolutionRate }}%</div>
        <div class="stat-label">Resolved</div>
        <div class="stat-trend">
          <span :class="trendClass(stats.resolutionTrend)">↖ {{ stats.resolutionTrend }}%</span>
        </div>
      </div>
    </div>

    <!-- Interactive Chart -->
    <div class="chart-container">
      <apexchart
        v-if="!loading"
        type="area"
        height="280"
        :options="chartOptions"
        :series="chartSeries"
      ></apexchart>
      <div v-else class="loading-spinner"></div>
    </div>

    <!-- Detection Type Breakdown -->
    <div class="detection-types">
      <h3>Alert Types</h3>
      <div class="type-grid">
        <div 
          v-for="(type, index) in detectionTypes"
          :key="index"
          class="type-card"
          @click="filterByType(type.name)"
        >
          <div class="type-icon" :style="{ backgroundColor: type.color }">
            <component :is="type.icon" />
          </div>
          <div class="type-info">
            <div class="type-count">{{ type.count }}</div>
            <div class="type-name">{{ type.name }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useSocket } from '@/composables/useSocket'
import { useAgentStore } from '@/stores/agent'
import { ClockIcon, VideoIcon, AlertCircleIcon, MessageSquareIcon } from 'vue-tabler-icons'
import apexchart from 'vue3-apexcharts'

const { socket } = useSocket()
const agentStore = useAgentStore()

const loading = ref(true)
const currentView = ref('performance')
const detectionTypes = ref([])

const stats = ref({
  activeAssignments: 0,
  assignmentTrend: 0,
  avgResponseTime: 0,
  responseTrend: 0,
  resolutionRate: 0,
  resolutionTrend: 0,
  detectionBreakdown: []
})

// Chart Configuration
const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    toolbar: { show: false },
    zoom: { enabled: false }
  },
  colors: ['#6366f1'],
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  xaxis: {
    type: 'datetime',
    labels: { style: { colors: '#6b7280' } }
  },
  yaxis: { labels: { style: { colors: '#6b7280' } },
  tooltip: { x: { format: 'dd MMM yyyy' } },
  grid: { borderColor: '#374151' }
}))

const chartSeries = ref([{
  name: 'Activities',
  data: []
}]))

const fetchInitialData = async () => {
  try {
    const [assignmentRes, performanceRes] = await Promise.all([
      fetch('/api/assignments?agent_id=' + agentStore.currentAgent.id),
      fetch('/api/analytics/agent-performance')
    ])
    
    const assignmentData = await assignmentRes.json()
    const performanceData = await performanceRes.json()

    stats.value = {
      ...stats.value,
      ...performanceData,
      activeAssignments: assignmentData.length
    }

    detectionTypes.value = performanceData.detectionBreakdown.map(t => ({
      ...t,
      icon: getTypeIcon(t.name),
      color: getTypeColor(t.name)
    }))

    chartSeries.value[0].data = performanceData.activityTimeline
    loading.value = false
  } catch (error) {
    console.error('Error fetching analytics:', error)
  }
}

const getTypeIcon = (name) => {
  const icons = {
    'Object': VideoIcon,
    'Audio': AlertCircleIcon,
    'Chat': MessageSquareIcon,
    'Response': ClockIcon
  }
  return icons[name] || AlertCircleIcon
}

const getTypeColor = (name) => {
  const colors = {
    'Object': '#ef4444',
    'Audio': '#3b82f6',
    'Chat': '#10b981',
    'Response': '#f59e0b'
  }
  return colors[name] || '#6b7280'
}

const trendClass = (value) => ({
  'positive': value > 0,
  'negative': value < 0
})

const toggleView = (view) => {
  currentView.value = view
  // Implement view-specific data fetching
}

onMounted(() => {
  fetchInitialData()
  
  socket.on('notification_update', (update) => {
    if (update.type === 'stats') {
      stats.value = { ...stats.value, ...update.data }
    }
  })

  socket.on('detection_alert', (alert) => {
    const typeIndex = detectionTypes.value.findIndex(t => t.name === alert.type)
    if (typeIndex > -1) {
      detectionTypes.value[typeIndex].count++
    }
  })
})
</script>

<style scoped>
/* Enhanced Mobile-First Styles */
.mobile-agent-analytics {
  padding: 1rem;
  background: var(--background-primary);
  min-height: 100vh;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.8rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--card-background);
  border-radius: 12px;
  padding: 1.2rem;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stat-trend {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 0.7rem;
}

.positive { color: #10b981; }
.negative { color: #ef4444; }

.chart-container {
  background: var(--card-background);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.detection-types h3 {
  color: var(--text-primary);
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr));
  gap: 1rem;
}

.type-card {
  display: flex;
  align-items: center;
  background: var(--card-background);
  padding: 1rem;
  border-radius: 12px;
}

.type-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
}

.type-count {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary);
}

.type-name {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.loading-spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #6366f1;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin: 2rem auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .stat-card {
    padding: 1rem;
  }
  
  .type-grid {
    grid-template-columns: 1fr;
  }
}
</style>