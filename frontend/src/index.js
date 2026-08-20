import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// إذا كنت تريد بدء قياس الأداء في تطبيقك، مرر دالة
// لتسجيل النتائج (مثال: reportWebVitals(console.log))
// أو أرسل إلى نقطة نهاية التحليلات. تعلم المزيد: https://bit.ly/CRA-vitals
reportWebVitals();
