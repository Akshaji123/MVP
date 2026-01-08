import { useState } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Sparkles, Copy, Download, RefreshCw, Check, FileText, Wand2 } from 'lucide-react';
import apiClient from '../api/client';
import { toast } from 'sonner';

const JDGenerator = ({ user, onLogout }) => {
  const [loading, setLoading] = useState(false);
  const [generatedJD, setGeneratedJD] = useState(null);
  const [copied, setCopied] = useState(false);
  const [formData, setFormData] = useState({
    job_title: '',
    company_name: '',
    department: '',
    location: '',
    employment_type: 'Full-time',
    experience_level: 'Mid-level',
    required_skills: '',
    salary_range: '',
    additional_requirements: '',
    company_description: '',
    tone: 'professional'
  });

  const [improveData, setImproveData] = useState({
    existing_jd: '',
    improvement_focus: 'general'
  });
  const [improvedJD, setImprovedJD] = useState(null);

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!formData.job_title || !formData.company_name) {
      toast.error('Job title and company name are required');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...formData,
        required_skills: formData.required_skills 
          ? formData.required_skills.split(',').map(s => s.trim()).filter(Boolean)
          : null
      };
      
      const response = await apiClient.post('/ai/generate-jd', payload);
      setGeneratedJD(response.data);
      toast.success('Job description generated successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate JD');
    } finally {
      setLoading(false);
    }
  };

  const handleImprove = async (e) => {
    e.preventDefault();
    if (!improveData.existing_jd) {
      toast.error('Please paste an existing job description');
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.post('/ai/improve-jd', improveData);
      setImprovedJD(response.data);
      toast.success('Job description improved successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to improve JD');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success('Copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadAsMarkdown = (content, filename) => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const employmentTypes = ['Full-time', 'Part-time', 'Contract', 'Freelance', 'Internship'];
  const experienceLevels = ['Entry-level', 'Junior', 'Mid-level', 'Senior', 'Lead', 'Manager', 'Director', 'Executive'];
  const tones = ['professional', 'casual', 'startup'];
  const improvementFocuses = [
    { value: 'general', label: 'General Improvement' },
    { value: 'inclusivity', label: 'More Inclusive' },
    { value: 'clarity', label: 'Better Clarity' },
    { value: 'engagement', label: 'More Engaging' }
  ];

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-7 h-7 text-purple-600" />
              AI Job Description Generator
            </h1>
            <p className="text-slate-600">Generate professional job descriptions with AI</p>
          </div>
          <Badge className="bg-purple-100 text-purple-700">
            Powered by GPT-4o
          </Badge>
        </div>

        <Tabs defaultValue="generate" className="w-full">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="generate">
              <Wand2 className="w-4 h-4 mr-2" />
              Generate New
            </TabsTrigger>
            <TabsTrigger value="improve">
              <RefreshCw className="w-4 h-4 mr-2" />
              Improve Existing
            </TabsTrigger>
          </TabsList>

          {/* Generate New JD Tab */}
          <TabsContent value="generate" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Form */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Job Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleGenerate} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Job Title *</Label>
                        <Input 
                          placeholder="e.g., Senior Software Engineer"
                          value={formData.job_title}
                          onChange={(e) => setFormData({...formData, job_title: e.target.value})}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Company Name *</Label>
                        <Input 
                          placeholder="e.g., TechCorp Inc"
                          value={formData.company_name}
                          onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Department</Label>
                        <Input 
                          placeholder="e.g., Engineering"
                          value={formData.department}
                          onChange={(e) => setFormData({...formData, department: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Location</Label>
                        <Input 
                          placeholder="e.g., Bangalore, India"
                          value={formData.location}
                          onChange={(e) => setFormData({...formData, location: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Employment Type</Label>
                        <select 
                          className="w-full border rounded-md p-2"
                          value={formData.employment_type}
                          onChange={(e) => setFormData({...formData, employment_type: e.target.value})}
                        >
                          {employmentTypes.map(type => (
                            <option key={type} value={type}>{type}</option>
                          ))}
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label>Experience Level</Label>
                        <select 
                          className="w-full border rounded-md p-2"
                          value={formData.experience_level}
                          onChange={(e) => setFormData({...formData, experience_level: e.target.value})}
                        >
                          {experienceLevels.map(level => (
                            <option key={level} value={level}>{level}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Required Skills (comma-separated)</Label>
                      <Input 
                        placeholder="e.g., React, Node.js, Python, AWS"
                        value={formData.required_skills}
                        onChange={(e) => setFormData({...formData, required_skills: e.target.value})}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Salary Range</Label>
                        <Input 
                          placeholder="e.g., ₹15-25 LPA"
                          value={formData.salary_range}
                          onChange={(e) => setFormData({...formData, salary_range: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Tone</Label>
                        <select 
                          className="w-full border rounded-md p-2"
                          value={formData.tone}
                          onChange={(e) => setFormData({...formData, tone: e.target.value})}
                        >
                          {tones.map(tone => (
                            <option key={tone} value={tone} className="capitalize">{tone}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Additional Requirements</Label>
                      <textarea 
                        className="w-full border rounded-md p-2 min-h-[80px]"
                        placeholder="Any specific requirements..."
                        value={formData.additional_requirements}
                        onChange={(e) => setFormData({...formData, additional_requirements: e.target.value})}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Company Description</Label>
                      <textarea 
                        className="w-full border rounded-md p-2 min-h-[80px]"
                        placeholder="Brief description of your company..."
                        value={formData.company_description}
                        onChange={(e) => setFormData({...formData, company_description: e.target.value})}
                      />
                    </div>

                    <Button 
                      type="submit" 
                      className="w-full bg-purple-600 hover:bg-purple-700"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 mr-2" />
                          Generate Job Description
                        </>
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Generated JD Preview */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-lg">Generated Job Description</CardTitle>
                  {generatedJD && (
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => copyToClipboard(generatedJD.content)}
                      >
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => downloadAsMarkdown(generatedJD.content, `${formData.job_title.replace(/\s+/g, '_')}_JD`)}
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </CardHeader>
                <CardContent>
                  {generatedJD ? (
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-sm text-slate-500">
                        <Badge variant="outline">{generatedJD.model}</Badge>
                        {generatedJD.is_ai_generated && (
                          <Badge className="bg-purple-100 text-purple-700">AI Generated</Badge>
                        )}
                      </div>
                      <div className="prose prose-sm max-w-none max-h-[600px] overflow-auto p-4 bg-slate-50 rounded-lg">
                        <pre className="whitespace-pre-wrap font-sans text-sm">{generatedJD.content}</pre>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <FileText className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                      <p>Fill in the details and click generate</p>
                      <p className="text-sm">Your AI-powered job description will appear here</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Improve Existing JD Tab */}
          <TabsContent value="improve" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Input */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Existing Job Description</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleImprove} className="space-y-4">
                    <div className="space-y-2">
                      <Label>Paste your existing JD</Label>
                      <textarea 
                        className="w-full border rounded-md p-3 min-h-[300px] font-mono text-sm"
                        placeholder="Paste your existing job description here..."
                        value={improveData.existing_jd}
                        onChange={(e) => setImproveData({...improveData, existing_jd: e.target.value})}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Improvement Focus</Label>
                      <select 
                        className="w-full border rounded-md p-2"
                        value={improveData.improvement_focus}
                        onChange={(e) => setImproveData({...improveData, improvement_focus: e.target.value})}
                      >
                        {improvementFocuses.map(focus => (
                          <option key={focus.value} value={focus.value}>{focus.label}</option>
                        ))}
                      </select>
                    </div>

                    <Button 
                      type="submit" 
                      className="w-full bg-purple-600 hover:bg-purple-700"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Improving...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2" />
                          Improve Job Description
                        </>
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Improved JD */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-lg">Improved Version</CardTitle>
                  {improvedJD?.improved && (
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => copyToClipboard(improvedJD.improved)}
                      >
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => downloadAsMarkdown(improvedJD.improved, 'improved_JD')}
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </CardHeader>
                <CardContent>
                  {improvedJD?.improved ? (
                    <div className="space-y-4">
                      <Badge className="bg-green-100 text-green-700 capitalize">
                        {improvedJD.improvement_focus} improvement
                      </Badge>
                      <div className="prose prose-sm max-w-none max-h-[500px] overflow-auto p-4 bg-green-50 rounded-lg">
                        <pre className="whitespace-pre-wrap font-sans text-sm">{improvedJD.improved}</pre>
                      </div>
                    </div>
                  ) : improvedJD?.error ? (
                    <div className="text-center py-12 text-red-500">
                      <p>Error: {improvedJD.error}</p>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      <RefreshCw className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                      <p>Paste an existing JD and select improvement focus</p>
                      <p className="text-sm">The AI-improved version will appear here</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default JDGenerator;
