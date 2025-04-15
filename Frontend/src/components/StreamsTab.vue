<template>
  <section class="streams-tab">
    <div class="tab-header">
      <h2>Stream Management</h2>
      <div class="controls">
        <div class="search-box">
          <font-awesome-icon icon="search" class="search-icon" />
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search streams..." 
            @input="filterStreams"
          />
        </div>
        <button @click="$emit('create')" class="create-button" v-wave>
          <font-awesome-icon icon="plus" /> Add Stream
        </button>
      </div>
    </div>
    
    <div class="streams-table">
      <div class="table-responsive">
        <table>
          <thead>
            <tr>
              <th>Streamer</th>
              <th>Platform</th>
              <th>Agent</th>
              <th class="text-center">Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stream in filteredStreams" :key="stream.id" class="stream-row">
              <td>
                <div class="streamer-info">
                  <div class="avatar">{{ stream.streamer_username.charAt(0).toUpperCase() }}</div>
                  <div>
                    <div class="streamer-name">{{ stream.streamer_username }}</div>
                    <div class="streamer-url">{{ formatUrl(stream.room_url) }}</div>
                  </div>
                </div>
              </td>
              <td>
                <span class="platform-tag" :class="stream.platform.toLowerCase()">
                  {{ stream.platform }}
                </span>
              </td>
              
              <td>
                <div class="agent-info">
                  <template v-if="getAssignedAgent(stream)">
                    <div class="agent-avatar">{{ getAssignedAgent(stream).username.charAt(0).toUpperCase() }}</div>
                    <div class="agent-name">{{ getAssignedAgent(stream).username }}</div>
                  </template>
                  <div v-else class="unassigned-label">
                    <font-awesome-icon icon="user-slash" />
                    <span>Unassigned</span>
                  </div>
                </div>
              </td>
              
              <td class="text-center">
                <span class="status-badge" :class="isStreamActive(stream) ? 'active' : 'inactive'">
                  {{ isStreamActive(stream) ? 'Active' : 'Inactive' }}
                </span>
              </td>
              
              <td class="actions">
                <button @click.stop="$emit('view', stream)" class="icon-button view" title="View Stream" v-wave>
                  <font-awesome-icon icon="eye" />
                </button>
                <button @click.stop="handleRefresh(stream)" class="icon-button refresh" title="Refresh Stream" v-wave>
                  <font-awesome-icon icon="sync-alt" />
                </button>
                <button @click.stop="$emit('edit', stream)" class="icon-button edit" title="Edit Stream" v-wave>
                  <font-awesome-icon icon="edit" />
                </button>
                <button @click.stop="confirmDelete(stream)" class="icon-button danger" title="Delete Stream" v-wave>
                  <font-awesome-icon icon="trash" />
                </button>
              </td>
            </tr>
            <tr v-if="filteredStreams.length === 0">
              <td colspan="5" class="empty-state">
                <div class="empty-content">
                  <font-awesome-icon icon="stream" class="empty-icon" />
                  <p>No streams found</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- Mobile Card View -->
    <div class="mobile-cards">
      <div v-for="stream in filteredStreams" :key="stream.id" class="stream-card">
        <div class="card-header">
          <div class="streamer-info">
            <div class="avatar">{{ stream.streamer_username.charAt(0).toUpperCase() }}</div>
            <div>
              <div class="streamer-name">{{ stream.streamer_username }}</div>
              <div class="streamer-url">{{ formatUrl(stream.room_url) }}</div>
            </div>
          </div>
          <span class="status-badge" :class="isStreamActive(stream) ? 'active' : 'inactive'">
            {{ isStreamActive(stream) ? 'Active' : 'Inactive' }}
          </span>
        </div>
        
        <div class="card-details">
          <div class="detail-row">
            <span class="detail-label">Platform:</span>
            <span class="platform-tag" :class="stream.platform.toLowerCase()">
              {{ stream.platform }}
            </span>
          </div>
          
          <div class="detail-row">
            <span class="detail-label">Agent:</span>
            <div class="agent-info">
              <template v-if="getAssignedAgent(stream)">
                <div class="agent-avatar">{{ getAssignedAgent(stream).username.charAt(0).toUpperCase() }}</div>
                <div class="agent-name">{{ getAssignedAgent(stream).username }}</div>
              </template>
              <div v-else class="unassigned-label">
                <font-awesome-icon icon="user-slash" />
                <span>Unassigned</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="card-actions">
          <button @click.stop="$emit('view', stream)" class="icon-button view" title="View Stream" v-wave>
            <font-awesome-icon icon="eye" />
          </button>
          <button @click.stop="handleRefresh(stream)" class="icon-button refresh" title="Refresh Stream" v-wave>
            <font-awesome-icon icon="sync-alt" />
          </button>
          <button @click.stop="$emit('edit', stream)" class="icon-button edit" title="Edit Stream" v-wave>
            <font-awesome-icon icon="edit" />
          </button>
          <button @click.stop="confirmDelete(stream)" class="icon-button danger" title="Delete Stream" v-wave>
            <font-awesome-icon icon="trash" />
          </button>
        </div>
      </div>
      
      <div v-if="filteredStreams.length === 0" class="empty-state-mobile">
        <div class="empty-content">
          <font-awesome-icon icon="stream" class="empty-icon" />
          <p>No streams found</p>
        </div>
      </div>
    </div>
    
    <!-- Confirmation Modal -->
   
  </section>
</template>

