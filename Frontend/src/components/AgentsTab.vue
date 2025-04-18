<template>
  <section class="agents-tab">
    <div class="tab-header">
      <h2>Agent Management</h2>
      <div class="controls">
        <button @click="createAgent" class="create-button" v-wave>
          <font-awesome-icon icon="plus" /> Add Agent
        </button>
      </div>
    </div>
    <div class="agents-table">
      <div class="table-wrapper">
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
              <td class="count-col" @mouseenter="showStreamsList(agent)" @mouseleave="hideStreamsList">
                <div class="stream-count">{{ getStreamCount(agent) }}</div>
                <div v-if="activeAgent === agent.id" class="streams-tooltip">
                  <div class="tooltip-header">Assigned Streams</div>
                  <div v-if="getStreamCount(agent) > 0" class="stream-list">
                    <div v-for="assignment in agent.assignments" :key="assignment.id" class="stream-item">
                      {{ getStreamInfo(assignment) }}
                    </div>
                  </div>
                  <div v-else class="empty-streams">No streams assigned</div>
                </div>
              </td>
              <td class="actions-col">
                <div class="actions">
                  <button @click.stop="editAgent(agent)" class="icon-button edit" title="Edit Agent" v-wave>
                    <font-awesome-icon icon="edit" />
                  </button>
                  <button @click.stop="confirmDeleteAgent(agent)" class="icon-button danger" title="Delete Agent" v-wave>
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
    <div class="mobile-cards">
      <div v-for="agent in agents" :key="agent.id" class="agent-card">
        <div class="card-header">
          <div class="agent-info">
            <div class="avatar">{{ agent.username.charAt(0).toUpperCase() }}</div>
            <div class="agent-name">{{ agent.username }}</div>
          </div>
        </div>
        <div class="card-details">
          <div class="detail-row" @click="toggleStreamsList(agent)">
            <span class="detail-label">Assigned Streams:</span>
            <span class="detail-value">{{ getStreamCount(agent) }}</span>
            <font-awesome-icon :icon="expandedAgent === agent.id ? 'chevron-up' : 'chevron-down'" class="expand-icon" />
          </div>
          <div v-if="expandedAgent === agent.id" class="stream-list-mobile">
            <div v-if="getStreamCount(agent) > 0" class="stream-items">
              <div v-for="assignment in agent.assignments" :key="assignment.id" class="stream-item-mobile">
                {{ getStreamInfo(assignment) }}
              </div>
            </div>
            <div v-else class="empty-streams">No streams assigned</div>
          </div>
        </div>
        <div class="card-actions">
          <button @click.stop="editAgent(agent)" class="icon-button edit" title="Edit Agent" v-wave>
            <font-awesome-icon icon="edit" />
          </button>
          <button @click.stop="confirmDeleteAgent(agent)" class="icon-button danger" title="Delete Agent" v-wave>
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
    <div v-if="showEditModal" class="modal-overlay" @click.self="cancelEdit">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ isNewAgent ? 'Add New Agent' : 'Edit Agent' }}</h3>
          <button @click="cancelEdit" class="close-button">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="username">Username</label>
            <input type="text" id="username" v-model="editForm.username" placeholder="Enter username">
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" v-model="editForm.password" 
              :placeholder="isNewAgent ? 'Enter password' : 'Leave blank to keep current password'">
          </div>
        </div>
        <div class="modal-footer">
          <button @click="cancelEdit" class="btn-cancel">Cancel</button>
          <button @click="saveAgent" class="btn-save" :disabled="!editForm.username">
            Save
          </button>
        </div>
      </div>
    </div>
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="cancelDelete">
      <div class="modal-content delete-modal">
        <div class="modal-header">
          <h3>Delete Agent</h3>
          <button @click="cancelDelete" class="close-button">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <div class="modal-body">
          <p>Are you sure you want to delete the agent <strong>{{ agentToDelete?.username }}</strong>?</p>
          <p class="warning-text">This action cannot be undone and will remove all assignments for this agent.</p>
        </div>
        <div class="modal-footer">
          <button @click="cancelDelete" class="btn-cancel">Cancel</button>
          <button @click="deleteAgent" class="btn-delete">
            Delete
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import axios from 'axios';
export default {
  name: 'AgentsTab',
  props: {
    agents: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      activeAgent: null,
      expandedAgent: null,
      showEditModal: false,
      showDeleteModal: false,
      isNewAgent: false,
      editingAgent: null,
      agentToDelete: null,
      editForm: {
        username: '',
        password: ''
      },
      streams: {}
    };
  },
  emits: ['edit', 'delete', 'agentUpdated'],
  methods: {
    getStreamCount(agent) {
      return agent.assignments?.length || 0;
    },
    getStreamInfo(assignment) {
      if (this.streams[assignment.stream_id]) {
        const stream = this.streams[assignment.stream_id];
        return `${stream.streamer_username} (${stream.type})`;
      }
      return `Stream #${assignment.stream_id}`;
    },
    showStreamsList(agent) {
      this.activeAgent = agent.id;
      if (agent.assignments && agent.assignments.length > 0) {
        agent.assignments.forEach(assignment => {
          if (!this.streams[assignment.stream_id]) {
            this.fetchStreamInfo(assignment.stream_id);
          }
        });
      }
    },
    hideStreamsList() {
      this.activeAgent = null;
    },
    toggleStreamsList(agent) {
      this.expandedAgent = this.expandedAgent === agent.id ? null : agent.id;
      if (this.expandedAgent && agent.assignments && agent.assignments.length > 0) {
        agent.assignments.forEach(assignment => {
          if (!this.streams[assignment.stream_id]) {
            this.fetchStreamInfo(assignment.stream_id);
          }
        });
      }
    },
    fetchStreamInfo(streamId) {
      axios.get(`/api/streams/${streamId}`)
        .then(response => {
          const stream = response.data;
          this.$set(this.streams, streamId, stream);
        })
        .catch(error => {
          console.error('Error fetching stream info:', error);
          this.$set(this.streams, streamId, { 
            streamer_username: 'Unknown', 
            type: 'unknown' 
          });
        });
    },
    editAgent(agent) {
      this.isNewAgent = false;
      this.editingAgent = agent;
      this.editForm.username = agent.username;
      this.editForm.password = '';
      this.showEditModal = true;
    },
    createAgent() {
      this.isNewAgent = true;
      this.editingAgent = null;
      this.editForm.username = '';
      this.editForm.password = '';
      this.showEditModal = true;
    },
    saveAgent() {
      const payload = {
        username: this.editForm.username
      };
      if (this.editForm.password) {
        payload.password = this.editForm.password;
      }
      if (this.isNewAgent) {
        axios.post('/api/agents', payload)
          .then(response => {
            this.$emit('agentUpdated', response.data.agent);
            this.showEditModal = false;
          })
          .catch(error => {
            console.error('Error creating agent:', error);
            alert('Failed to create agent: ' + (error.response?.data?.message || 'Unknown error'));
          });
      } else {
        axios.put(`/api/agents/${this.editingAgent.id}`, payload)
          .then(response => {
            this.$emit('agentUpdated', response.data.agent);
            this.showEditModal = false;
          })
          .catch(error => {
            console.error('Error updating agent:', error);
            alert('Failed to update agent: ' + (error.response?.data?.message || 'Unknown error'));
          });
      }
    },
    confirmDeleteAgent(agent) {
      this.agentToDelete = agent;
      this.showDeleteModal = true;
    },
    deleteAgent() {
      if (!this.agentToDelete) return;
      axios.delete(`/api/agents/${this.agentToDelete.id}`)
        .then(() => {
          this.$emit('agentUpdated');
          this.showDeleteModal = false;
          this.agentToDelete = null;
        })
        .catch(error => {
          console.error('Error deleting agent:', error);
          alert('Failed to delete agent: ' + (error.response?.data?.message || 'Unknown error'));
        });
    },
    cancelEdit() {
      this.showEditModal = false;
      this.editingAgent = null;
      this.editForm.username = '';
      this.editForm.password = '';
    },
    cancelDelete() {
      this.showDeleteModal = false;
      this.agentToDelete = null;
    }
  }
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

