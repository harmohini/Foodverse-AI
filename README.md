# FoodVerse AI — Multimodal Food Intelligence Platform

A complete, functional prototype that analyses food images, videos, and text to deliver nutrition estimates, freshness assessments, restaurant hygiene observations, recipe generation, and personalised meal planning.

## 🎥 Project Demo Video

Watch the complete demonstration of FoodVerse AI in action:
👉 **[Watch FoodVerse AI Demo Video on Google Drive](https://drive.google.com/file/d/1zPttiYTebIy7EDBSIKwYOPWtC5m6AFhw/view?usp=sharing)**

## Architecture

```
FoodVerse AI
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── core/               # Config & logging
│   │   ├── api/routes/         # Route handlers (food, nutrition, freshness, hygiene, cooking, meal_plans, history)
│   │   ├── database/           # SQLAlchemy models & connection
│   │   ├── schemas/            # Pydantic request/response models
│   │   └── services/           # Business logic & AI provider adapters
│   ├── tests/                  # Pytest test suite (49 tests)
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── App.tsx             # Router & layout shell
│   │   ├── pages/              # 9 feature pages
│   │   ├── components/         # Shared UI components, charts, upload zones
│   │   ├── services/           # Axios API client + service functions
│   │   ├── types/              # TypeScript type definitions
│   │   └── utils/              # Date formatting utilities
│   ├── tailwind.config.js      # FoodVerse design system
│   └── .env.example
└── README.md
```

## Prerequisites

- **Python 3.11+** (tested on 3.13)
- **Node.js 18+** (tested on 22)
- **npm 9+**

## Quick Start

### 1. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure (copy and optionally edit)
cp .env.example .env

# Start the backend
uvicorn app.main:app --reload --port 8000
```

Backend will start at **http://localhost:8000**
API docs: **http://localhost:8000/docs**

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will start at **http://localhost:5173**

## Environment Configuration

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `gemini` | AI provider: `gemini` (primary), `openai` (optional fallback), or `demo` |
| `GEMINI_API_KEY` | *(empty)* | Your Google Gemini API key (via Google AI Studio) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Primary Gemini model for multimodal vision & text generation |
| `GEMINI_VISION_MODEL` | `gemini-2.5-flash` | Multimodal model for food/freshness/hygiene image analysis |
| `GEMINI_TEXT_MODEL` | `gemini-2.5-flash` | Text model for nutrition, recipe cooking, and meal planning |
| `OPENAI_API_KEY` | *(empty)* | Optional OpenAI API key (for fallback provider) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible base URL |
| `OPENAI_VISION_MODEL` | `gpt-4o` | Vision model for OpenAI fallback |
| `OPENAI_TEXT_MODEL` | `gpt-4o` | Text model for OpenAI fallback |
| `DATABASE_URL` | `sqlite:///./data/foodverse.db` | SQLite DB path |
| `MAX_IMAGE_SIZE_MB` | `10` | Max image upload size |
| `MAX_VIDEO_SIZE_MB` | `100` | Max video upload size |
| `FRONTEND_URL` | `http://localhost:5173` | CORS origin |

## Running Tests

```bash
cd backend
source .venv/bin/activate
python3 -m pytest tests/ -v
```

**Expected result:** 49 tests passing, ~2 seconds.

## Building for Production

```bash
# Frontend production build
cd frontend
npm run build
npm run type-check

# Backend (no build step needed — run with uvicorn or gunicorn)
```

## Demo Mode vs Live AI

The app runs in **Demo Mode** by default when `AI_PROVIDER=demo` — no API keys required. Setting `AI_PROVIDER=gemini` and providing a valid `GEMINI_API_KEY` enables live Gemini inference.

| Feature | Demo Mode | Live AI Mode (Google Gemini API) |
|---|---|---|
| Food Recognition | Sample result (Grilled Chicken Salad) | Real Gemini multimodal inference (image & text) |
| Nutrition Analysis | Reference database values | AI-generated estimates (text & image) |
| Freshness Check | Sample assessment | Real vision & text freshness assessment |
| Hygiene Monitor | Sample report | Frame-by-frame vision & text observations |
| Smart Cooking | Pre-written recipe | LLM-generated recipe with interactive safety chat |
| Meal Planner | 3-day demo plan | LLM-generated personalised plan with shopping list |

A **Demo Mode** banner is shown on every result when running in demo mode.

## Six Core Features

1. **Food Recognition** — Supports both image uploads (JPEG/PNG/WebP) and text descriptions; identifies dish, ingredients, and serving size.
2. **Nutrition Analysis** — Estimates calories, macros, fiber, sodium; visual score ring and macro pie chart (supports text requests and image estimation).
3. **Freshness Check** — Visual & text assessment of Fresh / Moderately Fresh / Possible Spoilage with safety disclaimers.
4. **Hygiene Monitor** — Image/video frame extraction and text observation analysis with a full evidence report.
5. **Smart Cooking** — Recipe generation with step-by-step instructions, food safety notes, and chat follow-ups.
6. **Meal Planner** — 1–7-day plans with shopping lists; respects allergies and dietary exclusions.

## API Endpoints

```
GET  /api/health
GET  /api/health/ready
GET  /api/health/provider

POST /api/v1/food/recognize
POST /api/v1/food/recognize-text
POST /api/v1/nutrition/analyze
POST /api/v1/nutrition/analyze-image
POST /api/v1/freshness/analyze
POST /api/v1/freshness/analyze-text
POST /api/v1/hygiene/analyze
POST /api/v1/hygiene/analyze-text
POST /api/v1/cooking/generate
POST /api/v1/cooking/chat
POST /api/v1/meal-plans/generate
GET  /api/v1/meal-plans/
GET  /api/v1/meal-plans/{plan_id}
PUT  /api/v1/meal-plans/{plan_id}
DELETE /api/v1/meal-plans/{plan_id}
GET  /api/v1/history/
GET  /api/v1/history/{analysis_id}
DELETE /api/v1/history/{analysis_id}
```

## Known Limitations

- Audio transcription is not implemented in this version.
- Video analysis requires OpenCV (`pip install opencv-python-headless`) for frame extraction.
- Nutrition values are estimates — not laboratory-verified.
- Freshness and hygiene analysis cannot detect pathogens, temperature abuse, or internal contamination.
- SQLite database is for local single-user use only.
- No authentication or multi-user isolation.

## Responsible AI Notices

- AI-generated results are clearly labelled as estimates.
- Demo results are always distinguished from live AI inference.
- Food safety warnings are included on all freshness and hygiene outputs.
- Nutrition scores are educational heuristics, not medical judgments.
- Meal plans are general guidance, not clinical dietary recommendations.

## Deployment Considerations

For production use:
- Replace SQLite with PostgreSQL.
- Add proper authentication.
- Use a secrets manager for API keys.
- Set `DEBUG=false` and `APP_ENV=production`.
- Serve the frontend build from a CDN or static host.
- Run the backend behind Nginx or a reverse proxy with TLS.
