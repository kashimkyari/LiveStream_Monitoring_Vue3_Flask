<template>
  <div class="mobile-admin-agents" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <!-- Header -->
    <div class="view-controls">
      <h2>Agents</h2>
      <div class="controls-right">
        <button class="refresh-btn" @click="loadAgents" :disabled="loading">
          <font-awesome-icon icon="sync" :class="{ 'fa-spin': loading }" />
        </button>
      </div>
    </div>

    <!-- Search Filter -->
    <div class="search-filter">
      <input type="text" v-model="searchQuery" placeholder="Search agents..." class="search-input" />
    </div>

    <!-- Agents List -->
    <div class="agents-list">
      <div class="agent-item" v-for="agent in filteredAgents" :key="agent.id" @click="showAgentDetails(agent)">
        <font-awesome-icon icon="users" class="agent-icon" />
        <div class="agent-content">
          <p class="agent-name">{{ agent.username }}</p>
          <span class="agent-status" :class="{ active: agent.online }">
            {{ agent.online ? 'Online' : 'Offline' }}
          </span>
        </div>
      </div>
      <p v-if="loading" class="loading-text">Loading agents...</p>
      <p v-else-if="!filteredAgents.length" class="no-data">No agents found</p>
    </div>

    <!-- Add Agent Button -->
    <button class="fab" @click="showAddAgentModal">
      <font-awesome-icon icon="plus" />
    </button>

    <!-- Add Agent Bottom Sheet -->
    <div class="bottom-sheet" :class="{ active: showAddModal }">
      <div class="bottom-sheet-content">
        <div class="modal-header">
          <h3>Add New Agent</h3>
          <button class="close-btn" @click="closeAddAgentModal">
            <font-awesome-icon icon="times" />
          </button>
        </div>
        <form @submit.prevent="addAgent">
          <div class="form-group">
            <label for="add-username">Username</label>
            <input
              id="add-username"
              v-model="newAgent.username"
              type="text"
              placeholder="Enter username"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label for="add-email">Email</label>
            <input
              id="add-email"
              v-model="newAgent.email"
              type="email"
              placeholder="Enter email"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label for="add-password">Password</label>
            <input
              id="add-password"
              v-model="newAgent.password"
              type="password"
              placeholder="Enter password"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="newAgent.receiveUpdates" />
              Receive Updates
            </label>
          </div>
          <div class="form-actions">
            <button type="button" class="cancel-btn" @click="closeAddAgentModal">Cancel</button>
            <button type="submit" class="submit-btn" :disabled="addingAgent">Add Agent</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Agent Details Bottom Sheet -->
    <div class="bottom-sheet" :class="{ active: showDetailsModal }">
      <div class="bottom-sheet-content">
        <div class="modal-header">
          <h3>{{ isEditing ? 'Edit Agent' : 'Agent Details' }}</h3>
          <div class="header-actions">
            <button class="delete-btn" @click="confirmDeleteAgent(selectedAgent.id)">
              <font-awesome-icon icon="trash" />
            </button>
            <button v-if="!isEditing" class="edit-btn" @click="startEditing">
              <font-awesome-icon icon="edit" />
            </button>
            <button class="close-btn" @click="closeDetailsModal">
              <font-awesome-icon icon="times" />
            </button>
          </div>
        </div>
        <div class="agent-details" v-if="selectedAgent">
          <form v-if="isEditing" @submit.prevent="saveAgentChanges">
            <div class="form-group">
              <label for="edit-username">Username</label>
              <input
                id="edit-username"
                v-model="editAgent.username"
                type="text"
                placeholder="Enter username"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="edit-email">Email</label>
              <input
                id="edit-email"
                v-model="editAgent.email"
                type="email"
                placeholder="Enter email"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="editAgent.receiveUpdates" />
                Receive Updates
              </label>
            </div>
            <div class="form-group stream-assignment-group">
              <label for="edit-streams">Assigned Streams</label>
              <div class="stream-assignment-container">
                <div class="stream-search">
                  <input
                    type="text"
                    v-model="streamSearchQuery"
                    placeholder="Search streams..."
                    class="form-input stream-search-input"
                    @input="filterStreams"
                  />
                </div>
                <div class="stream-list-container">
                  <div v-if="filteredStreams.length === 0" class="no-streams-message">
                    No streams found
                  </div>
                  <div v-else class="stream-item" v-for="stream in filteredStreams" :key="stream.id" @click="toggleStreamAssignment(stream.id)" :class="{ 'assigned': editAgent.streamIds.includes(stream.id) }">
                    <div class="stream-info">
                      <span class="stream-name">{{ stream.streamer_username }}</span>
                      <span class="stream-platform" :class="stream.platform.toLowerCase()">{{ stream.platform }}</span>
                    </div>
                    <div class="assignment-status">
                      <span v-if="editAgent.streamIds.includes(stream.id)" class="assigned-badge">Assigned</span>
                      <font-awesome-icon 
                        :icon="editAgent.streamIds.includes(stream.id) ? 'check-circle' : 'plus-circle'" 
                        class="status-icon" 
                        :class="{ 'assigned-icon': editAgent.streamIds.includes(stream.id) }" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="form-actions">
              <button type="button" class="cancel-btn" @click="cancelEditing">Cancel</button>
              <button type="submit" class="submit-btn" :disabled="savingChanges">Save Changes</button>
            </div>
          </form>
          <div v-else>
            <div class="detail-row">
              <span class="detail-label">Username:</span>
              <span class="detail-value">{{ selectedAgent.username }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Email:</span>
              <span class="detail-value">{{ selectedAgent.email }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Status:</span>
              <span class="detail-value" :class="{ active: selectedAgent.online }">
                {{ selectedAgent.online ? 'Online' : 'Offline' }}
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Receive Updates:</span>
              <span class="detail-value">{{ selectedAgent.receiveUpdates ? 'Yes' : 'No' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Assigned Streams:</span>
              <div class="assigned-streams">
                <div v-if="assignedStreamsLoading" class="loading-text">Loading streams...</div>
                <div v-else-if="!assignedStreams.length" class="no-data">No streams assigned</div>
                <div v-else class="stream-list">
                  <div v-for="stream in assignedStreams" :key="stream.id" class="stream-item">
                    <span class="stream-name">{{ stream.streamer_username }}</span>
                    <span class="stream-platform" :class="stream.platform.toLowerCase()">
                      {{ stream.platform }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div class="form-actions">
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Blur effect for parent component when modal is open -->
    <div class="modal-overlay" v-if="showAddModal || showDetailsModal"></div>

    <!-- Add ConfirmationModal at the end of template -->
    <ConfirmationModal
      v-if="showConfirmationModal"
      :title="confirmationConfig.title"
      :message="confirmationConfig.message"
      :action-text="confirmationConfig.actionText"
      @close="onConfirmationClose"
      @confirm="confirmationConfig.onConfirm"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import ConfirmationModal from './ConfirmationModal.vue'

export default {
  name: 'MobileAdminAgents',
  components: {
    ConfirmationModal
  },
  props: {
    isDarkTheme: Boolean
  },
  emits: ['agent-selected'],
  setup() {
    const toast = useToast()
    const searchQuery = ref('')
    const showAddModal = ref(false)
    const showDetailsModal = ref(false)
    const showConfirmationModal = ref(false)
    const confirmationConfig = ref({
      title: '',
      message: '',
      actionText: '',
      onConfirm: null
    })
    const addingAgent = ref(false)
    const assignedStreamsLoading = ref(false)
    const assignedStreams = ref([])
    const allStreams = ref([])
    const selectedAgent = ref(null)
    const agents = ref([])
    const loading = ref(false)
    const isEditing = ref(false)
    const savingChanges = ref(false)
    const editAgent = ref({})
    const streamSearchQuery = ref('')
    const filteredStreams = ref([])

    const newAgent = ref({
      username: '',
      email: '',
      password: '',
      receiveUpdates: false
    })

    const filteredAgents = computed(() => {
      if (!agents.value) return []
      return agents.value.filter(agent =>
        agent.username.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    })

    const filterStreams = () => {
      if (!streamSearchQuery.value) {
        filteredStreams.value = allStreams.value
      } else {
        filteredStreams.value = allStreams.value.filter(stream =>
          stream.streamer_username.toLowerCase().includes(streamSearchQuery.value.toLowerCase()) ||
          stream.platform.toLowerCase().includes(streamSearchQuery.value.toLowerCase())
        )
      }
    }

    const toggleStreamAssignment = (streamId) => {
      const index = editAgent.value.streamIds.indexOf(streamId)
      if (index === -1) {
        editAgent.value.streamIds.push(streamId)
      } else {
        editAgent.value.streamIds.splice(index, 1)
      }
    }

    const loadAgents = async () => {
      loading.value = true
      toast.info('Loading agents...')
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/agents', {
          headers: { Authorization: `Bearer ${token}` }
        })
        agents.value = response.data
        toast.success('Agents loaded successfully')
      } catch (error) {
        const message = error.response?.data?.message || 'Failed to load agents'
        toast.error(message)
        agents.value = []
      } finally {
        loading.value = false
      }
    }

    const loadAllStreams = async () => {
      toast.info('Loading all streams...')
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/streams', {
          headers: { Authorization: `Bearer ${token}` }
        })
        allStreams.value = Object.values(response.data).map(stream => ({
          ...stream,
          platform: stream.type || 'Unknown'
        }))
        filteredStreams.value = allStreams.value
        toast.success('Streams loaded successfully')
      } catch (error) {
        const message = error.response?.data?.message || 'Failed to load streams'
        toast.error(message)
        allStreams.value = []
        filteredStreams.value = []
      }
    }

    const showAddAgentModal = () => {
      showAddModal.value = true
    }

    const closeAddAgentModal = () => {
      showAddModal.value = false
      newAgent.value = { username: '', email: '', password: '', receiveUpdates: false }
    }

    const showAgentDetails = async (agent) => {
      selectedAgent.value = agent
      showDetailsModal.value = true
      isEditing.value = false
      toast.info('Loading agent details...')
      try {
        await Promise.all([loadAssignedStreams(agent.id), loadAllStreams()])
        toast.success('Agent details loaded successfully')
      } catch (error) {
        toast.error('Failed to load agent details')
      }
    }

    const closeDetailsModal = () => {
      showDetailsModal.value = false
      selectedAgent.value = null
      assignedStreams.value = []
      isEditing.value = false
      editAgent.value = {}
    }

    const startEditing = () => {
      editAgent.value = {
        username: selectedAgent.value.username,
        email: selectedAgent.value.email,
        receiveUpdates: selectedAgent.value.receiveUpdates,
        streamIds: assignedStreams.value.map(stream => stream.id)
      }
      streamSearchQuery.value = ''
      filteredStreams.value = allStreams.value
      isEditing.value = true
    }

    const cancelEditing = () => {
      isEditing.value = false
      editAgent.value = {}
    }

    const saveAgentChanges = async () => {
      savingChanges.value = true
      toast.info('Saving agent changes...')
      try {
        const token = localStorage.getItem('token')
        // Update agent details
        const response = await axios.patch(`/api/agents/${selectedAgent.value.id}`, {
          username: editAgent.value.username,
          email: editAgent.value.email,
          receiveUpdates: editAgent.value.receiveUpdates
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        agents.value = agents.value.map(agent =>
          agent.id === selectedAgent.value.id ? response.data : agent
        )
        selectedAgent.value = response.data
        toast.success('Agent details updated successfully')
        
        // Handle stream assignments by removing old ones and adding new ones
        toast.info('Updating stream assignments...')
        // Get current assignments for the agent
        const currentAssignmentsResponse = await axios.get(`/api/assignments?agent_id=${selectedAgent.value.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        const currentAssignments = currentAssignmentsResponse.data.assignments
        const currentStreamIds = currentAssignments.map(a => a.stream_id)
        const newStreamIds = editAgent.value.streamIds || []
        
        // Remove assignments that are no longer in the new list
        const streamsToRemove = currentStreamIds.filter(id => !newStreamIds.includes(id))
        for (const streamId of streamsToRemove) {
          const assignment = currentAssignments.find(a => a.stream_id === streamId)
          if (assignment) {
            await axios.delete(`/api/assignments/${assignment.id}`, {
              headers: { Authorization: `Bearer ${token}` }
            })
          }
        }
        
        // Add new assignments that weren't in the old list
        const streamsToAdd = newStreamIds.filter(id => !currentStreamIds.includes(id))
        for (const streamId of streamsToAdd) {
          await axios.post('/api/assign', {
            agent_id: selectedAgent.value.id,
            stream_id: streamId
          }, {
            headers: { Authorization: `Bearer ${token}` }
          })
        }
        
        if (streamsToRemove.length > 0 || streamsToAdd.length > 0) {
          toast.success('Stream assignments updated successfully')
        } else {
          toast.info('No changes to stream assignments')
        }
        
        await loadAssignedStreams(selectedAgent.value.id)
        isEditing.value = false
        editAgent.value = {}
      } catch (error) {
        const message = error.response?.data?.message || 'Failed to update agent or assignments'
        toast.error(message)
      } finally {
        savingChanges.value = false
      }
    }

    const loadAssignedStreams = async (agentId) => {
      assignedStreamsLoading.value = true
      toast.info('Loading assigned streams...')
      try {
        const token = localStorage.getItem('token')
        // Use the assignment endpoint to get current assignments for the agent
        const response = await axios.get(`/api/assignments?agent_id=${agentId}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        const assignedStreamIds = response.data.assignments.map(a => a.stream_id)
        
        // Get full stream details
        const streamsResponse = await axios.get('/api/streams', {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        assignedStreams.value = streamsResponse.data
          .filter(stream => assignedStreamIds.includes(stream.id))
          .map(stream => ({
            ...stream,
            platform: stream.type || 'Unknown'
          }))
        toast.success('Assigned streams loaded successfully')
      } catch (error) {
        const message = error.response?.data?.message || 'Failed to load assigned streams'
        toast.error(message)
        assignedStreams.value = []
      } finally {
        assignedStreamsLoading.value = false
      }
    }

    const addAgent = async () => {
      addingAgent.value = true
      toast.info('Adding new agent...')
      try {
        const token = localStorage.getItem('token')
        const response = await axios.post('/api/register', {
          username: newAgent.value.username,
          email: newAgent.value.email,
          password: newAgent.value.password,
          receiveUpdates: newAgent.value.receiveUpdates
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        closeAddAgentModal()
        agents.value = [...agents.value, response.data.user]
        toast.success('Agent created successfully')
      } catch (error) {
        const message = error.response?.data?.message || 'Failed to create agent'
        toast.error(message)
      } finally {
        addingAgent.value = false
      }
    }

    const confirmDeleteAgent = async (agentId) => {
      showConfirmationModal.value = true
      confirmationConfig.value = {
        title: 'Delete Agent',
        message: 'Are you sure you want to delete this agent? This action cannot be undone.',
        actionText: 'Delete',
        onConfirm: () => deleteAgent(agentId)
      }
    }

    const deleteAgent = async (agentId) => {
      toast.info('Deleting agent...')
      try {
        const token = localStorage.getItem('token')
        if (!token) throw new Error('No authentication token found')
        await axios.delete(`/api/agents/${agentId}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        agents.value = agents.value.filter(agent => agent.id !== agentId)
        if (selectedAgent.value?.id === agentId) {
          closeDetailsModal()
        }
        toast.success('Agent deleted successfully')
      } catch (error) {
        const message = error.response?.data?.message || 'Failed to delete agent'
        toast.error(message)
      }
    }

    const onConfirmationClose = () => {
      showConfirmationModal.value = false
    }

    // Load agents on component mount
    onMounted(() => {
      loadAgents()
    })

    return {
      searchQuery,
      filteredAgents,
      showAddModal,
      showDetailsModal,
      newAgent,
      addingAgent,
      selectedAgent,
      assignedStreams,
      assignedStreamsLoading,
      allStreams,
      loading,
      agents,
      isEditing,
      editAgent,
      savingChanges,
      showAddAgentModal,
      closeAddAgentModal,
      showAgentDetails,
      closeDetailsModal,
      startEditing,
      cancelEditing,
      saveAgentChanges,
      addAgent,
      confirmDeleteAgent,
      deleteAgent,
      loadAgents,
      streamSearchQuery,
      filteredStreams,
      filterStreams,
      toggleStreamAssignment,
      showConfirmationModal,
      confirmationConfig,
      onConfirmationClose
    }
  }
}
</script>

<style scoped>
.mobile-admin-agents {
  font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --primary-color: #4361ee;
  --primary-light: #4361ee20;
  --secondary-color: #3f37c9;
  --danger-color: #e5383b;
  --success-color: #38b000;
  --warning-color: #ffb700;
  --text-color: #333333;
  --text-light: #777777;
  --background-color: #f8f9fa;
  --card-bg: #ffffff;
  --border-color: #e0e0e0;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  --border-radius: 12px;
  --border-radius-sm: 8px;
  background-color: var(--background-color);
  color: var(--text-color);
  padding: 16px;
  position: relative;
  min-height: 100vh;
  box-sizing: border-box;
}

.mobile-admin-agents[data-theme="dark"] {
  --primary-color: #4cc9f0;
  --primary-light: #4cc9f020;
  --secondary-color: #4895ef;
  --text-color: #f8f9fa;
  --text-light: #b0b0b0;
  --background-color: #121212;
  --card-bg: #1e1e1e;
  --border-color: #333333;
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
}

/* View Controls */
.view-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.view-controls h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-color);
}

.controls-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.refresh-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--border-radius-sm);
  background-color: var(--primary-color);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.refresh-btn:hover {
  background-color: var(--secondary-color);
  transform: scale(1.05);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Search Filter */
.search-filter {
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  background-color: var(--card-bg);
  color: var(--text-color);
  font-size: 0.875rem;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.search-input::placeholder {
  color: var(--text-light);
}

/* Agents List */
.agents-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 70px; /* Space for FAB */
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: var(--card-bg);
  padding: 12px;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: var(--transition);
  border: 1px solid var(--border-color);
}

.agent-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.agent-icon {
  color: var(--primary-color);
  font-size: 1.25rem;
}

.agent-content {
  flex: 1;
}

.agent-name {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-color);
}

.agent-status {
  font-size: 0.75rem;
  color: var(--text-light);
}

.agent-status.active {
  color: var(--success-color);
}

.delete-btn {
  background-color: var(--danger-color);
  color: white;
  border: none;
  border-radius: var(--border-radius-sm);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.delete-btn:hover {
  background-color: #d32f2f;
  transform: scale(1.05);
}

.loading-text,
.no-data {
  font-size: 0.875rem;
  color: var(--text-light);
  text-align: center;
  padding: 16px;
}

/* Floating Action Button */
.fab {
  position: fixed;
  bottom: 80px;
  right: 16px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 50%;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition);
  box-shadow: var(--shadow-md);
  font-size: 1.5rem;
  z-index: 10;
}

.fab:hover {
  background-color: var(--secondary-color);
  transform: scale(1.1);
}

/* Bottom Sheet */
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: var(--card-bg);
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  box-shadow: var(--shadow-md);
  transform: translateY(100%);
  transition: transform 0.3s ease-in-out;
  z-index: 1000;
  max-height: 90vh;
  overflow-y: auto;
}

.bottom-sheet.active {
  transform: translateY(0);
}

.bottom-sheet-content {
  padding: 16px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-color);
}

/* Header Actions Buttons */
.edit-btn,
.close-btn,
.delete-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--border-radius-sm);
  border: none;
  background-color: var(--border-color);
  color: var(--text-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition);
}

.delete-btn {
  background-color: var(--danger-color);
  color: white;
}

.edit-btn:hover,
.close-btn:hover {
  background-color: var(--primary-light);
}

.delete-btn:hover {
  background-color: #d32f2f;
}

/* Form Styles */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: var(--text-color);
}

.form-input,
.form-input[multiple] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  background-color: var(--background-color);
  color: var(--text-color);
  font-size: 0.875rem;
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.form-input[multiple] {
  height: 100px;
  overflow-y: auto;
}

.form-input:focus,
.form-input[multiple]:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.form-input::placeholder {
  color: var(--text-light);
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.cancel-btn,
.submit-btn {
  flex: 1;
  padding: 12px;
  border-radius: var(--border-radius-sm);
  border: none;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
}

.cancel-btn {
  background-color: var(--border-color);
  color: var(--text-color);
}

.cancel-btn:hover {
  background-color: #d1d5db;
}

.submit-btn {
  background-color: var(--primary-color);
  color: white;
}

.submit-btn:hover {
  background-color: var(--secondary-color);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Agent Details */
.agent-details {
  padding: 16px 0;
}

.detail-row {
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.detail-label {
  font-weight: 600;
  color: var(--text-color);
  min-width: 100px;
}

.detail-value {
  color: var(--text-color);
  word-break: break-word;
}

.detail-value.active {
  color: var(--success-color);
}

.assigned-streams {
  width: 100%;
}

.stream-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stream-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: var(--background-color);
  border-radius: var(--border-radius-sm);
  border: 1px solid var(--border-color);
  box-shadow: var (--shadow-sm);
}

.stream-name {
  font-size: 0.875rem;
  color: var(--text-color);
}

.stream-platform {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.stream-platform.chaturbate {
  background-color: #f59e0b20;
  color: #f59e0b;
  border: 1px solid #f59e0b40;
}

.stream-platform.stripchat {
  background-color: #8b5cf620;
  color: #8b5cf6;
  border: 1px solid #8b5cf640;
}

/* Stream Assignment Styles */
.stream-assignment-group {
  margin-bottom: 20px;
}

.stream-assignment-container {
  background-color: var(--background-color);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-sm);
  padding: 10px;
  max-height: 300px;
  display: flex;
  flex-direction: column;
}

.stream-search {
  margin-bottom: 10px;
}

.stream-search-input {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  color: var(--text-color);
}

.stream-search-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px var (--primary-light);
}

.stream-list-container {
  overflow-y: auto;
  flex: 1;
}

.stream-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: var(--transition);
  border: 1px solid transparent;
}

.stream-item:hover {
  background-color: var(--primary-light);
  border-color: var(--primary-color);
}

.stream-info {
  display: flex;
  flex-direction: column;
}

.stream-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-color);
}

.stream-platform {
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  text-transform: uppercase;
  margin-top: 2px;
}

.stream-platform.chaturbate {
  background-color: #f59e0b20;
  color: #f59e0b;
  border: 1px solid #f59e0b40;
}

.stream-platform.stripchat {
  background-color: #8b5cf620;
  color: #8b5cf6;
  border: 1px solid #8b5cf640;
}

.assignment-icon {
  color: var(--text-light);
  font-size: 1.2rem;
  transition: var(--transition);
}

.assignment-icon.assigned {
  color: var(--success-color);
}

.no-streams-message {
  display: flex;
  height: 100%;
  justify-content: center;
  align-items: center;
  color: var(--text-light);
  font-style: italic;
  font-size: 0.875rem;
}

/* SweetAlert2 Custom Styles */
:deep(.swal-light),
:deep(.swal-dark) {
  background-color: var(--card-bg);
  color: var(--text-color);
  font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-md);
}

:deep(.swal-title) {
  color: var(--text-color);
  font-size: 1.25rem;
  font-weight: 600;
}

:deep(.swal-text) {
  color: var(--text-light);
  font-size: 0.875rem;
}

:deep(.swal-confirm) {
  background-color: var(--danger-color) !important;
  color: white !important;
  border: none !important;
  border-radius: var(--border-radius-sm) !important;
  padding: 12px 24px !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  transition: var(--transition) !important;
  box-shadow: var(--shadow-sm) !important;
}

:deep(.swal-confirm:hover) {
  background-color: #d32f2f !important;
}

:deep(.swal-cancel) {
  background-color: var(--border-color) !important;
  color: var(--text-color) !important;
  border: none !important;
  border-radius: var(--border-radius-sm) !important;
  padding: 12px 24px !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  transition: var(--transition) !important;
  box-shadow: var(--shadow-sm) !important;
}

:deep(.swal-cancel:hover) {
  background-color: #d1d5db !important;
}

:deep(.swal2-loader) {
  border-color: var(--primary-color) transparent var(--primary-color) transparent !important;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
  .mobile-admin-agents {
    padding: 12px;
  }

  .bottom-sheet {
    max-height: 95vh;
  }

  .agent-item {
    padding: 10px;
  }

  .delete-btn {
    width: 36px;
    height: 36px;
  }
}

@media (max-width: 480px) {
  .view-controls h2 {
    font-size: 1.25rem;
  }

  .form-actions {
    flex-direction: column;
  }

  .cancel-btn,
  .submit-btn {
    width: 100%;
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .detail-label {
    min-width: auto;
  }
}

.assigned {
  background-color: var(--primary-light);
  border-left: 4px solid var(--primary-color);
}

.assigned-badge {
  font-size: 0.75rem;
  color: var(--success-color);
  margin-right: 8px;
}

.status-icon {
  color: var(--text-light);
  transition: var(--transition);
}

.status-icon.assigned-icon {
  color: var(--success-color);
}

/* Blur effect for parent component when modal is open */
.mobile-admin-agents.modal-open {
  filter: blur(5px);
  pointer-events: none;
}

/* Overlay for blur effect */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
}
</style>