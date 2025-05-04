<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content" ref="modalContent">
      <button class="modal-close" @click="$emit('close')" v-wave>
        <font-awesome-icon icon="times" />
      </button>
      <div class="modal-header">
        <h3>{{ isEditing ? 'Edit Agent' : 'Add New Agent' }}</h3>
      </div>
      <div class="modal-body">
        <form @submit.prevent="submitForm">
          <div class="form-group" ref="usernameGroup">
            <label for="username">Username</label>
            <input id="username" v-model="form.username" required />
          </div>
          
          <div class="form-group" ref="emailGroup">
            <label for="email">Email</label>
            <input id="email" v-model="form.email" type="email" required />
          </div>
          
          <div class="form-group" ref="passwordGroup" v-if="!isEditing">
            <label for="password">Password</label>
            <input id="password" v-model="form.password" type="password" required />
          </div>
          
          <div class="form-group" ref="receiveUpdatesGroup" v-if="!isEditing">
            <label for="receiveUpdates">Receive Updates</label>
            <input id="receiveUpdates" v-model="form.receiveUpdates" type="checkbox" />
          </div>
          
          <div class="form-actions">
            <button type="button" @click="$emit('close')" class="cancel-button" v-wave>
              Cancel
            </button>
            <button type="submit" class="submit-button" v-wave ref="submitButton">
              {{ isEditing ? 'Update Agent' : 'Create Agent' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import anime from 'animejs/lib/anime.es.js'

export default {
  name: 'CreateAgentModal',
  props: {
    isEditing: {
      type: Boolean,
      default: false
    },
    agent: {
      type: Object,
      default: null
    }
  },
  emits: ['close', 'submit'],
  setup(props, { emit }) {
    const form = ref({
      username: props.agent ? props.agent.username : '',
      email: props.agent ? props.agent.email : '',
      password: '',
      receiveUpdates: props.agent ? props.agent.receiveUpdates : false
    })
    
    const modalContent = ref(null)
    const usernameGroup = ref(null)
    const emailGroup = ref(null)
    const passwordGroup = ref(null)
    const receiveUpdatesGroup = ref(null)
    const submitButton = ref(null)
    
    onMounted(() => {
      // Animate modal appearance
      if (modalContent.value) {
        anime({
          targets: modalContent.value,
          scale: [0.9, 1],
          opacity: [0, 1],
          duration: 400,
          easing: 'easeOutElastic(1, .8)'
        })
      }
      
      // Staggered animation for form elements
      const targets = [
        usernameGroup.value,
        emailGroup.value,
        passwordGroup.value,
        receiveUpdatesGroup.value,
        submitButton.value
      ].filter(el => el); // Filter out null/undefined elements
      
      if (targets.length > 0) {
        anime({
          targets: targets,
          translateY: [20, 0],
          opacity: [0, 1],
          delay: anime.stagger(100, {start: 300}),
          duration: 500,
          easing: 'easeOutQuad'
        })
      }
    })
    
    const submitForm = () => {
      // Animation for button press
      anime({
        targets: submitButton.value,
        scale: [1, 0.95, 1],
        duration: 300,
        easing: 'easeInOutQuad',
        complete: () => {
          // Success animation
          anime({
            targets: modalContent.value,
            translateY: [0, -20],
            opacity: [1, 0],
            duration: 300,
            easing: 'easeOutQuad',
            complete: () => {
              emit('submit', form.value)
              form.value = {
                username: '',
                email: '',
                password: '',
                receiveUpdates: false
              }
            }
          })
        }
      })
    }
    
    return {
      form,
      submitForm,
      modalContent,
      usernameGroup,
      emailGroup,
      passwordGroup,
      receiveUpdatesGroup,
      submitButton
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
  max-width: 450px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  position: relative;
  opacity: 0; /* Initial state for anime.js */
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
  z-index: 2;
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
  background: linear-gradient(45deg, var(--primary-color), #8a6eff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-align: center;
}

.modal-body {
  padding: 25px;
}

.form-group {
  margin-bottom: 20px;
  opacity: 0; /* Initial state for anime.js */
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-color);
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--input-border);
  border-radius: 8px;
  background-color: var(--input-bg);
  color: var(--text-color);
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.form-group input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
  outline: none;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  gap: 15px;
  margin-top: 30px;
}

.cancel-button {
  flex: 1;
  background-color: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--input-border);
  padding: 10px 15px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.cancel-button:hover {
  background-color: var(--input-bg);
  transform: translateY(-2px);
}

.submit-button {
  flex: 1;
  background: linear-gradient(45deg, var(--primary-color), #8a6eff);
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  opacity: 0; /* Initial state for anime.js */
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* Responsive styles */
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