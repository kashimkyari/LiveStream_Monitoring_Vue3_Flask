<template>
  <div class="form-container">
    <div class="form-header">
      <h2 class="form-title">Stream Management</h2>
    </div>
    
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="platform-select">Platform:</label>
        <select
          id="platform-select"
          v-model="platform"
          :class="['form-select', {'platform-switch': roomUrl.includes('stripchat.com')}]"
        >
          <option value="chaturbate">Chaturbate</option>
          <option value="stripchat">Stripchat</option>
        </select>
      </div>
      <div class="form-group">
        <label for="room-url">Room URL:</label>
        <input
          id="room-url"
          type="url"
          v-model="roomUrl"
          :placeholder="`Enter ${platform} room URL`"
          class="form-input"
          required
          inputmode="url"
        />
      </div>
      <div class="form-group assign-group">
        <label for="agent-select">Assign Agent:</label>
        <div class="assign-wrapper">
          <select
            id="agent-select"
            v-model="selectedAgentId"
            class="form-select"
          >
            <option v-for="agent in agents" :key="agent.id" :value="agent.id">
              {{ agent.username }}
            </option>
          </select>
          <button 
            type="button"
            class="quick-add-button"
            @click="showAddAgentModal = true"
            aria-label="Quick add agent"
          >
            + Add Agent
          </button>
        </div>
      </div>
      <button
        type="submit"
        :class="[
          'add-button',
          { 'submitting': isSubmitting && progress < 100 },
          { 'success': submitSuccess || (progress >= 100 && !submitError) },
          { 'error': submitError && !(progress >= 100 && !submitError) }
        ]"
        :disabled="isSubmitting && progress < 100 && !submitError"
        style="width: 100%; position: relative; overflow: hidden"
      >
        <template v-if="submitError && !(progress >= 100 && !submitError)">
          Retry Now
        </template>
        <template v-else-if="isSubmitting && progress < 100">
          <div class="button-progress">
            <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
            <div class="progress-text">
              {{ progress }}% - {{ progressMessage }} {{ estimatedTime > 0 ? `(Est. ${estimatedTime}s left)` : '' }}
            </div>
          </div>
        </template>
        <template v-else-if="(progress >= 100 && !submitError) || submitSuccess">
          Stream Created Successfully!
        </template>
        <template v-else>
          Add Stream
        </template>
      </button>
    </form>
    
    <add-agent-modal 
      v-if="showAddAgentModal"
      @close="showAddAgentModal = false"
      @agent-created="handleAgentCreated"
    />
  </div>
</template>

<script>
import { ref, watch, onMounted, defineComponent } from 'vue';
import axios from 'axios';

// You'll need to create this component separately
import AddAgentModal from './AddAgentModal.vue';

