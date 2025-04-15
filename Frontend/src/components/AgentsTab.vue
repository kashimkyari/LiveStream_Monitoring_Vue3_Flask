<template>
  <section class="agents-tab">
    <div class="tab-header">
      <h2>Agent Management</h2>
      <div class="controls">
        <button @click="$emit('create')" class="create-button" v-wave>
          <font-awesome-icon icon="plus" /> Add Agent
        </button>
      </div>
    </div>
    
    <div class="agents-table">
      <div class="table-responsive">
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Assigned Streams</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in agents" :key="agent.id" class="agent-row">
              <td>
                <div class="agent-info">
                  <div class="avatar">{{ agent.username.charAt(0).toUpperCase() }}</div>
                  <div class="agent-name">{{ agent.username }}</div>
                </div>
              </td>
              <td>{{ agent.assignments?.length || 0 }}</td>
              <td class="actions">
                <button @click.stop="$emit('edit', agent)" class="icon-button edit" title="Edit Agent" v-wave>
                  <font-awesome-icon icon="edit" />
                </button>
                <button @click.stop="$emit('delete', agent)" class="icon-button danger" title="Delete Agent" v-wave>
                  <font-awesome-icon icon="trash" />
                </button>
              </td>
            </tr>
            <tr v-if="agents.length === 0">
              <td colspan="4" class="empty-state">
                <div class="empty-content">
                  <font-awesome-icon icon="user-circle" class="empty-icon" />
                  <p>No agents found</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- Mobile Card View -->
    <div class="mobile-cards">
      <div v-for="agent in agents" :key="agent.id" class="agent-card">
        <div class="card-header">
          <div class="agent-info">
            <div class="avatar">{{ agent.username.charAt(0).toUpperCase() }}</div>
            <div class="agent-name">{{ agent.username }}</div>
          </div>
          <span class="status-badge" :class="agent.online ? 'active' : 'inactive'">
            {{ agent.online ? 'Online' : 'Offline' }}
          </span>
        </div>
        
        <div class="card-details">
          <div class="detail-row">
            <span class="detail-label">Assigned Streams:</span>
            <span class="detail-value">{{ agent.assignments?.length || 0 }}</span>
          </div>
        </div>
        
        <div class="card-actions">
          <button @click.stop="$emit('edit', agent)" class="icon-button edit" title="Edit Agent" v-wave>
            <font-awesome-icon icon="edit" />
          </button>
          <button @click.stop="$emit('delete', agent)" class="icon-button danger" title="Delete Agent" v-wave>
            <font-awesome-icon icon="trash" />
          </button>
        </div>
      </div>
      
      <div v-if="agents.length === 0" class="empty-state-mobile">
        <div class="empty-content">
          <font-awesome-icon icon="user-circle" class="empty-icon" />
          <p>No agents found</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'AgentsTab',
  props: {
    agents: {
      type: Array,
      default: () => []
    }
  },
  emits: ['create', 'edit', 'delete']
}
</script>

<style scoped>
.agents-tab {
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
  animation: fadeIn 0.4s ease;
  position: relative;
  padding-top: 1.5rem; /* Added padding top for better spacing */
}

.tab-header {
  margin-bottom: 2rem;
}

.tab-header h2 {
  margin-bottom: 1.5rem;
  font-size: 2rem;
  color: var(--text-color);
  font-weight: 600;
  letter-spacing: -0.5px;
}

.controls {
  display: flex;
  gap: 15px;
  align-items: center;
  justify-content: flex-end;
}

.create-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.create-button:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.agents-table {
  background-color: var(--input-bg);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--input-border);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.agents-table:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
}

.table-responsive {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

th, td {
  padding: 16px;
  text-align: left;
}

th {
  background-color: var(--hover-bg);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  color: var(--text-muted, #6c757d);
  border-bottom: 1px solid var(--input-border);
}

.text-center {
  text-align: center;
}

.agent-row {
  transition: all 0.2s ease;
  border-bottom: 1px solid var(--input-border);
}

.agent-row:hover {
  background-color: var(--hover-bg);
}

.agent-row:last-child {
  border-bottom: none;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  background-color: #4caf50;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.1rem;
}

.agent-name {
  font-weight: 500;
  font-size: 1rem;
}

.status-badge {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  min-width: 80px;
  justify-content: center;
}

.status-badge.active {
  background-color: rgba(40, 167, 69, 0.15);
  color: #28a745;
}

.status-badge.inactive {
  background-color: rgba(108, 117, 125, 0.15);
  color: #6c757d;
}

.actions {
  white-space: nowrap;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.icon-button {
  background: none;
  border: none;
  cursor: pointer;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.icon-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.icon-button.edit {
  color: #ffc107;
}

.icon-button.danger {
  color: #dc3545;
}

.icon-button:hover.danger {
  background-color: rgba(220, 53, 69, 0.1);
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--text-muted, #6c757d);
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 10px;
  opacity: 0.5;
}

/* Mobile Card View */
.mobile-cards {
  display: none;
}

.agent-card {
  background-color: var(--input-bg);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--input-border);
  margin-bottom: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.card-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--input-border);
  background-color: var(--hover-bg);
}

.card-details {
  padding: 16px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-weight: 500;
  color: var(--text-muted, #6c757d);
  font-size: 0.9rem;
}

.detail-value {
  font-weight: 500;
}

.card-actions {
  padding: 12px 16px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid var(--input-border);
  background-color: var(--hover-bg);
}

.empty-state-mobile {
  text-align: center;
  padding: 40px 0;
  background-color: var(--input-bg);
  border-radius: 12px;
  border: 1px solid var(--input-border);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Responsive styles */
@media (max-width: 1280px) {
  .agents-tab {
    padding: 1.5rem 1.25rem;
  }
}

@media (max-width: 992px) {
  .agents-tab {
    padding: 1.5rem 1rem;
  }
}

@media (max-width: 768px) {
  .agents-tab {
    padding: 1.25rem 0.75rem;
  }
  
  .tab-header h2 {
    font-size: 1.6rem;
    margin-bottom: 1.25rem;
  }
  
  .controls {
    width: 100%;
    justify-content: center;
  }
  
  .create-button {
    width: 100%;
    justify-content: center;
  }

  /* Show cards instead of table for mobile */
  .agents-table {
    display: none;
  }
  
  .mobile-cards {
    display: block;
    margin-top: 20px;
  }
}

@media (max-width: 480px) {
  .agents-tab {
    padding: 1rem 0.5rem;
  }
  
  .tab-header h2 {
    font-size: 1.4rem;
    margin-bottom: 1rem;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .card-header .status-badge {
    align-self: flex-start;
  }
  
  .card-actions {
    justify-content: space-around;
  }
  
  .avatar {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
}
</style>