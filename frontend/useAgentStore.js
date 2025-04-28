import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAgentStore = defineStore('agent', () => {
  const currentAgent = ref(null)
  const assignments = ref([])
  const notifications = ref([])

  const setAgent = (agentData) => {
    currentAgent.value = agentData
  }

  const setAssignments = (assignmentsData) => {
    assignments.value = assignmentsData
  }

  const addNotification = (notification) => {
    notifications.value.unshift(notification)
  }

  return {
    currentAgent,
    assignments,
    notifications,
    setAgent,
    setAssignments,
    addNotification
  }
})