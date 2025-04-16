<template>
  <div class="create-account-container">
    <form @submit.prevent="handleSubmit" class="create-account-form" ref="createAccountForm">
      <div class="back-button" @click="$emit('back')" ref="backButton">
        <font-awesome-icon icon="arrow-left" />
      </div>
      
      <div class="logo-container" ref="logoContainer">
        <font-awesome-icon icon="user-plus" class="logo-icon" />
      </div>
      <h2 class="title-text" ref="titleText">Create Account</h2>
      <p class="subtitle" ref="subtitle">Join our secure platform</p>
      
      <div class="form-content" ref="formContent">
        <div class="step-indicator" ref="stepIndicator">
          <div class="step" :class="{ active: currentStep === 1 }">1</div>
          <div class="step-line"></div>
          <div class="step" :class="{ active: currentStep === 2 }">2</div>
          <div class="step-line"></div>
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
                placeholder=" "
                required
                minlength="3"
                ref="usernameInput"
              />
              <label for="username" class="input-label">Username</label>
            </div>
            <p class="input-hint">Choose a unique username (min. 3 characters)</p>
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
                placeholder=" "
                required
                ref="emailInput"
              />
              <label for="email" class="input-label">Email Address</label>
            </div>
            <p class="input-hint">We'll send a verification code to this email</p>
          </div>
          
          <button type="button" class="action-button" :disabled="loading || !canProceedStep1" @click="proceedToStep2" ref="nextButton">
            <template v-if="loading">
              <font-awesome-icon icon="spinner" spin class="mr-2" />
              Processing...
            </template>
            <template v-else>
              <font-awesome-icon icon="arrow-right" class="mr-2" />
              Continue
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
                placeholder=" "
                required
                minlength="8"
                ref="passwordInput"
              />
              <label for="password" class="input-label">Password</label>
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
                placeholder=" "
                required
                ref="confirmPasswordInput"
              />
              <label for="confirmPassword" class="input-label">Confirm Password</label>
            </div>
            <p class="input-hint" v-if="passwordMismatch" style="color: var(--error-color);">
              <font-awesome-icon icon="exclamation-circle" class="mr-1" />
              Passwords don't match
            </p>
          </div>
          
          <div class="button-group">
            <button type="button" class="secondary-button" @click="currentStep = 1" :disabled="loading" ref="backStepButton">
              <font-awesome-icon icon="arrow-left" class="mr-2" />
              Back
            </button>
            
            <button type="button" class="action-button" :disabled="loading || !canProceedStep2" @click="proceedToStep3" ref="nextStepButton">
              <template v-if="loading">
                <font-awesome-icon icon="spinner" spin class="mr-2" />
                Processing...
              </template>
              <template v-else>
                <font-awesome-icon icon="arrow-right" class="mr-2" />
                Continue
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
              <input type="checkbox" id="agreeTerms" v-model="agreedToTerms" :disabled="loading" />
              <label for="agreeTerms" class="checkbox-label">
                I agree to the <a href="#" @click.prevent="showTerms" class="terms-link">Terms of Service</a> and <a href="#" @click.prevent="showPrivacy" class="terms-link">Privacy Policy</a>
              </label>
            </div>
            
            <div class="checkbox-container">
              <input type="checkbox" id="agreeUpdates" v-model="agreedToUpdates" :disabled="loading" />
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
            
            <button type="submit" class="action-button" :disabled="loading || !canSubmit" ref="createButton">
              <template v-if="loading">
                <font-awesome-icon icon="spinner" spin class="mr-2" />
                Creating Account...
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
          <p class="success-message">Welcome to our platform. You can now log in with your credentials.</p>
          <button type="button" class="action-button" @click="$emit('back')">
            <font-awesome-icon icon="sign-in-alt" class="mr-2" />
            Go to Login
          </button>
        </div>
      </div>
      
      <div class="decorative-circles">
        <div class="circle circle-1" ref="circle1"></div>
        <div class="circle circle-2" ref="circle2"></div>
        <div class="circle circle-3" ref="circle3"></div>
      </div>
    </form>
  </div>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useToast } from 'vue-toastification'
import "vue-toastification/dist/index.css"
import anime from 'animejs/lib/anime.es.js'
import api from '@/services/api'

