<template>
  <div class="notification-preferences">
    <h2>Notification Preferences</h2>
    
    <div class="preference-section">
      <h3>Grouping</h3>
      <div class="preference-group">
        <div class="preference-option" 
             :class="{ 'active': isGroupedByType }" 
             @click="toggleGroupByType">
          <div class="option-icon">
            <font-awesome-icon icon="layer-group" />
          </div>
          <div class="option-content">
            <div class="option-title">Group by Type</div>
            <div class="option-description">Group notifications by event type (keyword, object, etc.)</div>
          </div>
          <div class="option-indicator">
            <div class="toggle" :class="{ 'on': isGroupedByType }">
              <div class="toggle-knob"></div>
            </div>
          </div>
        </div>
        
        <div class="preference-option" 
             :class="{ 'active': isGroupedByStream }" 
             @click="toggleGroupByStream">
          <div class="option-icon">
            <font-awesome-icon icon="stream" />
          </div>
          <div class="option-content">
            <div class="option-title">Group by Stream</div>
            <div class="option-description">Group notifications by stream source</div>
          </div>
          <div class="option-indicator">
            <div class="toggle" :class="{ 'on': isGroupedByStream }">
              <div class="toggle-knob"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="preference-section">
      <h3>Display</h3>
      <div class="preference-group">
        <div class="preference-option" 
             :class="{ 'active': showUnreadOnly }" 
             @click="toggleUnreadOnly">
          <div class="option-icon">
            <font-awesome-icon icon="bell" />
          </div>
          <div class="option-content">
            <div class="option-title">Show Unread Only</div>
            <div class="option-description">Only display unread notifications</div>
          </div>
          <div class="option-indicator">
            <div class="toggle" :class="{ 'on': showUnreadOnly }">
              <div class="toggle-knob"></div>
            </div>
          </div>
        </div>
        
        <div class="preference-option" 
             :class="{ 'active': autoRefresh }" 
             @click="toggleAutoRefresh">
          <div class="option-icon">
            <font-awesome-icon icon="sync" />
          </div>
          <div class="option-content">
            <div class="option-title">Auto Refresh</div>
            <div class="option-description">Automatically check for new notifications</div>
          </div>
          <div class="option-indicator">
            <div class="toggle" :class="{ 'on': autoRefresh }">
              <div class="toggle-knob"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="preference-section">
      <h3>Types</h3>
      <div class="preference-group">
        <div v-for="type in notificationTypes" 
             :key="type.id" 
             class="preference-option" 
             :class="{ 'active': type.enabled }" 
             @click="toggleNotificationType(type.id)">
          <div class="option-icon" :style="{ color: type.color }">
            <font-awesome-icon :icon="type.icon" />
          </div>
          <div class="option-content">
            <div class="option-title">{{ type.name }}</div>
            <div class="option-description">{{ type.description }}</div>
          </div>
          <div class="option-indicator">
            <div class="toggle" :class="{ 'on': type.enabled }">
              <div class="toggle-knob"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="preference-footer">
      <button class="save-btn" @click="savePreferences">Save Preferences</button>
      <button class="reset-btn" @click="resetPreferences">Reset to Default</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useMobileNotifications } from '../composables/useMobileNotifications';
import { useToast } from 'vue-toastification';

