import { useState } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import DashboardPage from '@/pages/DashboardPage';
import FoodRecognitionPage from '@/pages/FoodRecognitionPage';
import NutritionPage from '@/pages/NutritionPage';
import FreshnessPage from '@/pages/FreshnessPage';
import HygienePage from '@/pages/HygienePage';
import CookingPage from '@/pages/CookingPage';
import MealPlannerPage from '@/pages/MealPlannerPage';
import HistoryPage from '@/pages/HistoryPage';
import SettingsPage from '@/pages/SettingsPage';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Overview',
  '/food': 'Food Recognition',
  '/nutrition': 'Nutrition Analysis',
  '/freshness': 'Freshness Check',
  '/hygiene': 'Hygiene Monitor',
  '/cooking': 'Smart Cooking',
  '/meal-planner': 'Meal Planner',
  '/history': 'Analysis History',
  '/settings': 'Settings',
};

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const title = PAGE_TITLES[location.pathname] || 'FoodVerse AI';

  return (
    <div className="flex h-screen overflow-hidden bg-cream-100">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-6">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/food" element={<FoodRecognitionPage />} />
            <Route path="/nutrition" element={<NutritionPage />} />
            <Route path="/freshness" element={<FreshnessPage />} />
            <Route path="/hygiene" element={<HygienePage />} />
            <Route path="/cooking" element={<CookingPage />} />
            <Route path="/meal-planner" element={<MealPlannerPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
