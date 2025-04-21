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
import { ref, inject } from 'vue';
import AuthService from '../services/AuthService';
import { useToast } from 'vue-toastification';

export default {
  name: 'MobileLogin',
  emits: ['login-success', 'goto-forgot-password', 'goto-register'],
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
    const analyzeContext = inject('analyzeContext');
    
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
      emit('goto-forgot-password');
    };
    
    const goToRegister = () => {
      emit('goto-register');
    };
    
    // Initialize
    // Check if username is stored in localStorage
    const rememberedUsername = localStorage.getItem('rememberedUsername');
    if (rememberedUsername) {
      username.value = rememberedUsername;
      rememberMe.value = true;
    }
    
    // Show login help for first-time users
    // Get current context once component is mounted
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
    }, 500); // Small delay to ensure component is fully mounted
    
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
.mobile-login {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 1.5rem;
  background-color: var(--bs-body-bg);
}

.login-container {
  width: 100%;
  max-width: 400px;
  background-color: var(--bs-body-bg);
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: var(--bs-primary);
}

.login-subtitle {
  font-size: 1rem;
  color: var(--bs-secondary);
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.9rem;
  font-weight: 600;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 1rem;
  color: var(--bs-secondary);
  font-size: 1rem;
}

.input-container input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid var(--bs-border-color);
  border-radius: 8px;
  font-size: 1rem;
  background-color: var(--bs-tertiary-bg);
  color: var(--bs-body-color);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-container input:focus {
  border-color: var(--bs-primary);
  box-shadow: 0 0 0 2px rgba(var(--bs-primary-rgb), 0.25);
  outline: none;
}

.toggle-password {
  position: absolute;
  right: 1rem;
  background: none;
  border: none;
  color: var(--bs-secondary);
  cursor: pointer;
  font-size: 1rem;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.remember-me input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  accent-color: var(--bs-primary);
}

.forgot-password-link {
  color: var(--bs-primary);
  background: none;
  border: none;
  padding: 0;
  font-size: 0.9rem;
  cursor: pointer;
  text-decoration: underline;
  transition: color 0.2s;
}

.forgot-password-link:hover {
  color: var(--bs-primary-darker, var(--bs-primary));
  filter: brightness(0.9);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: var(--bs-danger-bg-subtle);
  color: var(--bs-danger);
  border-radius: 6px;
  font-size: 0.9rem;
}

.login-button {
  background-color: var(--bs-primary);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.875rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 3rem;
}

.login-button:hover {
  filter: brightness(0.9);
}

.login-button:disabled {
  background-color: var(--bs-secondary);
  cursor: not-allowed;
}

.spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.25rem;
}

.register-option {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  margin-top: 1rem;
}

.register-link {
  color: var(--bs-primary);
  background: none;
  border: none;
  padding: 0;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s;
}

.register-link:hover {
  color: var(--bs-primary-darker, var(--bs-primary));
  filter: brightness(0.9);
}
</style>