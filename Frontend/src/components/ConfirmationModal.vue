<template>
  <div class="modal-overlay" ref="modalOverlay" @click.self="closeModal">
    <div class="modal-content small" ref="modalContent">
      <div class="modal-header">
        <h3>{{ title }}</h3>
      </div>
      <div class="modal-body">
        <p>{{ message }}</p>
      </div>
      <div class="modal-footer" v-if="!isLoading">
        <button @click="closeModal" class="cancel-button" v-wave>
          Cancel
        </button>
        <button @click="confirmAction" class="submit-button danger" v-wave>
          {{ actionText }}
        </button>
      </div>
      <div v-else class="loading-spinner" ref="spinner"></div>
    </div>
  </div>
</template>

<script>
import anime from 'animejs';

export default {
  name: 'ConfirmationModal',
  props: {
    title: String,
    message: String,
    actionText: String
  },
  emits: ['close', 'confirm'],
  data() {
    return {
      isLoading: false
    };
  },
  mounted() {
    this.animateModalOpen();
  },
  watch: {
    isLoading(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          this.animateSpinner();
        });
      }
    }
  },
  methods: {
    animateModalOpen() {
      anime({
        targets: this.$refs.modalOverlay,
        opacity: [0, 1],
        duration: 400,
        easing: 'easeOutQuad'
      });
      
      anime({
        targets: this.$refs.modalContent,
        opacity: [0, 1],
        scale: [0.9, 1],
        duration: 500,
        easing: 'easeOutElastic(1, 0.6)'
      });
    },
    closeModal() {
      if (this.isLoading) return;
      
      anime({
        targets: this.$refs.modalContent,
        opacity: 0,
        scale: 0.9,
        duration: 300,
        easing: 'easeInQuad',
        complete: () => {
          anime({
            targets: this.$refs.modalOverlay,
            opacity: 0,
            duration: 300,
            easing: 'easeInQuad',
            complete: () => {
              this.$emit('close');
            }
          });
        }
      });
    },
    confirmAction() {
      if (this.isLoading) return;
      this.isLoading = true;
      
      anime({
        targets: this.$refs.modalContent,
        scale: [1, 0.95, 1],
        duration: 300,
        easing: 'easeInOutQuad',
        complete: () => {
          this.$emit('confirm');
        }
      });
    },
    finishLoading() {
      this.isLoading = false;
      this.closeModal();
    },
    animateSpinner() {
      anime({
        targets: this.$refs.spinner,
        rotate: '360deg',
        duration: 1000,
        easing: 'linear',
        loop: true
      });
    }
  }
}
</script>

<style scoped>
.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--input-border);
  display: flex;
  justify-content: center;
  gap: 15px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid transparent;
  border-top-color: var(--primary-color);
  border-radius: 50%;
  margin: 20px auto;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

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
  opacity: 0; /* Start invisible for animation */
}

.modal-content.small {
  max-width: 500px;
  width: 100%;
  background-color: var(--bg-color);
  border-radius: 12px;
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  opacity: 0; /* Start invisible for animation */
  transform-origin: center;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid var(--input-border);
  text-align: center;
  position: relative;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
  background: linear-gradient(45deg, var(--primary-color), #6c5ce7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
}

.modal-body {
  padding: 25px 20px;
  text-align: center;
}

.modal-body p {
  margin: 0;
  font-size: 1rem;
  line-height: 1.6;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--input-border);
  display: flex;
  justify-content: center;
  gap: 15px;
}

.cancel-button {
  background-color: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--input-border);
  padding: 10px 18px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
  min-width: 100px;
}

.cancel-button:hover {
  background-color: var(--input-bg);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.submit-button.danger {
  background: linear-gradient(45deg, #dc3545, #ff5a67);
}

.submit-button {
  background: linear-gradient(45deg, var(--primary-color), #6c5ce7);
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
  min-width: 100px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
}

.submit-button:active, .cancel-button:active {
  transform: translateY(1px);
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