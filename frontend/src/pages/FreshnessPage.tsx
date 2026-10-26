import { useState } from 'react';
import { Leaf, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { analyzeFreshness } from '@/services/api';
import type { FreshnessResult } from '@/types';
import { ImageUploadZone } from '@/components/upload/UploadZone';
import { AnalysisLoadingCard, ErrorAlert, DemoModeBanner, ConfidenceBadge, SectionHeader } from '@/components/common';
import clsx from 'clsx';

const STATUS_CONFIG = {
  'Fresh': { icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200', badge: 'badge-fresh' },
  'Moderately Fresh': { icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200', badge: 'badge-moderate' },
  'Possible Spoilage': { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50 border-red-200', badge: 'badge-spoilage' },
};

const SEVERITY_COLORS = {
  normal: 'text-emerald-700 bg-emerald-50',
  mild: 'text-amber-700 bg-amber-50',
  concerning: 'text-red-700 bg-red-50',
};

export default function FreshnessPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [foodCategory, setFoodCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<FreshnessResult | null>(null);

  function handleFile(f: File) {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError('');
  }

  async function handleAnalyse() {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const res = await analyzeFreshness(file, foodCategory);
      setResult(res);
      toast.success('Freshness assessment complete!');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Analysis failed.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  const statusCfg = result ? STATUS_CONFIG[result.status as keyof typeof STATUS_CONFIG] : null;

  return (
    <div className="max-w-4xl mx-auto space-y-6 fade-in">
      <SectionHeader
        title="Food Freshness Check"
        subtitle="Upload a photo of your food to assess visible freshness indicators."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload */}
        <div className="card space-y-4">
          <h3 className="font-semibold text-charcoal-900">Upload Food Image</h3>
          <ImageUploadZone
            onFile={handleFile}
            preview={preview}
            label="Drop a fruit, vegetable, or food photo"
            onError={(msg) => { setError(msg); toast.error(msg); }}
          />
          <div>
            <label className="label" htmlFor="food-category">Food Category (optional)</label>
            <select
              id="food-category"
              className="select"
              value={foodCategory}
              onChange={(e) => setFoodCategory(e.target.value)}
            >
              <option value="">Auto-detect</option>
              <option>Fruit</option>
              <option>Vegetables</option>
              <option>Meat & Poultry</option>
              <option>Fish & Seafood</option>
              <option>Dairy</option>
              <option>Bread & Bakery</option>
              <option>Cooked Meals</option>
              <option>Other</option>
            </select>
          </div>
          {error && <ErrorAlert message={error} />}
          <button
            id="analyse-freshness-btn"
            onClick={handleAnalyse}
            disabled={!file || loading}
            className="btn-primary w-full"
          >
            <Leaf className="w-4 h-4" />
            {loading ? 'Assessing…' : 'Assess Freshness'}
          </button>
        </div>

        {/* Result */}
        <div className="space-y-4">
          {loading ? (
            <AnalysisLoadingCard message="Assessing freshness indicators…" />
          ) : result && statusCfg ? (
            <div className="space-y-4 fade-in">
              <DemoModeBanner isDemo={result.metadata.is_demo} />

              {/* Status banner */}
              <div className={clsx('card border', statusCfg.bg)}>
                <div className="flex items-center gap-3 mb-3">
                  <statusCfg.icon className={clsx('w-7 h-7', statusCfg.color)} />
                  <div>
                    <p className="font-bold text-lg font-display text-charcoal-900">{result.status}</p>
                    <p className="text-sm text-charcoal-100">{result.food_category}</p>
                  </div>
                  <ConfidenceBadge confidence={result.confidence} />
                </div>
              </div>

              {/* Observations */}
              {result.observations.length > 0 && (
                <div className="card">
                  <h3 className="font-semibold text-charcoal-900 mb-3">Visual Observations</h3>
                  <div className="space-y-2">
                    {result.observations.map((obs, i) => (
                      <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-cream-100">
                        <span className={clsx('px-2 py-0.5 rounded text-xs font-medium flex-shrink-0', SEVERITY_COLORS[obs.severity])}>
                          {obs.characteristic}
                        </span>
                        <p className="text-sm text-charcoal-500">{obs.observation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Next steps */}
              {result.next_steps.length > 0 && (
                <div className="card">
                  <h3 className="font-semibold text-charcoal-900 mb-3">Recommended Next Steps</h3>
                  <ul className="space-y-2">
                    {result.next_steps.map((step, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-charcoal-500">
                        <span className="w-5 h-5 rounded-full bg-forest-50 text-forest-500 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                          {i + 1}
                        </span>
                        {step}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Safety disclaimer */}
              <div className="warning-box text-xs">
                <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <span>{result.safety_disclaimer}</span>
              </div>
            </div>
          ) : (
            <div className="card flex flex-col items-center py-12 text-center">
              <div className="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center mb-4">
                <Leaf className="w-7 h-7 text-emerald-600" />
              </div>
              <p className="font-semibold text-charcoal-900">Upload to check freshness</p>
              <p className="text-sm text-charcoal-100 mt-1">Results include visual observations and practical next steps.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
