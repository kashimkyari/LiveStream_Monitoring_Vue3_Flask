// src/services/MobileStreamService.js
// Mobile-optimized service for API interactions

import axios from 'axios';
import { ref } from 'vue';

/**
 * Mobile-optimized Stream Service that handles caching and optimized API requests
 * to reduce data usage and improve performance on mobile devices
 */
class MobileStreamService {
  
  /**
   * Get details for a specific stream
   * @param {number} streamId - The ID of the stream to fetch
   * @returns {Promise} - Promise resolving to stream data
   */
  static async getStream(streamId) {
    // Try to find in cache first
    if (this.isCacheValid('streams')) {
      const cachedStream = this._cache.streams.value.find(s => s.id === streamId);
      if (cachedStream) return cachedStream;
    }

    // If not in cache or cache expired, fetch from API
    return axios.get(`/api/streams/${streamId}`)
      .then(response => {
        // Update this single stream in cache if streams cache exists
        if (this._cache.streams.value.length > 0) {
          const index = this._cache.streams.value.findIndex(s => s.id === streamId);
          if (index >= 0) {
            this._cache.streams.value[index] = response.data;
          } else {
            this._cache.streams.value.push(response.data);
          }
        }
        return response.data;
      });
  }

  /**
   * Get all assignments for a specific agent with caching
   * @param {number} agentId - The agent ID
   * @returns {Promise} - Promise resolving to list of assignments
   */
  static async getAgentAssignments(agentId) {
    const cacheKey = `assignments_${agentId}`;
    
    // Check cache
    if (this._cache.queryCache.has(cacheKey)) {
      const cachedData = this._cache.queryCache.get(cacheKey);
      if (Date.now() - cachedData.timestamp < this._cache.expirationTime) {
        return cachedData.data;
      }
    }

    // Fetch fresh data
    return axios.get(`/api/agents/${agentId}/assignments`)
      .then(response => {
        // Store in cache
        this._cache.queryCache.set(cacheKey, {
          data: response.data,
          timestamp: Date.now()
        });
        return response.data;
      });
  }

  /**
   * Get all streams with optional filters and caching for mobile
   * @param {Object} [filters={}] - Optional filters (platform, streamer)
   * @param {string} [filters.platform] - Platform filter (chaturbate|stripchat)
   * @param {string} [filters.streamer] - Streamer username search string
   * @param {boolean} [forceRefresh=false] - Whether to force a refresh from the API
   * @returns {Promise} - Promise resolving to list of streams
   */
  static async getAllStreams(filters = {}, forceRefresh = false) {
    // Create a cache key for this specific query
    const cacheKey = `streams_${filters.platform || 'all'}_${filters.streamer || 'all'}`;
    
    // Mobile optimization parameters to reduce data usage
    const mobileParams = {
      platform: filters.platform,
      streamer: filters.streamer,
      mobile_view: true,        // Signal to backend this is a mobile request
      exclude_thumbnails: true, // Explicitly exclude thumbnails to reduce data
      min_data: true            // Request minimal data payload
    };
    
    // If we have a specific filter, use query cache
    if (filters.platform || filters.streamer) {
      if (!forceRefresh && this._cache.queryCache.has(cacheKey)) {
        const cachedData = this._cache.queryCache.get(cacheKey);
        if (Date.now() - cachedData.timestamp < this._cache.expirationTime) {
          return cachedData.data;
        }
      }
      
      // Fetch with filters
      return axios.get('/api/streams', {
        params: mobileParams
      }).then(response => {
        // Store in query cache
        this._cache.queryCache.set(cacheKey, {
          data: response.data,
          timestamp: Date.now()
        });
        return response.data;
      });
    } 
    
    // For all streams without filters, use main cache
    if (!forceRefresh && this.isCacheValid('streams')) {
      return this._cache.streams.value;
    }
    
    // Fetch all streams with mobile optimization
    return axios.get('/api/streams', {
      params: {
        mobile_view: true,
        exclude_thumbnails: true,
        min_data: true
      }
    }).then(response => {
        // Update main cache
        this._cache.streams.value = response.data;
        this._cache.lastFetched.streams = Date.now();
        return response.data;
      });
  }

  /**
   * Get all agents with caching for mobile
   * @param {boolean} [forceRefresh=false] - Whether to force a refresh from the API
   * @returns {Promise} - Promise resolving to list of agents
   */
  static async getAllAgents(forceRefresh = false) {
    if (!forceRefresh && this.isCacheValid('agents')) {
      return this._cache.agents.value;
    }
    
    return axios.get('/api/agents')
      .then(response => {
        this._cache.agents.value = response.data;
        this._cache.lastFetched.agents = Date.now();
        return response.data;
      });
  }

  /**
   * Create a new stream assignment with optimized request
   * @param {Object} assignmentData - Assignment details
   * @param {number} assignmentData.agentId - Agent ID to assign
   * @param {number} assignmentData.streamId - Stream ID to assign
   * @returns {Promise} - Promise resolving to created assignment
   */
  static createAssignment({ agentId, streamId }) {
    return axios.post('/api/assign', { agentId, streamId })
      .then(response => {
        // Invalidate relevant caches
        this._cache.queryCache.delete(`assignments_${agentId}`);
        return response.data;
      });
  }

