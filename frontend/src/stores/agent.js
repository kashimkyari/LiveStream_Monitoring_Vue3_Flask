import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAgentStore = defineStore('agent', () => {
  const currentAgent = ref(null)
  const assignments = ref([])
  const notifications = ref([])
  
  // Add a flag to track if initialization attempt was made
  const initialized = ref(false)
  
  // Modified to include initialization logic
  const setAgent = (agentData) => {
    currentAgent.value = agentData
    initialized.value = true
  }
  
  // New method to check if we have a valid agent
  const hasAgent = () => {
    return !!currentAgent.value && !!currentAgent.value.id
  }
  
  // New method to initialize with default agent if needed
  const initializeAgent = async () => {
    if (initialized.value) return
    
    // Mark as initialized to prevent multiple attempts
    initialized.value = true
    
    try {
      // Try to load default agent data from API or localStorage
      const savedAgentId = localStorage.getItem('lastAgentId')
      
      if (savedAgentId) {
        const response = await fetch(`/api/agents/${savedAgentId}`)
        if (response.ok) {
          const agentData = await response.json()
          currentAgent.value = agentData
          return
        }
      }
      
      // If no saved agent or fetch failed, try to get first available agent
      const response = await fetch('/api/agents')
      if (response.ok) {
        const agents = await response.json()
        if (agents.length > 0) {
          currentAgent.value = agents[0]
          localStorage.setItem('lastAgentId', agents[0].id)
        }
      }
    } catch (error) {
      console.error('Failed to initialize agent:', error)
    }
  }

  const setCurrentAgent = async (agentId) => {
    try {
      const response = await fetch(`/api/agents/${agentId}`)
      const data = await response.json()
      currentAgent.value = data
      if (data.assignments) {
        setAssignments(data.assignments)
      }
    } catch (error) {
      console.error('Error fetching agent:', error)
    }
  }
  
  const loadAgents = async () => {
    try {
      const response = await fetch('/api/agents')
      return await response.json()
    } catch (error) {
      console.error('Error loading agents:', error)
      return []
    }
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
    initialized,
    setAgent,
    setCurrentAgent,
    loadAgents,
    setAssignments,
    addNotification,
    hasAgent,
    initializeAgent
  }
})