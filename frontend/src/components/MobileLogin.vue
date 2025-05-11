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
      </form>
    </div>
    
    <!-- Success animation -->
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
    
   
  </div>
</template>

<script>
import { ref, computed, inject, onMounted, nextTick, watch } from 'vue';
import AuthService from '../services/AuthService';
import { useToast } from 'vue-toastification';
import anime from 'animejs/lib/anime.es.js';

export default {
  name: 'MobileLogin',
  emits: ['login-success', 'forgot-password'],
  setup(_props, { emit }) {
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
    const usernameHasFocus = ref(false);
    const passwordHasFocus = ref(false);
    const usernameInput = ref(null);
    const passwordInput = ref(null);
    const progressFill = ref(null);
    const particleContainer = ref(null);
    const toast = useToast();
    const analyzeContext = inject('analyzeContext', null);

    const isFormValid = computed(() => {
      return username.value.trim() !== '' && password.value.trim() !== '';
    });

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

    const togglePasswordVisibility = () => {
      showPassword.value = !showPassword.value;
      anime({
        targets: '.toggle-password',
        scale: [1, 0.9, 1],
        duration: 300,
        easing: 'easeInOutQuad'
      });
    };

    const saveUsername = () => {
      if (rememberMe.value) {
        localStorage.setItem('rememberedUsername', username.value);
      } else {
        localStorage.removeItem('rememberedUsername');
      }
    };

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

    const animateError = () => {
      loginError.value = true;
      anime({
        targets: '.login-container',
        translateX: [0, 10, -10, 5, -5, 0],
        duration: 400,
        easing: 'easeInOutQuad',
        complete: () => {
          loginError.value = false;
        }
      });
      anime({
        targets: '.error-icon',
        scale: [1, 1.2, 1],
        opacity: [0.7, 1, 0.7],
        duration: 600,
        easing: 'easeInOutQuad'
      });
    };

    const createParticles = () => {
      if (!particleContainer.value) return;
      const container = particleContainer.value;
      container.innerHTML = '';
      const colors = ['#2dce89', '#11cdef', '#5e72e4'];
      for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        particle.style.width = `${Math.random() * 6 + 4}px`;
        particle.style.height = particle.style.width;
        container.appendChild(particle);
      }
    };

    const playSuccessAnimation = () => {
      createParticles();
      const timeline = anime.timeline({
        easing: 'easeOutExpo'
      });
      timeline
        .add({
          targets: '.checkmark-circle',
          strokeDashoffset: [anime.setDashoffset, 0],
          duration: 800,
          easing: 'easeOutCubic'
        })
        .add({
          targets: '.checkmark-check',
          strokeDashoffset: [anime.setDashoffset, 0],
          duration: 600,
          easing: 'easeOutCubic'
        }, '-=400')
        .add({
          targets: progressFill.value,
          width: '100%',
          duration: 1500,
          easing: 'easeInOutQuad'
        }, '-=300')
        .add({
          targets: '.welcome-message',
          opacity: [0, 1],
          translateY: [20, 0],
          duration: 600,
          easing: 'easeOutBack'
        }, '-=1200')
        .add({
          targets: '.redirect-message',
          opacity: [0, 1],
          translateY: [15, 0],
          duration: 600,
          easing: 'easeOutBack'
        }, '-=400')
        .add({
          targets: '.particle',
          translateX: () => anime.random(-100, 100),
          translateY: () => anime.random(-100, 100),
          scale: [0, 1, 0],
          opacity: [0, 0.8, 0],
          easing: 'easeOutExpo',
          duration: 1500,
          delay: anime.stagger(20)
        }, '-=1500')
        .add({
          targets: '.transition-overlay',
          opacity: [0, 1],
          duration: 600,
          easing: 'easeInQuad',
          complete: redirectToDashboard
        }, '-=400');
    };

    const redirectToDashboard = () => {
      localStorage.setItem('isAuthenticated', 'true');
      if (analyzeContext) {
        analyzeContext({
          screen: 'login',
          action: 'success',
          user: username.value
        });
      }
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 800);
    };

    const handleLogin = async () => {
      if (!isFormValid.value) {
        errorMessage.value = 'Please enter both username and password.';
        toast.error('Please enter both username and password.');
        animateError();
        return;
      }

      isLoading.value = true;
      errorMessage.value = '';

      anime({
        targets: '.login-button',
        scale: [1, 0.98, 1],
        duration: 200,
        easing: 'easeInOutQuad'
      });

      try {
        const result = await AuthService.login(username.value, password.value);
        if (result.success) {
          saveUsername();
          toast.success('Login successful!');
          if (analyzeContext) {
            analyzeContext({
              screen: 'login',
              action: 'login_success',
              user: username.value
            });
          }
          loginSuccess.value = true;
          await nextTick();
          playSuccessAnimation();
          emit('login-success', result.user);
        } else {
          errorMessage.value = result.message || 'Invalid credentials. Please try again.';
          toast.error(errorMessage.value);
          animateError();
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

    const goToForgotPassword = () => {
      emit('forgot-password');
      if (analyzeContext) {
        analyzeContext({
          screen: 'login',
          action: 'navigate',
          destination: 'forgot_password'
        });
      }
    };

    const animateFloatingShapes = () => {
      anime({
        targets: '.floating-shape',
        translateX: () => anime.random(-15, 15),
        translateY: () => anime.random(-15, 15),
        rotate: () => anime.random(-10, 10),
        opacity: () => anime.random(0.1, 0.2),
        scale: () => anime.random(0.9, 1.1),
        duration: () => anime.random(2000, 4000),
        delay: anime.stagger(150),
        easing: 'easeInOutQuad',
        complete: animateFloatingShapes
      });
    };

    onMounted(() => {
      detectPreferredTheme();
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
          isDarkMode.value = e.matches;
          applyTheme();
        }
      });
      const rememberedUsername = localStorage.getItem('rememberedUsername');
      if (rememberedUsername) {
        username.value = rememberedUsername;
        rememberMe.value = true;
      }
      if (!username.value && usernameInput.value) {
        setTimeout(() => {
          usernameInput.value.focus();
        }, 300);
      }
      checkFirstVisit();
      animateFloatingShapes();
      setTimeout(() => {
        if (analyzeContext) {
          analyzeContext({
            screen: 'login',
            action: 'view',
            isFirstTime: !localStorage.getItem('login_help_shown')
          });
        }
      }, 300);
      anime({
        targets: '.login-container',
        translateY: [15, 0],
        opacity: [0, 1],
        duration: 600,
        easing: 'easeOutQuad'
      });
    });

    watch(isFormValid, (newVal) => {
      if (newVal) {
        anime({
          targets: '.login-button',
          scale: [1, 1.03, 1],
          backgroundColor: ['#5e72e4', '#4a62d3', '#5e72e4'],
          duration: 200,
          easing: 'easeOutQuad'
        });
      }
    });

    return {
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
      isFormValid,
      toggleTheme,
      togglePasswordVisibility,
      handleLogin,
      goToForgotPassword,
      closeHelp,
      getGreeting,
      focusPassword,
      usernameInput,
      passwordInput,
      progressFill,
      particleContainer,
      redirectToDashboard
    };
  }
};
</script>

