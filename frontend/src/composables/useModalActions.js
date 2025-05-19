// src/composables/useModalActions.js
import { ref } from 'vue'
import axios from 'axios'

export function useModalActions(toast, fetchDashboardData) {
  // Modals
  const selectedStream = ref(null)
  const showCreateStreamModal = ref(false)
  const showCreateAgentModal = ref(false)
  const confirmationModal = ref({
    show: false,
    title: '',
    message: '',
    action: null,
    actionText: 'Confirm'
  })
  
  // Stream creation state
  const streamCreationState = ref({
    isSubmitting: false,
    progress: 0,
    progressMessage: '',
    jobId: null,
    estimatedTime: 0,
    error: null,
    submitSuccess: false,
    submitError: false
  })
  
  // Stream methods
  const openStreamDetails = (stream) => {
    selectedStream.value = stream
  }
  
const closeModal = () => {
  selectedStream.value = null
  
  // Clean up any active SSE connections or polling intervals
  cleanupStreamCreation()
  
  // Reset stream creation state
  streamCreationState.value = {
    isSubmitting: false,
    progress: 0,
    progressMessage: '',
    jobId: null,
    estimatedTime: 0,
    error: null,
    submitSuccess: false,
    submitError: false,
    eventSource: null,
    pollInterval: null
  }
}
  
const subscribeToProgress = (jobId) => {
  // Add a timeout to detect initial connection failure
  let connectionEstablished = false
  const connectionTimeout = setTimeout(() => {
    if (!connectionEstablished) {
      streamCreationState.value.submitError = true
      streamCreationState.value.error = 'Connection timed out. Stream may still be creating.'
      streamCreationState.value.isSubmitting = false
      
      if (eventSource) {
        eventSource.close()
      }
      
      // Fall back to polling for status
      startPollingForStatus(jobId)
    }
  }, 5000) // 5 second timeout
  
  const eventSource = new EventSource(`/api/streams/interactive/sse?job_id=${jobId.value}`)
  
  // Handle connection open
  eventSource.onopen = () => {
    connectionEstablished = true
    clearTimeout(connectionTimeout)
    console.log('SSE connection established')
  }
  
  eventSource.onmessage = (e) => {
    connectionEstablished = true
    clearTimeout(connectionTimeout)
    
    try {
      const data = JSON.parse(e.data)
      streamCreationState.value.progress = data.progress
      streamCreationState.value.progressMessage = data.message
      streamCreationState.value.estimatedTime = data.estimated_time || 0
      
      if (data.progress >= 100) {
        if (data.error) {
          streamCreationState.value.submitError = true
          streamCreationState.value.error = data.error
        } else {
          streamCreationState.value.submitSuccess = true
        }
        eventSource.close()
        
        // If successful, refresh dashboard data to show the new stream
        if (!data.error) {
          fetchDashboardData()
          toast.success('Stream created successfully')
          showCreateStreamModal.value = false
        }
      }
    } catch (error) {
      console.error('Error parsing SSE data:', error)
      // Continue listening - don't close the connection on parse error
    }
  }
  
  eventSource.onerror = (err) => {
    console.error("SSE error:", err)
    
    // Only handle if we haven't already fallen back to polling
    if (connectionEstablished) {
      // Try reconnecting once
      if (eventSource.readyState === EventSource.CLOSED) {
        connectionEstablished = false
        startPollingForStatus(jobId)
        eventSource.close()
      }
    }
  }
  
  // Store the event source for cleanup
  streamCreationState.value.eventSource = eventSource
}

// Add a polling fallback when SSE fails
const startPollingForStatus = (jobId) => {
  console.log('Falling back to polling for job status:', jobId)
  
  const pollInterval = setInterval(async () => {
    try {
      const response = await axios.get(`/api/streams/interactive/status?job_id=${jobId.value}`)
      const data = response.data
      
      streamCreationState.value.progress = data.progress
      streamCreationState.value.progressMessage = data.message || 'Processing...'
      
      if (data.progress >= 100 || data.error) {
        clearInterval(pollInterval)
        
        if (data.error) {
          streamCreationState.value.submitError = true
          streamCreationState.value.error = data.error
        } else {
          streamCreationState.value.submitSuccess = true
          fetchDashboardData()
          toast.success('Stream created successfully')
          showCreateStreamModal.value = false
        }
      }
    } catch (error) {
      console.error('Error polling for status:', error)
      // Don't stop polling on error, but after 5 minutes we should give up
      if (Date.now() - streamCreationState.value.startTime > 30000) {
        clearInterval(pollInterval)
        streamCreationState.value.submitError = true
        streamCreationState.value.error = 'Status updates timed out. Please check the streams list to see if creation was successful.'
      }
    }
  }, 15000) // Poll every 3 seconds
  
  // Store the interval ID for cleanup
  streamCreationState.value.pollInterval = pollInterval
}

// Add cleanup function
const cleanupStreamCreation = () => {
  if (streamCreationState.value.eventSource) {
    streamCreationState.value.eventSource.close()
    streamCreationState.value.eventSource = null
  }
  
  if (streamCreationState.value.pollInterval) {
    clearInterval(streamCreationState.value.pollInterval)
    streamCreationState.value.pollInterval = null
  }
}
  
const createStream = async (streamData) => {
  try {
    // Cleanup any existing connections/intervals
    cleanupStreamCreation()
    
    // Reset state
    streamCreationState.value = {
      isSubmitting: true,
      progress: 0,
      progressMessage: 'Initializing...',
      jobId: null,
      estimatedTime: 0,
      error: null,
      submitError: false,
      submitSuccess: false,
      startTime: Date.now(),
      eventSource: null,
      pollInterval: null
    }
    
    // Ensure we have valid data to work with
    if (!streamData || !streamData.room_url) {
      throw new Error('Invalid stream data provided')
    }
    
    // Determine platform from URL if not explicitly set
    if (!streamData.platform) {
      if (streamData.room_url.toLowerCase().includes('stripchat.com')) {
        streamData.platform = 'stripchat'
      } else {
        streamData.platform = 'chaturbate'
      }
    }
    
    console.log('Creating stream with data:', streamData)
    
    // Use interactive stream creation API endpoint
    const response = await axios.post('/api/streams/interactive', streamData)
    
    if (response.data && response.data.job_id) {
      streamCreationState.value.jobId = response.data.job_id
      subscribeToProgress(response.data.job_id)
    } else {
      // Fallback to non-interactive if job_id is not returned
      await handleLegacyStreamCreation(streamData)
    }
  } catch (error) {
    console.error('Failed to create stream:', error)
    streamCreationState.value.error = error.response?.data?.message || 'Failed to start stream creation'
    streamCreationState.value.submitError = true
    streamCreationState.value.isSubmitting = false
    toast.error('Failed to create stream')
  }
}
  
  // Fallback method for legacy API without progress tracking
  const handleLegacyStreamCreation = async (streamData) => {
    try {
      const response = await axios.post('/api/streams', streamData)
      if (response.status === 201) {
        showCreateStreamModal.value = false
        fetchDashboardData()
        toast.success('Stream created successfully')
        streamCreationState.value.submitSuccess = true
      }
    } catch (error) {
      console.error('Failed to create stream (legacy method):', error)
      streamCreationState.value.error = error.response?.data?.message || 'Failed to create stream'
      streamCreationState.value.submitError = true
      toast.error('Failed to create stream')
    } finally {
      streamCreationState.value.isSubmitting = false
    }
  }
  
  const assignAgent = async (stream) => {
    try {
      confirmationModal.value = {
        show: true,
        title: 'Assign Agent',
        message: 'Please select an agent to assign:',
        action: async (agentId) => {
          if (!agentId) {
            toast.error('Please select an agent!')
            return
          }
          
          await axios.post('/api/assign', {
            agent_id: agentId,
            stream_id: stream.id
          })
          fetchDashboardData()
          closeModal()
          toast.success('Agent assigned successfully')
        },
        actionText: 'Assign'
      }
    } catch (error) {
      console.error('Failed to assign agent:', error)
      toast.error('Failed to assign agent')
    }
  }
  
  const editStream = () => {
    toast.info('Edit stream functionality would go here')
  }
  
  const confirmDeleteStream = (stream) => {
    confirmationModal.value = {
      show: true,
      title: 'Delete Stream',
      message: `Are you sure you want to delete the stream for ${stream.streamer_username}?`,
      action: () => deleteStream(stream),
      actionText: 'Delete'
    }
  }
  
  const deleteStream = async (stream) => {
    try {
      await axios.delete(`/api/streams/${stream.id}`)
      confirmationModal.value.show = false
      fetchDashboardData()
      toast.success('Stream deleted successfully')
    } catch (error) {
      console.error('Failed to delete stream:', error)
      toast.error('Failed to delete stream')
    }
  }
  
  // Agent methods
  const createAgent = async (agentData) => {
    try {
      const response = await axios.post('/api/agents', agentData)
      if (response.status === 201) {
        showCreateAgentModal.value = false
        fetchDashboardData()
        toast.success('Agent created successfully')
      }
    } catch (error) {
      console.error('Failed to create agent:', error)
      toast.error('Failed to create agent')
    }
  }
  
  const editAgent = () => {
    toast.info('Edit agent functionality would go here')
  }
  
  const confirmDeleteAgent = (agent) => {
    confirmationModal.value = {
      show: true,
      title: 'Delete Agent',
      message: `Are you sure you want to delete agent ${agent.username}?`,
      action: () => deleteAgent(agent),
      actionText: 'Delete'
    }
  }
  
  const deleteAgent = async (agent) => {
    try {
      await axios.delete(`/api/agents/${agent.id}`)
      confirmationModal.value.show = false
      fetchDashboardData()
      toast.success('Agent deleted successfully')
    } catch (error) {
      console.error('Failed to delete agent:', error)
      toast.error('Failed to delete agent')
    }
  }
  
  const confirmAction = () => {
    if (confirmationModal.value.action) {
      confirmationModal.value.action()
    }
    confirmationModal.value.show = false
  }
  
  return {
    selectedStream,
    showCreateStreamModal,
    showCreateAgentModal,
    confirmationModal,
    streamCreationState,
    openStreamDetails,
    closeModal,
    assignAgent,
    createStream,
    editStream,
    confirmDeleteStream,
    deleteStream,
    createAgent,
    editAgent,
    confirmDeleteAgent,
    deleteAgent,
    confirmAction
  }
}