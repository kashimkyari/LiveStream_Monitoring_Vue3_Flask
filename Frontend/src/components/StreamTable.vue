<template>
  <div class="stream-table-container">
    <div v-if="streams.length === 0" class="empty-state">
      No {{ platform }} streams available.
    </div>
    <template v-else>
      <div class="search-controls">
        <div class="search-wrapper">
          <span class="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search streams..."
            v-model="searchTerm"
            class="search-input"
          />
        </div>
        <div class="view-toggle">
          <button
            :class="['view-button', { active: !showCardView }]"
            @click="showCardView = false"
            aria-label="Table view"
          >
            <span class="icon">📋</span>
          </button>
          <button
            :class="['view-button', { active: showCardView }]"
            @click="showCardView = true"
            aria-label="Card view"
          >
            <span class="icon">📱</span>
          </button>
        </div>
      </div>

      <!-- Card View Layout -->
      <div v-if="showCardView" class="stream-cards">
        <div
          v-for="stream in filteredStreams"
          :key="stream.id"
          :class="['stream-card', { 'new-stream-highlight': newStreamId === stream.id }]"
        >
          <div class="card-header">
            <h3 class="card-title">ID: {{ stream.id }}</h3>
            <button
              @click="confirmDelete(stream.id, stream.streamer_username)"
              class="delete-button"
              title="Delete stream"
              aria-label="Delete stream"
            >
              <span class="delete-icon">🗑️</span>
            </button>
          </div>
          <div class="card-content">
            <div class="info-row">
              <strong>Username:</strong> {{ stream.streamer_username }}
            </div>
            <div class="info-row">
              <strong>Stream:</strong>
              <a
                v-if="stream[`${platform.toLowerCase()}_m3u8_url`]"
                :href="stream[`${platform.toLowerCase()}_m3u8_url`]"
                target="_blank"
                rel="noopener noreferrer"
                class="stream-link"
              >
                Open Stream
              </a>
              <span v-else>N/A</span>
            </div>
            <div class="agent-assignment">
              <div class="assignment-label">AGENT:</div>
              <div v-if="stream.assignments && stream.assignments.length > 0" class="assigned-agents">
                <div
                  v-for="(assignment, index) in stream.assignments"
                  :key="index"
                  class="agent-tag"
                >
                  <span class="agent-icon">👤</span>
                  {{ getAgentUsername(assignment.agent_id) }}
                </div>
              </div>
              <div v-else class="unassigned-badge">⚠️ UNASSIGNED</div>
            </div>
            <div class="action-buttons">
              <button
                class="manage-button"
                @click="$emit('manage-assignments', stream)"
                title="Manage Assignments"
              >
                Manage
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Table View Layout -->
      <div v-else class="responsive-table">
        <div class="table-header">
          <div class="th" @click="handleSort('id')">
            ID
            <span v-if="sortConfig.key === 'id'" class="sort-indicator">
              {{ sortConfig.direction === 'asc' ? '▲' : '▼' }}
            </span>
          </div>
          <div class="th" @click="handleSort('streamer_username')">
            Username
            <span v-if="sortConfig.key === 'streamer_username'" class="sort-indicator">
              {{ sortConfig.direction === 'asc' ? '▲' : '▼' }}
            </span>
          </div>
          <div class="th">Agent</div>
          <div class="th">Stream</div>
          <div class="th">Actions</div>
        </div>

        <div 
          v-for="stream in filteredStreams" 
          :key="stream.id"
          :class="['table-row', { 'new-stream-highlight': newStreamId === stream.id }]"
        >
          <div class="td" data-label="ID">{{ stream.id }}</div>
          <div class="td" data-label="Username">{{ stream.streamer_username }}</div>
          <div class="td" data-label="Agent">
            <div v-if="stream.assignments && stream.assignments.length > 0" class="assigned-agents">
              <div
                v-for="(assignment, index) in stream.assignments"
                :key="index"
                class="agent-tag"
              >
                <span class="agent-icon">👤</span>
                {{ getAgentUsername(assignment.agent_id) }}
              </div>
            </div>
            <div v-else class="unassigned-badge">⚠️ UNASSIGNED</div>
          </div>
          <div class="td" data-label="Stream">
            <a
              v-if="stream[`${platform.toLowerCase()}_m3u8_url`]"
              :href="stream[`${platform.toLowerCase()}_m3u8_url`]"
              target="_blank"
              rel="noopener noreferrer"
              class="stream-link"
            >
              Open Stream
            </a>
            <span v-else>N/A</span>
          </div>
          <div class="td" data-label="Actions">
            <div class="action-buttons">
              <button
                @click="confirmDelete(stream.id, stream.streamer_username)"
                class="delete-button"
                title="Delete stream"
                aria-label="Delete stream"
              >
                <span class="delete-icon">🗑️</span>
              </button>
              <button
                @click="$emit('manage-assignments', stream)"
                class="manage-button"
                title="Manage Assignments"
                aria-label="Manage Assignments"
              >
                Manage
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="table-footer">
        Showing {{ filteredStreams.length }} of {{ streams.length }} streams
      </div>
    </template>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="delete-modal-backdrop" @click="cancelDelete">
      <div class="delete-modal" @click.stop>
        <h3>Confirm Delete</h3>
        <p>Are you sure you want to delete the stream for <strong>{{ streamToDelete.username }}</strong>?</p>
        <div class="modal-actions">
          <button class="cancel-button" @click="cancelDelete">Cancel</button>
          <button class="confirm-delete-button" @click="executeDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';

