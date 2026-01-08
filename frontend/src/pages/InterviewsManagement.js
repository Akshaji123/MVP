import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Calendar, Clock, Video, MapPin, Users, Plus, X, Star, MessageSquare, Check } from 'lucide-react';
import apiClient from '../api/client';
import { toast } from 'sonner';

const InterviewsManagement = ({ user, onLogout }) => {
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedInterview, setSelectedInterview] = useState(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [calendarView, setCalendarView] = useState(null);
  const [feedbackForm, setFeedbackForm] = useState({
    rating: 5,
    technical_score: 5,
    communication_score: 5,
    problem_solving_score: 5,
    cultural_fit_score: 5,
    strengths: '',
    areas_of_improvement: '',
    comments: '',
    recommendation: 'proceed'
  });

  useEffect(() => {
    fetchInterviews();
    fetchCalendar();
  }, []);

  const fetchInterviews = async () => {
    try {
      const response = await apiClient.get('/interviews');
      setInterviews(response.data);
    } catch (error) {
      toast.error('Failed to fetch interviews');
    } finally {
      setLoading(false);
    }
  };

  const fetchCalendar = async () => {
    try {
      const response = await apiClient.get('/interviews/calendar/upcoming', { params: { days: 7 } });
      setCalendarView(response.data);
    } catch (error) {
      console.error('Failed to fetch calendar');
    }
  };

  const handleSubmitFeedback = async () => {
    if (!selectedInterview) return;
    try {
      const payload = {
        ...feedbackForm,
        strengths: feedbackForm.strengths.split(',').map(s => s.trim()).filter(Boolean),
        areas_of_improvement: feedbackForm.areas_of_improvement.split(',').map(s => s.trim()).filter(Boolean)
      };
      await apiClient.post(`/interviews/${selectedInterview.id}/feedback`, payload);
      toast.success('Feedback submitted successfully');
      setShowFeedbackModal(false);
      setSelectedInterview(null);
      fetchInterviews();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit feedback');
    }
  };

  const handleCancelInterview = async (interviewId, reason) => {
    try {
      await apiClient.post(`/interviews/${interviewId}/cancel`, null, { params: { reason } });
      toast.success('Interview cancelled');
      fetchInterviews();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to cancel interview');
    }
  };

  const statusColors = {
    'scheduled': 'bg-blue-100 text-blue-700',
    'completed': 'bg-green-100 text-green-700',
    'cancelled': 'bg-red-100 text-red-700',
    'rescheduled': 'bg-yellow-100 text-yellow-700',
    'no_show': 'bg-slate-100 text-slate-700'
  };

  const typeIcons = {
    'phone': '📞',
    'video': '🎥',
    'onsite': '🏢',
    'technical': '💻',
    'hr': '👔',
    'panel': '👥',
    'case_study': '📊'
  };

  const formatDateTime = (dateStr) => {
    const date = new Date(dateStr);
    return {
      date: date.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' }),
      time: date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    };
  };

  const upcomingInterviews = interviews.filter(i => i.interview_status === 'scheduled' && new Date(i.scheduled_at) > new Date());
  const pastInterviews = interviews.filter(i => i.interview_status !== 'scheduled' || new Date(i.scheduled_at) <= new Date());

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Interviews</h1>
            <p className="text-slate-600">Manage interview schedules and feedback</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Calendar className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{upcomingInterviews.length}</div>
                  <div className="text-sm text-slate-600">Upcoming</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Check className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{interviews.filter(i => i.interview_status === 'completed').length}</div>
                  <div className="text-sm text-slate-600">Completed</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Video className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{interviews.filter(i => i.interview_type === 'video').length}</div>
                  <div className="text-sm text-slate-600">Video Calls</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Star className="w-5 h-5 text-yellow-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">
                    {interviews.filter(i => i.rating).length > 0 
                      ? (interviews.filter(i => i.rating).reduce((sum, i) => sum + i.rating, 0) / interviews.filter(i => i.rating).length).toFixed(1)
                      : '-'}
                  </div>
                  <div className="text-sm text-slate-600">Avg Rating</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Calendar View */}
        {calendarView && Object.keys(calendarView.calendar).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">This Week</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-7 gap-2">
                {Object.entries(calendarView.calendar).map(([date, items]) => (
                  <div key={date} className="p-2 bg-slate-50 rounded-lg">
                    <div className="text-xs font-medium text-slate-600 mb-1">{date}</div>
                    <div className="text-lg font-bold text-indigo-600">{items.length}</div>
                    <div className="text-xs text-slate-500">interviews</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Interviews List */}
        {loading ? (
          <div className="text-center py-12">Loading interviews...</div>
        ) : interviews.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No interviews scheduled</h3>
              <p className="text-slate-600">Interviews will appear here when scheduled</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Upcoming */}
            {upcomingInterviews.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Upcoming Interviews</h3>
                <div className="space-y-3">
                  {upcomingInterviews.map((interview) => {
                    const { date, time } = formatDateTime(interview.scheduled_at);
                    return (
                      <Card key={interview.id} className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4">
                          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex items-start gap-4">
                              <div className="text-3xl">{typeIcons[interview.interview_type] || '📅'}</div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <h4 className="font-semibold">Round {interview.interview_round}</h4>
                                  <Badge className={statusColors[interview.interview_status]}>
                                    {interview.interview_status}
                                  </Badge>
                                  <Badge variant="outline" className="capitalize">{interview.interview_type}</Badge>
                                </div>
                                <p className="text-sm text-slate-600 mt-1">Application ID: {interview.application_id.slice(0, 8)}...</p>
                                {interview.interviewer_names?.length > 0 && (
                                  <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
                                    <Users className="w-3 h-3" /> {interview.interviewer_names.join(', ')}
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                              <div className="text-right">
                                <div className="font-semibold">{date}</div>
                                <div className="text-sm text-slate-600 flex items-center gap-1">
                                  <Clock className="w-3 h-3" /> {time} ({interview.duration_minutes} min)
                                </div>
                              </div>
                              <div className="flex gap-2">
                                {interview.meeting_link && (
                                  <Button size="sm" className="bg-green-600 hover:bg-green-700" asChild>
                                    <a href={interview.meeting_link} target="_blank" rel="noopener noreferrer">
                                      <Video className="w-4 h-4 mr-1" /> Join
                                    </a>
                                  </Button>
                                )}
                                <Button size="sm" variant="outline" onClick={() => handleCancelInterview(interview.id, 'Cancelled by user')}>
                                  Cancel
                                </Button>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Past */}
            {pastInterviews.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3">Past Interviews</h3>
                <div className="space-y-3">
                  {pastInterviews.slice(0, 10).map((interview) => {
                    const { date, time } = formatDateTime(interview.scheduled_at);
                    return (
                      <Card key={interview.id} className="bg-slate-50">
                        <CardContent className="p-4">
                          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex items-start gap-4">
                              <div className="text-3xl opacity-50">{typeIcons[interview.interview_type] || '📅'}</div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <h4 className="font-semibold">Round {interview.interview_round}</h4>
                                  <Badge className={statusColors[interview.interview_status]}>
                                    {interview.interview_status}
                                  </Badge>
                                </div>
                                <p className="text-sm text-slate-600 mt-1">{date} at {time}</p>
                                {interview.rating && (
                                  <div className="flex items-center gap-1 mt-1">
                                    <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                                    <span className="font-medium">{interview.rating}/10</span>
                                    {interview.recommendation && (
                                      <Badge variant="outline" className="ml-2 capitalize">{interview.recommendation}</Badge>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div>
                              {interview.interview_status === 'completed' && !interview.rating && (
                                <Button size="sm" onClick={() => { setSelectedInterview(interview); setShowFeedbackModal(true); }}>
                                  <MessageSquare className="w-4 h-4 mr-1" /> Add Feedback
                                </Button>
                              )}
                              {interview.interview_status === 'scheduled' && (
                                <Button size="sm" onClick={() => { setSelectedInterview(interview); setShowFeedbackModal(true); }}>
                                  <MessageSquare className="w-4 h-4 mr-1" /> Submit Feedback
                                </Button>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Feedback Modal */}
        {showFeedbackModal && selectedInterview && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-2xl max-h-[90vh] overflow-auto">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Submit Interview Feedback</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => { setShowFeedbackModal(false); setSelectedInterview(null); }}>
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Overall Rating (1-10)</Label>
                    <Input type="number" min="1" max="10" value={feedbackForm.rating} onChange={(e) => setFeedbackForm({...feedbackForm, rating: parseInt(e.target.value)})} />
                  </div>
                  <div>
                    <Label>Recommendation</Label>
                    <select className="w-full border rounded-md p-2" value={feedbackForm.recommendation} onChange={(e) => setFeedbackForm({...feedbackForm, recommendation: e.target.value})}>
                      <option value="hire">Hire</option>
                      <option value="next_round">Move to Next Round</option>
                      <option value="proceed">Proceed</option>
                      <option value="hold">Hold</option>
                      <option value="reject">Reject</option>
                    </select>
                  </div>
                  <div>
                    <Label>Technical Score (1-10)</Label>
                    <Input type="number" min="1" max="10" value={feedbackForm.technical_score} onChange={(e) => setFeedbackForm({...feedbackForm, technical_score: parseInt(e.target.value)})} />
                  </div>
                  <div>
                    <Label>Communication Score (1-10)</Label>
                    <Input type="number" min="1" max="10" value={feedbackForm.communication_score} onChange={(e) => setFeedbackForm({...feedbackForm, communication_score: parseInt(e.target.value)})} />
                  </div>
                  <div>
                    <Label>Problem Solving Score (1-10)</Label>
                    <Input type="number" min="1" max="10" value={feedbackForm.problem_solving_score} onChange={(e) => setFeedbackForm({...feedbackForm, problem_solving_score: parseInt(e.target.value)})} />
                  </div>
                  <div>
                    <Label>Cultural Fit Score (1-10)</Label>
                    <Input type="number" min="1" max="10" value={feedbackForm.cultural_fit_score} onChange={(e) => setFeedbackForm({...feedbackForm, cultural_fit_score: parseInt(e.target.value)})} />
                  </div>
                </div>
                <div>
                  <Label>Strengths (comma-separated)</Label>
                  <Input placeholder="Strong communication, Technical depth, Problem solving" value={feedbackForm.strengths} onChange={(e) => setFeedbackForm({...feedbackForm, strengths: e.target.value})} />
                </div>
                <div>
                  <Label>Areas of Improvement (comma-separated)</Label>
                  <Input placeholder="System design, Time management" value={feedbackForm.areas_of_improvement} onChange={(e) => setFeedbackForm({...feedbackForm, areas_of_improvement: e.target.value})} />
                </div>
                <div>
                  <Label>Comments</Label>
                  <textarea className="w-full border rounded-md p-2 min-h-[100px]" placeholder="Detailed feedback about the candidate..." value={feedbackForm.comments} onChange={(e) => setFeedbackForm({...feedbackForm, comments: e.target.value})} />
                </div>
                <div className="flex justify-end gap-3">
                  <Button variant="outline" onClick={() => { setShowFeedbackModal(false); setSelectedInterview(null); }}>Cancel</Button>
                  <Button className="bg-indigo-600 hover:bg-indigo-700" onClick={handleSubmitFeedback}>Submit Feedback</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default InterviewsManagement;
