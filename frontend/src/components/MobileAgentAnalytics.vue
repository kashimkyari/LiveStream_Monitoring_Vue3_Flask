<template>
  <div class="mobile-agent-analytics">
    <div class="section-header">
      <h2>Agent Performance</h2>
    </div>

    <!-- Real-time Stats Grid -->
    <div class="stats-container">
      <div class="stat-card" @click="toggleView('assignments')">
        <div class="stat-value">{{ formatNumber(stats.activeAssignments) }}</div>
        <div class="stat-label">Active Streams</div>
        <div class="stat-trend">
          <span :class="trendClass(stats.assignmentTrend)">
            <span class="trend-icon">{{ stats.assignmentTrend > 0 ? '↗' : '↙' }}</span>
            {{ Math.abs(stats.assignmentTrend) }}%
          </span>
        </div>
      </div>

      <div class="stat-card" @click="toggleView('response')">
        <div class="stat-value">{{ stats.avgResponseTime }}m</div>
        <div class="stat-label">Avg Response</div>
        <div class="stat-trend">
          <span :class="trendClass(stats.responseTrend)">
            <span class="trend-icon">{{ stats.responseTrend > 0 ? '↗' : '↙' }}</span>
            {{ Math.abs(stats.responseTrend) }}%
          </span>
        </div>
      </div>

      <div class="stat-card" @click="toggleView('resolutions')">
        <div class="stat-value">{{ stats.resolutionRate }}%</div>
        <div class="stat-label">Resolved</div>
        <div class="stat-trend">
          <span :class="trendClass(stats.resolutionTrend)">
            <span class="trend-icon">{{ stats.resolutionTrend > 0 ? '↗' : '↙' }}</span>
            {{ Math.abs(stats.resolutionTrend) }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Interactive Chart -->
    <div class="chart-container">
      <apexchart v-if="!loading" type="area" height="240" :options="chartOptions" :series="chartSeries"></apexchart>
      <div v-else class="loading-spinner"></div>

      <div class="chart-time-filters">
        <button v-for="period in timePeriods" :key="period.value"
          :class="['time-filter-btn', { active: selectedPeriod === period.value }]" @click="changePeriod(period.value)">
          {{ period.label }}
        </button>
      </div>
    </div>

    <!-- Detection Type Breakdown -->
    <div class="detection-types">
      <h3>Alert Types</h3>
      <div class="type-grid">
        <div v-for="(type, index) in detectionTypes" :key="index" class="type-card" @click="filterByType(type.name)">
          <div class="type-icon" :style="{ backgroundColor: type.color }">
            <component :is="type.icon" />
          </div>
          <div class="type-info">
            <div class="type-name">{{ type.name }}</div>
            <div class="type-count">{{ type.count }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAgentStore } from '../stores/agent'
import { ClockIcon, VideoIcon, AlertCircleIcon, MessageIcon, MusicIcon } from 'vue-tabler-icons'
import apexchart from 'vue3-apexcharts'
import io from 'socket.io-client'

const agentStore = useAgentStore()
const socket = io('https://monitor-backend.jetcamstudio.com:5000/notifications', {
  path: '/ws'
});

const loading = ref(true)
const currentView = ref('performance')
const detectionTypes = ref([])
const selectedPeriod = ref('day')

const timePeriods = [
  { label: '24h', value: 'day' },
  { label: '7d', value: 'week' },
  { label: '30d', value: 'month' }
]

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
    zoom: { enabled: false },
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
  },
  colors: ['#6366f1'],
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.7,
      opacityTo: 0.2,
      stops: [0, 100]
    }
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { colors: '#6b7280' },
      datetimeFormatter: {
        year: 'yyyy',
        month: 'MMM',
        day: 'dd MMM',
        hour: 'HH:mm'
      },
      rotateAlways: false,
      hideOverlappingLabels: true
    }
  },
  yaxis: {
    labels: {
      style: { colors: '#6b7280' },
      formatter: (value) => Math.round(value)
    }
  },
  tooltip: {
    x: { format: 'dd MMM yyyy, HH:mm' },
    theme: 'dark'
  },
  grid: {
    borderColor: 'rgba(55, 65, 81, 0.2)',
    row: {
      colors: ['transparent'],
      opacity: 0.5
    }
  },
  legend: { show: false },
  responsive: [{
    breakpoint: 480,
    options: {
      chart: {
        height: 200
      },
      xaxis: {
        labels: {
          rotate: -45,
          style: {
            fontSize: '10px'
          }
        }
      }
    }
  }]
}))