/* Updated Table Styles from StreamsTab */
.agents-table {
  height: calc(100vh - 250px);
  min-height: 400px;
  max-height: 800px;
  overflow: hidden;
  position: relative;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--input-border);
  background-color: var(--input-bg);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.table-wrapper {
  height: 100%;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--primary-rgb), 0.3) transparent;
}

.table-wrapper::-webkit-scrollbar {
  width: 8px;
}

.table-wrapper::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 10px;
}

.table-wrapper::-webkit-scrollbar-thumb {
  background-color: rgba(var(--primary-rgb), 0.3);
  border-radius: 10px;
  border: 2px solid transparent;
}

.table-wrapper::-webkit-scrollbar-thumb:hover {
  background-color: rgba(var(--primary-rgb), 0.5);
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  color: var(--text-color);
}

thead th {
  position: sticky;
  top: 0;
  background-color: var(--input-bg);
  padding: 1.2rem 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
  font-size: 0.9rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  z-index: 10;
}

tbody tr {
  transition: background-color 0.2s ease;
}

tbody tr:hover {
  background-color: rgba(var(--primary-rgb), 0.04);
}

tbody td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  vertical-align: middle;
}

/* Original AgentsTab-specific styles */
.avatar-col {
  width: 60px;
  padding: 8px;
}

