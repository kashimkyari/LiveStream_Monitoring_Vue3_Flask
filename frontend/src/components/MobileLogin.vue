<template>
  <div class="mobile-login">
    <!-- Theme toggle button added for accessibility -->
    <button 
      @click="toggleTheme" 
      class="theme-toggle"
      :aria-label="isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'"
      role="switch"
      :aria-checked="isDarkMode"
    >
      <font-awesome-icon :icon="isDarkMode ? 'sun' : 'moon'" />
    </button>
    
    <div class="login-container">
      <div class="login-header">
        <h1 class="login-title">Login</h1>
        <p class="login-subtitle">Sign in to your account</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Username</label>
          <div class="input-container">
            <font-awesome-icon icon="user" class="input-icon" />
            <input 
              type="text" 
              id="username" 
              v-model="username" 
              placeholder="Enter your username"
              required
              autocomplete="username"
              :disabled="isLoading"
            >
          </div>
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <div class="input-container">
            <font-awesome-icon icon="lock" class="input-icon" />
            <input 
              :type="showPassword ? 'text' : 'password'"
              id="password" 
              v-model="password" 
              placeholder="Enter your password"
              required
              autocomplete="current-password"
              :disabled="isLoading"
            >
            <button 
              type="button" 
              class="toggle-password"
              @click="togglePasswordVisibility"
              :disabled="isLoading"
              aria-label="Toggle password visibility"
            >
              <font-awesome-icon :icon="showPassword ? 'eye-slash' : 'eye'" />
            </button>
          </div>
        </div>
        
        <div class="form-options">
          <div class="remember-me">
            <input 
              type="checkbox" 
              id="remember" 
              v-model="rememberMe"
              :disabled="isLoading"
            >
            <label for="remember">Remember me</label>
          </div>
          <button 
            type="button" 
            class="forgot-password-link"
            @click="goToForgotPassword"
            :disabled="isLoading"
          >
            Forgot password?
          </button>
        </div>
        
        <div v-if="errorMessage" class="error-message">
          <font-awesome-icon icon="exclamation-circle" />
          <span>{{ errorMessage }}</span>
        </div>
        
        <button 
          type="submit" 
          class="login-button"
          :disabled="isLoading"
        >
          <span v-if="!isLoading">Sign In</span>
          <div v-else class="spinner">
            <font-awesome-icon icon="spinner" spin />
          </div>
        </button>
        
        
        
        
        
        <div class="register-option">
          <span>Don't have an account?</span>
          <button 
            type="button" 
            class="register-link"
            @click="goToRegister"
            :disabled="isLoading"
          >
            Create Account
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, inject, onMounted } from 'vue';
import AuthService from '../services/AuthService';
import { useToast } from 'vue-toastification';

