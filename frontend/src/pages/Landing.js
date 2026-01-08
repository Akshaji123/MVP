import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, Users, TrendingUp, Award, Rocket, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/button';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Nav */}
      <nav className="border-b border-slate-200 bg-white/70 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <img 
              src="https://customer-assets.emergentagent.com/job_talentsphere-4/artifacts/2at054ix_Flat%20New%20Orange%20logo%20Transparent.png" 
              alt="Hiring Referrals Logo" 
              className="h-10 w-auto"
            />
          </div>
          <Button data-testid="nav-login-btn" onClick={() => navigate('/auth')} className="bg-indigo-700 hover:bg-indigo-800 text-white rounded-lg px-6">
            Sign In
          </Button>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 pt-24 pb-16">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 data-testid="hero-heading" className="text-5xl md:text-7xl font-bold tracking-tighter mb-6" style={{fontFamily: 'Outfit, sans-serif'}}>
              AI-Powered
              <br />
              <span className="bg-gradient-to-r from-indigo-700 to-lime-400 bg-clip-text text-transparent">
                Hiring Platform
              </span>
            </h1>
            <p className="text-lg text-slate-600 mb-8 leading-relaxed" style={{fontFamily: 'Satoshi, sans-serif'}}>
              Transform your recruitment process with intelligent resume parsing, AI-powered matching, 
              and gamified referral rewards. Reduce hiring time by 70%.
            </p>
            <div className="flex gap-4">
              <Button data-testid="hero-getstarted-btn" onClick={() => navigate('/auth')} size="lg" className="bg-indigo-700 hover:bg-indigo-800 text-white rounded-lg px-8 hover:scale-105 transition-transform">
                Get Started
              </Button>
              <Button data-testid="hero-leaderboard-btn" onClick={() => navigate('/leaderboard')} size="lg" variant="outline" className="border-slate-300 rounded-lg px-8 hover:border-indigo-700 hover:scale-105 transition-transform">
                View Leaderboard
              </Button>
            </div>
          </div>
          <div className="relative">
            <img 
              src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&q=80&w=800" 
              alt="Team collaboration" 
              className="rounded-2xl shadow-2xl hover-lift"
            />
            <div className="absolute -bottom-6 -left-6 bg-white rounded-xl shadow-xl p-4 border border-slate-200">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-lime-400 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-slate-900" />
                </div>
                <div>
                  <div className="text-2xl font-bold" style={{fontFamily: 'Outfit, sans-serif'}}>70%</div>
                  <div className="text-sm text-slate-600">Faster Hiring</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="bg-white border-t border-slate-200 py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-4xl font-bold text-center mb-16" style={{fontFamily: 'Outfit, sans-serif'}}>Platform Features</h2>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { icon: <Briefcase className="w-8 h-8" />, title: 'Smart Job Posting', desc: 'AI-generated job descriptions optimized for maximum reach' },
              { icon: <Users className="w-8 h-8" />, title: 'Resume Parsing', desc: 'Extract skills, experience, and qualifications automatically' },
              { icon: <TrendingUp className="w-8 h-8" />, title: 'AI Matching', desc: 'Score candidates based on job requirements with 95% accuracy' },
              { icon: <Award className="w-8 h-8" />, title: 'Gamified Rewards', desc: 'Leaderboards and instant payouts for successful referrals' },
            ].map((feature, idx) => (
              <div key={idx} className="bg-slate-50 rounded-xl p-8 border border-slate-200 hover-lift cursor-pointer" data-testid={`feature-card-${idx}`}>
                <div className="w-16 h-16 bg-indigo-100 rounded-lg flex items-center justify-center mb-4 text-indigo-700">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-3" style={{fontFamily: 'Outfit, sans-serif'}}>{feature.title}</h3>
                <p className="text-slate-600 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { value: '50K+', label: 'Active Jobs' },
              { value: '1M+', label: 'Candidates' },
              { value: '₹100Cr+', label: 'Rewards Paid' },
            ].map((stat, idx) => (
              <div key={idx} className="text-center" data-testid={`stat-${idx}`}>
                <div className="text-6xl font-black mb-2" style={{fontFamily: 'Outfit, sans-serif', color: '#4338ca'}}>{stat.value}</div>
                <div className="text-lg text-slate-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-br from-indigo-700 to-indigo-900 py-24">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6" style={{fontFamily: 'Outfit, sans-serif'}}>
            Ready to Transform Your Hiring?
          </h2>
          <p className="text-indigo-100 text-lg mb-8">
            Join thousands of companies and recruiters using AI to hire faster and smarter.
          </p>
          <Button data-testid="cta-getstarted-btn" onClick={() => navigate('/auth')} size="lg" className="bg-lime-400 hover:bg-lime-500 text-slate-900 font-semibold rounded-lg px-12 hover:scale-105 transition-transform">
            Get Started Free
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p>© 2025 Hiring referrals. Powered by AI.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;