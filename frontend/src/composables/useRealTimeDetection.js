/**
 * Real-time detection notification composable
 * Handles detection events from backend via websockets
 */
import { ref, onMounted, onBeforeUnmount } from "vue";
import { io } from "socket.io-client";
import { useToast } from "vue-toastification";

export function useRealTimeDetection() {
  // State
  const detections = ref([]);
  const currentDetection = ref(null);
  const loading = ref(false);
  const connected = ref(false);
  const socket = ref(null);

  // Notifications preferences (can be overridden when initializing)
  const showKeywordDetections = ref(true);
  const showObjectDetections = ref(true);
  const showStreamUpdates = ref(true);
  const toast = useToast();

  /**
   * Initialize socket connection and event listeners
   * @param {Object} options - Configuration options
   * @param {string} options.serverUrl - The socket server URL
   * @param {boolean} options.autoConnect - Whether to connect automatically
   * @param {Object} options.preferences - Notification preferences
   */
  const initialize = ({
    serverUrl = "     https://monitor-backend.jetcamstudio.com:5000/notifications",
    autoConnect = true,
    preferences = {},
  } = {}) => {
    if (socket.value) {
      console.warn("Socket connection already initialized");
      return;
    }

    // Apply preferences
    if (preferences.showKeywordDetections !== undefined) {
      showKeywordDetections.value = preferences.showKeywordDetections;
    }

    if (preferences.showObjectDetections !== undefined) {
      showObjectDetections.value = preferences.showObjectDetections;
    }

    if (preferences.showStreamUpdates !== undefined) {
      showStreamUpdates.value = preferences.showStreamUpdates;
    }

    // Initialize socket
    const url = serverUrl;
    socket.value = io(url, {
      autoConnect,
      path: "/ws",
      transports: ["websocket", "polling"],
    });

    // Listen for connect event
    socket.value.on("connect", () => {
      console.log("Connected to real-time detection server");
      connected.value = true;
    });

    // Listen for disconnect event
    socket.value.on("disconnect", () => {
      console.log("Disconnected from real-time detection server");
      connected.value = false;
    });

    // Listen for detection events
    socket.value.on("detection", (data) => {
      console.log("Detection received:", data);

      if (!shouldShowDetection(data)) {
        console.log("Detection filtered out by user preferences");
        return;
      }

      // Add to detection list
      addDetection(data);

      // Show as current detection for notification
      showDetection(data);
    });

    // Connect if autoConnect is true
    if (autoConnect) {
      connect();
    }
  };

  /**
   * Connect to the socket server
   */
  const connect = () => {
    if (!socket.value) {
      console.error("Socket not initialized, call initialize() first");
      return;
    }

    if (!socket.value.connected) {
      socket.value.connect();
    }
  };

  /**
   * Disconnect from the socket server
   */
  const disconnect = () => {
    if (socket.value && socket.value.connected) {
      socket.value.disconnect();
    }
  };

  /**
   * Check if a detection should be shown based on user preferences
   * @param {Object} detection - The detection object
   * @returns {boolean} - Whether the detection should be shown
   */
  const shouldShowDetection = (detection) => {
    if (!detection || !detection.event_type) return false;

    const eventType = detection.event_type.toLowerCase();

    if (eventType === "keyword_detected" && !showKeywordDetections.value) {
      return false;
    }

    if (eventType === "object_detected" && !showObjectDetections.value) {
      return false;
    }

    if (
      (eventType === "stream_started" || eventType === "stream_ended") &&
      !showStreamUpdates.value
    ) {
      return false;
    }

    return true;
  };

  /**
   * Add a detection to the list
   * @param {Object} detection - The detection object
   */
  const addDetection = (detection) => {
    if (!detection) return;

    // Add timestamp if not present
    if (!detection.timestamp) {
      detection.timestamp = new Date().toISOString();
    }

    // Add to beginning of the list (most recent first)
    detections.value.unshift(detection);

    // Limit the number of detections we store (keep 50 latest)
    if (detections.value.length > 50) {
      detections.value = detections.value.slice(0, 50);
    }
  };

  /**
   * Show a detection as a notification
   * @param {Object} detection - The detection object
   */
  const showDetection = (detection) => {
    if (!detection) return;

    // Set as current detection to trigger notification component
    currentDetection.value = detection;

    // Also show a toast notification for less important events
    const eventType = detection.event_type?.toLowerCase();

    if (eventType === "stream_started" || eventType === "stream_ended") {
      const streamer = detection.streamer_username || "Unknown";
      const message =
        eventType === "stream_started"
          ? `${streamer} started streaming`
          : `${streamer}'s stream ended`;

      toast.info(message, {
        timeout: 3000,
      });
    }
  };

  /**
   * Dismiss the current detection notification
   */
  const dismissCurrentDetection = () => {
    currentDetection.value = null;
  };

  /**
   * Clear all detections
   */
  const clearDetections = () => {
    detections.value = [];
    currentDetection.value = null;
  };

  /**
   * Watch for notification preference changes in localStorage
   */
  const watchPreferences = () => {
    window.addEventListener("storage", (event) => {
      if (event.key === "notificationPreferences") {
        try {
          const preferences = JSON.parse(event.newValue);

          if (preferences.types) {
            showKeywordDetections.value =
              preferences.types.keyword_detected !== false;
            showObjectDetections.value =
              preferences.types.object_detected !== false;
            showStreamUpdates.value =
              preferences.types.stream_started !== false &&
              preferences.types.stream_ended !== false;
          }
        } catch (error) {
          console.error("Failed to parse notification preferences:", error);
        }
      }
    });

    // Load initial preferences
    try {
      const savedPreferences = localStorage.getItem("notificationPreferences");

      if (savedPreferences) {
        const preferences = JSON.parse(savedPreferences);

        if (preferences.types) {
          showKeywordDetections.value =
            preferences.types.keyword_detected !== false;
          showObjectDetections.value =
            preferences.types.object_detected !== false;
          showStreamUpdates.value =
            preferences.types.stream_started !== false &&
            preferences.types.stream_ended !== false;
        }
      }
    } catch (error) {
      console.error("Failed to load notification preferences:", error);
    }
  };

  // Setup and cleanup
  onMounted(() => {
    watchPreferences();
  });

  onBeforeUnmount(() => {
    disconnect();
  });

  return {
    detections,
    currentDetection,
    loading,
    connected,
    initialize,
    connect,
    disconnect,
    dismissCurrentDetection,
    clearDetections,
    shouldShowDetection,
  };
}