export default {
  name: 'MobileLogin',
  emits: ['login-success', 'forgot-password', 'create-account'],
  setup(props, { emit }) {
    // State
    const username = ref('');
    const password = ref('');
    const rememberMe = ref(false);
    const showPassword = ref(false);
    const isLoading = ref(false);
    const errorMessage = ref('');
    
    // Theme state
    const isDarkMode = ref(false);
    
    // Toast notifications
    const toast = useToast();
    
    // Get context help functions from global context
    const analyzeContext = inject('analyzeContext', null);
    
    // Theme detection and toggle methods
    const detectPreferredTheme = () => {
      // Check localStorage first
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme) {
        isDarkMode.value = savedTheme === 'dark';
      } else {
        // Check system preference as fallback
        isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
      }
      
      // Apply theme to document
      applyTheme();
    };
    
    const toggleTheme = () => {
      isDarkMode.value = !isDarkMode.value;
      localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light');
      applyTheme();
    };
    
    const applyTheme = () => {
      // Set data-theme attribute on document body
      document.documentElement.setAttribute('data-theme', isDarkMode.value ? 'dark' : 'light');
    };
    
    // Original methods
    const togglePasswordVisibility = () => {
      showPassword.value = !showPassword.value;
    };
    
    const handleLogin = async () => {
      if (!username.value || !password.value) {
        errorMessage.value = 'Please enter both username and password.';
        return;
      }
      
      isLoading.value = true;
      errorMessage.value = '';
      
      try {
        const result = await AuthService.login(username.value, password.value);
        
        if (result.success) {
          // Save username in localStorage if remember me is checked

           
          if (rememberMe.value) {
            localStorage.setItem('rememberedUsername', username.value);
          } else {
            localStorage.removeItem('rememberedUsername');
          }

          
          toast.success('Login successful!');
          emit('login-success', result.user);
          window.location.href = '/';

          
          
        }

         else {
          const errorMsg = result.message || 'Login failed. Please try again.';
          errorMessage.value = errorMsg;
          
          // Show help bubble for login error
          if (analyzeContext) {
            analyzeContext({
              screen: 'login',
              action: 'error',
              error: { message: errorMsg }
            });
          }
        }
      } catch (error) {
        console.error('Login error:', error);
        const errorMsg = 'An unexpected error occurred. Please try again.';
        errorMessage.value = errorMsg;
        
        // Show help bubble for login error
        if (analyzeContext) {
          analyzeContext({
            screen: 'login',
            action: 'error',
            error: { 
              message: errorMsg,
              details: error.message || 'Connection error'
            }
          });
        }
      } finally {
        isLoading.value = false;
        // Redirect to home page
         
      }
    };
    
    const goToForgotPassword = () => {
      // Emit event to navigate to the MobileForgotPasswordComponent
      emit('forgot-password');
    };

    const goToRegister = () => {
      // Emit event to navigate to the MobileCreateAccountComponent
      emit('create-account');
    };
    
    onMounted(() => {
      // Initialize theme
      detectPreferredTheme();
      
      // Listen for system theme changes
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        // Only update if the user hasn't set a preference already
        if (!localStorage.getItem('theme')) {
          isDarkMode.value = e.matches;
          applyTheme();
        }
      });
      
      // Check if username is stored in localStorage
      const rememberedUsername = localStorage.getItem('rememberedUsername');
      if (rememberedUsername) {
        username.value = rememberedUsername;
        rememberMe.value = true;
      }
      
      // Show login help for first-time users
      setTimeout(() => {
        if (analyzeContext) {
          analyzeContext({
            screen: 'login',
            action: 'view',
            isFirstTime: !localStorage.getItem('login_help_shown')
          });
          
          // Mark that login help has been shown
          localStorage.setItem('login_help_shown', 'true');
        }
      }, 500);
    });
    
    return {
      username,
      password,
      rememberMe,
      showPassword,
      isLoading,
      errorMessage,
      isDarkMode,
      toggleTheme,
      togglePasswordVisibility,
      handleLogin,
      goToForgotPassword,
      goToRegister
    };
  }
};
</script>

<style scoped>
/* Define color variables for light and dark themes */
:root {
  /* Light theme (default) */
  --primary-color: #5e72e4;
  --primary-dark: #324cdd;
  --secondary-color: #8392ab;
  --success-color: #2dce89;
  --info-color: #11cdef;
  --warning-color: #fb6340;
  --danger-color: #f5365c;
  --background-color: #f8f9fe;
  --surface-color: #ffffff;
  --text-primary: #32325d;
  --text-secondary: #8898aa;
  --border-color: #e9ecef;
  --input-bg: #ffffff;
  --shadow-color: rgba(0, 0, 0, 0.05);
  --shadow-color-intense: rgba(50, 50, 93, 0.1);
  --focus-ring-color: rgba(94, 114, 228, 0.2);
  --error-bg: rgba(245, 54, 92, 0.1);
  --hover-bg: rgba(0, 0, 0, 0.05);
  --social-google: #ea4335;
  --social-apple: #000000;
  --divider-color: rgba(0, 0, 0, 0.1);
}

