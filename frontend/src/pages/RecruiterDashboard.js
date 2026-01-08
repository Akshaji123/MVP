import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { jobs as jobsAPI, resumes, referrals as referralsAPI, leaderboard as leaderboardAPI } from '../api/client';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Award, TrendingUp, Upload, Briefcase, DollarSign } from 'lucide-react';

const RecruiterDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [myResumes, setMyResumes] = useState([]);
  const [myReferrals, setMyReferrals] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [showReferral, setShowReferral] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [referralData, setReferralData] = useState({
    candidate_name: '',
    candidate_email: '',
    candidate_phone: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [jobsRes, resumesRes, referralsRes, leaderboardRes] = await Promise.all([
        jobsAPI.getAll({ status: 'active' }),
        resumes.getAll(),
        referralsAPI.getAll(),
        leaderboardAPI.get()
      ]);
      setJobs(jobsRes.data);
      setMyResumes(resumesRes.data);
      setMyReferrals(referralsRes.data);
      setLeaderboard(leaderboardRes.data);
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

  const handleCreateReferral = async (e) => {
    e.preventDefault();
    try {
      await referralsAPI.create({
        job_id: selectedJob,
        ...referralData
      });
      toast.success('Referral created successfully!');
      setShowReferral(false);
      setReferralData({ candidate_name: '', candidate_email: '', candidate_phone: '' });
      fetchData();
    } catch (error) {
      toast.error('Failed to create referral');
    }
  };

  const myStats = myReferrals.reduce((acc, ref) => {
    acc.total++;
    if (ref.status === 'hired') {
      acc.successful++;
      acc.earnings += ref.reward_amount;
    }
    return acc;
  }, { total: 0, successful: 0, earnings: 0 });

  const myRank = leaderboard.findIndex(entry => entry.user_id === user.id) + 1;

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
      <div className="space-y-8" data-testid="recruiter-dashboard">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2" style={{fontFamily: 'Outfit, sans-serif'}}>Recruiter Dashboard</h1>
          <p className="text-slate-600">Upload resumes, make referrals, and earn rewards</p>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { title: 'My Rank', value: `#${myRank || '-'}`, icon: <Award className="w-5 h-5" />, color: 'lime' },
            { title: 'Total Referrals', value: myStats.total, icon: <TrendingUp className="w-5 h-5" />, color: 'indigo' },
            { title: 'Successful', value: myStats.successful, icon: <Briefcase className="w-5 h-5" />, color: 'pink' },
            { title: 'Total Earnings', value: `₹${(myStats.earnings / 1000).toFixed(1)}k`, icon: <DollarSign className="w-5 h-5" />, color: 'lime' },
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

        {/* Actions */}
        <div className="flex gap-4">
          <Dialog open={showUpload} onOpenChange={setShowUpload}>
            <DialogTrigger asChild>
              <Button data-testid="upload-resume-btn" className="bg-indigo-700 hover:bg-indigo-800">
                <Upload className="w-4 h-4 mr-2" /> Upload Resume
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Upload Candidate Resume</DialogTitle>
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

          <Button data-testid="view-leaderboard-btn" variant="outline" onClick={() => navigate('/leaderboard')} className="border-slate-300">
            View Leaderboard
          </Button>
        </div>

        {/* Job Marketplace */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Active Job Openings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {jobs.map((job) => (
                <div key={job.id} data-testid={`job-${job.id}`} className="border border-slate-200 rounded-lg p-4 hover:bg-slate-50 cursor-pointer">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-lg">{job.title}</h3>
                      <p className="text-sm text-slate-600">{job.company_name}</p>
                    </div>
                    <span className="px-3 py-1 bg-lime-100 text-lime-700 rounded-full text-xs font-medium">
                      ₹5k Reward
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mb-3 line-clamp-2">{job.description}</p>
                  <div className="flex gap-2 mb-3">
                    <span className="px-2 py-1 bg-slate-100 rounded text-xs">{job.location}</span>
                    <span className="px-2 py-1 bg-slate-100 rounded text-xs">{job.experience_level}</span>
                  </div>
                  <Dialog open={showReferral && selectedJob === job.id} onOpenChange={(open) => {
                    setShowReferral(open);
                    if (open) setSelectedJob(job.id);
                  }}>
                    <DialogTrigger asChild>
                      <Button data-testid={`refer-btn-${job.id}`} size="sm" className="w-full bg-indigo-700 hover:bg-indigo-800" onClick={() => setSelectedJob(job.id)}>
                        Refer Candidate
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Refer Candidate for {job.title}</DialogTitle>
                      </DialogHeader>
                      <form onSubmit={handleCreateReferral} className="space-y-4 mt-4">
                        <div>
                          <Label htmlFor="candidate-name">Candidate Name</Label>
                          <Input
                            id="candidate-name"
                            data-testid="candidate-name-input"
                            value={referralData.candidate_name}
                            onChange={(e) => setReferralData({ ...referralData, candidate_name: e.target.value })}
                            required
                            className="mt-2"
                          />
                        </div>
                        <div>
                          <Label htmlFor="candidate-email">Candidate Email</Label>
                          <Input
                            id="candidate-email"
                            data-testid="candidate-email-input"
                            type="email"
                            value={referralData.candidate_email}
                            onChange={(e) => setReferralData({ ...referralData, candidate_email: e.target.value })}
                            required
                            className="mt-2"
                          />
                        </div>
                        <div>
                          <Label htmlFor="candidate-phone">Phone (Optional)</Label>
                          <Input
                            id="candidate-phone"
                            data-testid="candidate-phone-input"
                            value={referralData.candidate_phone}
                            onChange={(e) => setReferralData({ ...referralData, candidate_phone: e.target.value })}
                            className="mt-2"
                          />
                        </div>
                        <Button data-testid="submit-referral-btn" type="submit" className="w-full bg-indigo-700 hover:bg-indigo-800">
                          Submit Referral
                        </Button>
                      </form>
                    </DialogContent>
                  </Dialog>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* My Resumes */}
        {myResumes.length > 0 && (
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle>Uploaded Resumes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {myResumes.map((resume) => (
                  <div key={resume.id} data-testid={`resume-${resume.id}`} className="flex items-center justify-between p-4 border border-slate-200 rounded-lg">
                    <div>
                      <div className="font-medium">{resume.file_name}</div>
                      <div className="text-sm text-slate-600">Skills: {resume.skills.join(', ')}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold" style={{color: resume.overall_score >= 80 ? '#22c55e' : resume.overall_score >= 50 ? '#eab308' : '#ef4444'}}>
                        {resume.overall_score}
                      </div>
                      <div className="text-xs text-slate-600">AI Score</div>
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

export default RecruiterDashboard;