<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content small">
      <div class="modal-header">
        <h3>{{ title }}</h3>
      </div>
      <div class="modal-body">
        <p>{{ message }}</p>
      </div>
      <div class="modal-footer">
        <button @click="$emit('close')" class="cancel-button" v-wave>
          Cancel
        </button>
        <button @click="$emit('confirm')" class="submit-button danger" v-wave>
          {{ actionText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConfirmationModal',
  props: {
    title: String,
    message: String,
    actionText: String
  },
  emits: ['close', 'confirm']
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

.modal-content.small {
  max-width: 500px;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid var(--input-border);
  text-align: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.modal-body {
  padding: 20px;
  text-align: center;
}

.modal-body p {
  margin: 0;
  font-size: 1rem;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--input-border);
  display: flex;
  justify-content: center;
  gap: 10px;
}

.cancel-button {
  background-color: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--input-border);
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-button:hover {
  background-color: var(--input-bg);
}

.submit-button.danger {
  background-color: #dc3545;
}

.submit-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.submit-button:hover {
  opacity: 0.9;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Responsive styles */
@media (max-width: 576px) {
  .modal-footer {
    flex-direction: column;
  }
  
  .cancel-button,
  .submit-button {
    width: 100%;
  }
}
</style>