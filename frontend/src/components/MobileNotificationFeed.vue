<template>
  <div class="notification-feed">
    <!-- Feed Header with Filter Button -->
    <div class="feed-header d-flex justify-content-between align-items-center">
      <h5 class="mb-0">{{ title }}</h5>
      <div>
        <button class="btn btn-sm btn-outline-secondary" @click="$emit('filter')">
          <i class="fas fa-filter"></i>
        </button>
        <button v-if="unreadCount > 0" class="btn btn-sm btn-primary ms-2" @click="markAllAsRead">
          Mark All Read
        </button>
      </div>
    </div>
    
    <!-- Filter Pills (if filters are active) -->
    <div v-if="hasActiveFilters" class="filter-pills d-flex flex-wrap gap-2 mt-2 mb-3">
      <div 
        v-for="eventType in activeFilters.eventTypes" 
        :key="`et-${eventType}`"
        class="filter-pill"
        @click="removeEventTypeFilter(eventType)"
      >
        <span class="pill-text">{{ formatEventType(eventType) }}</span>
        <i class="fas fa-times-circle ms-1"></i>
      </div>
      
      <div 
        v-for="platform in activeFilters.platforms" 
        :key="`p-${platform}`"
        class="filter-pill"
        @click="removePlatformFilter(platform)"
      >
        <span class="pill-text">{{ platform }}</span>
        <i class="fas fa-times-circle ms-1"></i>
      </div>
      
      <div 
        v-if="activeFilters.eventTypes.length > 0 || activeFilters.platforms.length > 0"
        class="filter-pill clear-all"
        @click="clearAllFilters"
      >
        <span class="pill-text">Clear All</span>
        <i class="fas fa-times-circle ms-1"></i>
      </div>
    </div>
    
    <!-- Loading Indicator -->
    <div v-if="isLoading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    
    <!-- Group By Toggle -->
    <div class="group-toggle d-flex justify-content-between align-items-center mb-3">
      <span class="text-muted small">Group notifications by:</span>
      <div class="btn-group btn-group-sm">
        <button 
          class="btn" 
          :class="preferences.groupByStream ? 'btn-primary' : 'btn-outline-secondary'"
          @click="toggleGroupByStream"
        >
          Stream
        </button>
        <button 
          class="btn" 
          :class="preferences.groupByType ? 'btn-primary' : 'btn-outline-secondary'"
          @click="toggleGroupByType"
        >
          Type
        </button>
        <button 
          class="btn" 
          :class="!preferences.groupByStream && !preferences.groupByType ? 'btn-primary' : 'btn-outline-secondary'"
          @click="setNoGrouping"
        >
          None
        </button>
      </div>
    </div>
    
    <!-- Notifications List with Pull-to-Refresh -->
    <div 
      ref="feedContainer"
      class="feed-container"
      @scroll="handleScroll"
    >
      <!-- Pull to Refresh Indicator -->
      <div 
        v-if="isPulling" 
        class="pull-indicator"
        :class="{ 'releasing': isReleasing, 'refreshing': isRefreshing }"
      >
        <i class="fas fa-sync-alt"></i>
        <span>{{ pullStatusText }}</span>
      </div>
      
      <!-- Feed Content -->
      <div class="feed-content" :style="{ transform: `translateY(${pullDistance}px)` }">
        <!-- Notifications -->
        <template v-if="notifications.length > 0">
          <div 
            v-for="notification in notifications" 
            :key="notification.id"
            class="notification-item"
            :class="{ 'unread': !notification.read, 'has-group': notification.group }"
            @click="handleNotificationClick(notification)"
          >
            <!-- Regular Notification -->
            <template v-if="!notification.group">
              <div class="notification-icon">
                <i :class="getNotificationIcon(notification.event_type)"></i>
              </div>
              
              <div class="notification-content">
                <div class="notification-header">
                  <strong>{{ formatEventType(notification.event_type) }}</strong>
                  <small class="notification-time">{{ formatTime(notification.timestamp) }}</small>
                </div>
                
                <div class="notification-details">
                  {{ getNotificationMessage(notification) }}
                </div>
                
                <div v-if="notification.streamer || notification.platform" class="notification-meta">
                  <span v-if="notification.streamer" class="notification-streamer">
                    {{ notification.streamer }}
                  </span>
                  <span v-if="notification.platform" class="notification-platform">
                    {{ notification.platform }}
                  </span>
                </div>
              </div>
            </template>
            
            <!-- Grouped Notification -->
            <template v-else>
              <div class="notification-icon">
                <i :class="getNotificationIcon(notification.event_type)"></i>
                <span class="group-count">{{ notification.groupCount }}</span>
              </div>
              
              <div class="notification-content">
                <div class="notification-header">
                  <strong>
                    {{ notification.groupType === 'stream' 
                      ? notification.streamer || getStreamerFromUrl(notification.room_url) 
                      : formatEventType(notification.event_type) }}
                  </strong>
                  <small class="notification-time">{{ formatTime(notification.timestamp) }}</small>
                </div>
                
                <div class="notification-details">
                  {{ getGroupMessage(notification) }}
                </div>
                
                <div v-if="!expandedGroups[notification.id]" class="group-toggle">
                  <button class="btn btn-sm btn-link p-0" @click.stop="expandGroup(notification.id)">
                    Show all {{ notification.groupCount }} notifications
                  </button>
                </div>
              </div>
            </template>
          </div>
          
          <!-- Expanded Group Items -->
          <div v-for="(notification, index) in notifications" :key="`exp-${notification.id}`">
            <div v-if="notification.group && expandedGroups[notification.id]" class="expanded-group">
              <div class="expanded-group-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                  {{ notification.groupType === 'stream' 
                    ? notification.streamer || getStreamerFromUrl(notification.room_url) 
                    : formatEventType(notification.event_type) }}
                </h6>
                <button class="btn btn-sm btn-link" @click="collapseGroup(notification.id)">
                  <i class="fas fa-chevron-up"></i>
                </button>
              </div>
              
              <div class="expanded-group-items">
                <div 
                  v-for="groupItem in notification.group" 
                  :key="groupItem.id"
                  class="notification-item sub-item"
                  :class="{ 'unread': !groupItem.read }"
                  @click="markAsRead(groupItem.id)"
                >
                  <div class="notification-icon small">
                    <i :class="getNotificationIcon(groupItem.event_type)"></i>
                  </div>
                  
                  <div class="notification-content">
                    <div class="notification-header">
                      <strong>{{ formatEventType(groupItem.event_type) }}</strong>
                      <small class="notification-time">{{ formatTime(groupItem.timestamp) }}</small>
                    </div>
                    
                    <div class="notification-details">
                      {{ getNotificationMessage(groupItem) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Load More Button -->
          <div v-if="hasMoreNotifications" class="text-center py-3">
            <button 
              class="btn btn-outline-primary" 
              @click="loadMoreNotifications"
              :disabled="isLoadingMore"
            >
              <span v-if="isLoadingMore" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              {{ isLoadingMore ? 'Loading...' : 'Load More' }}
            </button>
          </div>
        </template>
        
        <!-- Empty State -->
        <div v-else-if="!isLoading" class="text-center py-5 text-muted">
          <i class="fas fa-bell-slash fa-3x mb-3"></i>
          <p>No notifications</p>
          <button v-if="hasActiveFilters" class="btn btn-sm btn-outline-secondary" @click="clearAllFilters">
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useMobileNotifications } from '../composables/useMobileNotifications';
import { format, formatDistance } from 'date-fns';

export default {
  name: 'MobileNotificationFeed',
  
  props: {
    title: {
      type: String,
      default: 'Notifications'
    },
    limit: {
      type: Number,
      default: 20
    }
  },
  
  emits: ['filter'],
  
  setup(props) {
    const { 
      notifications, 
      unreadCount, 
      preferences,
      isLoading,
      loadNotifications,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      updatePreferences,
      recordInteraction
    } = useMobileNotifications();
    
    // Local state
    const expandedGroups = ref({});
    const feedContainer = ref(null);
    const currentPage = ref(1);
    const hasMoreNotifications = ref(true);
    const isLoadingMore = ref(false);
    
    // Pull to refresh state
    const isPulling = ref(false);
    const isReleasing = ref(false);
    const isRefreshing = ref(false);
    const pullDistance = ref(0);
    const pullStartY = ref(0);
    const pullThreshold = 60; // pixels
    const maxPullDistance = 100; // pixels
    
    // Pull to refresh status text
    const pullStatusText = computed(() => {
      if (isRefreshing.value) return 'Refreshing...';
      if (isReleasing.value) return 'Release to refresh';
      return 'Pull down to refresh';
    });
    
    // Check if there are active filters
    const hasActiveFilters = computed(() => {
      if (!preferences.value || !preferences.value.filters) return false;
      
      const { eventTypes = [], platforms = [] } = preferences.value.filters;
      return eventTypes.length > 0 || platforms.length > 0;
    });
    
    // Get active filters
    const activeFilters = computed(() => {
      if (!preferences.value || !preferences.value.filters) {
        return { eventTypes: [], platforms: [] };
      }
      
      return {
        eventTypes: preferences.value.filters.eventTypes || [],
        platforms: preferences.value.filters.platforms || []
      };
    });
    
    // Filter functions
    const removeEventTypeFilter = (eventType) => {
      const eventTypes = [...(preferences.value.filters?.eventTypes || [])];
      const index = eventTypes.indexOf(eventType);
      
      if (index > -1) {
        eventTypes.splice(index, 1);
        updateFilters({ eventTypes });
      }
    };
    
    const removePlatformFilter = (platform) => {
      const platforms = [...(preferences.value.filters?.platforms || [])];
      const index = platforms.indexOf(platform);
      
      if (index > -1) {
        platforms.splice(index, 1);
        updateFilters({ platforms });
      }
    };
    
    const clearAllFilters = () => {
      updateFilters({ eventTypes: [], platforms: [] });
    };
    
    const updateFilters = (filters) => {
      updatePreferences({
        filters: {
          ...preferences.value.filters,
          ...filters
        }
      });
      
      // Reset page and load notifications with new filters
      currentPage.value = 1;
      hasMoreNotifications.value = true;
      loadNotifications(true);
    };
    
    // Set grouping mode
    const setNoGrouping = () => {
      updatePreferences({
        groupByType: false,
        groupByStream: false
      });
    };
    
    // Load more notifications
    const loadMoreNotifications = async () => {
      if (isLoadingMore.value) return;
      
      isLoadingMore.value = true;
      recordInteraction();
      
      try {
        // In a real implementation, this would use a pagination API
        // For now, simulate loading more by incrementing the page
        currentPage.value++;
        
        // TODO: Implement actual pagination in the service
        // This is a placeholder for future implementation
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // For demo purposes, after page 3 we'll say there are no more notifications
        if (currentPage.value > 3) {
          hasMoreNotifications.value = false;
        }
      } catch (error) {
        console.error('Error loading more notifications:', error);
      } finally {
        isLoadingMore.value = false;
      }
    };
    
    // Pull to refresh handlers
    const handleTouchStart = (e) => {
      // Only enable pull to refresh when scrolled to top
      if (feedContainer.value.scrollTop > 0) return;
      
      pullStartY.value = e.touches[0].clientY;
      isPulling.value = true;
    };
    
    const handleTouchMove = (e) => {
      if (!isPulling.value) return;
      
      const touchY = e.touches[0].clientY;
      const diff = touchY - pullStartY.value;
      
      // Only allow pulling down, not up
      if (diff < 0) {
        pullDistance.value = 0;
        return;
      }
      
      // Apply resistance formula to make it harder to pull beyond maxPullDistance
      pullDistance.value = Math.min(maxPullDistance, diff * 0.5);
      
      // Set releasing state based on threshold
      isReleasing.value = pullDistance.value > pullThreshold;
    };
    
    const handleTouchEnd = () => {
      if (!isPulling.value) return;
      
      // If pulled past threshold, refresh
      if (isReleasing.value) {
        isRefreshing.value = true;
        pullDistance.value = pullThreshold; // Keep showing the refreshing indicator
        
        // Perform refresh
        loadNotifications(true).then(() => {
          // Reset states after small delay to show the refresh animation
          setTimeout(() => {
            isPulling.value = false;
            isReleasing.value = false;
            isRefreshing.value = false;
            pullDistance.value = 0;
          }, 1000);
        });
      } else {
        // If not pulled past threshold, reset
        isPulling.value = false;
        isReleasing.value = false;
        pullDistance.value = 0;
      }
    };
    
    // Handle notification click
    const handleNotificationClick = (notification) => {
      // If this is a grouped notification and not expanded, expand it
      if (notification.group && !expandedGroups.value[notification.id]) {
        expandGroup(notification.id);
        return;
      }
      
      // Otherwise mark as read
      markAsRead(notification.id);
      recordInteraction();
    };
    
    // Format time relative to now
    const formatTime = (timestamp) => {
      if (!timestamp) return '';
      
      const date = new Date(timestamp);
      const now = new Date();
      
      // If today, show time
      if (date.toDateString() === now.toDateString()) {
        return format(date, 'h:mm a');
      }
      
      // If within last 7 days, show relative time
      const diffDays = Math.floor((now - date) / (24 * 60 * 60 * 1000));
      if (diffDays < 7) {
        return formatDistance(date, now, { addSuffix: true });
      }
      
      // Otherwise show date
      return format(date, 'MMM d');
    };
    
    // Format event type from snake_case to Title Case
    const formatEventType = (type) => {
      if (!type) return 'Notification';
      
      return type
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    };
    
    // Get notification icon based on event type
    const getNotificationIcon = (eventType) => {
      const iconMap = {
        'stream_created': 'fas fa-video text-success',
        'keyword_detected': 'fas fa-comment-dots text-warning',
        'object_detected': 'fas fa-eye text-info',
        'stream_offline': 'fas fa-video-slash text-danger',
        'assignment_created': 'fas fa-user-plus text-primary',
        'assignment_removed': 'fas fa-user-minus text-secondary'
      };
      
      return iconMap[eventType] || 'fas fa-bell text-primary';
    };
    
    // Get readable message from notification
    const getNotificationMessage = (notification) => {
      if (!notification) return '';
      
      // Extract information from the notification
      const streamer = notification.streamer || notification.details?.streamer_name || 'Unknown';
      
      // Construct message based on event type
      switch (notification.event_type) {
        case 'stream_created':
          return `New stream started`;
        case 'keyword_detected':
          const keyword = notification.details?.keyword || 'keyword';
          return `"${keyword}" mentioned in stream`;
        case 'object_detected':
          const object = notification.details?.object || 'object';
          return `${object} detected in stream`;
        case 'stream_offline':
          return `Stream went offline`;
        case 'assignment_created':
          const agent = notification.details?.agent || 'An agent';
          return `${agent} assigned to stream`;
        case 'assignment_removed':
          return `Agent removed from stream`;
        default:
          return notification.details?.message || 'New notification';
      }
    };
    
    // Get group message
    const getGroupMessage = (notification) => {
      if (!notification || !notification.group) return '';
      
      if (notification.groupType === 'stream') {
        return `${notification.groupCount} notifications from this stream`;
      } else if (notification.groupType === 'eventType') {
        return `${notification.groupCount} ${formatEventType(notification.event_type).toLowerCase()} events`;
      }
      
      return `${notification.groupCount} notifications`;
    };
    
    // Extract streamer from URL
    const getStreamerFromUrl = (url) => {
      if (!url) return 'Unknown';
      
      try {
        const parts = url.split('/');
        return parts[parts.length - 1] || parts[parts.length - 2] || 'Unknown';
      } catch (error) {
        return 'Unknown';
      }
    };
    
    // Group expansion
    const expandGroup = (id) => {
      expandedGroups.value = { ...expandedGroups.value, [id]: true };
      recordInteraction();
    };
    
    const collapseGroup = (id) => {
      const updated = { ...expandedGroups.value };
      delete updated[id];
      expandedGroups.value = updated;
      recordInteraction();
    };
    
    // Handle container scroll for infinite loading
    const handleScroll = () => {
      if (!feedContainer.value || !hasMoreNotifications.value || isLoadingMore.value) return;
      
      const { scrollTop, scrollHeight, clientHeight } = feedContainer.value;
      
      // If scrolled near the bottom, load more
      if (scrollTop + clientHeight >= scrollHeight - 100) {
        loadMoreNotifications();
      }
    };
    
    // Set up event listeners
    onMounted(() => {
      // Load initial notifications
      loadNotifications();
      
      // Add touch event listeners for pull to refresh
      if (feedContainer.value) {
        feedContainer.value.addEventListener('touchstart', handleTouchStart);
        feedContainer.value.addEventListener('touchmove', handleTouchMove);
        feedContainer.value.addEventListener('touchend', handleTouchEnd);
      }
    });
    
    // Clean up event listeners
    onUnmounted(() => {
      if (feedContainer.value) {
        feedContainer.value.removeEventListener('touchstart', handleTouchStart);
        feedContainer.value.removeEventListener('touchmove', handleTouchMove);
        feedContainer.value.removeEventListener('touchend', handleTouchEnd);
      }
    });
    
    return {
      // State
      notifications,
      unreadCount,
      preferences,
      isLoading,
      expandedGroups,
      feedContainer,
      hasMoreNotifications,
      isLoadingMore,
      hasActiveFilters,
      activeFilters,
      isPulling,
      isReleasing, 
      isRefreshing,
      pullDistance,
      pullStatusText,
      
      // Methods
      loadNotifications,
      markAsRead,
      markAllAsRead,
      toggleGroupByType,
      toggleGroupByStream,
      setNoGrouping,
      loadMoreNotifications,
      handleScroll,
      handleNotificationClick,
      formatTime,
      formatEventType,
      getNotificationIcon,
      getNotificationMessage,
      getGroupMessage,
      getStreamerFromUrl,
      expandGroup,
      collapseGroup,
      removeEventTypeFilter,
      removePlatformFilter,
      clearAllFilters
    };
  }
};
</script>

<style scoped>
.notification-feed {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.feed-header {
  padding: 1rem;
  flex-shrink: 0;
}

.filter-pills {
  padding: 0 1rem;
  flex-shrink: 0;
}

.filter-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  background-color: var(--bs-primary-bg-subtle);
  color: var(--bs-primary);
  border-radius: 50px;
  font-size: 0.75rem;
  cursor: pointer;
}

.filter-pill.clear-all {
  background-color: var(--bs-tertiary-bg);
  color: var(--bs-secondary);
}

.group-toggle {
  padding: 0 1rem;
  flex-shrink: 0;
}

.feed-container {
  flex-grow: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  position: relative;
}

.pull-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  padding-bottom: 10px;
  font-size: 0.875rem;
  color: var(--bs-secondary);
  transform: translateY(-100%);
}

