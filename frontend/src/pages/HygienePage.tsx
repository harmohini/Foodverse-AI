import { useState } from 'react';
import { Eye, CheckCircle2, XCircle, HelpCircle, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import { analyzeHygiene } from '@/services/api';
import type { HygieneReport, HygieneIndicator } from '@/types';
import { VideoUploadZone } from '@/components/upload/UploadZone';
import { AnalysisLoadingCard, ErrorAlert, DemoModeBanner, SectionHeader } from '@/components/common';
import clsx from 'clsx';

const STATUS_ICONS = {
  observed: { icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  not_observed: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50' },
  unable_to_assess: { icon: HelpCircle, color: 'text-charcoal-100', bg: 'bg-gray-50' },
};

function IndicatorRow({ ind }: { ind: HygieneIndicator }) {
  const cfg = STATUS_ICONS[ind.status as keyof typeof STATUS_ICONS] || STATUS_ICONS.unable_to_assess;
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl bg-cream-100">
      <div className={clsx('w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0', cfg.bg)}>
        <cfg.icon className={clsx('w-4 h-4', cfg.color)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-charcoal-900">{ind.indicator}</p>
        <p className="text-xs text-charcoal-100 mt-0.5">{ind.evidence || 'No evidence captured.'}</p>
        {ind.timestamp_seconds !== undefined && ind.timestamp_seconds !== null && (
          <span className="text-xs text-charcoal-100 mt-0.5 block">@ {ind.timestamp_seconds.toFixed(1)}s</span>
        )}
      </div>
      <span className={clsx(
        'text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0',
        ind.status === 'observed' ? 'bg-emerald-100 text-emerald-700' :
        ind.status === 'not_observed' ? 'bg-red-100 text-red-700' :
        'bg-gray-100 text-gray-600'
      )}>
        {ind.status.replace(/_/g, ' ')}
      </span>
    </div>
  );
}

export default function HygienePage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<HygieneReport | null>(null);

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
      const res = await analyzeHygiene(file);
      setResult(res);
      toast.success('Hygiene report generated!');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Analysis failed.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 fade-in">
      <SectionHeader
        title="Restaurant Hygiene Monitor"
        subtitle="Upload a kitchen or food-service video to identify visible hygiene indicators."
      />

      {/* Upload */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-charcoal-900">Upload Kitchen Video</h3>
        <VideoUploadZone
          onFile={handleFile}
          preview={preview}
          onError={(msg) => { setError(msg); toast.error(msg); }}
        />
        {error && <ErrorAlert message={error} />}
        <button
          id="analyse-hygiene-btn"
          onClick={handleAnalyse}
          disabled={!file || loading}
          className="btn-primary"
        >
          <Eye className="w-4 h-4" />
          {loading ? 'Analysing Video…' : 'Generate Hygiene Report'}
        </button>
      </div>

      {/* Result */}
      {loading ? (
        <AnalysisLoadingCard message="Extracting frames and analysing hygiene indicators…" />
      ) : result ? (
        <div className="space-y-6 fade-in">
          <DemoModeBanner isDemo={result.metadata.is_demo} />

          {/* Summary */}
          <div className="card">
            <h3 className="font-semibold text-charcoal-900 mb-1">{result.overall_assessment}</h3>
            <p className="text-sm text-charcoal-100">
              {result.frames_analyzed} frames analysed
              {result.duration_seconds ? ` · Video duration: ${result.duration_seconds.toFixed(0)}s` : ''}
            </p>
          </div>

          {/* Indicators */}
          <div className="card">
            <h3 className="font-semibold text-charcoal-900 mb-4">Hygiene Indicators Observed</h3>
            <div className="space-y-2">
              {result.indicators.map((ind, i) => (
                <IndicatorRow key={i} ind={ind} />
              ))}
              {result.indicators.length === 0 && (
                <p className="text-sm text-charcoal-100 text-center py-4">No indicators assessed.</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Limitations */}
            {result.limitations.length > 0 && (
              <div className="card">
                <h3 className="font-semibold text-charcoal-900 mb-3">Limitations</h3>
                <ul className="space-y-1.5">
                  {result.limitations.map((l, i) => (
                    <li key={i} className="text-sm text-charcoal-500 flex items-start gap-2">
                      <span className="text-charcoal-100 mt-0.5">•</span>{l}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Corrective Actions */}
            {result.corrective_actions.length > 0 && (
              <div className="card">
                <h3 className="font-semibold text-charcoal-900 mb-3">Suggested Actions</h3>
                <ul className="space-y-1.5">
                  {result.corrective_actions.map((a, i) => (
                    <li key={i} className="text-sm text-charcoal-500 flex items-start gap-2">
                      <span className="text-forest-500 font-bold mt-0.5">→</span>{a}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Disclaimer */}
          <div className="warning-box text-xs">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>{result.disclaimer}</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}
