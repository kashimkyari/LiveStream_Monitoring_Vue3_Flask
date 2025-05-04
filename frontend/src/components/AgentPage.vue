<template>
  <div class="agent-container">
    <header class="agent-header">
      <div class="header-content">
        <h1 class="page-title">Agent Portal</h1>
        <div class="user-actions">
          <div class="status-indicator online">
            <span class="status-dot"></span>
            <span class="status-text">Online</span>
          </div>
          <span class="username">{{ username }}</span>
          <button @click="logout" class="logout-button">Logout</button>
        </div>
      </div>
    </header>

    <main class="agent-content">
      <div class="sidebar">
        <nav class="nav-menu">
          <div class="nav-item active">
            <i class="nav-icon dashboard-icon"></i>
            <span>Dashboard</span>
          </div>
          <div class="nav-item">
            <i class="nav-icon tickets-icon"></i>
            <span>Tickets</span>
            <span class="badge">12</span>
          </div>
          <div class="nav-item">
            <i class="nav-icon chat-icon"></i>
            <span>Live Chat</span>
            <span class="badge">3</span>
          </div>
          <div class="nav-item">
            <i class="nav-icon knowledge-icon"></i>
            <span>Knowledge Base</span>
          </div>
          <div class="nav-item">
            <i class="nav-icon profile-icon"></i>
            <span>My Profile</span>
          </div>
        </nav>
      </div>

      <div class="main-panel">
        <div class="welcome-banner">
          <h2>Welcome back, {{ username }}!</h2>
          <p>You have 12 open tickets and 3 pending chat requests.</p>
        </div>

        <div class="quick-stats">
          <div class="stat-card">
            <div class="stat-icon tickets-stat"></div>
            <div class="stat-info">
              <h3>Open Tickets</h3>
              <p class="stat-value">12</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon resolution-stat"></div>
            <div class="stat-info">
              <h3>Avg. Resolution Time</h3>
              <p class="stat-value">1.8 hours</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon satisfaction-stat"></div>
            <div class="stat-info">
              <h3>Customer Satisfaction</h3>
              <p class="stat-value">94%</p>
            </div>
          </div>
        </div>

        <div class="tickets-section">
          <div class="section-header">
            <h3>Recent Tickets</h3>
            <button class="view-all-button">View All</button>
          </div>
          
          <div class="tickets-list">
            <div class="ticket-card urgent">
              <div class="ticket-priority" title="Urgent Priority"></div>
              <div class="ticket-info">
                <h4 class="ticket-title">Unable to access account after password reset</h4>
                <p class="ticket-meta">Ticket #1089 • James Wilson • 45 minutes ago</p>
              </div>
              <button class="ticket-action-btn">View</button>
            </div>
            
            <div class="ticket-card high">
              <div class="ticket-priority" title="High Priority"></div>
              <div class="ticket-info">
                <h4 class="ticket-title">Payment processing error on checkout page</h4>
                <p class="ticket-meta">Ticket #1088 • Maria Garcia • 1 hour ago</p>
              </div>
              <button class="ticket-action-btn">View</button>
            </div>
            
            <div class="ticket-card medium">
              <div class="ticket-priority" title="Medium Priority"></div>
              <div class="ticket-info">
                <h4 class="ticket-title">Cannot update shipping address</h4>
                <p class="ticket-meta">Ticket #1087 • Robert Johnson • 3 hours ago</p>
              </div>
              <button class="ticket-action-btn">View</button>
            </div>
            
            <div class="ticket-card low">
              <div class="ticket-priority" title="Low Priority"></div>
              <div class="ticket-info">
                <h4 class="ticket-title">Request for product feature information</h4>
                <p class="ticket-meta">Ticket #1086 • Sarah Brown • 5 hours ago</p>
              </div>
              <button class="ticket-action-btn">View</button>
            </div>
          </div>
        </div>
        <div class="streams-section">
          <div class="section-header">
            <h3>Assigned Streams</h3>
            <button class="view-all-button">View All</button>
          </div>
          
          <div class="streams-list">
            <div v-if="assignedStreams.length === 0" class="empty-state">
              <p>No streams assigned</p>
            </div>
            <div v-else v-for="stream in assignedStreams" :key="stream.id" class="stream-card">
              <div class="stream-info">
                <h4 class="stream-title">{{ stream.streamer_username }}</h4>
                <p class="stream-meta">{{ stream.platform }} • <a :href="stream.room_url" target="_blank">View Stream</a></p>
              </div>
              <button class="stream-action-btn">View Details</button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { useRouter } from 'vue-router';

