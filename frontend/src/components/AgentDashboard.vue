<template>
  <div class="agent-container" ref="appContainer" :data-theme="isDarkTheme ? 'dark' : 'light'">
    <AgentSidebar 
      :activeTab="currentTab" 
      @tab-change="handleTabChange" 
      :isOnline="isOnline"
      :messageUnreadCount="stats.unreadMessages"
    />
    
    <div class="main-content" :class="{ 'sidebar-minimized': sidebarMinimized }" ref="mainContent">
      <div class="dashboard-content" ref="dashboardContent">
        <!-- Streams Tab -->
        <transition name="fade-slide" mode="out-in">
          <div v-if="currentTab === 'streams'">
            <AgentStreamsComponent
              v-if="dashboardReady && !isLoadingStreams"
              :streams="validatedStreams"
              :isLoading="isLoadingStreams"
              :error="streamErrors"
              :lastRefreshed="lastRefresh"
              @refresh-streams="refreshStreams"
              @update-stream="updateStreamStatus"
            />
            <!-- Skeleton Loading State -->
            <div v-else class="skeleton-container">
              <div class="dashboard-header skeleton-loading">
                <h2 class="skeleton-header"></h2>
              </div>
              <div class="stats-section skeleton-loading">
                <div class="skeleton-stat-card"></div>
                <div class="skeleton-stat-card"></div>
                <div class="skeleton-stat-card"></div>
              </div>
              <div class="controls-section skeleton-loading">
                <div class="search-box">
                  <div class="skeleton-search-input"></div>
                </div>
                <div class="view-controls">
                  <div class="skeleton-refresh-btn"></div>
                </div>
              </div>
              <div class="streams-section skeleton-loading">
                <div class="stream-container grid">
                  <div class="skeleton-stream-card"></div>
                  <div class="skeleton-stream-card"></div>
                  <div class="skeleton-stream-card"></div>
                </div>
              </div>
            </div>
          </div>
        </transition>
        
        <!-- Tasks Tab -->
        <transition name="fade-slide" mode="out-in">
          <AgentTasksComponent
            v-if="currentTab === 'tasks'"
            :tasks="tasks"
            @refresh-tasks="fetchTasks"
            @complete-task="handleTaskComplete"
          />
        </transition>
        
        <!-- Notifications Tab -->
        <transition name="fade-slide" mode="out-in">
          <AgentNotificationsComponent
            v-if="currentTab === 'notifications'"
            :alerts="allAlerts"
            @refresh-notifications="fetchAllLogs"
            @mark-read="handleMarkNotificationRead"
          />
        </transition>
        
        <!-- Messages Tab -->
        <transition name="fade-slide" mode="out-in">
          <AgentMessageComponent 
            v-if="currentTab === 'messages'"
            :currentUser="user" 
            @refresh-messages="handleMessagesRefresh"
          />
        </transition>

        <transition name="fade-slide" mode="out-in">
          <AgentSettingsPage 
            v-if="currentTab === 'settings'"
            :currentUser="user" 
            @update-user="fetchCurrentUser"
          />
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, onBeforeUnmount, watch, provide, inject } from 'vue'
import { library } from '@fortawesome/fontawesome-svg-core'
import AgentSidebar from './AgentSidebar.vue'
import AgentStreamsComponent from './AgentStreamsComponent.vue'
import AgentTasksComponent from './AgentTasksComponent.vue'
import AgentNotificationsComponent from './AgentNotificationsComponent.vue'
import AgentMessageComponent from './AgentMessageComponent.vue'
import anime from 'animejs/lib/anime.es.js'
import axios from 'axios'
import {
  faSync,
  faBellSlash,
  faVideoSlash,
  faExclamationCircle,
  faExclamationTriangle,
  faInfoCircle,
  faCheckCircle,
  faCamera,
  faUser,
  faLock,
  faSkull,
  faExclamation,
  faFlag,
  faFire,
  faTachometerAlt,
  faVideo,
  faClipboardList,
  faBell,
  faComments,
  faBox,
  faPlayCircle,
  faCheck,
  faCheckDouble,
  faClipboardCheck,
  faBars,
  faTimes,
  faSun,
  faMoon
} from '@fortawesome/free-solid-svg-icons'
import AgentSettingsPage from './AgentSettingsPage.vue'

library.add(
  faSync,
  faBellSlash,
  faVideoSlash,
  faExclamationCircle,
  faExclamationTriangle,
  faInfoCircle,
  faCheckCircle,
  faCamera,
  faUser,
  faLock,
  faSkull,
  faExclamation,
  faFlag,
  faFire,
  faTachometerAlt,
  faVideo,
  faClipboardList,
  faBell,
  faComments,
  faBox,
  faPlayCircle,
  faCheck,
  faCheckDouble,
  faClipboardCheck,
  faBars,
  faTimes,
  faSun,
  faMoon
)

