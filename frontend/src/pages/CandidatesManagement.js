import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { User, Search, Briefcase, MapPin, Clock, Star, X, Mail, Phone, FileText, Filter } from 'lucide-react';
import apiClient from '../api/client';
import { toast } from 'sonner';

const CandidatesManagement = ({ user, onLogout }) => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [matchingJobs, setMatchingJobs] = useState([]);
  const [filters, setFilters] = useState({
    skills: '',
    minExperience: '',
    maxExperience: '',
    availability: ''
  });
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    try {
      const params = {};
      if (filters.skills) params.skills = filters.skills;
      if (filters.minExperience) params.min_experience = parseInt(filters.minExperience);
      if (filters.maxExperience) params.max_experience = parseInt(filters.maxExperience);
      if (filters.availability) params.availability = filters.availability;
      
      const response = await apiClient.get('/candidates', { params });
      setCandidates(response.data);
    } catch (error) {
      toast.error('Failed to fetch candidates');
    } finally {
      setLoading(false);
    }
  };

  const fetchMatchingJobs = async (candidateId) => {
    try {
      const response = await apiClient.get(`/candidates/${candidateId}/match-jobs`);
      setMatchingJobs(response.data.matches || []);
    } catch (error) {
      console.error('Failed to fetch matching jobs');
    }
  };

  const applyFilters = () => {
    setLoading(true);
    fetchCandidates();
    setShowFilters(false);
  };

  const clearFilters = () => {
    setFilters({ skills: '', minExperience: '', maxExperience: '', availability: '' });
    setLoading(true);
    fetchCandidates();
  };

  const filteredCandidates = candidates.filter(c => {
    const name = c.current_title || '';
    const company = c.current_company || '';
    const skills = (c.skills || []).join(' ');
    const searchLower = searchTerm.toLowerCase();
    return name.toLowerCase().includes(searchLower) || 
           company.toLowerCase().includes(searchLower) ||
           skills.toLowerCase().includes(searchLower);
  });

  const availabilityColors = {
    'immediate': 'bg-green-100 text-green-700',
    '2weeks': 'bg-blue-100 text-blue-700',
    '1month': 'bg-yellow-100 text-yellow-700',
    '3months': 'bg-orange-100 text-orange-700'
  };

  const availabilityLabels = {
    'immediate': 'Immediate',
    '2weeks': '2 Weeks',
    '1month': '1 Month',
    '3months': '3 Months'
  };

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Candidates</h1>
            <p className="text-slate-600">Browse and manage candidate profiles</p>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search by title, company, or skills..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" onClick={() => setShowFilters(!showFilters)}>
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm font-medium">Skills (comma-separated)</label>
                  <Input 
                    placeholder="React, Python, AWS" 
                    value={filters.skills}
                    onChange={(e) => setFilters({...filters, skills: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Min Experience (years)</label>
                  <Input 
                    type="number" 
                    min="0"
                    value={filters.minExperience}
                    onChange={(e) => setFilters({...filters, minExperience: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Max Experience (years)</label>
                  <Input 
                    type="number" 
                    min="0"
                    value={filters.maxExperience}
                    onChange={(e) => setFilters({...filters, maxExperience: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Availability</label>
                  <select 
                    className="w-full border rounded-md p-2"
                    value={filters.availability}
                    onChange={(e) => setFilters({...filters, availability: e.target.value})}
                  >
                    <option value="">Any</option>
                    <option value="immediate">Immediate</option>
                    <option value="2weeks">2 Weeks</option>
                    <option value="1month">1 Month</option>
                    <option value="3months">3 Months</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <Button onClick={applyFilters} className="bg-indigo-600 hover:bg-indigo-700">Apply Filters</Button>
                <Button variant="outline" onClick={clearFilters}>Clear</Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                  <User className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{candidates.length}</div>
                  <div className="text-sm text-slate-600">Total Candidates</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Clock className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{candidates.filter(c => c.availability === 'immediate').length}</div>
                  <div className="text-sm text-slate-600">Available Now</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Star className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{candidates.filter(c => c.experience_years >= 5).length}</div>
                  <div className="text-sm text-slate-600">Senior (5+ yrs)</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Briefcase className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{candidates.filter(c => c.is_available_for_referral).length}</div>
                  <div className="text-sm text-slate-600">Open to Referrals</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Candidates List */}
        {loading ? (
          <div className="text-center py-12">Loading candidates...</div>
        ) : filteredCandidates.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <User className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No candidates found</h3>
              <p className="text-slate-600">Try adjusting your search or filters</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredCandidates.map((candidate) => (
              <Card key={candidate.id} className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => { setSelectedCandidate(candidate); fetchMatchingJobs(candidate.id); }}>
                <CardContent className="p-5">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <User className="w-6 h-6 text-indigo-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900">{candidate.current_title || 'No Title'}</h3>
                        <p className="text-sm text-slate-600">{candidate.current_company || 'No Company'}</p>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {candidate.skills?.slice(0, 5).map((skill, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">{skill}</Badge>
                          ))}
                          {candidate.skills?.length > 5 && (
                            <Badge variant="secondary" className="text-xs">+{candidate.skills.length - 5}</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                      <div className="text-center px-3">
                        <div className="text-lg font-bold text-indigo-600">{candidate.experience_years || 0}</div>
                        <div className="text-xs text-slate-600">Years Exp</div>
                      </div>
                      <span className={`px-3 py-1 text-xs rounded-full ${availabilityColors[candidate.availability] || 'bg-slate-100 text-slate-600'}`}>
                        {availabilityLabels[candidate.availability] || 'Unknown'}
                      </span>
                      {candidate.overall_score && (
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                          <span className="font-medium">{candidate.overall_score}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Candidate Details Modal */}
        {selectedCandidate && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-3xl max-h-[90vh] overflow-auto">
              <CardHeader className="flex flex-row items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">
                    <User className="w-8 h-8 text-indigo-600" />
                  </div>
                  <div>
                    <CardTitle>{selectedCandidate.current_title || 'No Title'}</CardTitle>
                    <p className="text-slate-600">{selectedCandidate.current_company || 'No Company'}</p>
                    <span className={`inline-block mt-1 px-2 py-1 text-xs rounded-full ${availabilityColors[selectedCandidate.availability] || 'bg-slate-100 text-slate-600'}`}>
                      {availabilityLabels[selectedCandidate.availability] || 'Unknown'} availability
                    </span>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={() => { setSelectedCandidate(null); setMatchingJobs([]); }}>
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 bg-slate-50 rounded-lg">
                    <div className="text-2xl font-bold text-indigo-600">{selectedCandidate.experience_years || 0}</div>
                    <div className="text-xs text-slate-600">Years Experience</div>
                  </div>
                  <div className="text-center p-3 bg-slate-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{selectedCandidate.skills?.length || 0}</div>
                    <div className="text-xs text-slate-600">Skills</div>
                  </div>
                  <div className="text-center p-3 bg-slate-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {selectedCandidate.expected_salary ? `₹${(selectedCandidate.expected_salary / 100000).toFixed(1)}L` : '-'}
                    </div>
                    <div className="text-xs text-slate-600">Expected CTC</div>
                  </div>
                </div>

                {/* Skills */}
                <div>
                  <h4 className="font-medium mb-2">Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedCandidate.skills?.map((skill, idx) => (
                      <Badge key={idx} variant="secondary">{skill}</Badge>
                    )) || <span className="text-slate-500">No skills listed</span>}
                  </div>
                </div>

                {/* Education */}
                {selectedCandidate.education?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Education</h4>
                    <div className="space-y-2">
                      {selectedCandidate.education.map((edu, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 rounded-lg">
                          <div className="font-medium">{edu.degree}</div>
                          <div className="text-sm text-slate-600">{edu.institution}</div>
                          {edu.field && <div className="text-sm text-slate-500">{edu.field}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Work History */}
                {selectedCandidate.work_history?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Work History</h4>
                    <div className="space-y-2">
                      {selectedCandidate.work_history.map((work, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 rounded-lg">
                          <div className="font-medium">{work.title}</div>
                          <div className="text-sm text-slate-600">{work.company}</div>
                          <div className="text-xs text-slate-500">{work.start_date} - {work.is_current ? 'Present' : work.end_date}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Preferred Locations */}
                {selectedCandidate.preferred_locations?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Preferred Locations</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedCandidate.preferred_locations.map((loc, idx) => (
                        <span key={idx} className="flex items-center gap-1 px-2 py-1 bg-slate-100 rounded text-sm">
                          <MapPin className="w-3 h-3" /> {loc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Matching Jobs */}
                {matchingJobs.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Matching Jobs ({matchingJobs.length})</h4>
                    <div className="space-y-2">
                      {matchingJobs.slice(0, 5).map((job, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                          <div>
                            <div className="font-medium">{job.job_title}</div>
                            <div className="text-sm text-slate-600">{job.company_name}</div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-green-600">{job.match_score}%</div>
                            <div className="text-xs text-slate-500">Match</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Links */}
                <div className="flex gap-3">
                  {selectedCandidate.resume_url && (
                    <Button variant="outline" size="sm" asChild>
                      <a href={selectedCandidate.resume_url} target="_blank" rel="noopener noreferrer">
                        <FileText className="w-4 h-4 mr-2" /> View Resume
                      </a>
                    </Button>
                  )}
                  {selectedCandidate.portfolio_url && (
                    <Button variant="outline" size="sm" asChild>
                      <a href={selectedCandidate.portfolio_url} target="_blank" rel="noopener noreferrer">
                        Portfolio
                      </a>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default CandidatesManagement;