<style scoped>
/* Root variables with improved contrast */
:root {
  --primary-color: #5e72e4;
  --primary-hover: #4a62d3;
  --primary-dark: #3f51b5;
  --secondary-color: #64748b;
  --success-color: #2dce89;
  --info-color: #11cdef;
  --warning-color: #fb6340;
  --danger-color: #dc2626;
  --background-color: #f8fafc;
  --surface-color: #ffffff;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --border-color: #e2e8f0;
  --input-bg: #ffffff;
  --input-focus-bg: #f8fafc;
  --shadow-color: rgba(0, 0, 0, 0.08);
  --shadow-color-intense: rgba(0, 0, 0, 0.12);
  --focus-ring-color: rgba(94, 114, 228, 0.3);
  --error-bg: rgba(239, 68, 68, 0.1);
  --hover-bg: rgba(0, 0, 0, 0.04);
  --divider-color: rgba(0, 0, 0, 0.12);
  --particle-color: rgba(94, 114, 228, 0.6);
  --shape-color: rgba(94, 114, 228, 0.08);
  --tooltip-bg: #ffffff;
  --tooltip-shadow: rgba(0, 0, 0, 0.12);
}

/* Dark theme with improved contrast */
[data-theme="dark"] {
  --primary-color: #818cf8;
  --primary-hover: #6366f1;
  --primary-dark: #4f46e5;
  --secondary-color: #94a3b8;
  --success-color: #4ade80;
  --info-color: #22d3ee;
  --warning-color: #f97316;
  --danger-color: #ef4444;
  --background-color: #0f172a;
  --surface-color: #1e293b;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --border-color: #334155;
  --input-bg: #1e293b;
  --input-focus-bg: #293548;
  --shadow-color: rgba(0, 0, 0, 0.25);
  --shadow-color-intense: rgba(0, 0, 0, 0.3);
  --focus-ring-color: rgba(129, 140, 248, 0.4);
  --error-bg: rgba(239, 68, 68, 0.15);
  --hover-bg: rgba(255, 255, 255, 0.06);
  --divider-color: rgba(255, 255, 255, 0.12);
  --particle-color: rgba(129, 140, 248, 0.6);
  --shape-color: rgba(129, 140, 248, 0.08);
  --tooltip-bg: #1e293b;
  --tooltip-shadow: rgba(0, 0, 0, 0.25);
}

