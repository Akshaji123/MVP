import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import Landing from './pages/Landing';
import Auth from './pages/Auth';
import AdminDashboard from './pages/AdminDashboard';
import CompanyDashboard from './pages/CompanyDashboard';
import RecruiterDashboard from './pages/RecruiterDashboard';
import CandidateDashboard from './pages/CandidateDashboard';
import JobDetails from './pages/JobDetails';
import Leaderboard from './pages/Leaderboard';
import EnterpriseAdmin from './pages/EnterpriseAdmin';
import Settings from './pages/Settings';
import DomainSettings from './pages/DomainSettings';
import GamificationDashboard from './pages/GamificationDashboard';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  const ProtectedRoute = ({ children, allowedRoles }) => {
    if (!user) return <Navigate to="/auth" />;
    if (allowedRoles && !allowedRoles.includes(user.role)) {
      return <Navigate to="/" />;
    }
    return children;
  };

  const getDashboard = () => {
    if (!user) return <Landing />;
    
    switch (user.role) {
      case 'admin':
        return <AdminDashboard user={user} onLogout={handleLogout} />;
      case 'company':
        return <CompanyDashboard user={user} onLogout={handleLogout} />;
      case 'recruiter':
        return <RecruiterDashboard user={user} onLogout={handleLogout} />;
      case 'candidate':
        return <CandidateDashboard user={user} onLogout={handleLogout} />;
      default:
        return <Landing />;
    }
  };

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={getDashboard()} />
          <Route path="/auth" element={user ? <Navigate to="/" /> : <Auth setUser={setUser} />} />
          <Route path="/jobs/:jobId" element={
            <ProtectedRoute>
              <JobDetails user={user} onLogout={handleLogout} />
            </ProtectedRoute>
          } />
          <Route path="/leaderboard" element={<Leaderboard user={user} onLogout={handleLogout} />} />
          <Route path="/enterprise-admin" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <EnterpriseAdmin user={user} onLogout={handleLogout} />
            </ProtectedRoute>
          } />
          <Route path="/domain-settings" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <DomainSettings user={user} onLogout={handleLogout} />
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <Settings user={user} onLogout={handleLogout} />
            </ProtectedRoute>
          } />
          <Route path="/gamification" element={
            <ProtectedRoute>
              <GamificationPage user={user} onLogout={handleLogout} />
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" expand={true} richColors />
    </div>
  );
}

export default App;