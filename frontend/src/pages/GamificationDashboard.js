import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import api from '../api/client';
import { 
  Trophy, 
  Star, 
  Flame, 
  Medal, 
  Target, 
  TrendingUp,
  Crown,
  Award,
  Zap,
  Gift,
  Users,
  ChevronUp
} from 'lucide-react';

const TIER_COLORS = {
  'Bronze': 'bg-amber-600',
  'Silver': 'bg-slate-400',
  'Gold': 'bg-yellow-500',
  'Platinum': 'bg-slate-300',
  'Diamond': 'bg-cyan-400'
};

const TIER_ICONS = {
  'Bronze': Medal,
  'Silver': Trophy,
  'Gold': Crown,
  'Platinum': Star,
  'Diamond': Zap
};

const GamificationDashboard = ({ user }) => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [allAchievements, setAllAchievements] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [streakUpdated, setStreakUpdated] = useState(false);

  useEffect(() => {
    if (user?.id) {
      fetchGamificationData();
    }
  }, [user]);

  const fetchGamificationData = async () => {
    setLoading(true);
    try {
      const [statsRes, achievementsRes, leaderboardRes] = await Promise.all([
        api.get(`/gamification/user/${user.id}/stats`),
        api.get('/gamification/achievements'),
        api.get('/gamification/leaderboard?limit=10')
      ]);
      
      setStats(statsRes.data);
      setAllAchievements(achievementsRes.data);
      setLeaderboard(leaderboardRes.data);
    } catch (error) {
      console.error('Error fetching gamification data:', error);
      toast.error('Failed to load gamification data');
    } finally {
      setLoading(false);
    }
  };

  const updateStreak = async () => {
    try {
      const response = await api.post(`/gamification/user/${user.id}/streak/update`);
      if (response.data.updated) {
        toast.success(`Streak updated! Current streak: ${response.data.current_streak} days`);
        setStreakUpdated(true);
        fetchGamificationData();
      } else {
        toast.info(response.data.message || 'Streak already updated today');
      }
    } catch (error) {
      toast.error('Failed to update streak');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const currentTier = stats?.points?.current_tier;
  const nextTier = stats?.points?.next_tier;
  const totalPoints = stats?.points?.total_points || 0;
  const currentLevel = stats?.points?.current_level;
  const streak = stats?.streak;
  const userAchievements = stats?.achievements?.recent || [];

  const progressToNextTier = nextTier 
    ? Math.min(100, ((totalPoints - (currentTier?.point_threshold || 0)) / (nextTier.point_threshold - (currentTier?.point_threshold || 0))) * 100)
    : 100;

  const TierIcon = TIER_ICONS[currentTier?.name] || Trophy;

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Points & Tier Card */}
        <Card className="md:col-span-2 bg-gradient-to-br from-indigo-600 to-purple-700 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-indigo-200 text-sm font-medium">Total Points</p>
                <h2 className="text-4xl font-bold mt-1">{totalPoints.toLocaleString()}</h2>
                <div className="flex items-center gap-2 mt-3">
                  <Badge className={`${TIER_COLORS[currentTier?.name] || 'bg-slate-500'} text-white`}>
                    <TierIcon className="w-3 h-3 mr-1" />
                    {currentTier?.name || 'Bronze'} Tier
                  </Badge>
                  {currentLevel && (
                    <Badge variant="secondary" className="bg-white/20 text-white">
                      {currentLevel.name}
                    </Badge>
                  )}
                </div>
              </div>
              <div className="text-right">
                <TierIcon className="w-16 h-16 text-white/30" />
              </div>
            </div>
            
            {nextTier && (
              <div className="mt-4">
                <div className="flex justify-between text-sm text-indigo-200 mb-1">
                  <span>Progress to {nextTier.name}</span>
                  <span>{nextTier.point_threshold - totalPoints} pts needed</span>
                </div>
                <Progress value={progressToNextTier} className="h-2 bg-white/20" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Streak Card */}
        <Card className="bg-gradient-to-br from-orange-500 to-red-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-200 text-sm font-medium">Current Streak</p>
                <h2 className="text-3xl font-bold mt-1">{streak?.current_streak || 0} days</h2>
                <p className="text-orange-200 text-xs mt-1">Max: {streak?.max_streak || 0} days</p>
              </div>
              <Flame className="w-12 h-12 text-white/30" />
            </div>
            <Button 
              onClick={updateStreak}
              variant="secondary"
              size="sm"
              className="mt-3 bg-white/20 hover:bg-white/30 text-white w-full"
              disabled={streakUpdated}
            >
              {streakUpdated ? 'Updated Today' : 'Check In Today'}
            </Button>
            {streak?.streak_freeze_available && (
              <Badge className="mt-2 bg-blue-500 text-white">
                <Zap className="w-3 h-3 mr-1" />
                Streak Freeze Available
              </Badge>
            )}
          </CardContent>
        </Card>

        {/* Achievements Count */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-500 text-sm font-medium">Achievements</p>
                <h2 className="text-3xl font-bold mt-1 text-slate-900">
                  {stats?.achievements?.total || 0}
                </h2>
                <p className="text-slate-400 text-xs mt-1">of {allAchievements.length} total</p>
              </div>
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
                <Award className="w-6 h-6 text-indigo-600" />
              </div>
            </div>
            <Progress 
              value={allAchievements.length ? ((stats?.achievements?.total || 0) / allAchievements.length) * 100 : 0} 
              className="h-2 mt-4" 
            />
          </CardContent>
        </Card>
      </div>

      {/* Tabs for Achievements and Leaderboard */}
      <Tabs defaultValue="achievements" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="achievements">
            <Trophy className="w-4 h-4 mr-2" />
            Achievements
          </TabsTrigger>
          <TabsTrigger value="leaderboard">
            <Users className="w-4 h-4 mr-2" />
            Leaderboard
          </TabsTrigger>
          <TabsTrigger value="rewards">
            <Gift className="w-4 h-4 mr-2" />
            Rewards
          </TabsTrigger>
        </TabsList>

        {/* Achievements Tab */}
        <TabsContent value="achievements" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allAchievements.map((achievement) => {
              const isEarned = userAchievements.some(ua => ua.achievement_id === achievement.id);
              return (
                <Card 
                  key={achievement.id} 
                  className={`transition-all ${isEarned ? 'border-green-500 bg-green-50' : 'opacity-60'}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                        isEarned ? 'bg-green-500 text-white' : 'bg-slate-200 text-slate-400'
                      }`}>
                        {achievement.tier === 1 && <Medal className="w-6 h-6" />}
                        {achievement.tier === 2 && <Trophy className="w-6 h-6" />}
                        {achievement.tier === 3 && <Crown className="w-6 h-6" />}
                        {achievement.tier >= 4 && <Star className="w-6 h-6" />}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-slate-900">{achievement.name}</h4>
                        <p className="text-sm text-slate-500 mt-1">{achievement.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="text-xs">
                            +{achievement.points} pts
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            Tier {achievement.tier}
                          </Badge>
                          {isEarned && (
                            <Badge className="bg-green-500 text-white text-xs">
                              Earned!
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="w-5 h-5 text-yellow-500" />
                Top Performers
              </CardTitle>
              <CardDescription>Users ranked by total points</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {leaderboard.map((entry, index) => (
                  <div 
                    key={entry.user_id} 
                    className={`flex items-center gap-4 p-3 rounded-lg ${
                      entry.user_id === user.id ? 'bg-indigo-50 border border-indigo-200' : 'bg-slate-50'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                      index === 0 ? 'bg-yellow-500 text-white' :
                      index === 1 ? 'bg-slate-400 text-white' :
                      index === 2 ? 'bg-amber-600 text-white' :
                      'bg-slate-200 text-slate-600'
                    }`}>
                      {entry.rank}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-slate-900">
                        {entry.username || entry.email?.split('@')[0] || 'Anonymous'}
                        {entry.user_id === user.id && (
                          <Badge className="ml-2 bg-indigo-500 text-white text-xs">You</Badge>
                        )}
                      </p>
                      <p className="text-sm text-slate-500">{entry.current_tier}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-indigo-600">{entry.total_points?.toLocaleString()} pts</p>
                    </div>
                  </div>
                ))}
                
                {leaderboard.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No users on the leaderboard yet</p>
                    <p className="text-sm">Start earning points to appear here!</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rewards Tab */}
        <TabsContent value="rewards" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {currentTier?.rewards?.map((reward, index) => (
              <Card key={index} className="border-green-200 bg-green-50">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center">
                      <Gift className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-green-800">{reward.name}</h4>
                      <p className="text-sm text-green-600 capitalize">{reward.type}</p>
                    </div>
                    <Badge className="ml-auto bg-green-500 text-white">Active</Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {nextTier?.rewards?.filter(r => !currentTier?.rewards?.some(cr => cr.id === r.id)).map((reward, index) => (
              <Card key={`next-${index}`} className="border-slate-200 opacity-60">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-slate-300 text-slate-500 rounded-full flex items-center justify-center">
                      <Gift className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-600">{reward.name}</h4>
                      <p className="text-sm text-slate-500 capitalize">{reward.type}</p>
                    </div>
                    <Badge variant="outline" className="ml-auto">
                      <ChevronUp className="w-3 h-3 mr-1" />
                      {nextTier.name} Tier
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}

            {(!currentTier?.rewards || currentTier.rewards.length === 0) && (!nextTier?.rewards || nextTier.rewards.length === 0) && (
              <div className="col-span-2 text-center py-8 text-slate-500">
                <Gift className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Keep earning points to unlock rewards!</p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Commission Rate Info */}
      {currentLevel && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-500" />
              Your Commission Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <div>
                <p className="text-sm text-green-700">Current Level: {currentLevel.name}</p>
                <p className="text-2xl font-bold text-green-800">{(currentLevel.commission_rate * 100).toFixed(1)}%</p>
              </div>
              <div 
                className="w-16 h-16 rounded-full border-4 flex items-center justify-center"
                style={{ borderColor: currentLevel.color }}
              >
                <Target className="w-8 h-8" style={{ color: currentLevel.color }} />
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GamificationDashboard;