export default {
  name: 'MobileNotificationPreferences',
  setup() {
    // Get notification helpers from composable
    const { isGroupedByType, isGroupedByStream, toggleGroupByType, toggleGroupByStream } = useMobileNotifications();
    
    // Local states
    const showUnreadOnly = ref(false);
    const autoRefresh = ref(true);
    const notificationTypes = ref([
      {
        id: 'keyword_detected',
        name: 'Keyword Alerts',
        description: 'Notifications when keywords are detected in chat',
        icon: 'comment-dots',
        color: 'var(--light-danger)',
        enabled: true
      },
      {
        id: 'object_detected',
        name: 'Object Detection',
        description: 'Notifications when objects are detected in stream',
        icon: 'eye',
        color: 'var(--light-warning)',
        enabled: true
      },
      {
        id: 'stream_started',
        name: 'Stream Started',
        description: 'Notifications when streams go live',
        icon: 'video',
        color: 'var(--light-success)',
        enabled: true
      },
      {
        id: 'stream_ended',
        name: 'Stream Ended',
        description: 'Notifications when streams end',
        icon: 'video-slash',
        color: 'var(--light-secondary)',
        enabled: true
      },
      {
        id: 'assignment_created',
        name: 'Assignment Created',
        description: 'Notifications for new stream assignments',
        icon: 'user-check',
        color: 'var(--light-info)',
        enabled: true
      },
      {
        id: 'assignment_removed',
        name: 'Assignment Removed',
        description: 'Notifications when you are unassigned from streams',
        icon: 'user-times',
        color: 'var(--light-danger)',
        enabled: true
      }
    ]);
    
    const toast = useToast();
    
    // Toggle unread only
    const toggleUnreadOnly = () => {
      showUnreadOnly.value = !showUnreadOnly.value;
    };
    
    // Toggle auto refresh
    const toggleAutoRefresh = () => {
      autoRefresh.value = !autoRefresh.value;
    };
    
    // Toggle notification type
    const toggleNotificationType = (typeId) => {
      const type = notificationTypes.value.find(t => t.id === typeId);
      if (type) {
        type.enabled = !type.enabled;
      }
    };
    
    // Save preferences
    const savePreferences = () => {
      try {
        // Build preferences object
        const preferences = {
          grouping: {
            byType: isGroupedByType.value,
            byStream: isGroupedByStream.value
          },
          display: {
            unreadOnly: showUnreadOnly.value,
            autoRefresh: autoRefresh.value
          },
          types: {}
        };
        
        // Add enabled state for each notification type
        notificationTypes.value.forEach(type => {
          preferences.types[type.id] = type.enabled;
        });
        
        // Save to localStorage
        localStorage.setItem('notificationPreferences', JSON.stringify(preferences));
        
        toast.success('Preferences saved');
      } catch (error) {
        console.error('Failed to save preferences:', error);
        toast.error('Failed to save preferences');
      }
    };
    
    // Reset preferences
    const resetPreferences = () => {
      // Reset grouping
      if (isGroupedByType.value) toggleGroupByType();
      if (isGroupedByStream.value) toggleGroupByStream();
      
      // Reset local states
      showUnreadOnly.value = false;
      autoRefresh.value = true;
      
      // Reset notification types
      notificationTypes.value.forEach(type => {
        type.enabled = true;
      });
      
      // Remove from localStorage
      localStorage.removeItem('notificationPreferences');
      
      toast.info('Preferences reset to default');
    };
    
    // Load saved preferences on mount
    onMounted(() => {
      try {
        const savedPreferences = localStorage.getItem('notificationPreferences');
        
        if (savedPreferences) {
          const preferences = JSON.parse(savedPreferences);
          
          // Restore grouping settings
          if (preferences.grouping) {
            if (preferences.grouping.byType && !isGroupedByType.value) toggleGroupByType();
            if (preferences.grouping.byStream && !isGroupedByStream.value) toggleGroupByStream();
          }
          
          // Restore display settings
          if (preferences.display) {
            showUnreadOnly.value = preferences.display.unreadOnly || false;
            autoRefresh.value = preferences.display.autoRefresh !== false; // default to true
          }
          
          // Restore notification type settings
          if (preferences.types) {
            notificationTypes.value.forEach(type => {
              if (preferences.types[type.id] !== undefined) {
                type.enabled = preferences.types[type.id];
              }
            });
          }
        }
      } catch (error) {
        console.error('Failed to load preferences:', error);
      }
    });
    
    return {
      isGroupedByType,
      isGroupedByStream,
      showUnreadOnly,
      autoRefresh,
      notificationTypes,
      toggleGroupByType,
      toggleGroupByStream,
      toggleUnreadOnly,
      toggleAutoRefresh,
      toggleNotificationType,
      savePreferences,
      resetPreferences
    };
  }
};
</script>

