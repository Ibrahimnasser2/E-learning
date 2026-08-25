import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { courseAPI } from '../services/api';
import {
  GraduationCap,
  BookOpen,
  CheckCircle,
  Plus,
  Layers,
} from 'lucide-react';
import './FacultyLearningPlatform.css';

/**
 * Faculty Learning Platform — official curriculum (منهج) only.
 * Flow: select level → add courses. Not related to Course Management.
 */
const FacultyLearningPlatform = () => {
  const navigate = useNavigate();
  const [levels, setLevels] = useState([]);
  const [level, setLevel] = useState('');
  const [catalog, setCatalog] = useState([]);
  const [mine, setMine] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const lv = await courseAPI.getCatalogLevels();
        setLevels(lv.levels || []);
        const existing = await courseAPI.getFacultyCurriculumCourses();
        setMine(existing.courses || []);
      } catch (e) {
        console.error(e);
        setMessage('Could not load curriculum catalog.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!level) {
      setCatalog([]);
      setSelected([]);
      return;
    }
    courseAPI.getCatalogCourses(level)
      .then((res) => setCatalog(res.courses || []))
      .catch(() => setCatalog([]));
    setSelected([]);
  }, [level]);

  const mineCodes = new Set(mine.map((c) => c.course_code).filter(Boolean));

  const toggleCode = (code) => {
    setSelected((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const addSelected = async () => {
    if (!level || selected.length === 0) return;
    try {
      setSaving(true);
      setMessage('');
      await courseAPI.addFacultyCurriculumCourses(level, selected);
      const existing = await courseAPI.getFacultyCurriculumCourses();
      setMine(existing.courses || []);
      setSelected([]);
      setMessage(`Added ${selected.length} course(s) to your Learning Platform.`);
    } catch (e) {
      setMessage(e.response?.data?.detail || 'Failed to add courses.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flp-page">
        <div className="flp-loading">Loading Learning Platform…</div>
      </div>
    );
  }

  return (
    <div className="flp-page">
      <div className="flp-container">
        <header className="flp-header">
          <div>
            <h1>
              <GraduationCap size={28} />
              Learning Platform
            </h1>
            <p>Official curriculum only — select a level, then add courses. Separate from Course Management.</p>
          </div>
          <div className="flp-header-actions">
            <button type="button" className="flp-btn ghost" onClick={() => navigate('/courses/faculty')}>
              Course Management
            </button>
            <button type="button" className="flp-btn ghost" onClick={() => navigate('/chat')}>
              Back to Chat
            </button>
          </div>
        </header>

        <section className="flp-step">
          <h2>
            <Layers size={18} />
            1. Select level
          </h2>
          <div className="flp-levels">
            {levels.map((lv) => (
              <button
                key={lv.id}
                type="button"
                className={`flp-level-chip ${level === lv.id ? 'active' : ''}`}
                onClick={() => setLevel(lv.id)}
              >
                {lv.label_ar || lv.label_en || `Level ${lv.id}`}
              </button>
            ))}
          </div>
        </section>

        <section className="flp-step">
          <h2>
            <BookOpen size={18} />
            2. Add courses
          </h2>
          {!level ? (
            <p className="flp-hint">Choose a level above to see official courses.</p>
          ) : catalog.length === 0 ? (
            <p className="flp-hint">No catalog courses for this level.</p>
          ) : (
            <>
              <div className="flp-catalog-grid">
                {catalog.map((c) => {
                  const already = mineCodes.has(c.code);
                  const checked = selected.includes(c.code);
                  return (
                    <label
                      key={c.code}
                      className={`flp-course-option ${already ? 'added' : ''} ${checked ? 'checked' : ''}`}
                    >
                      <input
                        type="checkbox"
                        disabled={already}
                        checked={already || checked}
                        onChange={() => toggleCode(c.code)}
                      />
                      <div>
                        <strong>{c.title}</strong>
                        <span>{c.code} · {c.credit_hours} ساعة</span>
                      </div>
                      {already && (
                        <span className="flp-added-pill">
                          <CheckCircle size={12} /> Added
                        </span>
                      )}
                    </label>
                  );
                })}
              </div>
              <button
                type="button"
                className="flp-btn primary"
                disabled={saving || selected.length === 0}
                onClick={addSelected}
              >
                <Plus size={16} />
                {saving ? 'Adding…' : `Add selected (${selected.length})`}
              </button>
            </>
          )}
          {message && <p className="flp-message">{message}</p>}
        </section>

        <section className="flp-step">
          <h2>Your curriculum courses ({mine.length})</h2>
          {mine.length === 0 ? (
            <p className="flp-hint">No curriculum courses yet. Select a level and add courses above.</p>
          ) : (
            <ul className="flp-mine-list">
              {mine.map((c) => (
                <li key={c.id}>
                  <BookOpen size={16} />
                  <span className="flp-mine-title">{c.title}</span>
                  <span className="flp-mine-meta">
                    {c.course_code} · مستوى {c.level}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <p className="flp-footnote">
            Students appear here after you use <strong>Upload Students</strong> (Excel: الرقم الجامعي · المستوى · المقررات).
            Course Management is a separate custom library and is not linked to these courses.
          </p>
        </section>
      </div>
    </div>
  );
};

export default FacultyLearningPlatform;
