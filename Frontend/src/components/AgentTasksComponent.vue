<template>
  <div class="tasks-container">
    <div class="tasks-header">
      <h2>My Tasks</h2>
      <button class="refresh-button" @click="refreshTasks">
        <font-awesome-icon :icon="['fas', 'sync']" :class="{ 'rotating': isLoading }" />
      </button>
    </div>
    
    <div class="tasks-list" v-if="tasks.length > 0">
      <div v-for="(task, index) in tasks" :key="index" class="task-card">
        <div class="task-status" :class="task.priority"></div>
        <div class="task-content">
          <div class="task-title">{{ task.title }}</div>
          <div class="task-description">{{ task.description }}</div>
          <div class="task-meta">
            <span class="task-created">{{ formatTime(task.created_at) }}</span>
            <span class="task-due" v-if="task.due_date">Due: {{ formatDate(task.due_date) }}</span>
          </div>
        </div>
        <div class="task-actions">
          <button class="action-button complete-button" @click="completeTask(task.id)">
            <font-awesome-icon :icon="['fas', 'check']" />
            <span>Complete</span>
          </button>
        </div>
      </div>
    </div>
    
    <div class="empty-state" v-else>
      <font-awesome-icon :icon="['fas', 'clipboard-check']" class="empty-icon" />
      <div class="empty-text">No pending tasks</div>
      <div class="empty-subtext">You've completed all your tasks!</div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

export default {
  name: 'AgentTasksComponent',
  components: {
    FontAwesomeIcon
  },
  props: {
    tasks: {
      type: Array,
      default: () => []
    }
  },
  emits: ['refresh-tasks', 'complete-task'],
  setup(props, { emit }) {
    const isLoading = ref(false)
    
    const refreshTasks = () => {
      isLoading.value = true
      emit('refresh-tasks')
      setTimeout(() => {
        isLoading.value = false
      }, 1000)
    }
    
    const completeTask = (taskId) => {
      emit('complete-task', taskId)
    }
    
    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      
      const date = new Date(timestamp)
      return date.toLocaleString()
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return ''
      
      const date = new Date(dateString)
      return date.toLocaleDateString()
    }
    
    return {
      isLoading,
      refreshTasks,
      completeTask,
      formatTime,
      formatDate
    }
  }
}
</script>

<style scoped>
/* Styles for the tasks component */
</style>