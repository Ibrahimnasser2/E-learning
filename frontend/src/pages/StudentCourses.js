import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { courseAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Clock,
  Search,
  Filter,
  PlayCircle,
  GraduationCap,
  MessageSquare
} from 'lucide-react';
import './StudentCourses.css';

const StudentCourses = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
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
    } finally {
      setLoading(false);
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

  const enrolledCoursesRaw = enrollments.map(e => e.course).filter(Boolean);
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
              Courses assigned by your instructor — use the AI tutor from Chat
            </p>
          </div>
          <button className="btn btn-secondary" onClick={() => navigate('/chat')}>
            Back to Chat
          </button>
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


        <div className="courses-section">
            {enrolledCourses.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon-wrapper">
                  <Clock size={48} />
                </div>
                <h2>No courses yet</h2>
                <p>Your instructor will add you to a course section. Check back after they upload the roster.</p>
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
                        <button
                          className="btn btn-primary btn-block"
                          onClick={() => navigate(`/chat?courseId=${course.id}`)}
                        >
                          <MessageSquare size={16} />
                          Open AI Tutor
                        </button>
                        {course.course_url && (
                          <a
                            href={course.course_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-secondary btn-block"
                          >
                            <PlayCircle size={16} />
                            Course Link
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
        </div>
      </div>
    </div>
  );
};

export default StudentCourses;

