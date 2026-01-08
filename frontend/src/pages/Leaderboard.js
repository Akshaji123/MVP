import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { leaderboard as leaderboardAPI } from '../api/client';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Avatar } from '../components/ui/avatar';
import { Award, Trophy, Medal, TrendingUp, DollarSign, Briefcase } from 'lucide-react';

const Leaderboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await leaderboardAPI.get();
      setLeaderboard(response.data);
    } catch (error) {
      toast.error('Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return <Trophy className="w-6 h-6 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-6 h-6 text-slate-400" />;
    if (rank === 3) return <Medal className="w-6 h-6 text-orange-600" />;
    return <span className="text-lg font-bold text-slate-600">#{rank}</span>;
  };

  const getRankBg = (rank) => {
    if (rank === 1) return 'bg-gradient-to-r from-yellow-400 to-yellow-500';
    if (rank === 2) return 'bg-gradient-to-r from-slate-300 to-slate-400';
    if (rank === 3) return 'bg-gradient-to-r from-orange-400 to-orange-500';
    return 'bg-white';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Nav */}
      <nav className="border-b border-slate-200 bg-white/70 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-700 to-indigo-900 rounded-lg flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight" style={{fontFamily: 'Outfit, sans-serif'}}>Hiring referrals</span>
          </div>
          <Button data-testid="back-dashboard-btn" onClick={() => navigate('/')} variant="outline" className="border-slate-300">
            Back to Dashboard
          </Button>
        </div>
      </nav>

      {/* Header */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 mb-4">
            <Trophy className="w-12 h-12 text-lime-400" />
          </div>
          <h1 data-testid="leaderboard-heading" className="text-5xl font-bold tracking-tight mb-4" style={{fontFamily: 'Outfit, sans-serif'}}>
            Recruiter <span className="text-gradient">Leaderboard</span>
          </h1>
          <p className="text-lg text-slate-600">Top performers earning rewards through successful referrals</p>
        </div>

        {/* Top 3 Podium */}
        {leaderboard.length >= 3 && (
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {/* 2nd Place */}
            <div className="md:mt-8">
              <Card data-testid="rank-2-card" className="border-slate-300 shadow-lg overflow-hidden">
                <div className="h-2 bg-gradient-to-r from-slate-300 to-slate-400"></div>
                <CardContent className="pt-6 text-center">
                  <div className="w-20 h-20 bg-slate-100 rounded-full mx-auto mb-4 flex items-center justify-center">
                    <Medal className="w-10 h-10 text-slate-400" />
                  </div>
                  <div className="text-3xl font-bold mb-1" style={{fontFamily: 'Outfit, sans-serif'}}>#2</div>
                  <div className="text-lg font-semibold mb-2">{leaderboard[1].user_name}</div>
                  <div className="text-sm text-slate-600 mb-4">{leaderboard[1].role}</div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Referrals</span>
                      <span className="font-semibold">{leaderboard[1].total_referrals}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Successful</span>
                      <span className="font-semibold text-lime-600">{leaderboard[1].successful_referrals}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Earnings</span>
                      <span className="font-semibold text-indigo-600">₹{(leaderboard[1].total_earnings / 1000).toFixed(1)}k</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* 1st Place */}
            <div>
              <Card data-testid="rank-1-card" className="border-yellow-300 shadow-2xl overflow-hidden">
                <div className="h-3 bg-gradient-to-r from-yellow-400 to-yellow-500"></div>
                <CardContent className="pt-6 text-center">
                  <div className="w-24 h-24 bg-yellow-50 rounded-full mx-auto mb-4 flex items-center justify-center relative">
                    <Trophy className="w-12 h-12 text-yellow-500" />
                    <div className="absolute -top-2 -right-2 w-8 h-8 bg-lime-400 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold">1st</span>
                    </div>
                  </div>
                  <div className="text-4xl font-bold mb-2 text-gradient" style={{fontFamily: 'Outfit, sans-serif'}}>#1</div>
                  <div className="text-xl font-bold mb-2">{leaderboard[0].user_name}</div>
                  <div className="text-sm text-slate-600 mb-4">{leaderboard[0].role}</div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Referrals</span>
                      <span className="font-semibold">{leaderboard[0].total_referrals}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Successful</span>
                      <span className="font-semibold text-lime-600">{leaderboard[0].successful_referrals}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Earnings</span>
                      <span className="font-semibold text-indigo-600">₹{(leaderboard[0].total_earnings / 1000).toFixed(1)}k</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* 3rd Place */}
            <div className="md:mt-8">
              <Card data-testid="rank-3-card" className="border-orange-300 shadow-lg overflow-hidden">
                <div className="h-2 bg-gradient-to-r from-orange-400 to-orange-500"></div>
                <CardContent className="pt-6 text-center">
                  <div className="w-20 h-20 bg-orange-50 rounded-full mx-auto mb-4 flex items-center justify-center">
                    <Medal className="w-10 h-10 text-orange-600" />
                  </div>
                  <div className="text-3xl font-bold mb-1" style={{fontFamily: 'Outfit, sans-serif'}}>#3</div>
                  <div className="text-lg font-semibold mb-2">{leaderboard[2].user_name}</div>
                  <div className="text-sm text-slate-600 mb-4">{leaderboard[2].role}</div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Referrals</span>
                      <span className="font-semibold">{leaderboard[2].total_referrals}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Successful</span>
                      <span className="font-semibold text-lime-600">{leaderboard[2].successful_referrals}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-600">Earnings</span>
                      <span className="font-semibold text-indigo-600">₹{(leaderboard[2].total_earnings / 1000).toFixed(1)}k</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* Full Leaderboard */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Full Rankings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {leaderboard.map((entry) => (
                <div 
                  key={entry.user_id} 
                  data-testid={`leaderboard-entry-${entry.rank}`}
                  className={`flex items-center justify-between p-4 rounded-lg border ${
                    entry.rank <= 3 ? getRankBg(entry.rank) + ' border-transparent text-white' : 'bg-white border-slate-200'
                  } hover:shadow-md transition-shadow`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 flex items-center justify-center">
                      {getRankIcon(entry.rank)}
                    </div>
                    <div>
                      <div className={`font-semibold ${entry.rank <= 3 ? 'text-white' : 'text-slate-900'}`}>{entry.user_name}</div>
                      <div className={`text-sm ${entry.rank <= 3 ? 'text-white/80' : 'text-slate-600'}`}>{entry.role}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-8">
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${entry.rank <= 3 ? 'text-white' : 'text-slate-900'}`}>
                        {entry.total_referrals}
                      </div>
                      <div className={`text-xs ${entry.rank <= 3 ? 'text-white/80' : 'text-slate-600'}`}>Referrals</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${entry.rank <= 3 ? 'text-white' : 'text-lime-600'}`}>
                        {entry.successful_referrals}
                      </div>
                      <div className={`text-xs ${entry.rank <= 3 ? 'text-white/80' : 'text-slate-600'}`}>Successful</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${entry.rank <= 3 ? 'text-white' : 'text-indigo-600'}`}>
                        ₹{(entry.total_earnings / 1000).toFixed(1)}k
                      </div>
                      <div className={`text-xs ${entry.rank <= 3 ? 'text-white/80' : 'text-slate-600'}`}>Earnings</div>
                    </div>
                  </div>
                </div>
              ))}
              {leaderboard.length === 0 && (
                <div className="text-center py-12 text-slate-500">
                  No data yet. Start referring candidates to appear on the leaderboard!
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
};

export default Leaderboard;