/* Dark theme styles */
[data-theme="dark"] {
  --primary-color: #7986e7;
  --primary-dark: #5e72e4;
  --secondary-color: #a0b0c8;
  --success-color: #4dd4a0;
  --info-color: #45d8f3;
  --warning-color: #fc8b6a;
  --danger-color: #f76d8c;
  --background-color: #121212;
  --surface-color: #1e1e2d;
  --text-primary: #e2e4f3;
  --text-secondary: #b3b9cc;
  --border-color: #2e3344;
  --input-bg: #2a2a3c;
  --shadow-color: rgba(0, 0, 0, 0.2);
  --shadow-color-intense: rgba(0, 0, 0, 0.25);
  --focus-ring-color: rgba(126, 143, 241, 0.4);
  --error-bg: rgba(245, 54, 92, 0.2);
  --hover-bg: rgba(255, 255, 255, 0.07);
  --social-google: #ea4335;
  --social-apple: #ffffff;
  --divider-color: rgba(255, 255, 255, 0.15);
}

/* Mobile-first approach - base styles are for mobile */
.mobile-login {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  min-height: 100vh;
  padding: 1rem;
  background-color: var(--background-color);
  width: 100%;
  position: relative; /* For positioning the theme toggle */
  transition: background-color 0.3s ease;
}

/* Theme toggle button positioning and styling */
.theme-toggle {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background-color: var(--surface-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  cursor: pointer;
  z-index: 10;
  box-shadow: 0 2px 10px var(--shadow-color);
  transition: all 0.2s ease;
}

.theme-toggle:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  outline-offset: 2px;
}

.theme-toggle:active {
  transform: translateY(1px);
}

.login-container {
  width: 100%;
  max-width: 100%; /* Full width on mobile */
  background-color: var(--surface-color);
  border-radius: 1rem;
  box-shadow: 0 0.25rem 0.75rem var(--shadow-color);
  padding: 1.5rem;
  margin-top: 4rem; /* Increased for better spacing with theme toggle */
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}

.login-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.login-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: var(--primary-color);
  transition: color 0.3s ease;
}

.login-subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
  transition: color 0.3s ease;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  transition: color 0.3s ease;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 0.875rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  transition: color 0.3s ease;
}

.input-container input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 2.5rem;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  font-size: 1rem;
  background-color: var(--input-bg);
  color: var(--text-primary);
  transition: all 0.3s ease;
  height: 3rem;
  -webkit-appearance: none; /* Remove default styling on iOS */
}

.input-container input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--focus-ring-color);
  outline: none;
}

.input-container input:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  outline-offset: 1px;
}

.input-container input::placeholder {
  color: var(--text-secondary);
  opacity: 0.7;
}

.toggle-password {
  position: absolute;
  right: 0.875rem;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.875rem;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 3rem;
  width: 3rem; /* Increased for better touch target */
  min-width: 3rem; /* Ensure minimum width for accessibility */
  transition: color 0.2s ease;
}

.toggle-password:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  border-radius: 0.25rem;
}

.toggle-password:active {
  color: var(--primary-color);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.remember-me input[type="checkbox"] {
  width: 1.25rem; /* Increased for better touch target */
  height: 1.25rem; /* Increased for better touch target */
  accent-color: var(--primary-color);
  margin: 0;
  -webkit-appearance: none;
  appearance: none;
  border: 1px solid var(--border-color);
  border-radius: 0.25rem;
  position: relative;
  background-color: var(--input-bg);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.remember-me input[type="checkbox"]:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  outline-offset: 1px;
}

.remember-me input[type="checkbox"]:checked {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.remember-me input[type="checkbox"]:checked::after {
  content: '';
  position: absolute;
  top: 0.25rem;
  left: 0.4rem;
  width: 0.25rem;
  height: 0.5rem;
  border: solid white;
  border-width: 0 0.125rem 0.125rem 0;
  transform: rotate(45deg);
}

.remember-me label {
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.875rem; /* Increased for readability */
  transition: color 0.3s ease;
}

.forgot-password-link {
  color: var(--primary-color);
  background: none;
  border: none;
  padding: 0.5rem; /* Added padding for better touch target */
  font-size: 0.875rem; /* Increased for readability */
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: color 0.2s;
  min-height: 2.5rem; /* Ensure minimum height for accessibility */
  border-radius: 0.25rem;
}

.forgot-password-link:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  outline-offset: 1px;
}

.forgot-password-link:active {
  color: var(--primary-dark);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: var(--error-bg);
  color: var(--danger-color);
  border-radius: 0.5rem;
  font-size: 0.875rem; /* Increased for readability */
  margin-top: 0.5rem;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.login-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0;
  font-size: 1rem; /* Increased for readability */
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 3rem; /* Increased for better touch target */
  width: 100%;
  margin-top: 0.5rem;
  box-shadow: 0 0.25rem 0.375rem var(--shadow-color-intense), 0 0.0625rem 0.1875rem var(--shadow-color);
}

.login-button:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  outline-offset: 2px;
}

