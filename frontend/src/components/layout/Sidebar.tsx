import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Search, Zap, Leaf, Eye, ChefHat,
  Calendar, Clock, Settings, Sparkles, X
} from 'lucide-react';
import clsx from 'clsx';

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/food', label: 'Food Recognition', icon: Search },
  { to: '/nutrition', label: 'Nutrition Analysis', icon: Zap },
  { to: '/freshness', label: 'Freshness Check', icon: Leaf },
  { to: '/hygiene', label: 'Hygiene Monitor', icon: Eye },
  { to: '/cooking', label: 'Smart Cooking', icon: ChefHat },
  { to: '/meal-planner', label: 'Meal Planner', icon: Calendar },
  { to: '/history', label: 'Analysis History', icon: Clock },
  { to: '/settings', label: 'Settings', icon: Settings },
];

interface SidebarProps {
  open?: boolean;
  onClose?: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={clsx(
          'fixed top-0 left-0 h-full w-64 bg-white border-r border-forest-50 z-50 flex flex-col transition-transform duration-300 lg:translate-x-0 lg:static lg:z-auto',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-forest-50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-forest-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-display font-bold text-charcoal-900 text-sm leading-none">FoodVerse</p>
              <p className="text-xs text-charcoal-100 mt-0.5">AI Platform</p>
            </div>
          </div>
          {onClose && (
            <button onClick={onClose} className="lg:hidden btn-ghost p-1.5">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={onClose}
              className={({ isActive }) =>
                isActive ? 'nav-item-active' : 'nav-item'
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-forest-50">
          <p className="text-xs text-charcoal-100 leading-relaxed">
            FoodVerse AI v1.0 · Local prototype for single-user use.
          </p>
        </div>
      </aside>
    </>
  );
}