export default {
  name: 'AgentDashboard',
  components: {
    AgentSidebar,
    AgentStreamsComponent,
    AgentTasksComponent,
    AgentNotificationsComponent,
    AgentMessageComponent, 
    AgentSettingsPage
  },
  props: {
    isOnline: {
      type: Boolean,
      default: true
    }
  },
  setup() {
    // Inject theme from App.vue
    const appTheme = inject('theme', ref(true))
    
    // Create a computed property for isDarkTheme to match App.vue's naming
    const isDarkTheme = computed(() => appTheme.value === true)
    
    // State variables
    const user = ref(null)
    const lastRefresh = ref(new Date())
    const isRefreshing = ref(false)
    const currentTab = ref('streams')
    const isMobile = ref(window.innerWidth <= 768)
    const refreshInterval = ref(null)
    const showQuickNav = ref(false)
    const sidebarMinimized = ref(false)
    const dashboardReady = ref(false) // New state to track dashboard readiness
    
    // Tooltip state
    const showTooltip = ref(false)
    const tooltipText = ref('')
    const tooltipStyle = ref({})
    const tooltipTimeout = ref(null)
    
    // Navigation tabs
    const navTabs = [
      { id: 'streams', label: 'Streams', icon: ['fas', 'video'] },
      { id: 'tasks', label: 'Tasks', icon: ['fas', 'clipboard-list'] },
      { id: 'notifications', label: 'Notifications', icon: ['fas', 'bell'] },
      { id: 'messages', label: 'Messages', icon: ['fas', 'comments'] },
      { id: 'settings', label: 'Settings', icon: ['fas', 'cog'] }
    ]
    
    // Animation refs
    const appContainer = ref(null)
    const sidebar = ref(null)
    const mainContent = ref(null)
    const dashboardHeader = ref(null)
    const dashboardContent = ref(null)
    const dashboardGrid = ref(null)
    const statusDisplay = ref(null)
    const statusBadge = ref(null)
    const lastRefreshTime = ref(null)
    const refreshButton = ref(null)
    const quickNavButton = ref(null)
    const quickNavMenu = ref(null)
    const navItems = ref([])
    const tooltip = ref(null)
    const themeToggle = ref(null)
    
    // Re-provide app theme to child components
    provide('appTheme', appTheme)
    
    // Data states
    const stats = ref({
      activeStreams: 0,
      flaggedEvents: 0,
      pendingTasks: 0,
      unreadMessages: 0
    })
    
    // Stream-specific states
    const allStreams = ref([])
    const validatedStreams = ref([])
    const isLoadingStreams = ref(false)
    const streamErrors = ref(null)
    const streamRefreshTimer = ref(null)
    
    const recentAlerts = ref([])
    const activeStreams = ref([])
    const tasks = ref([])
    const allAlerts = ref([])
    
    // Error handling
    const errors = ref({})
    
    // Page title based on current tab
    const pageTitle = computed(() => {
      switch (currentTab.value) {
        case 'streams':
          return 'Assigned Streams'
        case 'tasks':
          return 'Tasks'
        case 'notifications':
          return 'Notifications'
        case 'messages':
          return 'Messages'
        default:
          return 'streams'
      }
    })
    
    // Format the last refresh time
    const formattedLastRefresh = computed(() => {
      return lastRefresh.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    })
    
    // Get badge count by tab
    const getBadgeCount = (tabId) => {
      switch (tabId) {
        case 'streams':
          return stats.value.activeStreams
        case 'tasks':
          return stats.value.pendingTasks
        case 'notifications':
          return stats.value.flaggedEvents
        case 'messages':
          return stats.value.unreadMessages
        default:
          return 0
      }
    }
    
    // Toggle quick navigation menu
    const toggleQuickNav = () => {
      showQuickNav.value = !showQuickNav.value
      
      if (showQuickNav.value) {
        // Animate menu items entrance
        nextTick(() => {
          if (navItems.value && navItems.value.length) {
            anime({
              targets: navItems.value,
              translateX: [-20, 0],
              opacity: [0, 1],
              delay: anime.stagger(70),
              easing: 'easeOutQuad',
              duration: 500
            })
          }
        })
      }
    }
    
    // Navigate using quick nav
    const quickNavTo = (tabId) => {
      handleTabChange(tabId)
      showQuickNav.value = false
    }
    
    // Show tooltip message
    const showTooltipMessage = (message, duration = 2000) => {
      // Clear any existing timeout
      if (tooltipTimeout.value) clearTimeout(tooltipTimeout.value)
      
      tooltipText.value = message
      
      // Position near the refresh button
      if (refreshButton.value) {
        const btnRect = refreshButton.value.getBoundingClientRect()
        tooltipStyle.value = {
          top: `${btnRect.bottom + 10}px`,
          right: `20px`
        }
      } else {
        tooltipStyle.value = {
          top: '20%',
          right: '20px'
        }
      }
      
      showTooltip.value = true
      
      // Animate tooltip
      nextTick(() => {
        if (tooltip.value) {
          anime({
            targets: tooltip.value,
            translateY: ['-10px', '0px'],
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutQuad'
          })
        }
      })
      
      // Hide after duration
      tooltipTimeout.value = setTimeout(() => {
        if (tooltip.value) {
          anime({
            targets: tooltip.value,
            translateY: ['0px', '-10px'],
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInQuad',
            complete: () => {
              showTooltip.value = false
            }
          })
        } else {
          showTooltip.value = false
        }
      }, duration)
    }
    
    // Check if the device is mobile
    const checkMobile = () => {
      isMobile.value = window.innerWidth <= 768
    }
    
    // Handle tab change with animation
    const handleTabChange = (tab) => {
      // Store previous tab for cleanup
      const previousTab = currentTab.value
      
      // Update current tab
      currentTab.value = tab
      
      // If leaving streams tab, stop any stream refresh interval
      if (previousTab === 'streams' && tab !== 'streams') {
        if (streamRefreshTimer.value) {
          clearInterval(streamRefreshTimer.value)
          streamRefreshTimer.value = null
        }
      }
      
      // If entering streams tab, load streams if needed and start refresh timer
      if (tab === 'streams') {
        // Load streams if we don't have any yet
        if (validatedStreams.value.length === 0 && !isLoadingStreams.value) {
          loadStreamData()
        }
        
        // Start auto-refresh timer for streams
        startStreamRefreshTimer()
      }
      
      // Wait for tab to be rendered before animating
      nextTick(() => {
        // Animate the page title
        if (pageTitle.value) {
          anime({
            targets: pageTitle.value,
            translateX: [20, 0],
            opacity: [0, 1],
            duration: 500,
            easing: 'easeOutQuad'
          })
        }
        
        // Run tab-specific animations
        if (tab === 'streams') {
          animateDashboardEntrance()
        } else if (tab === 'tasks') {
          animateTabEntrance()
        } else if (tab === 'notifications') {
          animateTabEntrance()
        } else if (tab === 'messages') {
          animateTabEntrance()
        }
      })
    }
    
    // Enhanced tab entrance animation
    const animateTabEntrance = () => {
      // Animate header elements with more fluidity
      if (dashboardHeader.value) {
        // Staggered entrance for header elements
        anime({
          targets: [statusBadge.value, lastRefreshTime.value, refreshButton.value],
          translateY: ['-20px', 0],
          opacity: [0, 1],
          delay: anime.stagger(100),
          duration: 600,
          easing: 'spring(1, 80, 10, 0)'
        })
        
        // Highlight animation for active elements
        anime({
          targets: dashboardHeader.value,
          boxShadow: [
            '0 0 0 rgba(0, 123, 255, 0)',
            '0 0 15px rgba(0, 123, 255, 0.3)',
            '0 0 0 rgba(0, 123, 255, 0)'
          ],
          duration: 1500,
          easing: 'easeOutQuad'
        })
      }
      
      // Find and animate any table elements if present
      const table = dashboardContent.value.querySelector('table')
      if (table) {
        // Animate table rows with staggered entrance
        anime({
          targets: table.querySelectorAll('tbody tr'),
          translateX: ['-20px', 0],
          opacity: [0, 1],
          backgroundColor: [
            'rgba(0, 123, 255, 0.1)',
            'rgba(0, 123, 255, 0)'
          ],
          delay: anime.stagger(50),
          duration: 800,
          easing: 'easeOutQuad'
        })
        
        // Bounce in effect for table headers
        anime({
          targets: table.querySelectorAll('th'),
          translateY: ['-15px', 0],
          opacity: [0, 1],
          delay: anime.stagger(80),
          duration: 700,
          easing: 'easeOutElastic(1, .6)'
        })
      }
      
      // Animate any cards or sections within the tab
      const sections = dashboardContent.value.querySelectorAll('.section, .card')
      if (sections.length) {
        anime({
          targets: sections,
          scale: [0.95, 1],
          opacity: [0, 1],
          translateY: ['20px', 0],
          delay: anime.stagger(120),
          duration: 700,
          easing: 'easeOutExpo'
        })
      }
    }
    
    // Enhanced dashboard entrance with spectacular animations
    const animateDashboardEntrance = () => {
      // Animate dashboard grid using advanced staggered animations
      if (dashboardGrid.value && dashboardGrid.value.$el) {
        // Create an initial wave effect across the entire dashboard
        anime({
          targets: dashboardGrid.value.$el,
          backgroundColor: [
            'rgba(0, 123, 255, 0.05)',
            'rgba(0, 123, 255, 0)'
          ],
          duration: 1200,
          easing: 'easeOutQuad'
        });
        
        // Get all the card elements in the dashboard
        const cards = dashboardGrid.value.$el.querySelectorAll('.dashboard-card')
        if (cards && cards.length) {
          // Create a ripple effect from center
          anime({
            targets: cards,
            scale: [0.8, 1],
            translateY: [30, 0],
            opacity: [0, 1],
            rotateX: ['5deg', '0deg'],
            boxShadow: [
              '0 0 0 rgba(0,0,0,0)',
              '0 10px 25px rgba(0,0,0,0.1)'
            ],
            delay: anime.stagger(80, {grid: [2, Math.ceil(cards.length/2)], from: 'center'}),
            easing: 'easeOutExpo',
            duration: 800
          });
          
          // Add subtle continuous hover animation to cards
          cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
              anime({
                targets: card,
                translateY: -8,
                boxShadow: '0 15px 30px rgba(0,0,0,0.15)',
                duration: 400,
                easing: 'easeOutCubic'
              });
            });
            
            card.addEventListener('mouseleave', () => {
              anime({
                targets: card,
                translateY: 0,
                boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                duration: 500,
                easing: 'easeOutElastic(1, .5)'
              });
            });
          });
        }
        
        // Animate specific sections within each card with sequence
        const cardHeaders = dashboardGrid.value.$el.querySelectorAll('.card-header')
        if (cardHeaders && cardHeaders.length) {
          anime({
            targets: cardHeaders,
            translateX: ['-30px', 0],
            opacity: [0, 1],
            delay: anime.stagger(70),
            easing: 'easeOutQuint',
            duration: 700,
            endDelay: 200
          });
        }
        
        // Find and animate any chart containers with scaling effect
        const chartContainers = dashboardGrid.value.$el.querySelectorAll('.chart-container, canvas')
        if (chartContainers.length) {
          anime({
            targets: chartContainers,
            scale: [0.7, 1],
            opacity: [0, 1],
            delay: anime.stagger(150, {start: 300}),
            duration: 800,
            easing: 'easeOutElastic(1, .6)'
          });
        }
        
        // Animate stat counters with counting effect and text highlighting
        const statValues = dashboardGrid.value.$el.querySelectorAll('.stat-value')
        if (statValues && statValues.length) {
          // First make them visible with scaling
          anime({
            targets: statValues,
            scale: [0.5, 1],
            opacity: [0, 1],
            delay: anime.stagger(150, {start: 400}),
            duration: 800,
            easing: 'easeOutElastic(1, .5)'
          });
          
          // Then animate the counting
          setTimeout(() => {
            anime({
              targets: statValues,
              innerHTML: [0, el => el.innerHTML],
              round: 1,
              easing: 'easeInOutExpo',
              duration: 2000,
              delay: anime.stagger(100)
            });
          }, 500);
          
          // Add pulse highlight to emphasize important stats
          anime({
            targets: statValues,
            color: [
              'rgba(0, 123, 255, 1)',
              'rgba(33, 37, 41, 1)'
            ],
            delay: 1500,
            duration: 1500,
            easing: 'easeOutQuad'
          });
        }
        
        // Enhance alert/notification items with sequential fade in
        const alertItems = dashboardGrid.value.$el.querySelectorAll('.alert-item, .notification-item')
        if (alertItems.length) {
          anime({
            targets: alertItems,
            translateX: ['-20px', 0],
            opacity: [0, 1],
            delay: anime.stagger(80, {start: 600}),
            duration: 600,
            easing: 'easeOutCubic'
          });
        }
      }
    }
    
    // Enhanced tab navigation with fluid transition effects
    const navigateToTab = (tab) => {
      // Store current tab content for transition
      const currentTabEl = dashboardContent.value.querySelector(':scope > *:not(.action-tooltip):not(.quick-nav-menu)');
      
      if (!currentTabEl) {
        // If no current tab content, just switch
        handleTabChange(tab);
        return;
      }
      
      // Create an impressive transition effect
      anime({
        targets: currentTabEl,
        translateX: [0, -30],
        opacity: [1, 0],
        filter: ['blur(0px)', 'blur(5px)'],
        duration: 400,
        easing: 'easeInOutQuad',
        complete: () => {
          // Change the tab
          handleTabChange(tab);
          
          // When the new tab is rendered, animate it in
          nextTick(() => {
            const newTabEl = dashboardContent.value.querySelector(':scope > *:not(.action-tooltip):not(.quick-nav-menu)');
            if (newTabEl) {
              // Create page transition reveal effect
              anime.set(newTabEl, {
                translateX: 50,
                opacity: 0,
                filter: 'blur(5px)'
              });
              
              // Ripple effect on background during tab change
              const ripple = document.createElement('div');
              ripple.className = 'tab-change-ripple';
              ripple.style.position = 'absolute';
              ripple.style.top = '50%';
              ripple.style.left = '50%';
              ripple.style.transform = 'translate(-50%, -50%) scale(0)';
              ripple.style.width = '10px';
              ripple.style.height = '10px';
              ripple.style.borderRadius = '50%';
              ripple.style.backgroundColor = 'rgba(0, 123, 255, 0.1)';
              ripple.style.zIndex = '-1';
              
              dashboardContent.value.appendChild(ripple);
              
              // Animate the ripple
              anime({
                targets: ripple,
                scale: 100,
                opacity: [0.5, 0],
                duration: 800,
                easing: 'easeOutQuad',
                complete: () => {
                  dashboardContent.value.removeChild(ripple);
                }
              });
              
              // Animate the new tab content
              anime({
                targets: newTabEl,
                translateX: [50, 0],
                opacity: [0, 1],
                filter: ['blur(5px)', 'blur(0px)'],
                duration: 600,
                delay: 150,
                easing: 'easeOutQuint'
              });
              
              // Enhance the page title for new tab
              anime({
                targets: pageTitle.value,
                translateY: ['-20px', 0],
                opacity: [0, 1],
                duration: 800,
                easing: 'easeOutElastic(1, .5)'
              });
            }
          });
        }
      });
    }
    
    // Fetch current user information
    const fetchCurrentUser = async () => {
      try {
        const response = await axios.get('/api/session')
        user.value = response.data.user
      } catch (error) {
        console.error('Error fetching user data:', error)
      }
    }
    
    // Check if m3u8 URL returns a video stream
    const checkM3u8Status = async (url) => {
      if (!url) return false
      
      try {
        // HTTP HEAD request to check if the URL exists without downloading content
        const response = await axios.head(url, { 
          timeout: 5000,
          validateStatus: status => status !== 404 // Accept any status except 404
        })
        return response.status >= 200 && response.status < 400
      } catch (err) {
        console.log(`M3u8 URL not available (network error): ${url}`)
        // Mark as offline if we get a network error
        return false
      }
    }
    
    // Get m3u8 URL for a stream
    const getStreamM3u8Url = (stream) => {
      if (!stream) return null
      
      const platform = (stream.platform || '').toLowerCase()
      if (platform === 'chaturbate' && stream.chaturbate_m3u8_url) {
        return stream.chaturbate_m3u8_url
      } else if (platform === 'stripchat' && stream.stripchat_m3u8_url) {
        return stream.stripchat_m3u8_url
      }
      return null
    }
    
    // Validate stream status by checking m3u8 URL
    const validateStreamStatus = async (streamsList) => {
      const validatedStreams = [...streamsList]
      const statusCheckPromises = []
      
      for (let i = 0; i < validatedStreams.length; i++) {
        const currentStream = validatedStreams[i]
        const m3u8Url = getStreamM3u8Url(currentStream)
        
        // Create a promise for each stream to check its status
        const statusPromise = async () => {
          try {
            if (m3u8Url) {
              currentStream.isLive = await checkM3u8Status(m3u8Url)
            } else {
              currentStream.isLive = false
            }
          } catch (err) {
            // If there's any error during validation, mark the stream as offline
            console.error(`Error validating stream status for ${currentStream.id}:`, err)
            currentStream.isLive = false
          }
          return currentStream
        }
        
        statusCheckPromises.push(statusPromise())
      }
      
      // Wait for all status checks to complete
      return Promise.all(statusCheckPromises)
    }
    
    // Update a single stream's status with animation feedback
    const updateStreamStatus = async (streamId) => {
      try {
        const streamIndex = validatedStreams.value.findIndex(s => s.id === streamId)
        if (streamIndex === -1) return
        
        // Get updated stream data
        const response = await axios.get(`/api/detection-status/${streamId}`)
        if (response.data) {
          const updatedStream = response.data
          
          // Check m3u8 URL status
          const m3u8Url = getStreamM3u8Url(updatedStream)
          try {
            updatedStream.isLive = m3u8Url ? await checkM3u8Status(m3u8Url) : false
          } catch (error) {
            console.error('Network error checking stream status:', error)
            updatedStream.isLive = false
          }
          
          // Fetch detections
          try {
            const detectionsResponse = await axios.get(`/api/detection-status/${streamId}`)
            updatedStream.detections = detectionsResponse.data || []
          } catch (detErr) {
            console.error(`Error fetching detections for stream ${streamId}:`, detErr)
            updatedStream.detections = []
          }
          
          // Update the stream in the list
          validatedStreams.value[streamIndex] = updatedStream
          
          // Show feedback
          showTooltipMessage(`Stream ${updatedStream.title || streamId} updated`)
        }
      } catch (err) {
        console.error('Error updating stream status:', err)
        showTooltipMessage('Error updating stream', 3000)
      }
    }
    
    // Start auto-refresh timer for streams with animation
    const startStreamRefreshTimer = () => {
      // Clear existing timer if any
      if (streamRefreshTimer.value) {
        clearInterval(streamRefreshTimer.value)
      }
      
      // Set up new refresh timer (every 5 minutes)
      streamRefreshTimer.value = setInterval(() => {
        if (currentTab.value === 'streams') {
          refreshStreams()
          
          // Animate refresh button when auto-refresh triggers
          if (refreshButton.value) {
            anime({
              targets: refreshButton.value,
              rotate: '360deg',
              scale: [1, 1.2, 1],
              duration: 1000,
              easing: 'easeInOutBack'
            })
          }
        }
      }, 5 * 60 * 1000) // 5 minutes
    }
    
    // Load all streams and validate their status with loading animation
    const loadStreamData = async () => {
      if (isLoadingStreams.value) return
      
      isLoadingStreams.value = true
      streamErrors.value = null
      
      // Animate skeleton loading
      nextTick(() => {
        const skeletonElements = document.querySelectorAll('.skeleton-loading');
        if (skeletonElements.length) {
          anime({
            targets: skeletonElements,
            opacity: [0.5, 1],
            duration: 1000,
            easing: 'easeInOutQuad',
            loop: true,
            direction: 'alternate'
          });
        }
      });
      
      try {
        // Get all streams
        const response = await axios.get('/api/streams')
        const allStreamsData = response.data || []
        
        // Store all streams
        allStreams.value = allStreamsData
        
        // Filter streams assigned to current user
        const assignedStreams = allStreamsData.filter(stream => {
          if (!stream.assignments || !Array.isArray(stream.assignments)) {
            return false
          }
          
          return stream.assignments.some(assignment => {
            return Number(assignment.agent_id) === Number(user.value?.id)
          })
        })
        
        // Validate each stream's status
        const validated = await validateStreamStatus(assignedStreams)
        
        // Fetch detections for each stream
        for (const stream of validated) {
          try {
            const detectionsResponse = await axios.get(`/api/detection-status/${stream.id}`)
            stream.detections = detectionsResponse.data || []
          } catch (detErr) {
            console.error(`Error fetching detections for stream ${stream.id}:`, detErr)
            stream.detections = []
          }
        }
        
        // Update validated streams
        validatedStreams.value = validated
        
        // Update stats
        stats.value.activeStreams = validated.filter(s => s.isLive).length
        
        // Update last refresh time
        lastRefresh.value = new Date()
        
        // Show success feedback
        showTooltipMessage(`${validated.length} streams loaded`)
        
      } catch (err) {
        console.error('Error loading streams:', err)
        streamErrors.value = err.response?.data?.message || 'Failed to load streams. Please try again.'
        
        // Show error feedback
        showTooltipMessage('Error loading streams', 3000)
      } finally {
        isLoadingStreams.value = false
        
        // Stop skeleton animation
        anime.remove('.skeleton-loading');
      }
    }
    
    // Refresh streams data with animation
    const refreshStreams = async () => {
      if (isLoadingStreams.value) return
      
      isRefreshing.value = true
      
      // Animate refresh button
      if (refreshButton.value) {
        anime({
          targets: refreshButton.value,
          rotate: '360deg',
          scale: [1, 1.2, 1],
          duration: 1000,
          easing: 'easeInOutQuad'
        })
      }
      
      await loadStreamData()
      isRefreshing.value = false
    }
    
    // Fetch all the data for dashboard with loading animation
    const fetchDashboardData = async () => {
      isRefreshing.value = true
      
      // Animate refresh
      if (refreshButton.value) {
        anime({
          targets: refreshButton.value,
          rotate: '360deg',
          scale: [1, 1.2, 1],
          duration: 1000,
          easing: 'easeInOutQuad'
        })
      }
      
      try {
        await Promise.all([
          fetchActiveStreams(),
          fetchRecentLogs(),
          fetchTasks(),
          fetchUnreadMessageCount(),
          fetchCurrentUser()
        ])
        
        // Update stats based on retrieved data
        updateStats()
        
        // Show success feedback
        showTooltipMessage('Dashboard updated')
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
        showTooltipMessage('Error updating dashboard', 3000)
      } finally {
        isRefreshing.value = false
      }
    }
    
    // Handle messages refresh with animation
    const handleMessagesRefresh = () => {
      // Animate refresh
      if (refreshButton.value) {
        anime({
          targets: refreshButton.value,
          rotate: '360deg',
          scale: [1, 1.2, 1],
          duration: 800,
          easing: 'easeInOutBack'
        })
      }
      
      // Update unread message count in the stats
      fetchUnreadMessageCount()
    }

    // Fetch unread message count with animation
    const fetchUnreadMessageCount = async () => {
      try {
        const response = await axios.get('/api/messages/unread-count')
        
        // If count changed, animate the badge
        if (stats.value.unreadMessages !== (response.data.count || 0)) {
          // Find message badge if it exists
          const msgBadge = document.querySelector('.sidebar-nav-item[data-tab="messages"] .badge')
          if (msgBadge) {
            anime({
              targets: msgBadge,
              scale: [1, 1.5, 1],
              backgroundColor: [
                'rgb(59, 130, 246)', // Default blue
                'rgb(239, 68, 68)',  // Highlight red
                'rgb(59, 130, 246)'  // Back to blue
              ],
              duration: 800,
              easing: 'easeInOutQuad'
            })
          }
        }
        
        stats.value.unreadMessages = response.data.count || 0
      } catch (error) {
        console.error('Error fetching unread message count:', error)
      }
    }

    
    // Fetch tasks with animation feedback
    const fetchTasks = async () => {
      try {
        const response = await axios.get('/api/tasks')
        
        // If task count changed, animate the badge
        if (tasks.value.length !== (response.data || []).length) {
          // Find tasks badge if it exists
          const taskBadge = document.querySelector('.sidebar-nav-item[data-tab="tasks"] .badge')
          if (taskBadge) {
            anime({
              targets: taskBadge,
              scale: [1, 1.5, 1],
              backgroundColor: [
                'rgb(59, 130, 246)', // Default blue
                'rgb(239, 68, 68)',  // Highlight red
                'rgb(59, 130, 246)'  // Back to blue
              ],
              duration: 800,
              easing: 'easeInOutQuad'
            })
          }
        }
        
        tasks.value = response.data || []
        
        // Update task count in stats
        stats.value.pendingTasks = tasks.value.length
      } catch (error) {
        console.error('Error fetching tasks:', error)
        tasks.value = []
      }
    }

    // Fetch all notifications/logs with animation
    const fetchAllLogs = async () => {
      isRefreshing.value = true
      
      // Animate refresh button
      if (refreshButton.value) {
        anime({
          targets: refreshButton.value,
          rotate: '360deg',
          scale: [1, 1.2, 1],
          duration: 800,
          easing: 'easeInOutBack'
        })
      }
      
      try {
        const response = await axios.get('/api/logs')
        allAlerts.value = response.data || []
        
        // Show feedback
        showTooltipMessage(`${allAlerts.value.length} notifications loaded`)
      } catch (error) {
        console.error('Error fetching all logs:', error)
        allAlerts.value = []
        showTooltipMessage('Error loading notifications', 3000)
      } finally {
        isRefreshing.value = false
      }
    }

    // Fetch recent alert logs
    const fetchRecentLogs = async () => {
      try {
        const response = await axios.get('/api/logs')
        
        // Transform the raw log data into alert format
        recentAlerts.value = (response.data || []).map(log => {
          let level = 'info'
          if (log.event_type?.includes('detection')) {
            level = log.event_type.includes('object') ? 'warning' : 'info'
          }
          
          return {
            title: log.event_type ? formatEventType(log.event_type) : 'System Event',
            description: getLogDescription(log),
            timestamp: log.timestamp || new Date(),
            level: level
          }
        }).slice(0, 5) // Only show 5 most recent alerts
      } catch (error) {
        console.error('Error fetching recent logs:', error)
        errors.value.logs = 'Failed to fetch recent alerts'
        recentAlerts.value = []
      }
    }
    
    // Format event types for display
    const formatEventType = (eventType) => {
      if (!eventType) return 'Unknown Event'
      
      // Convert snake_case to Title Case
      return eventType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    }
    
    // Get a human-readable description for a log
    const getLogDescription = (log) => {
      if (!log) return 'No details available'
      
      // Return a human-readable description based on event type
      const eventType = log.event_type || ''
      
      if (eventType.includes('object_detection')) {
        return `Object detected: ${log.details?.object || 'Unknown object'}`
      } else if (eventType.includes('chat_keyword')) {
        return `Keyword detected in chat: ${log.details?.keyword || 'Unknown keyword'}`
      } else {
        return log.details?.message || 'System event occurred'
      }
    }
    
    // Fetch active streams assigned to the agent
    const fetchActiveStreams = async () => {
      try {
        const response = await axios.get('/api/dashboard')
        
        if (response.data?.assignments) {
          activeStreams.value = response.data.assignments.map(stream => ({
            ...stream,
            isLive: true, // Assuming all returned streams are live
          }))
        } else {
          activeStreams.value = []
        }
        
        // Update stream count in stats
        stats.value.activeStreams = activeStreams.value.length
      } catch (error) {
        console.error('Error fetching active streams:', error)
        errors.value.streams = 'Failed to fetch active streams'
        activeStreams.value = []
      }
    }
    
    // Update dashboard stats
    const updateStats = () => {
      stats.value = {
        activeStreams: validatedStreams.value.filter(s => s.isLive).length || 0,
        flaggedEvents: recentAlerts.value.length || 0,
        pendingTasks: tasks.value.length || 0,
        unreadMessages: stats.value.unreadMessages || 0
      }
    }
    
    // Handle task completion with animation
    const handleTaskComplete = async (taskId) => {
      isRefreshing.value = true
      
      try {
        await axios.put(`/api/tasks/${taskId}/complete`)
        
        // Find the task item in DOM to animate it
        const taskItem = document.querySelector(`.task-item[data-id="${taskId}"]`)
        if (taskItem) {
          // Animate task completion
          anime({
            targets: taskItem,
            translateX: [0, '100%'],
            opacity: [1, 0],
            duration: 500,
            easing: 'easeInQuad',
            complete: () => {
              // Remove from local list
              tasks.value = tasks.value.filter(task => task.id !== taskId)
              // Update task count
              stats.value.pendingTasks = tasks.value.length
            }
          })
        } else {
          // No animation, just update data
          tasks.value = tasks.value.filter(task => task.id !== taskId)
          stats.value.pendingTasks = tasks.value.length
        }
        
        // Show feedback
        showTooltipMessage('Task completed')
      } catch (error) {
        console.error('Error completing task:', error)
        showTooltipMessage('Error completing task', 3000)
      } finally {
        isRefreshing.value = false
      }
    }

    // Handle marking notification as read with animation
    const handleMarkNotificationRead = async (notificationIdOrIds) => {
      const isArray = Array.isArray(notificationIdOrIds)
      const endpoint = isArray ? '/api/logs/mark-read' : `/api/logs/${notificationIdOrIds}/mark-read`
      const method = isArray ? 'put' : 'put'
      
      try {
        const response = await axios[method](endpoint, { 
          ids: isArray ? notificationIdOrIds : null 
        })
        
        if (response.data.success) {
          // Animate notification items
          if (isArray) {
            // Find all notification items to animate
            const notifications = notificationIdOrIds.map(id => 
              document.querySelector(`.notification-item[data-id="${id}"]`)
            ).filter(el => el)
            
            if (notifications.length) {
              anime({
                targets: notifications,
                backgroundColor: [
                  'rgba(59, 130, 246, 0.1)', // Highlight blue
                  'rgba(255, 255, 255, 0)'   // Fade to transparent
                ],
                duration: 800,
                easing: 'easeOutQuad'
              })
            }
            
            // Mark multiple as read
            allAlerts.value = allAlerts.value.map(alert => {
              if (notificationIdOrIds.includes(alert.id)) {
                return { ...alert, read: true }
              }
              return alert
            })
          } else {
            // Find the notification item to animate
            const notification = document.querySelector(`.notification-item[data-id="${notificationIdOrIds}"]`)
            if (notification) {
              anime({
                targets: notification,
                backgroundColor: [
                  'rgba(59, 130, 246, 0.1)', // Highlight blue
                  'rgba(255, 255, 255, 0)'   // Fade to transparent
                ],
                duration: 800,
                easing: 'easeOutQuad'
              })
            }
            
            // Mark one as read
            const index = allAlerts.value.findIndex(alert => alert.id === notificationIdOrIds)
            if (index !== -1) {
              allAlerts.value[index] = { ...allAlerts.value[index], read: true }
            }
          }
          
          // Show feedback
          showTooltipMessage(isArray ? 'Notifications marked as read' : 'Notification marked as read')
        }
      } catch (error) {
        console.error('Error marking notification as read:', error)
        showTooltipMessage('Error updating notification', 3000)
      }
    }
    
    // Refresh the dashboard with animation
    const refreshDashboard = async () => {
      if (isRefreshing.value) return
      
      isRefreshing.value = true
      
      // Animate refresh button
      if (refreshButton.value) {
        anime({
          targets: refreshButton.value,
          rotate: '360deg',
          scale: [1, 1.2, 1],
          duration: 1000,
          easing: 'easeInOutQuad'
        })
      }
      
      // Refresh different data based on active tab
      if (currentTab.value === 'dashboard') {
        await fetchDashboardData()
      } else if (currentTab.value === 'streams') {
        await refreshStreams()
      } else if (currentTab.value === 'tasks') {
        await fetchTasks()
      } else if (currentTab.value === 'notifications') {
        await fetchAllLogs()
      } else if (currentTab.value === 'messages') {
        await handleMessagesRefresh()
      }
      
      lastRefresh.value = new Date()
      isRefreshing.value = false
      
      // Show feedback
      showTooltipMessage('Data refreshed')
    }
    
    // Watch for tab changes to update UI
    watch(currentTab, () => {
      // Animation handled in handleTabChange
    })
    
    // Watch for theme changes
    watch(appTheme, (newValue) => {
      console.log('Theme changed to:', newValue)
    })
    
    // Setup initial animations
    const setupInitialAnimations = () => {
      // Staggered entrance of UI elements
      if (dashboardHeader.value && statusDisplay.value) {
        anime({
          targets: dashboardHeader.value,
          translateY: ['-20px', 0],
          opacity: [0, 1],
          easing: 'easeOutQuad',
          duration: 600
        })
        
        anime({
          targets: [statusBadge.value, lastRefreshTime.value, refreshButton.value],
          translateY: ['-10px', 0],
          opacity: [0, 1],
          delay: anime.stagger(100, {start: 300}),
          easing: 'easeOutQuad', 
          duration: 500
        })
      }
      
      // Animate sidebar entrance if visible
      if (sidebar.value && !isMobile.value) {
        if (sidebar.value.$el) {
          const sidebarNavItems = sidebar.value.$el.querySelectorAll ? 
            sidebar.value.$el.querySelectorAll('.sidebar-nav-item') : 
            [];
            
          if (sidebarNavItems.length) {
            anime({
              targets: sidebarNavItems,
              translateX: ['-20px', 0],
              opacity: [0, 1],
              delay: anime.stagger(70),
              easing: 'easeOutQuad',
              duration: 500
            });
          } else {
            anime({
              targets: sidebar.value.$el,
              translateX: ['-20px', 0],
              opacity: [0.8, 1],
              easing: 'easeOutQuad',
              duration: 500
            });
          }
        }
      }
      
      // Theme toggle button entrance (if exists)
      if (themeToggle.value) {
        anime({
          targets: themeToggle.value,
          scale: [0, 1],
          rotate: ['180deg', '0deg'],
          opacity: [0, 1],
          easing: 'easeOutElastic(1, 0.6)',
          duration: 1000,
          delay: 800
        })
      }
      
      // Quick navigation button entrance for mobile
      if (quickNavButton.value && isMobile.value) {
        anime({
          targets: quickNavButton.value,
          scale: [0, 1],
          opacity: [0, 1],
          easing: 'easeOutBack',
          duration: 600,
          delay: 1000
        })
      }
      
      // Run tab-specific entrance animation
      if (currentTab.value === 'dashboard') {
        nextTick(() => {
          animateDashboardEntrance()
        })
      }
    }
    
    // Setup and cleanup
    onMounted(async () => {
      console.log('AgentDashboard mounted, theme:', appTheme.value);
      
      // Fetch critical data before rendering components
      await fetchCurrentUser();
      dashboardReady.value = true; // Set dashboard as ready after fetching user
      
      // Setup initial animations
      nextTick(() => {
        setupInitialAnimations()
      })
      
      // Add resize listener
      window.addEventListener('resize', checkMobile)
      
      // Initial mobile check
      checkMobile()
    })
    
    onBeforeUnmount(() => {
      // Cleanup event listeners
      window.removeEventListener('resize', checkMobile)
      
      // Clear intervals
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
      }
      
      if (streamRefreshTimer.value) {
        clearInterval(streamRefreshTimer.value)
      }
      
      // Clear any timeouts
      if (tooltipTimeout.value) {
        clearTimeout(tooltipTimeout.value)
      }
    })
    
    return {
      // State
      appTheme,
      user,
      lastRefresh,
      isRefreshing,
      currentTab,
      isMobile,
      stats,
      recentAlerts,
      activeStreams,
      validatedStreams,
      tasks,
      allAlerts,
      isLoadingStreams,
      streamErrors,
      navTabs,
      showQuickNav,
      showTooltip,
      tooltipText,
      tooltipStyle,
      sidebarMinimized,
      dashboardReady, // Expose new state
      
      // Computed
      formattedLastRefresh,
      isDarkTheme,
      
      // Refs
      appContainer,
      sidebar,
      mainContent,
      dashboardHeader,
      dashboardContent,
      dashboardGrid,
      pageTitle,
      statusDisplay,
      statusBadge,
      lastRefreshTime,
      refreshButton,
      quickNavButton,
      quickNavMenu,
      navItems,
      tooltip,
      
      // Methods
      handleTabChange,
      navigateToTab,
      refreshDashboard,
      refreshStreams,
      updateStreamStatus,
      fetchTasks,
      fetchAllLogs,
      handleMessagesRefresh,
      handleTaskComplete,
      handleMarkNotificationRead,
      toggleQuickNav,
      quickNavTo,
      getBadgeCount,
      showTooltipMessage,
      animateDashboardEntrance,
      animateTabEntrance
    }
  }
}
</script>

