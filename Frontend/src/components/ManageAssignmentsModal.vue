<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <h3 class="modal-title">Manage Assignments for Stream {{ stream.id }}</h3>
      <button class="close-button" @click="$emit('close')">×</button>
      <div class="assignments-form">
        <p>Select agents to assign to this stream:</p>
        <div class="agent-checkboxes">
          <label v-for="agent in agents" :key="agent.id">
            <input
              type="checkbox"
              :checked="selectedAgentIds.includes(agent.id)"
              @change="toggleAgentSelection(agent.id)"
            />
            {{ agent.username }}
          </label>
        </div>
      </div>
      <button class="submit-button" @click="handleSave">Save Assignments</button>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import axios from 'axios';

export default {
  name: 'ManageAssignmentsModal',
  props: {
    stream: {
      type: Object,
      required: true
    },
    agents: {
      type: Array,
      required: true
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const selectedAgentIds = ref(
      props.stream.assignments ? props.stream.assignments.map(a => a.agent_id) : []
    );

    const toggleAgentSelection = (agentId) => {
      if (selectedAgentIds.value.includes(agentId)) {
        selectedAgentIds.value = selectedAgentIds.value.filter(id => id !== agentId);
      } else {
        selectedAgentIds.value.push(agentId);
      }
    };

    const handleSave = async () => {
      try {
        await axios.put(`/api/streams/${props.stream.id}/assignments`, { 
          assignments: selectedAgentIds.value 
        });
        emit('save', props.stream.id, selectedAgentIds.value);
        emit('close');
      } catch (err) {
        console.error("Failed to update assignments:", err);
      }
    };

    return {
      selectedAgentIds,
      toggleAgentSelection,
      handleSave
    };
  }
};
</script>