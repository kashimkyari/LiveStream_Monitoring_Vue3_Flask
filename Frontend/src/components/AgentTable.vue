<template>
  <div class="agent-table-container">
    <h2 class="section-title">Agents Management</h2>
    <div v-if="agents.length === 0" class="empty-state">
      No agents available.
    </div>
    <template v-else>
      <div class="search-container">
        <input
          type="text"
          placeholder="Search agents..."
          v-model="searchTerm"
          @input="currentPage = 1"
          class="search-input"
        />
      </div>
      <div v-if="showCardView" class="agent-cards">
        <div v-for="agent in currentAgents" :key="agent.id" class="agent-card">
          <div class="agent-card-header">
            <h3>ID: {{ agent.id }}</h3>
          </div>
          <div class="agent-card-content">
            <p><strong>Username:</strong> {{ agent.username }}</p>
          </div>
          <div class="agent-card-actions">
            <button class="edit-button" @click="$emit('edit', agent)" title="Edit Agent">
              ✏️
            </button>
            <button class="delete-button" @click="$emit('delete', agent.id)" title="Delete Agent">
              🗑️
            </button>
          </div>
        </div>
      </div>
      <table v-else class="streams-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="agent in currentAgents" :key="agent.id">
            <td>{{ agent.id }}</td>
            <td>{{ agent.username }}</td>
            <td>
              <button class="edit-button" @click="$emit('edit', agent)" title="Edit Agent">
                ✏️
              </button>
              <button class="delete-button" @click="$emit('delete', agent.id)" title="Delete Agent">
                🗑️
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="table-footer">
        Showing {{ currentAgents.length }} of {{ filteredAgents.length }} agents
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';

export default {
  name: 'AgentTable',
  props: {
    agents: {
      type: Array,
      required: true
    }
  },
  emits: ['edit', 'delete'],
  setup(props) {
    const showCardView = ref(window.innerWidth < 768);
    const searchTerm = ref('');
    const currentPage = ref(1);
    const itemsPerPage = 5;

    const handleResize = () => {
      showCardView.value = window.innerWidth < 768;
    };

    onMounted(() => {
      window.addEventListener('resize', handleResize);
    });

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize);
    });

    const filteredAgents = computed(() => {
      return props.agents.filter(agent =>
        agent.username.toLowerCase().includes(searchTerm.value.toLowerCase())
      );
    });

    const totalPages = computed(() => 
      Math.ceil(filteredAgents.value.length / itemsPerPage)
    );

    const currentAgents = computed(() => {
      const indexOfLast = currentPage.value * itemsPerPage;
      const indexOfFirst = indexOfLast - itemsPerPage;
      return filteredAgents.value.slice(indexOfFirst, indexOfLast);
    });

    const paginate = (pageNumber) => {
      if (pageNumber < 1 || pageNumber > totalPages.value) return;
      currentPage.value = pageNumber;
    };

    return {
      showCardView,
      searchTerm,
      currentPage,
      filteredAgents,
      currentAgents,
      totalPages,
      paginate
    };
  }
};
</script>