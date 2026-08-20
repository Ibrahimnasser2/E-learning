import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { fileAPI } from '../services/api';
import './StudentUpload.css';

const StudentUpload = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  if (!user || user.role !== 'admin') {
    return (
      <div className="student-upload-container">
        <div className="error-card">
          <h2>🔒 Access Denied</h2>
          <p>You do not have permission to access this page.</p>
          <button onClick={() => navigate('/chat')} className="back-button">
            ← Back to Chat
          </button>
        </div>
      </div>
    );
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      setError(null);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.toLowerCase().endsWith('.xlsx') || droppedFile.name.toLowerCase().endsWith('.xls')) {
        setFile(droppedFile);
        setResult(null);
        setError(null);
      } else {
        setError('Please select a valid Excel file (.xlsx or .xls)');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select an Excel file to upload.');
      return;
    }
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await fileAPI.uploadStudentFile(file);
      setResult(res);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Upload failed. Please check the file format and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/chat');
  };

  return (
    <div className="student-upload-container">
      <div className="upload-card">
        <div className="card-header">
          <button onClick={handleBack} className="back-button">
            ← Back to Chat
          </button>
          <h1>📊 Student Upload</h1>
          <p className="subtitle">Upload Excel file to create student accounts</p>
        </div>

        <div className="upload-section">
          <div className="file-requirements">
            <h3>📋 File Requirements</h3>
            <ul>
              <li>File format: <strong>.xlsx</strong> or <strong>.xls</strong></li>
              <li>Required columns: <strong>Name</strong>, <strong>University ID</strong>, <strong>Phone Number</strong></li>
              <li>Each row represents one student</li>
            </ul>
          </div>

          <div className="file-upload-area">
            <div 
              className={`dropzone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                id="file-input"
                style={{ display: 'none' }}
              />
              <label htmlFor="file-input" className="file-input-label">
                {file ? (
                  <div className="file-selected">
                    <span className="file-icon">📄</span>
                    <div className="file-info">
                      <strong>{file.name}</strong>
                      <span>{(file.size / 1024).toFixed(1)} KB</span>
                    </div>
                  </div>
                ) : (
                  <div className="upload-prompt">
                    <span className="upload-icon">📁</span>
                    <p>Drag & drop your Excel file here</p>
                    <p>or click to browse</p>
                  </div>
                )}
              </label>
            </div>
          </div>

          <div className="upload-actions">
            <button 
              onClick={handleUpload} 
              disabled={loading || !file} 
              className={`upload-button ${loading ? 'loading' : ''}`}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Processing...
                </>
              ) : (
                <>
                  <span>📤</span>
                  Upload Students
                </>
              )}
            </button>
          </div>
        </div>

        {result && (
          <div className="result-section success">
            <h3>✅ Upload Complete</h3>
            <div className="result-stats">
              <div className="stat-item">
                <span className="stat-number">{result.added}</span>
                <span className="stat-label">Students Added</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">{result.skipped}</span>
                <span className="stat-label">Students Skipped</span>
              </div>
            </div>
            <p className="result-message">
              {result.added > 0 
                ? `Successfully created ${result.added} new student account${result.added > 1 ? 's' : ''}.`
                : 'No new students were added.'
              }
              {result.skipped > 0 && ` ${result.skipped} student${result.skipped > 1 ? 's were' : ' was'} already registered.`}
            </p>
          </div>
        )}

        {error && (
          <div className="result-section error">
            <h3>❌ Upload Failed</h3>
            <p className="error-message">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentUpload; 