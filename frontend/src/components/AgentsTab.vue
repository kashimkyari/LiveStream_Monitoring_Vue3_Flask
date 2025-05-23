<template>
  <section class="agents-tab">
    <div class="tab-header">
      <h2>Agent Management</h2>
      <div class="controls">
        <div class="search-box">
          <font-awesome-icon icon="search" class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search agents..." 
          />
        </div>
        <button @click="openCreateModal" class="create-button" v-wave>
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
              <th>Username</th>
              <th>Email</th>
              <th>Status</th>
              <th class="count-col">Streams</th>
              <th class="actions-col">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in filteredAgents" :key="agent.agent_id || agent.id" class="agent-row" :class="{'highlight': (agent.agent_id || agent.id) === highlightedAgentId}">
              <td class="avatar-col">
                <div class="avatar">{{ agent.username.charAt(0).toUpperCase() }}</div>
              </td>
              <td>
                <div class="agent-name">{{ agent.username }}</div>
                <div class="agent-role" v-if="agent.role">{{ agent.role }}</div>
              </td>
              <td>
                <div class="agent-email">{{ agent.email || 'N/A' }}</div>
              </td>
              <td>
                <span class="status-badge" :class="{'active': agent.online, 'inactive': !agent.online}" v-if="agent.hasOwnProperty('online')">{{ agent.online ? 'Online' : 'Offline' }}</span>
                <span class="status-badge unknown" v-else>Unknown</span>
              </td>
              <td class="count-col" @click="toggleStreamsList(agent)" @mouseenter="showStreamsList(agent)" @mouseleave="hideStreamsList">
                <div class="stream-count">{{ getStreamCount(agent) }}</div>
                <div v-if="activeAgent === (agent.agent_id || agent.id)" class="streams-tooltip">
                  <div class="tooltip-header">Assigned Streams ({{ getStreamCount(agent) }})</div>
                  <div v-if="getStreamCount(agent) > 0" class="stream-list">
                    <div v-for="assignment in agent.assignments" :key="assignment.id" class="stream-item">
                      <span v-if="assignment.stream">
                        <strong>{{ assignment.stream.streamer_username }}</strong> ({{ assignment.stream.platform }}) - 
                        <span class="stream-status" :class="{'online': assignment.stream.status === 'online', 'offline': assignment.stream.status !== 'online'}">{{ assignment.stream.status === 'online' ? 'Online' : 'Offline' }}</span>
                        <br />
                        <a :href="assignment.stream.room_url" target="_blank" class="stream-link">View Stream</a>
                      </span>
                      <span v-else class="unavailable">Stream details unavailable</span>
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
                    <font-awesome-icon icon="trash" :class="{'animate-trash': deletingAgentId === (agent.agent_id || agent.id)}" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="agents.length === 0">
              <td colspan="6" class="empty-state">
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
      <div v-for="agent in filteredAgents" :key="agent.agent_id || agent.id" class="agent-card">
        <div class="card-header">
          <div class="agent-info">
            <div class="avatar">{{ agent.username.charAt(0).toUpperCase() }}</div>
            <div class="agent-name">{{ agent.username }}</div>
          </div>
          <div class="agent-status" :class="{'online': agent.online, 'offline': !agent.online}" v-if="agent.hasOwnProperty('online')">{{ agent.online ? 'Online' : 'Offline' }}</div>
          <div class="agent-status unknown" v-else>Unknown</div>
        </div>
        <div class="card-details">
          <div class="detail-row" v-if="agent.email">
            <span class="detail-label">Email:</span>
            <span class="detail-value">{{ agent.email }}</span>
          </div>
          <div class="detail-row" v-if="agent.role">
            <span class="detail-label">Role:</span>
            <span class="detail-value">{{ agent.role }}</span>
          </div>
          <div class="detail-row" @click="toggleStreamsList(agent)">
            <span class="detail-label">Assigned Streams:</span>
            <span class="detail-value">{{ getStreamCount(agent) }}</span>
            <font-awesome-icon :icon="expandedAgent === (agent.agent_id || agent.id) ? 'chevron-up' : 'chevron-down'" class="expand-icon" />
          </div>
          <div v-if="expandedAgent === (agent.agent_id || agent.id)" class="stream-list-mobile">
            <div v-if="getStreamCount(agent) > 0" class="stream-items">
              <div v-for="assignment in agent.assignments" :key="assignment.id" class="stream-item-mobile">
                <span v-if="assignment.stream">
                  {{ assignment.stream.streamer_username }} ({{ assignment.stream.platform }}) - 
                  <a :href="assignment.stream.room_url" target="_blank" class="stream-link">View Stream</a>
                </span>
                <span v-else>Stream details unavailable</span>
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
            <font-awesome-icon icon="trash" :class="{'animate-trash': deletingAgentId === (agent.agent_id || agent.id)}" />
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
    <CreateAgentModal 
      v-if="showCreateModal" 
      :is-editing="isEditing" 
      :agent="editingAgent" 
      @close="closeCreateModal" 
      @submit="handleAgentSubmit" 
    />
  </section>
