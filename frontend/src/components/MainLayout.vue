<template>
  <div class="main-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <font-awesome-icon icon="shield-alt" />
        </div>
        <h2>StreamSafe</h2>
      </div>
      
      <nav class="sidebar-nav">
        <router-link v-for="item in navItems" :key="item.path" :to="item.path">
          <font-awesome-icon :icon="item.icon" />
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      
      <button class="logout-btn" @click="$emit('logout')">
        <font-awesome-icon icon="sign-out-alt" />
        <span>Logout</span>
      </button>
    </aside>
    
    <main class="content">
      <AdminDashboard v-if="userRole === 'admin'" />
      <AgentDashboard v-else-if="userRole === 'agent'" />
      <!-- <DefaultDashboard v-else /> -->
    </main>
  </div>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import AdminDashboard from './AdminDashboard.vue'
import AgentDashboard from './AgentDashboard.vue'
// import DefaultDashboard from './DefaultDashboard.vue'

export default {
  name: 'MainLayout',
  components: { FontAwesomeIcon, AdminDashboard, AgentDashboard },
  props: {
    userRole: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      navItems: [
        { path: '/dashboard', icon: 'tachometer-alt', label: 'Dashboard' },
        { path: '/streams', icon: 'video', label: 'Streams' },
        { path: '/alerts', icon: 'bell', label: 'Alerts' },
        { path: '/reports', icon: 'chart-bar', label: 'Reports' },
        { path: '/settings', icon: 'cog', label: 'Settings' }
      ]
    }
  }
}
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  background-color: var(--bg-secondary);
  padding: 20px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-header .logo {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary);
  color: white;
  border-radius: 8px;
}

.sidebar-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.2s ease;
}

.sidebar-nav a:hover {
  background-color: rgba(var(--primary), 0.1);
  color: var(--primary);
}

.sidebar-nav a.router-link-exact-active {
  background-color: rgba(var(--primary), 0.2);
  color: var(--primary);
  font-weight: 500;
}

.sidebar-nav a svg {
  width: 18px;
  text-align: center;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-top: auto;
  border-radius: 8px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background-color: rgba(247, 37, 133, 0.1);
  color: var(--danger);
}

.content {
  flex: 1;
  padding: 30px;
  background-color: var(--bg-primary);
}

@media (max-width: 768px) {
  .sidebar {
    width: 200px;
    padding: 15px;
  }
  
  .content {
    padding: 20px;
  }
}

@media (max-width: 576px) {
  .main-layout {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    padding: 15px;
  }
  
  .sidebar-nav {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 15px;
  }
  
  .sidebar-nav a {
    padding: 8px 12px;
    font-size: 14px;
  }
  
  .logout-btn {
    margin-top: 15px;
  }
  
  .content {
    padding: 15px;
  }
}
</style>