<style scoped>
.notification-preferences {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 20px;
  color: var(--light-text);
  font-size: 1.5rem;
  font-weight: 600;
}

[data-theme='dark'] h2 {
  color: var(--dark-text);
}

.preference-section {
  margin-bottom: 25px;
}

h3 {
  margin-bottom: 12px;
  color: var(--light-text);
  font-size: 1.1rem;
  font-weight: 600;
  border-bottom: 1px solid var(--light-border);
  padding-bottom: 8px;
}

[data-theme='dark'] h3 {
  color: var(--dark-text);
  border-bottom-color: var(--dark-border);
}

.preference-group {
  background-color: var(--light-card-bg);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px var(--light-shadow);
}

[data-theme='dark'] .preference-group {
  background-color: var(--dark-card-bg);
  box-shadow: 0 2px 4px var(--dark-shadow);
}

.preference-option {
  display: flex;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid var(--light-border);
  cursor: pointer;
  transition: background-color 0.2s ease;
}

[data-theme='dark'] .preference-option {
  border-bottom-color: var(--dark-border);
}

.preference-option:last-child {
  border-bottom: none;
}

.preference-option:hover {
  background-color: var(--light-hover);
}

[data-theme='dark'] .preference-option:hover {
  background-color: var(--dark-hover);
}

.preference-option.active {
  background-color: rgba(66, 153, 225, 0.05);
}

[data-theme='dark'] .preference-option.active {
  background-color: rgba(99, 179, 237, 0.05);
}

.option-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(66, 153, 225, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  color: var(--light-primary);
}

[data-theme='dark'] .option-icon {
  background-color: rgba(99, 179, 237, 0.1);
  color: var(--dark-primary);
}

.option-content {
  flex: 1;
  min-width: 0;
}

.option-title {
  font-weight: 500;
  margin-bottom: 4px;
  color: var(--light-text);
}

[data-theme='dark'] .option-title {
  color: var(--dark-text);
}

.option-description {
  font-size: 0.85rem;
  color: var(--light-text-secondary);
}

[data-theme='dark'] .option-description {
  color: var(--dark-text-secondary);
}

.option-indicator {
  flex-shrink: 0;
  margin-left: 15px;
}

.toggle {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background-color: var(--light-hover);
  position: relative;
  transition: background-color 0.3s ease;
}

[data-theme='dark'] .toggle {
  background-color: var(--dark-hover);
}

.toggle.on {
  background-color: var(--light-primary);
}

[data-theme='dark'] .toggle.on {
  background-color: var(--dark-primary);
}

.toggle-knob {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: white;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.3s ease;
}

.toggle.on .toggle-knob {
  transform: translateX(20px);
}

.preference-footer {
  margin-top: 25px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.save-btn {
  padding: 10px 20px;
  background-color: var(--light-primary);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

[data-theme='dark'] .save-btn {
  background-color: var(--dark-primary);
}

.save-btn:hover {
  background-color: var(--light-primary-dark, #3182ce);
}

[data-theme='dark'] .save-btn:hover {
  background-color: var(--dark-primary-light, #90cdf4);
}

.reset-btn {
  padding: 10px 20px;
  background-color: transparent;
  color: var(--light-text-secondary);
  border: 1px solid var(--light-border);
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

[data-theme='dark'] .reset-btn {
  color: var(--dark-text-secondary);
  border-color: var(--dark-border);
}

.reset-btn:hover {
  background-color: var(--light-hover);
  color: var(--light-text);
}

[data-theme='dark'] .reset-btn:hover {
  background-color: var(--dark-hover);
  color: var(--dark-text);
}
</style>