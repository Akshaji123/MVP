import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import axios from 'axios';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Download, Database, Code, FileArchive, RefreshCw } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const EnterpriseAdmin = ({ user, onLogout }) => {
  const [backups, setBackups] = useState([]);
  const [exports, setExports] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDownloads();
  }, []);

  const fetchDownloads = async () => {
    try {
      const token = localStorage.getItem('token');
      const [backupsRes, exportsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/admin/backups`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${BACKEND_URL}/api/admin/exports`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setBackups(backupsRes.data);
      setExports(exportsRes.data);
    } catch (error) {
      toast.error('Failed to load downloads');
    }
  };

  const createBackup = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${BACKEND_URL}/api/admin/backup`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Database backup created successfully!');
      fetchDownloads();
    } catch (error) {
      toast.error('Backup creation failed');
    } finally {
      setLoading(false);
    }
  };

  const exportCode = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${BACKEND_URL}/api/admin/export-code`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Code exported successfully!');
      fetchDownloads();
    } catch (error) {
      toast.error('Code export failed');
    } finally {
      setLoading(false);
    }
  };

  const downloadFile = (type, filename) => {
    const token = localStorage.getItem('token');
    const url = `${BACKEND_URL}/api/admin/${type}/${filename}/download?token=${token}`;
    window.open(url, '_blank');
  };

  const formatFileSize = (bytes) => {
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-8" data-testid="enterprise-admin">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2" style={{fontFamily: 'Outfit, sans-serif'}}>
            Enterprise Admin
          </h1>
          <p className="text-slate-600">Manage backups, exports, and system data</p>
        </div>

        {/* Actions */}
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="border-indigo-200 bg-indigo-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5 text-indigo-700" />
                Database Backup
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600 mb-4">
                Create a complete backup of all platform data including users, jobs, applications, and more.
              </p>
              <Button 
                data-testid="create-backup-btn"
                onClick={createBackup} 
                disabled={loading}
                className="bg-indigo-700 hover:bg-indigo-800 w-full"
              >
                {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Database className="w-4 h-4 mr-2" />}
                Create Backup
              </Button>
            </CardContent>
          </Card>

          <Card className="border-lime-200 bg-lime-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="w-5 h-5 text-lime-700" />
                Code Export
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600 mb-4">
                Export the entire codebase (backend + frontend) as a downloadable ZIP archive.
              </p>
              <Button 
                data-testid="export-code-btn"
                onClick={exportCode} 
                disabled={loading}
                className="bg-lime-600 hover:bg-lime-700 w-full"
              >
                {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Code className="w-4 h-4 mr-2" />}
                Export Code
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Database Backups */}
        <Card className="border-slate-200">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Database Backups</CardTitle>
            <Button variant="outline" size="sm" onClick={fetchDownloads}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {backups.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                No backups available. Create your first backup above.
              </div>
            ) : (
              <div className="space-y-3">
                {backups.map((backup, idx) => (
                  <div key={idx} data-testid={`backup-${idx}`} className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50">
                    <div className="flex items-center gap-3">
                      <FileArchive className="w-8 h-8 text-indigo-600" />
                      <div>
                        <div className="font-semibold">{backup.name}</div>
                        <div className="text-sm text-slate-600">
                          {formatFileSize(backup.size)} • {new Date(backup.created).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <Button 
                      data-testid={`download-backup-${idx}`}
                      size="sm" 
                      onClick={() => downloadFile('backups', backup.name)}
                      className="bg-indigo-700 hover:bg-indigo-800"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Code Exports */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Code Exports</CardTitle>
          </CardHeader>
          <CardContent>
            {exports.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                No code exports available. Create your first export above.
              </div>
            ) : (
              <div className="space-y-3">
                {exports.map((exp, idx) => (
                  <div key={idx} data-testid={`export-${idx}`} className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50">
                    <div className="flex items-center gap-3">
                      <Code className="w-8 h-8 text-lime-600" />
                      <div>
                        <div className="font-semibold">{exp.name}</div>
                        <div className="text-sm text-slate-600">
                          {formatFileSize(exp.size)} • {new Date(exp.created).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <Button 
                      data-testid={`download-export-${idx}`}
                      size="sm" 
                      onClick={() => downloadFile('exports', exp.name)}
                      className="bg-lime-600 hover:bg-lime-700"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
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

export default EnterpriseAdmin;