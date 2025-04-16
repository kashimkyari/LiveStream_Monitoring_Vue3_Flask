<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ isNew ? 'Add Stream' : 'Edit Stream' }}</h3>
        <button @click="$emit('close')" class="close-button" v-wave>
          <font-awesome-icon icon="times" />
        </button>
      </div>
      
      <div class="modal-body">
        <div class="form-group">
          <label>Room URL</label>
          <input 
            type="text" 
            v-model="streamData.room_url" 
            :disabled="!isNew"
            placeholder="https://chaturbate.com/username/"
          />
          <small v-if="!isNew" class="helper-text">Room URL cannot be changed after creation</small>
        </div>
        
        <div class="form-group" v-if="isNew">
          <label>Platform</label>
          <select v-model="streamData.platform">
            <option value="chaturbate">Chaturbate</option>
            <option value="stripchat">Stripchat</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Assigned Agents</label>
          <div class="agent-selection">
            <div 
              v-for="agent in agents" 
              :key="agent.id" 
              class="agent-option"
              :class="{ selected: isAgentSelected(agent.id) }"
              @click="toggleAgent(agent.id)"
            >
              <div class="agent-avatar">{{ agent.username.charAt(0).toUpperCase() }}</div>
              <div class="agent-name">{{ agent.username }}</div>
              <font-awesome-icon 
                :icon="isAgentSelected(agent.id) ? 'check-circle' : 'circle'" 
                class="selection-icon" 
              />
            </div>
            
            <div v-if="agents.length === 0" class="no-agents">
              No agents available
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="$emit('close')" class="cancel-button" v-wave>
          Cancel
        </button>
        <button @click="saveStream" class="submit-button" v-wave :disabled="isLoading">
          <span v-if="isLoading">
            <font-awesome-icon icon="spinner" spin />
          </span>
          <span v-else>
            {{ isNew ? 'Create Stream' : 'Save Changes' }}
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'StreamEditorModal',
  props: {
    stream: {
      type: Object,
      default: () => null
    },
    agents: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      isLoading: false,
      streamData: {
        room_url: '',
        platform: 'chaturbate',
        agent_ids: []
      }
    }
  },
  computed: {
    isNew() {
      return !this.stream;
    }
  },
  watch: {
    stream: {
      immediate: true,
      handler(newStream) {
        if (newStream) {
          this.streamData = {
            id: newStream.id,
            room_url: newStream.room_url,
            platform: newStream.platform?.toLowerCase() || 'chaturbate',
            agent_ids: this.getAgentIdsFromStream(newStream)
          };
        } else {
          this.streamData = {
            room_url: '',
            platform: 'chaturbate',
            agent_ids: []
          };
        }
      }
    }
  },
  methods: {
    getAgentIdsFromStream(stream) {
      if (!stream.assignments || !Array.isArray(stream.assignments)) {
        return [];
      }
      return stream.assignments.map(assignment => assignment.agent_id);
    },
    
    isAgentSelected(agentId) {
      return this.streamData.agent_ids.includes(agentId);
    },
    
    toggleAgent(agentId) {
      if (this.isAgentSelected(agentId)) {
        this.streamData.agent_ids = this.streamData.agent_ids.filter(id => id !== agentId);
      } else {
        this.streamData.agent_ids.push(agentId);
      }
    },
    
   async saveStream() {
  this.isLoading = true;
  
  try {
    let response;
    
    if (this.isNew) {
      // Create new stream
      response = await axios.post('/api/streams/interactive', this.streamData);
      this.$emit('created', response.data);
    } else {
      // Update existing stream - only pass agent_ids without refresh flag
      // when we're only updating assignments
      response = await axios.put(`/api/streams/${this.streamData.id}`, {
        agent_ids: this.streamData.agent_ids
      });
      this.$emit('updated', response.data.stream);
    }
    
    this.$emit('close');
  } catch (error) {
    console.error('Error saving stream:', error);
    alert('Failed to save stream. Please try again.');
  } finally {
    this.isLoading = false;
  }
}
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  background-color: var(--input-bg);
  border-radius: 12px;
  width: 600px;
  max-width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  border: 1px solid var(--input-border);
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid var(--input-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: var(--text-muted);
  transition: all 0.2s ease;
}

.close-button:hover {
  color: var(--text-color);
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-color);
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 1rem;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.2);
}

.helper-text {
  display: block;
  margin-top: 5px;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.agent-selection {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--input-border);
  border-radius: 8px;
}

.agent-option {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid var(--input-border);
}

.agent-option:last-child {
  border-bottom: none;
}

.agent-option:hover {
  background-color: var(--hover-bg);
}

.agent-option.selected {
  background-color: rgba(var(--primary-rgb), 0.1);
}

.agent-avatar {
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
  margin-right: 12px;
}

.agent-name {
  flex: 1;
  font-weight: 500;
}

.selection-icon {
  color: var(--primary-color);
  font-size: 1.2rem;
}

.no-agents {
  padding: 20px;
  text-align: center;
  color: var(--text-muted);
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--input-border);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-button {
  background-color: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--input-border);
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
}

.cancel-button:hover {
  background-color: var(--input-bg);
}

.submit-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.2s ease;
  font-weight: 500;
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit-button:not(:disabled):hover {
  opacity: 0.9;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Responsive styles */
@media (max-width: 768px) {
  .modal-content {
    width: 100%;
    max-height: 85vh;
  }
}

@media (max-width: 576px) {
  .modal-header h3 {
    font-size: 1.3rem;
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .cancel-button,
  .submit-button {
    width: 100%;
  }
}
</style>