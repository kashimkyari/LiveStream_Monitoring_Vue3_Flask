# Mobile Monitoring Platform

A mobile-first moderation platform designed for dynamic, responsive content management with advanced real-time notification capabilities.

## Project Overview

This Vue 3 application is built for modern browsers and mobile devices, providing a responsive interface for content moderation and management. The platform features real-time notifications, user authentication, and stream monitoring capabilities.

## Key Features

- 📱 Mobile-first, responsive design
- 🔔 Real-time notification system
- 🔐 Advanced mobile authentication components
- 🎨 Theme switching (dark/light mode)
- 📊 Dashboard analytics
- 🖼️ Stream monitoring and management
- 💬 Messaging system

## Tech Stack

- **Frontend**: Vue 3 with Composition API
- **Backend**: Flask with SQLAlchemy
- **Database**: PostgreSQL
- **Authentication**: JWT-based auth with Flask-Login
- **Real-time**: Flask-SocketIO for real-time updates
- **Styling**: Bootstrap with custom dark theme

## Project Structure

### Vue Components

The src directory contains the following key components:

#### Core Components
- `App.vue` - Main application component with global state
- `Dashboard.vue` - Primary dashboard for desktop view
- `MobileAdminDashboard.vue` - Mobile-optimized dashboard for administrators
- `MobileAgentDashboard.vue` - Mobile-optimized dashboard for agents

#### Mobile Components
- `MobileHome.vue` - First tab component for mobile dashboards
- `MobileLogin.vue` - Mobile-optimized login screen
- `MobileForgotPassword.vue` - Password recovery flow
- `MobileCreateAccount.vue` - Registration flow
- `MobileNotificationsPanel.vue` - Notification management interface
- `MobileNotificationPreferences.vue` - User notification settings
- `MobileNotificationBadge.vue` - Real-time notification counter

#### Services
- `AuthService.js` - Handles authentication flows
- `StreamService.js` - Stream management functions
- `MobileNotificationService.js` - Mobile-optimized notification API
- `mobileDetector.js` - Device detection utilities

#### Composables
- `useMobileNotifications.js` - Notification state and methods
- `useIsMobile.js` - Responsive design helpers

### Routes

Backend routes defined in Flask:

- `/api/auth/*` - Authentication endpoints
- `/api/streams/*` - Stream management
- `/api/notifications/*` - Notification delivery and management
- `/api/messages/*` - Messaging system
- `/api/dashboard/*` - Dashboard statistics
- `/api/agents/*` - Agent management
- `/api/detections/*` - Detection processing

## Development Notes

### Mobile-First Design Principles

- Designed for touch interaction first
- Optimized for smaller screens with simplified layouts
- Bandwidth-conscious data loading

### Theme Switching

The application supports switching between dark and light themes:

```javascript
// Theme state is managed in App.vue and provided to child components
const isDarkTheme = ref(localStorage.getItem('themePreference') === 'dark')

// Theme can be updated from any child component
provide('updateTheme', (isDark) => {
  isDarkTheme.value = isDark
})
```

### Notification System

Real-time notifications with filtering capabilities:

```javascript
// From useMobileNotifications.js
const toggleGroupByType = () => {
  notifications.value.groupByType = !notifications.value.groupByType
  localStorage.setItem('groupNotificationsByType', notifications.value.groupByType)
}
```

## Future Enhancements

- Enhanced offline support with local storage caching
- Push notification support for mobile browsers
- Media optimization for low-bandwidth connections

## License

All rights reserved. This codebase is proprietary and confidential.



sudo cp /etc/letsencrypt/live/monitor-backend.jetcamstudio.com/fullchain.pem ./fullchain.pem
sudo cp /etc/letsencrypt/live/monitor-backend.jetcamstudio.com/privkey.pem ./privkey.pem

sudo chown ec2-user:ec2-user /home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend/fullchain.pem
sudo chown ec2-user:ec2-user /home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend/privkey.pem
sudo chmod 600 /home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend/fullchain.pem
sudo chmod 600 /home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend/privkey.pem
