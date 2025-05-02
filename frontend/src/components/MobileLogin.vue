<template>
  <div class="mobile-login" :class="{ 'dark-mode': isDarkMode }">
    <!-- Animated background elements -->
    <div class="animated-background">
      <div v-for="i in 5" :key="`shape-${i}`" class="floating-shape"></div>
    </div>
    
    <!-- Theme toggle button with animation -->
    <button 
      @click="toggleTheme" 
      class="theme-toggle"
      :aria-label="isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'"
      role="switch"
      :aria-checked="isDarkMode"
    >
      <transition name="theme-icon" mode="out-in">
        <font-awesome-icon v-if="isDarkMode" key="sun" icon="sun" />
        <font-awesome-icon v-else key="moon" icon="moon" />
      </transition>
    </button>
    
    <div class="login-container" :class="{ 'shake': loginError }">
      <div class="login-header">
        <h1 class="login-title">
          <span class="greeting">{{ getGreeting() }}</span>
          <span class="title-text">Login</span>
        </h1>
        <p class="login-subtitle">Sign in to access your dashboard</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Username</label>
          <div class="input-container" :class="{ 'focus': usernameHasFocus, 'filled': username }">
            <font-awesome-icon icon="user" class="input-icon" />
            <input 
              type="text" 
              id="username" 
              v-model="username" 
              placeholder="Enter your username"
              required
              autocomplete="username"
              :disabled="isLoading"
              @focus="usernameHasFocus = true"
              @blur="usernameHasFocus = false"
              @keyup.enter="focusPassword"
              ref="usernameInput"
            >
            <transition name="fade">
              <font-awesome-icon v-if="username" icon="check" class="validation-icon" />
            </transition>
          </div>
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <div class="input-container" :class="{ 'focus': passwordHasFocus, 'filled': password }">
            <font-awesome-icon icon="lock" class="input-icon" />
            <input 
              :type="showPassword ? 'text' : 'password'"
              id="password" 
              v-model="password" 
              placeholder="Enter your password"
              required
              autocomplete="current-password"
              :disabled="isLoading"
              @focus="passwordHasFocus = true"
              @blur="passwordHasFocus = false"
              ref="passwordInput"
            >
            <button 
              type="button" 
              class="toggle-password"
              @click="togglePasswordVisibility"
              :disabled="isLoading"
              aria-label="Toggle password visibility"
            >
              <transition name="fade" mode="out-in">
                <font-awesome-icon :key="showPassword ? 'hide' : 'show'" :icon="showPassword ? 'eye-slash' : 'eye'" />
              </transition>
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
        
        <transition name="slide-fade">
          <div v-if="errorMessage" class="error-message">
            <font-awesome-icon icon="exclamation-circle" class="error-icon pulse" />
            <span>{{ errorMessage }}</span>
          </div>
        </transition>
        
        <button 
          type="submit" 
          class="login-button"
          :disabled="isLoading || !isFormValid"
          :class="{ 'button-ready': isFormValid && !isLoading }"
        >
          <transition name="fade" mode="out-in">
            <span v-if="!isLoading" key="sign-in">Sign In</span>
            <div v-else key="loading" class="spinner-container">
              <font-awesome-icon icon="spinner" spin class="spinner" />
              <span class="loading-text">Verifying...</span>
            </div>
          </transition>
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
    
    <!-- Enhanced success animation with particles and smooth transition -->
    <div v-if="loginSuccess" class="animation-overlay">
      <div class="success-container">
        <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
          <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
          <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
        </svg>
        
        <div class="progress-bar">
          <div class="progress-fill" ref="progressFill"></div>
        </div>
        
        <div class="success-content">
          <h2 class="welcome-message">Welcome Back{{ username ? ', ' + username : '' }}!</h2>
          <p class="redirect-message">Redirecting to dashboard...</p>
        </div>
        
        <div class="particle-container" ref="particleContainer"></div>
        <div class="transition-overlay"></div>
      </div>
    </div>
    
    <!-- Quick help tooltip that appears on first visit -->
    <transition name="fade">
      <div v-if="showHelp" class="help-tooltip">
        <button @click="closeHelp" class="close-tooltip">
          <font-awesome-icon icon="times" />
        </button>
        <h3>Welcome!</h3>
        <p>Enter your credentials to sign in or create a new account.</p>
        <div class="tooltip-tips">
          <div class="tooltip-tip">
            <font-awesome-icon icon="lightbulb" />
            <span>Use the theme toggle to switch between light and dark mode.</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { ref, computed, inject, onMounted, nextTick, watch } from 'vue';
