// استيراد المكتبات المطلوبة لصفحة التسجيل
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useForm } from 'react-hook-form';
import './Auth.css';

// مكون صفحة التسجيل
const Register = () => {
  // حالة التحميل أثناء عملية التسجيل
  const [loading, setLoading] = useState(false);
  // رسالة الخطأ في حالة فشل التسجيل
  const [error, setError] = useState('');
  // استخدام سياق المصادقة للحصول على دالة التسجيل
  const { register: registerUser } = useAuth();
  // دالة التنقل بين الصفحات
  const navigate = useNavigate();

  // إعداد نموذج التسجيل باستخدام react-hook-form
  const {
    register,  // دالة تسجيل حقول النموذج
    handleSubmit,  // دالة معالجة إرسال النموذج
    formState: { errors },  // أخطاء التحقق من صحة البيانات
    watch  // دالة مراقبة قيم الحقول
  } = useForm();

  // مراقبة قيمة كلمة المرور للتحقق من تطابقها
  const password = watch('password');

  const roles = [
    { value: 'faculty', label: 'أعضاء هيئة التدريس (Faculty)' },
    { value: 'student', label: 'الطلاب (Students)' },
  ];
  const [selectedRole, setSelectedRole] = useState('faculty');
  const [specialization, setSpecialization] = useState('');

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


  // دالة معالجة إرسال نموذج التسجيل
  const onSubmit = async (data) => {
    setLoading(true);
    setError('');

    // محاولة التسجيل باستخدام البيانات المدخلة
    const result = await registerUser(
      data.username,
      data.email,
      data.password,
      selectedRole,
      selectedRole === 'student' ? specialization : null
    );

    if (result.success) {
      // في حالة النجاح، الانتقال إلى صفحة تسجيل الدخول مع رسالة نجاح
      navigate('/login', {
        state: { message: 'Registration successful! Please log in.' }
      });
    } else {
      // في حالة الفشل، عرض رسالة الخطأ
      setError(result.error);
    }

    setLoading(false);
  };


  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* رأس صفحة التسجيل */}
        <div className="auth-header">
          <div className="auth-logo">
            <h1>MANAMU</h1>
            <span className="auth-subtitle">AI Assistant</span>
          </div>
        </div>
        <h2>Create Account</h2>
        <p className="auth-description">
          Join and start your AI journey
        </p>
        {/* عرض رسالة الخطأ إذا وجدت */}
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        {/* نموذج التسجيل */}
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
                },
                pattern: {
                  value: /^[a-zA-Z0-9_]+$/,
                  message: 'Username can only contain letters, numbers, and underscores'
                }
              })}
              className={errors.username ? 'error' : ''}
              placeholder="Choose a username"
            />
            {errors.username && (
              <span className="error-text">{errors.username.message}</span>
            )}
          </div>
          {/* حقل البريد الإلكتروني */}
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Invalid email address'
                }
              })}
              className={errors.email ? 'error' : ''}
              placeholder="Enter your email"
            />
            {errors.email && (
              <span className="error-text">{errors.email.message}</span>
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
              placeholder="Create a password"
            />
            {errors.password && (
              <span className="error-text">{errors.password.message}</span>
            )}
          </div>
          {/* حقل تأكيد كلمة المرور */}
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              {...register('confirmPassword', {
                required: 'Please confirm your password',
                validate: value => value === password || 'Passwords do not match'
              })}
              className={errors.confirmPassword ? 'error' : ''}
              placeholder="Confirm your password"
            />
            {errors.confirmPassword && (
              <span className="error-text">{errors.confirmPassword.message}</span>
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
          {/* حقل التخصص (للطلاب فقط) */}
          {selectedRole === 'student' && (
            <div className="form-group">
              <label htmlFor="specialization">التخصص (Specialization) *</label>
              <select
                id="specialization"
                value={specialization}
                onChange={e => setSpecialization(e.target.value)}
                className="role-select"
                style={{ padding: '12px', borderRadius: '10px', border: '2px solid #bdc3c7', fontSize: '16px' }}
                required
              >
                <option value="">اختر التخصص</option>
                {specializations.map(spec => (
                  <option key={spec} value={spec}>{spec}</option>
                ))}
              </select>
            </div>
          )}
          {/* زر إنشاء الحساب */}
          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
        {/* رابط تسجيل الدخول للمستخدمين الموجودين */}
        <div className="auth-footer">
          <p>
            Already have an account? <Link to="/login">Log in here</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register; 