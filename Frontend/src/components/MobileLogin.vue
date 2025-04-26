<template>
  <div class="mobile-login">
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
        
        <div class="divider">
          <span>or</span>
        </div>
        
        <div class="social-login">
          <button type="button" class="social-button google">
            <font-awesome-icon :icon="['fab', 'google']" />
            <span>Sign in with Google</span>
          </button>
          <button type="button" class="social-button apple">
            <font-awesome-icon :icon="['fab', 'apple']" />
            <span>Sign in with Apple</span>
          </button>
        </div>
        
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
    
    // Toast notifications
    const toast = useToast();
    
    // Get context help functions from global context
    const analyzeContext = inject('analyzeContext', null);
    
    // Methods
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
          
          // Redirect to home page
          window.location.href = '/';
        } else {
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
      togglePasswordVisibility,
      handleLogin,
      goToForgotPassword,
      goToRegister
    };
  }
};
</script>

<style scoped>
:root {
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
}

.login-container {
  width: 100%;
  max-width: 100%; /* Full width on mobile */
  background-color: var(--surface-color);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  padding: 1.5rem;
  margin-top: 2rem;
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
}

.login-subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
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
}

.input-container input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 2.5rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  background-color: var(--input-bg);
  color: var(--text-primary);
  transition: all 0.2s ease;
  height: 48px;
  -webkit-appearance: none; /* Remove default styling on iOS */
}

.input-container input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(94, 114, 228, 0.2);
  outline: none;
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
  height: 48px;
  width: 32px;
  transition: color 0.2s ease;
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
  width: 1rem;
  height: 1rem;
  accent-color: var(--primary-color);
  margin: 0;
  -webkit-appearance: none;
  appearance: none;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  position: relative;
}

.remember-me input[type="checkbox"]:checked {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.remember-me input[type="checkbox"]:checked::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 5px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.remember-me label {
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.75rem;
}

.forgot-password-link {
  color: var(--primary-color);
  background: none;
  border: none;
  padding: 0;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: color 0.2s;
}

.forgot-password-link:active {
  color: var(--primary-dark);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: rgba(245, 54, 92, 0.1);
  color: var(--danger-color);
  border-radius: 8px;
  font-size: 0.75rem;
  margin-top: 0.5rem;
}

.login-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 48px;
  width: 100%;
  margin-top: 0.5rem;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
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
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--border-color);
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
  height: 48px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  border: 1px solid var(--border-color);
  background-color: var(--surface-color);
  cursor: pointer;
  transition: background-color 0.2s;
}

.social-button.google {
  color: #ea4335;
}

.social-button.apple {
  color: #000000;
}

.social-button:active {
  background-color: rgba(0, 0, 0, 0.05);
}

.register-option {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  margin-top: 1.5rem;
  color: var(--text-secondary);
}

.register-link {
  color: var(--primary-color);
  background: none;
  border: none;
  padding: 0;
  font-weight: 600;
  font-size: 0.75rem;
  cursor: pointer;
  transition: color 0.2s;
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
    font-size: 16px;
  }
}

/* Media query for devices in portrait orientation */
@media screen and (orientation: portrait) {
  .login-container {
    margin-top: 10vh;
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
    margin-top: -2rem;
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
}
</style>