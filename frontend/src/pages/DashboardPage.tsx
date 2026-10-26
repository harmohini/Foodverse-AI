import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Zap, Leaf, Eye, ChefHat, Calendar, ArrowRight, Upload, Clock, Sparkles } from 'lucide-react';
import { getHistory } from '@/services/api';
import type { HistoryItem } from '@/types';
import { EmptyState, LoadingSpinner } from '@/components/common';
import { format } from '../utils/date';

const FEATURES = [
  { to: '/food', icon: Search, label: 'Food Recognition', desc: 'Identify dishes from photos', color: 'bg-forest-50 text-forest-500' },
  { to: '/nutrition', icon: Zap, label: 'Nutrition Analysis', desc: 'Estimate macros & calories', color: 'bg-amber-50 text-amber-600' },
  { to: '/freshness', icon: Leaf, label: 'Freshness Check', desc: 'Visual spoilage assessment', color: 'bg-emerald-50 text-emerald-600' },
  { to: '/hygiene', icon: Eye, label: 'Hygiene Monitor', desc: 'Kitchen safety from video', color: 'bg-blue-50 text-blue-600' },
  { to: '/cooking', icon: ChefHat, label: 'Smart Cooking', desc: 'Generate recipes & get help', color: 'bg-purple-50 text-purple-600' },
  { to: '/meal-planner', icon: Calendar, label: 'Meal Planner', desc: 'Create personalised plans', color: 'bg-rose-50 text-rose-600' },
];

const ANALYSIS_TYPE_LABELS: Record<string, string> = {
  food_recognition: 'Food Recognition',
  nutrition: 'Nutrition Analysis',
  freshness: 'Freshness Check',
  hygiene: 'Hygiene Monitor',
  cooking: 'Recipe Generated',
};

export default function DashboardPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory(6)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-8 fade-in">
      {/* Hero */}
      <div className="bg-white rounded-3xl p-8 border border-forest-50 shadow-card relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-forest-50 rounded-full -translate-y-32 translate-x-32 opacity-60" />
        <div className="relative">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-forest-50 text-forest-500 text-xs font-semibold mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            Multimodal Food Intelligence
          </div>
          <h1 className="font-display text-3xl font-bold text-charcoal-900 leading-tight">
            Your food,<br />understood better.
          </h1>
          <p className="text-charcoal-100 mt-3 max-w-lg">
            Analyse nutrition, check freshness, and make smarter food decisions — all from images, video, and text.
          </p>
          <div className="flex gap-3 mt-6">
            <Link to="/food" className="btn-primary" id="hero-start-btn">
              <Upload className="w-4 h-4" />
              Analyse Food
            </Link>
            <Link to="/meal-planner" className="btn-secondary" id="hero-plan-btn">
              <Calendar className="w-4 h-4" />
              Plan Meals
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="section-title mb-4">Six Core Capabilities</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {FEATURES.map(({ to, icon: Icon, label, desc, color }) => (
            <Link
              key={to}
              to={to}
              id={`feature-${to.replace('/', '')}`}
              className="card-hover flex flex-col gap-3"
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <p className="font-semibold text-charcoal-900 text-sm">{label}</p>
                <p className="text-xs text-charcoal-100 mt-0.5">{desc}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-charcoal-100 mt-auto" />
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Analyses */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Recent Analyses</h2>
            <Link to="/history" className="text-sm text-forest-500 font-medium hover:underline">
              View all
            </Link>
          </div>
          {loading ? (
            <LoadingSpinner message="Loading history…" size="sm" />
          ) : history.length === 0 ? (
            <EmptyState
              icon={<Clock className="w-7 h-7" />}
              title="No analyses yet"
              description="Your recent food analyses will appear here once you start using the app."
              action={
                <Link to="/food" className="btn-primary text-sm px-4 py-2">
                  Start with Food Recognition
                </Link>
              }
            />
          ) : (
            <div className="space-y-3">
              {history.map((item) => (
                <div key={item.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-cream-100 transition-colors">
                  <div className="w-8 h-8 rounded-lg bg-forest-50 flex items-center justify-center flex-shrink-0">
                    <Clock className="w-4 h-4 text-forest-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-charcoal-900 truncate">
                      {item.food_name || ANALYSIS_TYPE_LABELS[item.analysis_type] || item.analysis_type}
                    </p>
                    <p className="text-xs text-charcoal-100">
                      {ANALYSIS_TYPE_LABELS[item.analysis_type]} · {format(item.created_at)}
                    </p>
                  </div>
                  {item.is_demo && (
                    <span className="badge-demo text-xs">Demo</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* How it works */}
        <div className="card">
          <h2 className="section-title mb-4">How FoodVerse Works</h2>
          <div className="space-y-4">
            {[
              { step: '01', title: 'Upload or Describe', desc: 'Provide an image, video, or type a food/dish name.' },
              { step: '02', title: 'AI Analysis', desc: 'FoodVerse processes your input using vision models and LLMs.' },
              { step: '03', title: 'Structured Results', desc: 'Receive nutrition estimates, freshness assessments, or recipes.' },
              { step: '04', title: 'Save & Plan', desc: 'History is saved locally. Use insights in your meal planner.' },
            ].map(({ step, title, desc }) => (
              <div key={step} className="flex gap-4">
                <div className="w-8 h-8 rounded-lg bg-forest-500 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {step}
                </div>
                <div>
                  <p className="text-sm font-semibold text-charcoal-900">{title}</p>
                  <p className="text-xs text-charcoal-100 mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
