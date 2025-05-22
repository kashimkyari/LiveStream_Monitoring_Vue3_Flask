/**
 * Authentication Service
 *
 * Provides authentication functionality for both desktop and mobile interfaces
 * Features:
 * - Login/logout handling
 * - Registration
 * - Password reset
 * - Session management
 * - Improved mobile device support
 */
import axios from "axios";
import { useToast } from "vue-toastification";
import sessionService from "./SessionService";

// Define the API base URL - switched to HTTP for better compatibility
const API_BASE_URL = "     https://monitor-backend.jetcamstudio.com:5000"; // Local development API URL (relative path)

// Create axios instance with the base URL
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds timeout
  withCredentials: true, // Important for cookies/sessions across domains
});

class AuthService {
  constructor() {
    this.toast = useToast();
  }

  /**
   * Log in a user
   * @param {string} username - Username
   * @param {string} password - Password
   * @returns {Promise<Object>} - User data or error
   */
  async login(username, password) {
    try {
      const response = await apiClient.post("/api/login", {
        username,
        password,
      });

      if (response.data && response.data.success) {
        // Validate user role from server response
        const userRole =
          response.data.user.role || (username === "admin" ? "admin" : "agent");

        // Create session with user data and token
        sessionService.createSession(
          {
            ...response.data.user,
            role: userRole, // Ensure role is set
          },
          response.data.token || null
        );

        // Set theme if not set
        if (!localStorage.getItem("theme")) {
          localStorage.setItem("theme", "light");
        }

        return {
          success: true,
          user: {
            ...response.data.user,
            role: userRole,
          },
        };
      } else {
        return {
          success: false,
          message: response.data.message || "Login failed.",
        };
      }
    } catch (error) {
      console.error("Login error:", error);

      // Provide more specific error messages for mobile users
      let errorMessage = "Login failed. Please try again.";

      if (error.response) {
        if (error.response.status === 401) {
          errorMessage = "Invalid username or password.";
        } else if (error.response.status === 429) {
          errorMessage = "Too many login attempts. Please try again later.";
        } else if (error.response.data && error.response.data.message) {
          errorMessage = error.response.data.message;
        }
      } else if (error.request) {
        errorMessage =
          "Network error. Please check your connection and server availability.";
      }

      return {
        success: false,
        message: errorMessage,
      };
    }
  }

  /**
   * Log out the current user
   * @returns {Promise<boolean>} - Success status
   */
  async logout() {
    try {
      // First try to notify the server
      await apiClient.post("/api/logout");
    } catch (error) {
      console.error("Logout error on server:", error);
      // Continue with local logout even if server request fails
    } finally {
      // Always destroy the local session
      sessionService.destroySession();
    }

    return true;
  }

  /**
   * Register a new user
   * @param {string} username - Username
   * @param {string} email - Email
   * @param {string} password - Password
   * @returns {Promise<Object>} - Registration result
   */
  async register(username, email, password) {
    try {
      const response = await apiClient.post("/api/register", {
        username,
        email,
        password,
      });

      if (response.data && response.data.success) {
        // Automatically log in after successful registration if token provided
        if (response.data.token) {
          sessionService.createSession(response.data.user, response.data.token);
        }

        return {
          success: true,
          user: response.data.user,
        };
      } else {
        return {
          success: false,
          message: response.data.message || "Registration failed.",
        };
      }
    } catch (error) {
      console.error("Registration error:", error);

      // Provide more specific error messages
      let errorMessage = "Registration failed. Please try again.";

      if (error.response) {
        if (error.response.status === 409) {
          if (error.response.data && error.response.data.field === "username") {
            errorMessage = "Username already exists. Please choose another.";
          } else if (
            error.response.data &&
            error.response.data.field === "email"
          ) {
            errorMessage =
              "Email already registered. Please use another email.";
          } else {
            errorMessage = "Account already exists.";
          }
        } else if (error.response.data && error.response.data.message) {
          errorMessage = error.response.data.message;
        }
      } else if (error.request) {
        errorMessage = "Network error. Please check your connection.";
      }

      return {
        success: false,
        message: errorMessage,
      };
    }
  }

  /**
   * Send password reset request
   * @param {string} email - Email address
   * @returns {Promise<Object>} - Reset request result
   */
  async forgotPassword(email) {
    try {
      const response = await apiClient.post("/api/forgot-password", {
        email,
      });

      if (response.data && response.data.success) {
        return {
          success: true,
          message: response.data.message || "Password reset email sent.",
        };
      } else {
        return {
          success: false,
          message: response.data.message || "Failed to send reset email.",
        };
      }
    } catch (error) {
      console.error("Password reset request error:", error);

      let errorMessage = "Failed to send reset email. Please try again.";

      if (
        error.response &&
        error.response.data &&
        error.response.data.message
      ) {
        errorMessage = error.response.data.message;
      } else if (error.request) {
        errorMessage = "Network error. Please check your connection.";
      }

      return {
        success: false,
        message: errorMessage,
      };
    }
  }