export default {
  name: 'AgentPage',
  
  setup() {
    const router = useRouter();
    return { router };
  },
  
  data() {
    return {
      username: 'Agent Smith',
      assignedStreams: []
    };
  },
  
  created() {
    // Check if user has agent role
    const role = localStorage.getItem('userRole');
    if (role !== 'agent') {
      this.router.push('/login');
    }
  },
  
  methods: {
    logout() {
      localStorage.removeItem('userRole');
      this.router.push('/login');
    }
  }
};
</script>

<style scoped>
.agent-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #121212;
  color: #f0f0f0;
}

.agent-header {
  background-color: #1a1a1a;
  border-bottom: 1px solid #2d2d2d;
  padding: 16px 24px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: #f8f8f8;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-indicator.online .status-dot {
  background-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.status-indicator.online .status-text {
  color: #4CAF50;
}

.username {
  font-weight: 500;
  color: #b3b3b3;
}

.logout-button {
  background-color: transparent;
  color: #007bff;
  border: 1px solid #007bff;
  border-radius: 4px;
  padding: 8px 16px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-button:hover {
  background-color: rgba(0,123,255,0.1);
}

.agent-content {
  display: flex;
  flex: 1;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.sidebar {
  width: 220px;
  background-color: #1a1a1a;
  border-right: 1px solid #2d2d2d;
  padding: 24px 0;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-left: 3px solid transparent;
  position: relative;
}

.nav-item:hover {
  background-color: #252525;
}

.nav-item.active {
  background-color: #252525;
  border-left-color: #007bff;
}

.nav-icon {
  width: 20px;
  height: 20px;
  background-color: #6c757d;
  border-radius: 4px;
}

.badge {
  position: absolute;
  right: 24px;
  background-color: #ff5722;
  color: white;
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.main-panel {
  flex: 1;
  padding: 24px;
}

.welcome-banner {
  background: linear-gradient(135deg, #0e4429 0%, #006064 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.welcome-banner h2 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 1.5rem;
  color: #ffffff;
}

.welcome-banner p {
  margin: 0;
  color: rgba(255,255,255,0.8);
}

.quick-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background-color: #1e1e1e;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background-color: #252525;
}

.stat-info h3 {
  margin-top: 0;
  margin-bottom: 4px;
  font-size: 0.9rem;
  color: #b0b0b0;
  font-weight: 500;
}

.stat-value {
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0;
  color: #f8f8f8;
}

.tickets-section {
  background-color: #1e1e1e;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.streams-section {
  background-color: #1e1e1e;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  margin-top: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.view-all-button {
  background-color: transparent;
  color: #007bff;
  border: 1px solid #007bff;
  border-radius: 4px;
  padding: 8px 16px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-all-button:hover {
  background-color: rgba(0,123,255,0.1);
}

.tickets-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ticket-card {
  background-color: #252525;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.ticket-priority {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #6c757d;
}

.ticket-info {
  flex: 1;
}

.ticket-title {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 1rem;
  color: #f8f8f8;
}

.ticket-meta {
  margin: 0;
  color: rgba(255,255,255,0.8);
}

.ticket-action-btn {
  background-color: transparent;
  color: #007bff;
  border: 1px solid #007bff;
  border-radius: 4px;
  padding: 8px 16px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ticket-action-btn:hover {
  background-color: rgba(0,123,255,0.1);
}

.streams-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stream-card {
  background-color: #252525;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stream-info {
  flex: 1;
}

.stream-title {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 1rem;
  color: #f8f8f8;
}

.stream-meta {
  margin: 0;
  color: rgba(255,255,255,0.8);
}

.stream-action-btn {
  background-color: transparent;
  color: #007bff;
  border: 1px solid #007bff;
  border-radius: 4px;
  padding: 8px 16px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.stream-action-btn:hover {
  background-color: rgba(0,123,255,0.1);
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  color: rgba(255,255,255,0.8);
}

@media (max-width: 768px) {
  .admin-content {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #2d2d2d;
    padding: 16px 0;
  }
  
  .nav-menu {
    flex-direction: row;
    overflow-x: auto;
    padding: 0 16px;
  }
  
  .nav-item {
    padding: 8px 16px;
    border-left: none;
    border-bottom: 3px solid transparent;
  }
  
  .nav-item.active {
    border-left-color: transparent;
    border-bottom-color: #007bff;
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
  }
}
</style>