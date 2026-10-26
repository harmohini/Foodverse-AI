import { Menu, Wifi, WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getHealth } from '@/services/api';
import type { HealthStatus } from '@/types';

interface HeaderProps {
  title: string;
  onMenuClick: () => void;
}

export function Header({ title, onMenuClick }: HeaderProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <header className="h-16 bg-white border-b border-forest-50 flex items-center justify-between px-6 flex-shrink-0 sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <button
          id="menu-toggle"
          onClick={onMenuClick}
          className="lg:hidden btn-ghost p-2 -ml-2"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="font-display font-bold text-lg text-charcoal-900">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        {health !== null ? (
          health.is_demo_mode ? (
            <div className="badge-demo">
              <WifiOff className="w-3 h-3" />
              Demo Mode
            </div>
          ) : (
            <div className="badge-live">
              <Wifi className="w-3 h-3" />
              AI Connected
            </div>
          )
        ) : (
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-500">
            <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse" />
            Connecting…
          </div>
        )}
      </div>
    </header>
  );
}
