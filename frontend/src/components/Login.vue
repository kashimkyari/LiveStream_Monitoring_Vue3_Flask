<template>
  <div class="login-container">
    <!-- Show Login Form when not in Forgot Password mode and not in Create Account mode -->
    <form v-if="!showForgotPassword && !showCreateAccount" @submit.prevent="handleSubmit" class="login-form" ref="loginForm">
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
              placeholder=" "
              required
              ref="usernameInput"
            />
            <label for="username" class="input-label">Username</label>
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
              placeholder=" "
              required
              ref="passwordInput"
            />
            <label for="password" class="input-label">Password</label>
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
      </div>
      
      <div class="decorative-circles">
        <div class="circle circle-1" ref="circle1"></div>
        <div class="circle circle-2" ref="circle2"></div>
        <div class="circle circle-3" ref="circle3"></div>
      </div>
    </form>
    
    <ForgotPasswordComponent 
      v-else-if="showForgotPassword" 
      @back="showForgotPassword = false" 
    />
  </div>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useToast } from 'vue-toastification';
import "vue-toastification/dist/index.css"
import anime from 'animejs/lib/anime.es.js';
import api from '@/services/api'
import ForgotPasswordComponent from './ForgotPassword.vue'

export default {
  name: 'LoginComponent',
  components: { 
    FontAwesomeIcon,
    ForgotPasswordComponent
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
      sessionChecking: false
    }
  },
  mounted() {
    this.initializeAnimations();
    // Check if user is already authenticated when component mounts
    this.checkSession();
  },
  methods: {
    async checkSession() {
      this.sessionChecking = true;
      
      try {
        console.log("Checking session status...");
        const response = await api.get('/api/session');
        
        if (response.status === 200 && response.data.logged_in) {
          console.log("User already logged in as:", response.data.user.role);
  this.$emit('login-success', response.data.user.role);
          
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
    
    initializeAnimations() {
      // Initial animations when component mounts
      anime.timeline({
        easing: 'easeOutExpo',
      })
      .add({
        targets: this.$refs.loginForm,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800,
      })
      .add({
        targets: this.$refs.logoContainer,
        scale: [0.5, 1],
        opacity: [0, 1],
        duration: 700,
      }, '-=600')
      .add({
        targets: [this.$refs.welcomeText, this.$refs.subtitle],
        opacity: [0, 1],
        translateY: [10, 0],
        delay: anime.stagger(150),
        duration: 700,
      }, '-=500')
      .add({
        targets: [this.$refs.usernameGroup, this.$refs.passwordGroup, this.$refs.loginButton],
        opacity: [0, 1],
        translateY: [20, 0],
        delay: anime.stagger(150),
        duration: 700,
      }, '-=500')
      .add({
        targets: this.$refs.additionalLinks,
        opacity: [0, 1],
        translateY: [10, 0],
        duration: 700,
      }, '-=400')
      .add({
        targets: [this.$refs.circle1, this.$refs.circle2, this.$refs.circle3],
        scale: [0, 1],
        opacity: [0, 0.7],
        delay: anime.stagger(150),
        duration: 1000,
      }, '-=700');

      // Add focus animations to input fields
      this.setupInputAnimations();
      
      // Animate decorative circles continuously
      this.animateDecorations();
    },
    
    setupInputAnimations() {
      const inputs = [this.$refs.usernameInput, this.$refs.passwordInput];
      
      inputs.forEach(input => {
        if (!input) return;
        
        input.addEventListener('focus', () => {
          anime({
            targets: input.parentNode,
            scale: [1, 1.02],
            boxShadow: ['0 0 0 rgba(var(--primary-color-rgb), 0)', '0 0 15px rgba(var(--primary-color-rgb), 0.25)'],
            duration: 300,
            easing: 'easeOutCubic'
          });
        });
        
        input.addEventListener('blur', () => {
          anime({
            targets: input.parentNode,
            scale: [1.02, 1],
            boxShadow: ['0 0 15px rgba(var(--primary-color-rgb), 0.25)', '0 0 0 rgba(var(--primary-color-rgb), 0)'],
            duration: 300,
            easing: 'easeOutCubic'
          });
        });
      });
    },
    
    animateDecorations() {
      // Continuous animations for decorative elements
      if (this.$refs.circle1) {
        anime({
          targets: this.$refs.circle1,
          translateX: '10px',
          translateY: '15px',
          duration: 8000,
          direction: 'alternate',
          loop: true,
          easing: 'easeInOutSine'
        });
      }
      
      if (this.$refs.circle2) {
        anime({
          targets: this.$refs.circle2,
          translateX: '-15px',
          translateY: '-10px',
          duration: 9000,
          direction: 'alternate',
          loop: true,
          easing: 'easeInOutSine'
        });
      }
      
      if (this.$refs.circle3) {
        anime({
          targets: this.$refs.circle3,
          translateX: '8px',
          translateY: '-12px',
          duration: 7000,
          direction: 'alternate',
          loop: true,
          easing: 'easeInOutSine'
        });
      }
    },
    
    async handleSubmit() {
      if (!this.username.trim() || !this.password.trim()) {
        this.showError('Please fill in all fields')
        this.shakeForm();
        return;
      }

      this.loading = true;
      this.error = null;
      
      // Button animation when loading
      anime({
        targets: this.$refs.loginButton,
        scale: [1, 0.98],
        duration: 300,
        easing: 'easeInOutQuad'
      });
      
      try {
        const response = await api.post('/api/login', {
              username: this.username,
              password: this.password
            })

        if (response.status === 200 && response.data.message === "Login successful") {
          this.animateSuccessfulLogin();
          this.toast.success("Login successful!", {
            timeout: 2000,
            position: "top-center",
            icon: true
          })
          setTimeout(() => {
            this.$emit('login-success', response.data.role)
          }, 1200);
        } else {
          this.showError(response.data.message || 'Login failed. Please try again.')
          this.shakeForm();
        }
      } catch (error) {
        console.error('Login error:', error)
        if (error.response) {
          // Server responded with error status
          this.showError(error.response.data?.message || 
                        `Server error: ${error.response.status} ${error.response.statusText}`)
        } else if (error.request) {
          // Request was made but no response received
          this.showError('Network error - please check your connection')
        } else {
          // Something else happened
          this.showError(error.message || 'Login failed. Please try again.')
        }
        this.shakeForm();
      } finally {
        
        if (!this.loading); // Avoid animation if already reset by success animation
        
        anime({
          targets: this.$refs.loginButton,
          scale: [0.98, 1],
          duration: 300,
          easing: 'easeOutQuad'
        });
        this.loading = false;
      }
    },
    
    animateSuccessfulLogin() {
      anime.timeline({
        easing: 'easeOutExpo',
      })
      .add({
        targets: this.$refs.loginButton,
        scale: [0.98, 1.05],
        backgroundColor: ['var(--primary-color)', '#2ecc71'],
        duration: 500,
      })
      .add({
        targets: [this.$refs.usernameGroup, this.$refs.passwordGroup, this.$refs.additionalLinks],
        opacity: 0,
        translateY: -10,
        duration: 500,
        delay: anime.stagger(100)
      }, '-=300')
      .add({
        targets: this.$refs.loginButton,
        scale: [1.05, 1],
        duration: 200,
      }, '-=200');
    },
    
    shakeForm() {
      if (!this.$refs.loginForm) return;
      
      anime({
        targets: this.$refs.loginForm,
        translateX: [
          { value: -10, duration: 100, delay: 0 },
          { value: 10, duration: 100, delay: 0 },
          { value: -8, duration: 100, delay: 0 },
          { value: 8, duration: 100, delay: 0 },
          { value: -5, duration: 100, delay: 0 },
          { value: 0, duration: 100, delay: 0 }
        ],
        easing: 'easeInOutSine'
      });
    },
    
    forgotPassword() {
      // Show the ForgotPassword component
      this.showForgotPassword = true;
    },
    
    showError(message) {
      this.error = message;
      this.toast.error(message, {
        timeout: 5000,
        position: "top-center",
        icon: true,
        closeButton: true,
        pauseOnFocusLoss: true,
        pauseOnHover: true,
        draggable: true,
        draggablePercent: 0.6,
        showCloseButtonOnHover: false,
        hideProgressBar: false,
        closeOnClick: true,
        rtl: false
      });
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 1rem;
  background-color: var(--bg-color);
  overflow: hidden;
}

.login-form {
  width: 100%;
  max-width: 400px;
  padding: 2.5rem;
  background: var(--input-bg);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.15);
  position: relative;
  margin-top: 1rem;
  overflow: hidden;
  opacity: 0; /* Initial state for animation */
}

.form-content {
  margin-top: 1.5rem;
  position: relative;
  z-index: 2;
}

.logo-container {
  text-align: center;
  margin-bottom: 2rem;
  position: relative;
  z-index: 2;
}

.logo-icon {
  font-size: 2.5rem;
  color: var(--primary-color);
  padding: 1.2rem;
  border-radius: 50%;
  background: rgba(var(--primary-color-rgb), 0.1);
  box-shadow: 0 5px 15px rgba(var(--primary-color-rgb), 0.2);
}

.welcome-text {
  color: var(--text-color);
  font-size: 1.85rem;
  text-align: center;
  margin: 0 0 0.8rem 0;
  font-weight: 700;
  position: relative;
  z-index: 2;
}

.subtitle {
  color: var(--text-color);
  opacity: 0.8;
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1rem;
  position: relative;
  z-index: 2;
}

.input-group {
  margin-bottom: 1.5rem;
  position: relative;
  z-index: 2;
}

.input-container {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.input-icon {
  position: absolute;
  left: 1.2rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-color);
  opacity: 0.6;
  z-index: 1;
}

.input-field {
  width: 100%;
  padding: 1.2rem 1.2rem 1.2rem 3.2rem;
  border: 2px solid var(--input-border);
  border-radius: 12px;
  color: var(--text-color);
  font-size: 1rem;
  background: var(--bg-color);
  transition: all 0.3s ease;
}

.input-field:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.15);
}

.input-label {
  position: absolute;
  left: 3.2rem;
  top: 50%;
  transform: translateY(-50%);
  background: var(--bg-color);
  padding: 0 0.5rem;
  color: var(--text-color);
  opacity: 0.6;
  transition: all 0.3s ease;
  pointer-events: none;
}

.input-field:focus + .input-label,
.input-field:not(:placeholder-shown) + .input-label {
  transform: translateY(-2rem) scale(0.85);
  opacity: 1;
  color: var(--primary-color);
  font-weight: 600;
  left: 2.5rem;
}

.login-button {
  width: 100%;
  padding: 1.1rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  position: relative;
  z-index: 2;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(var(--primary-color-rgb), 0.25);
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(var(--primary-color-rgb), 0.3);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(var(--primary-color-rgb), 0.2);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.additional-links {
  margin-top: 2rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
  position: relative;
  z-index: 2;
}

.link-text {
  color: var(--text-color);
  opacity: 0.8;
  text-decoration: none;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  position: relative;
}

.link-text:hover {
  opacity: 1;
  color: var(--primary-color);
}

.link-text:after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 1px;
  background-color: var(--primary-color);
  transition: width 0.3s ease;
}

.link-text:hover:after {
  width: 100%;
}

.separator {
  color: var(--text-color);
  opacity: 0.4;
}

/* Decorative elements */
.decorative-circles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 1;
}

