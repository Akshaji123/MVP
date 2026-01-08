import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Briefcase, LayoutDashboard, Users, Award, LogOut, Menu, Settings, Shield, Trophy, Building2, Calendar, DollarSign, MessageSquare } from 'lucide-react';
import { useState } from 'react';

const DashboardLayout = ({ user, onLogout, children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', path: '/', icon: <LayoutDashboard className="w-5 h-5" /> },
    { name: 'Leaderboard', path: '/leaderboard', icon: <Award className="w-5 h-5" /> },
    { name: 'Gamification', path: '/gamification', icon: <Trophy className="w-5 h-5" /> },
  ];

  // Add role-based navigation
  if (user.role === 'admin' || user.role === 'super_admin' || user.role === 'recruiter' || user.role === 'client') {
    navigation.push({ name: 'Candidates', path: '/candidates', icon: <Users className="w-5 h-5" /> });
  }
  
  if (user.role === 'admin' || user.role === 'super_admin' || user.role === 'recruiter' || user.role === 'client' || user.role === 'candidate') {
    navigation.push({ name: 'Interviews', path: '/interviews', icon: <Calendar className="w-5 h-5" /> });
  }

  // Financial and Messages for everyone
  navigation.push({ name: 'Financial', path: '/financial', icon: <DollarSign className="w-5 h-5" /> });
  navigation.push({ name: 'Messages', path: '/messages', icon: <MessageSquare className="w-5 h-5" /> });

  // Add Enterprise Admin for admin users
  if (user.role === 'admin' || user.role === 'super_admin') {
    navigation.push({ name: 'Companies', path: '/companies', icon: <Building2 className="w-5 h-5" /> });
    navigation.push({ name: 'Enterprise Admin', path: '/enterprise-admin', icon: <Settings className="w-5 h-5" /> });
    navigation.push({ name: 'Domain Settings', path: '/domain-settings', icon: <Shield className="w-5 h-5" /> });
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Nav */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
                <img 
                  src="https://customer-assets.emergentagent.com/job_talentsphere-4/artifacts/2at054ix_Flat%20New%20Orange%20logo%20Transparent.png" 
                  alt="Hiring Referrals Logo" 
                  className="h-10 w-auto"
                />
              </div>
              
              {/* Desktop Nav */}
              <div className="hidden md:flex items-center gap-4">
                {navigation.map((item) => (
                  <button
                    key={item.path}
                    data-testid={`nav-${item.name.toLowerCase()}`}
                    onClick={() => navigate(item.path)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      location.pathname === item.path
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {item.icon}
                    {item.name}
                  </button>
                ))}
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-4">
              <div className="hidden md:block text-right">
                <div className="text-sm font-medium">{user.full_name}</div>
                <div className="text-xs text-slate-600 capitalize">{user.role}</div>
              </div>
              <Button 
                data-testid="settings-btn"
                variant="outline" 
                size="sm" 
                onClick={() => navigate('/settings')}
                className="border-slate-300"
              >
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
              <Button data-testid="logout-btn" onClick={onLogout} variant="outline" size="sm" className="border-slate-300">
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
              <button className="md:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
                <Menu className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 border-t border-slate-200">
              {navigation.map((item) => (
                <button
                  key={item.path}
                  onClick={() => {
                    navigate(item.path);
                    setMobileMenuOpen(false);
                  }}
                  className={`flex items-center gap-2 w-full px-4 py-3 text-sm font-medium ${
                    location.pathname === item.path
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {item.icon}
                  {item.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  );
};

export default DashboardLayout;