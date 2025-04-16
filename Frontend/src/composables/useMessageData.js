import { ref, computed, watch } from 'vue'
import axios from 'axios'

export function useMessageData(user) {
  const messages = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  
  // Calculate unread message count
  const messageUnreadCount = computed(() => {
    if (!messages.value) return 0
    return messages.value.filter(msg => !msg.read && msg.receiver_id === user.value?.id).length
  })
  
  // Fetch all messages for the current user
  const fetchMessages = async () => {
    if (!user.value) return
    
    isLoading.value = true
    error.value = null
    
    try {
      const response = await axios.get('/api/messages')
      messages.value = response.data
    } catch (err) {
      console.error('Error fetching messages:', err)
      error.value = err.message || 'Failed to fetch messages'
    } finally {
      isLoading.value = false
    }
  }
  
  // Mark a message as read
  const markAsRead = async (messageId) => {
    try {
      await axios.put(`/api/messages/${messageId}/mark-read`)
      // Update the local state
      const messageIndex = messages.value.findIndex(m => m.id === messageId)
      if (messageIndex !== -1) {
        messages.value[messageIndex].read = true
      }
    } catch (err) {
      console.error('Error marking message as read:', err)
    }
  }
  
  // Send a new message
  const sendMessage = async (receiverId, content) => {
    try {
      const response = await axios.post('/api/messages', {
        receiver_id: receiverId,
        message: content
      })
      // Add the new message to our local state
      messages.value.push(response.data)
      return response.data
    } catch (err) {
      console.error('Error sending message:', err)
      throw err
    }
  }
  
  // Watch for user changes and refresh messages
  watch(() => user.value, (newUser) => {
    if (newUser) {
      fetchMessages()
    }
  })
  
  return {
    messages,
    isLoading,
    error,
    messageUnreadCount,
    fetchMessages,
    markAsRead,
    sendMessage
  }
}