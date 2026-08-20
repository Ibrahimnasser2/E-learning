import React, { useState, useEffect, useRef } from 'react';
import { ragAPI } from '../services/api';
import './Chat.css';
import { useNavigate } from 'react-router-dom';
import {
  User,
  MessageSquare,
  Home,
  Globe,
  Loader,
  Hand,
  Menu,
  BookOpen
} from 'lucide-react';

const GeneralChat = () => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settings, setSettings] = useState({
    temperature: 0.7,
    maxOutput: 'medium',
    topK: 3,
    showContext: false,
    autoScroll: true
  });
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [enableWebSearch, setEnableWebSearch] = useState(false);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    if (settings.autoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, settings.autoScroll]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || loading) return;

    setLoading(true);
    const userMessage = newMessage;
    setNewMessage('');

    // Add user message immediately
    const tempId = Date.now();
    setMessages(prev => [
      ...prev,
      {
        id: tempId,
        message: userMessage,
        response: null,
        created_at: new Date().toISOString(),
        context: null,
        loading: true
      }
    ]);

    try {
      const response = await ragAPI.sendGeneralMessage(
        userMessage,
        settings.topK,
        settings.temperature,
        settings.maxOutput,
        enableWebSearch
      );

      // Replace the temporary message with the real response
      setMessages(prev => prev.map(m =>
        m.id === tempId
          ? { ...response, id: tempId, message: userMessage, loading: false }
          : m
      ));
    } catch (error) {
      let errorMsg = 'Error: Could not get response.';
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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? '' : date.toLocaleString();
  };

  return (
    <div className="chat-layout">
      {/* Fixed Header Container */}
      <header className="chat-header">
        <div className="header-left">
          <div className="header-title">
            <h1>MANAMU</h1>
            <span className="subtitle">AI Assistant</span>
          </div>
        </div>
        <div className="header-right">
          <div className="user-info">
            <span className="username">General Inquiry</span>
            <button onClick={() => navigate('/login')} className="logout-button">
              Login
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
          <button className="sidebar-button" onClick={() => window.location.reload()} title="Home">
            <Home size={18} />{sidebarOpen && ' Home'}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className={`chat-main ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <div className="chat-content">
          {/* Messages Container */}
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h3>Welcome to MANAMU! <Hand size={24} className="wave-icon" /></h3>
                <p>I'm your AI assistant. How can I help you today?</p>
                <p>Feel free to ask any general questions!</p>
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
                          <div className="message-text">{message.response}</div>
                        )}
                        {/* Show context sources if available and showContext is enabled */}
                        {message.context && settings.showContext && !message.loading && (
                          (() => { console.log('message.context:', message.context); console.log('message.context.context:', message.context && message.context.context); return null; })(),
                          <details className="context-details">
                            <summary><BookOpen size={14} style={{ marginRight: '4px' }} /> View Sources</summary>
                            <div className="context-list">
                              {Array.isArray(message.context.context) && message.context.context.map((ctx, i) => (
                                <div key={i} className="context-item">
                                  {typeof ctx === 'object' && ctx !== null ? (
                                    <p>
                                      <strong>File:</strong> {ctx.file_name || 'Unknown'}<br />
                                      <span>{ctx.text || ''}</span>
                                    </p>
                                  ) : (
                                    <p>{ctx}</p>
                                  )}
                                </div>
                              ))}
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
            {loading && (
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
      {settingsModalOpen && (
        <div className="modal-overlay" onClick={() => setSettingsModalOpen(false)}>
          <div className="modal settings-modal" onClick={e => e.stopPropagation()}>
            <h2>Settings</h2>
            <div className="setting-group">
              <label>Temperature: {settings.temperature}</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => setSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                className="setting-slider"
              />
            </div>
            <div className="setting-group">
              <label>Max Output Length:</label>
              <select
                value={settings.maxOutput}
                onChange={(e) => setSettings(prev => ({ ...prev, maxOutput: e.target.value }))}
                className="setting-select"
              >
                <option value="small">Small (0-50 words)</option>
                <option value="medium">Medium (50-100 words)</option>
                <option value="large">Long (100+ words)</option>
              </select>
            </div>
            <div className="setting-group">
              <label>Top K Results: {settings.topK}</label>
              <input
                type="range"
                min="1"
                max="10"
                step="1"
                value={settings.topK}
                onChange={(e) => setSettings(prev => ({ ...prev, topK: parseInt(e.target.value) }))}
                className="setting-slider"
              />
            </div>
            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.showContext}
                  onChange={(e) => setSettings(prev => ({ ...prev, showContext: e.target.checked }))}
                />
                Show Context
              </label>
            </div>
            <div className="setting-group">
              <label>
                <input
                  type="checkbox"
                  checked={settings.autoScroll}
                  onChange={(e) => setSettings(prev => ({ ...prev, autoScroll: e.target.checked }))}
                />
                Auto-scroll
              </label>
            </div>
            <button className="close-modal-btn" onClick={() => setSettingsModalOpen(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneralChat;
