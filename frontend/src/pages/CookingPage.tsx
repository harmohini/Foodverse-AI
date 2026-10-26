import { useState, useRef, useEffect } from 'react';
import { ChefHat, Send, Clock, Users, Utensils, ShieldCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import { generateRecipe, chatCooking } from '@/services/api';
import type { Recipe, CookingRequest, ChatMessage } from '@/types';
import { AnalysisLoadingCard, ErrorAlert, DemoModeBanner, SectionHeader, WarningBox } from '@/components/common';

function RecipeCard({ recipe }: { recipe: Recipe }) {
  return (
    <div className="space-y-6">
      <DemoModeBanner isDemo={recipe.is_demo} />

      {/* Header */}
      <div className="card">
        <h2 className="text-2xl font-bold font-display text-charcoal-900">{recipe.title}</h2>
        <p className="text-charcoal-100 mt-1">{recipe.description}</p>
        <div className="flex flex-wrap gap-3 mt-4">
          <span className="inline-flex items-center gap-1.5 text-sm text-charcoal-500 bg-cream-100 rounded-lg px-3 py-1.5">
            <Clock className="w-4 h-4 text-forest-500" />
            Prep: {recipe.prep_time_minutes}m
          </span>
          <span className="inline-flex items-center gap-1.5 text-sm text-charcoal-500 bg-cream-100 rounded-lg px-3 py-1.5">
            <Utensils className="w-4 h-4 text-forest-500" />
            Cook: {recipe.cook_time_minutes}m
          </span>
          <span className="inline-flex items-center gap-1.5 text-sm text-charcoal-500 bg-cream-100 rounded-lg px-3 py-1.5">
            <Users className="w-4 h-4 text-forest-500" />
            Serves: {recipe.servings}
          </span>
          <span className="px-3 py-1.5 bg-forest-50 text-forest-500 rounded-lg text-sm font-medium">
            {recipe.difficulty}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ingredients */}
        <div className="card">
          <h3 className="font-semibold text-charcoal-900 mb-4">Ingredients</h3>
          <ul className="space-y-2">
            {recipe.ingredients.map((ing, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-charcoal-500">
                <span className="w-5 h-5 rounded-full bg-forest-50 text-forest-500 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">✓</span>
                <span>
                  <strong>{ing.quantity} {ing.unit}</strong> {ing.item}
                  {ing.preparation && <span className="text-charcoal-100"> — {ing.preparation}</span>}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Equipment & Substitutions */}
        <div className="space-y-4">
          {recipe.equipment.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-charcoal-900 mb-3">Equipment</h3>
              <div className="flex flex-wrap gap-2">
                {recipe.equipment.map((e, i) => (
                  <span key={i} className="px-3 py-1 bg-cream-100 text-charcoal-500 rounded-lg text-xs">{e}</span>
                ))}
              </div>
            </div>
          )}
          {recipe.substitutions.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-charcoal-900 mb-3">Substitutions</h3>
              <ul className="space-y-1.5">
                {recipe.substitutions.map((s, i) => (
                  <li key={i} className="text-sm text-charcoal-500 flex items-start gap-2">
                    <span className="text-amber-500 flex-shrink-0">↔</span>{s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Steps */}
      <div className="card">
        <h3 className="font-semibold text-charcoal-900 mb-4">Step-by-Step Instructions</h3>
        <div className="space-y-4">
          {recipe.steps.map((step) => (
            <div key={step.step_number} className="flex gap-4">
              <div className="w-8 h-8 rounded-xl bg-forest-500 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                {step.step_number}
              </div>
              <div className="flex-1">
                <p className="text-sm text-charcoal-500 leading-relaxed">{step.instruction}</p>
                {step.tip && (
                  <p className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2 mt-2">
                    💡 {step.tip}
                  </p>
                )}
                {step.duration_minutes && (
                  <p className="text-xs text-charcoal-100 mt-1">~{step.duration_minutes} min</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Food Safety */}
      {recipe.food_safety_notes.length > 0 && (
        <div className="card border border-amber-200 bg-amber-50">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="w-5 h-5 text-amber-600" />
            <h3 className="font-semibold text-amber-800">Food Safety Reminders</h3>
          </div>
          <ul className="space-y-1.5">
            {recipe.food_safety_notes.map((n, i) => (
              <li key={i} className="text-sm text-amber-800 flex items-start gap-2">
                <span className="flex-shrink-0 mt-0.5">⚠</span>{n}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Allergen notes */}
      {recipe.allergen_notes.length > 0 && (
        <div className="info-box text-xs">
          <span>{recipe.allergen_notes.join(' ')}</span>
        </div>
      )}
    </div>
  );
}

interface ChatBubbleProps {
  msg: ChatMessage;
}

function ChatBubble({ msg }: ChatBubbleProps) {
  return (
    <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
        msg.role === 'user'
          ? 'bg-forest-500 text-white rounded-tr-sm'
          : 'bg-white border border-forest-50 text-charcoal-500 rounded-tl-sm shadow-card'
      }`}>
        {msg.content}
      </div>
    </div>
  );
}

export default function CookingPage() {
  const [form, setForm] = useState<CookingRequest>({
    dish_name: '',
    available_ingredients: [],
    cuisine_preference: '',
    dietary_preference: '',
    cooking_time_minutes: undefined,
    difficulty: 'medium',
    servings: 2,
  });
  const [ingredientsText, setIngredientsText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  async function handleGenerate() {
    if (!form.dish_name.trim()) { toast.error('Enter a dish name.'); return; }
    setLoading(true);
    setError('');
    setChatMessages([]);
    try {
      const req = {
        ...form,
        available_ingredients: ingredientsText.split(',').map((s) => s.trim()).filter(Boolean),
      };
      const res = await generateRecipe(req);
      setRecipe(res);
      toast.success('Recipe generated!');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Generation failed.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleChat() {
    if (!chatInput.trim() || !recipe) return;
    const userMsg: ChatMessage = { role: 'user', content: chatInput };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);
    try {
      const res = await chatCooking(
        recipe.recipe_id,
        chatInput,
        chatMessages.map((m) => ({ role: m.role, content: m.content }))
      );
      setChatMessages((prev) => [...prev, { role: 'assistant', content: res.message }]);
    } catch {
      setChatMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I could not respond. Please try again.' }]);
    } finally {
      setChatLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 fade-in">
      <SectionHeader
        title="Smart Cooking Assistant"
        subtitle="Generate recipes and get instant help with substitutions, dietary changes, and cooking tips."
      />

      {/* Form */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-charcoal-900">Recipe Request</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2">
            <label className="label" htmlFor="dish-name">Dish Name or Request</label>
            <input
              id="dish-name"
              className="input"
              placeholder="e.g. Herb-roasted chicken, quick pasta carbonara…"
              value={form.dish_name}
              onChange={(e) => setForm({ ...form, dish_name: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <label className="label" htmlFor="ingredients">Available Ingredients (optional, comma-separated)</label>
            <input
              id="ingredients"
              className="input"
              placeholder="chicken, garlic, lemon, olive oil…"
              value={ingredientsText}
              onChange={(e) => setIngredientsText(e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="cuisine">Cuisine Preference</label>
            <select id="cuisine" className="select" value={form.cuisine_preference} onChange={(e) => setForm({ ...form, cuisine_preference: e.target.value })}>
              <option value="">Any cuisine</option>
              <option>Italian</option><option>Japanese</option><option>Mexican</option>
              <option>Indian</option><option>Mediterranean</option><option>American</option>
              <option>Thai</option><option>French</option><option>Chinese</option>
            </select>
          </div>
          <div>
            <label className="label" htmlFor="dietary">Dietary Preference</label>
            <select id="dietary" className="select" value={form.dietary_preference} onChange={(e) => setForm({ ...form, dietary_preference: e.target.value })}>
              <option value="">No restriction</option>
              <option>Vegetarian</option><option>Vegan</option><option>Gluten-free</option>
              <option>Dairy-free</option><option>Keto</option><option>Low-carb</option>
            </select>
          </div>
          <div>
            <label className="label" htmlFor="cook-time">Max Cooking Time (minutes)</label>
            <input id="cook-time" type="number" min={10} max={240} className="input" placeholder="60"
              value={form.cooking_time_minutes || ''} onChange={(e) => setForm({ ...form, cooking_time_minutes: Number(e.target.value) || undefined })} />
          </div>
          <div>
            <label className="label" htmlFor="servings">Servings</label>
            <input id="servings" type="number" min={1} max={20} className="input" value={form.servings}
              onChange={(e) => setForm({ ...form, servings: Number(e.target.value) })} />
          </div>
          <div>
            <label className="label" htmlFor="difficulty">Difficulty</label>
            <select id="difficulty" className="select" value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: e.target.value as 'easy' | 'medium' | 'hard' })}>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
        </div>
        {error && <ErrorAlert message={error} />}
        <button id="generate-recipe-btn" onClick={handleGenerate} disabled={loading} className="btn-primary">
          <ChefHat className="w-4 h-4" />
          {loading ? 'Generating…' : 'Generate Recipe'}
        </button>
      </div>

      {/* Recipe */}
      {loading ? (
        <AnalysisLoadingCard message="Creating your recipe…" />
      ) : recipe ? (
        <>
          <RecipeCard recipe={recipe} />

          {/* Chat */}
          <div className="card">
            <h3 className="font-semibold text-charcoal-900 mb-1">Ask a Follow-up Question</h3>
            <p className="text-xs text-charcoal-100 mb-4">
              "Make this vegetarian" · "Replace butter with olive oil" · "Reduce prep time"
            </p>
            <div className="bg-cream-100 rounded-2xl p-4 min-h-[120px] max-h-64 overflow-y-auto space-y-3 mb-3">
              {chatMessages.length === 0 && (
                <p className="text-sm text-charcoal-100 text-center py-4">Chat history will appear here.</p>
              )}
              {chatMessages.map((msg, i) => <ChatBubble key={i} msg={msg} />)}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-forest-50 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-charcoal-100 shadow-card">
                    Thinking…
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div className="flex gap-2">
              <input
                id="chat-input"
                className="input flex-1"
                placeholder="Ask anything about this recipe…"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleChat()}
              />
              <button
                id="chat-send-btn"
                onClick={handleChat}
                disabled={!chatInput.trim() || chatLoading}
                className="btn-primary px-4"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
