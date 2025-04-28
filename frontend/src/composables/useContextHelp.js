/**
 * Context-Aware Help Bubbles Composable
 * 
 * Provides intelligent, context-sensitive help bubbles that appear based on:
 * - Current user action
 * - Application state
 * - User experience level
 * - Previous interactions
 */
import { ref, /* computed, */ watch, onMounted, onUnmounted } from 'vue';
import { useToast } from 'vue-toastification'; // eslint-disable-line no-unused-vars

export function useContextHelp() {
  // State
  const helpVisible = ref(false);
  const helpContent = ref({
    title: '',
    message: '',
    type: 'info', // info, tip, warning
    position: 'bottom', // top, right, bottom, left
    context: '', // which feature this help relates to
    actionButtons: [] // array of { label, action } objects
  });
  const helpHistory = ref([]); // keep track of which help bubbles the user has seen
  const helpDismissed = ref({}); // track which help bubbles user has dismissed
  const userActivity = ref({
    lastAction: null,
    lastScreen: null,
    idleTime: 0
  });
  const helpQueue = ref([]); // Queue for multiple help bubbles

  // Initialize toast for notifications (will be used in future enhancements)
  const toast = useToast(); // eslint-disable-line no-unused-vars
  
  // Track idle time
  let idleTimer = null;
  
  // Define the help content library
  const helpLibrary = {
    // Authentication related help
    'auth-login': {
      title: 'Login Help',
      message: 'Enter your username and password to access the dashboard.',
      type: 'info',
      position: 'bottom',
      priority: 1
    },
    'auth-error': {
      title: 'Authentication Failed',
      message: 'There was a problem with your login. Please check your credentials and try again.',
      type: 'warning',
      position: 'bottom',
      priority: 0 // highest priority
    },
    // Navigation related help
    'nav-first-time': {
      title: 'Welcome to the Dashboard',
      message: 'Use the navigation bar at the bottom to access different sections.',
      type: 'tip',
      position: 'bottom',
      priority: 1
    },
    // Streams tab related help
    'streams-empty': {
      title: 'No Streams Yet',
      message: 'Assigned streams will appear here. Contact an administrator to get streams assigned to you.',
      type: 'info',
      position: 'bottom',
      priority: 2
    },
    'stream-viewing': {
      title: 'Stream Viewing',
      message: 'You can monitor the stream and trigger detection using the controls.',
      type: 'tip',
      position: 'bottom',
      priority: 2
    },
    // Stream modal related help
    'stream-modal-first-time': {
      title: 'Stream Details',
      message: 'This modal shows the livestream and detection options. Use the video controls to watch the stream and the "Run Detection" button to analyze the content.',
      type: 'info',
      position: 'bottom',
      priority: 1
    },
    'stream-modal-load-error': {
      title: 'Stream Loading Error',
      message: 'There was a problem loading the stream. This could be due to connectivity issues or the stream may be offline.',
      type: 'warning',
      position: 'bottom',
      priority: 0
    },
    'stream-modal-playback-error': {
      title: 'Playback Error',
      message: 'There was a problem playing the stream. This could be due to network bandwidth or the stream format.',
      type: 'warning',
      position: 'bottom',
      priority: 0
    },
    'stream-modal-playback-guide': {
      title: 'Playback Controls',
      message: 'Use the video controls to play/pause, adjust volume, and toggle fullscreen. If you experience buffering, try lowering the quality.',
      type: 'tip',
      position: 'bottom',
      priority: 2
    },
    'stream-modal-detection-guide': {
      title: 'About Detection',
      message: 'Pressing "Run Detection" will analyze the current stream for content that matches your monitoring criteria and generate notifications.',
      type: 'tip',
      position: 'bottom',
      priority: 1
    },
    'stream-modal-detection-error': {
      title: 'Detection Error',
      message: 'There was a problem starting the detection process. Please try again or contact support if the issue persists.',
      type: 'warning',
      position: 'bottom',
      priority: 0
    },
    // Agent dashboard related help
    'agent-dashboard-first-time': {
      title: 'Agent Dashboard',
      message: 'This is your monitoring workspace. View assigned streams, check notifications, and communicate with your team.',
      type: 'info',
      position: 'bottom',
      priority: 1
    },
    'agent-dashboard-empty': {
      title: 'No Assignments',
      message: 'You don\'t have any streams assigned yet. New assignments will appear here when they are allocated to you.',
      type: 'info',
      position: 'bottom',
      priority: 2
    },
    // Messages tab related help
    'messages-new': {
      title: 'New Message',
      message: 'Type your message and press send to communicate with other team members.',
      type: 'tip',
      position: 'bottom',
      priority: 2
    },
    // Notifications tab related help
    'notifications-filter': {
      title: 'Filter Notifications',
      message: 'You can filter notifications by type using the filter button.',
      type: 'tip',
      position: 'bottom',
      priority: 3
    },
    'notifications-empty': {
      title: 'No Notifications',
      message: 'You don\'t have any notifications yet. Detection results and system messages will appear here.',
      type: 'info',
      position: 'bottom',
      priority: 3
    },
    // Detection related
    'detection-triggered': {
      title: 'Detection Triggered',
      message: 'Detection has been triggered for this stream. You will be notified of the results.',
      type: 'info',
      position: 'top',
      priority: 0 // highest priority
    },
    'detection-complete': {
      title: 'Detection Complete',
      message: 'The detection process has completed. Check the notifications tab for any findings.',
      type: 'info',
      position: 'top',
      priority: 1
    }
  };
  
  // Methods
  
  /**
   * Show a context-sensitive help bubble
   * @param {string} contextKey - The key for the help content
   * @param {Object} options - Optional overrides for the help content
   */
  const showHelp = (contextKey, options = {}) => {
    // Don't show help that has been dismissed
    if (helpDismissed.value[contextKey]) return;
    
    // Get the help content from the library
    const helpInfo = helpLibrary[contextKey];
    if (!helpInfo) return;
    
    // Merge with options
    const mergedContent = {
      ...helpInfo,
      ...options,
      context: contextKey
    };
    
    // Default action buttons
    if (!mergedContent.actionButtons || mergedContent.actionButtons.length === 0) {
      mergedContent.actionButtons = [
        { 
          label: 'Got it', 
          action: () => dismissHelp(contextKey),
          primary: true
        },
        { 
          label: "Don't show again", 
          action: () => {
            dismissHelp(contextKey, true);
            // Save this preference in localStorage
            const dismissed = JSON.parse(localStorage.getItem('dismissedHelp') || '{}');
            dismissed[contextKey] = true;
            localStorage.setItem('dismissedHelp', JSON.stringify(dismissed));
          },
          primary: false
        }
      ];
    }
    
    // If another help bubble is already showing, queue this one
    if (helpVisible.value) {
      // Only add to queue if not already in queue
      if (!helpQueue.value.find(item => item.context === contextKey)) {
        helpQueue.value.push(mergedContent);
      }
      return;
    }
    
    // Show the help
    helpContent.value = mergedContent;
    helpVisible.value = true;
    
    // Add to history if not already there
    if (!helpHistory.value.includes(contextKey)) {
      helpHistory.value.push(contextKey);
    }
  };
  
  /**
   * Dismiss the current help bubble
   * @param {string} contextKey - The context key of the help to dismiss
   * @param {boolean} dontShowAgain - If true, this help won't be shown again
   */
  const dismissHelp = (contextKey, dontShowAgain = false) => {
    helpVisible.value = false;
    
    if (dontShowAgain) {
      helpDismissed.value[contextKey] = true;
    }
    
    // Show next help bubble in queue if any
    if (helpQueue.value.length > 0) {
      setTimeout(() => {
        const nextHelp = helpQueue.value.shift();
        showHelp(nextHelp.context, nextHelp);
      }, 500);
    }
  };
  
  /**
   * Analyze the current context and show appropriate help
   * @param {Object} context - Current application context
   */
  const analyzeContext = (context) => {
    // Update user activity
    userActivity.value.lastAction = context.action;
    userActivity.value.lastScreen = context.screen;
    userActivity.value.idleTime = 0;
    
    // ===== Authentication related help =====
    
    // Show login help for first-time users
    if (context.screen === 'login' && context.action === 'view' && context.isFirstTime) {
      showHelp('auth-login');
      return;
    }
    
    // Detect auth error and show help immediately
    if (context.error && context.screen === 'login') {
      showHelp('auth-error', {
        message: 'Authentication failed: ' + context.error.message,
        actionButtons: [
          { 
            label: 'OK', 
            action: () => dismissHelp('auth-error'),
            primary: true
          }
        ]
      });
      return;
    }
    
    // ===== Dashboard related help =====
    
    // Show first-time navigation help
    if (context.screen === 'dashboard' && !helpHistory.value.includes('nav-first-time')) {
      showHelp('nav-first-time');
      return;
    }
    
    // Show agent dashboard help for first-time users
    if (context.screen === 'agent_dashboard' && context.action === 'view' && context.isFirstTime) {
      showHelp('agent-dashboard-first-time');
      return;
    }
    
    // Show empty assignments help
    if (context.screen === 'agent_dashboard' && 
        context.stats && 
        context.stats.assignmentsCount === 0) {
      showHelp('agent-dashboard-empty');
      return;
    }
    
    // ===== Stream related help =====
    
    // Show streams help when viewing an empty stream list
    if (context.screen === 'streams' && context.isEmpty) {
      showHelp('streams-empty');
      return;
    }
    
    // Show stream viewing help when opening a stream for the first time
    if (context.screen === 'stream-details' && !helpHistory.value.includes('stream-viewing')) {
      showHelp('stream-viewing');
      return;
    }
    
    // ===== Stream modal related help =====
    
    // Show stream modal help for first-time users
    if (context.screen === 'stream_modal' && context.action === 'view' && context.isFirstTime) {
      showHelp('stream-modal-first-time');
      return;
    }
    
    // Show stream load error help
    if (context.screen === 'stream_modal' && 
        context.action === 'error' && 
        context.error && 
        context.error.type === 'load_error') {
      showHelp('stream-modal-load-error', {
        message: context.error.message || 'Failed to load stream. Please try again.'
      });
      return;
    }
    
    // Show playback error help
    if (context.screen === 'stream_modal' && 
        context.action === 'error' && 
        context.error && 
        context.error.type === 'playback_error') {
      showHelp('stream-modal-playback-error', {
        message: context.error.message || 'Failed to start playback. Please try again.'
      });
      return;
    }
    
    // Show playback guide for first-time playback
    if (context.screen === 'stream_modal' && 
        context.action === 'playback_started' && 
        context.isFirstTime) {
      showHelp('stream-modal-playback-guide');
      return;
    }
    
    // Show detection guide for first-time users
    if (context.screen === 'stream_modal' && 
        context.action === 'detection_started' && 
        context.isFirstTime) {
      showHelp('stream-modal-detection-guide');
      return;
    }
    
    // Show detection error help
    if (context.screen === 'stream_modal' && 
        context.action === 'error' && 
        context.error && 
        context.error.type === 'detection_error') {
      showHelp('stream-modal-detection-error', {
        message: context.error.message || 'Failed to run detection. Please try again.'
      });
      return;
    }
    
    // ===== Messages related help =====
    
    // Messages help
    if (context.screen === 'messages' && context.action === 'new-conversation') {
      showHelp('messages-new');
      return;
    }
    
    // ===== Notifications related help =====
    
    // Notifications filter help
    if (context.screen === 'notifications' && 
        context.action === 'view' && 
        !helpHistory.value.includes('notifications-filter')) {
      showHelp('notifications-filter');
      return;
    }
    
    // Empty notifications help
    if (context.screen === 'notifications' && 
        context.action === 'view' && 
        context.isEmpty) {
      showHelp('notifications-empty');
      return;
    }
    
    // Detection complete notification
    if (context.action === 'detection_complete') {
      showHelp('detection-complete');
      return;
    }
  };
  
  /**
   * Reset the idle timer
   */
  const resetIdleTimer = () => {
    if (idleTimer) {
      clearInterval(idleTimer);
    }
    
    userActivity.value.idleTime = 0;
    
    // Start a new timer
    idleTimer = setInterval(() => {
      userActivity.value.idleTime += 1;
      
      // If user is idle for more than 30 seconds on a screen, analyze context again
      if (userActivity.value.idleTime === 30) {
        const currentScreen = userActivity.value.lastScreen;
        if (currentScreen) {
          analyzeContext({
            screen: currentScreen,
            action: 'idle',
            idle: true
          });
        }
      }
    }, 1000);
  };
  
  // Load dismissed help from localStorage
  onMounted(() => {
    try {
      const dismissed = JSON.parse(localStorage.getItem('dismissedHelp') || '{}');
      helpDismissed.value = dismissed;
    } catch (e) {
      console.error('Error loading dismissed help:', e);
    }
    
    // Start idle timer
    resetIdleTimer();
    
    // Add event listeners to reset idle timer
    window.addEventListener('mousemove', resetIdleTimer);
    window.addEventListener('keypress', resetIdleTimer);
    window.addEventListener('click', resetIdleTimer);
    window.addEventListener('touchstart', resetIdleTimer);
  });
  
  // Clean up
  onUnmounted(() => {
    if (idleTimer) {
      clearInterval(idleTimer);
    }
    
    window.removeEventListener('mousemove', resetIdleTimer);
    window.removeEventListener('keypress', resetIdleTimer);
    window.removeEventListener('click', resetIdleTimer);
    window.removeEventListener('touchstart', resetIdleTimer);
  });
  
  // Auto-dismiss help after a certain time for non-critical messages
  watch(helpVisible, (isVisible) => {
    if (isVisible && helpContent.value.type !== 'warning') {
      setTimeout(() => {
        // Only auto-dismiss if this is still the same help bubble
        if (helpVisible.value && helpContent.value.type !== 'warning') {
          dismissHelp(helpContent.value.context);
        }
      }, 7000); // Auto-dismiss after 7 seconds
    }
  });
  
  // Export
  return {
    helpVisible,
    helpContent,
    helpHistory,
    showHelp,
    dismissHelp,
    analyzeContext
  };
}