const chartSeries = ref([{
  name: 'Activities',
  data: []
}])

const formatNumber = (num) => {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num
}

const fetchInitialData = async () => {
  try {
    // Check if currentAgent exists before accessing its properties
    if (!agentStore.currentAgent) {
      console.warn('No agent selected. Loading default data.')
      // Load default/fallback data or wait for agent selection
      loadDefaultData()
      return
    }

    const [assignmentRes, performanceRes] = await Promise.all([
      fetch('/api/assignments?agent_id=' + agentStore.currentAgent.id),
      fetch('/api/analytics/agent-performance?period=' + selectedPeriod.value)
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
    // Load fallback data on error
    loadDefaultData()
  }
}

const getTypeIcon = (name) => {
  const icons = {
    'Object': VideoIcon,
    'Audio': MusicIcon,
    'Chat': MessageIcon,
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

const trendClass = (value) => {
  return {
    'positive': value > 0,
    'negative': value < 0
  }
}

const toggleView = (view) => {
  currentView.value = view
  loading.value = true
  // Implement view-specific data fetching
  setTimeout(() => {
    loading.value = false
  }, 500)
}

const changePeriod = async (period) => {
  selectedPeriod.value = period
  loading.value = true

  try {
    const res = await fetch('/api/analytics/agent-performance?period=' + period)
    const data = await res.json()

    // Update chart data if available
    if (data.activityTimeline && data.activityTimeline.length > 0) {
      chartSeries.value[0].data = data.activityTimeline
    } else {
      // Generate mock data for different time periods
      const mockData = []
      const now = new Date()

      // Adjust time range based on selected period
      const points = period === 'day' ? 24 : period === 'week' ? 7 : 30
      const intervalUnit = period === 'day' ? 'hours' : 'days'

      for (let i = 0; i < points; i++) {
        const timestamp = new Date(now)
        if (intervalUnit === 'hours') {
          timestamp.setHours(now.getHours() - points + i)
        } else {
          timestamp.setDate(now.getDate() - points + i)
        }

        mockData.push({
          x: timestamp.getTime(),
          y: Math.floor(Math.random() * 30) + 5
        })
      }

      chartSeries.value[0].data = mockData
    }

    // Update relevant stats
    stats.value = {
      ...stats.value,
      assignmentTrend: data.assignmentTrend || stats.value.assignmentTrend,
      responseTrend: data.responseTrend || stats.value.responseTrend,
      resolutionTrend: data.resolutionTrend || stats.value.resolutionTrend
    }
  } catch (error) {
    console.error('Error fetching period data:', error)

    // Generate mock data on error
    const mockData = []
    const now = new Date()
    const points = period === 'day' ? 24 : period === 'week' ? 7 : 30
    const intervalUnit = period === 'day' ? 'hours' : 'days'

    for (let i = 0; i < points; i++) {
      const timestamp = new Date(now)
      if (intervalUnit === 'hours') {
        timestamp.setHours(now.getHours() - points + i)
      } else {
        timestamp.setDate(now.getDate() - points + i)
      }

      mockData.push({
        x: timestamp.getTime(),
        y: Math.floor(Math.random() * 30) + 5
      })
    }

    chartSeries.value[0].data = mockData
  } finally {
    loading.value = false
  }
}

const filterByType = (typeName) => {
  // Implement filtering by alert type
  console.log(`Filtering by: ${typeName}`)
  // Here you would fetch data filtered by this type
}

const loadDefaultData = () => {
  stats.value = {
    activeAssignments: 0,
    assignmentTrend: 0,
    avgResponseTime: 0,
    responseTrend: 0,
    resolutionRate: 0,
    resolutionTrend: 0,
    detectionBreakdown: []
  }

  detectionTypes.value = [
    { name: 'Object', count: 0, icon: getTypeIcon('Object'), color: getTypeColor('Object') },
    { name: 'Audio', count: 0, icon: getTypeIcon('Audio'), color: getTypeColor('Audio') },
    { name: 'Chat', count: 0, icon: getTypeIcon('Chat'), color: getTypeColor('Chat') },
    { name: 'Response', count: 0, icon: getTypeIcon('Response'), color: getTypeColor('Response') }
  ]

  // Generate mock chart data
  const mockData = []
  const now = new Date()
  const points = selectedPeriod.value === 'day' ? 24 : selectedPeriod.value === 'week' ? 7 : 30
  const intervalUnit = selectedPeriod.value === 'day' ? 'hours' : 'days'

  for (let i = 0; i < points; i++) {
    const timestamp = new Date(now)
    if (intervalUnit === 'hours') {
      timestamp.setHours(now.getHours() - points + i)
    } else {
      timestamp.setDate(now.getDate() - points + i)
    }

    mockData.push({
      x: timestamp.getTime(),
      y: 0 // Empty data for fallback
    })
  }

  chartSeries.value[0].data = mockData
  loading.value = false
}

onMounted(() => {
  fetchInitialData()

  // Set up socket listeners
  if (socket && typeof socket.on === 'function') {
    // Listen for stats updates
    socket.on('notification', (notification) => {
      if (notification.type === 'stats') {
        stats.value = { ...stats.value, ...notification.data }
      }
    })

    // Listen for detection alerts
    socket.on('notification', (notification) => {
      if (notification.type === 'detection_alert') {
        const typeIndex = detectionTypes.value.findIndex(t => t.name === notification.alert_type)
        if (typeIndex > -1) {
          detectionTypes.value[typeIndex].count++
        }
      }
    })

    // Join agent-specific notification room - Add proper check for currentAgent
    if (agentStore.currentAgent && agentStore.currentAgent.id) {
      socket.emit('join', { room: `user_${agentStore.currentAgent.id}` })
      socket.emit('join', { room: 'role_agent' })

      // Subscribe to stream notifications for all assigned streams
      socket.emit('get_unread_notifications')
    } else {
      console.warn('No agent selected. Socket rooms not joined.')
    }
  } else {
    console.error('Socket connection unavailable')
  }
})
</script>

<style scoped>
/* Enhanced Mobile-First Styles */
.mobile-agent-analytics {
  padding: 0.75rem;
  background: var(--background-primary);
  min-height: 100vh;
  max-width: 100%;
  overflow-x: hidden;
}

.section-header {
  margin-bottom: 1rem;
}

.section-header h2 {
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0.5rem 0;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.6rem;
  margin-bottom: 1.25rem;
}

.stat-card {
  background: var(--card-background);
  border-radius: 12px;
  padding: 0.75rem;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  touch-action: manipulation;
}

.stat-card:active {
  transform: scale(0.98);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.2rem;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.stat-trend {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  font-size: 0.65rem;
  padding: 0.2rem 0.4rem;
  border-radius: 1rem;
  background-color: rgba(0, 0, 0, 0.1);
}

.trend-icon {
  margin-right: 0.15rem;
}

.positive {
  color: #10b981;
}

.negative {
  color: #ef4444;
}

.chart-container {
  background: var(--card-background);
  border-radius: 12px;
  padding: 0.75rem;
  margin-bottom: 1.25rem;
  overflow: hidden;
}

.chart-time-filters {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.time-filter-btn {
  border: none;
  background: rgba(99, 102, 241, 0.1);
  color: var(--text-secondary);
  border-radius: 1rem;
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.time-filter-btn.active {
  background: #6366f1;
  color: white;
}

.detection-types {
  margin-top: 1.25rem;
}

.detection-types h3 {
  color: var(--text-primary);
  margin-bottom: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.type-card {
  display: flex;
  align-items: center;
  background: var(--card-background);
  padding: 0.75rem;
  border-radius: 12px;
  transition: transform 0.2s ease;
  touch-action: manipulation;
}

.type-card:active {
  transform: scale(0.98);
}

.type-icon {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.75rem;
  color: white;
}

.type-info {
  flex: 1;
}

.type-count {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.type-name {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.loading-spinner {
  border: 3px solid rgba(99, 102, 241, 0.1);
  border-top: 3px solid #6366f1;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin: 2rem auto;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

/* Enhanced mobile responsiveness */
@media (max-width: 380px) {
  .stats-container {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
  }

  .stat-value {
    font-size: 1.1rem;
  }

  .stat-label {
    font-size: 0.7rem;
  }

  .stat-trend {
    font-size: 0.6rem;
  }

  .type-grid {
    grid-template-columns: 1fr;
  }
}

/* Safe area insets for notched phones */
@supports (padding: max(0px)) {
  .mobile-agent-analytics {
    padding-left: max(0.75rem, env(safe-area-inset-left));
    padding-right: max(0.75rem, env(safe-area-inset-right));
    padding-bottom: max(0.75rem, env(safe-area-inset-bottom));
  }
}
</style>