<template>
  <div class="mobile-agent-streams">
    <div class="section-header">
      <h2>My Assigned Streams</h2>
      <div class="refresh-button" @click="$emit('refresh')">
        <font-awesome-icon icon="sync" :class="{ 'fa-spin': isLoading }" />
      </div>
    </div>

    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading your streams...</p>
    </div>

    <div v-else-if="assignments.length === 0" class="empty-state">
      <p>You don't have any assigned streams.</p>
    </div>

    <div v-else class="stream-cards">
      <div 
        v-for="assignment in assignments" 
        :key="assignment.id" 
        class="stream-card card"
        @click="$emit('open-stream', assignment)"
      >
        <div class="stream-card-header">
          <h3>{{ assignment.streamer_username }}</h3>
          <div class="stream-platform" :class="assignment.platform.toLowerCase()">
            {{ assignment.platform }}
          </div>
        </div>
        <div class="stream-card-body">
          <div class="stream-info">
            <p class="stream-viewers">
              <font-awesome-icon icon="eye" /> 
              {{ formatNumber(assignment.viewer_count || 0) }}
            </p>
            <p class="stream-time">
              <font-awesome-icon icon="clock" />
              {{ formatStreamTime(assignment.stream_start_time) }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import { formatDistance } from 'date-fns'

defineProps({
  assignments: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['refresh', 'open-stream'])

const formatNumber = (num) => {
  if (num >= 1000000) return `${(num/1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num/1000).toFixed(1)}K`
  return num
}

const formatStreamTime = (timestamp) => {
  if (!timestamp) return 'Unknown'
  try {
    return formatDistance(new Date(timestamp), new Date(), { addSuffix: true })
  } catch {
    return 'Unknown'
  }
}
</script>

<style scoped>
.mobile-agent-streams {
  padding: 0.5rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  font-size: 1.2rem;
  margin: 0;
}

.refresh-button {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background-color: var(--input-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.refresh-button:hover {
  transform: rotate(180deg);
}

.stream-cards {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

.stream-card {
  padding: 1rem;
  background-color: var(--card-bg);
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stream-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stream-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.8rem;
}

.stream-card-header h3 {
  font-size: 1rem;
  margin: 0;
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stream-platform {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.stream-platform.chaturbate {
  background-color: #f5a62322;
  color: #f5a623;
  border: 1px solid #f5a62333;
}

.stream-platform.stripchat {
  background-color: #7e57c222;
  color: #7e57c2;
  border: 1px solid #7e57c233;
}

.stream-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--text-light);
}

.stream-info p {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 0;
  gap: 1rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-color);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-light);
}
</style>