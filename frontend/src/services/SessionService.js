/**
 * Session Management Service
 *
 * Provides robust session management for both desktop and mobile interfaces
 * Features:
 * - Persistent session checking with token refresh
 * - Mobile-specific session handling
 * - Offline detection and reconnection
 * - Enhanced session storage strategy
 */

import axios from "axios";
import { useToast } from "vue-toastification";
import authService from "./AuthService";

// Define the API base URL
const API_BASE_URL = "     https://monitor-backend.jetcamstudio.com:5000/api";

// Session configuration constants
const SESSION_REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes
const SESSION_TOKEN_KEY = "session_token";
const SESSION_EXPIRY_KEY = "session_expiry";
const OFFLINE_RETRY_DELAY = 5000; // 5 seconds

class SessionService {
  constructor() {
    this.toast = useToast();
    this.isCheckingSession = false;
    this.sessionInterval = null;
    this.offlineMode = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  /**
   * Initialize the session service
   * @returns {Promise<Object>} Session status
   */
  async initialize() {
    // Check for network connection
    this.checkNetworkStatus();

    // Initialize network event listeners
    window.addEventListener("online", this.handleNetworkChange.bind(this));
    window.addEventListener("offline", this.handleNetworkChange.bind(this));

    // Check for existing session
    const sessionResult = await this.checkSession();

    // Set up automatic session refresh if session is valid
    if (sessionResult.authenticated) {
      this.startSessionRefresh();
    }

    return sessionResult;
  }

  /**
   * Check network status
   */
  checkNetworkStatus() {
    this.offlineMode = !navigator.onLine;
    console.log(`Network status: ${this.offlineMode ? "Offline" : "Online"}`);
  }

  /**
   * Handle network status changes
   */
  async handleNetworkChange() {
    this.checkNetworkStatus();

    if (!this.offlineMode && this.reconnectAttempts > 0) {
      // We're back online after being offline
      console.log(
        "Network connection restored. Attempting to restore session..."
      );
      this.toast.info("Network connection restored. Restoring session...");
      this.reconnectAttempts = 0;
      await this.checkSession();
    }

    if (this.offlineMode) {
      console.log("Network connection lost. Switching to offline mode...");
      this.toast.warning(
        "Network connection lost. Some features may be unavailable."
      );
    }
  }

  /**
   * Check if the user has a valid session
   * @returns {Promise<Object>} Session status
   */
  async checkSession() {
    // Prevent multiple simultaneous checks
    if (this.isCheckingSession) {
      console.log("Session check already in progress");
      return { authenticated: false, checking: true };
    }

    this.isCheckingSession = true;
    console.log("Checking session status...");

    try {
      // First try to use the stored token if available
      const storedToken = localStorage.getItem(SESSION_TOKEN_KEY);
      const storedExpiry = localStorage.getItem(SESSION_EXPIRY_KEY);

      // If we have a stored token and it's not expired, use it
      if (
        storedToken &&
        storedExpiry &&
        new Date().getTime() < parseInt(storedExpiry)
      ) {
        console.log("Using stored session token");

        // Set the token in the Authorization header
        axios.defaults.headers.common[
          "Authorization"
        ] = `Bearer ${storedToken}`;
      }

      // Make the session check request
      const response = await axios.get(`${API_BASE_URL}/check-session`, {
        withCredentials: true,
        timeout: 8000, // 8 second timeout, helpful for slow mobile connections
      });

      console.log("Session check response:", response.data);

      if (response.data && response.data.authenticated) {
        // Store the new token if provided
        if (response.data.token) {
          this.storeSessionToken(response.data.token, response.data.expiresIn);
        }

        // Update localStorage with latest user info
        this.updateLocalUserData(response.data.user);

        return {
          authenticated: true,
          user: response.data.user,
        };
      } else {
        // Clear any stored data if not authenticated
        this.clearSessionData();

        return {
          authenticated: false,
        };
      }
    } catch (error) {
      console.error("Session check error:", error);

      // Check if we're offline
      if (
        !navigator.onLine ||
        (error.message && error.message.includes("Network Error"))
      ) {
        console.log("Network appears to be offline");
        this.offlineMode = true;

        // Try to use local data if available
        const authData = authService.getCurrentAuth();
        if (authData.authenticated) {
          console.log("Using cached authentication data in offline mode");

          // Schedule a retry when we might be back online
          this.scheduleOfflineRetry();

          return {
            authenticated: true,
            user: authData.user,
            offlineMode: true,
          };
        }
      }

      // Clear session data on error
      this.clearSessionData();

      return {
        authenticated: false,
        error:
          "Session check failed. " +
          (error.response?.data?.message || error.message || "Unknown error"),
      };
    } finally {
      this.isCheckingSession = false;
    }
  }

  /**
   * Store session token and expiry
   * @param {string} token - Session token
   * @param {number} expiresIn - Expiry time in seconds
   */
  storeSessionToken(token, expiresIn = 86400) {
    // Store token in localStorage
    localStorage.setItem(SESSION_TOKEN_KEY, token);

    // Calculate and store expiry time (current time + expiresIn in ms)
    const expiryTime = new Date().getTime() + expiresIn * 1000;
    localStorage.setItem(SESSION_EXPIRY_KEY, expiryTime.toString());

    // Set for future API calls
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;

    console.log(`Session token stored. Expires in ${expiresIn} seconds`);
  }

  /**
   * Clear session data from storage
   */
  clearSessionData() {
    localStorage.removeItem(SESSION_TOKEN_KEY);
    localStorage.removeItem(SESSION_EXPIRY_KEY);
    delete axios.defaults.headers.common["Authorization"];
  }

  /**
   * Update local user data
   * @param {Object} user - User data
   */
  updateLocalUserData(user) {
    if (!user) return;

    localStorage.setItem("userId", user.id);
    localStorage.setItem("username", user.username);
    localStorage.setItem("userRole", user.role);

    // Add timestamp for data freshness tracking
    localStorage.setItem("userDataTimestamp", new Date().getTime().toString());
  }

  /**
   * Start automatic session refresh
   */
  startSessionRefresh() {
    // Clear any existing interval
    if (this.sessionInterval) {
      clearInterval(this.sessionInterval);
    }

    console.log(
      `Starting session refresh interval (every ${
        SESSION_REFRESH_INTERVAL / 1000
      } seconds)`
    );

    // Set up new refresh interval
    this.sessionInterval = setInterval(async () => {
      // Skip refresh if we're offline
      if (this.offlineMode) {
        console.log("Skipping session refresh - device is offline");
        return;
      }

      console.log("Performing scheduled session refresh");
      await this.checkSession();
    }, SESSION_REFRESH_INTERVAL);
  }

  /**
   * Stop automatic session refresh
   */
  stopSessionRefresh() {
    if (this.sessionInterval) {
      clearInterval(this.sessionInterval);
      this.sessionInterval = null;
      console.log("Session refresh stopped");
    }
  }

  /**
   * Schedule a retry when device is offline
   */
  scheduleOfflineRetry() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log("Maximum reconnect attempts reached");
      return;
    }

