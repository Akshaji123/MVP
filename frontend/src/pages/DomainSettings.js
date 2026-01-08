import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import axios from 'axios';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Shield, Plus, X, Mail } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const DomainSettings = ({ user, onLogout }) => {
  const [enabled, setEnabled] = useState(false);
  const [domains, setDomains] = useState([]);
  const [newDomain, setNewDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [emails, setEmails] = useState([]);

  useEffect(() => {
    fetchSettings();
    fetchEmails();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/admin/domain-settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEnabled(response.data.enabled);
      setDomains(response.data.allowed_domains || []);
    } catch (error) {
      toast.error('Failed to load settings');
    }
  };

  const fetchEmails = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BACKEND_URL}/api/admin/emails/sent?limit=10`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmails(response.data.emails || []);
    } catch (error) {
      console.error('Failed to load emails');
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${BACKEND_URL}/api/admin/domain-settings`,
        { enabled, allowed_domains: domains },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Domain settings updated successfully!');
    } catch (error) {
      toast.error('Failed to update settings');
    } finally {
      setLoading(false);
    }
  };

  const addDomain = () => {
    if (newDomain && !domains.includes(newDomain)) {
      setDomains([...domains, newDomain.toLowerCase()]);
      setNewDomain('');
    }
  };

  const removeDomain = (domain) => {
    setDomains(domains.filter(d => d !== domain));
  };

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-8" data-testid="domain-settings">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2" style={{fontFamily: 'Outfit, sans-serif'}}>
            Security & Email Settings
          </h1>
          <p className="text-slate-600">Manage domain restrictions and email automation</p>
        </div>

        {/* Domain Restrictions */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-700" />
              Domain-Based Access Control
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div>
                <div className="font-semibold">Enable Domain Restrictions</div>
                <div className="text-sm text-slate-600">Only allow registration from approved email domains</div>
              </div>
              <Switch
                checked={enabled}
                onCheckedChange={setEnabled}
                data-testid="enable-restrictions-switch"
              />
            </div>

            {enabled && (
              <div>
                <Label>Allowed Email Domains</Label>
                <div className="flex gap-2 mt-2">
                  <Input
                    data-testid="domain-input"
                    placeholder="e.g., company.com"
                    value={newDomain}
                    onChange={(e) => setNewDomain(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addDomain()}
                  />
                  <Button
                    data-testid="add-domain-btn"
                    onClick={addDomain}
                    className="bg-indigo-700 hover:bg-indigo-800"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add
                  </Button>
                </div>

                <div className="mt-4 space-y-2">
                  {domains.length === 0 ? (
                    <p className="text-sm text-slate-500 text-center py-4">
                      No domains added. Add domains above to restrict access.
                    </p>
                  ) : (
                    domains.map((domain) => (
                      <div
                        key={domain}
                        data-testid={`domain-${domain}`}
                        className="flex items-center justify-between p-3 bg-indigo-50 border border-indigo-200 rounded-lg"
                      >
                        <span className="font-medium text-indigo-900">@{domain}</span>
                        <button
                          data-testid={`remove-${domain}`}
                          onClick={() => removeDomain(domain)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            <Button
              data-testid="save-domain-settings-btn"
              onClick={handleSave}
              disabled={loading}
              className="w-full bg-indigo-700 hover:bg-indigo-800"
            >
              {loading ? 'Saving...' : 'Save Settings'}
            </Button>
          </CardContent>
        </Card>

        {/* Email Log */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-lime-700" />
              Email Automation Log
            </CardTitle>
          </CardHeader>
          <CardContent>
            {emails.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                No emails sent yet. Emails will be logged here for testing.
              </div>
            ) : (
              <div className="space-y-3">
                {emails.map((email, idx) => (
                  <div key={idx} data-testid={`email-log-${idx}`} className="p-4 border border-slate-200 rounded-lg hover:bg-slate-50">
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-semibold">{email.subject}</div>
                      <span className="px-2 py-1 bg-lime-100 text-lime-700 rounded text-xs">
                        {email.status}
                      </span>
                    </div>
                    <div className="text-sm text-slate-600">
                      To: {email.to}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {new Date(email.sent_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default DomainSettings;