/* Base container with safe area insets */
.mobile-login {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: env(safe-area-inset-top, 1rem) env(safe-area-inset-right, 1rem) env(safe-area-inset-bottom, 1rem) env(safe-area-inset-left, 1rem);
  background-color: var(--background-color);
  width: 100%;
  position: relative;
  overflow-x: hidden;
  transition: background-color 0.4s ease, color 0.4s ease;
}

/* Optimized animated background */
.animated-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  will-change: transform;
  pointer-events: none;
}

.floating-shape {
  position: absolute;
  width: 10rem;
  height: 10rem;
  border-radius: 40%;
  background-color: var(--shape-color);
  opacity: 0.15;
  will-change: transform, opacity;
}

.floating-shape:nth-child(1) { top: 10%; left: 15%; width: 12rem; height: 12rem; }
.floating-shape:nth-child(2) { top: 55%; right: 10%; width: 9rem; height: 9rem; }
.floating-shape:nth-child(3) { bottom: 15%; left: 25%; width: 7rem; height: 7rem; }
.floating-shape:nth-child(4) { top: 35%; left: 65%; width: 11rem; height: 11rem; }
.floating-shape:nth-child(5) { bottom: 25%; right: 35%; width: 6rem; height: 6rem; }

/* Theme toggle with improved accessibility */
.theme-toggle {
  position: fixed;
  top: calc(1rem + env(safe-area-inset-top));
  right: calc(1rem + env(safe-area-inset-right));
  background-color: var(--surface-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  cursor: pointer;
  z-index: 20;
  box-shadow: 0 2px 8px var(--shadow-color);
  transition: all 0.2s ease;
}

.theme-toggle:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px var(--shadow-color-intense);
}

.theme-toggle:focus-visible {
  outline: 2px solid var(--focus-ring-color);
  outline-offset: 2px;
}

/* Login container with consistent spacing */
.login-container {
  width: 100%;
  max-width: 360px;
  background-color: var(--surface-color);
  border-radius: 1rem;
  box-shadow: 0 4px 16px var(--shadow-color);
  padding: 1.5rem;
  margin: 2rem 0;
  z-index: 1;
  position: relative;
  transition: all 0.3s ease;
}

.login-container.shake {
  animation: shake 0.4s cubic-bezier(0.36, 0.07, 0.19, 0.97);
}

@keyframes shake {
  10%, 90% { transform: translateX(-1px); }
  20%, 80% { transform: translateX(2px); }
  30%, 50%, 70% { transform: translateX(-3px); }
  40%, 60% { transform: translateX(3px); }
}

/* Login header with consistent typography */
.login-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.login-title {
  color: var(--primary-color);
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.greeting {
  font-size: 0.9rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.title-text {
  background: linear-gradient(to right, var(--primary-color), var(--info-color));
  -webkit-background-clip: text;
  color: var(--primary-color);
}

.login-subtitle {
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 400;
}

/* Form with consistent spacing */
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
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-primary);
}

.input-container {
  position: relative;
  background-color: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  padding: 0.75rem;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
}

.input-container.focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--focus-ring-color);
}

.input-container.filled {
  background-color: var(--input-focus-bg);
}

.input-icon {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-right: 0.5rem;
}

.input-container.focus .input-icon {
  color: var(--primary-color);
}

input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.95rem;
  outline: none;
}

input::placeholder {
  color: var(--text-secondary);
  opacity: 0.6;
}

.validation-icon {
  color: var(--success-color);
  font-size: 0.9rem;
  margin-left: 0.5rem;
}

.toggle-password {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  transition: color 0.2s ease;
}

.toggle-password:hover {
  color: var(--primary-color);
}

.toggle-password:focus-visible {
  outline: 2px solid var(--focus-ring-color);
  border-radius: 0.25rem;
}

/* Form options with better alignment */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0.5rem 0;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.remember-me input[type="checkbox"] {
  appearance: none;
  width: 1rem;
  height: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 0.25rem;
  background-color: var(--input-bg);
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
}

