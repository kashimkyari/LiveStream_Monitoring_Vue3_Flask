import { createRouter, createWebHistory } from 'vue-router';

// Lazy load components
const MobileAgentStreams = () => import('../components/MobileAgentStreams.vue');
const MobileAdminStreams = () => import('../components/MobileAdminStreams.vue');
const MobileAdminAgents = () => import('../components/MobileAdminAgents.vue');
const MobileAdminDashboard = () => import('../components/MobileAdminDashboard.vue');
const MobileLogin = () => import('../components/MobileLogin.vue');
const MobileAgentSettings = () => import('../components/MobileAgentSettings.vue');
const MobileAdminSettings = () => import('../components/MobileAdminSettings.vue');
const MobileAdminNotifications = () => import('../components/MobileAdminNotifications.vue');
const MobileAgentNotifications = () => import('../components/MobileAgentNotifications.vue');
const MobileAgentDashboard = () => import('../components/MobileAgentDashboard.vue');
const MobileForgotPassword = () => import('../components/MobileForgotPassword.vue');
const MobileAdminHome = () => import('../components/MobileAdminHome.vue');
const MobileCreateAccount = () => import('../components/MobileCreateAccount.vue');
const MobileAgentMessages = () => import('../components/MobileAgentMessages.vue');
const MobileAgentAnalytics = () => import('../components/MobileAgentAnalytics.vue');
const MobileAuthContainer = () => import('../components/MobileAuthContainer.vue');
const AdminDashboard = () => import('../components/AdminDashboard.vue');
const AgentDashboard = () => import('../components/AgentDashboard.vue');
const Login = () => import('../components/Login.vue');
const CreateAccount = () => import('../components/CreateAccount.vue');
const ForgotPassword = () => import('../components/ForgotPassword.vue');
const AdminMessageComponent = () => import('../components/AdminMessageComponent.vue');
const AgentMessageComponent = () => import('../components/AgentMessageComponent.vue');
const AdminNotificationsPage = () => import('../components/AdminNotificationsPage.vue');
const AgentNotificationsComponent = () => import('../components/AgentNotificationsComponent.vue');
const StreamsTab = () => import('../components/StreamsTab.vue');
const AgentStreamsComponent = () => import('../components/AgentStreamsComponent.vue');
const AgentsTab = () => import('../components/AgentsTab.vue');
const FlagSettingsPage = () => import('../components/FlagSettingsPage.vue');

// Define routes
const routes = [
  {
    path: '/',
    name: 'Login',
    component: MobileLogin,
    meta: { requiresAuth: false }
  },
  {
    path: '/admin-dashboard',
    name: 'AdminDashboard',
    component: MobileAdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/agent-dashboard',
    name: 'AgentDashboard',
    component: MobileAgentDashboard,
    meta: { requiresAuth: true, requiresAgent: true }
  },
  { path: '/agent/streams', component: MobileAgentStreams, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/admin/streams', component: MobileAdminStreams, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/agents', component: MobileAdminAgents, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/dashboard', component: MobileAdminDashboard, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/login', component: MobileLogin },
  { path: '/agent/settings', component: MobileAgentSettings, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/admin/settings', component: MobileAdminSettings, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/notifications', component: MobileAdminNotifications, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/agent/notifications', component: MobileAgentNotifications, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/agent/dashboard', component: MobileAgentDashboard, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/forgot-password', component: MobileForgotPassword },
  { path: '/admin/home', component: MobileAdminHome, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/create-account', component: MobileCreateAccount },
  { path: '/agent/messages', component: MobileAgentMessages, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/agent/analytics', component: MobileAgentAnalytics, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/auth', component: MobileAuthContainer },
  // Desktop or additional routes
  { path: '/desktop/admin/dashboard', component: AdminDashboard, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/desktop/agent/dashboard', component: AgentDashboard, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/desktop/login', component: Login },
  { path: '/desktop/create-account', component: CreateAccount },
  { path: '/desktop/forgot-password', component: ForgotPassword },
  { path: '/desktop/admin/messages', component: AdminMessageComponent, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/desktop/agent/messages', component: AgentMessageComponent, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/desktop/admin/notifications', component: AdminNotificationsPage, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/desktop/agent/notifications', component: AgentNotificationsComponent, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/desktop/admin/streams', component: StreamsTab, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/desktop/agent/streams', component: AgentStreamsComponent, meta: { requiresAuth: true, role: 'agent' } },
  { path: '/desktop/admin/agents', component: AgentsTab, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/desktop/admin/flag-settings', component: FlagSettingsPage, meta: { requiresAuth: true, role: 'admin' } },
  // Add other routes as needed for modals and smaller components if they are to be standalone pages
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Route guard to check user roles
const checkUserRole = (to, from, next) => {
  const userRole = localStorage.getItem('userRole')
  
  // If no role is set, redirect to login
  if (!userRole) {
    next('/')
    return
  }

  // Check if trying to access admin routes
  if (to.meta.requiresAdmin && userRole !== 'admin') {
    next('/agent-dashboard')
    return
  }

  // Check if trying to access agent routes
  if (to.meta.requiresAgent && userRole !== 'agent') {
    next('/admin-dashboard')
    return
  }

  next()
}

// Add the guard to all routes
router.beforeEach(checkUserRole)

export default router; 