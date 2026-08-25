// استيراد المكتبات المطلوبة لتطبيق React
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Chat from './pages/Chat';
import AdminConsole from './pages/AdminConsole';
import FacultyCourses from './pages/FacultyCourses';
import FacultyLearningPlatform from './pages/FacultyLearningPlatform';
import StudentCourses from './pages/StudentCourses';
import './App.css';

const homeForRole = (role) => {
  if (role === 'admin') return '/admin';
  return '/chat';
};

const ProtectedRoute = ({ children, adminOnly = false, blockAdmin = false }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== 'admin') return <Navigate to="/chat" replace />;
  if (blockAdmin && user.role === 'admin') return <Navigate to="/admin" replace />;
  return children;
};

const PublicRoute = ({ children }) => {
  const { user } = useAuth();
  if (user) return <Navigate to={homeForRole(user.role)} replace />;
  return children;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route
              path="/"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route path="/register" element={<Navigate to="/login" replace />} />
            <Route
              path="/admin"
              element={
                <ProtectedRoute adminOnly>
                  <AdminConsole />
                </ProtectedRoute>
              }
            />
            <Route
              path="/chat"
              element={
                <ProtectedRoute blockAdmin>
                  <Chat />
                </ProtectedRoute>
              }
            />
            <Route path="/upload-students" element={<Navigate to="/admin" replace />} />
            <Route path="/upload-faculty" element={<Navigate to="/admin" replace />} />
            <Route path="/upload-staff" element={<Navigate to="/admin" replace />} />
            <Route
              path="/courses/learning"
              element={
                <ProtectedRoute blockAdmin>
                  <FacultyLearningPlatform />
                </ProtectedRoute>
              }
            />
            <Route
              path="/courses/faculty"
              element={
                <ProtectedRoute blockAdmin>
                  <FacultyCourses />
                </ProtectedRoute>
              }
            />
            <Route
              path="/courses/student"
              element={
                <ProtectedRoute blockAdmin>
                  <StudentCourses />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