import { useRouter } from 'vue-router';
import AuthService from '../services/AuthService';
import { useToast } from 'vue-toastification';
import anime from 'animejs/lib/anime.es.js';

export default {
  name: 'MobileLogin',
  emits: ['login-success', 'forgot-password', 'create-account'],
  setup(props, { emit }) {
    // Router for navigation
    const router = useRouter();
    
    // State management
    const username = ref('');
    const password = ref('');
    const rememberMe = ref(false);
    const showPassword = ref(false);
    const isLoading = ref(false);
    const errorMessage = ref('');
    const isDarkMode = ref(false);
    const loginSuccess = ref(false);
    const loginError = ref(false);
    const showHelp = ref(false);
    
    // Focus state tracking
    const usernameHasFocus = ref(false);
    const passwordHasFocus = ref(false);
    
    // References for DOM elements
    const usernameInput = ref(null);
    const passwordInput = ref(null);
    const progressFill = ref(null);
    const particleContainer = ref(null);
    
    // Services
    const toast = useToast();
    const analyzeContext = inject('analyzeContext', null);
    
    // Computed properties
    const isFormValid = computed(() => {
      return username.value.trim() !== '' && password.value.trim() !== '';
    });
    
    // Helper methods
    const getGreeting = () => {
      const hour = new Date().getHours();
      if (hour < 12) return 'Good Morning';
      if (hour < 18) return 'Good Afternoon';
      return 'Good Evening';
    };
    
    const focusPassword = () => {
      if (passwordInput.value) {
        passwordInput.value.focus();
      }
    };
    
    // Theme detection and management
    const detectPreferredTheme = () => {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme) {
        isDarkMode.value = savedTheme === 'dark';
      } else {
        isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
      }
      applyTheme();
    };

    const toggleTheme = () => {
      isDarkMode.value = !isDarkMode.value;
      localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light');
      applyTheme();
      
      // Animate theme change
      anime({
        targets: '.theme-toggle',
        rotate: [0, 360],
        duration: 600,
        easing: 'easeOutQuad'
      });
    };

    const applyTheme = () => {
      document.documentElement.setAttribute('data-theme', isDarkMode.value ? 'dark' : 'light');
    };

    // Password visibility toggle
    const togglePasswordVisibility = () => {
      showPassword.value = !showPassword.value;
      
      // Animate button press
      anime({
        targets: '.toggle-password',
        scale: [1, 0.9, 1],
        duration: 300,
        easing: 'easeInOutQuad'
      });
    };

    // Save username if "Remember me" is checked
    const saveUsername = () => {
      if (rememberMe.value) {
        localStorage.setItem('rememberedUsername', username.value);
      } else {
        localStorage.removeItem('rememberedUsername');
      }
    };
    
    // Handle help tooltip
    const checkFirstVisit = () => {
      const isFirstVisit = !localStorage.getItem('login_help_shown');
      showHelp.value = isFirstVisit;
      if (isFirstVisit) {
        setTimeout(() => {
          anime({
            targets: '.help-tooltip',
            translateY: [20, 0],
            opacity: [0, 1],
            duration: 800,
            easing: 'easeOutElastic(1, 0.5)'
          });
        }, 500);
      }
    };
    
    const closeHelp = () => {
      anime({
        targets: '.help-tooltip',
        translateY: [0, 20],
        opacity: [1, 0],
        duration: 300,
        easing: 'easeOutQuad',
        complete: () => {
          showHelp.value = false;
          localStorage.setItem('login_help_shown', 'true');
        }
      });
    };
    
    // Animation for error state
    const animateError = () => {
      loginError.value = true;
      
      // Shake animation for login container
      anime({
        targets: '.login-container',
        translateX: [0, 15, -15, 10, -10, 5, -5, 0],
        duration: 600,
        easing: 'easeInOutQuad',
        complete: () => {
          loginError.value = false;
        }
      });
      
      // Pulse animation for error icon
      anime({
        targets: '.error-icon',
        scale: [1, 1.2, 1],
        opacity: [0.7, 1, 0.7],
        duration: 600,
        loop: 2,
        easing: 'easeInOutQuad'
      });
    };
    
    // Create and animate particles for success animation
    const createParticles = () => {
      if (!particleContainer.value) return;
      
      const container = particleContainer.value;
      container.innerHTML = '';
      
      const colors = ['#2dce89', '#11cdef', '#5e72e4', '#ffffff'];
      const shapes = ['circle', 'square', 'triangle', 'star'];
      
      for (let i = 0; i < 40; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const shape = shapes[Math.floor(Math.random() * shapes.length)];
        particle.classList.add(shape);
        
        particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        particle.style.width = `${Math.random() * 10 + 5}px`;
        particle.style.height = particle.style.width;
        
        container.appendChild(particle);
      }
    };
    
    // Success animation sequence
    const playSuccessAnimation = () => {
      createParticles();
      
      // Animation timeline for success state
      const timeline = anime.timeline({
        easing: 'easeOutExpo'
      });
      
      // Animate checkmark
      timeline.add({
        targets: '.checkmark-circle',
        strokeDashoffset: [anime.setDashoffset, 0],
        duration: 1000,
        easing: 'easeOutCubic'
      })
      .add({
        targets: '.checkmark-check',
        strokeDashoffset: [anime.setDashoffset, 0],
        duration: 800,
        easing: 'easeOutCubic'
      }, '-=600')
      
      // Progress bar animation
      .add({
        targets: progressFill.value,
        width: '100%',
        duration: 2000,
        easing: 'easeInOutQuad'
      }, '-=400')
      
      // Welcome message animation
      .add({
        targets: '.welcome-message',
        opacity: [0, 1],
        translateY: [30, 0],
        duration: 800,
        easing: 'easeOutBack'
      }, '-=1800')
      
      // Redirect message animation
      .add({
        targets: '.redirect-message',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800,
        easing: 'easeOutBack'
      }, '-=600')
      
      // Particle explosion animation
      .add({
        targets: '.particle',
        translateX: () => anime.random(-150, 150),
        translateY: () => anime.random(-150, 150),
        scale: [0, 1, 0],
        opacity: [0, 1, 0],
        easing: 'easeOutExpo',
        duration: 2000,
        delay: anime.stagger(30)
      }, '-=2000')
      
      // Final fade to dashboard
      .add({
        targets: '.transition-overlay',
        opacity: [0, 1],
        duration: 800,
        easing: 'easeInQuad',
        complete: () => {
          // Navigate to dashboard
          redirectToDashboard();
        }
      }, '-=500');
    };
    
    // Redirect to dashboard
    const redirectToDashboard = () => {
      // Store authentication state in localStorage or sessionStorage
      localStorage.setItem('isAuthenticated', 'true');
      
      // Log analytics event
      if (analyzeContext) {
        analyzeContext({
          screen: 'login',
          action: 'success',
          user: username.value
        });
      }
      
      // Redirect to dashboard
      setTimeout(() => {
        if (router) {
          router.push('/dashboard');
        } else {
          window.location.href = '/dashboard';
        }
      }, 1000);
    };

    // Main login handler
    const handleLogin = async () => {
      if (!isFormValid.value) {
        errorMessage.value = 'Please enter both username and password.';
        toast.error('Please enter both username and password.');
        animateError();
        return;
      }

      isLoading.value = true;
      errorMessage.value = '';

      // Animate the login button
      anime({
        targets: '.login-button',
        scale: [1, 0.98, 1],
        duration: 300,
        easing: 'easeInOutQuad'
      });

      try {
        // Call the authentication service
        const result = await AuthService.login(username.value, password.value);

        // Check login result
        if (result.success) {
          // Save username if "Remember me" is checked
          saveUsername();
          
          // Show success toast
          toast.success('Login successful!');

          
          // Track analytics
          if (analyzeContext) {
            analyzeContext({
              screen: 'login',
              action: 'login_success',
              user: username.value
            });
          }
          
          // Show success animation
          loginSuccess.value = true;
          await nextTick();
          playSuccessAnimation();
          
          // Emit the login success event
          emit('login-success', result.user);
          window.location.href = '/dashboard';
        } else {
          // Handle error case
          errorMessage.value = result.message || 'Invalid credentials. Please try again.';
          toast.error(errorMessage.value);
          animateError();
          
          // Track analytics
          if (analyzeContext) {
            analyzeContext({
              screen: 'login',
              action: 'login_error',
              error: { message: result.message }
            });
          }
        }
      } catch (error) {
        console.error('Unexpected login error:', error);
        const errorMsg = 'An unexpected error occurred. Please try again.';
        errorMessage.value = errorMsg;
        toast.error(errorMsg);
        animateError();
        
        // Track analytics
        if (analyzeContext) {
          analyzeContext({
            screen: 'login',
            action: 'error',
            error: {
              message: errorMsg,
              details: error.message || 'Unknown error'
            }
          });
        }
      } finally {
        isLoading.value = false;
        window.location.href = '/dashboard';
      }
    };

    // Navigation handlers
    const goToForgotPassword = () => {
      emit('forgot-password');
      
      // Track analytics
      if (analyzeContext) {
        analyzeContext({
          screen: 'login',
          action: 'navigate',
          destination: 'forgot_password'
        });
      }
    };

    const goToRegister = () => {
      emit('create-account');
      
      // Track analytics
      if (analyzeContext) {
        analyzeContext({
          screen: 'login',
          action: 'navigate',
          destination: 'register'
        });
      }
    };
    
    // Animate floating shapes
    const animateFloatingShapes = () => {
      anime({
        targets: '.floating-shape',
        translateX: () => anime.random(-20, 20),
        translateY: () => anime.random(-20, 20),
        rotate: () => anime.random(-15, 15),
        opacity: () => anime.random(0.1, 0.3),
        scale: () => anime.random(0.8, 1.2),
        duration: () => anime.random(3000, 5000),
        delay: anime.stagger(200),
        easing: 'easeInOutQuad',
        complete: animateFloatingShapes,
        loop: true
      });
    };
    
    // Initial setup
    onMounted(() => {
      detectPreferredTheme();
      
      // Listen for system theme changes
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
          isDarkMode.value = e.matches;
          applyTheme();
        }
      });
      
      // Restore remembered username
      const rememberedUsername = localStorage.getItem('rememberedUsername');
      if (rememberedUsername) {
        username.value = rememberedUsername;
        rememberMe.value = true;
      }
      
      // Auto-focus username field if empty
      if (!username.value && usernameInput.value) {
        setTimeout(() => {
          usernameInput.value.focus();
        }, 500);
      }
      
      // Check if it's the first visit to show help tooltip
      checkFirstVisit();
      
      // Start background animations
      animateFloatingShapes();
      
      // Track page view
      setTimeout(() => {
        if (analyzeContext) {
          analyzeContext({
            screen: 'login',
            action: 'view',
            isFirstTime: !localStorage.getItem('login_help_shown')
          });
        }
      }, 500);
      
      // Entrance animation for login container
      anime({
        targets: '.login-container',
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 800,
        easing: 'easeOutQuad'
      });
    });
    
    // Watch for form validation changes to animate button
    watch(isFormValid, (newVal) => {
      if (newVal) {
        anime({
          targets: '.login-button',
          scale: [1, 1.05, 1],
          backgroundColor: ['#5e72e4', '#324cdd', '#5e72e4'],
          duration: 300,
          easing: 'easeOutQuad'
        });
      }
    });

    return {
      // State
      username,
      password,
      rememberMe,
      showPassword,
      isLoading,
      errorMessage,
      isDarkMode,
      loginSuccess,
      loginError,
      showHelp,
      usernameHasFocus,
      passwordHasFocus,
      
      // Computed
      isFormValid,
      
      // Methods
      toggleTheme,
      togglePasswordVisibility,
      handleLogin,
      goToForgotPassword,
      goToRegister,
      closeHelp,
      getGreeting,
      focusPassword,
      
      // Refs
      usernameInput,
      passwordInput,
      progressFill,
      particleContainer
    };
  }
};
</script>

