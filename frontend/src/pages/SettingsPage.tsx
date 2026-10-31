import { useEffect, useState } from 'react';
import { Settings, Server, Database, Wifi, WifiOff, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';
import { getHealth, getProviderStatus } from '@/services/api';
import type { HealthStatus } from '@/types';
import { SectionHeader, InfoBox, WarningBox, LoadingSpinner } from '@/components/common';

interface ProviderStatus {
  provider: string;
  configured: boolean;
  reachable: boolean;
  mode: 'live' | 'demo' | 'degraded';
  detail: string;
  model?: string;
}

function ProviderStatusBadge({ mode }: { mode: ProviderStatus['mode'] }) {
  if (mode === 'live') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <Wifi className="w-3 h-3" />
        Live AI — Provider Connected
      </span>
    );
  }
  if (mode === 'degraded') {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 border border-amber-200">
        <AlertTriangle className="w-3 h-3" />
        Provider Unreachable
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 border border-amber-200">
      <WifiOff className="w-3 h-3" />
      Demo Mode
    </span>
  );
}

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [provider, setProvider] = useState<ProviderStatus | null>(null);
  const [providerLoading, setProviderLoading] = useState(true);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null))
      .finally(() => setHealthLoading(false));

    getProviderStatus()
      .then(setProvider)
      .catch(() => setProvider(null))
      .finally(() => setProviderLoading(false));
  }, []);

  return (
    <div className="max-w-3xl mx-auto space-y-6 fade-in">
      <SectionHeader
        title="Settings"
        subtitle="System status and configuration information for FoodVerse AI."
      />

      {/* Backend Status */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-forest-500" />
          <h3 className="font-semibold text-charcoal-900">Backend Status</h3>
        </div>
        {healthLoading ? (
          <LoadingSpinner size="sm" message="Connecting to backend…" />
        ) : health ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Status', value: health.status === 'ok' ? 'Online' : health.status },
                { label: 'Version', value: `v${health.version}` },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 bg-cream-100 rounded-xl">
                  <p className="text-xs text-charcoal-100 uppercase tracking-wide font-medium">{label}</p>
                  <p className="text-sm font-semibold text-charcoal-900 mt-0.5">{value}</p>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 rounded-xl px-4 py-2.5 border border-emerald-100">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              Backend is reachable and responding normally.
            </div>
          </div>
        ) : (
          <div className="error-box">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>Backend is not reachable. Ensure it is running on port 8000.</span>
          </div>
        )}
      </div>

      {/* AI Provider Status */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-forest-500" />
          <h3 className="font-semibold text-charcoal-900">AI Provider</h3>
        </div>

        {providerLoading ? (
          <div className="flex items-center gap-2 text-sm text-charcoal-100">
            <Loader2 className="w-4 h-4 spinner text-forest-500" />
            Checking provider connectivity…
          </div>
        ) : provider ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-charcoal-900 capitalize">{provider.provider}</p>
                {provider.model && (
                  <p className="text-xs text-charcoal-100 mt-0.5">Model: {provider.model}</p>
                )}
              </div>
              <ProviderStatusBadge mode={provider.mode} />
            </div>

            {provider.mode === 'live' ? (
              <InfoBox message={provider.detail} />
            ) : provider.mode === 'degraded' ? (
              <div className="warning-box text-xs">
                <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <span>{provider.detail}</span>
              </div>
            ) : (
              <div className="warning-box text-xs">
                <WifiOff className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <span>{provider.detail} Analysis results will be illustrative sample data.</span>
              </div>
            )}
          </div>
        ) : (
          <WarningBox message="Could not retrieve provider status. Check that the backend is running." />
        )}
      </div>

      {/* Data Storage */}
      <div className="card space-y-3">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-forest-500" />
          <h3 className="font-semibold text-charcoal-900">Data Storage</h3>
        </div>
        <InfoBox message="FoodVerse AI uses SQLite for local storage. Analysis history and meal plans persist in backend/data/foodverse.db. This is a single-user local prototype — no cloud sync or multi-user isolation." />
        <p className="text-sm text-charcoal-500">
          Uploaded files are stored in{' '}
          <code className="text-xs bg-cream-200 rounded px-1.5 py-0.5 font-mono">backend/data/uploads/</code>.
          Delete files manually to free space.
        </p>
      </div>

      {/* Responsible AI */}
      <div className="card space-y-3">
        <h3 className="font-semibold text-charcoal-900">Responsible AI & Known Limitations</h3>
        <ul className="space-y-2 text-sm text-charcoal-500">
          {[
            'Nutrition values are estimates — actual content varies by preparation and portion size.',
            'Freshness assessment is visual only. Pathogens, off-flavours, and temperature history cannot be detected.',
            'Hygiene monitoring requires human review. Visual analysis of a few frames cannot certify compliance.',
            'Meal plans are general guidance, not clinical dietary recommendations.',
            'AI confidence scores are model-generated, not laboratory-verified.',
            'Demo Mode results are clearly labelled sample outputs — no real AI inference is performed.',
          ].map((text, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-amber-500 flex-shrink-0 mt-0.5">⚠</span>
              {text}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
