import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Trash2, Search, RefreshCw, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { getHistory, deleteHistoryItem } from '@/services/api';
import type { HistoryItem } from '@/types';
import { LoadingSpinner, SectionHeader } from '@/components/common';
import { format } from '@/utils/date';

const TYPE_BADGES: Record<string, string> = {
  food_recognition: 'bg-forest-50 text-forest-500',
  nutrition: 'bg-amber-50 text-amber-600',
  freshness: 'bg-emerald-50 text-emerald-600',
  hygiene: 'bg-blue-50 text-blue-600',
  cooking: 'bg-purple-50 text-purple-600',
};

const TYPE_LABELS: Record<string, string> = {
  food_recognition: 'Food Recognition',
  nutrition: 'Nutrition',
  freshness: 'Freshness',
  hygiene: 'Hygiene',
  cooking: 'Cooking',
};

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    setError('');
    getHistory(100)
      .then(setItems)
      .catch((e) => setError(e.message || 'Failed to load history.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  async function handleDelete(analysisId: string) {
    try {
      await deleteHistoryItem(analysisId);
      setItems((prev) => prev.filter((i) => i.analysis_id !== analysisId));
      toast.success('Record deleted.');
    } catch {
      toast.error('Could not delete record.');
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 fade-in">
      <SectionHeader
        title="Analysis History"
        subtitle="All your completed food analyses, stored locally."
        action={
          <button
            id="refresh-history-btn"
            onClick={load}
            disabled={loading}
            className="btn-secondary text-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'spinner' : ''}`} />
            Refresh
          </button>
        }
      />

      {loading ? (
        <LoadingSpinner message="Loading history…" />
      ) : error ? (
        <div className="card">
          <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-800">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        </div>
      ) : items.length === 0 ? (
        /* ── Clean empty state — no demo or mock data ── */
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-forest-50 flex items-center justify-center mb-4">
            <Clock className="w-8 h-8 text-forest-500" />
          </div>
          <h3 className="font-semibold text-charcoal-900 text-lg">No analysis history yet</h3>
          <p className="text-sm text-charcoal-100 mt-2 max-w-xs">
            Your completed food analyses will appear here once you use any of the six features.
          </p>
          <Link
            to="/food"
            id="history-start-btn"
            className="btn-primary mt-6"
          >
            <Search className="w-4 h-4" />
            Start Analysing
          </Link>
        </div>
      ) : (
        <div className="card divide-y divide-gray-50">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-3 py-3 hover:bg-cream-100 -mx-6 px-6 transition-colors group first:rounded-t-2xl last:rounded-b-2xl"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-medium text-charcoal-900 truncate">
                    {item.food_name || TYPE_LABELS[item.analysis_type] || item.analysis_type}
                  </p>
                  {item.is_demo && (
                    <span className="badge-demo text-xs">Demo</span>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TYPE_BADGES[item.analysis_type] || 'bg-gray-50 text-gray-600'}`}>
                    {TYPE_LABELS[item.analysis_type] || item.analysis_type}
                  </span>
                  <span className="text-xs text-charcoal-100">{item.input_type}</span>
                  <span className="text-xs text-charcoal-100">·</span>
                  <span className="text-xs text-charcoal-100">{format(item.created_at)}</span>
                </div>
              </div>
              <button
                id={`delete-history-${item.analysis_id}`}
                onClick={() => handleDelete(item.analysis_id)}
                className="btn-ghost p-1.5 text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Info note */}
      {!loading && !error && items.length > 0 && (
        <div className="info-box text-xs">
          <span>
            History is saved locally in the SQLite database and persists across restarts.
            Demo-mode results are labelled <strong>Demo</strong>. Live AI results have no label.
            Delete individual records using the trash icon.
          </span>
        </div>
      )}
    </div>
  );
}
