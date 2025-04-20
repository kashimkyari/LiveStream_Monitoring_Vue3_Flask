<template>
  <div class="mobile-create-account-container">
    <form @submit.prevent="handleSubmit" class="mobile-create-account-form" ref="createAccountForm">
      <div class="back-button" @click="$emit('back')" ref="backButton">
        <font-awesome-icon icon="arrow-left" />
      </div>
      
      <div class="logo-container" ref="logoContainer">
        <font-awesome-icon icon="user-plus" class="logo-icon" />
      </div>
      <h2 class="title-text" ref="titleText">Create Account</h2>
      <p class="subtitle" ref="subtitle">Join our secure platform</p>
      
      <div class="form-content" ref="formContent">
        <!-- Step Indicator -->
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

export default {
  name: 'MobileCreateAccountComponent',
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
.mobile-create-account-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  width: 100%;
  padding: 1rem;
  background-color: var(--bs-dark);
}

.mobile-create-account-form {
  width: 100%;
  max-width: 480px;
  padding: 1.5rem;
  background: var(--bs-gray-800);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  position: relative;
}

.back-button {
  position: absolute;
  top: 1rem;
  left: 1rem;
  background: transparent;
  border: none;
  color: var(--bs-gray-400);
  cursor: pointer;
  transition: color 0.2s ease;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.back-button:hover {
  color: var(--bs-info);
}

.logo-container {
  text-align: center;
  margin-top: 1rem;
  margin-bottom: 1.5rem;
}

.logo-icon {
  font-size: 2rem;
  color: var(--bs-info);
  padding: 1rem;
  border-radius: 50%;
  background: rgba(13, 202, 240, 0.1);
}

.title-text {
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

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.step {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: var(--bs-gray-700);
  color: var(--bs-gray-300);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 600;
}

.step.active {
  background-color: var(--bs-info);
  color: white;
}

.step-line {
  height: 2px;
  width: 30px;
  background-color: var(--bs-gray-700);
  margin: 0 5px;
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

.input-hint {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--bs-gray-500);
}

.input-hint.error {
  color: var(--bs-danger);
}

.input-hint .available {
  color: var(--bs-success);
}

.input-hint .unavailable {
  color: var(--bs-danger);
}

.password-requirements {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: var(--bs-gray-500);
}

.requirement {
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.requirement.met {
  color: var(--bs-success);
}

.action-button {
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

.action-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.secondary-button {
  width: 45%;
  padding: 0.8rem;
  background: var(--bs-gray-700);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.secondary-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.button-group {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 1rem;
}

.password-strength {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.pw-very-weak, .pw-weak {
  color: var(--bs-danger);
}

.pw-medium {
  color: var(--bs-warning);
}

.pw-strong {
  color: var(--bs-success);
}

.pw-very-strong {
  color: var(--bs-success);
}

.terms-section {
  margin-bottom: 1.5rem;
}

.terms-title {
  color: white;
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

.terms-text {
  color: var(--bs-gray-400);
  font-size: 0.85rem;
  margin-bottom: 1rem;
  text-align: center;
}

.checkbox-container {
  display: flex;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 0.5rem;
}

.checkbox-label {
  color: var(--bs-gray-300);
  font-size: 0.85rem;
  line-height: 1.4;
}

.terms-link {
  color: var(--bs-info);
  text-decoration: none;
}

.success-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 1.5rem;
}

.success-icon {
  font-size: 3rem;
  color: var(--bs-success);
  margin-bottom: 1rem;
}

.success-title {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.success-message {
  color: var(--bs-gray-400);
  margin-bottom: 1.5rem;
}

@media (max-width: 480px) {
  .mobile-create-account-container {
    padding: 0.5rem;
  }
  
  .mobile-create-account-form {
    padding: 1.25rem;
  }
}
</style>