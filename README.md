# Mobile Monitoring Platform

A mobile-first moderation platform designed for dynamic, responsive content management with advanced real-time notification capabilities and robust backend infrastructure.

## Project Overview

This Vue 3 application, paired with a powerful Flask backend, is built for modern browsers and mobile devices, providing a responsive interface for content moderation, stream monitoring, and user management. The platform features real-time notifications, user authentication, advanced stream detection, and comprehensive administrative tools.

## Key Features

- 📱 **Mobile-First Design**: Optimized for touch interaction with responsive layouts for various screen sizes.
- 🔔 **Real-Time Notifications**: Instant updates on detections, messages, and system events.
- 🔐 **Secure Authentication**: JWT-based authentication with password recovery and user role management.
- 🎨 **Theme Switching**: Seamless transition between dark and light modes for user comfort.
- 📊 **Dashboard Analytics**: Detailed insights into stream activity, agent performance, and system health.
- 🖼️ **Stream Monitoring & Management**: Real-time monitoring of multiple streaming platforms with automated detection.
- 💬 **Messaging System**: Internal communication tool for agents and administrators.
- 🔍 **Advanced Detection**: AI-powered detection of flagged content using YOLOv9c for image analysis.
- 🌐 **WebSocket Integration**: Real-time data exchange for live updates and interactions.
- 🛡️ **SSL Security**: Secure connections with configurable SSL certificates for database and server communications.
- 📁 **File Management**: Handling of uploads and attachments within the messaging system.
- 🌍 **Multi-Platform Support**: Integration with platforms like Chaturbate and Stripchat for stream management.

## Tech Stack

- **Frontend**: Vue 3 with Composition API, Vite for fast builds, and lazy loading for performance optimization.
- **Backend**: Flask with SQLAlchemy for ORM, Flask-SocketIO for real-time communication, and Flask-Migrate for database migrations.
- **Database**: PostgreSQL with SSL support for secure remote connections.
- **Authentication**: JWT-based auth with Flask-Login for session management.
- **Real-Time**: WebSocket integration via Flask-SocketIO for live data updates.
- **Styling**: Custom CSS with Bootstrap elements, supporting dark/light theme toggling.
- **AI/ML**: YOLOv9c model for object detection in streams.
- **Deployment**: Docker support with Gunicorn for production server deployment.

## Project Structure

### Frontend Components

#### Core Components
- `App.vue` - Main application component with global state management.
- `Dashboard.vue` & `AdminDashboard.vue` - Primary dashboards for desktop administrative views.
- `MobileAdminDashboard.vue` & `MobileAgentDashboard.vue` - Mobile-optimized dashboards for administrators and agents.

#### Mobile Components (Lazy Loaded for Performance)
- `MobileAdminStreams.vue` & `MobileAgentStreams.vue` - Stream management interfaces.
- `MobileAdminAgents.vue` - Agent management for administrators.
- `MobileLogin.vue` & `MobileForgotPassword.vue` - Authentication screens.
- `MobileCreateAccount.vue` - User registration flow.
- `MobileAdminSettings.vue` & `MobileAgentSettings.vue` - Configuration panels.
- `MobileAdminNotifications.vue` & `MobileAgentNotifications.vue` - Notification management.
- `MobileAgentAnalytics.vue` - Performance metrics for agents.
- `MobileAdminHome.vue` - Landing page for admin mobile dashboard.
- `MobileAgentMessages.vue` - Messaging interface for agents.
- `MobileStreamCard.vue` & `MobileVideoPlayer.vue` - Stream visualization components.
- `MobileNavigationBar.vue` - Mobile navigation controls.
- Numerous other mobile-optimized components for modals, notifications, and UI elements.

#### Services & Utilities
- `AuthService.js` - Manages authentication flows and token handling.
- `StreamService.js` - Stream data fetching and management.
- `MobileNotificationService.js` - API for mobile-optimized notifications.
- `mobileDetector.js` - Device detection for responsive design.

#### Composables
- `useMobileNotifications.js` - Manages notification state and logic.
- `useIsMobile.js` - Helpers for responsive design decisions.

### Backend Structure

#### Core Modules
- `main.py` - Application entry point with migration handling on startup.
- `config.py` - Configuration management with SSL settings for secure database connections.
- `models.py` - Database models for users, streams, assignments, logs, and more.
- `monitoring.py` - Stream monitoring logic with Whisper integration for audio transcription.
- `detection.py` - AI-based detection mechanisms.
- `socket_events.py` - WebSocket event handlers for real-time updates.

