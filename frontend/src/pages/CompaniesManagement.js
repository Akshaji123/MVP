import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Building2, Plus, Search, Globe, MapPin, Users, Briefcase, X, Edit, BarChart3 } from 'lucide-react';
import apiClient from '../api/client';
import { toast } from 'sonner';

const CompaniesManagement = ({ user, onLogout }) => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companyStats, setCompanyStats] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    legal_name: '',
    industry: '',
    company_size: 'startup',
    website: '',
    description: '',
    headquarters_location: '',
    founded_year: '',
    company_type: 'startup'
  });

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await apiClient.get('/companies');
      setCompanies(response.data);
    } catch (error) {
      toast.error('Failed to fetch companies');
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanyStats = async (companyId) => {
    try {
      const response = await apiClient.get(`/companies/${companyId}/stats`);
      setCompanyStats(response.data.stats);
    } catch (error) {
      console.error('Failed to fetch company stats');
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        founded_year: formData.founded_year ? parseInt(formData.founded_year) : null
      };
      await apiClient.post('/companies', payload);
      toast.success('Company created successfully');
      setShowCreateModal(false);
      setFormData({
        name: '', legal_name: '', industry: '', company_size: 'startup',
        website: '', description: '', headquarters_location: '', founded_year: '', company_type: 'startup'
      });
      fetchCompanies();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create company');
    }
  };

  const filteredCompanies = companies.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.industry || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const companySizes = ['startup', 'small', 'medium', 'large', 'enterprise'];
  const companyTypes = ['startup', 'corporation', 'government', 'ngo'];
  const industries = ['Technology', 'Finance', 'Healthcare', 'Education', 'Manufacturing', 'Retail', 'Consulting', 'Other'];

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Companies Management</h1>
            <p className="text-slate-600">Manage client companies and partnerships</p>
          </div>
          <Button onClick={() => setShowCreateModal(true)} className="bg-indigo-600 hover:bg-indigo-700">
            <Plus className="w-4 h-4 mr-2" />
            Add Company
          </Button>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Search companies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                  <Building2 className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{companies.length}</div>
                  <div className="text-sm text-slate-600">Total Companies</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Users className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{companies.filter(c => c.is_active).length}</div>
                  <div className="text-sm text-slate-600">Active</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Briefcase className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{companies.filter(c => c.company_size === 'enterprise').length}</div>
                  <div className="text-sm text-slate-600">Enterprise</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Globe className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{new Set(companies.map(c => c.industry).filter(Boolean)).size}</div>
                  <div className="text-sm text-slate-600">Industries</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Companies Grid */}
        {loading ? (
          <div className="text-center py-12">Loading companies...</div>
        ) : filteredCompanies.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No companies found</h3>
              <p className="text-slate-600 mb-4">Get started by adding your first company</p>
              <Button onClick={() => setShowCreateModal(true)}>Add Company</Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCompanies.map((company) => (
              <Card key={company.id} className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => { setSelectedCompany(company); fetchCompanyStats(company.id); }}>
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {company.logo_url ? (
                        <img src={company.logo_url} alt={company.name} className="w-12 h-12 rounded-lg object-cover" />
                      ) : (
                        <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                          <Building2 className="w-6 h-6 text-indigo-600" />
                        </div>
                      )}
                      <div>
                        <h3 className="font-semibold text-slate-900">{company.name}</h3>
                        <span className="text-sm text-slate-500">{company.industry || 'No industry'}</span>
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${company.is_active ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
                      {company.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="space-y-2 text-sm text-slate-600">
                    {company.headquarters_location && (
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4" />
                        {company.headquarters_location}
                      </div>
                    )}
                    {company.website && (
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4" />
                        <a href={company.website} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline" onClick={(e) => e.stopPropagation()}>
                          {company.website.replace(/^https?:\/\//, '')}
                        </a>
                      </div>
                    )}
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      <span className="capitalize">{company.company_size || 'Unknown'} size</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-2xl max-h-[90vh] overflow-auto">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Add New Company</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setShowCreateModal(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateCompany} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Company Name *</Label>
                      <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Legal Name</Label>
                      <Input value={formData.legal_name} onChange={(e) => setFormData({...formData, legal_name: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>Industry</Label>
                      <select className="w-full border rounded-md p-2" value={formData.industry} onChange={(e) => setFormData({...formData, industry: e.target.value})}>
                        <option value="">Select industry</option>
                        {industries.map(i => <option key={i} value={i}>{i}</option>)}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label>Company Size</Label>
                      <select className="w-full border rounded-md p-2" value={formData.company_size} onChange={(e) => setFormData({...formData, company_size: e.target.value})}>
                        {companySizes.map(s => <option key={s} value={s} className="capitalize">{s}</option>)}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label>Company Type</Label>
                      <select className="w-full border rounded-md p-2" value={formData.company_type} onChange={(e) => setFormData({...formData, company_type: e.target.value})}>
                        {companyTypes.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label>Founded Year</Label>
                      <Input type="number" min="1800" max="2100" value={formData.founded_year} onChange={(e) => setFormData({...formData, founded_year: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>Website</Label>
                      <Input type="url" placeholder="https://" value={formData.website} onChange={(e) => setFormData({...formData, website: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>Headquarters</Label>
                      <Input placeholder="City, Country" value={formData.headquarters_location} onChange={(e) => setFormData({...formData, headquarters_location: e.target.value})} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <textarea className="w-full border rounded-md p-2 min-h-[100px]" value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} />
                  </div>
                  <div className="flex justify-end gap-3">
                    <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                    <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700">Create Company</Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Company Details Modal */}
        {selectedCompany && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-2xl">
              <CardHeader className="flex flex-row items-center justify-between">
                <div className="flex items-center gap-3">
                  {selectedCompany.logo_url ? (
                    <img src={selectedCompany.logo_url} alt={selectedCompany.name} className="w-12 h-12 rounded-lg object-cover" />
                  ) : (
                    <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-indigo-600" />
                    </div>
                  )}
                  <div>
                    <CardTitle>{selectedCompany.name}</CardTitle>
                    <span className="text-sm text-slate-500">{selectedCompany.industry || 'No industry'}</span>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={() => { setSelectedCompany(null); setCompanyStats(null); }}>
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Stats */}
                {companyStats && (
                  <div className="grid grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-indigo-600">{companyStats.total_jobs}</div>
                      <div className="text-xs text-slate-600">Total Jobs</div>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{companyStats.active_jobs}</div>
                      <div className="text-xs text-slate-600">Active Jobs</div>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{companyStats.total_applications}</div>
                      <div className="text-xs text-slate-600">Applications</div>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">{companyStats.hired_candidates}</div>
                      <div className="text-xs text-slate-600">Hired</div>
                    </div>
                  </div>
                )}

                {/* Details */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-slate-500">Legal Name:</span> <span className="font-medium">{selectedCompany.legal_name || '-'}</span></div>
                  <div><span className="text-slate-500">Type:</span> <span className="font-medium capitalize">{selectedCompany.company_type || '-'}</span></div>
                  <div><span className="text-slate-500">Size:</span> <span className="font-medium capitalize">{selectedCompany.company_size || '-'}</span></div>
                  <div><span className="text-slate-500">Founded:</span> <span className="font-medium">{selectedCompany.founded_year || '-'}</span></div>
                  <div><span className="text-slate-500">Location:</span> <span className="font-medium">{selectedCompany.headquarters_location || '-'}</span></div>
                  <div><span className="text-slate-500">Website:</span> {selectedCompany.website ? <a href={selectedCompany.website} target="_blank" rel="noopener noreferrer" className="font-medium text-indigo-600 hover:underline">{selectedCompany.website}</a> : '-'}</div>
                </div>

                {selectedCompany.description && (
                  <div>
                    <h4 className="font-medium mb-2">About</h4>
                    <p className="text-sm text-slate-600">{selectedCompany.description}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default CompaniesManagement;
