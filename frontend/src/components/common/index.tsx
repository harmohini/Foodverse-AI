import { Loader2, AlertCircle, CheckCircle2, Info, TriangleAlert } from 'lucide-react';

// ─── Loading Spinner ────────────────────────────────────────────────────────

interface LoadingProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LoadingSpinner({ message = 'Analysing…', size = 'md' }: LoadingProps) {
  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-10 h-10' };
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8">
      <Loader2 className={`${sizes[size]} text-forest-500 spinner`} />
      {message && <p className="text-sm text-charcoal-100">{message}</p>}
    </div>
  );
}

// ─── Analysis Loading Card ──────────────────────────────────────────────────

export function AnalysisLoadingCard({ message }: { message?: string }) {
  return (
    <div className="card flex flex-col items-center gap-4 py-12">
      <div className="w-16 h-16 rounded-2xl bg-forest-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-forest-500 spinner" />
      </div>
      <div className="text-center">
        <p className="font-semibold text-charcoal-900">{message || 'Running analysis…'}</p>
        <p className="text-sm text-charcoal-100 mt-1">This may take a few seconds.</p>
      </div>
      <div className="w-48 h-1.5 bg-forest-50 rounded-full overflow-hidden">
        <div className="h-full bg-forest-500 rounded-full animate-[progress_2s_ease-in-out_infinite]" style={{ width: '60%' }} />
      </div>
    </div>
  );
}

// ─── Empty State ────────────────────────────────────────────────────────────

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12 text-center">
      {icon && (
        <div className="w-16 h-16 rounded-2xl bg-forest-50 flex items-center justify-center text-forest-500">
          {icon}
        </div>
      )}
      <div>
        <p className="font-semibold text-charcoal-900">{title}</p>
        {description && <p className="text-sm text-charcoal-100 mt-1 max-w-xs mx-auto">{description}</p>}
      </div>
      {action}
    </div>
  );
}

// ─── Error Alert ────────────────────────────────────────────────────────────

export function ErrorAlert({ message }: { message: string }) {
  return (
    <div className="error-box">
      <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
      <span>{message}</span>
    </div>
  );
}

// ─── Warning Box ────────────────────────────────────────────────────────────

export function WarningBox({ message }: { message: string }) {
  return (
    <div className="warning-box">
      <TriangleAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
      <span>{message}</span>
    </div>
  );
}

// ─── Info Box ───────────────────────────────────────────────────────────────

export function InfoBox({ message }: { message: string }) {
  return (
    <div className="info-box">
      <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
      <span>{message}</span>
    </div>
  );
}

// ─── Success Banner ─────────────────────────────────────────────────────────

export function SuccessBanner({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-800">
      <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
      <span>{message}</span>
    </div>
  );
}

// ─── Demo Mode Banner ───────────────────────────────────────────────────────

export function DemoModeBanner({ isDemo }: { isDemo: boolean }) {
  if (!isDemo) return null;
  return (
    <div className="warning-box text-xs">
      <TriangleAlert className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
      <span>
        <strong>Demo Mode:</strong> These are illustrative sample results. No real AI inference was performed.
        Configure an AI provider in Settings to enable live analysis.
      </span>
    </div>
  );
}

// ─── Confidence Badge ───────────────────────────────────────────────────────

export function ConfidenceBadge({ confidence }: { confidence?: number }) {
  if (confidence === undefined) return null;
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? 'text-emerald-700 bg-emerald-50' : pct >= 60 ? 'text-amber-700 bg-amber-50' : 'text-red-700 bg-red-50';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {pct}% confidence
    </span>
  );
}

// ─── Skeleton Loader ────────────────────────────────────────────────────────

export function SkeletonCard() {
  return (
    <div className="card space-y-3">
      <div className="skeleton h-5 w-2/3 rounded" />
      <div className="skeleton h-4 w-full rounded" />
      <div className="skeleton h-4 w-4/5 rounded" />
      <div className="skeleton h-24 w-full rounded-xl" />
    </div>
  );
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className={`skeleton h-4 rounded ${i === lines - 1 ? 'w-3/4' : 'w-full'}`} />
      ))}
    </div>
  );
}

// ─── Section Header ─────────────────────────────────────────────────────────

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export function SectionHeader({ title, subtitle, action }: SectionHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div>
        <h2 className="section-title">{title}</h2>
        {subtitle && <p className="section-subtitle">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