#### Routes (API Endpoints)
- `/api/auth/*` - Authentication endpoints for login, registration, and password management.
- `/api/streams/*` - Stream CRUD operations and monitoring controls.
- `/api/notifications/*` - Notification delivery, marking, and management.
- `/api/messages/*` - Internal messaging system for user communication.
- `/api/dashboard/*` - Dashboard statistics and analytics data.
- `/api/agents/*` - Agent management and assignment handling.
- `/api/detections/*` - Detection event processing and logging.
- `/api/health/*` - System health checks.
- `/api/assignment/*` - Stream-agent assignment management.

#### Utilities & Additional Modules
- `ssl_utils.py` - SSL configuration for secure connections.
- `proxy_handler.py` - Proxy management for stream handling.
- `scraping.py` - Data scraping utilities for stream information.
- `notifications.py` & `messaging.py` - Notification and messaging logic.
- `db_init.py` & `drop_tables.py` - Database initialization and management scripts.

### Database Models

- **User**: Manages user accounts with roles (agent/admin), online status, and assignments.
- **Stream**: Polymorphic model for different streaming platforms (Chaturbate, Stripchat).
- **Assignment**: Links agents to streams for monitoring responsibilities.
- **Log** & **DetectionLog**: Records system events and detection incidents with image storage.
- **ChatKeyword** & **FlaggedObject**: Configuration for chat and visual detection triggers.
- **TelegramRecipient**: Integration for Telegram notifications.
- **ChatMessage** & **MessageAttachment**: Internal messaging with file attachment support.
- **PasswordResetToken**: Secure password recovery mechanism.

## Development Notes

### Mobile-First Design Principles
- **Touch Optimized**: Interfaces designed for touch interaction with larger tap targets.
- **Responsive Layouts**: Components adapt to various screen sizes with mobile-first CSS.
- **Bandwidth Conscious**: Lazy loading and optimized assets for low-bandwidth scenarios.

### Theme Switching
The application supports dynamic theme switching:
```javascript
// Theme state is managed in App.vue and provided to child components
const isDarkTheme = ref(localStorage.getItem('themePreference') === 'dark')

// Theme can be updated from any child component
provide('updateTheme', (isDark) => {
  isDarkTheme.value = isDark
})
```

### Notification System
Real-time notifications with advanced filtering:
```javascript
// From useMobileNotifications.js
const toggleGroupByType = () => {
  notifications.value.groupByType = !notifications.value.groupByType
  localStorage.setItem('groupNotificationsByType', notifications.value.groupByType)
}
```

### Database Migrations
Automatic Alembic migrations on startup to ensure schema consistency:
```python
# In main.py
def run_migrations(app):
    with app.app_context():
        try:
            current()  # Check current migration version
            upgrade()  # Apply any pending migrations
            app.logger.info('Database migrations applied successfully.')
        except Exception as e:
            app.logger.error(f'Failed to apply database migrations: {e}')
            raise
```

### Whisper Integration
Audio transcription with configurable settings for monitoring:
- Environment variables for model size, sample duration, and detection thresholds.
- Saving transcripts to a dedicated folder for analysis.

## Deployment Instructions

### SSL Certificate Setup
For production deployment, SSL certificates are managed as follows:
```bash
sudo cp /etc/letsencrypt/live/monitor-backend.jetcamstudio.com/fullchain.pem ./fullchain.pem
sudo cp /etc/letsencrypt/live/monitor-backend.jetcamstudio.com/privkey.pem ./privkey.pem

sudo chown ec2-user:ec2-user /home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend/fullchain.pem
sudo chown ec2-user:ec2-user /home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend/privkey.pem
sudo chmod 600 /home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend/fullchain.pem
sudo chmod 600 /home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend/privkey.pem
```

### Docker Support
A `Dockerfile` is provided for containerized deployment, and `gunicorn.service` for systemd integration.

## Future Enhancements

- **Offline Support**: Enhanced local storage caching for offline functionality.
- **Push Notifications**: Implementation of mobile browser push notifications.
- **Media Optimization**: Further compression and adaptive streaming for low-bandwidth environments.
- **AI Enhancements**: Expanding detection capabilities with additional models and algorithms.
- **Multi-Language Support**: Internationalization for broader accessibility.

## License

All rights reserved. This codebase is proprietary and confidential.