  /**
   * Update stream assignments in bulk with optimized request
   * @param {number} streamId - Stream ID to update assignments for
   * @param {number[]} agentIds - Array of agent IDs to assign
   * @returns {Promise} - Promise resolving to update result
   */
  static bulkUpdateAssignments(streamId, agentIds) {
    return axios.post(`/api/assignments/stream/${streamId}`, { agentIds })
      .then(response => {
        // Invalidate all agent assignment caches - cleaner than trying to identify affected ones
        for (const key of this._cache.queryCache.keys()) {
          if (key.startsWith('assignments_')) {
            this._cache.queryCache.delete(key);
          }
        }
        return response.data;
      });
  }

  /**
   * Delete a stream assignment with cache invalidation
   * @param {number} assignmentId - ID of assignment to remove
   * @param {number} agentId - Agent ID associated with the assignment
   * @returns {Promise} - Promise resolving to deletion result
   */
  static deleteAssignment(assignmentId, agentId) {
    return axios.delete(`/api/assignments/${assignmentId}`)
      .then(response => {
        // Invalidate related cache
        if (agentId) {
          this._cache.queryCache.delete(`assignments_${agentId}`);
        }
        return response.data;
      });
  }

  /**
   * Create a new stream with validation and progress tracking
   * Optimized for mobile to reduce bandwidth
   * @param {Object} streamData - Stream creation data
   * @param {string} streamData.room_url - Stream room URL
   * @param {string} streamData.platform - Stream platform
   * @param {number} [streamData.agent_id] - Optional agent ID for assignment
   * @returns {Promise} - Promise resolving to job information
   */
  static createStreamInteractive(streamData) {
    return axios.post('/api/streams/interactive', streamData)
      .then(response => {
        // Invalidate streams cache on successful creation
        this._cache.lastFetched.streams = null;
        return response.data;
      });
  }

  /**
   * Get status of a stream creation job
   * @param {string} jobId - Job ID to check status for
   * @returns {Promise} - Promise resolving to job status
   */
  static getJobStatus(jobId) {
    return axios.get('/api/streams/interactive/status', { 
      params: { job_id: jobId } 
    }).then(response => response.data);
  }

  /**
   * Optimize a request for mobile by reducing unneeded fields
   * This helps reduce data usage for mobile clients 
   * @param {string} endpoint - API endpoint to call
   * @param {Object} [params={}] - Optional query parameters
   * @returns {Promise} - Promise resolving to optimized data
   */
  static getOptimizedRequest(endpoint, params = {}) {
    // Add mobile optimization parameter
    const optimizedParams = {
      ...params,
      mobile_optimized: true
    };
    
    return axios.get(endpoint, { params: optimizedParams })
      .then(response => response.data);
  }

  /**
   * Get dashboard data optimized for mobile
   * @returns {Promise} - Promise resolving to mobile-optimized dashboard data
   */
  static getMobileDashboard() {
    return this.getOptimizedRequest('/api/dashboard', { view: 'mobile' });
  }

  /**
   * Refresh stream data for mobile view
   * @param {Object} stream - Stream to refresh
   * @returns {Promise} - Promise resolving to refresh result
   */
  static refreshStream(stream) {
    const streamId = stream.id;
    const platform = stream.type || stream.platform;

    let payload;
    let endpoint;

    // Platform-specific handling
    if (platform.toLowerCase() === 'chaturbate') {
      let username = '';
      if (stream.room_url?.includes('chaturbate.com/')) {
        username = stream.room_url.split('/').filter(Boolean).pop();
      } else {
        username = stream.streamer_username || '';
      }
      
      endpoint = '/api/streams/refresh/chaturbate';
      payload = { room_slug: username };
    } 
    else if (platform.toLowerCase() === 'stripchat') {
      endpoint = '/api/streams/refresh/stripchat';
      payload = { room_url: stream.room_url };
    }
    else {
      return Promise.reject(new Error('Unsupported platform for refresh'));
    }

    return axios.post(endpoint, payload)
      .then(response => {
        // Update cached stream if available
        if (this._cache.streams.value.length > 0) {
          const index = this._cache.streams.value.findIndex(s => s.id === streamId);
          if (index >= 0) {
            this._cache.streams.value[index] = {
              ...this._cache.streams.value[index],
              m3u8_url: response.data.m3u8_url
            };
          }
        }
        return response.data;
      });
  }
}

MobileStreamService._cache = {
  streams: ref([]),
  agents: ref([]),
  lastFetched: {
    streams: null,
    agents: null,
  },
  expirationTime: 5 * 60 * 1000,
  queryCache: new Map(),
};

// Add reactive properties for convenience
MobileStreamService.streams = MobileStreamService._cache.streams;
MobileStreamService.agents = MobileStreamService._cache.agents;

export default MobileStreamService;