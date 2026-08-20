// استيراد المكتبات المطلوبة لصفحة تسجيل الدخول
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useForm } from 'react-hook-form';
import './Auth.css';

// مكون صفحة تسجيل الدخول
const Login = () => {
  // حالة التحميل أثناء عملية تسجيل الدخول
  const [loading, setLoading] = useState(false);
  // رسالة الخطأ في حالة فشل تسجيل الدخول
  const [error, setError] = useState('');
  // استخدام سياق المصادقة للحصول على دالة تسجيل الدخول
  const { login } = useAuth();
  // دالة التنقل بين الصفحات
  const navigate = useNavigate();

  // إعداد نموذج تسجيل الدخول باستخدام react-hook-form
  const {
    register,  // دالة تسجيل حقول النموذج
    handleSubmit,  // دالة معالجة إرسال النموذج
    formState: { errors }  // أخطاء التحقق من صحة البيانات
  } = useForm();

  const roles = [
    { value: 'faculty', label: 'أعضاء هيئة التدريس (Faculty)' },
    { value: 'student', label: 'الطلاب (Students)' },
  ];
  const [selectedRole, setSelectedRole] = useState('faculty');

  // دالة معالجة إرسال نموذج تسجيل الدخول
  const onSubmit = async (data) => {
    setLoading(true);
    setError('');

    // محاولة تسجيل الدخول باستخدام البيانات المدخلة
    const result = await login(data.username, data.password, selectedRole);

    if (result.success) {
      // في حالة النجاح، الانتقال إلى صفحة المحادثة
      navigate('/chat');
    } else {
      // في حالة الفشل، عرض رسالة الخطأ
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="auth-container">
      <div className="auth-card">

        {/* رأس صفحة تسجيل الدخول */}
        <div className="auth-header">
          <div className="auth-logo">
            <h1>MANAMU</h1>
            <span className="auth-subtitle">AI Assistant</span>
          </div>
        </div>

        <h2>Welcome Back</h2>
        <p className="auth-description">Log in to continue to your AI assistant</p>

        {/* عرض رسالة الخطأ إذا وجدت */}
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* نموذج تسجيل الدخول */}
        <form onSubmit={handleSubmit(onSubmit)} className="auth-form">
          {/* حقل اسم المستخدم */}
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              {...register('username', {
                required: 'Username is required',
                minLength: {
                  value: 3,
                  message: 'Username must be at least 3 characters'
                }
              })}
              className={errors.username ? 'error' : ''}
              placeholder="Enter your username"
            />
            {errors.username && (
              <span className="error-text">{errors.username.message}</span>
            )}
          </div>

          {/* حقل كلمة المرور */}
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 6,
                  message: 'Password must be at least 6 characters'
                }
              })}
              className={errors.password ? 'error' : ''}
              placeholder="Enter your password"
            />
            {errors.password && (
              <span className="error-text">{errors.password.message}</span>
            )}
          </div>

          {/* حقل اختيار الدور */}
          <div className="form-group">
            <label htmlFor="role">Role</label>
            <select
              id="role"
              value={selectedRole}
              onChange={e => setSelectedRole(e.target.value)}
              className="role-select"
              style={{ padding: '12px', borderRadius: '10px', border: '2px solid #bdc3c7', fontSize: '16px' }}
            >
              {roles.map(role => (
                <option key={role.value} value={role.value}>{role.label}</option>
              ))}
            </select>
          </div>

          {/* زر تسجيل الدخول */}
          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        {/* رابط التسجيل للمستخدمين الجدد */}
        <div className="auth-footer">
          <p>
            Don't have an account? <Link to="/register">Create one here</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login; 