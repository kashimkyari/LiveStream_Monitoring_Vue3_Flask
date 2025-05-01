# Mobile Notifications System

This document describes the mobile-optimized notification system implemented for the moderation platform. The system provides enhanced real-time notifications with grouping, filtering, and preferences, all designed for optimal mobile experience.

## Components Overview

### Services

- **MobileNotificationService.js**: Singleton service that handles real-time notification delivery, grouping, filtering, and caching.
  - Provides efficient data usage with local storage caching
  - Handles Socket.IO connection for real-time updates
  - Implements notification grouping by stream or event type
  - Manages user notification preferences

### Composables

- **useMobileNotifications.js**: Vue 3 composable that provides reactive access to notification data and actions
  - Exposes notifications state and methods for components
  - Handles adaptive refresh based on user activity
  - Provides notification filtering and grouping toggle functions

- **useRealTimeDetection.js**: Specialized composable for handling detection notifications
  - Optimized for real-time keyword and object detection alerts
  - Supports sound, toast notifications, and vibration
  - Prioritizes certain detection types

### UI Components

- **MobileNotificationBadge.vue**: Animated notification badge for navigation bar
  - Shows unread count
  - Animates when new notifications arrive
  - Scales for readability

- **MobileNotificationsPanel.vue**: Full notifications panel with grouping and details
  - Shows notification groups with expandable details
  - Displays notification time, source, and details
  - Provides actions for marking as read

- **MobileNotificationPreferences.vue**: Settings panel for notification preferences
  - Controls for grouping options
  - Filters for event types and platforms
  - Sound and vibration toggles

- **MobileDetectionNotification.vue**: Real-time toast notification for detections
  - Shows immediate alerts for important detections
  - Prioritizes certain detection types
  - Provides direct navigation to streams

- **MobileNavigationBar.vue**: Navigation bar with integrated notifications
  - Includes notification badge
  - Handles navigation between panels
  - Manages panel visibility

## Features

### Notification Grouping

The system supports two types of grouping:

1. **Group by Stream**: Groups notifications from the same streamer/room
   - Useful for monitoring specific streamers
   - Shows count of events per stream

2. **Group by Event Type**: Groups notifications of the same type
   - Useful for monitoring specific types of events (keywords, objects)
   - Shows count of each event type

### Notification Filtering

Users can filter notifications by:

- Event types (keyword_detected, object_detected, etc.)
- Platforms (chaturbate, stripchat)
- Streamers (coming in future update)

### Real-time Detection Notifications

The system provides enhanced real-time notifications for detections:

- Immediate delivery through Socket.IO
- Sound alerts (configurable)
- Vibration on mobile devices (configurable)
- Toast notifications
- Priority highlighting for important detections

### Data Efficiency

The mobile notification system is optimized for data efficiency:

- Local storage caching
- Adaptive refresh based on user activity
- Batched updates
- Configurable cache lifetime

## Usage in Components

```javascript
// In a Vue component
import { useMobileNotifications } from '@/composables/useMobileNotifications';

export default {
  setup() {
    const { 
      notifications, 
      unreadCount,
      loadNotifications,
      markAsRead,
      toggleGroupByType 
    } = useMobileNotifications();

    // Access notifications
    console.log(notifications.value);

    // Mark a notification as read
    markAsRead(123);

    // Toggle grouping
    toggleGroupByType();

    return { notifications, unreadCount };
  }
}
```

## Integration with Mobile Navigation

The notification system is integrated into the mobile navigation bar, providing:

- Unread count badge
- Quick access to notifications panel
- Real-time updates without page refresh

## Future Enhancements

Planned enhancements for the mobile notification system:

- Streamer-specific notification preferences
- Time-based notification filters (e.g., quiet hours)
- Enhanced offline support
- Notification history with search
- Custom notification sounds