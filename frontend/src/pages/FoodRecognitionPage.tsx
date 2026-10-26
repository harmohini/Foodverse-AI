import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, CheckCircle2, Edit3, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { recognizeFood, analyzeNutrition } from '@/services/api';
import type { FoodRecognitionResult } from '@/types';
import { ImageUploadZone } from '@/components/upload/UploadZone';
import {
  AnalysisLoadingCard, ErrorAlert, DemoModeBanner,
  ConfidenceBadge, SectionHeader, WarningBox
} from '@/components/common';

export default function FoodRecognitionPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<FoodRecognitionResult | null>(null);
  const [editedName, setEditedName] = useState('');
  const [editedServing, setEditedServing] = useState('');
  const [editing, setEditing] = useState(false);

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
      const res = await recognizeFood(file);
      setResult(res);
      setEditedName(res.dish_name);
      setEditedServing(res.serving_size_estimate);
      toast.success('Food identified!');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Analysis failed.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyseNutrition() {
    if (!result) return;
    const name = editedName || result.dish_name;
    const serving = editedServing || result.serving_size_estimate;
    const ingredients = result.ingredients.map((i) => i.name);
    try {
      const res = await analyzeNutrition({ food_name: name, serving_size: serving, ingredients });
      toast.success('Nutrition analysed!');
      // Navigate to nutrition page — pass data via state
      navigate('/nutrition', { state: { nutrition: res } });
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Nutrition analysis failed.');
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 fade-in">
      <SectionHeader
        title="Food Recognition"
        subtitle="Upload a food photo to identify the dish and its ingredients."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload */}
        <div className="card space-y-4">
          <h3 className="font-semibold text-charcoal-900">Upload Image</h3>
          <ImageUploadZone
            onFile={handleFile}
            preview={preview}
            onError={(msg) => { setError(msg); toast.error(msg); }}
          />
          {error && <ErrorAlert message={error} />}
          <button
            id="analyse-food-btn"
            onClick={handleAnalyse}
            disabled={!file || loading}
            className="btn-primary w-full"
          >
            <Search className="w-4 h-4" />
            {loading ? 'Analysing…' : 'Identify Food'}
          </button>
        </div>

        {/* Result */}
        <div className="space-y-4">
          {loading ? (
            <AnalysisLoadingCard message="Identifying food in image…" />
          ) : result ? (
            <div className="card space-y-4 fade-in">
              <DemoModeBanner isDemo={result.metadata.is_demo} />

              <div className="flex items-start justify-between">
                <div>
                  {editing ? (
                    <input
                      value={editedName}
                      onChange={(e) => setEditedName(e.target.value)}
                      className="input text-lg font-bold mb-1"
                      id="edit-food-name"
                    />
                  ) : (
                    <h3 className="text-xl font-bold font-display text-charcoal-900">{editedName}</h3>
                  )}
                  {result.cuisine && (
                    <span className="text-sm text-charcoal-100">{result.cuisine} cuisine</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <ConfidenceBadge confidence={result.confidence} />
                  <button
                    id="edit-food-name-btn"
                    onClick={() => setEditing(!editing)}
                    className="btn-ghost p-1.5"
                    title="Edit food name"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <p className="text-sm text-charcoal-500 leading-relaxed">{result.description}</p>

              {/* Serving size */}
              <div>
                <label className="label">Serving Size</label>
                {editing ? (
                  <input
                    value={editedServing}
                    onChange={(e) => setEditedServing(e.target.value)}
                    className="input"
                    id="edit-serving"
                  />
                ) : (
                  <p className="text-sm font-medium text-charcoal-900 bg-forest-50 rounded-xl px-4 py-3">
                    {editedServing}
                  </p>
                )}
              </div>

              {/* Ingredients */}
              {result.ingredients.length > 0 && (
                <div>
                  <p className="label">Detected Ingredients</p>
                  <div className="flex flex-wrap gap-2">
                    {result.ingredients.map((ing, i) => (
                      <span key={i} className="px-3 py-1 rounded-full bg-forest-50 text-forest-500 text-xs font-medium">
                        {ing.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Warnings */}
              {result.metadata.warnings.slice(0, 1).map((w, i) => (
                result.metadata.is_demo && <WarningBox key={i} message={w} />
              ))}

              {editing && (
                <button onClick={() => setEditing(false)} className="btn-secondary w-full text-sm">
                  <CheckCircle2 className="w-4 h-4" />
                  Confirm Details
                </button>
              )}

              <button
                id="analyse-nutrition-btn"
                onClick={handleAnalyseNutrition}
                className="btn-primary w-full"
              >
                <ArrowRight className="w-4 h-4" />
                Analyse Nutrition
              </button>
            </div>
          ) : (
            <div className="card flex flex-col items-center justify-center py-12 text-center">
              <div className="w-14 h-14 rounded-2xl bg-forest-50 flex items-center justify-center mb-4">
                <Search className="w-7 h-7 text-forest-500" />
              </div>
              <p className="font-semibold text-charcoal-900">No result yet</p>
              <p className="text-sm text-charcoal-100 mt-1">Upload an image and click "Identify Food"</p>
            </div>
          )}
        </div>
      </div>

      {/* Provider info */}
      <div className="info-box text-xs">
        <span>
          <strong>Note:</strong> Food recognition uses a vision AI model when configured. In Demo Mode, a sample result is returned. Confidence scores are model-generated estimates, not laboratory-verified measurements.
        </span>
      </div>
    </div>
  );
}
