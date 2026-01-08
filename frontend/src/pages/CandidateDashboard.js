import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { jobs as jobsAPI, resumes, applications as applicationsAPI, dashboard } from '../api/client';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Briefcase, FileText, Upload, TrendingUp, MapPin } from 'lucide-react';

const CandidateDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [myResumes, setMyResumes] = useState([]);
  const [myApplications, setMyApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, jobsRes, resumesRes, appsRes] = await Promise.all([
        dashboard.getStats(),
        jobsAPI.getAll({ status: 'active' }),
        resumes.getAll(),
        applicationsAPI.getAll()
      ]);
      setStats(statsRes.data);
      setJobs(jobsRes.data);
      setMyResumes(resumesRes.data);
      setMyApplications(appsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadResume = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    try {
      await resumes.upload(selectedFile);
      toast.success('Resume uploaded and analyzed!');
      setShowUpload(false);
      setSelectedFile(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to upload resume');
    }
  };

  const handleApply = async (jobId) => {
    if (myResumes.length === 0) {
      toast.error('Please upload a resume first');
      return;
    }

    try {
      await applicationsAPI.create({
        job_id: jobId,
        resume_id: myResumes[0].id
      });
      toast.success('Application submitted!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to apply');
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
      <div className="space-y-8" data-testid="candidate-dashboard">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2" style={{fontFamily: 'Outfit, sans-serif'}}>Candidate Dashboard</h1>
          <p className="text-slate-600">Find your dream job with AI-powered matching</p>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { title: 'Active Jobs', value: stats?.active_jobs || 0, icon: <Briefcase className="w-5 h-5" /> },
            { title: 'My Applications', value: stats?.total_applications || 0, icon: <FileText className="w-5 h-5" /> },
            { title: 'Resumes', value: myResumes.length, icon: <Upload className="w-5 h-5" /> },
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

        {/* Upload Resume */}
        {myResumes.length === 0 && (
          <Card className="border-lime-200 bg-lime-50">
            <CardContent className="pt-6">
              <div className="text-center">
                <Upload className="w-12 h-12 text-lime-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Upload Your Resume</h3>
                <p className="text-slate-600 mb-4">Get AI-powered analysis and start applying to jobs</p>
                <Dialog open={showUpload} onOpenChange={setShowUpload}>
                  <DialogTrigger asChild>
                    <Button data-testid="upload-resume-btn" className="bg-indigo-700 hover:bg-indigo-800">
                      Upload Resume
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Upload Your Resume</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleUploadResume} className="space-y-4 mt-4">
                      <div>
                        <Label htmlFor="resume-file">Resume File (PDF/DOCX)</Label>
                        <Input
                          id="resume-file"
                          data-testid="resume-file-input"
                          type="file"
                          accept=".pdf,.docx,.doc"
                          onChange={(e) => setSelectedFile(e.target.files[0])}
                          required
                          className="mt-2"
                        />
                      </div>
                      <Button data-testid="submit-resume-btn" type="submit" className="w-full bg-indigo-700 hover:bg-indigo-800" disabled={!selectedFile}>
                        Upload & Analyze
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Job Matches */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Recommended Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {jobs.slice(0, 10).map((job) => {
                const hasApplied = myApplications.some(app => app.job_id === job.id);
                return (
                  <div key={job.id} data-testid={`job-${job.id}`} className="border border-slate-200 rounded-lg p-6 hover:bg-slate-50">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="text-xl font-semibold mb-1">{job.title}</h3>
                        <p className="text-slate-600">{job.company_name}</p>
                      </div>
                      {hasApplied && (
                        <span className="px-3 py-1 bg-lime-100 text-lime-700 rounded-full text-sm font-medium">
                          Applied
                        </span>
                      )}
                    </div>
                    <p className="text-slate-600 mb-4 line-clamp-2">{job.description}</p>
                    <div className="flex gap-2 mb-4 flex-wrap">
                      <span className="px-3 py-1 bg-slate-100 rounded-full text-sm flex items-center gap-1">
                        <MapPin className="w-3 h-3" /> {job.location}
                      </span>
                      <span className="px-3 py-1 bg-slate-100 rounded-full text-sm">{job.experience_level}</span>
                      <span className="px-3 py-1 bg-slate-100 rounded-full text-sm">{job.employment_type}</span>
                      <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">{job.salary_range}</span>
                    </div>
                    <div className="flex gap-2">
                      <Button 
                        data-testid={`apply-btn-${job.id}`}
                        onClick={() => handleApply(job.id)} 
                        className="bg-indigo-700 hover:bg-indigo-800"
                        disabled={hasApplied}
                      >
                        {hasApplied ? 'Applied' : 'Apply Now'}
                      </Button>
                      <Button data-testid={`view-btn-${job.id}`} variant="outline" onClick={() => navigate(`/jobs/${job.id}`)} className="border-slate-300">
                        View Details
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* My Applications */}
        {myApplications.length > 0 && (
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle>My Applications</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {myApplications.map((app) => (
                  <div key={app.id} data-testid={`application-${app.id}`} className="flex items-center justify-between p-4 border border-slate-200 rounded-lg">
                    <div>
                      <div className="font-semibold">{app.job_title}</div>
                      <div className="text-sm text-slate-600">Applied {new Date(app.created_at).toLocaleDateString()}</div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-2xl font-bold" style={{color: app.match_score >= 80 ? '#22c55e' : app.match_score >= 50 ? '#eab308' : '#ef4444'}}>
                          {app.match_score}%
                        </div>
                        <div className="text-xs text-slate-600">Match</div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        app.status === 'hired' ? 'bg-lime-100 text-lime-700' :
                        app.status === 'shortlisted' ? 'bg-indigo-100 text-indigo-700' :
                        app.status === 'rejected' ? 'bg-red-100 text-red-700' :
                        'bg-slate-100 text-slate-700'
                      }`}>
                        {app.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

export default CandidateDashboard;