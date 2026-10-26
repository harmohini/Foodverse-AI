import { useState } from 'react';
import { Calendar, ShoppingCart, Trash2, RefreshCw, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import toast from 'react-hot-toast';
import { generateMealPlan, deleteMealPlan } from '@/services/api';
import type { MealPlanRequest, MealPlanResponse, DayPlan, ShoppingItem } from '@/types';
import { AnalysisLoadingCard, ErrorAlert, DemoModeBanner, SectionHeader } from '@/components/common';

const CATEGORY_COLORS: Record<string, string> = {
  produce: 'bg-emerald-50 text-emerald-700',
  protein: 'bg-red-50 text-red-700',
  dairy: 'bg-blue-50 text-blue-700',
  pantry: 'bg-amber-50 text-amber-700',
  other: 'bg-gray-50 text-gray-700',
};

function DayCard({ day }: { day: DayPlan }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="card">
      <button
        className="flex items-center justify-between w-full mb-2"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-forest-500 text-white flex items-center justify-center text-sm font-bold">
            {day.day}
          </div>
          <span className="font-semibold text-charcoal-900">{day.date_label}</span>
        </div>
        <div className="flex items-center gap-2">
          {day.daily_estimated_calories && (
            <span className="text-xs text-charcoal-100">~{day.daily_estimated_calories.toFixed(0)} kcal</span>
          )}
          {open ? <ChevronUp className="w-4 h-4 text-charcoal-100" /> : <ChevronDown className="w-4 h-4 text-charcoal-100" />}
        </div>
      </button>
      {open && (
        <div className="space-y-3 mt-3">
          {day.meals.map((meal, i) => (
            <div key={i} className="p-3 bg-cream-100 rounded-xl">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-forest-500 uppercase tracking-wide">{meal.meal_type}</span>
                <span className="text-xs text-charcoal-100">
                  {meal.prep_time_minutes}m prep
                  {meal.estimated_calories ? ` · ~${meal.estimated_calories.toFixed(0)} kcal` : ''}
                </span>
              </div>
              <p className="text-sm font-semibold text-charcoal-900">{meal.name}</p>
              <p className="text-xs text-charcoal-100 mt-0.5">{meal.description}</p>
              {meal.brief_instructions && (
                <p className="text-xs text-charcoal-500 mt-2 leading-relaxed border-t border-forest-50 pt-2">
                  {meal.brief_instructions}
                </p>
              )}
              {meal.ingredients.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {meal.ingredients.slice(0, 5).map((ing, j) => (
                    <span key={j} className="text-xs px-2 py-0.5 bg-white rounded-full text-charcoal-500 border border-forest-50">{ing}</span>
                  ))}
                  {meal.ingredients.length > 5 && (
                    <span className="text-xs px-2 py-0.5 bg-white rounded-full text-charcoal-100 border border-forest-50">+{meal.ingredients.length - 5} more</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ShoppingListSection({ items }: { items: ShoppingItem[] }) {
  const grouped = items.reduce((acc, item) => {
    const cat = item.category || 'other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {} as Record<string, ShoppingItem[]>);

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <ShoppingCart className="w-5 h-5 text-forest-500" />
        <h3 className="font-semibold text-charcoal-900">Shopping List</h3>
      </div>
      <div className="space-y-4">
        {Object.entries(grouped).map(([cat, groupItems]) => (
          <div key={cat}>
            <h4 className={`text-xs font-semibold uppercase tracking-wide px-2 py-1 rounded-lg inline-block mb-2 ${CATEGORY_COLORS[cat] || CATEGORY_COLORS.other}`}>
              {cat}
            </h4>
            <ul className="space-y-1.5">
              {groupItems.map((item, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-charcoal-500">
                  <span className="w-4 h-4 rounded border border-forest-200 flex-shrink-0" />
                  <span className="font-medium">{item.quantity}</span>
                  <span>{item.ingredient}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MealPlannerPage() {
  const [allergiesText, setAllergiesText] = useState('');
  const [excludedText, setExcludedText] = useState('');
  const [cuisinesText, setCuisinesText] = useState('');
  const [form, setForm] = useState<MealPlanRequest>({
    dietary_pattern: '',
    meals_per_day: 3,
    plan_days: 7,
    cooking_time_preference: 'moderate',
    goal: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [plan, setPlan] = useState<MealPlanResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'plan' | 'shopping'>('plan');

  async function handleGenerate() {
    setLoading(true);
    setError('');
    try {
      const req: MealPlanRequest = {
        ...form,
        allergies: allergiesText.split(',').map((s) => s.trim()).filter(Boolean),
        excluded_foods: excludedText.split(',').map((s) => s.trim()).filter(Boolean),
        favorite_cuisines: cuisinesText.split(',').map((s) => s.trim()).filter(Boolean),
      };
      const res = await generateMealPlan(req);
      setPlan(res);
      toast.success('Meal plan generated!');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Generation failed.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!plan) return;
    try {
      await deleteMealPlan(plan.plan_id);
      setPlan(null);
      toast.success('Plan deleted.');
    } catch {
      toast.error('Could not delete plan.');
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 fade-in">
      <SectionHeader
        title="Personalised Meal Planner"
        subtitle="Create a custom daily or 7-day meal plan based on your preferences."
      />

      {/* Preferences form */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-charcoal-900">Your Preferences</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label" htmlFor="dietary-pattern">Dietary Pattern</label>
            <select id="dietary-pattern" className="select" value={form.dietary_pattern} onChange={(e) => setForm({ ...form, dietary_pattern: e.target.value })}>
              <option value="">Balanced (no restriction)</option>
              <option value="omnivore">Omnivore</option>
              <option value="vegetarian">Vegetarian</option>
              <option value="vegan">Vegan</option>
              <option value="pescatarian">Pescatarian</option>
              <option value="gluten-free">Gluten-free</option>
              <option value="keto">Keto</option>
            </select>
          </div>
          <div>
            <label className="label" htmlFor="goal">Goal</label>
            <input id="goal" className="input" placeholder="e.g. balanced eating, general fitness…"
              value={form.goal} onChange={(e) => setForm({ ...form, goal: e.target.value })} />
          </div>
          <div>
            <label className="label" htmlFor="allergies">Allergies & Exclusions (comma-separated)</label>
            <input id="allergies" className="input" placeholder="nuts, shellfish, gluten…"
              value={allergiesText} onChange={(e) => setAllergiesText(e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="excluded">Foods to Avoid (comma-separated)</label>
            <input id="excluded" className="input" placeholder="red meat, dairy…"
              value={excludedText} onChange={(e) => setExcludedText(e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="cuisines">Favourite Cuisines (optional)</label>
            <input id="cuisines" className="input" placeholder="Italian, Japanese, Mexican…"
              value={cuisinesText} onChange={(e) => setCuisinesText(e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="cooking-time">Cooking Time Preference</label>
            <select id="cooking-time" className="select" value={form.cooking_time_preference} onChange={(e) => setForm({ ...form, cooking_time_preference: e.target.value })}>
              <option value="quick">Quick (under 20 min)</option>
              <option value="moderate">Moderate (20–45 min)</option>
              <option value="leisurely">Leisurely (45+ min)</option>
            </select>
          </div>
          <div>
            <label className="label" htmlFor="meals-per-day">Meals per Day</label>
            <select id="meals-per-day" className="select" value={form.meals_per_day} onChange={(e) => setForm({ ...form, meals_per_day: Number(e.target.value) })}>
              <option value={2}>2 (Lunch + Dinner)</option>
              <option value={3}>3 (Breakfast + Lunch + Dinner)</option>
              <option value={4}>4 (+ 1 Snack)</option>
              <option value={5}>5 (+ 2 Snacks)</option>
            </select>
          </div>
          <div>
            <label className="label" htmlFor="plan-days">Plan Duration</label>
            <select id="plan-days" className="select" value={form.plan_days} onChange={(e) => setForm({ ...form, plan_days: Number(e.target.value) })}>
              <option value={1}>1 Day</option>
              <option value={3}>3 Days</option>
              <option value={5}>5 Days</option>
              <option value={7}>7 Days</option>
            </select>
          </div>
        </div>

        {error && <ErrorAlert message={error} />}

        <div className="warning-box text-xs">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <span>Meal plans are for general guidance only. Always check ingredient labels for allergens. This is not medical or clinical dietary advice.</span>
        </div>

        <button id="generate-meal-plan-btn" onClick={handleGenerate} disabled={loading} className="btn-primary">
          <Calendar className="w-4 h-4" />
          {loading ? 'Generating Plan…' : 'Generate Meal Plan'}
        </button>
      </div>

      {/* Plan result */}
      {loading ? (
        <AnalysisLoadingCard message="Creating your personalised meal plan…" />
      ) : plan ? (
        <div className="space-y-6 fade-in">
          <DemoModeBanner isDemo={plan.is_demo} />

          <div className="flex items-center justify-between">
            <h2 className="section-title">{plan.title}</h2>
            <div className="flex gap-2">
              <button id="regenerate-plan-btn" onClick={handleGenerate} className="btn-secondary text-sm">
                <RefreshCw className="w-4 h-4" />
                Regenerate
              </button>
              <button id="delete-plan-btn" onClick={handleDelete} className="btn-ghost text-sm text-red-500">
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-cream-200 rounded-xl p-1 w-fit">
            <button
              id="tab-plan"
              onClick={() => setActiveTab('plan')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'plan' ? 'bg-white shadow-card text-charcoal-900' : 'text-charcoal-100 hover:text-charcoal-500'}`}
            >
              Meal Plan
            </button>
            <button
              id="tab-shopping"
              onClick={() => setActiveTab('shopping')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'shopping' ? 'bg-white shadow-card text-charcoal-900' : 'text-charcoal-100 hover:text-charcoal-500'}`}
            >
              Shopping List ({plan.shopping_list.length})
            </button>
          </div>

          {activeTab === 'plan' ? (
            <div className="space-y-4">
              {plan.days.map((day) => <DayCard key={day.day} day={day} />)}
            </div>
          ) : (
            <ShoppingListSection items={plan.shopping_list} />
          )}

          {/* Allergy reminder */}
          <div className="warning-box text-xs">
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
            <span>{plan.allergy_reminder}</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}
