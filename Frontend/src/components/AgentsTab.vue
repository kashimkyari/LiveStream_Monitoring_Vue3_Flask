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
              <th class="avatar-col"></th>
              <th>Agent</th>
              <th class="count-col">Streams</th>
              <th class="actions-col">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in agents" :key="agent.id" class="agent-row">
              <td class="avatar-col">
                <div class="avatar">{{ agent.username.charAt(0).toUpperCase() }}</div>
              </td>
              <td>
                <div class="agent-name">{{ agent.username }}</div>
              </td>
              <td class="count-col">{{ agent.assignments?.length || 0 }}</td>
              <td class="actions-col">
                <div class="actions">
                  <button @click.stop="$emit('edit', agent)" class="icon-button edit" title="Edit Agent" v-wave>
                    <font-awesome-icon icon="edit" />
                  </button>
                  <button @click.stop="$emit('delete', agent)" class="icon-button danger" title="Delete Agent" v-wave>
                    <font-awesome-icon icon="trash" />
                  </button>
                </div>
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
  padding-top: 1.5rem;
}

.tab-header {
  margin-bottom: 2rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
}

.tab-header h2 {
  margin: 0;
  font-size: 1.75rem;
  color: var(--text-color);
  font-weight: 600;
  letter-spacing: -0.5px;
}

.controls {
  display: flex;
  gap: 15px;
  align-items: center;
}

.create-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
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
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--input-border);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.agents-table:hover {
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}

.table-responsive {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
}

th, td {
  padding: 12px;
  text-align: left;
  vertical-align: middle;
}

th {
  background-color: var(--hover-bg);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.5px;
  color: var(--text-muted, #6c757d);
  border-bottom: 1px solid var(--input-border);
}

/* Column widths */
.avatar-col {
  width: 60px;
  padding: 8px;
}

.count-col {
  width: 80px;
  text-align: center;
}

.actions-col {
  width: 100px;
  padding-right: 16px;
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

.avatar {
  width: 36px;
  height: 36px;
  background-color: #4caf50;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1rem;
}

.agent-name {
  font-weight: 500;
  font-size: 1rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.icon-button {
  background: none;
  border: none;
  cursor: pointer;
  width: 32px;
  height: 32px;
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
  padding: 30px 0;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--text-muted, #6c757d);
}

.empty-icon {
  font-size: 1.75rem;
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--input-border);
  margin-bottom: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--input-border);
  background-color: var(--hover-bg);
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-details {
  padding: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-weight: 500;
  color: var(--text-muted, #6c757d);
  font-size: 0.85rem;
}

.detail-value {
  font-weight: 500;
}

.card-actions {
  padding: 10px 12px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid var(--input-border);
  background-color: var(--hover-bg);
}

.empty-state-mobile {
  text-align: center;
  padding: 30px 0;
  background-color: var(--input-bg);
  border-radius: 12px;
  border: 1px solid var(--input-border);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Responsive styles */
@media (max-width: 992px) {
  .tab-header {
    margin-bottom: 1.5rem;
  }
  
  .tab-header h2 {
    font-size: 1.5rem;
  }
}

@media (max-width: 768px) {
  .tab-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .controls {
    width: 100%;
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
    margin-top: 15px;
  }
}

@media (max-width: 480px) {
  .agents-tab {
    padding: 1rem 0.5rem;
  }
  
  .tab-header h2 {
    font-size: 1.4rem;
  }
}
</style>