export default {
  name: 'CreateAccountComponent',
  components: { FontAwesomeIcon },
  emits: ['back', 'account-created'],
  setup() {
    const toast = useToast()
    return { toast }
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
             this.email.includes('@') && 
             this.email.includes('.') &&
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
    email(newVal) {
      if (newVal.includes('@') && newVal.includes('.')) {
        this.debouncedCheckEmail();
      } else {
        this.emailAvailable = null;
      }
    }
  },
  mounted() {
    this.initializeAnimations();
  },
  methods: {
    initializeAnimations() {
      // Initial animations when component mounts
      anime.timeline({
        easing: 'easeOutExpo',
      })
      .add({
        targets: this.$refs.createAccountForm,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800,
      })
      .add({
        targets: this.$refs.backButton,
        opacity: [0, 1],
        translateX: [-10, 0],
        duration: 500,
      }, '-=600')
      .add({
        targets: this.$refs.logoContainer,
        scale: [0.5, 1],
        opacity: [0, 1],
        duration: 700,
      }, '-=500')
      .add({
        targets: [this.$refs.titleText, this.$refs.subtitle],
        opacity: [0, 1],
        translateY: [10, 0],
        delay: anime.stagger(150),
        duration: 700,
      }, '-=500')
      .add({
        targets: this.$refs.formContent,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 700,
      }, '-=400')
      .add({
        targets: this.$refs.stepIndicator,
        opacity: [0, 1],
        scale: [0.8, 1],
        duration: 500,
      }, '-=300')
      .add({
        targets: [this.$refs.circle1, this.$refs.circle2, this.$refs.circle3],
        scale: [0, 1],
        opacity: [0, 0.7],
        delay: anime.stagger(150),
        duration: 1000,
      }, '-=700');
      
      // Animate decorative circles continuously
      this.animateDecorations();
    },
    
    animateStepChange() {
      anime.timeline({
        easing: 'easeOutExpo'
      })
      .add({
        targets: this.$refs.formContent,
        opacity: [1, 0],
        translateY: [0, -10],
        duration: 300,
        complete: () => {
          // Animation completed
        }
      })
      .add({
        targets: this.$refs.formContent,
        opacity: [0, 1],
        translateY: [10, 0],
        duration: 500,
      });
    },
    
    animateDecorations() {
      // Continuous animations for decorative elements
      anime({
        targets: this.$refs.circle1,
        translateX: '10px',
        translateY: '15px',
        duration: 8000,
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine'
      });
      
      anime({
        targets: this.$refs.circle2,
        translateX: '-15px',
        translateY: '-10px',
        duration: 9000,
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine'
      });
      
      anime({
        targets: this.$refs.circle3,
        translateX: '8px',
        translateY: '-12px',
        duration: 7000,
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine'
      });
    },
    
    debouncedCheckUsername() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.checkUsernameAvailability();
      }, 500);
    },
    
    debouncedCheckEmail() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.checkEmailAvailability();
      }, 500);
    },
    
    async checkUsernameAvailability() {
      if (!this.username || this.username.length < 3) return;
      
      try {
        const response = await api.post('/api/check-username', {
          username: this.username
        });
        
        if (response.status === 200) {
          this.usernameAvailable = response.data.available;
          if (!this.usernameAvailable) {
            this.toast.error("Username already taken", {
              position: "top-center"
            });
            this.shakeElement(this.$refs.usernameGroup);
          }
        }
      } catch (error) {
        console.error('Username check error:', error);
      }
    },
    
    async checkEmailAvailability() {
      if (!this.email || !this.email.includes('@') || !this.email.includes('.')) return;
      
      try {
        const response = await api.post('/api/check-email', {
          email: this.email
        });
        
        if (response.status === 200) {
          this.emailAvailable = response.data.available;
          if (!this.emailAvailable) {
            this.toast.error("Email already registered", {
              position: "top-center"
            });
            this.shakeElement(this.$refs.emailGroup);
          }
        }
      } catch (error) {
        console.error('Email check error:', error);
      }
    },
    
    async proceedToStep2() {
      if (!this.canProceedStep1) return;
      
      this.loading = true;
      
      try {
        // Final validation for username and email
        const usernameResponse = await api.post('/api/check-username', {
          username: this.username
        });
        
        const emailResponse = await api.post('/api/check-email', {
          email: this.email
        });
        
        if (!usernameResponse.data.available) {
          this.toast.error("Username already taken", {
            position: "top-center"
          });
          this.shakeElement(this.$refs.usernameGroup);
          this.loading = false;
          return;
        }
        
        if (!emailResponse.data.available) {
          this.toast.error("Email already registered", {
            position: "top-center"
          });
          this.shakeElement(this.$refs.emailGroup);
          this.loading = false;
          return;
        }
        
        // Proceed to next step
        this.currentStep = 2;
        this.animateStepChange();
        
        // Focus on password field
        setTimeout(() => {
          if (this.$refs.passwordInput) {
            this.$refs.passwordInput.focus();
          }
        }, 500);
      } catch (error) {
        console.error('Validation error:', error);
        this.toast.error("An error occurred. Please try again.", {
          position: "top-center"
        });
      } finally {
        this.loading = false;
      }
    },
    
    proceedToStep3() {
      if (!this.canProceedStep2) return;
      
      this.currentStep = 3;
      this.animateStepChange();
    },
    
    showTerms() {
      this.toast.info("Terms of Service will open in a new window", {
        position: "top-center"
      });
      // In a real app, you would open the terms page or modal
    },
    
    showPrivacy() {
      this.toast.info("Privacy Policy will open in a new window", {
        position: "top-center"
      });
      // In a real app, you would open the privacy page or modal
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
          
          // Animate success
          anime.timeline({
            easing: 'easeOutExpo'
          })
          .add({
            targets: this.$refs.successContainer,
            scale: [0.9, 1],
            opacity: [0, 1],
            duration: 800,
          });
          
          // Emit event
          this.$emit('account-created', this.username);
        } else {
          this.formError = response.data.message || "Failed to create account";
          this.toast.error(this.formError, {
            position: "top-center"
          });
          this.shakeElement(this.$refs.createAccountForm);
        }
      } catch (error) {
        console.error('Registration error:', error);
        this.formError = error.response?.data?.message || "An error occurred while creating your account";
        this.toast.error(this.formError, {
          position: "top-center"
        });
        this.shakeElement(this.$refs.createAccountForm);
      } finally {
        this.loading = false;
      }
    },
    
    shakeElement(element) {
      if (!element) return;
      
      anime({
        targets: element,
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
    }
  },
  beforeUnmount() {
    clearTimeout(this.debounceTimer);
  }
}
</script>

