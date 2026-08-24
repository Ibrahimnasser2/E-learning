import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { chatAPI, fileAPI, ragAPI, courseAPI } from '../services/api';
import { useDropzone } from 'react-dropzone';
import './Chat.css'; // Styles for chat interface
import { useNavigate, useSearchParams } from 'react-router-dom';
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
  File,
  Users,
  FileSpreadsheet
} from 'lucide-react';

const ROSTER_TEMPLATE_ROWS = [
  ['441234567', '101'],
  ['441234568', '101'],
  ['441234569', '102'],
];

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
  const [selectedCourseId, setSelectedCourseId] = useState('');
  const [myCourses, setMyCourses] = useState([]);
  const [rosterFile, setRosterFile] = useState(null);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [rosterResult, setRosterResult] = useState(null);
  const [rosterSectionNumber, setRosterSectionNumber] = useState('');
  const [rosterList, setRosterList] = useState([]);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

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
    setMessages([]);
    if (user) {
      loadChatHistory();
      loadFiles();
      loadMyCourses();
    }
  }, [user]);

  useEffect(() => {
    const cid = searchParams.get('courseId');
    if (cid) setSelectedCourseId(cid);
  }, [searchParams]);

  useEffect(() => {
    if (user?.role === 'faculty' && selectedCourseId) {
      loadCourseRoster(selectedCourseId);
    } else {
      setRosterList([]);
    }
  }, [user?.role, selectedCourseId]);

  const loadCourseRoster = async (courseId) => {
    try {
      const roster = await courseAPI.getCourseRoster(courseId);
      setRosterList(roster || []);
    } catch (e) {
      console.error('Error loading roster:', e);
      setRosterList([]);
    }
  };

  const downloadRosterTemplate = () => {
    const headers = ['الرقم الجامعي', 'رقم الشعبة'];
    const csv = [headers, ...ROSTER_TEMPLATE_ROWS]
      .map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'section-roster-template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRosterUpload = async () => {
    if (!selectedCourseId) {
      alert('Please select a course first.');
      return;
    }
    if (!rosterFile) {
      alert('Please choose an Excel file.');
      return;
    }
    setRosterLoading(true);
    setRosterResult(null);
    try {
      const res = await courseAPI.uploadCourseRoster(
        Number(selectedCourseId),
        rosterFile,
        rosterSectionNumber || null
      );
      setRosterResult(res);
      setRosterFile(null);
      await loadCourseRoster(selectedCourseId);
    } catch (e) {
      alert(e?.response?.data?.detail || 'Roster upload failed.');
    } finally {
      setRosterLoading(false);
    }
  };

  const loadMyCourses = async () => {
    try {
      if (user?.role === 'faculty') {
        const res = await courseAPI.getMyCourses();
        setMyCourses(res.courses || []);
      } else if (user?.role === 'student') {
        const res = await courseAPI.getMyEnrollments();
        setMyCourses((res || []).map((e) => e.course).filter(Boolean));
        if ((res || []).length === 1 && !selectedCourseId) {
          setSelectedCourseId(String(res[0].course_id));
        }
      }
    } catch (e) {
      console.error('Error loading courses:', e);
    }
  };

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
    if (user?.role === 'student' && !selectedCourseId) {
      alert('Please select a course before using the AI tutor.');
      return;
    }

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
        courseId: selectedCourseId ? Number(selectedCourseId) : null,
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
  const canUpload =
    user?.role === 'faculty' &&
    targetRoles.length > 0 &&
    (!targetRoles.includes('student') || !!selectedCourseId);

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    if (user.role === 'faculty' && targetRoles.length === 0) {
      alert('Please select at least one target role (Faculty and/or Students) before uploading.');
      return;
    }

    if (user.role === 'faculty' && targetRoles.includes('student') && !selectedCourseId) {
      alert('Please select a course when uploading materials for students.');
      return;
    }

    const course = myCourses.find((c) => String(c.id) === String(selectedCourseId));
    const specForUpload = course?.specialization || selectedSpecialization;

    const newUploads = acceptedFiles.map(file => ({
      id: `local-${file.name}-${Date.now()}`,
      name: file.name,
      status: 'Uploading & indexing...',
      error: null,
    }));
    setUploadingPDFs(prev => [...prev, ...newUploads]);
    setActiveTab('files');
    setUploadingFile(true);

    try {
      for (const file of acceptedFiles) {
        if (user.role !== 'faculty') continue;
        try {
          await fileAPI.uploadFile(
            file,
            targetRoles,
            specForUpload,
            targetRoles.includes('student') ? Number(selectedCourseId) : null
          );
          setUploadingPDFs(prev => prev.map(f =>
            f.name === file.name && f.status === 'Uploading & indexing...'
              ? { ...f, status: 'Success', error: null }
              : f
          ));
        } catch (error) {
          const msg = error.message || 'Upload/indexing failed';
          setUploadingPDFs(prev => prev.map(f =>
            f.name === file.name && f.status === 'Uploading & indexing...'
              ? { ...f, status: 'Indexing failed', error: msg }
              : f
          ));
          console.error('Error uploading file:', error);
        }
      }
      await loadFiles();
      await loadRagStats();
      setSelectedSpecialization('');
    } finally {
      setUploadingFile(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    disabled: !canUpload || uploadingFile,
    accept: {
      'application/pdf': ['.pdf']
    }
  });

  // رفع وثائق RAG
  const onRagDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;
    const newUploads = acceptedFiles.filter(f => f.name.toLowerCase().endsWith('.pdf')).map(file => ({
      id: `${file.name}-${Date.now()}`,
      name: file.name,
      status: 'Uploading & indexing...',
      error: null,
    }));
    setUploadingPDFs(prev => [...prev, ...newUploads]);
    setUploadingRagDoc(true);
    for (const file of acceptedFiles) {
      if (!file.name.toLowerCase().endsWith('.pdf')) continue;
      try {
        await ragAPI.uploadDocument(file, true);
        setUploadingPDFs(prev => prev.map(f => f.name === file.name && f.status === 'Uploading & indexing...' ? { ...f, status: 'Success', error: null } : f));
        await loadFiles();
        await loadRagStats();
      } catch (error) {
        setUploadingPDFs(prev => prev.map(f => f.name === file.name && f.status === 'Uploading & indexing...' ? { ...f, status: 'Indexing failed', error: error.message || 'Upload failed' } : f));
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
            <span className="username">
              مرحباً، {user?.display_name || user?.username}!
            </span>
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
            <button className="sidebar-button" onClick={() => setActiveTab('files')} title="Course setup">
              <Upload size={18} />{sidebarOpen && ' Course Setup'}
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
            <File size={16} /> Course Setup
          </button>
        </div>

        {/* Chat Tab Content */}
        {activeTab === 'chat' && (
          <div className="chat-content">
            {user?.role === 'student' && (
              <div className="course-context-bar">
                <label htmlFor="chat-course-select">AI Tutor course:</label>
                <select
                  id="chat-course-select"
                  value={selectedCourseId}
                  onChange={(e) => setSelectedCourseId(e.target.value)}
                  className="spec-select"
                >
                  <option value="">Select your course</option>
                  {myCourses.map((c) => (
                    <option key={c.id} value={c.id}>{c.title}</option>
                  ))}
                </select>
              </div>
            )}
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
            {user.role === 'faculty' && (
              <>
                <div className="roster-upload-panel">
                  <div className="roster-panel-head">
                    <Users size={22} />
                    <div>
                      <h3>Upload Section Students</h3>
                      <p>Excel with student IDs from the admin master list · ملف الطلاب</p>
                    </div>
                  </div>

                  <div className="roster-panel-body">
                    <div className="roster-field">
                      <label htmlFor="roster-course-select">Course *</label>
                      <select
                        id="roster-course-select"
                        className="spec-select"
                        value={selectedCourseId}
                        onChange={(e) => {
                          setSelectedCourseId(e.target.value);
                          setRosterResult(null);
                          const c = myCourses.find((x) => String(x.id) === e.target.value);
                          if (c) setSelectedSpecialization(c.specialization);
                        }}
                      >
                        <option value="">Select course</option>
                        {myCourses.map((c) => (
                          <option key={c.id} value={c.id}>{c.title}</option>
                        ))}
                      </select>
                      {myCourses.length === 0 && (
                        <small className="field-hint warn">
                          Create a course first from My Courses.
                        </small>
                      )}
                    </div>

                    <div className="roster-field">
                      <label htmlFor="roster-section">Default section (optional)</label>
                      <input
                        id="roster-section"
                        type="text"
                        className="spec-select"
                        value={rosterSectionNumber}
                        onChange={(e) => setRosterSectionNumber(e.target.value)}
                        placeholder="e.g. 101"
                      />
                    </div>

                    <div className="roster-example-mini">
                      <table>
                        <thead>
                          <tr>
                            <th>الرقم الجامعي</th>
                            <th>رقم الشعبة</th>
                          </tr>
                        </thead>
                        <tbody>
                          {ROSTER_TEMPLATE_ROWS.map((row, i) => (
                            <tr key={i}>
                              <td>{row[0]}</td>
                              <td>{row[1]}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="roster-actions">
                      <button type="button" className="roster-template-btn" onClick={downloadRosterTemplate}>
                        <FileSpreadsheet size={16} /> Download template
                      </button>
                      <label className="roster-file-picker">
                        <input
                          type="file"
                          accept=".xlsx,.xls"
                          onChange={(e) => {
                            setRosterFile(e.target.files?.[0] || null);
                            setRosterResult(null);
                          }}
                        />
                        {rosterFile ? rosterFile.name : 'Choose Excel file (.xlsx)'}
                      </label>
                      <button
                        type="button"
                        className="roster-upload-btn"
                        disabled={!rosterFile || !selectedCourseId || rosterLoading}
                        onClick={handleRosterUpload}
                      >
                        {rosterLoading ? 'Uploading…' : 'Upload & Link Students'}
                      </button>
                    </div>

                    {rosterResult && (
                      <div className="roster-result-box">
                        Linked <strong>{rosterResult.linked}</strong> · Skipped <strong>{rosterResult.skipped}</strong>
                        {rosterResult.errors?.length > 0 && (
                          <ul>
                            {rosterResult.errors.map((err, i) => (
                              <li key={i}>
                                Row {err.row}: {err.reason}
                                {err.university_id ? ` (${err.university_id})` : ''}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}

                    <div className="roster-enrolled">
                      <strong>Enrolled in this course: {rosterList.length}</strong>
                      {rosterList.length > 0 && (
                        <ul>
                          {rosterList.map((r) => (
                            <li key={r.id}>
                              {r.university_id || r.student_id} — {r.student_name || 'Student'}
                              {r.section_number ? ` · Section ${r.section_number}` : ''}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>

                <div className="upload-section">
                  <h3>Upload Course Materials</h3>
                  <p className="upload-subtitle">PDF files for the AI tutor · after linking students</p>

                <div className="upload-steps">
                  <div className={`upload-step ${targetRoles.length > 0 ? 'done' : 'current'}`}>
                    <span className="step-num">1</span>
                    <div className="step-body">
                      <label className="step-label">Who can access this file? *</label>
                      <div className="role-chips">
                        {roles.map(role => {
                          const selected = targetRoles.includes(role.value);
                          return (
                            <button
                              type="button"
                              key={role.value}
                              className={`role-chip ${selected ? 'selected' : ''}`}
                              onClick={() => {
                                const newRoles = selected
                                  ? targetRoles.filter(r => r !== role.value)
                                  : [...targetRoles, role.value];
                                setTargetRoles(newRoles);
                                if (!newRoles.includes('student')) {
                                  setSelectedSpecialization('');
                                }
                              }}
                            >
                              {role.label}
                            </button>
                          );
                        })}
                      </div>
                      {targetRoles.length === 0 && (
                        <small className="field-hint warn">Select Faculty and/or Students before uploading.</small>
                      )}
                    </div>
                  </div>

                  {targetRoles.includes('student') && (
                    <div className={`upload-step ${selectedCourseId ? 'done' : 'current'}`}>
                      <span className="step-num">2</span>
                      <div className="step-body">
                        <label className="step-label">Course *</label>
                        <select
                          className="spec-select"
                          value={selectedCourseId}
                          onChange={(e) => {
                            setSelectedCourseId(e.target.value);
                            const c = myCourses.find((x) => String(x.id) === e.target.value);
                            if (c) setSelectedSpecialization(c.specialization);
                          }}
                        >
                          <option value="">Select course</option>
                          {myCourses.map((c) => (
                            <option key={c.id} value={c.id}>{c.title}</option>
                          ))}
                        </select>
                        {!selectedCourseId && (
                          <small className="field-hint warn">Materials are indexed for enrolled students in this course only.</small>
                        )}
                      </div>
                    </div>
                  )}

                  <div className={`upload-step ${canUpload ? 'current' : 'locked'}`}>
                    <span className="step-num">{targetRoles.includes('student') ? '3' : '2'}</span>
                    <div className="step-body">
                      <label className="step-label">Upload PDF</label>
                      <div
                        {...getRootProps()}
                        className={`dropzone ${isDragActive ? 'active' : ''} ${!canUpload || uploadingFile ? 'disabled' : ''}`}
                      >
                        <input {...getInputProps()} />
                        <Upload size={28} className="dropzone-icon" />
                        {!canUpload ? (
                          <p>Complete the steps above to enable upload</p>
                        ) : isDragActive ? (
                          <p>Drop PDF here…</p>
                        ) : uploadingFile ? (
                          <p>Upload in progress — see status on each file below</p>
                        ) : (
                          <>
                            <p>Drag & drop PDF here, or click to browse</p>
                            <small>Ready to upload for: {targetRoles.join(', ')}</small>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
            <div className="files-list">
              <h3>Documents ({mergedPDFs.length})</h3>
              {mergedPDFs.length === 0 ? (
                <p className="empty-files">No PDF files uploaded yet.</p>
              ) : (
                <div className="files-list-rows">
                  {mergedPDFs.map((file, idx) => {
                    const isProcessing = file.status === 'Uploading & indexing...';
                    const isFailed = file.status === 'Indexing failed' || file.status === 'Fail to upload';
                    const isSuccess = file.status === 'Success' || (!file.status && file.id);
                    return (
                      <div
                        key={file.id || file.name + idx}
                        className={`file-row ${isProcessing ? 'is-processing' : ''} ${isFailed ? 'is-failed' : ''} ${isSuccess ? 'is-success' : ''}`}
                      >
                        <div className="file-row-icon">
                          {isProcessing ? <Loader className="spin" size={22} /> : <FileText size={22} />}
                        </div>
                        <div className="file-row-main">
                          <div className="file-row-title">{file.name || file.original_filename}</div>
                          <div className="file-row-meta">
                            {file.file_size ? <span>{formatFileSize(file.file_size)}</span> : null}
                            {file.specialization ? <span>{file.specialization}</span> : null}
                            {file.upload_time ? <span>{formatDate(file.upload_time)}</span> : null}
                          </div>
                          {isProcessing && (
                            <div className="file-progress" aria-hidden="true">
                              <div className="file-progress-bar" />
                            </div>
                          )}
                          {file.error && <p className="file-error-text">{file.error}</p>}
                        </div>
                        <div className="file-row-actions">
                          <span className={`status-pill ${isProcessing ? 'pending' : isFailed ? 'error' : 'ok'}`}>
                            {isProcessing ? 'Indexing' : isFailed ? 'Failed' : 'Ready'}
                          </span>
                          {file.id && !isProcessing && (
                            <button
                              type="button"
                              className="file-download-btn"
                              onClick={() => fileAPI.downloadFile(file.id)}
                              title="Download file"
                            >
                              <Download size={14} /> Download
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
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