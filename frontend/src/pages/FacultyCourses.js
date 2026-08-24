import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { courseAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Plus,
  Edit2,
  Trash2,
  ExternalLink,
  Search,
  Filter,
  MoreVertical,
  Users,
  Globe,
  Lock,
  Upload,
  FileSpreadsheet
} from 'lucide-react';
import './FacultyCourses.css';

const FacultyCourses = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [filteredCourses, setFilteredCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSpecialization, setFilterSpecialization] = useState('All');

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    specialization: '',
    course_url: '',
    course_type: 'internal',
    is_active: 'active',
    thumbnail_url: ''
  });

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

  const [isScraping, setIsScraping] = useState(false);
  const [scrapeTimeout, setScrapeTimeout] = useState(null);
  const [manageCourse, setManageCourse] = useState(null);
  const [rosterFile, setRosterFile] = useState(null);
  const [sectionNumber, setSectionNumber] = useState('');
  const [rosterLoading, setRosterLoading] = useState(false);
  const [rosterResult, setRosterResult] = useState(null);
  const [rosterList, setRosterList] = useState([]);

  // Extract YouTube thumbnail URL from YouTube video URL
  // Returns the main video thumbnail (not generic playlist thumbnail)
  const extractYouTubeThumbnail = (url) => {
    if (!url) return null;

    try {
      // Extract video ID from various YouTube URL formats
      // Important: Extract the specific video ID, not the playlist ID
      const patterns = [
        /[?&]v=([a-zA-Z0-9_-]{11})/,  // youtube.com/watch?v=VIDEO_ID
        /youtu\.be\/([a-zA-Z0-9_-]{11})/,  // youtu.be/VIDEO_ID
        /youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,  // youtube.com/embed/VIDEO_ID
        /youtube\.com\/v\/([a-zA-Z0-9_-]{11})/,  // youtube.com/v/VIDEO_ID
      ];

      let videoId = null;
      for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match && match[1]) {
          videoId = match[1];
          break;
        }
      }

      if (videoId) {
        // YouTube thumbnail URLs - maxresdefault is the main/highest quality image
        // This is the actual video thumbnail, not a generic one
        // Fallback chain: maxresdefault -> hqdefault -> mqdefault
        return `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
      }

      return null;
    } catch (error) {
      console.error('Error extracting YouTube thumbnail:', error);
      return null;
    }
  };

  // Handle URL change and auto-extract thumbnail/metadata
  const handleUrlChange = (url) => {
    // Update URL immediately
    setFormData(prev => ({
      ...prev,
      course_url: url
    }));

    // Clear previous timeout
    if (scrapeTimeout) clearTimeout(scrapeTimeout);

    if (!url) return;

    // 1. Fast local thumbnail extraction (immediate feedback)
    const localThumbnail = extractYouTubeThumbnail(url);
    if (localThumbnail) {
      setFormData(prev => ({ ...prev, thumbnail_url: localThumbnail }));
    }

    // 2. Server-side scraping for title and better thumbnail (debounced)
    const timeoutId = setTimeout(async () => {
      try {
        setIsScraping(true);
        const metadata = await courseAPI.scrapeMetadata(url);

        if (metadata) {
          setFormData(prev => ({
            ...prev,
            // Only auto-fill title if it's currently empty to avoid overwriting user edits
            title: (!prev.title && metadata.title) ? metadata.title : prev.title,
            // Always update thumbnail if we got a better one from server
            thumbnail_url: metadata.thumbnail_url || prev.thumbnail_url
          }));
        }
      } catch (error) {
        console.error("Error scraping metadata:", error);
      } finally {
        setIsScraping(false);
      }
    }, 800); // 800ms debounce

    setScrapeTimeout(timeoutId);
  };

  useEffect(() => {
    loadCourses();
  }, []);

  useEffect(() => {
    filterCourses();
  }, [searchQuery, filterSpecialization, courses]);

  const loadCourses = async () => {
    try {
      setLoading(true);
      const response = await courseAPI.getMyCourses();
      setCourses(response.courses || []);
    } catch (error) {
      console.error('Error loading courses:', error);
      // alert('Failed to load courses. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filterCourses = () => {
    let result = [...courses];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(course =>
        course.title.toLowerCase().includes(query) ||
        course.description?.toLowerCase().includes(query)
      );
    }

    if (filterSpecialization !== 'All') {
      result = result.filter(course => course.specialization === filterSpecialization);
    }

    setFilteredCourses(result);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCourse) {
        await courseAPI.updateCourse(editingCourse.id, formData);
      } else {
        await courseAPI.createCourse(formData);
      }
      setShowModal(false);
      setEditingCourse(null);
      resetForm();
      loadCourses();
    } catch (error) {
      console.error('Error saving course:', error);
      alert('Failed to save course. Please try again.');
    }
  };

  const handleEdit = (course) => {
    setEditingCourse(course);
    setFormData({
      title: course.title,
      description: course.description || '',
      specialization: course.specialization,
      course_url: course.course_url || '',
      course_type: course.course_type || 'internal',
      is_active: course.is_active || 'active',
      thumbnail_url: course.thumbnail_url || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (courseId) => {
    if (!window.confirm('Delete this course?')) return;
    try {
      await courseAPI.deleteCourse(courseId);
      loadCourses();
    } catch (error) {
      console.error('Error deleting course:', error);
      alert('Failed to delete course.');
    }
  };

  const openManageCourse = async (course) => {
    setManageCourse(course);
    setRosterFile(null);
    setRosterResult(null);
    setSectionNumber('');
    try {
      const roster = await courseAPI.getCourseRoster(course.id);
      setRosterList(roster || []);
    } catch (e) {
      setRosterList([]);
    }
  };

  const handleRosterUpload = async () => {
    if (!manageCourse || !rosterFile) return;
    setRosterLoading(true);
    setRosterResult(null);
    try {
      const res = await courseAPI.uploadCourseRoster(
        manageCourse.id,
        rosterFile,
        sectionNumber || null
      );
      setRosterResult(res);
      const roster = await courseAPI.getCourseRoster(manageCourse.id);
      setRosterList(roster || []);
      loadCourses();
    } catch (e) {
      alert(e?.response?.data?.detail || 'Roster upload failed');
    } finally {
      setRosterLoading(false);
    }
  };

  const downloadRosterTemplate = () => {
    const rows = [
      ['الرقم الجامعي', 'رقم الشعبة'],
      ['441234567', '101'],
      ['441234568', '101'],
      ['441234569', '102'],
    ];
    const csv = '\uFEFF' + rows.map((r) => r.map((c) => `"${c}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'section-roster-template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      specialization: '',
      course_url: '',
      course_type: 'internal',
      is_active: 'active',
      thumbnail_url: ''
    });
    setEditingCourse(null);
  };

  const openNewCourseModal = () => {
    resetForm();
    setShowModal(true);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner-large"></div>
        <p>Loading courses...</p>
      </div>
    );
  }

  return (
    <div className="faculty-courses-page">
      <div className="page-container">
        <header className="page-header">
          <div className="header-content">
            <h1 className="page-title">
              <BookOpen className="icon-lg" />
              <span>Course Management</span>
            </h1>
            <p className="page-subtitle">Create, manage and track your educational content</p>
          </div>
          <div className="header-actions">
            <button className="btn btn-secondary" onClick={() => navigate('/chat')}>
              Back to Chat
            </button>
            <button className="btn btn-primary" onClick={openNewCourseModal}>
              <Plus size={18} />
              Create Course
            </button>
          </div>
        </header>

        <div className="filters-bar">
          <div className="search-wrapper">
            <Search className="search-icon" size={18} />
            <input
              type="text"
              placeholder="Search courses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="filter-wrapper">
            <Filter className="filter-icon" size={18} />
            <select
              value={filterSpecialization}
              onChange={(e) => setFilterSpecialization(e.target.value)}
              className="filter-select"
            >
              <option value="All">All Specializations</option>
              {specializations.map(spec => (
                <option key={spec} value={spec}>{spec}</option>
              ))}
            </select>
          </div>
        </div>

        {filteredCourses.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon-wrapper">
              <BookOpen size={48} />
            </div>
            <h2>No courses found</h2>
            <p>
              {searchQuery || filterSpecialization !== 'All'
                ? "Try adjusting your search or filters"
                : "Start by creating your first course"}
            </p>
            {!searchQuery && filterSpecialization === 'All' && (
              <button className="btn btn-primary" onClick={openNewCourseModal}>
                <Plus size={18} />
                Create Course
              </button>
            )}
          </div>
        ) : (
          <div className="courses-grid">
            {filteredCourses.map((course) => (
              <div key={course.id} className="course-card">
                <div className="course-card-image">
                  {(() => {
                    // Use stored thumbnail, or extract from URL, or show placeholder
                    const thumbnailUrl = course.thumbnail_url ||
                      (course.course_url ? extractYouTubeThumbnail(course.course_url) : null);

                    if (thumbnailUrl) {
                      return (
                        <img
                          src={thumbnailUrl}
                          alt={course.title}
                          loading="lazy"
                          onError={(e) => {
                            // Try fallback to hqdefault if maxresdefault fails
                            if (thumbnailUrl.includes('maxresdefault')) {
                              const fallbackUrl = thumbnailUrl.replace('maxresdefault.jpg', 'hqdefault.jpg');
                              if (e.target.src !== fallbackUrl) {
                                e.target.src = fallbackUrl;
                              } else {
                                e.target.style.display = 'none';
                              }
                            } else {
                              e.target.style.display = 'none';
                            }
                          }}
                        />
                      );
                    }
                    return (
                      <div className="course-image-placeholder">
                        <BookOpen size={48} />
                      </div>
                    );
                  })()}
                </div>
                <div className="course-card-header">
                  <div className="course-status">
                    <span className={`status-badge ${course.is_active === 'active' ? 'active' : 'inactive'}`}>
                      {course.is_active === 'active' ? 'Active' : 'Inactive'}
                    </span>
                    <span className="type-badge">
                      {course.course_type === 'internal' ? <Lock size={12} /> : <Globe size={12} />}
                      {course.course_type === 'internal' ? 'Internal' : 'External'}
                    </span>
                  </div>
                  <div className="course-menu">
                    <button className="icon-btn" onClick={() => handleEdit(course)} title="Edit">
                      <Edit2 size={16} />
                    </button>
                    <button className="icon-btn danger" onClick={() => handleDelete(course.id)} title="Delete">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <div className="course-card-body">
                  <h3 className="course-title" title={course.title}>{course.title}</h3>
                  <p className="course-description">
                    {course.description || "No description provided."}
                  </p>

                  <div className="course-meta">
                    <div className="meta-item">
                      <span className="meta-label">Specialization</span>
                      <span className="meta-value">{course.specialization}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Students</span>
                      <span className="meta-value">
                        <Users size={14} />
                        {course.enrollment_count || 0}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="course-card-footer course-actions-row">
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    onClick={() => openManageCourse(course)}
                  >
                    <Users size={14} />
                    Section Roster
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={() => navigate(`/chat?courseId=${course.id}`)}
                  >
                    <Upload size={14} />
                    Upload Materials
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {manageCourse && (
          <div className="modal-overlay" onClick={() => setManageCourse(null)}>
            <div className="modal-content roster-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Section Roster — {manageCourse.title}</h2>
                <button className="modal-close" onClick={() => setManageCourse(null)}>×</button>
              </div>
              <p className="roster-help">
                Upload student university IDs already provisioned by the administrator.
                Each ID is validated against the master list — unknown IDs show{' '}
                <strong>Student ID not found</strong>. Section number is optional.
              </p>
              <div className="roster-format-box">
                <strong>Excel columns:</strong>
                <span>الرقم الجامعي</span>
                <span>رقم الشعبة (optional)</span>
              </div>
              <div className="form-group">
                <label>Default section number (optional)</label>
                <input
                  type="text"
                  value={sectionNumber}
                  onChange={(e) => setSectionNumber(e.target.value)}
                  placeholder="e.g. 101"
                />
              </div>
              <button type="button" className="btn btn-ghost btn-sm" onClick={downloadRosterTemplate}>
                <FileSpreadsheet size={14} /> Download template (CSV)
              </button>
              <div className="form-group">
                <label>Excel file (.xlsx)</label>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => setRosterFile(e.target.files?.[0] || null)}
                />
              </div>
              <button
                type="button"
                className="btn btn-primary"
                disabled={!rosterFile || rosterLoading}
                onClick={handleRosterUpload}
              >
                {rosterLoading ? 'Uploading…' : 'Upload & Link Students'}
              </button>
              {rosterResult && (
                <div className="roster-result">
                  <p>
                    Linked <strong>{rosterResult.linked}</strong> · Skipped <strong>{rosterResult.skipped}</strong>
                    {rosterResult.reindexed_students > 0 && (
                      <> · Re-indexed materials for <strong>{rosterResult.reindexed_students}</strong> students</>
                    )}
                  </p>
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
              <h3>Enrolled students ({rosterList.length})</h3>
              {rosterList.length === 0 ? (
                <p>No students linked yet.</p>
              ) : (
                <ul className="roster-list">
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
        )}

        {showModal && (
          <div className="modal-overlay" onClick={() => { setShowModal(false); resetForm(); }}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>{editingCourse ? 'Edit Course' : 'Create New Course'}</h2>
                <button className="modal-close" onClick={() => { setShowModal(false); resetForm(); }}>
                  ×
                </button>
              </div>

              <form onSubmit={handleSubmit} className="course-form">
                <div className="form-group">
                  <label htmlFor="title">Course Title *</label>
                  <input
                    type="text"
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                    placeholder="e.g., Advanced Machine Learning"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="description">Description</label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows="4"
                    placeholder="What will students learn in this course?"
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="specialization">Specialization *</label>
                    <select
                      id="specialization"
                      value={formData.specialization}
                      onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                      required
                    >
                      <option value="">Select Specialization</option>
                      {specializations.map((spec) => (
                        <option key={spec} value={spec}>{spec}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="course_type">Course Type</label>
                    <select
                      id="course_type"
                      value={formData.course_type}
                      onChange={(e) => setFormData({ ...formData, course_type: e.target.value })}
                    >
                      <option value="internal">Internal (University)</option>
                      <option value="external">External (Link)</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="course_url">Course URL</label>
                  <div className="input-with-icon">
                    <ExternalLink size={16} className="input-icon" />
                    <input
                      type="url"
                      id="course_url"
                      value={formData.course_url}
                      onChange={(e) => handleUrlChange(e.target.value)}
                      placeholder="https://www.youtube.com/watch?v=..."
                    />
                  </div>
                  {formData.thumbnail_url && (
                    <div className="thumbnail-preview">
                      <label>Course Thumbnail Preview:</label>
                      <img
                        src={formData.thumbnail_url}
                        alt="Course thumbnail"
                        className="thumbnail-preview-image"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                </div>

                {editingCourse && (
                  <div className="form-group">
                    <label htmlFor="is_active">Status</label>
                    <select
                      id="is_active"
                      value={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.value })}
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                )}

                <div className="form-actions">
                  <button type="button" className="btn btn-ghost" onClick={() => { setShowModal(false); resetForm(); }}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    {editingCourse ? 'Save Changes' : 'Create Course'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FacultyCourses;

