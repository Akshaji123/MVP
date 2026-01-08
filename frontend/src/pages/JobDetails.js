import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { jobs as jobsAPI } from '../api/client';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { MapPin, Briefcase, DollarSign, Building, Clock } from 'lucide-react';

const JobDetails = ({ user, onLogout }) => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJob();
  }, [jobId]);

  const fetchJob = async () => {
    try {
      const response = await jobsAPI.getById(jobId);
      setJob(response.data);
    } catch (error) {
      toast.error('Failed to load job details');
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

  if (!job) {
    return (
      <DashboardLayout user={user} onLogout={onLogout}>
        <div className="text-center py-12">
          <p className="text-slate-600 mb-4">Job not found</p>
          <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-8" data-testid="job-details">
        <Button data-testid="back-btn" variant="ghost" onClick={() => navigate('/')} className="text-slate-600">
          ← Back
        </Button>

        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-3xl mb-3" style={{fontFamily: 'Outfit, sans-serif'}}>{job.title}</CardTitle>
                <div className="flex items-center gap-4 text-slate-600">
                  <span className="flex items-center gap-1">
                    <Building className="w-4 h-4" />
                    {job.company_name}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    {job.location}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {new Date(job.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <span className={`px-4 py-2 rounded-lg text-sm font-medium ${
                job.status === 'active' ? 'bg-lime-100 text-lime-700' : 'bg-slate-100 text-slate-700'
              }`}>
                {job.status}
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex gap-3 flex-wrap">
              <span className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg font-medium flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                {job.salary_range}
              </span>
              <span className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg">{job.experience_level}</span>
              <span className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg">{job.employment_type}</span>
            </div>

            <div>
              <h3 className="text-xl font-semibold mb-3" style={{fontFamily: 'Outfit, sans-serif'}}>Job Description</h3>
              <p className="text-slate-600 leading-relaxed whitespace-pre-wrap">{job.description}</p>
            </div>

            <div>
              <h3 className="text-xl font-semibold mb-3" style={{fontFamily: 'Outfit, sans-serif'}}>Requirements</h3>
              <ul className="space-y-2">
                {job.requirements.map((req, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-slate-600">
                    <span className="text-lime-500 mt-1">•</span>
                    <span>{req}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex gap-3 pt-4">
              <Button data-testid="apply-job-btn" className="bg-indigo-700 hover:bg-indigo-800">
                Apply Now
              </Button>
              <Button data-testid="refer-job-btn" variant="outline" className="border-slate-300">
                Refer Someone
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Application Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <div className="text-4xl font-bold mb-2" style={{fontFamily: 'Outfit, sans-serif'}}>{job.applications_count}</div>
                <div className="text-slate-600">Total Applications</div>
              </div>
              <div>
                <div className="text-4xl font-bold mb-2 text-lime-600" style={{fontFamily: 'Outfit, sans-serif'}}>₹5,000</div>
                <div className="text-slate-600">Referral Reward</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default JobDetails;