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
const MobileAddStreamModal = () => import('../components/MobileAddStreamModal.vue');
const MobileMessageComponent = () => import('../components/MobileMessageComponent.vue');
const MobileAgentAnalytics = () => import('../components/MobileAgentAnalytics.vue');
const MobileAdminHome = () => import('../components/MobileAdminHome.vue');
const MobileCreateAccount = () => import('../components/MobileCreateAccount.vue');
const MobileAuthContainer = () => import('../components/MobileAuthContainer.vue');
const MobileAgentMessages = () => import('../components/MobileAgentMessages.vue');

// Define routes
const routes = [
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
  // Add other mobile components as needed
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router; 