</template>

<script>
import axios from 'axios';
import { useToast } from 'vue-toastification';
import CreateAgentModal from './CreateAgentModal.vue';

export default {
  name: 'AgentsTab',
  components: {
    CreateAgentModal
  },
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
      showCreateModal: false,
      showDeleteModal: false,
      isEditing: false,
      editingAgent: null,
      agentToDelete: null,
      deletingAgentId: null,
      searchQuery: '',
      highlightedAgentId: null,
      localAgents: [],
      agentsFetched: false
    };
  },
  emits: ['edit', 'delete', 'agentUpdated', 'reloadAgents'],
  setup() {
    const toast = useToast();
    return { toast };
  },
  computed: {
    filteredAgents() {
      return this.localAgents.filter(agent => {
        const usernameMatch = agent.username && agent.username.toLowerCase().includes(this.searchQuery.toLowerCase());
        const emailMatch = agent.email && agent.email.toLowerCase().includes(this.searchQuery.toLowerCase());
        return usernameMatch || emailMatch;
      });
    }
  },
  methods: {
    getStreamCount(agent) {
      return agent.assignments?.length || 0;
    },
    fetchAssignmentsForAgent(agent) {
      if (agent.assignments) return; // Already have assignments
      axios.get('/api/assignments', {
        params: {
          agent_id: agent.agent_id || agent.id
        }
      })
        .then(response => {
          agent.assignments = response.data.assignments || [];
        })
        .catch(error => {
          console.error(`Error fetching assignments for agent ${agent.agent_id || agent.id}:`, error);
          agent.assignments = [];
        });
    },
    showStreamsList(agent) {
      this.activeAgent = agent.agent_id || agent.id;
      this.fetchAssignmentsForAgent(agent);
    },
    hideStreamsList() {
      this.activeAgent = null;
    },
    toggleStreamsList(agent) {
      this.expandedAgent = this.expandedAgent === (agent.agent_id || agent.id) ? null : (agent.agent_id || agent.id);
      if (this.expandedAgent) {
        this.fetchAssignmentsForAgent(agent);
      }
    },
    openCreateModal() {
      this.isEditing = false;
      this.editingAgent = null;
      this.showCreateModal = true;
    },
    editAgent(agent) {
      this.isEditing = true;
      this.editingAgent = agent;
      this.showCreateModal = true;
      this.highlightedAgentId = agent.agent_id || agent.id;
      setTimeout(() => {
        this.highlightedAgentId = null;
      }, 3000);
    },
    closeCreateModal() {
      this.showCreateModal = false;
      this.editingAgent = null;
    },
    handleAgentSubmit(formData) {
      const payload = {
        username: formData.username,
        email: formData.email
      };
      if (formData.password) {
        payload.password = formData.password
      }
      if (formData.receiveUpdates !== undefined) {
        payload.receiveUpdates = formData.receiveUpdates
      }
      if (this.isEditing) {
        const agentId = this.editingAgent.agent_id || this.editingAgent.id;
        axios.put(`/api/agents/${agentId}`, payload)
          .then(response => {
            this.$emit('agentUpdated', response.data.agent);
            this.toast.success('Agent updated successfully', {
              timeout: 3000,
              position: "top-center",
              icon: true
            });
            this.highlightedAgentId = response.data.agent.agent_id || response.data.agent.id;
            setTimeout(() => {
              this.highlightedAgentId = null;
            }, 3000);
            this.closeCreateModal();
            this.reloadAgents();
          })
          .catch(error => {
            console.error('Error updating agent:', error);
            this.toast.error('Failed to update agent: ' + (error.response?.data?.message || 'Unknown error'), {
              timeout: 3000,
              position: "top-center",
              icon: true
            });
          });
      } else {
        axios.post('/api/register', payload)
          .then(response => {
            this.$emit('agentUpdated', response.data.user);
            this.toast.success('Agent created successfully', {
              timeout: 3000,
              position: "top-center",
              icon: true
            });
            this.highlightedAgentId = response.data.user.agent_id || response.data.user.id;
            setTimeout(() => {
              this.highlightedAgentId = null;
            }, 3000);
            this.closeCreateModal();
            this.reloadAgents();
          })
          .catch(error => {
            console.error('Error creating agent:', error);
            this.toast.error('Failed to create agent: ' + (error.response?.data?.message || 'Unknown error'), {
              timeout: 3000,
              position: "top-center",
              icon: true
            });
          });
      }
    },
    confirmDeleteAgent(agent) {
      this.agentToDelete = agent;
      this.showDeleteModal = true;
    },
    deleteAgent() {
      if (!this.agentToDelete) return;
      const agentId = this.agentToDelete.agent_id || this.agentToDelete.id;
      this.deletingAgentId = agentId;
      console.log('Attempting to delete agent with ID:', agentId);
      console.log('Full agent object:', this.agentToDelete);
      axios.delete(`/api/agents/${agentId}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
        .then(response => {
          console.log('Delete successful:', response.data);
          console.log('Full response:', response);
          this.$emit('agentUpdated');
          this.toast.success('Agent deleted successfully', {
            timeout: 3000,
            position: "top-center",
            icon: true
          });
          this.showDeleteModal = false;
          this.agentToDelete = null;
          this.deletingAgentId = null;
          this.reloadAgents();
        })
        .catch(error => {
          console.error('Error deleting agent:', error);
          console.error('Error response:', error.response);
          console.error('Full error object:', error);
          let errorMessage = 'Failed to delete agent';
          if (error.response) {
            errorMessage += ` (Status: ${error.response.status})`;
            if (error.response.data && error.response.data.message) {
              errorMessage += `: ${error.response.data.message}`;
            }
            if (error.response.status === 500) {
              errorMessage += `: Server error - 'PasswordReset' is not defined in the backend. Please contact support to fix this issue.`;
            }
          } else if (error.request) {
            errorMessage += ': No response received from server';
          } else {
            errorMessage += `: ${error.message}`;
          }
          this.toast.error(errorMessage, {
            timeout: 7000,
            position: "top-center",
            icon: true
          });
          this.deletingAgentId = null;
        });
    },
    cancelDelete() {
      this.showDeleteModal = false;
      this.agentToDelete = null;
    },
    reloadAgents() {
      this.$emit('reloadAgents');
      // Also fetch agents locally if props are not updated immediately
      this.fetchAgents();
    },
    fetchAgents() {
      if (this.agentsFetched) return;
      axios.get('/api/agents')
        .then(response => {
          this.localAgents = response.data || [];
          this.agentsFetched = true;
          // Optionally, fetch assignments for all agents upfront
          this.localAgents.forEach(agent => {
            if (!agent.assignments) {
              this.fetchAssignmentsForAgent(agent);
            }
          });
        })
        .catch(error => {
          console.error('Error fetching agents:', error);
          this.toast.error('Failed to fetch agents: ' + (error.response?.data?.message || 'Unknown error'), {
            timeout: 3000,
            position: "top-center",
            icon: true
          });
          // If fetch fails, fall back to props
          this.localAgents = this.agents;
        });
    }
  },
  mounted() {
    this.reloadAgents();
    // Initialize localAgents from props if available
    if (this.agents.length > 0) {
      this.localAgents = this.agents;
      this.agentsFetched = true;
    }
  },
  watch: {
    agents(newAgents) {
      // Update localAgents when props change
      this.localAgents = newAgents;
      this.agentsFetched = true;
    }
  }
}
</script>

<style scoped>
.agents-tab {
  box-sizing: border-box;
  animation: fadeIn 0.4s ease;
  position: relative;
  padding-top: 1.5rem;
  flex-wrap: wrap;
  width: auto;
  padding-right: 20px;
  
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

.search-box {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
}

.search-box input {
  padding: 8px 16px 8px 30px;
  border: 1px solid var(--input-border);
  border-radius: 6px;
  background-color: var(--background-color);
  font-size: 0.95rem;
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
  min-height: 300px;
  max-height: 600px;
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
  overflow-x: hidden;
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
  justify-content: space-around;
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
  
  .agents-table {
    min-height: 200px;
    max-height: 500px;
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

.agent-row.highlight {
  animation: highlight 0.5s ease-in-out 3 alternate;
}

@keyframes highlight {
  0% { background-color: rgba(var(--primary-rgb), 0.04); }
  100% { background-color: rgba(var(--primary-rgb), 0.2); }
}

.animate-trash {
  animation: trashShake 0.5s ease-in-out infinite alternate;
}

@keyframes trashShake {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(10deg); }
}

.stream-link {
  color: var(--primary-color);
  text-decoration: none;
}
.stream-link:hover {
  text-decoration: underline;
}

.streams-tooltip {
  position: absolute;
  top: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  background-color: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 8px;
  padding: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  min-width: 200px;
  max-width: 300px;
  font-size: 0.85rem;
  color: var(--text-color);
}

/* Add a tooltip arrow */
.streams-tooltip::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 12px;
  height: 12px;
  background-color: var(--input-bg);
  border-left: 1px solid var(--input-border);
  border-top: 1px solid var(--input-border);
}

.tooltip-header {
  font-weight: 600;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--input-border);
  padding-bottom: 6px;
  color: var(--primary-color);
}

.stream-list {
  max-height: 150px;
  overflow-y: auto;
}

.stream-item {
  margin-bottom: 8px;
  line-height: 1.4;
  border-left: 2px solid var(--primary-color);
  padding-left: 8px;
}

.stream-item:last-child {
  margin-bottom: 0;
}

.empty-streams {
  color: var(--text-muted);
  font-style: italic;
}

.agent-status {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.agent-status.online {
  background-color: rgba(40, 199, 111, 0.1);
  color: #28c76f;
}

.agent-status.offline {
  background-color: rgba(234, 84, 85, 0.1);
  color: #ea5455;
}

.agent-status.unknown {
  background-color: rgba(108, 117, 125, 0.1);
  color: #6c757d;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge.active {
  background-color: rgba(40, 199, 111, 0.1);
  color: #28c76f;
}

.status-badge.inactive {
  background-color: rgba(234, 84, 85, 0.1);
  color: #ea5455;
}

.status-badge.unknown {
  background-color: rgba(108, 117, 125, 0.1);
  color: #6c757d;
}

.stream-status {
  font-size: 0.75rem;
  padding: 1px 4px;
  border-radius: 10px;
  margin-left: 5px;
}

.stream-status.online {
  background-color: rgba(40, 199, 111, 0.15);
  color: #28c76f;
}

.stream-status.offline {
  background-color: rgba(234, 84, 85, 0.15);
  color: #ea5455;
}

.unavailable {
  color: var(--text-muted);
  font-style: italic;
}

.agent-email {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
  display: inline-block;
  vertical-align: middle;
}
</style>