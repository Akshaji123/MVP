import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Mail, Send, Inbox, MessageSquare, X, Clock, Check, Reply, User, Search, Plus } from 'lucide-react';
import apiClient from '../api/client';
import { toast } from 'sonner';

const CommunicationCenter = ({ user, onLogout }) => {
  const [inboxMessages, setInboxMessages] = useState([]);
  const [sentMessages, setSentMessages] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [showComposeModal, setShowComposeModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [composeForm, setComposeForm] = useState({
    recipient_id: '',
    subject: '',
    message_body: '',
    priority: 'normal'
  });
  const [users, setUsers] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [inboxRes, sentRes, unreadRes] = await Promise.all([
        apiClient.get('/communication/messages/inbox'),
        apiClient.get('/communication/messages/sent'),
        apiClient.get('/communication/messages/unread-count')
      ]);
      setInboxMessages(inboxRes.data);
      setSentMessages(sentRes.data);
      setUnreadCount(unreadRes.data.unread_count);
      
      // Fetch users for recipient selection (admin only)
      if (user.role === 'admin' || user.role === 'super_admin' || user.role === 'recruiter') {
        try {
          const usersRes = await apiClient.get('/users', { params: { limit: 100 } });
          setUsers(usersRes.data);
        } catch (e) {
          // Users endpoint might fail for non-admin
        }
      }
    } catch (error) {
      toast.error('Failed to fetch messages');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!composeForm.recipient_id || !composeForm.message_body) {
      toast.error('Please fill in all required fields');
      return;
    }
    try {
      await apiClient.post('/communication/messages', composeForm);
      toast.success('Message sent successfully');
      setShowComposeModal(false);
      setComposeForm({ recipient_id: '', subject: '', message_body: '', priority: 'normal' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send message');
    }
  };

  const handleReply = async (originalMessage) => {
    if (!composeForm.message_body) {
      toast.error('Please enter a message');
      return;
    }
    try {
      await apiClient.post(`/communication/messages/${originalMessage.id}/reply`, {
        recipient_id: originalMessage.sender_id,
        message_body: composeForm.message_body,
        message_type: 'text',
        priority: 'normal'
      });
      toast.success('Reply sent successfully');
      setSelectedMessage(null);
      setComposeForm({ recipient_id: '', subject: '', message_body: '', priority: 'normal' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send reply');
    }
  };

  const handleViewMessage = async (message) => {
    setSelectedMessage(message);
    // Mark as read when viewing
    if (!message.is_read && message.recipient_id === user.id) {
      try {
        await apiClient.get(`/communication/messages/${message.id}`);
        fetchData(); // Refresh to update unread count
      } catch (e) {
        // Ignore errors
      }
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString('en-IN', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    }
  };

  const priorityColors = {
    'urgent': 'bg-red-100 text-red-700',
    'high': 'bg-orange-100 text-orange-700',
    'normal': 'bg-slate-100 text-slate-700',
    'low': 'bg-blue-100 text-blue-700'
  };

  const filteredInbox = inboxMessages.filter(m => 
    (m.subject || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (m.sender_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (m.message_body || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredSent = sentMessages.filter(m => 
    (m.subject || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (m.recipient_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (m.message_body || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <DashboardLayout user={user} onLogout={onLogout}>
        <div className="text-center py-12">Loading messages...</div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Communication Center</h1>
            <p className="text-slate-600">Manage your messages and notifications</p>
          </div>
          <Button onClick={() => setShowComposeModal(true)} className="bg-indigo-600 hover:bg-indigo-700">
            <Plus className="w-4 h-4 mr-2" />
            Compose
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 rounded-lg">
                  <Inbox className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{inboxMessages.length}</div>
                  <div className="text-sm text-slate-600">Inbox</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className={unreadCount > 0 ? 'ring-2 ring-red-200' : ''}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${unreadCount > 0 ? 'bg-red-100' : 'bg-slate-100'}`}>
                  <Mail className={`w-5 h-5 ${unreadCount > 0 ? 'text-red-600' : 'text-slate-600'}`} />
                </div>
                <div>
                  <div className="text-2xl font-bold">{unreadCount}</div>
                  <div className="text-sm text-slate-600">Unread</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Send className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{sentMessages.length}</div>
                  <div className="text-sm text-slate-600">Sent</div>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <MessageSquare className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold">{inboxMessages.length + sentMessages.length}</div>
                  <div className="text-sm text-slate-600">Total</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Search messages..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Tabs */}
        <Tabs defaultValue="inbox" className="w-full">
          <TabsList>
            <TabsTrigger value="inbox" className="relative">
              Inbox
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="sent">Sent</TabsTrigger>
          </TabsList>

          {/* Inbox Tab */}
          <TabsContent value="inbox" className="mt-4">
            {filteredInbox.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Inbox className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No messages</h3>
                  <p className="text-slate-600">Your inbox is empty</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-2">
                {filteredInbox.map((message) => (
                  <Card 
                    key={message.id} 
                    className={`hover:shadow-md transition-shadow cursor-pointer ${!message.is_read ? 'bg-indigo-50 border-indigo-200' : ''}`}
                    onClick={() => handleViewMessage(message)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center flex-shrink-0">
                          <User className="w-5 h-5 text-slate-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className={`font-medium ${!message.is_read ? 'text-slate-900' : 'text-slate-700'}`}>
                                {message.sender_name || 'Unknown'}
                              </span>
                              {message.priority !== 'normal' && (
                                <Badge className={`text-xs ${priorityColors[message.priority]}`}>
                                  {message.priority}
                                </Badge>
                              )}
                            </div>
                            <span className="text-sm text-slate-500 flex-shrink-0">{formatDate(message.created_at)}</span>
                          </div>
                          {message.subject && (
                            <div className={`text-sm ${!message.is_read ? 'font-medium' : ''} truncate`}>
                              {message.subject}
                            </div>
                          )}
                          <div className="text-sm text-slate-600 truncate">
                            {message.message_body}
                          </div>
                        </div>
                        {!message.is_read && (
                          <div className="w-2 h-2 bg-indigo-600 rounded-full flex-shrink-0 mt-2" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Sent Tab */}
          <TabsContent value="sent" className="mt-4">
            {filteredSent.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Send className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No sent messages</h3>
                  <p className="text-slate-600">Messages you send will appear here</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-2">
                {filteredSent.map((message) => (
                  <Card 
                    key={message.id} 
                    className="hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => handleViewMessage(message)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <Send className="w-5 h-5 text-green-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium text-slate-700">
                              To: {message.recipient_name || 'Unknown'}
                            </span>
                            <div className="flex items-center gap-2">
                              {message.is_read && (
                                <Check className="w-4 h-4 text-green-600" />
                              )}
                              <span className="text-sm text-slate-500">{formatDate(message.created_at)}</span>
                            </div>
                          </div>
                          {message.subject && (
                            <div className="text-sm truncate">{message.subject}</div>
                          )}
                          <div className="text-sm text-slate-600 truncate">
                            {message.message_body}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Compose Modal */}
        {showComposeModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-lg">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>New Message</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setShowComposeModal(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSendMessage} className="space-y-4">
                  <div>
                    <Label>To *</Label>
                    {users.length > 0 ? (
                      <select 
                        className="w-full border rounded-md p-2" 
                        value={composeForm.recipient_id}
                        onChange={(e) => setComposeForm({...composeForm, recipient_id: e.target.value})}
                        required
                      >
                        <option value="">Select recipient</option>
                        {users.filter(u => u.id !== user.id).map(u => (
                          <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>
                        ))}
                      </select>
                    ) : (
                      <Input 
                        placeholder="Recipient User ID" 
                        value={composeForm.recipient_id}
                        onChange={(e) => setComposeForm({...composeForm, recipient_id: e.target.value})}
                        required
                      />
                    )}
                  </div>
                  <div>
                    <Label>Subject</Label>
                    <Input 
                      placeholder="Subject (optional)" 
                      value={composeForm.subject}
                      onChange={(e) => setComposeForm({...composeForm, subject: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Priority</Label>
                    <select 
                      className="w-full border rounded-md p-2" 
                      value={composeForm.priority}
                      onChange={(e) => setComposeForm({...composeForm, priority: e.target.value})}
                    >
                      <option value="low">Low</option>
                      <option value="normal">Normal</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                  <div>
                    <Label>Message *</Label>
                    <textarea 
                      className="w-full border rounded-md p-2 min-h-[150px]" 
                      placeholder="Type your message..." 
                      value={composeForm.message_body}
                      onChange={(e) => setComposeForm({...composeForm, message_body: e.target.value})}
                      required
                    />
                  </div>
                  <div className="flex justify-end gap-3">
                    <Button type="button" variant="outline" onClick={() => setShowComposeModal(false)}>Cancel</Button>
                    <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700">
                      <Send className="w-4 h-4 mr-2" /> Send
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        {/* View Message Modal */}
        {selectedMessage && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-2xl max-h-[90vh] overflow-auto">
              <CardHeader className="flex flex-row items-start justify-between">
                <div>
                  <CardTitle>{selectedMessage.subject || '(No Subject)'}</CardTitle>
                  <div className="text-sm text-slate-500 mt-1">
                    {selectedMessage.sender_id === user.id ? (
                      <span>To: {selectedMessage.recipient_name}</span>
                    ) : (
                      <span>From: {selectedMessage.sender_name}</span>
                    )}
                    <span className="mx-2">•</span>
                    <span>{new Date(selectedMessage.created_at).toLocaleString()}</span>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setSelectedMessage(null)}>
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-slate-50 p-4 rounded-lg whitespace-pre-wrap">
                  {selectedMessage.message_body}
                </div>
                
                {selectedMessage.sender_id !== user.id && (
                  <div className="space-y-3 border-t pt-4">
                    <Label>Reply</Label>
                    <textarea 
                      className="w-full border rounded-md p-2 min-h-[100px]" 
                      placeholder="Type your reply..." 
                      value={composeForm.message_body}
                      onChange={(e) => setComposeForm({...composeForm, message_body: e.target.value})}
                    />
                    <div className="flex justify-end">
                      <Button onClick={() => handleReply(selectedMessage)} className="bg-indigo-600 hover:bg-indigo-700">
                        <Reply className="w-4 h-4 mr-2" /> Send Reply
                      </Button>
                    </div>
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

export default CommunicationCenter;