.remember-me input[type="checkbox"]:checked {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.remember-me input[type="checkbox"]:checked::after {
  content: '✓';
  color: white;
  font-size: 0.7rem;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.remember-me input[type="checkbox"]:focus-visible {
  box-shadow: 0 0 0 2px var(--focus-ring-color);
}

.remember-me label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  cursor: pointer;
}

.forgot-password-link {
  background: transparent;
  border: none;
  color: var(--primary-color);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s ease;
}

.forgot-password-link:hover {
  color: var(--primary-hover);
  text-decoration: underline;
}

.forgot-password-link:focus-visible {
  outline: 2px solid var(--focus-ring-color);
  border-radius: 0.25rem;
}

/* Error message with better contrast */
.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: var(--error-bg);
  color: var(--danger-color);
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.85rem;
}

.error-icon {
  font-size: 1rem;
}

.error-icon.pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

/* Login button with improved feedback */
.login-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.875rem;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  margin: 0.75rem 0;
}

.login-button:hover:not(:disabled) {
  background-color: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(94, 114, 228, 0.2);
}

.login-button:focus-visible {
  outline: 2px solid var(--focus-ring-color);
  outline-offset: 2px;
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-button.button-ready {
  animation: button-pulse 1.5s ease-in-out infinite;
}

@keyframes button-pulse {
  0% { box-shadow: 0 0 0 0 rgba(94, 114, 228, 0.3); }
  70% { box-shadow: 0 0 0 8px rgba(94, 114, 228, 0); }
  100% { box-shadow: 0 0 0 0 rgba(94, 114, 228, 0); }
}

.spinner-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spinner {
  font-size: 1rem;
}

.loading-text {
  font-size: 0.9rem;
}

/* Success animation with optimized performance */
.animation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.success-container {
  background-color: var(--surface-color);
  border-radius: 1rem;
  padding: 2rem;
  width: 90%;
  max-width: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.checkmark {
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;
}

.checkmark-circle {
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  stroke-width: 2;
  stroke: var(--success-color);
  fill: none;
}

.checkmark-check {
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  stroke-width: 3;
  stroke: var(--success-color);
}

.progress-bar {
  width: 100%;
  height: 3px;
  background-color: var(--border-color);
  border-radius: 1.5px;
  margin-bottom: 1rem;
}

.progress-fill {
  height: 100%;
  width: 0;
  background-color: var(--success-color);
}

.welcome-message {
  color: var(--primary-color);
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.redirect-message {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.particle-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.particle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
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

/* Help tooltip with better positioning */
.help-tooltip {
  position: fixed;
  bottom: calc(1rem + env(safe-area-inset-bottom));
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 2rem);
  max-width: 300px;
  background-color: var(--tooltip-bg);
  border-radius: 0.75rem;
  padding: 1rem;
  box-shadow: 0 4px 16px var(--tooltip-shadow);
  z-index: 10;
}

.close-tooltip {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  font-size: 0.9rem;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-tooltip:hover {
  color: var(--text-primary);
  background-color: var(--hover-bg);
}

.close-tooltip:focus-visible {
  outline: 2px solid var(--focus-ring-color);
}

.help-tooltip h3 {
  color: var(--primary-color);
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.help-tooltip p {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}

.tooltip-tips {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tooltip-tip {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.tooltip-tip svg {
  color: var(--info-color);
  font-size: 0.9rem;
  margin-top: 0.1rem;
}

/* Transitions with reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .fade-enter-active, .fade-leave-active,
  .slide-fade-enter-active, .slide-fade-leave-active,
  .theme-icon-enter-active, .theme-icon-leave-active {
    transition: none;
  }
  
  .login-button.button-ready,
  .error-icon.pulse,
  .floating-shape,
  .theme-toggle,
  .toggle-password,
  .login-container.shake {
    animation: none;
  }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-fade-enter-active {
  transition: all 0.2s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.15s ease-in;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-8px);
  opacity: 0;
}

.theme-icon-enter-active,
.theme-icon-leave-active {
  transition: all 0.15s ease;
}

.theme-icon-enter-from,
.theme-icon-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* Responsive adjustments */
@media (max-width: 360px) {
  .login-container {
    padding: 1.25rem;
  }
  
  .login-title {
    font-size: 1.3rem;
  }
  
  .form-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .forgot-password-link {
    margin-left: 1.5rem;
  }
  
  .success-container {
    padding: 1.5rem;
  }
}

@media (min-height: 800px) {
  .login-container {
    margin: 3rem 0;
  }
}

@media (hover: hover) {
  .input-container:hover:not(.focus) {
    border-color: var(--secondary-color);
  }
}
</style>