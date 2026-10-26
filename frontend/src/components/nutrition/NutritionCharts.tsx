import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import type { NutritionData } from '@/types';

const MACRO_COLORS = { protein: '#245B43', carbs: '#A9BEA3', fat: '#D4A017' };

interface MacroPieProps {
  nutrition: NutritionData;
}

export function MacroPieChart({ nutrition }: MacroPieProps) {
  const data = [
    { name: 'Protein', value: (nutrition.protein_g || 0) * 4, grams: nutrition.protein_g || 0, color: MACRO_COLORS.protein },
    { name: 'Carbs', value: (nutrition.carbs_g || 0) * 4, grams: nutrition.carbs_g || 0, color: MACRO_COLORS.carbs },
    { name: 'Fat', value: (nutrition.fat_g || 0) * 9, grams: nutrition.fat_g || 0, color: MACRO_COLORS.fat },
  ].filter((d) => d.value > 0);

  return (
    <div className="flex items-center gap-6">
      <div className="w-32 h-32 flex-shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={28}
              outerRadius={52}
              paddingAngle={3}
              dataKey="value"
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(val: number, name: string, props: { payload?: { grams?: number } }) =>
                [`${props.payload?.grams?.toFixed(1)}g`, name]
              }
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="space-y-2">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: d.color }} />
            <span className="text-sm text-charcoal-500 w-16">{d.name}</span>
            <span className="text-sm font-semibold text-charcoal-900">{d.grams.toFixed(1)}g</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface NutritionBarProps {
  label: string;
  value?: number;
  unit: string;
  max: number;
  color?: string;
}

export function NutritionBar({ label, value, unit, max, color = '#245B43' }: NutritionBarProps) {
  if (value === undefined) return null;
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm text-charcoal-500">{label}</span>
        <span className="text-sm font-semibold text-charcoal-900">
          {value.toFixed(1)} {unit}
        </span>
      </div>
      <div className="h-2 bg-forest-50 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

interface NutritionSummaryCardProps {
  nutrition: NutritionData;
}

export function NutritionSummaryCard({ nutrition }: NutritionSummaryCardProps) {
  return (
    <div className="space-y-4">
      {/* Calories */}
      <div className="flex items-center justify-between p-4 bg-forest-50 rounded-xl">
        <div>
          <p className="text-xs text-charcoal-100 uppercase tracking-wide font-medium">Estimated Calories</p>
          <p className="text-3xl font-bold font-display text-charcoal-900 mt-0.5">
            {nutrition.calories?.toFixed(0) ?? '—'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-charcoal-100">Per serving</p>
          <p className="text-sm font-medium text-charcoal-500 mt-0.5">{nutrition.serving_size}</p>
        </div>
      </div>

      {/* Macro bars */}
      <div className="space-y-3">
        <NutritionBar label="Protein" value={nutrition.protein_g} unit="g" max={100} color="#245B43" />
        <NutritionBar label="Carbohydrates" value={nutrition.carbs_g} unit="g" max={300} color="#A9BEA3" />
        <NutritionBar label="Fat" value={nutrition.fat_g} unit="g" max={100} color="#D4A017" />
        <NutritionBar label="Fiber" value={nutrition.fiber_g} unit="g" max={38} color="#7FA88A" />
        <NutritionBar label="Sugar" value={nutrition.sugar_g} unit="g" max={50} color="#F5C842" />
        <NutritionBar label="Sodium" value={nutrition.sodium_mg} unit="mg" max={2300} color="#788078" />
      </div>
    </div>
  );
}

interface NutritionScoreRingProps {
  score?: number;
}

export function NutritionScoreRing({ score }: NutritionScoreRingProps) {
  if (score === undefined) return null;
  const color = score >= 70 ? '#245B43' : score >= 50 ? '#D4A017' : '#DC2626';
  const label = score >= 70 ? 'Good' : score >= 50 ? 'Moderate' : 'Low';

  return (
    <div className="flex items-center gap-4">
      <div className="relative w-20 h-20 flex-shrink-0">
        <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
          <circle cx="40" cy="40" r="32" fill="none" stroke="#EAF1E5" strokeWidth="8" />
          <circle
            cx="40" cy="40" r="32" fill="none"
            stroke={color} strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${(score / 100) * 201} 201`}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold font-display" style={{ color }}>{score.toFixed(0)}</span>
        </div>
      </div>
      <div>
        <p className="font-semibold" style={{ color }}>{label}</p>
        <p className="text-xs text-charcoal-100 mt-0.5">Nutrition Score</p>
        <p className="text-xs text-charcoal-100 mt-1">out of 100</p>
      </div>
    </div>
  );
}
