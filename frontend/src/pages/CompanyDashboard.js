import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { dashboard, jobs as jobsAPI, applications as applicationsAPI } from '../api/client';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Briefcase, FileText, Plus, TrendingUp } from 'lucide-react';

const CompanyDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateJob, setShowCreateJob] = useState(false);
  const [newJob, setNewJob] = useState({
    title: '',
    description: '',
    requirements: '',
    location: '',
    salary_range: '',
    experience_level: 'mid',
    employment_type: 'full-time'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, jobsRes, appsRes] = await Promise.all([
        dashboard.getStats(),
        jobsAPI.getAll(),
        applicationsAPI.getAll()
      ]);
      setStats(statsRes.data);
      setJobs(jobsRes.data);
      setApplications(appsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async (e) => {
    e.preventDefault();
    try {
      const jobData = {
        ...newJob,
        requirements: newJob.requirements.split(',').map(r => r.trim())
      };
      await jobsAPI.create(jobData);
      toast.success('Job posted successfully!');
      setShowCreateJob(false);
      fetchData();
    } catch (error) {
      toast.error('Failed to create job');
    }
  };

  const handleStatusChange = async (appId, newStatus) => {
    try {
      await applicationsAPI.updateStatus(appId, newStatus);
      toast.success('Status updated');
      fetchData();
    } catch (error) {
      toast.error('Failed to update status');
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
      <div className="space-y-8" data-testid="company-dashboard">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-2" style={{fontFamily: 'Outfit, sans-serif'}}>Company Dashboard</h1>
            <p className="text-slate-600">Manage your job postings and candidates</p>
          </div>
          <Dialog open={showCreateJob} onOpenChange={setShowCreateJob}>
            <DialogTrigger asChild>
              <Button data-testid="create-job-btn" className="bg-indigo-700 hover:bg-indigo-800">
                <Plus className="w-4 h-4 mr-2" /> Post Job
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Job Posting</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateJob} className="space-y-4 mt-4">
                <div>
                  <Label htmlFor="job-title">Job Title</Label>
                  <Input
                    id="job-title"
                    data-testid="job-title-input"
                    value={newJob.title}
                    onChange={(e) => setNewJob({ ...newJob, title: e.target.value })}
                    required
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="job-description">Description</Label>
                  <Textarea
                    id="job-description"
                    data-testid="job-description-input"
                    value={newJob.description}
                    onChange={(e) => setNewJob({ ...newJob, description: e.target.value })}
                    required
                    rows={4}
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="job-requirements">Requirements (comma-separated)</Label>
                  <Input
                    id="job-requirements"
                    data-testid="job-requirements-input"
                    value={newJob.requirements}
                    onChange={(e) => setNewJob({ ...newJob, requirements: e.target.value })}
                    placeholder="React, Node.js, 3+ years experience"
                    required
                    className="mt-2"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="job-location">Location</Label>
                    <Input
                      id="job-location"
                      data-testid="job-location-input"
                      value={newJob.location}
                      onChange={(e) => setNewJob({ ...newJob, location: e.target.value })}
                      required
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="job-salary">Salary Range</Label>
                    <Input
                      id="job-salary"
                      data-testid="job-salary-input"
                      value={newJob.salary_range}
                      onChange={(e) => setNewJob({ ...newJob, salary_range: e.target.value })}
                      placeholder="$80k - $120k"
                      required
                      className="mt-2"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="job-experience">Experience Level</Label>
                    <Select value={newJob.experience_level} onValueChange={(value) => setNewJob({ ...newJob, experience_level: value })}>
                      <SelectTrigger data-testid="job-experience-select" className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="entry">Entry Level</SelectItem>
                        <SelectItem value="mid">Mid Level</SelectItem>
                        <SelectItem value="senior">Senior Level</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="job-type">Employment Type</Label>
                    <Select value={newJob.employment_type} onValueChange={(value) => setNewJob({ ...newJob, employment_type: value })}>
                      <SelectTrigger data-testid="job-type-select" className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="full-time">Full Time</SelectItem>
                        <SelectItem value="part-time">Part Time</SelectItem>
                        <SelectItem value="contract">Contract</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button data-testid="submit-job-btn" type="submit" className="w-full bg-indigo-700 hover:bg-indigo-800">
                  Post Job
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { title: 'Total Jobs', value: stats?.total_jobs || 0, icon: <Briefcase className="w-5 h-5" /> },
            { title: 'Active Jobs', value: stats?.active_jobs || 0, icon: <TrendingUp className="w-5 h-5" /> },
            { title: 'Applications', value: stats?.total_applications || 0, icon: <FileText className="w-5 h-5" /> },
            { title: 'Pending Review', value: stats?.pending_applications || 0, icon: <FileText className="w-5 h-5" /> },
          ].map((stat, idx) => (
            <Card key={idx} data-testid={`stat-card-${idx}`} className="border-slate-200 hover-lift">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">{stat.title}</CardTitle>
                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-700">
                  {stat.icon}
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold" style={{fontFamily: 'Outfit, sans-serif'}}>{stat.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Recent Applications */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Recent Applications</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {applications.slice(0, 10).map((app) => (
                <div key={app.id} data-testid={`application-${app.id}`} className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50">
                  <div className="flex-1">
                    <div className="font-semibold">{app.candidate_name}</div>
                    <div className="text-sm text-slate-600">{app.job_title}</div>
                    <div className="text-xs text-slate-500 mt-1">{new Date(app.created_at).toLocaleDateString()}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-2xl font-bold" style={{color: app.match_score >= 80 ? '#22c55e' : app.match_score >= 50 ? '#eab308' : '#ef4444'}}>
                        {app.match_score}%
                      </div>
                      <div className="text-xs text-slate-600">Match Score</div>
                    </div>
                    <Select value={app.status} onValueChange={(value) => handleStatusChange(app.id, value)}>
                      <SelectTrigger data-testid={`status-select-${app.id}`} className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="reviewing">Reviewing</SelectItem>
                        <SelectItem value="shortlisted">Shortlisted</SelectItem>
                        <SelectItem value="rejected">Rejected</SelectItem>
                        <SelectItem value="hired">Hired</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              ))}
              {applications.length === 0 && (
                <div className="text-center py-12 text-slate-500">
                  No applications yet
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default CompanyDashboard;