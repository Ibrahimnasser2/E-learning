import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { chatAPI, fileAPI, ragAPI } from '../services/api';
import { useDropzone } from 'react-dropzone';
import './Chat.css'; // Styles for chat interface
import { useNavigate } from 'react-router-dom';
import {
  User,
  MessageSquare,
  Home,
  Upload,
  BookOpen,
  FileText,
  Globe,
  Loader,
  Hand,
  LogOut,
  Settings,
  Menu,
  X,
  Download,
  File
} from 'lucide-react';

const Chat = () => {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState([]);
  const [ragStats, setRagStats] = useState(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [uploadingRagDoc, setUploadingRagDoc] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settings, setSettings] = useState({
    temperature: 0.7,
    maxOutput: 'medium',
    topK: 3,
    showContext: true,
    autoScroll: true
  });
  const [theme, setTheme] = useState('light');
  const [enableWebSearch, setEnableWebSearch] = useState(false);
  const messagesEndRef = useRef(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [uploadingPDFs, setUploadingPDFs] = useState([]);
  const roles = [
    { value: 'faculty', label: 'أعضاء هيئة التدريس (Faculty)' },
    { value: 'student', label: 'الطلاب (Students)' },
  ];
  const specializations = [
    'Computer Science',
    'Information Technology',
    'Software Engineering',
    'Data Science',
    'Cybersecurity',
    'Artificial Intelligence',
    'Network Engineering',
    'Other'
  ];
  const [targetRoles, setTargetRoles] = useState([]);
  const [selectedSpecialization, setSelectedSpecialization] = useState('');
  const navigate = useNavigate();

  // التمرير التلقائي إلى الأسفل عند وصول رسائل جديدة
  const scrollToBottom = () => {
    if (settings.autoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, settings.autoScroll]);

  // تحميل سجل المحادثات والملفات عند تحميل المكون
  useEffect(() => {
    loadChatHistory();
    loadFiles();
    loadRagStats();
  }, []);

  useEffect(() => {
    setMessages([]); // مسح المحادثة عند تغيير المستخدم (تسجيل دخول/خروج/تسجيل)
    if (user) {
      loadChatHistory();
      loadFiles(); // إعادة تحميل الملفات للمستخدم الجديد
    }
  }, [user]);

  const loadChatHistory = async () => {
    try {
      const response = await chatAPI.getChatHistory();
      setMessages(response.messages || []);
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const loadFiles = async () => {
    try {
      const response = await fileAPI.getUserFiles();
      setFiles(response.files || []);
    } catch (error) {
      console.error('Error loading files:', error);
    }
  };

  const loadRagStats = async () => {
    try {
      const stats = await ragAPI.getStats();
      setRagStats(stats);
    } catch (error) {
      console.error('Error loading RAG stats:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || loading) return;

    setLoading(true);
    const userMessage = newMessage;
    setNewMessage('');

    const tempId = Date.now();
    setMessages(prev => [
      ...prev,
      {
        id: tempId,
        message: userMessage,
        response: '',
        created_at: new Date().toISOString(),
        context: null,
        loading: true
      }
    ]);

    try {
      const response = await chatAPI.sendMessageStream(userMessage, {
        topK: settings.topK,
        temperature: settings.temperature,
        outputLength: settings.maxOutput,
        enableWebSearch,
        onToken: (_token, fullText) => {
          setMessages(prev => prev.map(m =>
            m.id === tempId
              ? { ...m, response: fullText, loading: false }
              : m
          ));
        }
      });
      setMessages(prev => prev.map(m =>
        m.id === tempId
          ? {
              ...response,
              id: response.id || tempId,
              message: userMessage,
              loading: false
            }
          : m
      ));
    } catch (error) {
      let errorMsg = 'Error: Could not get response from bot.';
      if (error.response) {
        errorMsg += ` (Status: ${error.response.status}`;
        if (error.response.data && error.response.data.detail) {
          errorMsg += `, Detail: ${error.response.data.detail}`;
        }
        errorMsg += ')';
      } else if (error.message) {
        errorMsg += ` (${error.message})`;
      }
      setMessages(prev => prev.map(m =>
        m.id === tempId
          ? { ...m, response: errorMsg, loading: false }
          : m
      ));
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  // معالجات رفع الملفات
  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    // Validate specialization if uploading for students
    if (user.role === 'faculty' && targetRoles.includes('student') && !selectedSpecialization) {
      alert('Please select a specialization when uploading for students');
      return;
    }

    setUploadingFile(true);
    try {
      for (const file of acceptedFiles) {
        if (user.role === 'faculty') {
          await fileAPI.uploadFile(file, targetRoles, selectedSpecialization);
        }
      }
      await loadFiles();
      await loadRagStats();
      // Reset specialization after upload
      setSelectedSpecialization('');
    } catch (error) {
      console.error('Error uploading file:', error);
      alert(error.message || 'Error uploading file. Please try again.');
    } finally {
      setUploadingFile(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true
  });

  // رفع وثائق RAG
  const onRagDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;
    const newUploads = acceptedFiles.filter(f => f.name.toLowerCase().endsWith('.pdf')).map(file => ({
      id: `${file.name}-${Date.now()}`,
      name: file.name,
      status: 'Uploading & indexing...'
    }));
    setUploadingPDFs(prev => [...prev, ...newUploads]);
    setUploadingRagDoc(true);
    for (const file of acceptedFiles) {
      if (!file.name.toLowerCase().endsWith('.pdf')) continue;
      try {
        await ragAPI.uploadDocument(file, true);
        setUploadingPDFs(prev => prev.map(f => f.name === file.name && f.status === 'Uploading & indexing...' ? { ...f, status: 'Success' } : f));
        await loadFiles();
        await loadRagStats();
      } catch (error) {
        setUploadingPDFs(prev => prev.map(f => f.name === file.name && f.status === 'Uploading & indexing...' ? { ...f, status: 'Fail to upload' } : f));
        console.error('Error uploading RAG document:', error);
      }
    }
    setUploadingRagDoc(false);
  };

  const { getRootProps: getRagRootProps, getInputProps: getRagInputProps, isDragActive: isRagDragActive } = useDropzone({
    onDrop: onRagDrop,
    multiple: true,
    accept: {
      'application/pdf': ['.pdf']
    }
  });

  const clearRagIndex = async () => {
    if (window.confirm('Are you sure you want to clear the RAG index? This will remove all uploaded documents.')) {
      try {
        await ragAPI.clearIndex();
        await loadRagStats();
        alert('RAG index cleared successfully');
      } catch (error) {
        console.error('Error clearing RAG index:', error);
        alert('Error clearing RAG index. Please try again.');
      }
    }
  };

  const exportChatAsPDF = () => {
    // بناء HTML قابل للطباعة
    let html = `
      <html>
      <head>
        <title>MANAMU Chat Export</title>
        <style>
          body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; margin: 0; padding: 0; }
          .chat-container { max-width: 800px; margin: 40px auto; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); padding: 32px; }
          .msg-row { display: flex; margin-bottom: 24px; }
          .msg-user { justify-content: flex-end; }
          .msg-bot { justify-content: flex-start; }
          .msg-bubble { max-width: 60%; padding: 16px 20px; border-radius: 16px; font-size: 16px; line-height: 1.6; }
          .msg-user .msg-bubble { background: #3498db; color: #fff; margin-left: auto; }
          .msg-bot .msg-bubble { background: #f4f4f4; color: #222; margin-right: auto; }
          .msg-meta { font-size: 12px; color: #888; margin-top: 8px; text-align: right; }
        </style>
      </head>
      <body>
        <div class="chat-container">
          <h2>MANAMU Chat Export</h2>
          <hr style="margin: 24px 0;">
    `;
    messages.forEach(m => {
      html += `<div class="msg-row ${m.response ? 'msg-user' : 'msg-bot'}">`;
      if (m.message) {
        html += `<div class="msg-bubble">${m.message.replace(/\n/g, '<br/>')}</div>`;
      }
      if (m.response) {
        html += `<div class="msg-bubble">${m.response.replace(/\n/g, '<br/>')}</div>`;
      }
      html += `</div>`;
      html += `<div class="msg-meta">${formatDate(m.created_at)}</div>`;
    });
    html += `</div></body></html>`;
    // فتح نافذة جديدة والطباعة
    const win = window.open('', '', 'width=900,height=700');
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => { win.print(); }, 500);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  // دمج ملفات PDF من الخادم والملفات المحلية المرفوعة
  const backendPDFs = files.filter(f => (f.original_filename || '').toLowerCase().endsWith('.pdf'));
  const mergedPDFs = [
    ...uploadingPDFs
      .filter(up => !backendPDFs.some(f => f.original_filename === up.name)),
    ...backendPDFs.map(f => ({
      id: f.id,
      name: f.original_filename,
      status: 'Success',
      file_size: f.file_size,
      file_type: f.file_type,
      upload_time: f.upload_time
    }))
  ];

  return (
    <div className={`chat-layout theme-${theme}`}>
      {/* Fixed Header Container */}
      <header className="chat-header">
        <div className="header-left">
          <div className="header-title">
            <h1>MANAMU</h1>
            <span className="subtitle">AI Assistant</span>
          </div>
        </div>
        <div className="header-right">
          {/* Hide settings button for student/general_inquiry */}
          <div className="user-info">
            <span className="username">Welcome, {user?.username}!</span>
            <button onClick={logout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Fixed Sidebar Container */}
      <aside className={`chat-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-toggle-btn-container">
          <button
            className="sidebar-toggle-btn"
            onClick={() => setSidebarOpen((open) => !open)}
            title={sidebarOpen ? 'Close menu' : 'Open menu'}
          >
            <Menu size={24} />
          </button>
        </div>
        <div className="sidebar-section">
          {sidebarOpen && <h3>Menu</h3>}
          <button className="sidebar-button" onClick={() => setActiveTab('chat')} title="Home">
            <Home size={18} />{sidebarOpen && ' Home'}
          </button>
          {/* Show upload file button for faculty only */}
          {user?.role === 'faculty' && (
            <button className="sidebar-button" onClick={() => setActiveTab('files')} title="Upload">
              <Upload size={18} />{sidebarOpen && ' Upload Files'}
            </button>
          )}
          {/* Show courses platform button */}
          {user?.role === 'faculty' && (
            <button className="sidebar-button" onClick={() => navigate('/courses/faculty')} title="Courses">
              <BookOpen size={18} />{sidebarOpen && ' My Courses'}
            </button>
          )}
          {user?.role === 'student' && (
            <button className="sidebar-button" onClick={() => navigate('/courses/student')} title="Courses">
              <BookOpen size={18} />{sidebarOpen && ' Courses'}
            </button>
          )}
          <button className="sidebar-button" onClick={exportChatAsPDF} title="Export as PDF">
            <FileText size={18} />{sidebarOpen && ' Export PDF'}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className={`chat-main ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        {/* Navigation Tabs */}
        <div className="chat-tabs">
          <button
            className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={16} /> Chat
          </button>
          <button
            className={`tab-button ${activeTab === 'files' ? 'active' : ''}`}
            onClick={() => setActiveTab('files')}
          >
            <File size={16} /> Files ({mergedPDFs.length})
          </button>
        </div>

        {/* Chat Tab Content */}
        {activeTab === 'chat' && (
          <div className="chat-content">
            {/* Messages Container */}
            <div className="messages-container">
              {messages.length === 0 ? (
                <div className="welcome-message">
                  <div className="welcome-icon"><MessageSquare size={48} /></div>
                  <h3>Welcome to MANAMU!</h3>
                  <p>I'm your AI assistant. How can I help you today?</p>
                  <p>Start by uploading some documents then ask me anything!</p>
                </div>
              ) : (
                messages.map((message) => (
                  <React.Fragment key={message.id}>
                    {/* User Message - Right Side - Separate Row */}
                    <div className="message">
                      <div className="message-user">
                        <div className="message-content">
                          <div className="message-text">{message.message}</div>
                          <div className="message-time">{formatDate(message.created_at)}</div>
                        </div>
                        <div className="message-avatar"><User size={20} /></div>
                      </div>
                    </div>

                    {/* Bot Message - Left Side - Separate Row */}
                    <div className="message">
                      <div className="message-bot">
                        <div className="message-avatar"><MessageSquare size={20} /></div>
                        <div className="message-content">
                          {message.loading && !message.response ? (
                            <div className="typing-indicator">
                              <span></span><span></span><span></span>
                            </div>
                          ) : (
                            <div className="message-text">
                              {message.response}
                              {loading && messages[messages.length - 1]?.id === message.id && message.response ? (
                                <span className="stream-cursor">▍</span>
                              ) : null}
                            </div>
                          )}
                          {message.context && settings.showContext && !message.loading && (
                            <details className="context-details">
                              <summary>
                                <BookOpen size={14} style={{ marginRight: '4px' }} /> View Sources
                                {message.context.used_web_search && (
                                  <span style={{ marginLeft: '8px', color: '#4caf50', fontWeight: 'bold' }}>
                                    <Globe size={14} style={{ marginRight: '4px' }} /> Web Search Used
                                  </span>
                                )}
                              </summary>
                              <div className="context-list">
                                {message.context.context && message.context.context.map((ctx, i) => (
                                  <div key={i} className="context-item">
                                    <p>{ctx}</p>
                                  </div>
                                ))}
                                {message.context.web_search_results && message.context.web_search_results.length > 0 && (
                                  <div className="context-item" style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #ddd' }}>
                                    <strong style={{ color: '#4caf50', display: 'flex', alignItems: 'center', gap: '4px' }}><Globe size={14} /> Web Search Results:</strong>
                                    {message.context.web_search_results.map((result, i) => (
                                      <div key={i} style={{ marginTop: '8px', padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                                        <strong>{result.title}</strong>
                                        <p style={{ margin: '4px 0', fontSize: '0.9em', color: '#666' }}>{result.snippet}</p>
                                        {result.url && (
                                          <a href={result.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.85em', color: '#2196f3' }}>
                                            View Source →
                                          </a>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </details>
                          )}
                          <div className="message-time">{formatDate(message.created_at)}</div>
                        </div>
                      </div>
                    </div>
                  </React.Fragment>
                ))
              )}
              {loading && messages.length > 0 && !messages[messages.length - 1]?.response && (
                <div className="message">
                  <div className="message-bot">
                    <div className="message-avatar"><MessageSquare size={20} /></div>
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        {/* Files Tab Content */}
        {activeTab === 'files' && (
          <div className="files-content">
            {/* Only show upload section for faculty */}
            {user.role === 'faculty' && (
              <div className="upload-section">
                <h3>Upload Knowledge Documents (PDF only) ({mergedPDFs.length})</h3>
                <div className="form-group" style={{ marginBottom: 16 }}>
                  <label>Target Roles</label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', margin: '8px 0' }}>
                    {roles.map(role => (
                      <button
                        type="button"
                        key={role.value}
                        className={`chunk-btn${targetRoles.includes(role.value) ? ' selected' : ''}`}
                        style={{
                          padding: '10px 18px',
                          borderRadius: '18px',
                          border: targetRoles.includes(role.value) ? '2px solid #2980b9' : '2px solid #bdc3c7',
                          background: targetRoles.includes(role.value) ? '#2980b9' : '#f5f5f5',
                          color: targetRoles.includes(role.value) ? '#fff' : '#222',
                          fontWeight: 600,
                          cursor: 'pointer',
                          outline: 'none',
                          transition: 'all 0.2s',
                        }}
                        onClick={() => {
                          const newRoles = targetRoles.includes(role.value)
                            ? targetRoles.filter(r => r !== role.value)
                            : [...targetRoles, role.value];
                          setTargetRoles(newRoles);
                          // Clear specialization if student role is removed
                          if (!newRoles.includes('student')) {
                            setSelectedSpecialization('');
                          }
                        }}
                      >
                        {role.label}
                      </button>
                    ))}
                  </div>
                  <small style={{ color: '#888', marginTop: 4, display: 'block' }}>
                    اختر فئة أو أكثر للملف (Select one or more target roles for the file)
                  </small>
                </div>
                {targetRoles.includes('student') && (
                  <div className="form-group" style={{ marginBottom: 16 }}>
                    <label>Specialization (Required for Students) *</label>
                    <select
                      value={selectedSpecialization}
                      onChange={(e) => setSelectedSpecialization(e.target.value)}
                      style={{
                        padding: '10px',
                        borderRadius: '8px',
                        border: '2px solid #bdc3c7',
                        fontSize: '16px',
                        width: '100%',
                        marginTop: '8px'
                      }}
                      required
                    >
                      <option value="">Select Specialization</option>
                      {specializations.map(spec => (
                        <option key={spec} value={spec}>{spec}</option>
                      ))}
                    </select>
                    <small style={{ color: '#888', marginTop: 4, display: 'block' }}>
                      Select the specialization for students who should have access to this file
                    </small>
                  </div>
                )}
                <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''} ${uploadingFile ? 'uploading' : ''}`} style={{ marginBottom: 16, position: 'relative' }}>
                  <input {...getInputProps()} disabled={uploadingFile} />
                  {uploadingFile ? (
                    <div className="upload-progress-overlay">
                      <Loader className="spin" size={40} />
                      <p>Uploading and indexing…</p>
                      <small>Please wait until indexing finishes. Chat will use this file immediately after.</small>
                    </div>
                  ) : isDragActive ? (
                    <p>Drop files here...</p>
                  ) : (
                    <p>Drag & drop files here, or click to select files</p>
                  )}
                </div>
              </div>
            )}
            {(uploadingFile || uploadingRagDoc) && (
              <div className="global-upload-overlay" aria-live="polite">
                <div className="global-upload-card">
                  <Loader className="spin" size={48} />
                  <h3>Processing document</h3>
                  <p>Uploading and indexing into the knowledge base…</p>
                  <small>Do not close this page until the spinner finishes.</small>
                </div>
              </div>
            )}
            <div className="files-list">
              <h3>Uploaded Documents ({mergedPDFs.length})</h3>
              {mergedPDFs.length === 0 ? (
                <p>No PDF files uploaded yet.</p>
              ) : (
                <div className="files-grid">
                  {mergedPDFs.map((file, idx) => (
                    <div key={file.id || file.name + idx} className="file-card">
                      <div className="file-info">
                        <strong>{file.name || file.original_filename}</strong>
                        {file.file_size && <p>Size: {formatFileSize(file.file_size || 0)}</p>}
                        {file.file_type && <p>Type: {file.file_type || 'Unknown'}</p>}
                        {file.specialization && <p style={{ color: '#2980b9', fontWeight: 600 }}>Specialization: {file.specialization}</p>}
                        {file.upload_time && <small>Uploaded: {formatDate(file.upload_time)}</small>}
                        <div style={{ marginTop: 8, display: 'flex', gap: '8px', alignItems: 'center' }}>
                          <span style={{
                            color: file.status === 'Success' ? '#27ae60' : file.status === 'Fail to upload' ? '#e74c3c' : '#f39c12',
                            fontWeight: 600,
                            fontSize: 13
                          }}>{file.status}</span>
                          {file.id && (
                            <button
                              onClick={() => fileAPI.downloadFile(file.id)}
                              style={{
                                padding: '6px 12px',
                                borderRadius: '6px',
                                border: '1px solid #2980b9',
                                background: '#2980b9',
                                color: '#fff',
                                cursor: 'pointer',
                                fontSize: '12px',
                                fontWeight: 600
                              }}
                              title="Download file"
                            >
                              <Download size={14} /> Download
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {mergedPDFs.length > 0 && (
                <div style={{ marginTop: 20, textAlign: 'center' }}>
                  {/* Removed Index Available Files button and description */}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Fixed Input Container */}
      <div className={`chat-input-container ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <form onSubmit={handleSendMessage} className="message-form">
          <div className="web-search-toggle-container">
            <button
              type="button"
              className={`web-search-toggle ${enableWebSearch ? 'active' : ''}`}
              onClick={() => setEnableWebSearch(!enableWebSearch)}
              title={enableWebSearch ? 'Disable web search' : 'Enable web search (searches web when internal knowledge is insufficient)'}
            >
              <Globe size={16} />
              <span>{enableWebSearch ? 'Web Search ON' : 'Web Search OFF'}</span>
            </button>
          </div>
          <div className="input-wrapper">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
              disabled={loading}
              className="message-input"
              rows="1"
            />
            <button
              type="submit"
              disabled={loading || !newMessage.trim()}
              className="send-button"
            >
              {loading ? <Loader className="spin" size={20} /> : <MessageSquare size={20} />}
            </button>
          </div>
          <div className="input-hint">
            {enableWebSearch && <span style={{ color: '#4caf50', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'center' }}><Globe size={12} /> Web Search Enabled: Will search web if answer not found in documents</span>}
            {!enableWebSearch && <span>Current settings: Temp {settings.temperature} | Top-K {settings.topK} | Output {settings.maxOutput === 'small' ? 'Small (0-50 words)' : settings.maxOutput === 'medium' ? 'Medium (50-100 words)' : settings.maxOutput === 'large' ? 'Long (100+ words)' : settings.maxOutput}</span>}
          </div>
        </form>
      </div>

    </div>
  );
};

export default Chat;