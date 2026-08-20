// استيراد المكتبات المطلوبة لتطبيق React
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Chat from './pages/Chat';
import StudentUpload from './pages/StudentUpload';
import FacultyUpload from './pages/FacultyUpload';
import StaffUpload from './pages/StaffUpload';
import FacultyCourses from './pages/FacultyCourses';
import StudentCourses from './pages/StudentCourses';
import './App.css';

// مكون المسار المحمي
// يتحقق من تسجيل دخول المستخدم قبل السماح بالوصول للصفحة
const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
};

// مكون المسار العام
// يعيد توجيه المستخدم إلى صفحة المحادثة إذا كان مسجل دخول بالفعل
const PublicRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? <Navigate to="/chat" replace /> : children;
};

// المكون الرئيسي للتطبيق
function App() {
  return (
    // مزود سياق المصادقة - يوفر حالة تسجيل الدخول لجميع المكونات الفرعية
    <AuthProvider>
      {/* موجه المتصفح - يدير التنقل بين الصفحات */}
      <Router>
        <div className="App">
          {/* تعريف المسارات المختلفة في التطبيق */}
          <Routes>
            {/* مسار الصفحة الرئيسية - صفحة تسجيل الدخول */}
            <Route 
              path="/" 
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              } 
            />
            {/* مسار صفحة تسجيل الدخول */}
            <Route 
              path="/login" 
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              } 
            />
            {/* مسار صفحة التسجيل */}
            <Route 
              path="/register" 
              element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              } 
            />
            {/* مسار صفحة المحادثة - محمي يتطلب تسجيل دخول */}
            <Route 
              path="/chat" 
              element={
                <ProtectedRoute>
                  <Chat />
                </ProtectedRoute>
              } 
            />
            {/* مسار رفع الطلاب من ملف إكسل - محمي للمسؤول فقط */}
            <Route 
              path="/upload-students" 
              element={
                <ProtectedRoute>
                  <StudentUpload />
                </ProtectedRoute>
              } 
            />
            {/* مسار رفع أعضاء هيئة التدريس من ملف إكسل - محمي للمسؤول فقط */}
            <Route 
              path="/upload-faculty" 
              element={
                <ProtectedRoute>
                  <FacultyUpload />
                </ProtectedRoute>
              } 
            />
            {/* مسار رفع الموظفين من ملف إكسل - محمي للمسؤول فقط */}
            <Route 
              path="/upload-staff" 
              element={
                <ProtectedRoute>
                  <StaffUpload />
                </ProtectedRoute>
              } 
            />
            {/* مسار إدارة الكورسات لأعضاء هيئة التدريس */}
            <Route 
              path="/courses/faculty" 
              element={
                <ProtectedRoute>
                  <FacultyCourses />
                </ProtectedRoute>
              } 
            />
            {/* مسار Dashboard الكورسات للطلاب */}
            <Route 
              path="/courses/student" 
              element={
                <ProtectedRoute>
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