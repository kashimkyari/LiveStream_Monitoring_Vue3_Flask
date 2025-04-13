<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <h3 class="modal-title">Edit Agent</h3>
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
            placeholder="New Password (optional)"
            v-model="form.password"
            class="form-input"
          />
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <button class="submit-button" @click="handleSave">Save Changes</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue';

export default {
  name: 'EditAgentModal',
  props: {
    agent: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const form = reactive({
      username: props.agent.username,
      password: ''
    });
    const error = ref('');

    const handleSave = async () => {
      error.value = '';
      if (!form.username.trim()) {
        error.value = 'Username is required.';
        return;
      }
      const payload = { username: form.username.trim() };
      if (form.password.trim()) {
        payload.password = form.password.trim();
      }
      try {
        await emit('save', props.agent.id, payload);
        emit('close');
      } catch (err) {
        error.value = err.response?.data?.message || 'Failed to update agent.';
      }
    };

    return {
      form,
      error,
      handleSave
    };
  }
};
</script>