.count-col {
  width: 80px;
  text-align: center;
  position: relative;
}

.stream-count {
  cursor: pointer;
  display: inline-block;
  padding: 2px 8px;
  background-color: var(--primary-color);
  color: white;
  border-radius: 12px;
  font-size: 0.8rem;
  min-width: 20px;
  text-align: center;
}

.actions-col {
  width: 100px;
  padding-right: 16px;
}

.agent-row {
  transition: all 0.2s ease;
}

.agent-row:hover {
  background-color: var(--hover-bg);
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

/* Stream list mobile */
.stream-list-mobile {
  padding: 8px 0;
  margin-top: 10px;
  border-top: 1px dashed var(--input-border);
  animation: fadeIn 0.3s ease;
}

.stream-items {
  max-height: 150px;
  overflow-y: auto;
}

.stream-item-mobile {
  padding: 5px 0;
  margin-bottom: 5px;
  font-size: 0.85rem;
  color: var(--text-color);
}

.expand-icon {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-left: 5px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  background-color: var(--input-bg);
  border-radius: 10px;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

.delete-modal {
  max-width: 400px;
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--input-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--text-muted);
  transition: color 0.2s ease;
}

.close-button:hover {
  color: var(--text-color);
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid var(--input-border);
  background-color: var(--background-color);
  transition: border-color 0.3s, box-shadow 0.3s;
  font-size: 0.95rem;
}

.form-group input:focus {
  border-color: var(--primary-color);
  outline: none;
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--input-border);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-cancel, .btn-save, .btn-delete {
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel {
  background-color: transparent;
  border: 1px solid var(--input-border);
  color: var(--text-color);
}

.btn-cancel:hover {
  background-color: var(--hover-bg);
}

.btn-save {
  background-color: var(--primary-color);
  border: none;
  color: white;
}

.btn-save:hover {
  opacity: 0.9;
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-delete {
  background-color: #dc3545;
  border: none;
  color: white;
}

.btn-delete:hover {
  opacity: 0.9;
}

.warning-text {
  color: #dc3545;
  font-size: 0.9rem;
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
  cursor: pointer;
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

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
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
  
  .modal-content {
    width: 95%;
  }
}
</style>