  /**
   * Reset password with token
   * @param {string} token - Reset token
   * @param {string} password - New password
   * @returns {Promise<Object>} - Password reset result
   */
  async resetPassword(token, password) {
    try {
      const response = await apiClient.post("/api/reset-password", {
        token,
        password,
      });

      if (response.data && response.data.success) {
        return {
          success: true,
          message: response.data.message || "Password reset successful.",
        };
      } else {
        return {
          success: false,
          message: response.data.message || "Failed to reset password.",
        };
      }
    } catch (error) {
      console.error("Password reset error:", error);

      let errorMessage = "Failed to reset password. Please try again.";

      if (error.response) {
        if (error.response.status === 400) {
          errorMessage =
            "Invalid or expired token. Please request a new reset link.";
        } else if (error.response.data && error.response.data.message) {
          errorMessage = error.response.data.message;
        }
      } else if (error.request) {
        errorMessage = "Network error. Please check your connection.";
      }

      return {
        success: false,
        message: errorMessage,
      };
    }
  }

  /**
   * Verify reset token
   * @param {string} token - Reset token
   * @returns {Promise<Object>} - Token verification result
   */
  async verifyResetToken(token) {
    try {
      const response = await apiClient.post("/api/verify-reset-token", {
        token,
      });

      if (response.data && response.data.success) {
        return {
          success: true,
          user: response.data.user,
        };
      } else {
        return {
          success: false,
          message: response.data.message || "Invalid or expired token.",
        };
      }
    } catch (error) {
      console.error("Token verification error:", error);

      let errorMessage = "Token verification failed.";

      if (error.response && error.response.status === 400) {
        errorMessage =
          "Invalid or expired token. Please request a new reset link.";
      } else if (
        error.response &&
        error.response.data &&
        error.response.data.message
      ) {
        errorMessage = error.response.data.message;
      }

      return {
        success: false,
        message: errorMessage,
      };
    }
  }

  /**
   * Change password for authenticated user
   * @param {string} currentPassword - Current password
   * @param {string} newPassword - New password
   * @returns {Promise<Object>} - Password change result
   */
  async changePassword(currentPassword, newPassword) {
    try {
      const response = await apiClient.post("/api/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });

      if (response.data && response.data.success) {
        return {
          success: true,
          message: response.data.message || "Password changed successfully.",
        };
      } else {
        return {
          success: false,
          message: response.data.message || "Failed to change password.",
        };
      }
    } catch (error) {
      console.error("Password change error:", error);

      let errorMessage = "Failed to change password. Please try again.";

      if (error.response) {
        if (error.response.status === 401) {
          errorMessage = "Current password is incorrect.";
        } else if (error.response.data && error.response.data.message) {
          errorMessage = error.response.data.message;
        }
      } else if (error.request) {
        errorMessage = "Network error. Please check your connection.";
      }

      return {
        success: false,
        message: errorMessage,
      };
    }
  }

  /**
   * Check if a username is available
   * @param {string} username - Username to check
   * @returns {Promise<Object>} - Availability result
   */
  async checkUsername(username) {
    try {
      const response = await apiClient.post("/api/check-username", {
        username,
      });

      return {
        success: true,
        available: response.data.available,
      };
    } catch (error) {
      console.error("Username check error:", error);
      return {
        success: false,
        available: false,
        message: "Failed to check username availability.",
      };
    }
  }

  /**
   * Check if an email is available
   * @param {string} email - Email to check
   * @returns {Promise<Object>} - Availability result
   */
  async checkEmail(email) {
    try {
      const response = await apiClient.post("/check-email", {
        email,
      });

      return {
        success: true,
        available: response.data.available,
      };
    } catch (error) {
      console.error("Email check error:", error);
      return {
        success: false,
        available: false,
        message: "Failed to check email availability.",
      };
    }
  }

  /**
   * Check if user is authenticated
   * @returns {Promise<Object>} - Authentication status
   */
  async checkAuth() {
    // Delegate to the session service
    return sessionService.checkSession();
  }

  /**
   * Update user profile
   * @param {Object} profileData - Profile data to update
   * @returns {Promise<Object>} - Update result
   */
  async updateProfile(profileData) {
    try {
      const response = await apiClient.post("/api/update-profile", profileData);

      if (response.data && response.data.success) {
        // Update localStorage with updated user info
        if (response.data.user) {
          sessionService.updateLocalUserData(response.data.user);
        }

        return {
          success: true,
          user: response.data.user,
          message: response.data.message || "Profile updated successfully.",
        };
      } else {
        return {
          success: false,
          message: response.data.message || "Failed to update profile.",
        };
      }
    } catch (error) {
      console.error("Profile update error:", error);

      let errorMessage = "Failed to update profile. Please try again.";

      if (
        error.response &&
        error.response.data &&
        error.response.data.message
      ) {
        errorMessage = error.response.data.message;
      }

      return {
        success: false,
        message: errorMessage,
      };
    }
  }

  /**
   * Get current authentication status from localStorage
   * @returns {Object} Current auth status
   */
  getCurrentAuth() {
    const userId = localStorage.getItem("userId");
    const username = localStorage.getItem("username");
    const userRole = localStorage.getItem("userRole");
    const timestamp = localStorage.getItem("userDataTimestamp");

    if (userId && username) {
      return {
        authenticated: true,
        user: {
          id: userId,
          username,
          role: userRole || "agent",
        },
        timestamp: timestamp ? parseInt(timestamp) : null,
      };
    }

    return {
      authenticated: false,
    };
  }
}

// Create singleton instance
const authService = new AuthService();
export default authService;