<style scoped>
/* Root variables for theming */
:root {
  --primary-color: #5e72e4;
  --primary-hover: #4a62d3;
  --primary-dark: #324cdd;
  --secondary-color: #8392ab;
  --success-color: #2dce89;
  --info-color: #11cdef;
  --warning-color: #fb6340;
  --danger-color: #f5365c;
  --background-color: #f9fafc;
  --surface-color: #ffffff;
  --text-primary: #32325d;
  --text-secondary: #8898aa;
  --border-color: #e9ecef;
  --input-bg: #ffffff;
  --input-focus-bg: #ffffff;
  --shadow-color: rgba(0, 0, 0, 0.05);
  --shadow-color-intense: rgba(50, 50, 93, 0.1);
  --focus-ring-color: rgba(94, 114, 228, 0.25);
  --error-bg: rgba(245, 54, 92, 0.1);
  --hover-bg: rgba(0, 0, 0, 0.03);
  --divider-color: rgba(0, 0, 0, 0.1);
  --particle-color: rgba(94, 114, 228, 0.7);
  --shape-color: rgba(94, 114, 228, 0.1);
  --tooltip-bg: #ffffff;
  --tooltip-shadow: rgba(0, 0, 0, 0.1);
}

/* Dark theme variables */
[data-theme="dark"] {
  --primary-color: #7986e7;
  --primary-hover: #6575e0;
  --primary-dark: #5e72e4;
  --secondary-color: #a0b0c8;
  --success-color: #4dd4a0;
  --info-color: #45d8f3;
  --warning-color: #fc8b6a;
  --danger-color: #f76d8c;
  --background-color: #131929;
  --surface-color: #1f2b3d;
  --text-primary: #e2e4f3;
  --text-secondary: #b3b9cc;
  --border-color: #2e3344;
  --input-bg: #2a2a3c;
  --input-focus-bg: #323450;
  --shadow-color: rgba(0, 0, 0, 0.2);
  --shadow-color-intense: rgba(0, 0, 0, 0.25);
  --focus-ring-color: rgba(126, 143, 241, 0.4);
  --error-bg: rgba(245, 54, 92, 0.2);
  --hover-bg: rgba(255, 255, 255, 0.05);
  --divider-color: rgba(255, 255, 255, 0.15);
  --particle-color: rgba(126, 143, 241, 0.7);
  --shape-color: rgba(126, 143, 241, 0.1);
  --tooltip-bg: #2a2a3c;
  --tooltip-shadow: rgba(0, 0, 0, 0.3);
}

