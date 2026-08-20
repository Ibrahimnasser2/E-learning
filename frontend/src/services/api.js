// Import axios library for HTTP requests
import axios from 'axios';

// Base server URL
const API_BASE_URL = 'http://localhost:8000';

// RAG API interface
export const ragAPI = {
  // Send message and get response for general inquiries (no auth required)
  post: async (endpoint, data) => {
    const response = await axios.post(`${API_BASE_URL}${endpoint}`, data);
    return response;
  },

  // Send general chat message (fix for missing function)
  sendGeneralMessage: async (message, topK = 3, temperature = 0.2, outputLength = 'mid', enableWebSearch = false) => {
    const response = await axios.post(`${API_BASE_URL}/chat/general`, {
      message,
      top_k: topK,
      temperature,
      output_length: outputLength,
      enable_web_search: enableWebSearch  // Enable web search when internal knowledge is insufficient
    });
    return response.data;
  },

  // Get RAG system statistics
  getStats: async () => {
    const response = await axios.get(`${API_BASE_URL}/stats`);
    return response.data;
  },

  // Upload document to RAG system for indexing
  uploadDocument: async (file, append = true) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('append', append);  // Add to existing index or replace

    const response = await axios.post(`${API_BASE_URL}/upload-document`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Clear all documents from RAG index
  clearIndex: async () => {
    const response = await axios.delete(`${API_BASE_URL}/clear-index`);
    return response.data;
  },

  // Index all available files for the current user
  indexAvailableFiles: async () => {
    const response = await axios.post(`${API_BASE_URL}/index-available-files`);
    return response.data;
  }
};

// Chat API interface (requires authentication)
export const chatAPI = {
  // Get chat history
  getChatHistory: async () => {
    const response = await axios.get(`${API_BASE_URL}/chat`);
    return response.data;
  },

  // Send message and get response
  sendMessage: async (message, topK = 3, temperature = 0.2, outputLength = 'mid', enableWebSearch = false) => {
    const response = await axios.post(`${API_BASE_URL}/chat`, {
      message,  // Message text
      top_k: topK,  // Number of results retrieved from semantic search
      temperature,  // Creativity level in answer generation
      output_length: outputLength,  // Required answer length
      enable_web_search: enableWebSearch  // Enable web search when internal knowledge is insufficient
    });
    return response.data;
  }
};

// File API interface
export const fileAPI = {
  // Upload file to server (with target_roles and specialization)
  uploadFile: async (file, targetRoles = null, specialization = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (targetRoles) {
      formData.append('target_roles', JSON.stringify(targetRoles));
    }
    if (specialization) {
      formData.append('specialization', specialization);
    }
    try {
      const response = await axios.post(`${API_BASE_URL}/upload-file`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      // Try to extract detailed error message from backend
      let message = 'Error uploading file. Please try again.';
      if (error.response && error.response.data && error.response.data.detail) {
        message = error.response.data.detail;
      } else if (error.message) {
        message = error.message;
      }
      throw new Error(message);
    }
  },

  // Get user files
  getUserFiles: async () => {
    const response = await axios.get(`${API_BASE_URL}/files`);
    return response.data;
  },

  // Download file
  downloadFile: async (fileId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/download-file/${fileId}`, {
        responseType: 'blob',
      });
      // Create a blob URL and trigger download
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'download';
      if (contentDisposition) {
        // Improved regex to handle quoted and unquoted filenames better
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/i);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();

      // Cleanup with delay to ensure download starts and avoid race conditions
      setTimeout(() => {
        if (link.parentNode) {
          document.body.removeChild(link);
        }
        window.URL.revokeObjectURL(url);
      }, 100);

    } catch (error) {
      console.error('Error downloading file:', error);
      // Only show alert if it's not a successful download that somehow triggered an error
      // But since we can't easily know, we'll keep the alert but make it clearer if needed.
      // For now, the main fix is the setTimeout above which should prevent the error if it was due to cleanup.
      alert('Error downloading file. Please try again.');
    }
  },

  // Upload student Excel file
  uploadStudentFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE_URL}/upload-student-file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  // Upload faculty Excel file
  uploadFacultyFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE_URL}/upload-faculty-file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  // Upload staff Excel file
  uploadStaffFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE_URL}/upload-staff-file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
};

// Auth API interface
export const authAPI = {
  login: async (username, password, role) => {
    const response = await axios.post(`${API_BASE_URL}/login`, {
      username,
      password,
      role
    });
    return response.data;
  },
  register: async (username, email, password, role, specialization = null) => {
    const response = await axios.post(`${API_BASE_URL}/register`, {
      username,
      email,
      password,
      role,
      specialization
    });
    return response.data;
  }
};

// Course API interface
export const courseAPI = {
  // Create a new course (faculty only)
  createCourse: async (courseData) => {
    const response = await axios.post(`${API_BASE_URL}/courses`, courseData);
    return response.data;
  },

  // Get my courses (faculty: all their courses, student: courses matching specialization)
  getMyCourses: async () => {
    const response = await axios.get(`${API_BASE_URL}/courses/my-courses`);
    return response.data;
  },

  // Get course details
  getCourse: async (courseId) => {
    const response = await axios.get(`${API_BASE_URL}/courses/${courseId}`);
    return response.data;
  },

  // Update course (faculty only - owner)
  updateCourse: async (courseId, courseData) => {
    const response = await axios.put(`${API_BASE_URL}/courses/${courseId}`, courseData);
    return response.data;
  },

  // Delete course (faculty only - owner)
  deleteCourse: async (courseId) => {
    const response = await axios.delete(`${API_BASE_URL}/courses/${courseId}`);
    return response.data;
  },

  // Enroll in course (student only)
  enrollInCourse: async (courseId) => {
    const response = await axios.post(`${API_BASE_URL}/courses/${courseId}/enroll`);
    return response.data;
  },

  // Get my enrollments (student only)
  getMyEnrollments: async () => {
    const response = await axios.get(`${API_BASE_URL}/courses/my-enrollments`);
    return response.data;
  },

  // Scrape metadata from URL
  scrapeMetadata: async (url) => {
    const response = await axios.get(`${API_BASE_URL}/tools/scrape-metadata`, {
      params: { url }
    });
    return response.data;
  }
};

// Server health check API interface

// Server health check API interface
export const healthAPI = {
  // Check server and RAG manager status
  checkHealth: async () => {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  }
}; 