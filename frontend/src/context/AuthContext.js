// استيراد المكتبات المطلوبة لإدارة حالة المصادقة
import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../services/api';

// إنشاء سياق المصادقة
const AuthContext = createContext();

// دالة مخصصة لاستخدام سياق المصادقة
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// مزود سياق المصادقة - يدير حالة تسجيل الدخول للمستخدم
export const AuthProvider = ({ children }) => {
  // حالة المستخدم الحالي
  const [user, setUser] = useState(null);
  // رمز الوصول JWT - يتم استرجاعه من التخزين المحلي
  const [token, setToken] = useState(localStorage.getItem('token'));
  // حالة التحميل - تظهر أثناء التحقق من صحة الرمز
  const [loading, setLoading] = useState(true);

  // إعداد رؤوس axios الافتراضية عند تغيير الرمز
  useEffect(() => {
    if (token) {
      // إضافة رمز الوصول إلى رؤوس الطلبات
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      // إزالة رمز الوصول من رؤوس الطلبات
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // التحقق من صحة الرمز عند تحميل التطبيق
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          // التحقق من صحة الرمز مع الخادم
          const response = await axios.get(`${API_BASE_URL}/me`);
          setUser(response.data);
        } catch (error) {
          console.error('Authentication check failed:', error);
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [token]);

  // دالة تسجيل الدخول
  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/login`, {
        username,
        password,
      });
      
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      
      const userResponse = await axios.get(`${API_BASE_URL}/me`);
      setUser(userResponse.data);
      
      return { success: true, user: userResponse.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  // دالة التسجيل
  const register = async () => ({
    success: false,
    error: 'Registration is disabled. Contact your administrator.',
  });

  // دالة تسجيل الخروج
  const logout = () => {
    setUser(null);
    setToken(null);
    // إزالة الرمز من التخزين المحلي
    localStorage.removeItem('token');
    // إزالة الرمز من رؤوس axios
    delete axios.defaults.headers.common['Authorization'];
  };

  // القيم المقدمة من السياق
  const value = {
    user,  // بيانات المستخدم الحالي
    token,  // رمز الوصول
    loading,  // حالة التحميل
    login,  // دالة تسجيل الدخول
    register,  // دالة التسجيل
    logout,  // دالة تسجيل الخروج
    isAuthenticated: !!token  // حالة تسجيل الدخول (صحيح/خطأ)
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 