/* Base container styles */
.mobile-login {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 1rem;
  background-color: var(--background-color);
  width: 100%;
  position: relative;
  overflow: hidden;
  transition: background-color 0.5s ease;
}

/* Animated background elements */
.animated-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
}

.floating-shape {
  position: absolute;
  width: 12rem;
  height: 12rem;
  border-radius: 50%;
  background-color: var(--shape-color);
  opacity: 0.2;
}

.floating-shape:nth-child(1) {
  top: 5%;
  left: 10%;
  width: 15rem;
  height: 15rem;
  border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
}

.floating-shape:nth-child(2) {
  top: 60%;
  right: 5%;
  width: 10rem;
  height: 10rem;
  border-radius: 50% 50% 50% 50% / 60% 40% 60% 40%;
}

.floating-shape:nth-child(3) {
  bottom: 10%;
  left: 20%;
  width: 8rem;
  height: 8rem;
  border-radius: 40% 60% 60% 40% / 40% 60% 40% 60%;
}

.floating-shape:nth-child(4) {
  top: 30%;
  left: 60%;
  width: 12rem;
  height: 12rem;
  border-radius: 60% 40% 30% 70% / 50% 50% 50% 50%;
}

.floating-shape:nth-child(5) {
  bottom: 30%;
  right: 30%;
  width: 6rem;
  height: 6rem;
  border-radius: 50% 50% 30% 70% / 50% 60% 40% 50%;
}

