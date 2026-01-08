import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { DollarSign, TrendingUp, FileText, CreditCard, ArrowUpRight, ArrowDownRight, Plus, X, Clock, Check, AlertCircle } from 'lucide-react';
import apiClient from '../api/client';
import { toast } from 'sonner';

const FinancialDashboard = ({ user, onLogout }) => {
  const [dashboard, setDashboard] = useState(null);
  const [commissions, setCommissions] = useState([]);
  const [payments, setPayments] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [payoutRequests, setPayoutRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPayoutModal, setShowPayoutModal] = useState(false);
  const [payoutForm, setPayoutForm] = useState({
    requested_amount: '',
    payout_method: 'bank_transfer',
    bank_details: { account_number: '', ifsc: '', account_name: '' }
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [dashRes, commRes, payRes, invRes, payoutRes] = await Promise.all([
        apiClient.get('/financial/dashboard'),
        apiClient.get('/financial/commissions'),
        apiClient.get('/financial/payments'),
        apiClient.get('/financial/invoices').catch(() => ({ data: [] })),
        apiClient.get('/financial/payout-requests')
      ]);
      setDashboard(dashRes.data);
      setCommissions(commRes.data);
      setPayments(payRes.data);
      setInvoices(invRes.data);
      setPayoutRequests(payoutRes.data.payouts || []);
    } catch (error) {
      toast.error('Failed to fetch financial data');
    } finally {
      setLoading(false);
    }
  };

  const handlePayoutRequest = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/financial/payout-requests', {
        requested_amount: parseFloat(payoutForm.requested_amount),
        payout_method: payoutForm.payout_method,
        bank_details: payoutForm.bank_details
      });
      toast.success('Payout request submitted successfully');
      setShowPayoutModal(false);
      setPayoutForm({ requested_amount: '', payout_method: 'bank_transfer', bank_details: { account_number: '', ifsc: '', account_name: '' } });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit payout request');
    }
  };

  const handleApproveCommission = async (commissionId, newStatus) => {
    try {
      await apiClient.put(`/financial/commissions/${commissionId}/status`, null, {
        params: { new_status: newStatus }
      });
      toast.success(`Commission ${newStatus}`);
      fetchData();
    } catch (error) {
      toast.error('Failed to update commission status');
    }
  };

  const handleApprovePayout = async (payoutId) => {
    try {
      await apiClient.put(`/financial/payout-requests/${payoutId}/approve`);
      toast.success('Payout approved');
      fetchData();
    } catch (error) {
      toast.error('Failed to approve payout');
    }
  };

  const statusColors = {
    'pending': 'bg-yellow-100 text-yellow-700',
    'approved': 'bg-blue-100 text-blue-700',
    'processing': 'bg-purple-100 text-purple-700',
    'paid': 'bg-green-100 text-green-700',
    'completed': 'bg-green-100 text-green-700',
    'cancelled': 'bg-red-100 text-red-700',
    'failed': 'bg-red-100 text-red-700',
    'draft': 'bg-slate-100 text-slate-700',
    'sent': 'bg-blue-100 text-blue-700',
    'overdue': 'bg-red-100 text-red-700',
    'rejected': 'bg-red-100 text-red-700'
  };

  const formatCurrency = (amount, currency = 'INR') => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const isAdmin = user.role === 'admin' || user.role === 'super_admin';

  // Calculate totals from dashboard
  const totalEarned = dashboard?.total_earned || Object.values(dashboard?.earnings || {}).reduce((sum, e) => sum + (e.total || 0), 0);
  const pendingAmount = dashboard?.earnings?.pending?.total || dashboard?.commissions?.pending?.total || 0;
  const paidAmount = dashboard?.earnings?.paid?.total || dashboard?.commissions?.paid?.total || 0;

  if (loading) {
    return (
      <DashboardLayout user={user} onLogout={onLogout}>
        <div className="text-center py-12">Loading financial data...</div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Financial Dashboard</h1>
            <p className="text-slate-600">Track commissions, payments, and payouts</p>
          </div>
          {!isAdmin && (
            <Button onClick={() => setShowPayoutModal(true)} className="bg-green-600 hover:bg-green-700">
              <Plus className="w-4 h-4 mr-2" />
              Request Payout
            </Button>
          )}
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm">Total Earned</p>
                  <p className="text-3xl font-bold mt-1">{formatCurrency(totalEarned)}</p>
                </div>
                <div className="p-3 bg-white/20 rounded-lg">
                  <TrendingUp className="w-6 h-6" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm">Pending</p>
                  <p className="text-2xl font-bold mt-1 text-yellow-600">{formatCurrency(pendingAmount)}</p>
                </div>
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <Clock className="w-5 h-5 text-yellow-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm">Paid Out</p>
                  <p className="text-2xl font-bold mt-1 text-green-600">{formatCurrency(paidAmount)}</p>
                </div>
                <div className="p-3 bg-green-100 rounded-lg">
                  <Check className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm">Commissions</p>
                  <p className="text-2xl font-bold mt-1">{commissions.length}</p>
                </div>
                <div className="p-3 bg-indigo-100 rounded-lg">
                  <DollarSign className="w-5 h-5 text-indigo-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="commissions" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="commissions">Commissions</TabsTrigger>
            <TabsTrigger value="payments">Payments</TabsTrigger>
            <TabsTrigger value="invoices">Invoices</TabsTrigger>
            <TabsTrigger value="payouts">Payouts</TabsTrigger>
          </TabsList>

          {/* Commissions Tab */}
          <TabsContent value="commissions" className="mt-4">
            {commissions.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <DollarSign className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No commissions yet</h3>
                  <p className="text-slate-600">Commissions will appear here when earned</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {commissions.map((commission) => (
                  <Card key={commission.id}>
                    <CardContent className="p-4">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge className={statusColors[commission.commission_status]}>
                              {commission.commission_status}
                            </Badge>
                            <span className="text-sm text-slate-500 capitalize">{commission.commission_type}</span>
                          </div>
                          <div className="mt-2 text-sm text-slate-600">
                            <p>Base Amount: {formatCurrency(commission.base_amount)}</p>
                            <p>Package Level: <span className="capitalize">{commission.package_level}</span> | Tier: <span className="capitalize">{commission.user_tier}</span></p>
                            <p>Rate: {(commission.effective_rate * 100).toFixed(1)}% | TDS: {formatCurrency(commission.tds_amount)}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-green-600">{formatCurrency(commission.net_commission)}</div>
                          <div className="text-sm text-slate-500">Net Commission</div>
                          <div className="text-xs text-slate-400 mt-1">{formatDate(commission.earned_date)}</div>
                          {isAdmin && commission.commission_status === 'pending' && (
                            <div className="flex gap-2 mt-2 justify-end">
                              <Button size="sm" variant="outline" onClick={() => handleApproveCommission(commission.id, 'approved')}>
                                Approve
                              </Button>
                              <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleApproveCommission(commission.id, 'cancelled')}>
                                Reject
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Payments Tab */}
          <TabsContent value="payments" className="mt-4">
            {payments.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <CreditCard className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No payments yet</h3>
                  <p className="text-slate-600">Payment records will appear here</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {payments.map((payment) => (
                  <Card key={payment.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`p-2 rounded-lg ${payment.payment_status === 'completed' ? 'bg-green-100' : 'bg-slate-100'}`}>
                            <CreditCard className={`w-5 h-5 ${payment.payment_status === 'completed' ? 'text-green-600' : 'text-slate-600'}`} />
                          </div>
                          <div>
                            <div className="font-medium">{payment.payee_name || 'Unknown'}</div>
                            <div className="text-sm text-slate-500 capitalize">{payment.payment_method} • {payment.related_entity_type}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">{formatCurrency(payment.amount, payment.currency)}</div>
                          <Badge className={statusColors[payment.payment_status]}>
                            {payment.payment_status}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Invoices Tab */}
          <TabsContent value="invoices" className="mt-4">
            {invoices.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No invoices yet</h3>
                  <p className="text-slate-600">Invoices will appear here when created</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {invoices.map((invoice) => (
                  <Card key={invoice.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{invoice.invoice_number}</div>
                          <div className="text-sm text-slate-500">{invoice.company_name}</div>
                          <div className="text-xs text-slate-400">
                            Due: {formatDate(invoice.due_date)}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">{formatCurrency(invoice.total_amount, invoice.currency)}</div>
                          <Badge className={statusColors[invoice.invoice_status]}>
                            {invoice.invoice_status}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Payouts Tab */}
          <TabsContent value="payouts" className="mt-4">
            {payoutRequests.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <ArrowUpRight className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No payout requests</h3>
                  <p className="text-slate-600">Request a payout when you have available balance</p>
                  {!isAdmin && (
                    <Button className="mt-4" onClick={() => setShowPayoutModal(true)}>
                      Request Payout
                    </Button>
                  )}
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {payoutRequests.map((payout) => (
                  <Card key={payout.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{payout.user_name || 'You'}</div>
                          <div className="text-sm text-slate-500 capitalize">{payout.payout_method}</div>
                          <div className="text-xs text-slate-400">{formatDate(payout.created_at)}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">{formatCurrency(payout.requested_amount, payout.currency)}</div>
                          <Badge className={statusColors[payout.request_status]}>
                            {payout.request_status}
                          </Badge>
                          {isAdmin && payout.request_status === 'pending' && (
                            <div className="mt-2">
                              <Button size="sm" onClick={() => handleApprovePayout(payout.id)}>
                                Approve
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Payout Request Modal */}
        {showPayoutModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Request Payout</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setShowPayoutModal(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePayoutRequest} className="space-y-4">
                  <div>
                    <Label>Amount (₹)</Label>
                    <Input 
                      type="number" 
                      min="100" 
                      required 
                      value={payoutForm.requested_amount} 
                      onChange={(e) => setPayoutForm({...payoutForm, requested_amount: e.target.value})} 
                    />
                  </div>
                  <div>
                    <Label>Payout Method</Label>
                    <select 
                      className="w-full border rounded-md p-2" 
                      value={payoutForm.payout_method} 
                      onChange={(e) => setPayoutForm({...payoutForm, payout_method: e.target.value})}
                    >
                      <option value="bank_transfer">Bank Transfer</option>
                      <option value="paypal">PayPal</option>
                      <option value="wallet">Wallet</option>
                    </select>
                  </div>
                  {payoutForm.payout_method === 'bank_transfer' && (
                    <>
                      <div>
                        <Label>Account Holder Name</Label>
                        <Input 
                          value={payoutForm.bank_details.account_name} 
                          onChange={(e) => setPayoutForm({...payoutForm, bank_details: {...payoutForm.bank_details, account_name: e.target.value}})} 
                        />
                      </div>
                      <div>
                        <Label>Account Number</Label>
                        <Input 
                          value={payoutForm.bank_details.account_number} 
                          onChange={(e) => setPayoutForm({...payoutForm, bank_details: {...payoutForm.bank_details, account_number: e.target.value}})} 
                        />
                      </div>
                      <div>
                        <Label>IFSC Code</Label>
                        <Input 
                          value={payoutForm.bank_details.ifsc} 
                          onChange={(e) => setPayoutForm({...payoutForm, bank_details: {...payoutForm.bank_details, ifsc: e.target.value}})} 
                        />
                      </div>
                    </>
                  )}
                  <div className="flex justify-end gap-3">
                    <Button type="button" variant="outline" onClick={() => setShowPayoutModal(false)}>Cancel</Button>
                    <Button type="submit" className="bg-green-600 hover:bg-green-700">Submit Request</Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default FinancialDashboard;