export default defineComponent({
  name: 'AddStreamForm',
  components: {
    AddAgentModal
  },
  props: {
    onAddStream: {
      type: Function,
      required: true
    },
    refreshStreams: {
      type: Function,
      default: () => {}
    },
    onStreamAdded: {
      type: Function,
      default: () => {}
    },
    refreshAgents: {
      type: Function,
      default: () => {}
    }
  },
  setup(props) {
    const platform = ref('chaturbate');
    const roomUrl = ref('');
    const selectedAgentId = ref('');
    const agents = ref([]);
    const isSubmitting = ref(false);
    const submitSuccess = ref(false);
    const error = ref(null);
    const jobId = ref(null);
    const progress = ref(0);
    const progressMessage = ref('');
    const estimatedTime = ref(0);
    const showAddAgentModal = ref(false);
    const submitError = ref(false);
    
    // Watch for URL changes to update platform automatically
    watch(roomUrl, (newUrl) => {
      if (newUrl.toLowerCase().includes('stripchat.com')) {
        platform.value = 'stripchat';
      } else {
        platform.value = 'chaturbate';
      }
    });
    
    // Watch for progress completion to fetch new stream
    watch(progress, (newProgress) => {
      if (newProgress >= 100 && jobId.value) {
        fetchNewStream();
      }
    });
    
    // Fetch agents on component mount
    onMounted(async () => {
      await fetchAgents();
    });
    
    const fetchAgents = async () => {
      try {
        const res = await axios.get('/api/agents');
        agents.value = res.data;
        if (res.data.length > 0) {
          selectedAgentId.value = res.data[0].id.toString();
        }
      } catch (err) {
        console.error('Failed to fetch agents:', err);
      }
    };
    
    const subscribeToProgress = (jobId) => {
      const eventSource = new EventSource(`/api/streams/interactive/sse?job_id=${jobId}`);
      eventSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        progress.value = data.progress;
        progressMessage.value = data.message;
        estimatedTime.value = data.estimated_time || 0;
        
        if (data.progress >= 100) {
          if (data.error) {
            submitError.value = true;
            error.value = data.error;
          }
          eventSource.close();
        }
      };
      eventSource.onerror = (err) => {
        console.error("SSE error:", err);
        submitError.value = true;
        error.value = 'Connection to progress updates failed';
        eventSource.close();
      };
    };
    
    const handleSubmit = async () => {
      isSubmitting.value = true;
      error.value = null;
      
      progress.value = 0;
      progressMessage.value = 'Initializing...';
      jobId.value = null;
      submitError.value = false;
      submitSuccess.value = false;
      
      try {
        const response = await axios.post('/api/streams/interactive', {
          room_url: roomUrl.value,
          platform: platform.value,
          agent_id: selectedAgentId.value
        });
        jobId.value = response.data.job_id;
        subscribeToProgress(jobId.value);
      } catch (err) {
        error.value = err.response?.data?.message || 'Failed to start stream creation';
        submitError.value = true;
        isSubmitting.value = false;
      }
    };
    
    const fetchNewStream = async () => {
      try {
        const res = await axios.get('/api/streams?platform=' + platform.value);
        const newStream = res.data[res.data.length - 1];
        props.onAddStream(newStream);
        submitSuccess.value = true;
        submitError.value = false;
        
        if (props.onStreamAdded) props.onStreamAdded();
      } catch (err) {
        console.error('Failed to fetch new stream:', err);
        submitSuccess.value = true;
      }
    };
    
    const handleAgentCreated = async () => {
      try {
        const res = await axios.get('/api/agents');
        agents.value = res.data;
        if (res.data.length > 0) {
          selectedAgentId.value = res.data[res.data.length - 1].id.toString();
        }
        if (props.refreshAgents) props.refreshAgents();
      } catch (err) {
        console.error('Error refreshing agents:', err);
      }
    };
    
    return {
      platform,
      roomUrl,
      selectedAgentId,
      agents,
      isSubmitting,
      submitSuccess,
      error,
      jobId,
      progress,
      progressMessage,
      estimatedTime,
      showAddAgentModal,
      submitError,
      handleSubmit,
      handleAgentCreated
    };
  }
});
</script>

<style scoped>
/* You can transfer the CSS from StreamsPage.css or define your styles here */
.form-container {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  padding: 20px;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.form-title {
  font-size: 1.25rem;
  margin: 0;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-input, .form-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.assign-group {
  margin-bottom: 20px;
}

.assign-wrapper {
  display: flex;
  gap: 10px;
}

.quick-add-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0 15px;
  cursor: pointer;
}

.add-button {
  background-color: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.add-button:disabled {
  opacity: 0.7;
  cursor: progress;
}

.add-button.success {
  background-color: #4CAF50;
}

.add-button.error {
  background-color: #f44336;
}

.button-progress {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.3);
  z-index: 1;
}

.progress-text {
  position: relative;
  z-index: 2;
  color: white;
}

.platform-switch {
  animation: pulse 1s;
}

@keyframes pulse {
  0% { background-color: inherit; }
  50% { background-color: #FFECB3; }
  100% { background-color: inherit; }
}
</style>