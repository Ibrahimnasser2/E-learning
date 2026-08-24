import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../services/api';
import './AdminConsole.css';

const TEMPLATE_HEADERS = ['University ID', 'Name', 'Email', 'Specialization'];
const TEMPLATE_SAMPLE = [
  ['441234567', 'Ahmed Ali', '441234567@student.kk.edu.sa', 'Computer Science'],
  ['sara.hassan', 'Dr. Sara Hassan', 'sara.hassan@kk.edu.sa', ''],
];

const AdminConsole = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const loadSummary = useCallback(async () => {
    try {
      const data = await adminAPI.getSummary();
      setSummary(data);
    } catch (e) {
      console.error('Failed to load admin summary', e);
    }
  }, []);

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      navigate('/login', { replace: true });
      return;
    }
    loadSummary();
  }, [user, navigate, loadSummary]);

  const downloadTemplate = () => {
    const rows = [TEMPLATE_HEADERS, ...TEMPLATE_SAMPLE];
    const csv = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'manamu-users-template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select an Excel file.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await adminAPI.uploadUsersFile(file);
      setResult(res);
      await loadSummary();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user || user.role !== 'admin') {
    return null;
  }

  return (
    <div className="admin-console">
      <header className="admin-header">
        <div className="admin-brand">
          <h1>MANAMU Administration</h1>
          <p className="admin-subtitle">User Provisioning Portal</p>
        </div>
        <div className="admin-header-actions">
          <span className="admin-user-badge">{user.email}</span>
          <button type="button" className="admin-btn admin-btn-outline" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </header>

      <main className="admin-main">
        <section className="admin-stats">
          <div className="stat-card">
            <span className="stat-label">Total Users</span>
            <span className="stat-value">{summary?.total ?? '—'}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Students</span>
            <span className="stat-value">{summary?.students ?? '—'}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Faculty</span>
            <span className="stat-value">{summary?.faculty ?? '—'}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Administrators</span>
            <span className="stat-value">{summary?.admins ?? '—'}</span>
          </div>
        </section>

        <section className="admin-panel">
          <h2>Provision Users from Excel</h2>
          <p className="admin-panel-desc">
            Upload a spreadsheet to create student and faculty accounts. Role is detected automatically
            from the email domain — no Role column needed.
          </p>

          <div className="requirements-table-wrap">
            <table className="requirements-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Required</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Name</td>
                  <td>Yes</td>
                  <td>Full display name</td>
                </tr>
                <tr>
                  <td>Email</td>
                  <td>Yes*</td>
                  <td>
                    <code>{'{id}@student.kk.edu.sa'}</code> → Student ·{' '}
                    <code>{'{account}@kk.edu.sa'}</code> → Faculty
                  </td>
                </tr>
                <tr>
                  <td>University ID</td>
                  <td>Alt.</td>
                  <td>Student only — email auto-generated as <code>{'{id}@student.kk.edu.sa'}</code></td>
                </tr>
                <tr>
                  <td>Account</td>
                  <td>Alt.</td>
                  <td>Faculty only — email auto-generated as <code>{'{account}@kk.edu.sa'}</code></td>
                </tr>
                <tr>
                  <td>Specialization</td>
                  <td>Optional</td>
                  <td>For students only</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="password-note">
            Role is inferred from email — students use <strong>@student.kk.edu.sa</strong>, faculty use{' '}
            <strong>@kk.edu.sa</strong>. Initial password: <strong>MANAMU</strong> + last 4 characters of
            University ID / account (e.g. <code>441234567</code> → <code>MANAMU4567</code>).
          </p>

          <button type="button" className="admin-btn admin-btn-secondary" onClick={downloadTemplate}>
            Download Template (CSV)
          </button>

          <div
            className={`admin-dropzone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
            onDragEnter={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              const f = e.dataTransfer.files?.[0];
              if (f && /\.(xlsx|xls)$/i.test(f.name)) {
                setFile(f);
                setError(null);
              } else {
                setError('Please use .xlsx or .xls format.');
              }
            }}
          >
            <input
              type="file"
              accept=".xlsx,.xls"
              id="admin-file-input"
              style={{ display: 'none' }}
              onChange={(e) => {
                setFile(e.target.files?.[0] || null);
                setError(null);
              }}
            />
            <label htmlFor="admin-file-input" className="admin-dropzone-label">
              {file ? (
                <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
              ) : (
                <span>Drag & drop Excel file here, or click to browse</span>
              )}
            </label>
          </div>

          <button
            type="button"
            className="admin-btn admin-btn-primary"
            disabled={loading || !file}
            onClick={handleUpload}
          >
            {loading ? 'Uploading…' : 'Upload & Provision Users'}
          </button>

          {error && <div className="admin-alert admin-alert-error">{error}</div>}

          {result && (
            <div className="admin-result">
              <h3>Upload Results</h3>
              <p>
                <strong>{result.added}</strong> account(s) created ·{' '}
                <strong>{result.skipped}</strong> skipped (duplicates)
              </p>
              {result.errors?.length > 0 && (
                <ul className="admin-error-list">
                  {result.errors.map((err, i) => (
                    <li key={i}>
                      Row {err.row}: {err.reason}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default AdminConsole;
