<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <button class="modal-close" @click="$emit('close')" v-wave>
        <font-awesome-icon icon="times" />
      </button>
      <div class="modal-header">
        <h3>Add New Agent</h3>
      </div>
      <div class="modal-body">
        <form @submit.prevent="submitForm">
          <div class="form-row">
            <div class="form-group">
              <label for="username">Username</label>
              <input id="username" v-model="form.username" required />
            </div>
            <div class="form-group">
              <label for="password">Password</label>
              <input id="password" v-model="form.password" type="password" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="firstname">First Name</label>
              <input id="firstname" v-model="form.firstname" required />
            </div>
            <div class="form-group">
              <label for="lastname">Last Name</label>
              <input id="lastname" v-model="form.lastname" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="email">Email</label>
              <input id="email" v-model="form.email" type="email" required />
            </div>
            <div class="form-group">
              <label for="phonenumber">Phone Number</label>
              <input id="phonenumber" v-model="form.phonenumber" type="tel" required />
            </div>
          </div>
          <div class="form-actions">
            <button type="button" @click="$emit('close')" class="cancel-button" v-wave>
              Cancel
            </button>
            <button type="submit" class="submit-button" v-wave>
              Create Agent
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'CreateAgentModal',
  emits: ['close', 'submit'],
  setup(props, { emit }) {
    const form = ref({
      username: '',
      password: '',
      firstname: '',
      lastname: '',
      email: '',
      phonenumber: ''
    })
    
    const submitForm = () => {
      emit('submit', form.value)
      form.value = {
        username: '',
        password: '',
        firstname: '',
        lastname: '',
        email: '',
        phonenumber: ''
      }
    }
    
    return {
      form,
      submitForm
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
  border-radius: 10px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
  position: relative;
}

.modal-close {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.modal-close:hover {
  opacity: 1;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid var(--input-border);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
}

.modal-body {
  padding: 20px;
}

.form-row {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.form-row .form-group {
  flex: 1;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 0.9rem;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--input-border);
  border-radius: 5px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 0.9rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
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

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Responsive styles */
@media (max-width: 768px) {
  .form-row {
    flex-direction: column;
    gap: 0;
  }
}

@media (max-width: 576px) {
  .form-actions {
    flex-direction: column;
  }
  
  .cancel-button,
  .submit-button {
    width: 100%;
  }
}
</style>