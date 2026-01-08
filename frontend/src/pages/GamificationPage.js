import DashboardLayout from '../components/DashboardLayout';
import GamificationDashboard from './GamificationDashboard';

const GamificationPage = ({ user, onLogout }) => {
  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="p-6">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Gamification & Rewards</h1>
        <GamificationDashboard user={user} />
      </div>
    </DashboardLayout>
  );
};

export default GamificationPage;
