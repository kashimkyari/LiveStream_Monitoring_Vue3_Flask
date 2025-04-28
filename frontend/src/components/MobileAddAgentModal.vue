<template>
  <div class="mobile-modal-overlay" @click.self="$emit('close')">
    <div class="mobile-modal-content">
      <div class="mobile-modal-header">
        <h3>Add Agent</h3>
        <button class="mobile-modal-close" @click="$emit('close')">
          <font-awesome-icon icon="times" />
        </button>
      </div>
      
      <div class="mobile-modal-body">
        <div class="form-group">
          <label for="agent-username">Username</label>
          <input
            id="agent-username"
            type="text"
            placeholder="Enter username"
            v-model="form.username"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label for="agent-password">Password</label>
          <input
            id="agent-password"
            type="password"
            placeholder="Enter password"
            v-model="form.password"
            class="form-input"
          />
        </div>
        
        <div class="form-group">
          <label for="agent-email">Email</label>
          <input
            id="agent-email"
            type="email"
            placeholder="Enter email address"
            v-model="form.email"
            class="form-input"
          />
        </div>
        
        <div v-if="error" class="error-message">
          <font-awesome-icon icon="exclamation-circle" class="error-icon" />
          <span>{{ error }}</span>
        </div>
        
        <div v-if="message" class="success-message">
          <font-awesome-icon icon="check-circle" class="success-icon" />
          <span>{{ message }}</span>
        </div>
        
        <div class="form-actions">
          <button type="button" @click="$emit('close')" class="cancel-button">
            Cancel
          </button>
          <button 
            type="button" 
            @click="handleCreate" 
            class="submit-button"
            :disabled="isSubmitting || !isFormValid"
          >
            <font-awesome-icon icon="spinner" class="fa-spin" v-if="isSubmitting" />
            <span v-else>Create Agent</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed } from 'vue';
import { useToast } from 'vue-toastification';
import MobileStreamService from '../services/MobileStreamService';

export default {
  name: 'MobileAddAgentModal',
  emits: ['close', 'agent-created'],
  
  setup(props, { emit }) {
    const toast = useToast();
    const form = reactive({ 
      username: '', 
      password: '',
      email: ''
    });
    
    const error = ref('');
    const message = ref('');
    const isSubmitting = ref(false);
    
    // Form validation
    const isFormValid = computed(() => {
      return form.username.trim() && 
             form.password.trim() && 
             form.email.trim() && 
             /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email); // Simple email validation
    });
    
    const handleCreate = async () => {
      // Reset states
      error.value = '';
      message.value = '';
      
      // Validate form
      if (!form.username.trim()) {
        error.value = 'Username is required';
        return;
      }
      
      if (!form.password.trim()) {
        error.value = 'Password is required';
        return;
      }
      
      if (!form.email.trim()) {
        error.value = 'Email is required';
        return;
      }
      
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
        error.value = 'Please enter a valid email address';
        return;
      }
      
      // Prepare payload
      const payload = {
        username: form.username.trim(),
        password: form.password.trim(),
        email: form.email.trim(),
        role: 'agent' // Default role
      };
      
      try {
        isSubmitting.value = true;
        
        // Mobile-optimized request
        const optimizedPayload = {
          ...payload,
          mobile_view: true // Add mobile flag for potential backend optimization
        };
        
        // Create agent
        await MobileStreamService.getOptimizedRequest('/api/agents', optimizedPayload);
        
        // Handle success
        message.value = 'Agent created successfully';
        toast.success('Agent created');
        
        // Emit success event
        emit('agent-created');
        
        // Auto-close modal after delay
        setTimeout(() => {
          emit('close');
        }, 1500);
      } catch (err) {
        console.error('Error creating agent:', err);
        error.value = err.response?.data?.message || 'Failed to create agent';
        toast.error('Failed to create agent');
      } finally {
        isSubmitting.value = false;
      }
    };
    
    return {
      form,
      error,
      message,
      isSubmitting,
      isFormValid,
      handleCreate
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

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-color);
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 1rem;
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

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-button, 
.submit-button {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-button {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-color);
}

.submit-button {
  background-color: var(--primary-color);
  border: none;
  color: #fff;
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Improve touch targets for mobile */
@media (max-width: 480px) {
  .cancel-button,
  .submit-button {
    padding: 14px;
  }
}
</style>