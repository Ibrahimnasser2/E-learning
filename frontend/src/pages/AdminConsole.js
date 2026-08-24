import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../services/api';
import './AdminConsole.css';

const STUDENT_TEMPLATE_HEADERS = ['الرقم الجامعي', 'الاسم', 'الهاتف'];
const STUDENT_TEMPLATE_SAMPLE = [
  ['441234567', 'سارة محمد', '0501234567'],
  ['441234568', 'عمر خالد', '0507654321'],
];

const FACULTY_TEMPLATE_HEADERS = ['الاسم', 'البريد الجامعي', 'الهاتف'];
const FACULTY_TEMPLATE_SAMPLE = [
  ['د. أحمد علي', 'ahmed.ali@kk.edu.sa', '0501112233'],
  ['د. فاطمة حسن', 'fatima.hassan@kk.edu.sa', '0504445566'],
];

const downloadCsv = (headers, sample, filename) => {
  const rows = [headers, ...sample];
  const csv = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

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

  const downloadStudentTemplate = () => {
    downloadCsv(STUDENT_TEMPLATE_HEADERS, STUDENT_TEMPLATE_SAMPLE, 'students-template.csv');
  };

  const downloadFacultyTemplate = () => {
    downloadCsv(FACULTY_TEMPLATE_HEADERS, FACULTY_TEMPLATE_SAMPLE, 'faculty-template.csv');
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
            Upload two separate Excel files: one for students and one for faculty.
            Email and password are generated automatically for each file.
          </p>

          <div className="requirements-table-wrap">
            <table className="requirements-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Arabic</th>
                  <th>For</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>University ID</td>
                  <td>الرقم الجامعي</td>
                  <td>Students</td>
                  <td>Login username · email → <code>{'{id}@student.kk.edu.sa'}</code></td>
                </tr>
                <tr>
                  <td>Name</td>
                  <td>الاسم</td>
                  <td>All</td>
                  <td>Full display name</td>
                </tr>
                <tr>
                  <td>Phone</td>
                  <td>الهاتف</td>
                  <td>All</td>
                  <td>Contact number</td>
                </tr>
                <tr>
                  <td>University Email</td>
                  <td>البريد الجامعي</td>
                  <td>Faculty</td>
                  <td>Must be <code>@kk.edu.sa</code> · login = local-part before @</td>
                </tr>
                <tr>
                  <td>Specialization</td>
                  <td>التخصص</td>
                  <td>Students</td>
                  <td>Optional</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="password-note">
            <strong>Students:</strong> password <strong>MANAMU</strong> + last 4 digits of university ID.
            <strong> Faculty:</strong> password <strong>MANAMU</strong> + last 4 characters of email account
            (e.g. <code>ahmed.ali@kk.edu.sa</code> → <code>MANAMU.ali</code>).
          </p>

          <div className="admin-template-actions">
            <button type="button" className="admin-btn admin-btn-secondary" onClick={downloadStudentTemplate}>
              Download Students Template
            </button>
            <button type="button" className="admin-btn admin-btn-secondary" onClick={downloadFacultyTemplate}>
              Download Faculty Template
            </button>
          </div>

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
