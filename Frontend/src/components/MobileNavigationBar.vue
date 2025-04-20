<template>
  <div class="mobile-navbar" :class="{ 'admin': userRole === 'admin' }">
    <div class="navbar-item" @click="navigate('dashboard')">
      <font-awesome-icon icon="tachometer-alt" />
      <span>Dashboard</span>
    </div>
    
    <div class="navbar-item" @click="navigate('streams')">
      <font-awesome-icon icon="video" />
      <span>Streams</span>
    </div>
    
    <div class="navbar-item" @click="toggleNotifications">
      <div class="icon-wrapper">
        <font-awesome-icon icon="bell" />
        <MobileNotificationBadge v-if="unreadCount > 0" :count="unreadCount" />
      </div>
      <span>Alerts</span>
    </div>
    
    <div class="navbar-item" @click="navigate('messages')">
      <div class="icon-wrapper">
        <font-awesome-icon icon="comment" />
        <MobileNotificationBadge v-if="unreadMessages > 0" :count="unreadMessages" />
      </div>
      <span>Messages</span>
    </div>
    
    <div class="navbar-item" @click="navigate('settings')">
      <font-awesome-icon icon="cog" />
      <span>Settings</span>
    </div>
  </div>
  
  <MobileNotificationsPanel 
    :is-open="showNotifications" 
    @close="showNotifications = false"
    @notification-click="handleNotificationClick" />
</template>

<script>
import { ref, inject, onMounted } from 'vue';
import axios from 'axios';
import MobileNotificationBadge from './MobileNotificationBadge.vue';
import MobileNotificationsPanel from './MobileNotificationsPanel.vue';

export default {
  name: 'MobileNavigationBar',
  components: {
    MobileNotificationBadge,
    MobileNotificationsPanel
  },
  props: {
    userRole: {
      type: String,
      default: 'agent'
    }
  },
  setup(props, { emit }) {
    const showNotifications = ref(false);
    const unreadMessages = ref(0);
    
    // Inject dependencies
    const unreadCount = inject('unreadNotifications');
    
    // Toggle notifications panel
    const toggleNotifications = () => {
      showNotifications.value = !showNotifications.value;
    };
    
    // Navigation handler
    const navigate = (route) => {
      emit('navigate', route);
    };
    
    // Handle notification click
    const handleNotificationClick = (notification) => {
      emit('notification-click', notification);
      showNotifications.value = false;
    };
    
    // Fetch unread messages count
    const fetchUnreadMessages = async () => {
      try {
        const response = await axios.get('/api/messages/unread/count');
        if (response.data.success) {
          unreadMessages.value = response.data.count || 0;
        }
      } catch (error) {
        console.error('Failed to fetch unread messages count:', error);
      }
    };
    
    // Initialize
    onMounted(() => {
      fetchUnreadMessages();
      
      // Set up a background refresh for message counts
      setInterval(() => {
        if (document.visibilityState === 'visible') {
          fetchUnreadMessages();
        }
      }, 60000); // Refresh every minute
    });
    
    return {
      showNotifications,
      unreadCount,
      unreadMessages,
      toggleNotifications,
      navigate,
      handleNotificationClick
    };
  }
};
</script>

<style scoped>
.mobile-navbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 60px;
  background-color: var(--light-card-bg);
  box-shadow: 0 -2px 10px var(--light-shadow);
  z-index: 100;
}

[data-theme='dark'] .mobile-navbar {
  background-color: var(--dark-card-bg);
  box-shadow: 0 -2px 10px var(--dark-shadow);
}

.navbar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  padding: 5px;
  cursor: pointer;
  color: var(--light-text-secondary);
  transition: color 0.2s ease, background-color 0.2s ease;
}

[data-theme='dark'] .navbar-item {
  color: var(--dark-text-secondary);
}

.navbar-item:hover, .navbar-item.active {
  color: var(--light-primary);
  background-color: var(--light-hover);
}

[data-theme='dark'] .navbar-item:hover, 
[data-theme='dark'] .navbar-item.active {
  color: var(--dark-primary);
  background-color: var(--dark-hover);
}

.navbar-item svg {
  font-size: 1.2rem;
  margin-bottom: 3px;
}

.navbar-item span {
  font-size: 0.7rem;
  font-weight: 500;
}

.icon-wrapper {
  position: relative;
  display: inline-block;
}

/* Admin specific styles */
.mobile-navbar.admin .navbar-item {
  color: var(--light-text-secondary);
}

[data-theme='dark'] .mobile-navbar.admin .navbar-item {
  color: var(--dark-text-secondary);
}

.mobile-navbar.admin .navbar-item:hover, 
.mobile-navbar.admin .navbar-item.active {
  color: var(--light-primary);
}

[data-theme='dark'] .mobile-navbar.admin .navbar-item:hover, 
[data-theme='dark'] .mobile-navbar.admin .navbar-item.active {
  color: var(--dark-primary);
}
</style>