/* Theme toggle button */
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
  box-shadow: 0 4px 12px var(--shadow-color);
  transition: all 0.3s ease;
}

.theme-toggle:hover {
  transform: translateY(-2px);
  box-shadow: 0 7px 14px var(--shadow-color-intense);
}

.theme-toggle:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  outline-offset: 2px;
}

.theme-toggle:active {
  transform: translateY(1px);
  box-shadow: 0 2px 8px var(--shadow-color);
}

/* Login container */
.login-container {
  width: 100%;
  max-width: 400px;
  background-color: var(--surface-color);
  border-radius: 1.5rem;
  box-shadow: 0 8px 32px var(--shadow-color-intense);
  padding: 2rem;
  margin: 2rem 0;
  z-index: 1;
  position: relative;
  transition: all 0.3s ease, transform 0.4s cubic-bezier(0.36, 0.07, 0.19, 0.97);
}

.login-container.shake {
  animation: shake 0.6s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
  transform: translate3d(0, 0, 0);
  backface-visibility: hidden;
  perspective: 1000px;
}
/* The CSS continues from where it was cut off - completing the shake animation */
@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}

/* Login header */
.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-title {
  color: var(--primary-color);
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.greeting {
  font-size: 1rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.title-text {
  background: linear-gradient(to right, var(--primary-color), var(--info-color));
  -webkit-background-clip: text;
  color: var(--primary-color);
}

.login-subtitle {
  color: var(--text-secondary);
  font-size: 0.95rem;
  font-weight: 400;
  margin-top: 0.5rem;
}

/* Form styles */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  padding-left: 0.25rem;
}

.input-container {
  position: relative;
  background-color: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.input-container.focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 4px var(--focus-ring-color);
}

.input-container.filled {
  background-color: var(--input-focus-bg);
}

.input-icon {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-right: 0.75rem;
  transition: color 0.3s ease;
}

.input-container.focus .input-icon {
  color: var(--primary-color);
}

input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 1rem;
  padding: 0;
  outline: none;
}

