import { ref, onUnmounted } from 'vue'
import { io } from 'socket.io-client'

export function useSocket() {
  const socket = ref(null)
  const isConnected = ref(false)
  
  const connect = () => {
    // Replace with your Socket.IO server URL
    socket.value = io('54.86.99.85:5000', {
      withCredentials: true,
      autoConnect: true
    })

    socket.value.on('connect', () => {
      isConnected.value = true
    })

    socket.value.on('disconnect', () => {
      isConnected.value = false
    })
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.disconnect()
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    connect,
    disconnect
  }
}