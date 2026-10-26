// FoodVerse AI — TypeScript type definitions

export interface AnalysisMetadata {
  analysis_id: string;
  input_type: string;
  analysis_type: string;
  provider: string;
  is_demo: boolean;
  warnings: string[];
  created_at: string;
}

// Food Recognition
export interface Ingredient {
  name: string;
  confidence?: number;
}

export interface FoodRecognitionResult {
  dish_name: string;
  confidence?: number;
  description: string;
  ingredients: Ingredient[];
  cuisine?: string;
  serving_size_estimate: string;
  metadata: AnalysisMetadata;
}

// Nutrition
export interface NutritionData {
  food_name: string;
  serving_size: string;
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sugar_g?: number;
  sodium_mg?: number;
  nutrition_score?: number;
  score_explanation: string;
  summary: string;
  source: string;
  uncertainty_note: string;
}

export interface NutritionResponse {
  nutrition: NutritionData;
  metadata: AnalysisMetadata;
}

export interface NutritionRequest {
  food_name: string;
  serving_size?: string;
  ingredients?: string[];
}

// Freshness
export interface FreshnessObservation {
  characteristic: string;
  observation: string;
  severity: 'normal' | 'mild' | 'concerning';
}

export interface FreshnessResult {
  food_category: string;
  status: 'Fresh' | 'Moderately Fresh' | 'Possible Spoilage';
  confidence?: number;
  observations: FreshnessObservation[];
  next_steps: string[];
  safety_disclaimer: string;
  metadata: AnalysisMetadata;
}

// Hygiene
export interface HygieneIndicator {
  indicator: string;
  status: 'observed' | 'not_observed' | 'unable_to_assess';
  evidence: string;
  timestamp_seconds?: number;
}

export interface HygieneReport {
  overall_assessment: string;
  frames_analyzed: number;
  duration_seconds?: number;
  indicators: HygieneIndicator[];
  limitations: string[];
  corrective_actions: string[];
  disclaimer: string;
  metadata: AnalysisMetadata;
}

// Cooking
export interface RecipeIngredient {
  item: string;
  quantity: string;
  unit: string;
  preparation: string;
}

export interface RecipeStep {
  step_number: number;
  instruction: string;
  duration_minutes?: number;
  tip: string;
}

export interface Recipe {
  recipe_id: string;
  title: string;
  description: string;
  cuisine: string;
  dietary_info: string;
  prep_time_minutes: number;
  cook_time_minutes: number;
  servings: number;
  difficulty: string;
  ingredients: RecipeIngredient[];
  steps: RecipeStep[];
  substitutions: string[];
  equipment: string[];
  allergen_notes: string[];
  food_safety_notes: string[];
  estimated_nutrition?: NutritionData;
  is_demo: boolean;
}

export interface CookingRequest {
  dish_name: string;
  available_ingredients?: string[];
  cuisine_preference?: string;
  dietary_preference?: string;
  cooking_time_minutes?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  servings?: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface CookingChatResponse {
  message: string;
  is_demo: boolean;
}

// Meal Planner
export interface MealItem {
  meal_type: string;
  name: string;
  description: string;
  ingredients: string[];
  serving_size: string;
  prep_time_minutes: number;
  estimated_calories?: number;
  brief_instructions: string;
}

export interface DayPlan {
  day: number;
  date_label: string;
  meals: MealItem[];
  daily_estimated_calories?: number;
}

export interface ShoppingItem {
  ingredient: string;
  quantity: string;
  category: string;
}

export interface MealPlanRequest {
  dietary_pattern?: string;
  allergies?: string[];
  excluded_foods?: string[];
  favorite_cuisines?: string[];
  meals_per_day?: number;
  plan_days?: number;
  cooking_time_preference?: string;
  goal?: string;
  budget_preference?: string;
}

export interface MealPlanResponse {
  plan_id: string;
  title: string;
  days: DayPlan[];
  shopping_list: ShoppingItem[];
  allergy_reminder: string;
  is_demo: boolean;
  created_at: string;
}

// History
export interface HistoryItem {
  id: number;
  analysis_id: string;
  input_type: string;
  analysis_type: string;
  food_name?: string;
  provider: string;
  is_demo: boolean;
  created_at: string;
}

// Health
export interface HealthStatus {
  status: string;
  version: string;
  ai_provider: string;
  is_demo_mode: boolean;
  message: string;
}