<script>
export default {
  name: 'StreamsTab',
  props: {
    streams: {
      type: Array,
      default: () => []
    },
    agents: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      searchQuery: '',
      filteredStreams: [],
      showDeleteModal: false,
      streamToDelete: null
    }
  },
  emits: ['create', 'edit', 'delete', 'view', 'refresh'],
  watch: {
    streams: {
      immediate: true,
      handler(newStreams) {
        this.filteredStreams = [...newStreams];
      }
    }
  },
  methods: {
    getAssignedAgent(stream) {
      // First check the assignments array
      if (stream.assignments && stream.assignments.length > 0) {
        const assignment = stream.assignments[0];
        
        // If assignment already has agent object with username
        if (assignment.agent && assignment.agent.username) {
          return assignment.agent;
        }
        
        // Otherwise find agent by ID from our agents array
        if (assignment.agent_id) {
          const foundAgent = this.agents.find(agent => agent.id === assignment.agent_id);
          if (foundAgent) return foundAgent;
        }
      }
      return null;
    },
    
    filterStreams() {
      if (!this.searchQuery) {
        this.filteredStreams = [...this.streams];
        return;
      }
      
      const query = this.searchQuery.toLowerCase();
      this.filteredStreams = this.streams.filter(stream => {
        return stream.streamer_username.toLowerCase().includes(query) || 
               stream.platform.toLowerCase().includes(query) ||
               (this.getAssignedAgent(stream)?.username || '').toLowerCase().includes(query);
      });
    },
    
    formatUrl(url) {
      try {
        const urlObj = new URL(url);
        return urlObj.hostname;
      } catch (e) {
        return url;
      }
    },
    
    isStreamActive(stream) {
      // You can implement logic to determine if a stream is active
      // For now, we'll assume it's active if it has a valid m3u8 URL
      if (stream.platform === 'Chaturbate') {
        return !!stream.chaturbate_m3u8_url;
      } else if (stream.platform === 'Stripchat') {
        return !!stream.stripchat_m3u8_url;
      }
      return false;
    },
    
    handleRefresh(stream) {
      this.$emit('refresh', stream);
    },
    
    confirmDelete(stream) {
      this.streamToDelete = stream;
      this.showDeleteModal = true;
    },
    
    cancelDelete() {
      this.showDeleteModal = false;
      this.streamToDelete = null;
    },
    
    confirmDeleteAction() {
      if (this.streamToDelete) {
        this.$emit('delete', this.streamToDelete);
        this.showDeleteModal = false;
        this.streamToDelete = null;
      }
    }
  }
}
</script>

<style scoped>
.streams-tab {
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
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted, #6c757d);
  opacity: 0.6;
}

.search-box input {
  width: 100%;
  padding: 10px 15px 10px 35px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.search-box input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
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

.streams-table {
  background-color: var(--input-bg);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--input-border);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.streams-table:hover {
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

.stream-row {
  transition: all 0.2s ease;
  border-bottom: 1px solid var(--input-border);
}

.stream-row:hover {
  background-color: var(--hover-bg);
}

.stream-row:last-child {
  border-bottom: none;
}

.streamer-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  background-color: var(--primary-color);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.1rem;
}

.streamer-name {
  font-weight: 500;
  font-size: 1rem;
}

.streamer-url {
  font-size: 0.8rem;
  color: var(--text-muted, #6c757d);
  margin-top: 3px;
}

.platform-tag {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.platform-tag.chaturbate {
  background-color: rgba(244, 67, 54, 0.15);
  color: #f44336;
}

.platform-tag.stripchat {
  background-color: rgba(33, 150, 243, 0.15);
  color: #2196f3;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-avatar {
  width: 34px;
  height: 34px;
  background-color: #4caf50;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.agent-name {
  font-weight: 500;
  font-size: 0.95rem;
}

.unassigned-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted, #6c757d);
  font-size: 0.85rem;
  opacity: 0.8;
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

.icon-button.view {
  color: #6c757d;
}

.icon-button.refresh {
  color: #2196f3;
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

.stream-card {
  background-color: var(--input-bg);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--input-border);
  margin-bottom: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stream-card:hover {
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

/* Delete Modal */
.delete-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(3px);
}

.modal-content {
  background-color: var(--input-bg);
  padding: 30px;
  border-radius: 12px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.modal-content h3 {
  margin-top: 0;
  color: var(--heading-color, #333);
  font-size: 1.5rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 25px;
}

.cancel-button {
  padding: 10px 18px;
  background-color: transparent;
  border: 1px solid var(--input-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
}

.cancel-button:hover {
  background-color: var(--hover-bg);
}

.delete-button {
  padding: 10px 18px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
}

.delete-button:hover {
  background-color: #c82333;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Responsive styles */
@media (max-width: 1280px) {
  .streams-tab {
    padding: 1.5rem 1.25rem;
  }
}

@media (max-width: 992px) {
  .streams-tab {
    padding: 1.5rem 1rem;
  }
}

@media (max-width: 768px) {
  .streams-tab {
    padding: 1.25rem 0.75rem;
  }
  
  .tab-header h2 {
    font-size: 1.6rem;
    margin-bottom: 1.25rem;
  }
  
  .controls {
    flex-direction: column;
    width: 100%;
    gap: 12px;
  }
  
  .search-box {
    width: 100%;
    max-width: none;
  }
  
  .create-button {
    width: 100%;
    justify-content: center;
  }

  /* Show cards instead of table for mobile */
  .streams-table {
    display: none;
  }
  
  .mobile-cards {
    display: block;
    margin-top: 20px;
  }
}

@media (max-width: 480px) {
  .streams-tab {
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
  
  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .avatar {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
  
  .agent-avatar {
    width: 30px;
    height: 30px;
    font-size: 0.8rem;
  }
}
</style>