.login-button:active {
  background-color: var(--primary-dark);
  transform: translateY(1px);
}

.login-button:disabled {
  background-color: var(--secondary-color);
  cursor: not-allowed;
  opacity: 0.7;
  box-shadow: none;
}

.spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.125rem;
  color: white;
}

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 1.25rem 0;
  font-size: 0.875rem; /* Increased for readability */
  color: var(--text-secondary);
  transition: color 0.3s ease;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--border-color);
  transition: border-color 0.3s ease;
}

.divider::before {
  margin-right: 0.75rem;
}

.divider::after {
  margin-left: 0.75rem;
}

.social-login {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.social-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0;
  height: 3rem; /* Increased for better touch target */
  border-radius: 0.5rem;
  font-size: 1rem; /* Increased for readability */
  font-weight: 600;
  border: 1px solid var(--border-color);
  background-color: var(--surface-color);
  cursor: pointer;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.social-button:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  outline-offset: 2px;
}

.social-button.google {
  color: var(--social-google);
}

.social-button.apple {
  color: var(--social-apple);
}

.social-button:active {
  background-color: var(--hover-bg);
}

.register-option {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem; /* Increased for readability */
  margin-top: 1.5rem;
  color: var(--text-secondary);
  transition: color 0.3s ease;
}

.register-link {
  color: var(--primary-color);
  background: none;
  border: none;
  padding: 0.5rem; /* Added padding for better touch target */
  font-weight: 600;
  font-size: 0.875rem; /* Increased for readability */
  cursor: pointer;
  transition: color 0.2s;
  min-height: 2.5rem; /* Ensure minimum height for accessibility */
  border-radius: 0.25rem;
}

.register-link:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  outline-offset: 1px;
}

.register-link:active {
  color: var(--primary-dark);
}

/* Fix for iOS input zoom issue */
@media screen and (-webkit-min-device-pixel-ratio: 0) {
  select,
  textarea,
  input[type="text"],
  input[type="password"],
  input[type="number"] {
    font-size: 16px; /* iOS doesn't zoom on inputs with font-size >= 16px */
  }
}

/* Media query for devices in portrait orientation */
@media screen and (orientation: portrait) {
  .login-container {
    margin-top: 5rem; /* Adjusted for theme toggle */
    padding: 1.75rem;
  }
}

/* Additional mobile-specific adjustments */
@media (max-width: 380px) {
  .login-container {
    padding: 1.25rem;
  }
  
  .login-title {
    font-size: 1.375rem;
  }
  
  .form-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .forgot-password-link {
    align-self: flex-end;
    margin-top: -2.5rem; /* Adjusted for larger touch target */
  }
}

/* Handle iPhone notch areas */
@supports (padding: max(0px)) {
  .mobile-login {
    padding-left: max(1rem, env(safe-area-inset-left));
    padding-right: max(1rem, env(safe-area-inset-right));
    padding-bottom: max(1rem, env(safe-area-inset-bottom));
    padding-top: max(1rem, env(safe-area-inset-top));
  }
  
  /* Adjust theme toggle position for notch */
  .theme-toggle {
    right: max(1rem, env(safe-area-inset-right));
    top: max(1rem, env(safe-area-inset-top));
  }
}
</style>