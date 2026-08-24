import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../services/api';
import {
  Shield,
  GraduationCap,
  Users,
  Download,
  Upload,
  LogOut,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
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
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
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
        <div className="admin-header-inner">
          <div className="admin-brand">
            <div className="admin-brand-mark">
              <Shield size={28} strokeWidth={1.75} />
            </div>
            <div>
              <p className="admin-brand-tag">MANAMU · Administrative Portal</p>
              <h1>User Provisioning</h1>
              <p className="admin-subtitle">بوابة إدارة حسابات الطلاب وأعضاء هيئة التدريس</p>
            </div>
          </div>
          <div className="admin-header-actions">
            <span className="admin-user-badge">{user.email}</span>
            <button type="button" className="admin-btn admin-btn-outline" onClick={handleLogout}>
              <LogOut size={16} />
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="admin-main">
        <section className="admin-stats-row">
          <article className="stat-card stat-students">
            <div className="stat-icon-wrap">
              <GraduationCap size={22} />
            </div>
            <div className="stat-body">
              <span className="stat-label">Registered Students</span>
              <span className="stat-value">{summary?.students ?? 0}</span>
              <span className="stat-caption">الطلاب المسجلون</span>
            </div>
          </article>
          <article className="stat-card stat-faculty">
            <div className="stat-icon-wrap">
              <Users size={22} />
            </div>
            <div className="stat-body">
              <span className="stat-label">Faculty Members</span>
              <span className="stat-value">{summary?.faculty ?? 0}</span>
              <span className="stat-caption">أعضاء هيئة التدريس</span>
            </div>
          </article>
        </section>

        <section className="admin-panel">
          <div className="panel-head">
            <div>
              <h2>Excel User Import</h2>
              <p className="admin-panel-desc">
                Upload separate spreadsheets for students and faculty. Credentials are generated automatically.
              </p>
            </div>
          </div>

          <div className="example-grid">
            <article className="example-card example-students">
              <div className="example-card-head">
                <GraduationCap size={18} />
                <h3>Students File · ملف الطلاب</h3>
              </div>
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>الرقم الجامعي</th>
                      <th>الاسم</th>
                      <th>الهاتف</th>
                    </tr>
                  </thead>
                  <tbody>
                    {STUDENT_TEMPLATE_SAMPLE.map((row, i) => (
                      <tr key={i}>
                        {row.map((cell, j) => (
                          <td key={j}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="example-note">
                Email <code>{'{id}@student.kk.edu.sa'}</code> · Password <code>MANAMU</code> + last 4 digits
              </p>
              <button type="button" className="admin-btn admin-btn-template" onClick={downloadStudentTemplate}>
                <Download size={16} />
                Download Students Template
              </button>
            </article>

            <article className="example-card example-faculty">
              <div className="example-card-head">
                <Users size={18} />
                <h3>Faculty File · ملف المدرسين</h3>
              </div>
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>الاسم</th>
                      <th>البريد الجامعي</th>
                      <th>الهاتف</th>
                    </tr>
                  </thead>
                  <tbody>
                    {FACULTY_TEMPLATE_SAMPLE.map((row, i) => (
                      <tr key={i}>
                        {row.map((cell, j) => (
                          <td key={j}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="example-note">
                Login = email local-part · Password <code>MANAMU</code> + last 4 chars
              </p>
              <button type="button" className="admin-btn admin-btn-template" onClick={downloadFacultyTemplate}>
                <Download size={16} />
                Download Faculty Template
              </button>
            </article>
          </div>

          <div className="upload-section">
            <div className="upload-section-head">
              <FileSpreadsheet size={20} />
              <h3>Upload Excel File</h3>
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
                className="admin-file-input"
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  setError(null);
                }}
              />
              <label htmlFor="admin-file-input" className="admin-dropzone-label">
                <Upload size={32} strokeWidth={1.5} className="dropzone-icon" />
                {file ? (
                  <>
                    <strong>{file.name}</strong>
                    <span>{(file.size / 1024).toFixed(1)} KB · Ready to upload</span>
                  </>
                ) : (
                  <>
                    <strong>Drag & drop your Excel file here</strong>
                    <span>or click to browse · .xlsx / .xls</span>
                  </>
                )}
              </label>
            </div>

            <button
              type="button"
              className="admin-btn admin-btn-primary"
              disabled={loading || !file}
              onClick={handleUpload}
            >
              {loading ? 'Processing…' : 'Upload & Provision Users'}
            </button>
          </div>

          {error && (
            <div className="admin-alert admin-alert-error">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="admin-result">
              <div className="admin-result-head">
                <CheckCircle2 size={20} />
                <h3>Upload Complete</h3>
              </div>
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

      <footer className="admin-footer">
        <span>MANAMU E-Learning Platform · Administrative Access Only</span>
      </footer>
    </div>
  );
};

export default AdminConsole;