.circle {
  position: absolute;
  border-radius: 50%;
}

.circle-1 {
  background: linear-gradient(135deg, rgba(var(--primary-color-rgb), 0.5), rgba(var(--primary-color-rgb), 0.05));
  width: 200px;
  height: 200px;
  top: -100px;
  right: -80px;
  opacity: 0.7;
}

.circle-2 {
  background: linear-gradient(45deg, rgba(var(--primary-color-rgb), 0.1), rgba(var(--primary-color-rgb), 0.4));
  width: 150px;
  height: 150px;
  bottom: -50px;
  left: -50px;
  opacity: 0.5;
}

.circle-3 {
  background: linear-gradient(225deg, rgba(var(--primary-color-rgb), 0.15), rgba(var(--primary-color-rgb), 0.3));
  width: 80px;
  height: 80px;
  bottom: 40%;
  right: -20px;
  opacity: 0.4;
}

/* Animation class for shake effect */
@keyframes shakeEffect {
  0% { transform: translateX(0); }
  25% { transform: translateX(10px); }
  50% { transform: translateX(-10px); }
  75% { transform: translateX(5px); }
  100% { transform: translateX(0); }
}

/* Media queries for responsive design */
@media (max-width: 480px) {
  .login-form {
    padding: 2rem 1.5rem;
  }
  
  .welcome-text {
    font-size: 1.6rem;
  }
  
  .circle-1 {
    width: 150px;
    height: 150px;
  }
  
  .circle-2 {
    width: 100px;
    height: 100px;
  }
}
</style>