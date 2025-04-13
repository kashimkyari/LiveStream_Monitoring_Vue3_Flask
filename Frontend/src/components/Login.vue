<template>
  <div class="login-container">
    <form @submit.prevent="handleSubmit" class="login-form">
      <div class="logo-container">
        <font-awesome-icon icon="user-lock" class="logo-icon" />
      </div>
      <h2 class="welcome-text">Welcome Back</h2>
      <p class="subtitle">Sign in to continue</p>
      
      <div class="form-content">
        <div class="input-group">
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
            />
            <label for="username" class="input-label">Username</label>
          </div>
        </div>

        <div class="input-group">
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
            />
            <label for="password" class="input-label">Password</label>
          </div>
        </div>

        <button type="submit" class="login-button" :disabled="loading">
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

      <div class="additional-links">
        <a href="#" class="link-text">Forgot password?</a>
        <span class="separator">•</span>
        <a href="#" class="link-text">Create account</a>
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useToast } from 'vue-toastification';
import "vue-toastification/dist/index.css"

export default {
  name: 'LoginComponent',
  components: { FontAwesomeIcon },
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
      error: null
    }
  },
  methods: {
    async handleSubmit() {
      if (!this.username.trim() || !this.password.trim()) {
        this.showError('Please fill in all fields')
        return
      }

      this.loading = true
      this.error = null
      
      try {
        const response = await axios.post('/api/login', {
          username: this.username,
          password: this.password
        }, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        })

        if (response.status === 200 && response.data.message === "Login successful") {
          this.toast.success("Login successful!", {
            timeout: 2000,
            position: "top-center",
            icon: true
          })
          this.$emit('login-success', response.data.role)
        } else {
          this.showError(response.data.message || 'Login failed. Please try again.')
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
      } finally {
        this.loading = false
      }
    },
    showError(message) {
      this.error = message
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
      })
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
}

.login-form {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
  background: var(--input-bg);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  position: relative;
  margin-top: 1rem;
}

.form-content {
  margin-top: 1.5rem;
}

.logo-container {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-icon {
  font-size: 2.5rem;
  color: var(--primary-color);
  padding: 1rem;
  border-radius: 50%;
  background: rgba(var(--primary-color-rgb), 0.1);
}

.welcome-text {
  color: var(--text-color);
  font-size: 1.75rem;
  text-align: center;
  margin: 0 0 1rem 0;
}

.subtitle {
  color: var(--text-color);
  opacity: 0.8;
  text-align: center;
  margin-bottom: 2rem;
  font-size: 0.95rem;
}

.input-group {
  margin-bottom: 1.5rem;
}

.input-container {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-color);
  opacity: 0.6;
  z-index: 1;
}

.input-field {
  width: 100%;
  padding: 1rem 1rem 1rem 3rem;
  border: 2px solid var(--input-border);
  border-radius: 8px;
  color: var(--text-color);
  font-size: 1rem;
  background: var(--bg-color);
  transition: all 0.2s ease;
}

.input-field:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.15);
}

.input-label {
  position: absolute;
  left: 3rem;
  top: 50%;
  transform: translateY(-50%);
  background: var(--bg-color);
  padding: 0 0.5rem;
  color: var(--text-color);
  opacity: 0.6;
  transition: all 0.2s ease;
  pointer-events: none;
}

.input-field:focus + .input-label,
.input-field:not(:placeholder-shown) + .input-label {
  transform: translateY(-1.8rem) scale(0.9);
  opacity: 1;
  color: var(--primary-color);
  left: 2.5rem;
}

.login-button {
  width: 100%;
  padding: 1rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
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
}

.link-text {
  color: var(--text-color);
  opacity: 0.8;
  text-decoration: none;
  font-size: 0.9rem;
  transition: opacity 0.2s ease;
}

.link-text:hover {
  opacity: 1;
}

.separator {
  color: var(--text-color);
  opacity: 0.4;
}
</style>