.pull-indicator i {
  margin-bottom: 5px;
}

.pull-indicator.releasing i {
  color: var(--bs-primary);
}

.pull-indicator.refreshing i {
  animation: spin 1s linear infinite;
  color: var(--bs-primary);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.feed-content {
  transition: transform 0.2s ease;
}

.notification-item {
  display: flex;
  padding: 1rem;
  border-bottom: 1px solid var(--bs-border-color);
  cursor: pointer;
  transition: background-color 0.2s;
}

.notification-item:active {
  background-color: var(--bs-primary-bg-subtle);
}

.notification-item.unread {
  background-color: rgba(var(--bs-primary-rgb), 0.1);
}

.notification-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bs-light);
  border-radius: 50%;
  margin-right: 1rem;
  position: relative;
  flex-shrink: 0;
}

.notification-icon i {
  font-size: 1.2rem;
}

.notification-icon .group-count {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: var(--bs-danger);
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-content {
  flex-grow: 1;
  overflow: hidden;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.notification-time {
  font-size: 0.75rem;
  color: var(--bs-secondary);
}

.notification-details {
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 0.25rem;
}

.notification-meta {
  display: flex;
  font-size: 0.75rem;
  color: var(--bs-secondary);
}

.notification-streamer {
  margin-right: 0.5rem;
}

.notification-platform {
  padding-left: 0.5rem;
  border-left: 1px solid var(--bs-border-color);
}

.expanded-group {
  background-color: var(--bs-tertiary-bg);
  border-bottom: 1px solid var(--bs-border-color);
}

.expanded-group-header {
  padding: 0.5rem 1rem;
  background-color: var(--bs-secondary-bg);
}

.expanded-group-items .notification-item {
  padding: 0.75rem 1rem 0.75rem 2rem;
}

.expanded-group-items .notification-icon.small {
  width: 30px;
  height: 30px;
}

.group-toggle {
  margin-top: 0.25rem;
  font-size: 0.75rem;
}
</style>