<style scoped>
/* Define CSS variables to control sidebar width and mobile height - match with AdminDashboard */
:root {
  /* Existing variables */
  
  /* Stream sizing */
  --stream-base-width: 480px;
  --stream-base-height: 360px;
  --stream-min-width: 240px;
  --stream-min-height: 180px;
  
  /* Color variables with RGB format for opacity control */
  --primary-rgb: 59, 130, 246; /* blue-500 */
  --secondary-rgb: 156, 163, 175; /* gray-400 */
  --success-rgb: 16, 185, 129; /* green-500 */
  --danger-rgb: 239, 68, 68; /* red-500 */
  --warning-rgb: 245, 158, 11; /* yellow-500 */
  --info-rgb: 14, 165, 233; /* sky-500 */
}

[data-theme="dark"] {
  /* Dark theme variables */
  --primary-rgb: 96, 165, 250; /* blue-400 */
  --secondary-rgb: 156, 163, 175; /* gray-400 */
  --success-rgb: 34, 197, 94; /* green-400 */
  --danger-rgb: 248, 113, 113; /* red-400 */
  --warning-rgb: 251, 191, 36; /* yellow-400 */
  --info-rgb: 56, 189, 248; /* sky-400 */
  
  --bg-color: #121212;
  --header-bg: #1e1f22;
  --card-bg: #1f2937;
  --text-color: #e5e7eb;
  --text-muted: #9ca3af;
  --heading-color: #f3f4f6;
  --border-color: rgba(255, 255, 255, 0.1);
  --hover-bg: rgba(255, 255, 255, 0.05);
  --button-bg: #374151;
  --button-hover: #4b5563;
  --badge-bg: rgba(156, 163, 175, 0.2);
  --primary-color: #3b82f6;
  --primary-dark: #2563eb;
  --success-color: #10b981;
  --success-bg: rgba(16, 185, 129, 0.2);
  --danger-color: #ef4444;
  --error-bg: rgba(239, 68, 68, 0.1);
  --active-bg: rgba(59, 130, 246, 0.2);
  --counter-bg: rgba(255, 255, 255, 0.1);
  --skeleton-bg: rgba(255, 255, 255, 0.1);
}

