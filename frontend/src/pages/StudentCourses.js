import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { courseAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  CheckCircle,
  Clock,
  ExternalLink,
  Search,
  Filter,
  Users,
  Globe,
  Lock,
  PlayCircle,
  GraduationCap
} from 'lucide-react';
import './StudentCourses.css';

const StudentCourses = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('available'); // 'available' or 'enrolled'
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSpecialization, setFilterSpecialization] = useState('All');

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

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load available courses
      const coursesResponse = await courseAPI.getMyCourses();
      setCourses(coursesResponse.courses || []);

      // Load enrollments only if user is a student
      if (user?.role === 'student') {
        try {
          const enrollmentsResponse = await courseAPI.getMyEnrollments();
          setEnrollments(enrollmentsResponse || []);
        } catch (enrollError) {
          console.warn('Could not load enrollments:', enrollError);
          setEnrollments([]);
        }
      } else {
        setEnrollments([]);
      }
    } catch (error) {
      console.error('Error loading courses:', error);
      // const errorMessage = error.response?.data?.detail || 'Failed to load courses. Please try again.';
      // alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleEnroll = async (courseId) => {
    try {
      await courseAPI.enrollInCourse(courseId);
      alert('Successfully enrolled in the course!');
      loadData();
      setActiveTab('enrolled');
    } catch (error) {
      console.error('Error enrolling:', error);
      const message = error.response?.data?.detail || 'Failed to enroll in course. Please try again.';
      alert(message);
    }
  };

  const getFilteredCourses = (courseList) => {
    let result = [...courseList];

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

    return result;
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner-large"></div>
        <p>Loading your learning path...</p>
      </div>
    );
  }

  const enrolledCourseIds = enrollments.map(e => e.course_id);
  const availableCoursesRaw = courses.filter(c => !enrolledCourseIds.includes(c.id));
  const enrolledCoursesRaw = enrollments.map(e => e.course).filter(Boolean);

  const availableCourses = getFilteredCourses(availableCoursesRaw);
  const enrolledCourses = getFilteredCourses(enrolledCoursesRaw);

  return (
    <div className="student-courses-page">
      <div className="page-container">
        <header className="page-header">
          <div className="header-content">
            <h1 className="page-title">
              <GraduationCap className="icon-lg" />
              <span>Learning Platform</span>
            </h1>
            <p className="page-subtitle">
              {user?.specialization
                ? `Recommended for ${user.specialization}`
                : 'Explore and master new skills'}
            </p>
          </div>
          <button className="btn btn-secondary" onClick={() => navigate('/chat')}>
            Back to Chat
          </button>
        </header>

        <div className="tabs-container">
          <div className="tabs-list">
            <button
              className={`tab-btn ${activeTab === 'available' ? 'active' : ''}`}
              onClick={() => setActiveTab('available')}
            >
              <BookOpen size={18} />
              Available Courses
              <span className="tab-count">{availableCoursesRaw.length}</span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'enrolled' ? 'active' : ''}`}
              onClick={() => setActiveTab('enrolled')}
            >
              <CheckCircle size={18} />
              My Enrollments
              <span className="tab-count">{enrolledCoursesRaw.length}</span>
            </button>
          </div>
        </div>

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

        {activeTab === 'available' && (
          <div className="courses-section">
            {availableCourses.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon-wrapper">
                  <BookOpen size={48} />
                </div>
                <h2>No courses found</h2>
                <p>Check back later for new learning opportunities</p>
              </div>
            ) : (
              <div className="courses-grid">
                {availableCourses.map((course) => (
                  <div key={course.id} className="course-card">
                    <div className="course-card-image">
                      {course.thumbnail_url ? (
                        <img 
                          src={course.thumbnail_url} 
                          alt={course.title}
                          loading="lazy"
                          onError={(e) => {
                            // Try fallback to hqdefault if maxresdefault fails
                            if (course.thumbnail_url.includes('maxresdefault')) {
                              const fallbackUrl = course.thumbnail_url.replace('maxresdefault.jpg', 'hqdefault.jpg');
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
                      ) : (
                        <div className="course-image-placeholder">
                          <BookOpen size={48} />
                        </div>
                      )}
                    </div>
                    <div className="course-card-header">
                      <div className="course-status">
                        <span className="type-badge">
                          {course.course_type === 'internal' ? <Lock size={12} /> : <Globe size={12} />}
                          {course.course_type === 'internal' ? 'Internal' : 'External'}
                        </span>
                      </div>
                    </div>

                    <div className="course-card-body">
                      <h3 className="course-title" title={course.title}>{course.title}</h3>
                      <p className="course-description">
                        {course.description || "No description provided."}
                      </p>

                      <div className="course-meta">
                        <div className="meta-item">
                          <span className="meta-label">Instructor</span>
                          <span className="meta-value">{course.faculty_name || 'Faculty'}</span>
                        </div>
                        <div className="meta-item">
                          <span className="meta-label">Specialization</span>
                          <span className="meta-value">{course.specialization}</span>
                        </div>
                      </div>
                    </div>

                    <div className="course-card-footer">
                      <div className="footer-actions">
                        {course.course_url && (
                          <a
                            href={course.course_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-ghost btn-sm"
                          >
                            <ExternalLink size={14} />
                            Preview
                          </a>
                        )}
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => handleEnroll(course.id)}
                        >
                          Enroll Now
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'enrolled' && (
          <div className="courses-section">
            {enrolledCourses.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon-wrapper">
                  <Clock size={48} />
                </div>
                <h2>No enrollments yet</h2>
                <p>Browse available courses to start learning</p>
                <button className="btn btn-primary" onClick={() => setActiveTab('available')}>
                  Browse Courses
                </button>
              </div>
            ) : (
              <div className="courses-grid">
                {enrolledCourses.map((course) => {
                  const enrollment = enrollments.find(e => e.course_id === course.id);
                  return (
                    <div key={course.id} className="course-card enrolled">
                      <div className="course-card-image">
                        {course.thumbnail_url ? (
                          <img 
                            src={course.thumbnail_url} 
                            alt={course.title}
                            loading="lazy"
                            onError={(e) => {
                              // Try fallback to hqdefault if maxresdefault fails
                              if (course.thumbnail_url.includes('maxresdefault')) {
                                const fallbackUrl = course.thumbnail_url.replace('maxresdefault.jpg', 'hqdefault.jpg');
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
                        ) : (
                          <div className="course-image-placeholder">
                            <BookOpen size={48} />
                          </div>
                        )}
                      </div>
                      <div className="course-card-header">
                        <div className="course-status">
                          <span className="status-badge active">
                            <CheckCircle size={12} />
                            Enrolled
                          </span>
                        </div>
                        <span className="enrollment-date">
                          {new Date(enrollment.enrolled_at).toLocaleDateString()}
                        </span>
                      </div>

                      <div className="course-card-body">
                        <h3 className="course-title" title={course.title}>{course.title}</h3>

                        {enrollment.progress > 0 && (
                          <div className="progress-container">
                            <div className="progress-info">
                              <span className="progress-label">Progress</span>
                              <span className="progress-percentage">{enrollment.progress}%</span>
                            </div>
                            <div className="progress-bar">
                              <div
                                className="progress-fill"
                                style={{ width: `${enrollment.progress}%` }}
                              ></div>
                            </div>
                          </div>
                        )}

                        <div className="course-meta">
                          <div className="meta-item">
                            <span className="meta-label">Instructor</span>
                            <span className="meta-value">{course.faculty_name || 'Faculty'}</span>
                          </div>
                        </div>
                      </div>

                      <div className="course-card-footer">
                        {course.course_url ? (
                          <a
                            href={course.course_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-primary btn-block"
                          >
                            <PlayCircle size={16} />
                            Continue Learning
                          </a>
                        ) : (
                          <button className="btn btn-secondary btn-block" disabled>
                            No Content Link
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentCourses;

