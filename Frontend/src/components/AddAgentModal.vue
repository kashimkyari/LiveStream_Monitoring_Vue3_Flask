<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <h3 class="modal-title">Add Agent</h3>
      <button class="close-button" @click="$emit('close')">×</button>
      <div class="agent-form">
        <div class="form-group">
          <input
            type="text"
            placeholder="Username"
            v-model="form.username"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <input
            type="password"
            placeholder="Password"
            v-model="form.password"
            class="form-input"
          />
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <div v-if="message" class="success-message">{{ message }}</div>
        <button class="submit-button" @click="handleCreate">Create Agent</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue';
import axios from 'axios';

export default {
  name: 'AddAgentModal',
  emits: ['close', 'agent-created'],
  setup(props, { emit }) {
    const form = reactive({ username: '', password: '' });
    const error = ref('');
    const message = ref('');

    const handleCreate = async () => {
      error.value = '';
      message.value = '';
      if (!form.username.trim() || !form.password.trim()) {
        error.value = 'Both username and password are required.';
        return;
      }
      const payload = {
        username: form.username.trim(),
        password: form.password.trim()
      };
      try {
        const res = await axios.post('/api/agents', payload);
        message.value = res.data.message || 'Agent created successfully';
        emit('agent-created'); // Refresh agents list
        setTimeout(() => {
          emit('close');
        }, 1500);
      } catch (err) {
        error.value = err.response?.data?.message || 'Error creating agent.';
      }
    };

    return {
      form,
      error,
      message,
      handleCreate
    };
  }
};
</script>