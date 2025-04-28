```vue
<template>
  <div class="mobile-create-account-container">
    <!-- Theme toggle button -->
    <button 
      class="theme-toggle-button" 
      @click="toggleTheme" 
      :aria-label="isDarkTheme ? 'Switch to light theme' : 'Switch to dark theme'"
      role="switch"
      :aria-checked="isDarkTheme"
    >
      <font-awesome-icon :icon="isDarkTheme ? 'sun' : 'moon'" />
    </button>
    
    <form @submit.prevent="handleSubmit" class="mobile-create-account-form" ref="createAccountForm">
      <div class="back-button" @click="$emit('back')" ref="backButton">
        <font-awesome-icon icon="arrow-left" />
      </div>
      
      <div class="logo-container" ref="logoContainer">
        <font-awesome-icon icon="user" class="logo-icon" />
      </div>
      <h2 class="title-text" ref="titleText">Create Account</h2>
      <p class="subtitle" ref="subtitle">Join our secure platform</p>
      
      <div class="form-content" ref="formContent">
        <!-- Step Indicator -->
        <div class="step-indicator" ref="stepIndicator">
          <div class="step" :class="{ active: currentStep === 1 }">1</div>
          <div class="step-line" :class="{ active: currentStep > 1 }"></div>
          <div class="step" :class="{ active: currentStep === 2 }">2</div>
          <div class="step-line" :class="{ active: currentStep > 2 }"></div>
          <div class="step" :class="{ active: currentStep === 3 }">3</div>
        </div>
        
        <!-- Step 1: Account Information -->
        <div v-if="currentStep === 1">
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
                placeholder="Username"
                required
                minlength="3"
                ref="usernameInput"
              />
            </div>
            <p class="input-hint">
              <span v-if="usernameAvailable === null && username.length >= 3">Checking availability...</span>
              <span v-else-if="usernameAvailable === true" class="available">
                <font-awesome-icon icon="check-circle" /> Username available
              </span>
              <span v-else-if="usernameAvailable === false" class="unavailable">
                <font-awesome-icon icon="times-circle" /> Username already taken
              </span>
              <span v-else>Choose a unique username (min. 3 characters)</span>
            </p>
          </div>
          
          <div class="input-group" ref="emailGroup">
            <div class="input-container">
              <font-awesome-icon icon="envelope" class="input-icon" />
              <input
                type="email"
                id="email"
                v-model="email"
                :disabled="loading"
                class="input-field"
                autocomplete="email"
                placeholder="Email Address"
                required
                ref="emailInput"
              />
            </div>
            <p class="input-hint">
              <span v-if="emailAvailable === null && isValidEmail">Checking availability...</span>
              <span v-else-if="emailAvailable === true" class="available">
                <font-awesome-icon icon="check-circle" /> Email available
              </span>
              <span v-else-if="emailAvailable === false" class="unavailable">
                <font-awesome-icon icon="times-circle" /> Email already registered
              </span>
              <span v-else>We'll send a verification code to this email</span>
            </p>
          </div>
          
          <button type="button" class="action-button" :disabled="loading || !canProceedStep1" @click="proceedToStep2" ref="nextButton">
            <template v-if="loading">
              <font-awesome-icon icon="spinner" spin class="mr-2" />
              Processing...
            </template>
            <template v-else>
              Continue
              <font-awesome-icon icon="arrow-right" class="ml-2" />
            </template>
          </button>
        </div>
        
        <!-- Step 2: Password Creation -->
        <div v-if="currentStep === 2">
          <div class="input-group" ref="passwordGroup">
            <div class="input-container">
              <font-awesome-icon icon="lock" class="input-icon" />
              <input
                type="password"
                id="password"
                v-model="password"
                :disabled="loading"
                class="input-field"
                placeholder="Password"
                required
                minlength="8"
                ref="passwordInput"
              />
            </div>
            <p class="password-strength" :class="passwordStrengthClass">
              <font-awesome-icon :icon="passwordStrengthIcon" class="mr-1" />
              {{ passwordStrengthText }}
            </p>
            
            <div class="password-requirements">
              <div class="requirement" :class="{ met: password.length >= 8 }">
                <font-awesome-icon :icon="password.length >= 8 ? 'check-circle' : 'circle'" class="mr-1" />
                At least 8 characters
              </div>
              <div class="requirement" :class="{ met: password.match(/[A-Z]/) }">
                <font-awesome-icon :icon="password.match(/[A-Z]/) ? 'check-circle' : 'circle'" class="mr-1" />
                At least one uppercase letter
              </div>
              <div class="requirement" :class="{ met: password.match(/[0-9]/) }">
                <font-awesome-icon :icon="password.match(/[0-9]/) ? 'check-circle' : 'circle'" class="mr-1" />
                At least one number
              </div>
              <div class="requirement" :class="{ met: password.match(/[^A-Za-z0-9]/) }">
                <font-awesome-icon :icon="password.match(/[^A-Za-z0-9]/) ? 'check-circle' : 'circle'" class="mr-1" />
                At least one special character
              </div>
            </div>
          </div>
          
          <div class="input-group" ref="confirmPasswordGroup">
            <div class="input-container">
              <font-awesome-icon icon="check-double" class="input-icon" />
              <input
                type="password"
                id="confirmPassword"
                v-model="confirmPassword"
                :disabled="loading"
                class="input-field"
                placeholder="Confirm Password"
                required
                ref="confirmPasswordInput"
              />
            </div>
            <p class="input-hint error" v-if="passwordMismatch">
              <font-awesome-icon icon="exclamation-circle" class="mr-1" />
              Passwords don't match
            </p>
          </div>
          
          <div class="button-group">
            <button type="button" class="secondary-button" @click="currentStep = 1" :disabled="loading" ref="backStepButton">
              <font-awesome-icon icon="arrow-left" class="mr-2" />
              Back
            </button>
            
            <button type="button" class="action-button next-button" :disabled="loading || !canProceedStep2" @click="proceedToStep3" ref="nextStepButton">
              <template v-if="loading">
                <font-awesome-icon icon="spinner" spin class="mr-2" />
                Processing...
              </template>
              <template v-else>
                Continue
                <font-awesome-icon icon="arrow-right" class="ml-2" />
              </template>
            </button>
          </div>
        </div>
        
        <!-- Step 3: Terms and Verification -->
        <div v-if="currentStep === 3">
          <div class="terms-section" ref="termsSection">
            <h3 class="terms-title">Almost Done!</h3>
            <p class="terms-text">By creating an account, you agree to our Terms of Service and Privacy Policy. Please read them carefully.</p>
            
            <div class="checkbox-container">
              <input type="checkbox" id="agreeTerms" v-model="agreedToTerms" :disabled="loading" class="custom-checkbox" />
              <label for="agreeTerms" class="checkbox-label">
                I agree to the <a href="#" @click.prevent="showTerms" class="terms-link">Terms of Service</a> and <a href="#" @click.prevent="showPrivacy" class="terms-link">Privacy Policy</a>
              </label>
            </div>
            
            <div class="checkbox-container">
              <input type="checkbox" id="agreeUpdates" v-model="agreedToUpdates" :disabled="loading" class="custom-checkbox" />
              <label for="agreeUpdates" class="checkbox-label">
                I would like to receive updates and newsletters (optional)
              </label>
            </div>
          </div>
          
          <div class="button-group">
            <button type="button" class="secondary-button" @click="currentStep = 2" :disabled="loading" ref="backToPasswordButton">
              <font-awesome-icon icon="arrow-left" class="mr-2" />
              Back
            </button>
            
            <button type="submit" class="action-button create-button" :disabled="loading || !canSubmit" ref="createButton">
              <template v-if="loading">
                <font-awesome-icon icon="spinner" spin class="mr-2" />
                Creating...
              </template>
              <template v-else>
                <font-awesome-icon icon="user-plus" class="mr-2" />
                Create Account
              </template>
            </button>
          </div>
        </div>
        
        <!-- Success State -->
        <div v-if="accountCreated" class="success-container" ref="successContainer">
          <div class="success-icon">
            <font-awesome-icon icon="check-circle" />
          </div>
          <h3 class="success-title">Account Created Successfully!</h3>
          <p class="success-message">Welcome to our platform. You can now log in.</p>
          <button type="button" class="action-button" @click="$emit('back')">
            <font-awesome-icon icon="sign-in-alt" class="mr-2" />
            Go to Login
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useToast } from 'vue-toastification'
import "vue-toastification/dist/index.css"
import api from '@/services/api'
import { ref, onMounted } from 'vue'

export default {
  name: 'MobileCreateAccountComponent',
  components: { FontAwesomeIcon },
  emits: ['back', 'account-created'],
  setup() {
    const toast = useToast()
    
    // Theme detection and management
    const isDarkTheme = ref(false)
    
    const initializeTheme = () => {
      const savedTheme = localStorage.getItem('theme')
      if (savedTheme) {
        isDarkTheme.value = savedTheme === 'dark'
      } else {
        // Check system preference
        isDarkTheme.value = window.matchMedia('(prefers-color-scheme: dark)').matches
      }
      document.documentElement.setAttribute('data-theme', isDarkTheme.value ? 'dark' : 'light')
    }
    
    const toggleTheme = () => {
      isDarkTheme.value = !isDarkTheme.value
      const newTheme = isDarkTheme.value ? 'dark' : 'light'
      document.documentElement.setAttribute('data-theme', newTheme)
      localStorage.setItem('theme', newTheme)
    }
    
    onMounted(() => {
      initializeTheme()
      
      // Add listener for system theme change
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) { // Only if user hasn't set preference
          isDarkTheme.value = e.matches
          document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light')
        }
      })
    })
    
    return { toast, isDarkTheme, toggleTheme }
  },
  data() {
    return {
      currentStep: 1,
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      agreedToTerms: false,
      agreedToUpdates: false,
      loading: false,
      accountCreated: false,
      usernameAvailable: null,
      emailAvailable: null,
      debounceTimer: null,
      formError: null
    }
  },
  computed: {
    isValidEmail() {
      return this.email.includes('@') && this.email.includes('.');
    },
    passwordStrength() {
      // Simple password strength calculation
      let strength = 0;
      const password = this.password;
      
      if (password.length >= 8) strength += 1;
      if (password.match(/[A-Z]/)) strength += 1;
      if (password.match(/[0-9]/)) strength += 1;
      if (password.match(/[^A-Za-z0-9]/)) strength += 1;
      
      return strength;
    },
    passwordStrengthText() {
      const strength = this.passwordStrength;
      if (strength === 0) return 'Too weak';
      if (strength === 1) return 'Weak';
      if (strength === 2) return 'Medium';
      if (strength === 3) return 'Strong';
      if (strength === 4) return 'Very strong';
      return '';
    },
    passwordStrengthClass() {
      const strength = this.passwordStrength;
      if (strength === 0) return 'pw-very-weak';
      if (strength === 1) return 'pw-weak';
      if (strength === 2) return 'pw-medium';
      if (strength === 3) return 'pw-strong';
      if (strength === 4) return 'pw-very-strong';
      return '';
    },
    passwordStrengthIcon() {
      const strength = this.passwordStrength;
      if (strength <= 1) return 'times-circle';
      if (strength === 2) return 'exclamation-circle';
      return 'check-circle';
    },
    passwordMismatch() {
      return this.confirmPassword && this.password !== this.confirmPassword;
    },
    canProceedStep1() {
      return this.username.length >= 3 && 
             this.isValidEmail && 
             this.usernameAvailable !== false &&
             this.emailAvailable !== false;
    },
    canProceedStep2() {
      return this.password.length >= 8 &&
             this.confirmPassword === this.password &&
             this.passwordStrength >= 2;
    },
    canSubmit() {
      return this.canProceedStep1 && 
             this.canProceedStep2 && 
             this.agreedToTerms;
    }
  },
  watch: {
    username(newVal) {
      if (newVal.length >= 3) {
        this.debouncedCheckUsername();
      } else {
        this.usernameAvailable = null;
      }
    },
    email() {
      if (this.isValidEmail) {
        this.debouncedCheckEmail();
      } else {
        this.emailAvailable = null;
      }
    }
  },
  methods: {
    proceedToStep2() {
      if (!this.canProceedStep1) return;
      this.currentStep = 2;
      
      // Focus on password input when moving to step 2
      setTimeout(() => {
        if (this.$refs.passwordInput) {
          this.$refs.passwordInput.focus();
        }
      }, 300);
    },
    
    proceedToStep3() {
      if (!this.canProceedStep2) return;
      this.currentStep = 3;
    },
    
    showTerms() {
      this.toast.info("Terms of Service would be displayed here", {
        timeout: 3000,
        position: "top-center"
      });
    },
    
    showPrivacy() {
      this.toast.info("Privacy Policy would be displayed here", {
        timeout: 3000,
        position: "top-center"
      });
    },
    
    debouncedCheckUsername() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.checkUsername();
      }, 500);
    },
    
    debouncedCheckEmail() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.checkEmail();
      }, 500);
    },
    
    async checkUsername() {
      if (this.username.length < 3) return;
      
      try {
        const response = await api.post('/api/check-username', { username: this.username });
        this.usernameAvailable = response.data.available;
      } catch (error) {
        console.error('Username check error:', error);
        this.usernameAvailable = null;
      }
    },
    
    async checkEmail() {
      if (!this.isValidEmail) return;
      
      try {
        const response = await api.post('/api/check-email', { email: this.email });
        this.emailAvailable = response.data.available;
      } catch (error) {
        console.error('Email check error:', error);
        this.emailAvailable = null;
      }
    },
    
    async handleSubmit() {
      if (this.loading || !this.canSubmit) return;
      
      this.loading = true;
      this.formError = null;
      
      try {
        const response = await api.post('/api/register', {
          username: this.username,
          email: this.email,
          password: this.password,
          receiveUpdates: this.agreedToUpdates
        });
        
        if (response.status === 201) {
          this.accountCreated = true;
          this.toast.success("Account created successfully!", {
            position: "top-center"
          });
          
          // Emit event with username for auto-login
          this.$emit('account-created', this.username);
        } else {
          this.formError = response.data.message || "Failed to create account";
          this.toast.error(this.formError, {
            position: "top-center"
          });
        }
      } catch (error) {
        console.error('Registration error:', error);
        this.formError = error.response?.data?.message || 
                         "An error occurred while creating your account";
        this.toast.error(this.formError, {
          position: "top-center"
        });
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
  /* CSS Variables for Theming */
  /* Light theme variables (default) */
  :root {
    /* Color scheme */
    --primary-color: #3498db;
    --primary-dark: #2980b9;
    --secondary-color: #95a5a6;
    --success-color: #2ecc71;
    --danger-color: #e74c3c;
    --warning-color: #f39c12;
    
    /* Backgrounds */
    --bg-main: #f8f9fa;
    --bg-card: #ffffff;
    --bg-input: #ffffff;
    --bg-button-secondary: #e9ecef;
    --bg-step: #e9ecef;
    --bg-step-active: var(--primary-color);
    --bg-step-line: #e9ecef;
    --bg-step-line-active: var(--primary-color);
    --bg-password-req: #f1f3f5;
    --bg-checkbox: rgba(0, 0, 0, 0.05);
    
    /* Text */
    --text-primary: #212529;
    --text-secondary: #6c757d;
    --text-muted: #868e96;
    --text-contrast: #ffffff;
    --text-success: #2ecc71;
    --text-danger: #e74c3c;
    --text-warning: #f39c12;
    --text-link: var(--primary-color);
    
    /* Borders */
    --border-color: #dee2e6;
    --border-color-focus: #3498db;
    --border-radius-sm: 8px;
    --border-radius-md: 12px;
    --border-radius-lg: 16px;
    --border-radius-full: 50%;
    
    /* Shadows */
    --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.15);
    
    /* Focus */
    --focus-ring-color: rgba(52, 152, 219, 0.5);
    --focus-ring-width: 3px;
  }

  /* Dark theme variables */
  [data-theme="dark"] {
    /* Color scheme */
    --primary-color: #3498db;
    --primary-dark: #2980b9;
    --secondary-color: #7f8c8d;
    --success-color: #2ecc71;
    --danger-color: #e74c3c;
    --warning-color: #f39c12;
    
    /* Backgrounds */
    --bg-main: #121212;
    --bg-card: #1e1e1e;
    --bg-input: #252525;
    --bg-button-secondary: #333333;
    --bg-step: #2c2c2c;
    --bg-step-active: var(--primary-color);
    --bg-step-line: #2c2c2c;
    --bg-step-line-active: var(--primary-color);
    --bg-password-req: rgba(255, 255, 255, 0.03);
    --bg-checkbox: rgba(255, 255, 255, 0.03);
    
    /* Text */
    --text-primary: #ffffff;
    --text-secondary: #b3b3b3;
    --text-muted: #8a8a8a;
    --text-contrast: #ffffff;
    --text-success: #2ecc71;
    --text-danger: #e74c3c;
    --text-warning: #f39c12;
    --text-link: var(--primary-color);
    
    /* Borders */
    --border-color: #2c2c2c;
    --border-color-focus: #3498db;
    
    /* Shadows */
    --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.2);
    --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.3);
    --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.3);
    
    /* Focus */
    --focus-ring-color: rgba(52, 152, 219, 0.5);
    --focus-ring-width: 3px;
  }

  /* Theme Toggle Button - positioned for easy thumb access */
  .theme-toggle-button {
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

.theme-toggle-button:focus-visible {
  outline: 3px solid var(--focus-ring-color);
  outline-offset: 2px;
}

.theme-toggle-button:active {
  transform: translateY(1px);
}

  /* Main Container */
  .mobile-create-account-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    width: 100%;
    padding: 1rem;
    background-color: var(--bg-main);
    transition: background-color 0.3s ease;
    border-radius: 1rem;
    box-shadow: 0 0.25rem 0.75rem var(--shadow-color);
  }

  /* Form Container */
  .mobile-create-account-form {
    width: 100%;
    max-width: 480px;
    padding: 1.75rem 1.5rem;
    background: var(--bg-card);
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-lg);
    position: relative;
    transition: all 0.3s ease;
  }

  /* Back Button */
  .back-button {
    position: absolute;
    top: 1.25rem;
    left: 1.25rem;
    background: rgba(var(--primary-color-rgb), 0.1);
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.75rem; /* Increased to 44px min */
    height: 2.75rem; /* Increased to 44px min */
    border-radius: var(--border-radius-full);
    -webkit-tap-highlight-color: transparent;
  }

  .back-button:hover, .back-button:active {
    background: rgba(var(--primary-color-rgb), 0.2);
    color: var(--primary-color);
  }

  .back-button:focus-visible {
    outline: var(--focus-ring-width) solid var(--focus-ring-color);
    outline-offset: 0.125rem;
  }

  /* Logo Container */
  .logo-container {
    text-align: center;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
  }

  .logo-icon {
    font-size: 2rem;
    color: var(--primary-color);
    padding: 1.25rem;
    border-radius: var(--border-radius-full);
    background: rgba(var(--primary-color-rgb), 0.1);
  }

  /* Typography */
  .title-text {
    color: var(--text-primary);
    font-size: 1.6rem;
    text-align: center;
    margin: 0 0 0.5rem 0;
    font-weight: 700;
  }

  .subtitle {
    color: var(--text-secondary);
    text-align: center;
    margin-bottom: 1.75rem;
    font-size: 0.95rem;
  }

  /* Form Content */
  .form-content {
    margin-top: 1.25rem;
  }

  /* Step Indicator */
  .step-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 2rem;
  }

  .step {
    width: 2.5rem; /* 40px */
    height: 2.5rem; /* 40px */
    border-radius: var(--border-radius-full);
    background-color: var(--bg-step);
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95rem;
    font-weight: 600;
    transition: all 0.3s ease;
    border: 2px solid transparent;
    border-radius: 100%;
  }

  .step.active {
    background-color: var(--bg-step-active);
    color: var(--text-contrast);
    border-color: rgba(var(--primary-color-rgb), 0.3);
    box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2);
    border-radius: 100%;
  }

  .step-line {
    height: 0.1875rem; /* 3px */
    width: 1.875rem; /* 30px */
    background-color: var(--bg-step-line);
    margin: 0 0.375rem; /* 6px */
    transition: all 0.3s ease;
  }

  .step-line.active {
    background-color: var(--bg-step-line-active);
  }

  /* Input Groups */
  .input-group {
    margin-bottom: 1.5rem;
  }

  .input-container {
    position: relative;
    border-radius: var(--border-radius-md);
    overflow: hidden;
    transition: all 0.3s ease;
    box-shadow: var(--shadow-sm);
    border-radius: 0.8rem;
  
  }

  .input-container:focus-within {
    box-shadow: 0 0 0 2px var(--focus-ring-color);
    border-radius: 0.8rem;
  }

  .input-icon {
    position: absolute;
    left: 1.1rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 1rem;
  }

  .input-field {
    width: 100%;
    padding: 1rem 1rem 1rem 3rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-md);
    color: var(--text-primary);
    font-size: 1rem;
    background: var(--bg-input);
    transition: all 0.3s ease;
    height: 3rem; /* Ensures minimum 48px height */
    border-radius: 0.8rem;
  }

  .input-field:focus {
    border-color: var(--border-color-focus);
    outline: none;
  }
/* CSS Variables for Theming */
/* Continue from where it was cut off */

.input-field::placeholder {
  color: var(--text-muted);
  opacity: 0.7;
}

.input-field:disabled {
  background-color: rgba(var(--secondary-color-rgb), 0.1);
  cursor: not-allowed;
  opacity: 0.7;
}

.input-hint {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 0.5rem;
  margin-bottom: 0;
  padding-left: 0.5rem;
}

.input-hint.error {
  color: red;
}

/* Password Strength */
.password-strength {
  font-size: 0.85rem;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  padding-left: 0.5rem;
  display: flex;
  align-items: center;
}

.pw-very-weak, 
.pw-weak {
  color: red;
}

.pw-medium {
  color: yellow;
}

.pw-strong, 
.pw-very-strong {
  color: green;
}

/* Password Requirements */
.password-requirements {
  padding: 0.75rem;
  border-radius: var(--border-radius-sm);
  background-color: var(--bg-password-req);
  margin-top: 0.75rem;
}

.requirement {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.375rem;
  display: flex;
  align-items: center;
}

.requirement:last-child {
  margin-bottom: 0;
}

.requirement.met {
  color: green;
}

.requirement svg {
  margin-right: 0.5rem;
  font-size: 0.875rem;
}

/* Available/Unavailable Statuses */
.available {
  color: green;
}

.unavailable {
  color: red;
}

/* Buttons */
.action-button,
.secondary-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.25rem;
  border-radius: 0.8rem;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: pointer;
  height: 3rem; /* Minimum 48px for touch targets */
  width: 100%;
  border: none;
  -webkit-tap-highlight-color: transparent;
}

.action-button {
  background-color: var(--primary-color);
  color: var(--text-contrast);
  box-shadow: var(--shadow-sm);
}

.action-button:hover:not(:disabled),
.action-button:active:not(:disabled) {
  background-color: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.action-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.secondary-button {
  background-color: var(--bg-button-secondary);
  color: var(--text-secondary);
}

.secondary-button:hover:not(:disabled),
.secondary-button:active:not(:disabled) {
  background-color: var(--border-color);
  color: var(--text-primary);
}

.secondary-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.button-group {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

.button-group .secondary-button,
.button-group .action-button {
  flex: 1;
}

/* Terms Section */
.terms-section {
  margin-bottom: 1.5rem;
}

.terms-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
}

.terms-text {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 1.25rem;
  line-height: 1.5;
}

.checkbox-container {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  position: relative;
  padding: 0.25rem 0;
}

.custom-checkbox {
  position: relative;
  width: 1.25rem;
  height: 1.25rem;
  min-width: 1.25rem;
  margin-right: 0.75rem;
  appearance: none;
  -webkit-appearance: none;
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  background-color: var(--bg-checkbox);
  cursor: pointer;
  transition: all 0.2s ease;
}

.custom-checkbox:checked {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.custom-checkbox:checked::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--text-contrast);
  font-size: 0.8rem;
}

.checkbox-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.terms-link {
  color: var(--text-link);
  text-decoration: underline;
  transition: opacity 0.2s ease;
  margin: 0 0.25rem;
}

.terms-link:hover {
  opacity: 0.8;
}

/* Success Container */
.success-container {
  text-align: center;
  padding: 1.5rem 0;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.success-icon {
  font-size: 3.5rem;
  color: var(--success-color);
  margin-bottom: 1rem;
}

.success-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
}

.success-message {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

/* Utility classes */
.mr-1 { margin-right: 0.25rem; }
.mr-2 { margin-right: 0.5rem; }
.ml-2 { margin-left: 0.5rem; }

/* Responsive adjustments */
@media (min-width: 480px) {
  .mobile-create-account-form {
    padding: 2rem;
  }
}

/* Focus states for accessibility */
button:focus-visible,
input:focus-visible {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: 0.125rem;
}

/* Add missing RGB variables for rgba usage */
:root {
  --primary-color-rgb: 52, 152, 219;
  --secondary-color-rgb: 149, 165, 166;
}

[data-theme="dark"] {
  --primary-color-rgb: 52, 152, 219;
  --secondary-color-rgb: 127, 140, 141;
}

/* Animations */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-5px); }
  40%, 80% { transform: translateX(5px); }
}

.input-container.error {
  animation: shake 0.5s ease;
  border-color: var(--danger-color);
}

/* Touch optimizations for mobile */
@media (hover: none) {
  .action-button:active,
  .secondary-button:active,
  .back-button:active,
  .theme-toggle-button:active {
    transform: scale(0.98);
  }
}

/* iOS Safari specific tweaks */
@supports (-webkit-touch-callout: none) {
  input, button {
    -webkit-appearance: none;
    border-radius: var(--border-radius-md);
  }
}
</style>