import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Zap } from 'lucide-react';
import toast from 'react-hot-toast';
import { analyzeNutrition } from '@/services/api';
import type { NutritionResponse } from '@/types';
import { MacroPieChart, NutritionSummaryCard, NutritionScoreRing } from '@/components/nutrition/NutritionCharts';
import { AnalysisLoadingCard, ErrorAlert, DemoModeBanner, SectionHeader, InfoBox } from '@/components/common';

export default function NutritionPage() {
  const location = useLocation();
  const passedData = (location.state as { nutrition?: NutritionResponse })?.nutrition;

  const [foodName, setFoodName] = useState('');
  const [servingSize, setServingSize] = useState('1 serving');
  const [ingredients, setIngredients] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<NutritionResponse | null>(passedData || null);

  async function handleAnalyse() {
    if (!foodName.trim()) { toast.error('Enter a food name.'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await analyzeNutrition({
        food_name: foodName,
        serving_size: servingSize,
        ingredients: ingredients.split(',').map((s) => s.trim()).filter(Boolean),
      });
      setResult(res);
      toast.success('Nutrition analysed!');
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
        title="Nutrition Analysis"
        subtitle="Get estimated nutritional information for any food or dish."
      />

      {/* Input form */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-charcoal-900">Food Details</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label" htmlFor="food-name-input">Food Name</label>
            <input
              id="food-name-input"
              className="input"
              placeholder="e.g. Grilled Chicken Salad"
              value={foodName}
              onChange={(e) => setFoodName(e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="serving-size-input">Serving Size</label>
            <input
              id="serving-size-input"
              className="input"
              placeholder="e.g. 1 bowl (350g)"
              value={servingSize}
              onChange={(e) => setServingSize(e.target.value)}
            />
          </div>
        </div>
        <div>
          <label className="label" htmlFor="ingredients-input">
            Ingredients <span className="text-charcoal-100 font-normal">(optional, comma-separated)</span>
          </label>
          <input
            id="ingredients-input"
            className="input"
            placeholder="chicken, lettuce, olive oil, tomato…"
            value={ingredients}
            onChange={(e) => setIngredients(e.target.value)}
          />
        </div>
        {error && <ErrorAlert message={error} />}
        <button
          id="analyse-nutrition-submit-btn"
          onClick={handleAnalyse}
          disabled={loading || !foodName.trim()}
          className="btn-primary"
        >
          <Zap className="w-4 h-4" />
          {loading ? 'Analysing…' : 'Analyse Nutrition'}
        </button>
      </div>

      {/* Results */}
      {loading ? (
        <AnalysisLoadingCard message="Calculating nutritional estimates…" />
      ) : result ? (
        <div className="space-y-6 fade-in">
          <DemoModeBanner isDemo={result.metadata.is_demo} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Score */}
            <div className="card flex flex-col gap-4">
              <h3 className="font-semibold text-charcoal-900">Nutrition Score</h3>
              <NutritionScoreRing score={result.nutrition.nutrition_score} />
              <p className="text-xs text-charcoal-100 leading-relaxed">
                {result.nutrition.score_explanation}
              </p>
            </div>

            {/* Macros */}
            <div className="card">
              <h3 className="font-semibold text-charcoal-900 mb-4">Macronutrients</h3>
              <MacroPieChart nutrition={result.nutrition} />
            </div>

            {/* Summary */}
            <div className="card">
              <h3 className="font-semibold text-charcoal-900 mb-4">Summary</h3>
              <p className="text-sm text-charcoal-500 leading-relaxed">{result.nutrition.summary}</p>
              <div className="divider" />
              <p className="text-xs text-charcoal-100">
                <strong>Source:</strong> {result.nutrition.source}
              </p>
            </div>
          </div>

          {/* Full breakdown */}
          <div className="card">
            <h3 className="font-semibold text-charcoal-900 mb-4">Full Nutritional Breakdown</h3>
            <NutritionSummaryCard nutrition={result.nutrition} />
          </div>

          {/* Uncertainty note */}
          <InfoBox message={result.nutrition.uncertainty_note} />
        </div>
      ) : (
        <div className="card flex flex-col items-center py-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 flex items-center justify-center mb-4">
            <Zap className="w-7 h-7 text-amber-600" />
          </div>
          <p className="font-semibold text-charcoal-900">Enter a food to analyse</p>
          <p className="text-sm text-charcoal-100 mt-1">
            Type a food name above, or navigate here from Food Recognition.
          </p>
        </div>
      )}
    </div>
  );
}