.agent-container {
  top: 5;
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow-x: hidden; /* Prevent horizontal scrollbar during animations */
  height: auto;
  width: auto;
  margin-left: 60px;
}

.main-content {
  /* Default state is expanded */
  flex: 1;
  padding: 1rem;
  height: 90%;
}

/* Skeleton loading styles */
.skeleton-container {
  padding-right: 20px;
  margin-left: 60px;
}

.skeleton-loading {
  background: linear-gradient(90deg, var(--skeleton-bg, rgba(255, 255, 255, 0.1)), rgba(255, 255, 255, 0.2), var(--skeleton-bg, rgba(255, 255, 255, 0.1)));
  background-size: 1000px 100%;
  animation: shimmer 2s infinite linear;
  border-radius: 6px;
}

[data-theme="dark"] .skeleton-loading {
  background: linear-gradient(90deg, rgba(0, 0, 0, 0.1), rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.1));
  background-size: 1000px 100%;
}

.skeleton-header {
  width: 200px;
  height: 2rem;
  margin: 0 0 2rem;
}

.skeleton-stat-card {
  height: 100px;
  border-radius: 6px;
}

.skeleton-search-input {
  width: 100%;
  height: 36px;
  border-radius: 6px;
}

.skeleton-refresh-btn {
  width: 100px;
  height: 36px;
  border-radius: 6px;
}

