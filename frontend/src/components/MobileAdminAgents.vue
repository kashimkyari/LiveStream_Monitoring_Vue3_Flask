<template>
  <div class="mobile-admin-agents" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <div class="agents-header">
      <h2>Agents</h2>
    </div>
    <div class="search-filter">
      <input type="text" v-model="searchQuery" placeholder="Search agents..." class="search-input" />
    </div>
    <div class="agents-list">
      <div class="agent-item" v-for="agent in filteredAgents" :key="agent.id" @click="$emit('agent-selected', agent)">
        <font-awesome-icon icon="users" class="agent-icon" />
        <div class="agent-content">
          <p class="agent-name">{{ agent.name }}</p>
          <span class="agent-status" :class="{ active: agent.status === 'active' }">
            {{ agent.status }}
          </span>
        </div>
      </div>
      <p v-if="loading" class="loading-text">Loading agents...</p>
      <p v-else-if="!filteredAgents.length" class="no-data">No agents found</p>
    </div>
    <button class="fab" @click="$emit('add-agent')">
      <font-awesome-icon icon="plus" />
    </button>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'MobileAdminAgents',
  props: {
    loading: Boolean,
    agents: Array,
    isDarkTheme: Boolean
  },
  emits: ['agent-selected', 'add-agent'],
  setup(props) {
    const searchQuery = ref('')
    const filteredAgents = computed(() => {
      if (!props.agents) return []
      return props.agents.filter(agent =>
        agent.name.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    })
    return { searchQuery, filteredAgents }
  }
}
</script>

<style scoped>
.mobile-admin-agents {
  font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --primary-color: #4361ee;
  --primary-light: #4361ee20;
  --secondary-color: #3f37c9;
  --text-color: #333333;
  --text-light: #777777;
  --background-color: #f8f9fa;
  --card-bg: #ffffff;
  --border-color: #e0e0e0;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  --border-radius: 12px;
  background-color: var(--background-color);
  color: var(--text-color);
  padding: 12px;
  position: relative;
}

.mobile-admin-agents[data-theme="dark"] {
  --primary-color: #4cc9f0;
  --primary-light: #4cc9f020;
  --secondary-color: #4895ef;
  --text-color: #f8f9fa;
  --text-light: #b0b0b0;
  --background-color: #121212;
  --card-bg: #1e1e1e;
  --border-color: #333333;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
}

.agents-header h2 { font-size: 1.25rem; font-weight: 600; color: var(--text-color); margin: 0 0 12px; }

.search-filter { margin-bottom: 12px; }
.search-input { width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: var(--border-radius); background-color: var(--card-bg); color: var(--text-color); font-size: 0.875rem; box-shadow: var(--shadow-sm); }
.search-input::placeholder { color: var(--text-light); }

.agents-list { display: flex; flex-direction: column; gap: 12px; }
.agent-item { display: flex; align-items: center; gap: 12px; background-color: var(--card-bg); padding: 12px; border-radius: var(--border-radius); box-shadow: var(--shadow-sm); cursor: pointer; transition: var(--transition); border: 1px solid var(--border-color); }
.agent-item:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.agent-icon { color: var(--primary-color); font-size: 1.2rem; }
.agent-content { flex: 1; }
.agent-name { margin: 0; font-size: 0.875rem; color: var(--text-color); }
.agent-status { font-size: 0.75rem; color: var(--text-light); }
.agent-status.active { color: var(--success-color); }
.loading-text, .no-data { font-size: 0.875rem; color: var(--text-light); text-align: center; }

.fab { position: fixed; bottom: 90px; right: 12px; background-color: var(--primary-color); color: white; border: none; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: var(--transition); box-shadow: var(--shadow-md); font-size: 1.2rem; }
.fab:hover { background-color: var(--secondary-color); }
</style>