<style scoped>

.create-account-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 1rem;
  background-color: var(--bg-color);
  overflow: hidden;
}

.create-account-form {
  width: 100%;
  max-width: 480px;
  padding: 2.5rem;
  background: var(--input-bg);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.15);
  position: relative;
  margin-top: 1rem;
  overflow: hidden;
  opacity: 0; /* Initial state for animation */
}

.back-button {
  position: absolute;
  top: 1.5rem;
  left: 1.5rem;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-color);
  opacity: 0.7;
  transition: all 0.3s ease;
  box-shadow: 0 3px 8px rgba(0,0,0,0.1);
  z-index: 10;
}

.back-button:hover {
  transform: translateX(-3px);
  opacity: 1;
  color: var(--primary-color);
}

.form-content {
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

.title-text {
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

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
}

.step {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  border: 2px solid rgba(var(--primary-color-rgb), 0.3);
  color: var(--text-color);
  opacity: 0.7;
  transition: all 0.3s ease;
}

.step.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
  opacity: 1;
  box-shadow: 0 0 0 5px rgba(var(--primary-color-rgb), 0.15);
}

.step-line {
  height: 2px;
  width: 60px;
  background: rgba(var(--primary-color-rgb), 0.3);
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

.input-hint {
  font-size: 0.85rem;
  margin-top: 0.5rem;
  color: var(--text-color);
  opacity: 0.7;
  padding-left: 0.5rem;
}

.password-strength {
  font-size: 0.85rem;
  margin-top: 0.5rem;
  font-weight: 600;
  padding-left: 0.5rem;
  display: flex;
  align-items: center;
}

.pw-very-weak, .pw-weak {
  color: var(--error-color);
}

.pw-medium {
  color: var(--warning-color);
}

.pw-strong, .pw-very-strong {
  color: var(--success-color);
}

.password-requirements {
  margin-top: 1rem;
  padding: 1rem;
  background: var(--bg-color);
  border-radius: 10px;
  font-size: 0.85rem;
}

.requirement {
  margin-bottom: 0.5rem;
  color: var(--text-color);
  opacity: 0.7;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.requirement:last-child {
  margin-bottom: 0;
}

.requirement.met {
  color: var(--success-color);
  opacity: 1;
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.action-button {
  flex: 1;
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
  overflow: hidden;
  z-index: 1;
}

.action-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(var(--primary-color-rgb), 0.3);
}

.action-button:active {
  transform: translateY(-1px);
}

.action-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.secondary-button {
  padding: 1.1rem;
  background: transparent;
  color: var(--text-color);
  border: 2px solid var(--input-border);
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.secondary-button:hover {
  background: var(--bg-color);
  border-color: var(--text-color);
}

.secondary-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.terms-section {
  margin-bottom: 1.5rem;
}

.terms-title {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: var(--text-color);
  font-weight: 600;
}

.terms-text {
  font-size: 0.95rem;
  color: var(--text-color);
  opacity: 0.8;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.checkbox-container {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.checkbox-container input[type="checkbox"] {
  margin-top: 0.25rem;
  margin-right: 0.75rem;
  cursor: pointer;
}

.checkbox-label {
  font-size: 0.95rem;
  color: var(--text-color);
  line-height: 1.5;
}

.terms-link {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
}

.terms-link:hover {
  text-decoration: underline;
}

.success-container {
  text-align: center;
  padding: 1.5rem 0;
  opacity: 0; /* Initial state for animation */
}

.success-icon {
  font-size: 4rem;
  color: var(--success-color);
  margin-bottom: 1.5rem;
}

.success-title {
  font-size: 1.5rem;
  color: var(--text-color);
  margin-bottom: 1rem;
  font-weight: 700;
}

.success-message {
  font-size: 1rem;
  color: var(--text-color);
  opacity: 0.8;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.decorative-circles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.7;
}

.circle-1 {
  width: 180px;
  height: 180px;
  top: -90px;
  right: -60px;
  background: linear-gradient(135deg, rgba(var(--primary-color-rgb), 0.2), rgba(var(--primary-color-rgb), 0.05));
}

.circle-2 {
  width: 140px;
  height: 140px;
  bottom: -50px;
  left: -50px;
  background: linear-gradient(135deg, rgba(var(--accent-color-rgb), 0.2), rgba(var(--accent-color-rgb), 0.05));
}

.circle-3 {
  width: 80px;
  height: 80px;
  bottom: 20%;
  right: 20%;
  background: linear-gradient(135deg, rgba(var(--success-color-rgb), 0.2), rgba(var(--success-color-rgb), 0.05));
}

/* Media queries for responsive design */
@media (max-width: 600px) {
  .create-account-form {
    padding: 2rem 1.5rem;
    margin: 0;
  }
  
  .button-group {
    flex-direction: column;
  }
  
  .step-line {
    width: 30px;
  }
}

/* Dark mode and light mode color variables can be defined in App.vue or another global CSS file */
:root {
  --bg-color: #f8f9fa;
  --input-bg: #ffffff;
  --text-color: #1a2130;
  --input-border: #e1e4e8;
  --primary-color: #4361ee;
  --primary-color-rgb: 67, 97, 238;
  --accent-color: #3a86ff;
  --accent-color-rgb: 58, 134, 255;
  --success-color: #22c55e;
  --success-color-rgb: 34, 197, 94;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
}

/* Dark mode styles */
.dark-mode {
  --bg-color: #121212;
  --input-bg: #1e1e1e;
  --text-color: #f8f9fa;
  --input-border: #333333;
  --primary-color: #5d77ff;
  --primary-color-rgb: 93, 119, 255;
  --accent-color: #60a5fa;
  --accent-color-rgb: 96, 165, 250;
  --success-color: #22c55e;
  --success-color-rgb: 34, 197, 94;
  --warning-color: #fbbf24;
  --error-color: #f87171;
}

/* Animation keyframes */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.mr-1 { margin-right: 0.25rem; }
.mr-2 { margin-right: 0.5rem; }
</style>