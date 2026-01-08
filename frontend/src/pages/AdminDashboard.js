import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { dashboard, users as usersAPI, jobs as jobsAPI, applications as applicationsAPI } from '../api/client';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Users, Briefcase, FileText, Building } from 'lucide-react';

const AdminDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, usersRes] = await Promise.all([
        dashboard.getStats(),
        usersAPI.getAll()
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-8" data-testid="admin-dashboard">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2" style={{fontFamily: 'Outfit, sans-serif'}}>Admin Dashboard</h1>
          <p className="text-slate-600">Platform overview and management</p>
        </div>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { title: 'Total Jobs', value: stats?.total_jobs || 0, icon: <Briefcase className="w-5 h-5" />, color: 'indigo' },
            { title: 'Total Applications', value: stats?.total_applications || 0, icon: <FileText className="w-5 h-5" />, color: 'lime' },
            { title: 'Companies', value: stats?.total_companies || 0, icon: <Building className="w-5 h-5" />, color: 'pink' },
            { title: 'Candidates', value: stats?.total_candidates || 0, icon: <Users className="w-5 h-5" />, color: 'indigo' },
          ].map((stat, idx) => (
            <Card key={idx} data-testid={`stat-card-${idx}`} className="border-slate-200 hover-lift">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">{stat.title}</CardTitle>
                <div className={`p-2 bg-${stat.color}-100 rounded-lg text-${stat.color}-700`}>
                  {stat.icon}
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold" style={{fontFamily: 'Outfit, sans-serif'}}>{stat.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Users Table */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Platform Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="users-table">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-600">Name</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-600">Email</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-600">Role</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-slate-600">Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 px-4">{u.full_name}</td>
                      <td className="py-3 px-4 text-slate-600">{u.email}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${
                          u.role === 'admin' ? 'bg-purple-100 text-purple-700' :
                          u.role === 'company' ? 'bg-indigo-100 text-indigo-700' :
                          u.role === 'recruiter' ? 'bg-lime-100 text-lime-700' :
                          'bg-pink-100 text-pink-700'
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 text-sm">{new Date(u.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default AdminDashboard;