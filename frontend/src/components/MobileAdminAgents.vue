<template>
  <div class="agents-tab">
    <div class="tab-header">
      <h2>Agents</h2>
      <div class="filter-actions">
        <div class="search-container">
          <input 
            type="text" 
            v-model="agentSearchQuery" 
            placeholder="Search agent..."
            @input="filterAgents"
            class="search-input"
          />
          <font-awesome-icon icon="search" class="search-icon" />
        </div>
      </div>
    </div>
    
    <!-- Agent list -->
    <div class="agent-list" v-if="!loading">
      <p v-if="filteredAgents.length === 0" class="empty-message">
        No agents match your search
      </p>
      <div 
        v-for="agent in filteredAgents" 
        :key="agent.id" 
        class="agent-card"
        @click="openAgentDetails(agent)"
      >
        <div class="agent-status" :class="{ online: agent.online }"></div>
        <div class="agent-info">
          <div class="agent-name">{{ agent.username }}</div>
          <div class="agent-assignment-count">
            {{ agent.assignments ? agent.assignments.length : 0 }} stream(s) assigned
          </div>
        </div>
        <div class="agent-actions">
          <font-awesome-icon icon="chevron-right" />
        </div>
      </div>
    </div>
    <div v-else class="loading-container">
      <mobile-loading-spinner :size="40" text="Loading agents..." />
    </div>
    
    <!-- Add agent button -->
    <div class="floating-action-button" @click="$emit('add-agent')">
      <font-awesome-icon icon="user-plus" />
    </div>
  </div>
</template>

<script>
import MobileLoadingSpinner from './MobileLoadingSpinner.vue'
import axios from 'axios'
import { ref, computed } from 'vue'

export default {
  name: 'MobileAdminAgents',
  components: {
    MobileLoadingSpinner
  },
  props: {
    loading: Boolean,
    agents: Array
  },
  emits: ['agent-selected', 'add-agent'],
  setup(props, { emit }) {  // Add emit parameter
    const agentSearchQuery = ref('')
    
    // Filter agents based on search query
    const filteredAgents = computed(() => {
      if (!agentSearchQuery.value) return props.agents
      const query = agentSearchQuery.value.toLowerCase()
      return props.agents.filter(agent => 
        (agent.username || '').toLowerCase().includes(query)
      )
    })

    // Register user activity
    const registerUserActivity = () => {
      axios.post('/api/user-activity')
    }

    // Filter agents
    const filterAgents = () => {
      registerUserActivity()
    }

    // Open agent details
    const openAgentDetails = (agent) => {
      emit('agent-selected', agent)  // Use emit instead of $emit
      registerUserActivity()
    }

    return {
      agentSearchQuery,
      filteredAgents,
      filterAgents,
      openAgentDetails
    }
  }
}
</script>
<style scoped>
.mobile-admin-dashboard,
.mobile-admin-dashboard * {
  font-family: var(--font-family);
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.mobile-admin-dashboard {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  color: var(--text-color);
  padding-bottom: 70px; /* Space for bottom nav */
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 1rem;
}
</style>