export default {
  name: 'StreamTable',
  props: {
    streams: {
      type: Array,
      required: true
    },
    platform: {
      type: String,
      required: true
    },
    newStreamId: {
      type: Number,
      default: null
    },
    agents: {
      type: Array,
      required: true
    }
  },
  emits: ['delete', 'manage-assignments'],
  setup(props, { emit }) {
    const sortConfig = ref({ key: 'id', direction: 'asc' });
    const searchTerm = ref('');
    const showCardView = ref(window.innerWidth < 768);
    const isDarkMode = ref(window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    // Delete modal state
    const showDeleteModal = ref(false);
    const streamToDelete = ref({ id: null, username: '' });

    const handleResize = () => {
      showCardView.value = window.innerWidth < 768;
    };

    const handleThemeChange = (e) => {
      isDarkMode.value = e.matches;
    };

    onMounted(() => {
      window.addEventListener('resize', handleResize);
      const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      darkModeMediaQuery.addEventListener('change', handleThemeChange);
    });

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize);
      const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      darkModeMediaQuery.removeEventListener('change', handleThemeChange);
    });

    const handleSort = (key) => {
      sortConfig.value = {
        key,
        direction: sortConfig.value.key === key && sortConfig.value.direction === 'asc' ? 'desc' : 'asc'
      };
    };

    // Delete confirmation flow
    const confirmDelete = (id, username) => {
      streamToDelete.value = { id, username };
      showDeleteModal.value = true;
    };

    const cancelDelete = () => {
      showDeleteModal.value = false;
      streamToDelete.value = { id: null, username: '' };
    };

    const executeDelete = () => {
      emit('delete', streamToDelete.value.id);
      showDeleteModal.value = false;
      streamToDelete.value = { id: null, username: '' };
    };

    const sortedStreams = computed(() => {
      return [...props.streams].sort((a, b) => {
        if (a[sortConfig.value.key] < b[sortConfig.value.key]) {
          return sortConfig.value.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.value.key] > b[sortConfig.value.key]) {
          return sortConfig.value.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    });

    const filteredStreams = computed(() => {
      return sortedStreams.value.filter(stream =>
        Object.values(stream).some(value => {
          if (value === null || value === undefined) return false;
          return String(value).toLowerCase().includes(searchTerm.value.toLowerCase());
        })
      );
    });

    const getAgentUsername = (agentId) => {
      const agent = props.agents.find(a => a.id === agentId);
      return agent ? agent.username : 'Unknown';
    };

    // Clear highlight after 3 seconds
    watch(() => props.newStreamId, (newVal) => {
      if (newVal) {
        setTimeout(() => {
          // This assumes parent component will reset newStreamId to null
          // If not, you may need to implement that logic here
        }, 3000);
      }
    });

    return {
      sortConfig,
      searchTerm,
      showCardView,
      handleSort,
      filteredStreams,
      getAgentUsername,
      isDarkMode,
      showDeleteModal,
      streamToDelete,
      confirmDelete,
      cancelDelete,
      executeDelete
    };
  }
};
</script>

<style scoped>
.stream-table-container {
  width: 100%;
  max-width: 100%;
  position: relative;
}

/* Search and controls */
.search-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  gap: 1rem;
}

.search-wrapper {
  position: relative;
  flex-grow: 1;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
}