.skeleton-stream-card {
  height: 200px;
  border-radius: 6px;
}

.stats-section.skeleton-loading {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.controls-section.skeleton-loading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.stream-container.grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

/* Dashboard header */
.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 16px;
  background-color: var(--badge-bg, rgba(156, 163, 175, 0.2));
  color: var(--text-muted, #6B7280);
  font-size: 0.85rem;
  font-weight: 500;
}

.status-badge .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-muted, #6B7280);
}

.status-badge.online {
  background-color: var(--success-bg, rgba(16, 185, 129, 0.2));
  color: var(--success-color, #10B981);
}

.status-badge.online .status-dot {
  background-color: var(--success-color, #10B981);
}

.last-refresh {
  font-size: 0.8rem;
  color: var(--text-muted, #6B7280);
}

.refresh-button {
  width: 30px;
  height: 30px;
  border-radius: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--button-bg, #f5f7fa);
  color: var(--text-color, #374151);
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 20px;
}

.refresh-button:hover {
  background-color: var(--button-hover, #e5e7eb);
  transform: translateY(-2px);
}

.refresh-button:active {
  transform: translateY(0);
}

.refresh-button .rotate {
  animation: rotate 1s linear infinite;
}

/* Dashboard content */
.dashboard-content {
  flex: 1;
  overflow-y: auto;
  position: relative;
}

/* Error states */
.error-state {
  max-width: 100%;
  margin: 1rem auto;
  padding: 1.5rem;
  text-align: center;
  background-color: var(--error-bg);
  border: 1px solid var(--error-border);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.error-state h3 {
  margin-bottom: 0.5rem;
  color: var(--text-color);
  font-size: 1.25rem;
}

.error-state p {
  margin-bottom: 1rem;
  color: var(--text-color);
  font-size: 1rem;
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 100%;
  background-color: var(--primary-color);
  color: white;
  font-weight: 500;
  cursor: pointer;
  border: none;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.refresh-button:hover {
  opacity: 0.9;
}

/* Quick navigation for mobile */
.quick-nav-fab {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background-color: var(--primary-color, #3B82F6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  z-index: 100;
  transition: all 0.3s ease;
}

.quick-nav-fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
}

.quick-nav-menu {
  position: fixed;
  bottom: 84px;
  right: 20px;
  width: 240px;
  background-color: var(--card-bg, #ffffff);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
}

.quick-nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color, rgba(0, 0, 0, 0.05));
}

.quick-nav-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--heading-color, #111827);
}

.quick-nav-header .close-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--button-bg, #f5f7fa);
  color: var(--text-color, #374151);
  border: none;
  cursor: pointer;
}

.quick-nav-items {
  padding: 8px 0;
}

.quick-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.quick-nav-item:hover {
  background-color: var(--hover-bg, rgba(0, 0, 0, 0.05));
}

.quick-nav-item.active {
  background-color: var(--active-bg, rgba(59, 130, 246, 0.1));
  color: var(--primary-color, #3B82F6);
}

.quick-nav-item .badge {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  background-color: var(--primary-color, #3B82F6);
  color: white;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}

/* Theme toggle */
.theme-toggle {
  position: fixed;
  bottom: 20px;
  left: 20px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background-color: var(--card-bg, #ffffff);
  color: var(--heading-color, #111827);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 90;
  transition: all 0.3s ease;
}

.theme-toggle:hover {
  transform: scale(1.1) rotate(15deg);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

/* Action tooltip */
.action-tooltip {
  position: fixed;
  padding: 8px 12px;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  border-radius: 6px;
  font-size: 0.9rem;
  z-index: 200;
  pointer-events: none;
}

/* Enhanced Vue transitions with anime.js inspiration */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Enhanced scale transition */
.fade-scale-enter-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1); /* Elastic feel */
}

.fade-scale-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  transform: scale(0.9);
  opacity: 0;
  filter: blur(2px);
}

/* Enhanced slide transition with direction control */
.fade-slide-enter-active {
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1); /* Expo ease out feel */
  position: absolute;
  width: 100%;
  top: 0;
  left: 0;
}

.fade-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: absolute;
  width: 100%;
  top: 0;
  left: 0;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.95);
  filter: blur(3px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-30px) scale(0.95);
  filter: blur(3px);
}

/* New transition for tab content slides */
.slide-right-enter-active,
.slide-left-enter-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-right-leave-active,
.slide-left-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-50px);
  filter: blur(3px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(50px);
  filter: blur(3px);
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(50px);
  filter: blur(3px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-50px);
  filter: blur(3px);
}

/* Enhanced Animations */
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes shimmer {
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

@keyframes notify-bounce {
  0% { transform: scale(0.8); opacity: 0; }
  50% { transform: scale(1.15); opacity: 1; }
  70% { transform: scale(0.95); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes highlight-fade {
  0% { background-color: rgba(59, 130, 246, 0.2); }
  100% { background-color: transparent; }
}

/* Tab transition animations */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* Notification animation */
.notification-bounce {
  animation: notify-bounce 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* Highlight row effect */
.highlight-row {
  animation: highlight-fade 2s ease-out;
}

/* Floating elements animation */
.float-animation {
  animation: float 6s ease-in-out infinite;
}

/* Pulse effect for attention */
.pulse-animation {
  animation: pulse 2s ease-in-out infinite;
}

/* Responsive styles */
@media (max-width: 768px) {
  .agent-container {
    flex-direction: column;
    padding-left: 0;
    height: auto;
    width: auto;
  }

  .main-content {
    width: auto;
    height: 90%;
  }
  
  .dashboard-header {
    padding: 12px 16px;
  }
  
  .page-title {
    font-size: 1.3rem;
  }
  
  .status-display {
    gap: 8px;
  }
  
  .status-badge {
    padding: 3px 8px;
    font-size: 0.8rem;
  }
  
  .last-refresh {
    display: none;
  }
  
  .dashboard-content {
    height: 100%;
    width: auto;
  }
  
  .theme-toggle {
    bottom: 80px;
    left: 16px;
    width: 36px;
    height: 36px;
  }

  .skeleton-container {
    margin-left: 0;
    padding-right: 16px;
  }

  .skeleton-stream-card {
    height: 180px;
  }
}
</style>