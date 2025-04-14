<template>
  <section class="streams-tab">
    <div class="tab-header">
      <h2>Stream Management</h2>
      <button @click="$emit('create')" class="create-button" v-wave>
        <font-awesome-icon icon="plus" /> Add Stream
      </button>
    </div>
    
    <div class="streams-table">
      <div class="table-responsive">
        <table>
          <thead>
            <tr>
              <th>Streamer</th>
              <th>Platform</th>
              <th>Assigned Agent</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stream in streams" :key="stream.id">
              <td>{{ stream.streamer_username }}</td>
              <td>
                <span class="platform-tag" :class="stream.platform.toLowerCase()">
                  {{ stream.platform }}
                </span>
              </td>
              
              <td>
                {{ getAssignedAgentUsername(stream) }}
              </td>
              <td>
                <span class="status-badge" :class="{ active: stream.is_live }">
                  {{ stream.is_live ? 'Live' : 'Offline' }}
                </span>
              </td>
              <td class="actions">
                <button @click.stop="$emit('edit', stream)" class="icon-button" v-wave>
                  <font-awesome-icon icon="edit" />
                </button>
                <button @click.stop="$emit('delete', stream)" class="icon-button danger" v-wave>
                  <font-awesome-icon icon="trash" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'StreamsTab',
  props: {
    streams: Array,
    agents: Array
  },
  emits: ['create', 'edit', 'delete'],
  methods: {
    getAssignedAgentUsername(stream) {
      // Safely check if stream.assignments exists, has at least one element, and that element has an agent with username
      if (stream.assignments && 
          stream.assignments.length > 0 && 
          stream.assignments[0].agent && 
          stream.assignments[0].agent.username) {
        return stream.assignments[0].agent.username;
      }
      return 'Unassigned';
    }
  }
}
</script>

<style scoped>
.streams-tab {
  animation: fadeIn 0.4s ease;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tab-header h2 {
  margin: 0;
  font-size: 1.8rem;
}

.create-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: opacity 0.3s ease;
  display: inline-flex;
  align-items: center;
  font-size: 0.9rem;
}

.create-button:hover {
  opacity: 0.9;
}

.streams-table {
  background-color: var(--input-bg);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.table-responsive {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid var(--input-border);
}

th {
  background-color: var(--hover-bg);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.5px;
}

tr:hover {
  background-color: var(--hover-bg);
}

.platform-tag {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.platform-tag.chaturbate {
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.platform-tag.stripchat {
  background-color: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.active {
  background-color: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.status-badge:not(.active) {
  background-color: rgba(108, 117, 125, 0.2);
  color: #6c757d;
}

.actions {
  white-space: nowrap;
}

.icon-button {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  padding: 5px;
  margin: 0 5px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.icon-button:hover {
  opacity: 1;
}

.icon-button.danger {
  color: #dc3545;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Responsive styles */
@media (max-width: 768px) {
  .tab-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .create-button {
    width: 100%;
  }
}
</style>