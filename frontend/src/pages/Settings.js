import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import axios from 'axios';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { DollarSign, TrendingUp } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Settings = ({ user, onLogout }) => {
  const [currency, setCurrency] = useState(user.currency_preference || 'INR');
  const [rates, setRates] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchRates();
  }, []);

  const fetchRates = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/settings/currency-rates`);
      setRates(response.data);
    } catch (error) {
      console.error('Failed to fetch rates');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.patch(
        `${BACKEND_URL}/api/users/${user.id}/currency`,
        null,
        {
          params: { currency },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      // Update local storage
      const userData = JSON.parse(localStorage.getItem('user'));
      userData.currency_preference = currency;
      localStorage.setItem('user', JSON.stringify(userData));
      
      toast.success('Currency preference updated successfully!');
    } catch (error) {
      toast.error('Failed to update currency preference');
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-8" data-testid="settings-page">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2" style={{fontFamily: 'Outfit, sans-serif'}}>
            Settings
          </h1>
          <p className="text-slate-600">Manage your account preferences</p>
        </div>

        {/* Currency Settings */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-indigo-700" />
              Currency Preference
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label htmlFor="currency-select">Transaction Currency</Label>
              <Select value={currency} onValueChange={setCurrency}>
                <SelectTrigger data-testid="currency-select" className="mt-2">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="INR">Indian Rupee (₹ INR)</SelectItem>
                  <SelectItem value="USD">US Dollar ($ USD)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-slate-500 mt-2">
                This will be used for all invoices and financial transactions
              </p>
            </div>

            {rates && (
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-4 h-4 text-slate-600" />
                  <span className="font-semibold text-sm">Current Exchange Rate</span>
                </div>
                <div className="space-y-2 text-sm text-slate-600">
                  <div className="flex justify-between">
                    <span>1 INR =</span>
                    <span className="font-semibold">${rates.rates.USD.toFixed(3)} USD</span>
                  </div>
                  <div className="flex justify-between">
                    <span>1 USD =</span>
                    <span className="font-semibold">₹{(1/rates.rates.USD).toFixed(2)} INR</span>
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Last updated: {new Date(rates.updated_at).toLocaleString()}
                </p>
              </div>
            )}

            <Button 
              data-testid="save-settings-btn"
              onClick={handleSave} 
              disabled={saving || currency === user.currency_preference}
              className="bg-indigo-700 hover:bg-indigo-800"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </CardContent>
        </Card>

        {/* Account Info */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-600">Name</span>
                <span className="font-semibold">{user.full_name}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-600">Email</span>
                <span className="font-semibold">{user.email}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-slate-600">Role</span>
                <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium capitalize">
                  {user.role}
                </span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-slate-600">Member Since</span>
                <span className="font-semibold">{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Settings;