    this.reconnectAttempts++;

    console.log(
      `Scheduling offline retry attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${OFFLINE_RETRY_DELAY}ms`
    );

    setTimeout(async () => {
      // Check if we're back online
      if (navigator.onLine) {
        console.log(
          "Network appears to be back online, attempting session check"
        );
        await this.checkSession();
      } else {
        console.log("Still offline, rescheduling retry");
        this.scheduleOfflineRetry();
      }
    }, OFFLINE_RETRY_DELAY);
  }

  /**
   * Create a session after successful login
   * @param {Object} userData - User data from login
   * @param {string} token - Session token (if available)
   */
  createSession(userData, token = null) {
    if (!userData) return false;

    // Update local storage with user data
    this.updateLocalUserData(userData);

    // If token is provided, store it
    if (token) {
      this.storeSessionToken(token, userData.expiresIn || 86400);
    }

    // Start session refresh
    this.startSessionRefresh();

    return true;
  }

  /**
   * Destroy the current session (logout)
   */
  destroySession() {
    // Stop refresh interval
    this.stopSessionRefresh();

    // Clear session data
    this.clearSessionData();

    // Clear user data
    localStorage.removeItem("userId");
    localStorage.removeItem("username");
    localStorage.removeItem("userRole");
    localStorage.removeItem("userDataTimestamp");

    console.log("Session destroyed");
    return true;
  }
}

// Create singleton instance
const sessionService = new SessionService();
export default sessionService;
