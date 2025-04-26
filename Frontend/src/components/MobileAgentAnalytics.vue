<template>
  <div class="mobile-agent-analytics">
    <div class="section-header">
      <h2>Performance Overview</h2>
    </div>

    <div class="stats-container">
      <div class="stat-card">
        <div class="stat-value">{{ formatNumber(stats.totalAssignments) }}</div>
        <div class="stat-label">Total Assignments</div>
      </div>

      <div class="stat-card">
        <div class="stat-value">{{ formatNumber(stats.activeStreams) }}</div>
        <div class="stat-label">Active Streams</div>
      </div>

      <div class="stat-card">
        <div class="stat-value">{{ formatNumber(stats.completedToday) }}</div>
        <div class="stat-label">Completed Today</div>
      </div>
    </div>

    <div class="performance-chart-container">
      <p class="placeholder-text">Performance trends (mobile optimized)</p>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

defineProps({
  stats: {
    type: Object,
    default: () => ({
      totalAssignments: 0,
      activeStreams: 0,
      completedToday: 0
    })
  }
})

const formatNumber = (num) => {
  if (num >= 1000000) return `${(num/1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num/1000).toFixed(1)}K`
  return num
}
</script>

<style scoped>
.mobile-agent-analytics {
  padding: 0 0.5rem;
}

.section-header h2 {
  font-size: 1.2rem;
  margin: 0 0 1.5rem 0;
  color: var(--text-color);
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.8rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background-color: var(--card-bg);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 0.3rem;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-light);
  line-height: 1.3;
}

.performance-chart-container {
  background-color: var(--card-bg);
  border-radius: 8px;
  padding: 2rem 1rem;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-text {
  color: var(--text-light);
  font-style: italic;
  text-align: center;
  margin: 0;
}

@media (max-width: 480px) {
  .stats-container {
    gap: 0.5rem;
  }
  
  .stat-card {
    padding: 0.8rem;
  }
  
  .stat-value {
    font-size: 1.2rem;
  }
  
  .stat-label {
    font-size: 0.7rem;
  }
}
</style>