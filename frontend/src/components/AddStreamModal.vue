<template>
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-container">
        <div class="modal-header">
          <h2 class="modal-title">Add New Stream</h2>
          <button @click="$emit('close')" class="close-button">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <div class="modal-body">
          <AddStreamForm 
            :refresh-streams="refreshStreams" 
            :refresh-agents="refreshAgents"
            :on-add-stream="handleStreamAdded"
            :on-stream-added="onStreamAdded"
          />
        </div>
      </div>
    </div>
  </template>
  
  <script>
  // Comment out the import for the non-existent component
  // import AddStreamForm from './AddStreamForm.vue';
  import { defineComponent } from 'vue';
  import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
  import { library } from '@fortawesome/fontawesome-svg-core';
  import { faTimes } from '@fortawesome/free-solid-svg-icons';
  
  library.add(faTimes);
  
  export default defineComponent({
    name: 'AddStreamModal',
    components: {
      // AddStreamForm,
      FontAwesomeIcon
    },
    props: {
      refreshStreams: {
        type: Function,
        default: () => {}
      },
      refreshAgents: {
        type: Function,
        default: () => {}
      },
      onStreamAdded: {
        type: Function,
        default: () => {}
      }
    },
    setup(props, { emit }) {
      const handleStreamAdded = (newStream) => {
        emit('close');
        if (props.onAddStream) {
          props.onAddStream(newStream);
        }
      };
  
      return {
        handleStreamAdded
      };
    },
    emits: ['close', 'add-stream']
  });
  </script>
  
  <style scoped>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999;
  }
  
  .modal-container {
    background-color: var(--card-bg);
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    width: 90%;
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--card-border);
  }
  
  .modal-title {
    margin: 0;
    font-size: 1.25rem;
    color: var(--text-color);
  }
  
  .close-button {
    background: transparent;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: var(--text-color);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
    border-radius: 50%;
    transition: background-color 0.3s;
  }
  
  .close-button:hover {
    background-color: var(--hover-bg);
  }
  
  .modal-body {
    padding: 1.5rem;
  }
  
  /* Make sure the form container in modal doesn't have shadow or margin */
  :deep(.form-container) {
    box-shadow: none;
    margin-bottom: 0;
    padding: 0;
  }
  
  :deep(.form-header) {
    display: none; /* Hide the form title since we have it in the modal header */
  }
  
  @media (max-width: 768px) {
    .modal-container {
      width: 95%;
    }
  }
  </style>