input::placeholder {
  color: var(--text-secondary);
  opacity: 0.7;
}

.validation-icon {
  color: var(--success-color);
  font-size: 1rem;
  margin-left: 0.5rem;
}

.toggle-password {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s ease;
}

.toggle-password:hover {
  color: var(--primary-color);
}

.toggle-password:focus-visible {
  outline: 2px solid var(--focus-ring-color);
  border-radius: 0.25rem;
}

/* Form options */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.remember-me input[type="checkbox"] {
  appearance: none;
  width: 1.125rem;
  height: 1.125rem;
  border: 1px solid var(--border-color);
  border-radius: 0.25rem;
  background-color: var(--input-bg);
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
}

.remember-me input[type="checkbox"]:checked {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.remember-me input[type="checkbox"]:checked::after {
  content: '✓';
  color: white;
  font-size: 0.75rem;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.remember-me input[type="checkbox"]:focus-visible {
  box-shadow: 0 0 0 3px var(--focus-ring-color);
}

.remember-me label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  cursor: pointer;
}

.forgot-password-link {
  background: transparent;
  border: none;
  color: var(--primary-color);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.3s ease;
  padding: 0;
}

.forgot-password-link:hover {
  color: var(--primary-hover);
  text-decoration: underline;
}

/* Error message */
.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: var(--error-bg);
  color: var(--danger-color);
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}

.error-icon {
  font-size: 1.125rem;
}

.error-icon.pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 0.7; }
  50% { opacity: 1; }
  100% { opacity: 0.7; }
}

/* Login button */
.login-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 0.75rem;
  padding: 1rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  margin: 1rem 0;
  position: relative;
  overflow: hidden;
}

