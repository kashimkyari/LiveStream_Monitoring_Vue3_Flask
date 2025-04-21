<template>
  <div class="mobile-modal-overlay" @click.self="$emit('close')">
    <div class="mobile-modal-content">
      <div class="mobile-modal-header">
        <h3>Agent Details</h3>
        <button class="mobile-modal-close" @click="$emit('close')">
          <font-awesome-icon icon="times" />
        </button>
      </div>
      
      <div class="mobile-modal-body">
        <!-- Agent Info Section -->
        <div class="agent-info">
          <div class="agent-status" :class="{ online: agent.online }"></div>
          <div class="agent-username">{{ agent.username }}</div>
          <div class="agent-details">
            <div class="detail-item">
              <span class="detail-label">Email:</span>
              <span class="detail-value">{{ agent.email || 'Not provided' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Role:</span>
              <span class="detail-value">{{ agent.role || 'agent' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Last Active:</span>
              <span class="detail-value">{{ formatDate(agent.last_active) }}</span>
            </div>
          </div>
        </div>
        
        <!-- Assignments Section -->
        <div class="assignments-section">
          <h4>Assigned Streams</h4>
          <div v-if="!agent.assignments || agent.assignments.length === 0" class="empty-assignments">
            No streams assigned to this agent
          </div>
          <div v-else class="assignments-list">
            <div 
              v-for="assignment in agent.assignments" 
              :key="assignment.id" 
              class="assignment-item"
            >
              <div class="assignment-stream">
                {{ getStreamName(assignment.stream) }}
              </div>
              <div class="assignment-platform">
                {{ getPlatform(assignment.stream) }}
              </div>
              <button 
                class="assignment-remove" 
                @click="confirmRemoveAssignment(assignment)"
                :disabled="isSubmitting"
              >
                <font-awesome-icon icon="unlink" />
              </button>
            </div>
          </div>
        </div>
        
        <!-- Error/Success Messages -->
        <div v-if="error" class="error-message">
          <font-awesome-icon icon="exclamation-circle" class="error-icon" />
          <span>{{ error }}</span>
        </div>
        
        <div v-if="message" class="success-message">
          <font-awesome-icon icon="check-circle" class="success-icon" />
          <span>{{ message }}</span>
        </div>
        
        <!-- Action Buttons -->
        <div class="agent-actions">
          <button 
            class="edit-button" 
            @click="editAgent(agent)"
            :disabled="isSubmitting"
          >
            <font-awesome-icon icon="edit" />
            <span>Edit Agent</span>
          </button>
          
          <button 
            class="delete-button" 
            @click="confirmDeleteAgent(agent)"
            :disabled="isSubmitting"
          >
            <font-awesome-icon icon="trash-alt" />
            <span>Delete Agent</span>
          </button>
        </div>
        
        <!-- Confirmation Dialog -->
        <div v-if="showConfirmation" class="confirmation-dialog">
          <div class="confirmation-content">
            <font-awesome-icon icon="exclamation-triangle" class="warning-icon" />
            <h4>{{ confirmationTitle }}</h4>
            <p>{{ confirmationMessage }}</p>
            <div class="confirmation-actions">
              <button class="cancel-action" @click="cancelConfirmation">Cancel</button>
              <button class="confirm-action" @click="confirmAction">Confirm</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useToast } from 'vue-toastification';
import { format } from 'date-fns';
import MobileStreamService from '../services/MobileStreamService';

export default {
  name: 'MobileAgentDetailsModal',
  
  props: {
    agent: {
      type: Object,
      required: true
    }
  },
  
  emits: ['close', 'agent-updated', 'agent-deleted'],
  
  setup(props, { emit }) {
    const toast = useToast();
    
    // State
    const error = ref('');
    const message = ref('');
    const isSubmitting = ref(false);
    const showConfirmation = ref(false);
    const confirmationTitle = ref('');
    const confirmationMessage = ref('');
    const pendingAction = ref(null);
    const pendingData = ref(null);
    
    // Format date helper
    const formatDate = (dateString) => {
      if (!dateString) return 'Never';
      try {
        return format(new Date(dateString), 'MMM d, yyyy h:mm a');
      } catch (e) {
        return dateString;
      }
    };
    
    // Get stream name helper
    const getStreamName = (stream) => {
      if (!stream) return 'Unknown Stream';
      return stream.streamer_username || 'Unnamed Stream';
    };
    
    // Get platform helper
    const getPlatform = (stream) => {
      if (!stream) return '';
      const platform = stream.platform || stream.type || '';
      return platform.charAt(0).toUpperCase() + platform.slice(1).toLowerCase();
    };
    
    // Edit agent handler
    const editAgent = () => {
      // Placeholder for agent editing - could be implemented in a separate modal
      toast.info('Edit agent functionality would be implemented here');
    };
    
    // Confirmation for deleting an agent
    const confirmDeleteAgent = (agent) => {
      confirmationTitle.value = 'Delete Agent';
      confirmationMessage.value = `Are you sure you want to delete agent "${agent.username}"? This action cannot be undone.`;
      pendingAction.value = deleteAgent;
      pendingData.value = agent;
      showConfirmation.value = true;
    };
    
    // Delete agent handler
    const deleteAgent = async (agent) => {
      try {
        isSubmitting.value = true;
        error.value = '';
        message.value = '';
        
        // Add mobile optimization parameter
        await MobileStreamService.getOptimizedRequest(`/api/agents/${agent.id}`, { _method: 'DELETE' });
        
        toast.success('Agent deleted successfully');
        emit('agent-deleted', agent.id);
        emit('close');
      } catch (err) {
        console.error('Error deleting agent:', err);
        error.value = err.response?.data?.message || 'Failed to delete agent';
        toast.error('Failed to delete agent');
      } finally {
        isSubmitting.value = false;
      }
    };
    
    // Confirmation for removing an assignment
    const confirmRemoveAssignment = (assignment) => {
      confirmationTitle.value = 'Remove Assignment';
      confirmationMessage.value = `Are you sure you want to remove the assignment to "${getStreamName(assignment.stream)}"?`;
      pendingAction.value = removeAssignment;
      pendingData.value = assignment;
      showConfirmation.value = true;
    };
    
    // Remove assignment handler
    const removeAssignment = async (assignment) => {
      try {
        isSubmitting.value = true;
        error.value = '';
        message.value = '';
        
        // Delete assignment with mobile optimization
        await MobileStreamService.deleteAssignment(assignment.id, props.agent.id);
        
        toast.success('Assignment removed');
        message.value = 'Assignment removed successfully';
        
        // Create a copy of the assignments to avoid direct prop mutation
        const updatedAssignments = [...props.agent.assignments];
        const index = updatedAssignments.findIndex(a => a.id === assignment.id);
        if (index !== -1) {
          updatedAssignments.splice(index, 1);
        }
        
        // Create a new agent object with the updated assignments
        const updatedAgent = {
          ...props.agent,
          assignments: updatedAssignments
        };
        
        emit('agent-updated', updatedAgent);
      } catch (err) {
        console.error('Error removing assignment:', err);
        error.value = err.response?.data?.message || 'Failed to remove assignment';
        toast.error('Failed to remove assignment');
      } finally {
        isSubmitting.value = false;
      }
    };
    
    // Confirmation dialog handlers
    const confirmAction = () => {
      if (pendingAction.value && pendingData.value) {
        pendingAction.value(pendingData.value);
      }
      cancelConfirmation();
    };
    
    const cancelConfirmation = () => {
      showConfirmation.value = false;
      pendingAction.value = null;
      pendingData.value = null;
    };
    
    return {
      error,
      message,
      isSubmitting,
      showConfirmation,
      confirmationTitle,
      confirmationMessage,
      formatDate,
      getStreamName,
      getPlatform,
      editAgent,
      confirmDeleteAgent,
      confirmRemoveAssignment,
      confirmAction,
      cancelConfirmation
    };
  }
};
</script>

<style scoped>
.mobile-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 0 16px;
}

.mobile-modal-content {
  background-color: var(--card-bg);
  border-radius: 12px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.mobile-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.mobile-modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--text-color);
}

.mobile-modal-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 1.2rem;
  padding: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mobile-modal-body {
  padding: 16px;
}

.agent-info {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  position: relative;
}

.agent-status {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #ccc;
  position: absolute;
  top: 20px;
  right: 16px;
}

.agent-status.online {
  background-color: #4caf50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.agent-username {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-color);
}

.agent-details {
  color: var(--text-muted);
}

.detail-item {
  margin-bottom: 8px;
  display: flex;
  flex-wrap: wrap;
}

.detail-label {
  font-weight: 500;
  min-width: 100px;
}

.assignments-section {
  margin-bottom: 20px;
}

.assignments-section h4 {
  font-size: 1.1rem;
  margin-bottom: 12px;
  color: var(--text-color);
}

.empty-assignments {
  color: var(--text-muted);
  font-style: italic;
  padding: 12px;
  text-align: center;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
}

.assignments-list {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.assignment-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
}

.assignment-item:last-child {
  border-bottom: none;
}

.assignment-stream {
  flex: 1;
  font-weight: 500;
  color: var(--text-color);
}

.assignment-platform {
  color: var(--text-muted);
  margin-right: 12px;
  font-size: 0.85rem;
  background-color: var(--muted-bg);
  padding: 2px 8px;
  border-radius: 12px;
}

.assignment-remove {
  background: transparent;
  border: none;
  color: var(--danger-color, #f44336);
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
}

.assignment-remove:hover {
  background-color: rgba(244, 67, 54, 0.1);
}

.error-message {
  padding: 12px;
  background-color: rgba(244, 67, 54, 0.1);
  border-left: 3px solid #f44336;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f44336;
}

.error-icon {
  color: #f44336;
}

.success-message {
  padding: 12px;
  background-color: rgba(76, 175, 80, 0.1);
  border-left: 3px solid #4caf50;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #4caf50;
}

.success-icon {
  color: #4caf50;
}

.agent-actions {
  display: flex;
  gap: 12px;
}

.edit-button,
.delete-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.edit-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
}

.delete-button {
  background-color: transparent;
  color: var(--danger-color, #f44336);
  border: 1px solid var(--danger-color, #f44336);
}

/* Confirmation Dialog */
.confirmation-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1010;
  padding: 0 16px;
}

.confirmation-content {
  background-color: var(--card-bg);
  border-radius: 12px;
  width: 100%;
  max-width: 360px;
  padding: 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.warning-icon {
  font-size: 2rem;
  color: #ff9800;
  margin-bottom: 16px;
}

.confirmation-content h4 {
  margin: 0 0 8px 0;
  color: var(--text-color);
}

.confirmation-content p {
  margin: 0 0 24px 0;
  color: var(--text-muted);
  font-size: 0.95rem;
}

.confirmation-actions {
  display: flex;
  gap: 12px;
  width: 100%;
}

.cancel-action,
.confirm-action {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.cancel-action {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-color);
}

.confirm-action {
  background-color: var(--danger-color, #f44336);
  border: none;
  color: white;
}

/* Improve touch targets for mobile */
@media (max-width: 480px) {
  .edit-button,
  .delete-button,
  .cancel-action,
  .confirm-action {
    padding: 14px;
  }
  
  .assignment-remove {
    padding: 10px;
  }
}
</style>