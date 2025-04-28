// services/StreamService.js

import axios from 'axios';

class StreamService {
  /**
   * Get details for a specific stream
   * @param {number} streamId - The ID of the stream to fetch
   * @returns {Promise} - Promise resolving to stream data
   */
  static getStream(streamId) {
    return axios.get(`/api/streams/${streamId}`)
      .then(response => response.data);
  }

  /**
   * Get all assignments for a specific agent
   * @param {number} agentId - The agent ID
   * @returns {Promise} - Promise resolving to list of assignments
   */
  static getAgentAssignments(agentId) {
    return axios.get(`/api/agents/${agentId}/assignments`)
      .then(response => response.data);
  }

  /**
   * Get all streams with optional filters
   * @param {Object} [filters={}] - Optional filters (platform, streamer)
   * @param {string} [filters.platform] - Platform filter (chaturbate|stripchat)
   * @param {string} [filters.streamer] - Streamer username search string
   * @returns {Promise} - Promise resolving to list of streams
   */
  static getAllStreams(filters = {}) {
    return axios.get('/api/streams', {
      params: {
        platform: filters.platform,
        streamer: filters.streamer
      }
    }).then(response => response.data);
  }

  /**
   * Create a new stream assignment
   * @param {Object} assignmentData - Assignment details
   * @param {number} assignmentData.agentId - Agent ID to assign
   * @param {number} assignmentData.streamId - Stream ID to assign
   * @returns {Promise} - Promise resolving to created assignment
   */
  static createAssignment({ agentId, streamId }) {
    return axios.post('/api/assign', { agentId, streamId })
      .then(response => response.data);
  }

  /**
   * Update stream assignments in bulk
   * @param {number} streamId - Stream ID to update assignments for
   * @param {number[]} agentIds - Array of agent IDs to assign
   * @returns {Promise} - Promise resolving to update result
   */
  static bulkUpdateAssignments(streamId, agentIds) {
    return axios.post(`/api/assignments/stream/${streamId}`, { agentIds })
      .then(response => response.data);
  }

  /**
   * Delete a stream assignment
   * @param {number} assignmentId - ID of assignment to remove
   * @returns {Promise} - Promise resolving to deletion result
   */
  static deleteAssignment(assignmentId) {
    return axios.delete(`/api/assignments/${assignmentId}`)
      .then(response => response.data);
  }

  /**
   * Create a new stream with validation and progress tracking
   * @param {Object} streamData - Stream creation data
   * @param {string} streamData.room_url - Stream room URL
   * @param {string} streamData.platform - Stream platform
   * @param {number} [streamData.agent_id] - Optional agent ID for assignment
   * @returns {Promise} - Promise resolving to job information
   */
  static createStreamInteractive(streamData) {
    return axios.post('/api/streams/interactive', streamData)
      .then(response => response.data);
  }

  /**
   * Get status of a stream creation job
   * @param {string} jobId - Job ID to check status for
   * @returns {Promise} - Promise resolving to job status
   */
  static getJobStatus(jobId) {
    return axios.get('/api/streams/interactive/status', { params: { job_id: jobId } })
      .then(response => response.data);
  }
}

export default StreamService;