<template>
  <div v-if="error" class="error-overlay">
    <div class="error-message">{{ error }}</div>
    <button @click="refreshStreams" class="retry-button">Retry</button>
  </div>
  <div v-else class="streams-container">
    <AddStreamForm
      @add-stream="handleAddStream"
      @stream-added="handleStreamAdded"
      @refresh-streams="refreshStreams"
      @refresh-agents="fetchAgents"
    />

    <div class="tabs-container">
      <nav class="tabs-nav">
        <button
          v-for="platform in ['chaturbate', 'stripchat']"
          :key="platform"
          @click="activeTab = platform"
          :class="['tab-button', { active: activeTab === platform }]"
        >
          <span class="platform-name">
            {{ platform.charAt(0).toUpperCase() + platform.slice(1) }}
          </span>
          <span class="stream-count">{{ streams[platform].length }}</span>
        </button>
      </nav>
    </div>

    <div class="tables-container">
      <StreamTable
        :streams="streams[activeTab]"
        :platform="activeTab"
        :new-stream-id="newStreamId"
        :agents="agents"
        @delete="streamId => confirmDelete = { show: true, streamId }"
        @manage-assignments="openManageAssignments"
      />
    </div>

    <div class="tables-container">
      <AgentTable
        :agents="agents"
        @edit="openEditAgentModal"
        @delete="agentId => confirmDelete = { show: true, streamId: `agent-${agentId}` }"
      />
    </div>

    <Teleport to="body">
      <div v-if="toast" :class="['toast', toast.type]">
        <span class="toast-icon">
          {{ toast.type === 'success' ? '✅' : toast.type === 'error' ? '❌' : 'ℹ️' }}
        </span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>

      <ConfirmDialog
        v-if="confirmDelete.show"
        :message="
          confirmDelete.streamId && confirmDelete.streamId.toString().startsWith('agent-')
            ? 'Are you sure you want to delete this agent?'
            : 'Are you sure you want to delete this stream?'
        "
        @confirm="handleConfirmDelete"
        @cancel="handleCancelDelete"
      />

      <EditAgentModal
        v-if="editAgent"
        :agent="editAgent"
        @close="closeEditAgentModal"
        @save="handleEditAgent"
      />

      <ManageAssignmentsModal
        v-if="manageAssignmentStream"
        :stream="manageAssignmentStream"
        :agents="agents"
        @close="manageAssignmentStream = null"
        @save="handleAssignmentsUpdated"
      />
    </Teleport>

    <div class="fab-container">
      <button
        class="fab refresh-button"
        @click="refreshStreams"
        title="Refresh streams"
        aria-label="Refresh streams"
      >
        ↻
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue';
import axios from 'axios';
import AddStreamForm from './AddStreamForm.vue';
import StreamTable from './StreamTable.vue';
import AgentTable from './AgentTable.vue';
import ConfirmDialog from './ConfirmDialog.vue';
import EditAgentModal from './EditAgentModal.vue';
import ManageAssignmentsModal from './ManageAssignmentsModal.vue';

export default {
  name: 'StreamsPage',
  components: {
    AddStreamForm,
    StreamTable,
    AgentTable,
    ConfirmDialog,
    EditAgentModal,
    ManageAssignmentsModal
  },
  setup() {
    const streams = reactive({
      chaturbate: [],
      stripchat: []
    });
    const agents = ref([]);
    const error = ref(null);
    const activeTab = ref('chaturbate');
    const newStreamId = ref(null);
    const toast = ref(null);
    const confirmDelete = ref({ show: false, streamId: null });
    const editAgent = ref(null);
    const manageAssignmentStream = ref(null);

    const showToast = (message, type = 'success', duration = 3000) => {
      toast.value = { message, type };
      setTimeout(() => {
        toast.value = null;
      }, duration);
    };

    const fetchStreams = async (platform) => {
      try {
        const response = await axios.get(`/api/streams?platform=${platform}`);
        streams[platform] = response.data.map(stream => ({
          ...stream,
          platform: platform
        }));
      } catch (err) {
        error.value = err.response?.data?.message || 'Failed to fetch streams';
        console.error('Stream fetch error:', err);
      }
    };

    const fetchAgents = async () => {
      try {
        const res = await axios.get('/api/agents');
        agents.value = res.data;
      } catch (err) {
        console.error('Error fetching agents:', err);
      }
    };

    const refreshStreams = async () => {
      try {
        await Promise.all([fetchStreams('chaturbate'), fetchStreams('stripchat')]);
      } catch (err) {
        console.error(err);
      }
    };

    const handleDeleteStream = async (streamId, platform) => {
      try {
        await axios.delete(`/api/streams/${streamId}`);
        streams[platform] = streams[platform].filter(stream => stream.id !== streamId);
        showToast('Stream deleted successfully', 'success');
      } catch (err) {
        alert(err.response?.data?.message || 'Failed to delete stream');
        console.error('Delete error:', err);
      }
    };

    const handleDeleteAgent = async (agentId) => {
      try {
        await axios.delete(`/api/agents/${agentId}`);
        showToast('Agent deleted successfully', 'success');
        fetchAgents();
      } catch (err) {
        showToast(err.response?.data?.message || 'Failed to delete agent', 'error');
        console.error('Error deleting agent:', err);
      }
    };

    const handleConfirmDelete = () => {
      if (confirmDelete.value.streamId) {
        if (confirmDelete.value.streamId.toString().startsWith('agent-')) {
          const agentId = confirmDelete.value.streamId.split('-')[1];
          handleDeleteAgent(agentId);
        } else {
          handleDeleteStream(confirmDelete.value.streamId, activeTab.value);
        }
      }
      confirmDelete.value = { show: false, streamId: null };
    };

    const handleCancelDelete = () => {
      confirmDelete.value = { show: false, streamId: null };
    };

    const handleAddStream = (newStream) => {
      const platform = newStream.type.toLowerCase();
      activeTab.value = platform;
      newStreamId.value = newStream.id;
      streams[platform].push(newStream);
    };

    const handleStreamAdded = () => {
      showToast('Stream created successfully', 'success');
    };

    const handleEditAgent = async (agentId, payload) => {
      try {
        await axios.put(`/api/agents/${agentId}`, payload);
        showToast('Agent updated successfully', 'info');
        fetchAgents();
      } catch (err) {
        showToast(err.response?.data?.message || 'Failed to update agent', 'error');
        console.error('Error updating agent:', err);
      }
    };

    const openEditAgentModal = (agent) => {
      editAgent.value = agent;
    };

    const closeEditAgentModal = () => {
      editAgent.value = null;
    };

    const openManageAssignments = (stream) => {
      manageAssignmentStream.value = stream;
    };

    const handleAssignmentsUpdated = () => {
      refreshStreams();
    };

    onMounted(() => {
      refreshStreams();
      fetchAgents();
    });

    return {
      streams,
      agents,
      error,
      activeTab,
      newStreamId,
      toast,
      confirmDelete,
      editAgent,
      manageAssignmentStream,
      showToast,
      fetchStreams,
      fetchAgents,
      refreshStreams,
      handleDeleteStream,
      handleConfirmDelete,
      handleCancelDelete,
      handleAddStream,
      handleStreamAdded,
      handleEditAgent,
      openEditAgentModal,
      closeEditAgentModal,
      openManageAssignments,
      handleAssignmentsUpdated
    };
  }
};
</script>