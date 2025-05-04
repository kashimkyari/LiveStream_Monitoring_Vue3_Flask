<template>
  <div class="agent-assignments" ref="assignmentsContainer">
    <div class="assignments-header">
      <h4>{{ agent.username }}'s Assigned Streams</h4>
      <div class="status-badge" :class="{ 'online': agent.online }">
        {{ agent.online ? 'Online' : 'Offline' }}
      </div>
    </div>
    
    <div v-if="loading" class="loading-container">
      <div class="loader"></div>
      <p>Loading assignments...</p>
    </div>
    
    <div v-else-if="assignments.length === 0" class="no-assignments" ref="noAssignments">
      <font-awesome-icon icon="stream" size="2x" />
      <p>No streams assigned to this agent</p>
    </div>
    
    <ul v-else class="assignments-list">
      <li v-for="assignment in assignments" :key="assignment.id" class="assignment-item" ref="assignmentItems">
        <div class="stream-info">
          <div class="platform-badge" :class="getPlatformClass(assignment.stream.platform)">
            {{ assignment.stream.platform }}
          </div>
          <h5>{{ assignment.stream.streamer_username }}</h5>
          <a :href="assignment.stream.room_url" target="_blank" class="stream-link">
            <font-awesome-icon icon="external-link-alt" /> View Stream
          </a>
        </div>
        <div class="assignment-actions">
          <button @click="removeAssignment(assignment.id)" class="remove-btn" v-wave>
            <font-awesome-icon icon="times" />
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
// eslint-disable-next-line no-unused-vars
import { ref, onMounted } from 'vue'
import anime from 'animejs/lib/anime.es.js'

export default {
  name: 'AgentAssignments',
  props: {
    agent: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    const assignments = ref([])
    const loading = ref(true)
    const assignmentsContainer = ref(null)
    const assignmentItems = ref([])
    const noAssignments = ref(null)
    
    const fetchAssignments = async () => {
      loading.value = true
      try {
        const response = await fetch(`/api/agents/${props.agent.id}/assignments`)
        if (response.ok) {
          const data = await response.json()
          assignments.value = data
          
          // Animate items after they're loaded
          setTimeout(() => {
            if (assignments.value.length > 0) {
              anime({
                targets: assignmentItems.value,
                translateX: [-20, 0],
                opacity: [0, 1],
                delay: anime.stagger(100),
                duration: 500,
                easing: 'easeOutQuad'
              })
            } else if (noAssignments.value) {
              anime({
                targets: noAssignments.value,
                scale: [0.9, 1],
                opacity: [0, 1],
                duration: 500,
                easing: 'easeOutElastic(1, .8)'
              })
            }
          }, 100)
        }
      } catch (error) {
        console.error("Error fetching assignments:", error)
      } finally {
        loading.value = false
      }
    }
    
    const removeAssignment = async (assignmentId) => {
      const targetItem = assignmentItems.value.find(
        el => el.dataset.id === assignmentId.toString()
      )
      
      if (targetItem) {
        anime({
          targets: targetItem,
          translateX: 20,
          opacity: 0,
          duration: 300,
          easing: 'easeOutQuad',
          complete: async () => {
            try {
              const response = await fetch(`/api/assignments/${assignmentId}`, {
                method: 'DELETE'
              })
              
              if (response.ok) {
                assignments.value = assignments.value.filter(a => a.id !== assignmentId)
                
                if (assignments.value.length === 0 && noAssignments.value) {
                  anime({
                    targets: noAssignments.value,
                    scale: [0.9, 1],
                    opacity: [0, 1],
                    duration: 500,
                    easing: 'easeOutElastic(1, .8)'
                  })
                }
              }
            } catch (error) {
              console.error("Error removing assignment:", error)
            }
          }
        })
      }
    }
    
    const getPlatformClass = (platform) => {
      if (!platform) return ''
      return platform.toLowerCase()
    }
    
    onMounted(() => {
      // Initial container animation
      anime({
        targets: assignmentsContainer.value,
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 600,
        easing: 'easeOutQuad',
        complete: () => {
          fetchAssignments()
        }
      })
    })
    
    return {
      assignments,
      loading,
      removeAssignment,
      getPlatformClass,
      assignmentsContainer,
      assignmentItems,
      noAssignments
    }
  }
}
</script>

<style scoped>
.agent-assignments {
  background-color: var(--input-bg);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-top: 20px;
  opacity: 0; /* Initial state for anime.js */
}

.assignments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--input-border);
}

.assignments-header h4 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--text-color);
}

.status-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  background-color: var(--hover-bg);
  color: var(--text-color);
}

.status-badge.online {
  background-color: rgba(39, 174, 96, 0.2);
  color: #27ae60;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
}

.loader {
  width: 30px;
  height: 30px;
  border: 3px solid var(--input-border);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.no-assignments {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: var(--text-muted);
  opacity: 0; /* Initial state for anime.js */
}

.no-assignments p {
  margin-top: 15px;
}

.assignments-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.assignment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-radius: 8px;
  background-color: var(--hover-bg);
  margin-bottom: 10px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  opacity: 0; /* Initial state for anime.js */
}

.assignment-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

.stream-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stream-info h5 {
  margin: 0;
  font-size: 1rem;
}

.platform-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 5px;
  background-color: var(--input-bg);
}

.platform-badge.chaturbate {
  background-color: rgba(255, 90, 95, 0.2);
  color: #ff5a5f;
}

.platform-badge.stripchat {
  background-color: rgba(30, 144, 255, 0.2);
  color: #1e90ff;
}

.stream-link {
  font-size: 0.8rem;
  color: var(--primary-color);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 5px;
}

.assignment-actions {
  display: flex;
  gap: 10px;
}

.remove-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  background-color: rgba(231, 76, 60, 0.2);
  transform: scale(1.1);
}

@media (max-width: 768px) {
  .assignments-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .status-badge {
    align-self: flex-start;
  }
}
</style>