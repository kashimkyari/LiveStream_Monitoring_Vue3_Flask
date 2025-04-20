<template>
  <div class="mobile-login-container">
    <!-- Show Login Form when not in Forgot Password mode and not in Create Account mode -->
    <form v-if="!showForgotPassword && !showCreateAccount" @submit.prevent="handleSubmit" class="mobile-login-form" ref="loginForm">
      <div class="logo-container" ref="logoContainer">
        <font-awesome-icon icon="user-lock" class="logo-icon" />
      </div>
      <h2 class="welcome-text" ref="welcomeText">Welcome Back</h2>
      <p class="subtitle" ref="subtitle">Sign in to continue</p>
      
      <div class="form-content" ref="formContent">
        <div class="input-group" ref="usernameGroup">
          <div class="input-container">
            <font-awesome-icon icon="user" class="input-icon" />
            <input
              type="text"
              id="username"
              v-model="username"
              :disabled="loading"
              class="input-field"
              autocomplete="username"
              placeholder="Username or Email"
              required
              ref="usernameInput"
            />
          </div>
        </div>

        <div class="input-group" ref="passwordGroup">
          <div class="input-container">
            <font-awesome-icon icon="lock" class="input-icon" />
            <input
              type="password"
              id="password"
              v-model="password"
              :disabled="loading"
              class="input-field"
              autocomplete="current-password"
              placeholder="Password"
              required
              ref="passwordInput"
            />
          </div>
        </div>

        <button type="submit" class="login-button" :disabled="loading" ref="loginButton">
          <template v-if="loading">
            <font-awesome-icon icon="spinner" spin class="mr-2" />
            Signing In...
          </template>
          <template v-else>
            <font-awesome-icon icon="sign-in-alt" class="mr-2" />
            Sign In
          </template>
        </button>
      </div>

      <div class="additional-links" ref="additionalLinks">
        <a href="#" class="link-text" @click.prevent="forgotPassword">Forgot password?</a>
        <span class="separator">•</span>
        <a href="#" class="link-text" @click.prevent="createAccount">Create account</a>
      </div>
    </form>
    
    <MobileForgotPassword 
      v-else-if="showForgotPassword" 
      @back="showForgotPassword = false" 
    />
    <MobileCreateAccount 
      v-else-if="showCreateAccount" 
      @back="showCreateAccount = false" 
      @account-created="handleAccountCreated"
    />
  </div>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useToast } from 'vue-toastification'
import "vue-toastification/dist/index.css"
import api from '@/services/api'
import MobileForgotPassword from './MobileForgotPassword.vue'
import MobileCreateAccount from './MobileCreateAccount.vue'

export default {
  name: 'MobileLoginComponent',
  components: { 
    FontAwesomeIcon,
    MobileForgotPassword,
    MobileCreateAccount
  },
  emits: ['login-success'],
  setup() {
    const toast = useToast()
    return { toast }
  },
  data() {
    return {
      username: '',
      password: '',
      loading: false,
      error: null,
      showForgotPassword: false,
      showCreateAccount: false,
      sessionChecking: false
    }
  },
  mounted() {
    // Check if user is already authenticated when component mounts
    this.checkSession();
  },
  methods: {
    async checkSession() {
      this.sessionChecking = true;
      
      try {
        console.log("Checking session status...");
        const response = await api.get('/api/session');
        
        if (response.status === 200 && response.data.isLoggedIn) {
          console.log("User already logged in as:", response.data.user.role);
          this.$emit('login-success', response.data.user);
          
          this.toast.success("Welcome back!", {
            timeout: 2000,
            position: "top-center",
            icon: true
          });
        }
      } catch (error) {
        console.error('Session check failed:', error);
        
        // Only show error if it's not a 401 (which is expected for logged out users)
        if (error.response && error.response.status !== 401) {
          this.toast.error("Could not verify login status. Please check your connection.", {
            timeout: 5000,
            position: "top-center",
            icon: true
          });
        }
      } finally {
        this.sessionChecking = false;
      }
    },
    
    async handleSubmit() {
      if (!this.username.trim() || !this.password.trim()) {
        this.showError('Please fill in all fields');
        return;
      }

      this.loading = true;
      this.error = null;
      
      try {
        const response = await api.post('/api/login', {
              username: this.username,
              password: this.password
            });

        if (response.status === 200 && response.data.message === "Login successful") {
          this.toast.success("Login successful!", {
            timeout: 2000,
            position: "top-center",
            icon: true
          });
          
          const userData = {
            role: response.data.role,
            username: response.data.username
          };
          
          setTimeout(() => {
            this.$emit('login-success', userData);
          }, 500);
        } else {
          this.showError(response.data.message || 'Login failed. Please try again.');
        }
      } catch (error) {
        console.error('Login error:', error);
        if (error.response) {
          // Server responded with error status
          this.showError(error.response.data?.message || 
                        `Server error: ${error.response.status} ${error.response.statusText}`);
        } else if (error.request) {
          // Request was made but no response received
          this.showError('Network error - please check your connection');
        } else {
          // Something else happened
          this.showError(error.message || 'Login failed. Please try again.');
        }
      } finally {
        this.loading = false;
      }
    },
    
    forgotPassword() {
      // Show the ForgotPassword component
      this.showForgotPassword = true;
    },
    
    createAccount() {
      // Show the CreateAccount component
      this.showCreateAccount = true;
    },
    
    handleAccountCreated(username) {
      // Auto-login after account creation
      this.username = username;
      this.showCreateAccount = false;
      
      this.toast.success("Account created successfully! You can now log in.", {
        timeout: 3000,
        position: "top-center",
        icon: true
      });
    },
    
    showError(message) {
      this.error = message;
      this.toast.error(message, {
        timeout: 5000,
        position: "top-center",
        icon: true,
        closeButton: true
      });
    }
  }
}
</script>

<style scoped>
.mobile-login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  width: 100%;
  padding: 1rem;
  background-color: var(--bs-dark);
}

.mobile-login-form {
  width: 100%;
  max-width: 480px;
  padding: 1.5rem;
  background: var(--bs-gray-800);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  position: relative;
}

.logo-container {
  text-align: center;
  margin-bottom: 1.5rem;
}

.logo-icon {
  font-size: 2rem;
  color: var(--bs-info);
  padding: 1rem;
  border-radius: 50%;
  background: rgba(13, 202, 240, 0.1);
}

.welcome-text {
  color: white;
  font-size: 1.5rem;
  text-align: center;
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.subtitle {
  color: var(--bs-gray-400);
  text-align: center;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.form-content {
  margin-top: 1rem;
}

.input-group {
  margin-bottom: 1rem;
}

.input-container {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--bs-gray-500);
  font-size: 0.9rem;
}

.input-field {
  width: 100%;
  padding: 0.8rem 0.8rem 0.8rem 2.5rem;
  border: 1px solid var(--bs-gray-700);
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  background: var(--bs-gray-900);
}

.input-field:focus {
  border-color: var(--bs-info);
  outline: none;
}

.login-button {
  width: 100%;
  padding: 0.8rem;
  background: var(--bs-info);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.login-button:disabled {
  opacity: 0.7;
}

.additional-links {
  margin-top: 1.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}

.link-text {
  color: var(--bs-gray-300);
  text-decoration: none;
  font-size: 0.85rem;
}

.separator {
  color: var(--bs-gray-500);
  font-size: 0.85rem;
}

@media (max-width: 480px) {
  .mobile-login-container {
    padding: 0.5rem;
  }
  
  .mobile-login-form {
    padding: 1.25rem;
  }
}
</style>