.login-button:hover:not(:disabled) {
  background-color: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(94, 114, 228, 0.3);
}

.login-button:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 0 2px 6px rgba(94, 114, 228, 0.2);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.login-button.button-ready {
  animation: button-pulse 2s infinite;
}

@keyframes button-pulse {
  0% { box-shadow: 0 0 0 0 rgba(94, 114, 228, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(94, 114, 228, 0); }
  100% { box-shadow: 0 0 0 0 rgba(94, 114, 228, 0); }
}

.spinner-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.spinner {
  font-size: 1.125rem;
}

.loading-text {
  font-size: 1rem;
}

/* Register option */
.register-option {
  text-align: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.register-link {
  background: none;
  border: none;
  color: var(--primary-color);
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  margin-left: 0.5rem;
  transition: color 0.3s ease;
}

.register-link:hover {
  color: var(--primary-hover);
  text-decoration: underline;
}

/* Success animation overlay */
.animation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.success-container {
  background-color: var(--surface-color);
  border-radius: 1.5rem;
  padding: 2.5rem;
  width: 90%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 12px 50px rgba(0, 0, 0, 0.2);
}

.checkmark {
  width: 80px;
  height: 80px;
  margin-bottom: 1.5rem;
}

.checkmark-circle {
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  stroke-width: 2;
  stroke-miterlimit: 10;
  stroke: var(--success-color);
  fill: none;
}

.checkmark-check {
  transform-origin: 50% 50%;
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  stroke-width: 3;
  stroke: var(--success-color);
}

.progress-bar {
  width: 100%;
  height: 4px;
  background-color: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.progress-fill {
  height: 100%;
  width: 0%;
  background-color: var(--success-color);
  transition: width 2s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.welcome-message {
  color: var(--primary-color);
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  opacity: 0;
}

.redirect-message {
  color: var(--text-secondary);
  font-size: 1rem;
  opacity: 0;
}

.particle-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.particle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
}

.particle.square {
  border-radius: 2px;
}

.particle.triangle {
  width: 0;
  height: 0;
  background-color: transparent !important;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 12px solid var(--primary-color);
}

.particle.star {
  clip-path: polygon(
    50% 0%, 61% 35%, 98% 35%, 68% 57%,
    79% 91%, 50% 70%, 21% 91%, 32% 57%,
    2% 35%, 39% 35%
  );
}

.transition-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: var(--surface-color);
  opacity: 0;
  z-index: 10;
}

/* Help tooltip */
.help-tooltip {
  position: absolute;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 2rem);
  max-width: 320px;
  background-color: var(--tooltip-bg);
  border-radius: 1rem;
  padding: 1.25rem;
  box-shadow: 0 8px 32px var(--tooltip-shadow);
  z-index: 10;
  opacity: 0;
}

.close-tooltip {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  font-size: 1rem;
  border-radius: 50%;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-tooltip:hover {
  color: var(--text-primary);
  background-color: var(--hover-bg);
}

.help-tooltip h3 {
  color: var(--primary-color);
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
}

.help-tooltip p {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.tooltip-tips {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tooltip-tip {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.tooltip-tip svg {
  color: var(--info-color);
  font-size: 1rem;
  margin-top: 0.125rem;
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

.theme-icon-enter-active,
.theme-icon-leave-active {
  transition: all 0.2s ease;
}

.theme-icon-enter-from,
.theme-icon-leave-to {
  opacity: 0;
  transform: scale(0.7);
}

/* Responsive adjustments */
@media (max-width: 480px) {
  .login-container {
    padding: 1.5rem;
  }
  
  .login-title {
    font-size: 1.5rem;
  }
  
  .form-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .forgot-password-link {
    margin-left: 1.625rem;
  }
  
  .success-container {
    padding: 2rem 1.5rem;
  }
}

@media (min-height: 700px) {
  .login-container {
    margin: 3rem 0;
  }
}

/* Handle devices with hover capability differently */
@media (hover: hover) {
  .input-container:hover:not(.focus) {
    border-color: var(--secondary-color);
  }
}
</style>