import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import io from 'socket.io-client'

export function useMobileNotifications() {
  const toast = useToast()
  const notifications = ref([])
  const loading = ref(false)
  const unreadCount = ref(0)
  const isGroupedByType = ref(false)
  const isGroupedByStream = ref(false)
  const socket = ref(null);  // Should be declared in your composable scope

  const fetchNotifications = async () => {
    loading.value = true
    try {
      const response = await axios.get('/api/notifications', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      notifications.value = (response.data || []).map(n => ({
        ...n,
        read: n.read || false
      }))
      unreadCount.value = notifications.value.filter(n => !n.read).length
    } catch (error) {
      console.error('Error fetching notifications:', error)
      toast.error('Failed to load notifications')
    } finally {
      loading.value = false
    }
  }

  const markAsRead = async (notificationId) => {
    try {
      await axios.post(`/api/notifications/mark-read/${notificationId}`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.read = true
        unreadCount.value = notifications.value.filter(n => !n.read).length
      }
      toast.success('Notification marked as read')
    } catch (error) {
      console.error('Error marking notification as read:', error)
      toast.error('Failed to mark notification as read')
    }
  }

  const markAllAsRead = async () => {
    try {
      await axios.post('/api/notifications/mark-all-read', {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      notifications.value.forEach(n => (n.read = true))
      unreadCount.value = 0
      toast.success('All notifications marked as read')
    } catch (error) {
      console.error('Error marking all notifications as read:', error)
      toast.error('Failed to mark all notifications as read')
    }
  }

  const groupedNotifications = computed(() => {
    if (!isGroupedByType.value && !isGroupedByStream.value) return {}
    const grouped = {}
    notifications.value.forEach(notification => {
      const key = isGroupedByType.value ? notification.event_type : notification.room_url
      grouped[key] = grouped[key] || []
      grouped[key].push(notification)
    })
    return grouped
  })

  const toggleGroupByType = () => {
    isGroupedByType.value = !isGroupedByType.value
    if (isGroupedByType.value && isGroupedByStream.value) isGroupedByStream.value = false
  }

  const toggleGroupByStream = () => {
    isGroupedByStream.value = !isGroupedByStream.value
    if (isGroupedByStream.value && isGroupedByType.value) isGroupedByType.value = false
  }
 const setupSocket = () => {
    // Create the socket instance and assign to the ref
    socket.value = io(`   https://monitor-backend.jetcamstudio.com:5000/notifications`, {
        path: '/ws',
        transports: ['websocket', 'polling']
    });

    // Use socket.value to access the actual Socket.IO instance
    socket.value.on('connect', () => {
        console.log('Connected to Socket.IO notifications namespace');
        socket.value.emit('get_unread_notifications');
    });

    socket.value.on('notification', (data) => {
        notifications.value.unshift({
            ...data,
            read: false
        });
        unreadCount.value = notifications.value.filter(n => !n.read).length;
        toast.info(`New ${data.event_type.replace('_', ' ')} notification`);
    });

    socket.value.on('unread_notifications', ({ notifications: unread }) => {
        notifications.value = [...unread, ...notifications.value.filter(n => n.read)];
        unreadCount.value = unread.length;
    });

    socket.value.on('error', ({ message }) => {
        toast.error(message);
    });
};

  const disconnectSocket = () => {
    if (socket.value) {
        socket.value.disconnect();
    }
  }

  onMounted(() => {
    setupSocket()
    fetchNotifications()
  })

  onUnmounted(() => {
    disconnectSocket()
  })

  return {
    notifications,
    loading,
    unreadCount,
    groupedNotifications,
    isGroupedByType,
    isGroupedByStream,
    markAsRead,
    markAllAsRead,
    toggleGroupByType,
    toggleGroupByStream,
    fetchNotifications
  }
}