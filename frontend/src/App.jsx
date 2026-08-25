import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { DashboardPage } from './pages/DashboardPage';
import { AISpatialPage } from './pages/AISpatialPage';
import { ReviewValidationPage } from './pages/ReviewValidationPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { HistoryPage } from './pages/HistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { CommandCenterLayout } from './components/layout/CommandCenterLayout';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-gov-bg flex items-center justify-center text-white text-xs">
        Loading CadastralMap Session...
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          <Route path="/dashboard" element={<ProtectedRoute><CommandCenterLayout page={DashboardPage} /></ProtectedRoute>} />
          <Route path="/ai-analysis" element={<ProtectedRoute><CommandCenterLayout page={AISpatialPage} /></ProtectedRoute>} />
          <Route path="/review" element={<ProtectedRoute><CommandCenterLayout page={ReviewValidationPage} /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><CommandCenterLayout page={AnalyticsPage} /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><CommandCenterLayout page={HistoryPage} /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><CommandCenterLayout page={ReportsPage} /></ProtectedRoute>} />

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