.search-input {
  width: 100%;
  padding: 8px 8px 8px 35px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.view-toggle {
  display: flex;
  gap: 8px;
}

.view-button {
  padding: 6px 10px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.view-button.active {
  background: #e0e0e0;
  border-color: #aaa;
}

.view-button .icon {
  font-size: 1.1rem;
}

/* Card View */
.stream-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.stream-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.stream-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.card-header {
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
  background: #f8f8f8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.card-content {
  padding: 15px;
}

.info-row {
  margin-bottom: 8px;
  display: flex;
  gap: 8px;
  align-items: baseline;
  flex-wrap: wrap;
}

/* Table View - No horizontal scrolling */
.responsive-table {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.table-header {
  display: grid;
  grid-template-columns: 0.5fr 1fr 1.5fr 1fr 0.8fr;
  padding: 10px 0;
  border-bottom: 2px solid #ddd;
  font-weight: bold;
}

.th {
  padding: 10px;
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.sort-indicator {
  font-size: 0.8rem;
}

.table-row {
  display: grid;
  grid-template-columns: 0.5fr 1fr 1.5fr 1fr 0.8fr;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s;
}

.table-row:hover {
  background-color: #f9f9f9;
}

.td {
  padding: 12px 10px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Common styles */
.agent-assignment {
  margin: 10px 0;
}

.assignment-label {
  font-weight: bold;
  margin-bottom: 5px;
  color: #555;
}

.assigned-agents {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 5px;
}

.agent-tag {
  background: #f0f7ff;
  padding: 3px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.9rem;
  border: 1px solid #d0e3ff;
}

.agent-icon {
  font-size: 0.9rem;
}

.unassigned-badge {
  display: inline-block;
  padding: 3px 8px;
  background: #fff0f0;
  color: #d00;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
  border: 1px solid #ffcbcb;
}

.stream-link {
  color: #2a78e4;
  text-decoration: none;
}

.stream-link:hover {
  text-decoration: underline;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.delete-button, .manage-button {
  padding: 6px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.delete-button {
  background-color: #fff0f0;
  color: #d00;
  border: 1px solid #ffcbcb;
}

.delete-button:hover {
  background-color: #ffe0e0;
}

.manage-button {
  background-color: #f0f7ff;
  color: #0066cc;
  border: 1px solid #d0e3ff;
}

.manage-button:hover {
  background-color: #e0f0ff;
}

.delete-icon {
  font-size: 1.1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #777;
}

.table-footer {
  padding: 12px 0;
  color: #777;
  font-size: 0.9rem;
  text-align: right;
}

/* New stream highlight animation */
.new-stream-highlight {
  animation: highlightPulse 3s ease-in-out;
}

@keyframes highlightPulse {
  0% { background-color: rgba(255, 255, 150, 0.1); }
  50% { background-color: rgba(255, 255, 150, 0.5); }
  100% { background-color: rgba(255, 255, 150, 0); }
}

/* Delete Modal */
.delete-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.delete-modal {
  background: var(--modal-bg, #fff);
  color: var(--modal-text, #333);
  border-radius: 8px;
  padding: 20px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.delete-modal h3 {
  margin-top: 0;
  border-bottom: 1px solid var(--modal-border, #eee);
  padding-bottom: 10px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.cancel-button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
}

.confirm-delete-button {
  padding: 8px 16px;
  background: #d00;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .search-input {
    background: #333;
    color: #eee;
    border-color: #555;
  }
  
  .view-button {
    background: #333;
    border-color: #555;
    color: #eee;
  }
  
  .view-button.active {
    background: #444;
    border-color: #666;
  }
  
  .stream-card, .table-row {
    background: #222;
    border-color: #444;
  }
  
  .card-header {
    background: #2a2a2a;
    border-color: #444;
  }
  
  .th, .table-header {
    border-color: #444;
  }
  
  .table-row:hover {
    background: #2a2a2a;
  }
  
  .agent-tag {
    background: #2a3b52;
    border-color: #405a7d;
    color: #eee;
  }
  
  .unassigned-badge {
    background: #3a2a2a;
    border-color: #5a3a3a;
    color: #ff9999;
  }
  
  .delete-button {
    background: #3a2a2a;
    border-color: #5a3a3a;
    color: #ff9999;
  }
  
  .manage-button {
    background: #2a3b52;
    border-color: #405a7d;
    color: #99ccff;
  }
  
  .delete-modal {
    --modal-bg: #222;
    --modal-text: #eee;
    --modal-border: #444;
  }
  
  .cancel-button {
    border-color: #555;
    color: #eee;
  }
  
  .stream-link {
    color: #6db0ff;
  }
}

/* Mobile responsive adjustments */
@media (max-width: 767px) {
  .table-header {
    display: none;
  }
  
  .table-row {
    display: flex;
    flex-direction: column;
    padding: 10px;
    margin-bottom: 15px;
    border: 1px solid #ddd;
    border-radius: 6px;
  }
  
  .td {
    padding: 8px 0;
    display: flex;
    width: 100%;
    border-bottom: 1px solid #eee;
  }
  
  .td:last-child {
    border-bottom: none;
  }
  
  .td:before {
    content: attr(data-label);
    font-weight: bold;
    width: 100px;
    min-width: 100px;
    padding-right: 10px;
  }
  
  .action-buttons {
    margin-top: 0;
    justify-content: flex-end;
  }
  
  .search-controls {
    flex-direction: column;
  }
  
  .view-toggle {
    align-self: flex-end;
  }
}

/* Prevent horizontal scrolling on all screen sizes */
* {
  max-width: 100%;
  box-sizing: border-box;
}
</style>