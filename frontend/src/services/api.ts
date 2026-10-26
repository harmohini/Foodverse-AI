import apiClient from './apiClient';
import type {
  FoodRecognitionResult,
  NutritionRequest,
  NutritionResponse,
  FreshnessResult,
  HygieneReport,
  Recipe,
  CookingRequest,
  CookingChatResponse,
  MealPlanRequest,
  MealPlanResponse,
  HistoryItem,
  HealthStatus,
} from '@/types';

// Health
export const getHealth = () =>
  apiClient.get<HealthStatus>('/api/health').then((r) => r.data);

export const getProviderStatus = () =>
  apiClient.get<{
    provider: string;
    configured: boolean;
    reachable: boolean;
    mode: 'live' | 'demo' | 'degraded';
    detail: string;
    model?: string;
  }>('/api/health/provider').then((r) => r.data);

// Food Recognition
export const recognizeFood = (file: File) => {
  const fd = new FormData();
  fd.append('file', file);
  return apiClient.post<FoodRecognitionResult>('/api/v1/food/recognize', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};

// Nutrition
export const analyzeNutrition = (req: NutritionRequest) =>
  apiClient.post<NutritionResponse>('/api/v1/nutrition/analyze', req).then((r) => r.data);

// Freshness
export const analyzeFreshness = (file: File, foodCategory: string) => {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('food_category', foodCategory);
  return apiClient.post<FreshnessResult>('/api/v1/freshness/analyze', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};

// Hygiene
export const analyzeHygiene = (file: File) => {
  const fd = new FormData();
  fd.append('file', file);
  return apiClient.post<HygieneReport>('/api/v1/hygiene/analyze', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};

// Cooking
export const generateRecipe = (req: CookingRequest) =>
  apiClient.post<Recipe>('/api/v1/cooking/generate', req).then((r) => r.data);

export const chatCooking = (recipeId: string, message: string, chatHistory: { role: string; content: string }[]) =>
  apiClient.post<CookingChatResponse>('/api/v1/cooking/chat', {
    recipe_id: recipeId,
    message,
    chat_history: chatHistory,
  }).then((r) => r.data);

// Meal Plans
export const generateMealPlan = (req: MealPlanRequest) =>
  apiClient.post<MealPlanResponse>('/api/v1/meal-plans/generate', req).then((r) => r.data);

export const getMealPlans = () =>
  apiClient.get<MealPlanResponse[]>('/api/v1/meal-plans/').then((r) => r.data);

export const getMealPlan = (planId: string) =>
  apiClient.get<MealPlanResponse>(`/api/v1/meal-plans/${planId}`).then((r) => r.data);

export const deleteMealPlan = (planId: string) =>
  apiClient.delete(`/api/v1/meal-plans/${planId}`).then((r) => r.data);

// History
export const getHistory = (limit = 50) =>
  apiClient.get<HistoryItem[]>('/api/v1/history/', { params: { limit } }).then((r) => r.data);

export const getHistoryItem = (analysisId: string) =>
  apiClient.get(`/api/v1/history/${analysisId}`).then((r) => r.data);

export const deleteHistoryItem = (analysisId: string) =>
  apiClient.delete(`/api/v1/history/${analysisId}`).then((r) => r.data);
